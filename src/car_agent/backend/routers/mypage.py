"""マイページ API - 営業担当者の実績確認 + Genie チャット."""

import asyncio
import calendar
import json
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from car_agent.backend.config import get_settings, get_oauth_token, get_databricks_host, get_full_table_name
from car_agent.backend.database import db
from car_agent.backend.llm import llm

router = APIRouter(prefix="/api/mypage", tags=["mypage"])

# Genie チャットセッション（conversation_id を保持）
_genie_sessions: dict[str, str] = {}  # session_id -> conversation_id


@router.get("/reps")
async def list_sales_reps():
    """担当者一覧を sv_sales_results から返す（ALLオプション付き）。email を ID として返す。"""
    try:
        table = get_full_table_name("sv_sales_results")
        rows = await db.execute_query(
            f"""SELECT sales_rep_email, MAX(sales_rep_name) AS sales_rep_name
                FROM {table}
                WHERE sales_rep_email IS NOT NULL
                GROUP BY sales_rep_email
                ORDER BY sales_rep_name"""
        )
        reps = [{"id": r["sales_rep_email"], "name": r["sales_rep_name"]} for r in rows]
    except Exception:
        reps = []
    all_option = [{"id": "ALL", "name": "ALL"}]
    return {"success": True, "data": all_option + reps}


def _build_filters(sales_rep_email: str) -> tuple[str, str]:
    """WHERE / AND フィルター句を構築する。"""
    is_all = sales_rep_email == "ALL"
    base_where = "WHERE sale_date < CURRENT_DATE()"
    base_and = "AND sale_date < CURRENT_DATE()"
    if is_all:
        return base_where, base_and
    return (
        f"{base_where} AND sales_rep_email = '{sales_rep_email}'",
        f"{base_and} AND sales_rep_email = '{sales_rep_email}'",
    )


async def _generate_loss_actions(
    loss_reasons: list[dict],
    vehicle_breakdown: list[dict],
    same_period_diff: float | None,
) -> dict[str, str]:
    """失注理由ごとの改善アクションをClaudeで一括生成する。"""
    try:
        vehicle_summary = ", ".join(
            f"{v['vehicle_category']}({v['contracted']}/{v['total']}件 成約率{v['rate']}%)"
            for v in vehicle_breakdown
        )
        loss_list = "\n".join(
            f"- {r['loss_reason']}: {r['cnt']}件"
            for r in loss_reasons
        )
        pace_note = f"先月同時点比 {same_period_diff:+.1f}%" if same_period_diff is not None else ""

        prompt = f"""あなたは中古車販売の営業コーチです。
担当者の今月の失注データをもとに、各失注理由に対して考えられる仮説と対策の方向性を1文で示してください。

【今月の失注理由】
{loss_list}

【車種別成約率（今月）】
{vehicle_summary}

【ペース】{pace_note}

以下のJSON形式で出力してください（他のテキスト不要）:
{{"失注理由1": "仮説・対策案（1文）", "失注理由2": "..."}}

ルール:
- 1文30〜50文字以内
- 断定・命令形は禁止（「〜すべき」「〜しましょう」はNG）
- 「〜が一因かもしれません」「〜を検討する余地があります」「〜という仮説が考えられます」など、仮説・示唆のトーンにする
- 車種名・価格帯など具体的な要素を含める
"""
        response = await llm.chat(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.3,
        )
        text = response.strip()
        start, end = text.find("{"), text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
    except Exception as e:
        print(f"[loss_actions] generation failed: {e}")
    return {}


@router.get("/stats")
async def get_mypage_stats(sales_rep_email: str = Query(...)):
    """担当者の今月実績・失注理由・車両カテゴリ別成約率を返す。"""
    full_table = get_full_table_name("sv_sales_results")
    rep_filter, rep_and = _build_filters(sales_rep_email)

    latest_month_sub = f"SELECT date_trunc('month', MAX(sale_date)) FROM {full_table} {rep_filter}"

    monthly_q = f"""
        SELECT
            date_trunc('month', sale_date) AS month,
            COUNT(*) AS total,
            SUM(CASE WHEN outcome = '成約'   THEN 1 ELSE 0 END) AS contracted,
            SUM(CASE WHEN outcome = '失注'   THEN 1 ELSE 0 END) AS lost,
            SUM(CASE WHEN outcome = '商談中' THEN 1 ELSE 0 END) AS in_progress,
            ROUND(SUM(CASE WHEN outcome = '成約' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS contract_rate,
            ROUND(AVG(CASE WHEN outcome = '成約' THEN sale_price END)) AS avg_amount
        FROM {full_table}
        {rep_filter}
        GROUP BY 1 ORDER BY 1 DESC LIMIT 2
    """
    loss_q = f"""
        SELECT loss_reason, COUNT(*) AS cnt
        FROM {full_table}
        WHERE outcome = '失注' {rep_and}
          AND date_trunc('month', sale_date) = ({latest_month_sub})
          AND loss_reason IS NOT NULL AND loss_reason != ''
        GROUP BY 1 ORDER BY 2 DESC
    """
    vehicle_q = f"""
        SELECT
            vehicle_category,
            COUNT(*) AS total,
            SUM(CASE WHEN outcome = '成約' THEN 1 ELSE 0 END) AS contracted,
            ROUND(SUM(CASE WHEN outcome = '成約' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS rate
        FROM {full_table}
        WHERE date_trunc('month', sale_date) = ({latest_month_sub}) {rep_and}
        GROUP BY 1 ORDER BY rate DESC
    """
    daily_q = f"""
        SELECT
            date_trunc('month', sale_date) AS sale_month,
            DAY(sale_date)                 AS day_num,
            SUM(CASE WHEN outcome = '成約' THEN 1 ELSE 0 END) AS contracted
        FROM {full_table}
        WHERE date_trunc('month', sale_date) >= (
            SELECT add_months(date_trunc('month', MAX(sale_date)), -1)
            FROM {full_table} {rep_filter}
        ) {rep_and}
        GROUP BY 1, 2
        ORDER BY 1, 2
    """

    monthly, loss_reasons, vehicle_breakdown, daily_rows = await asyncio.gather(
        db.execute_query(monthly_q),
        db.execute_query(loss_q),
        db.execute_query(vehicle_q),
        db.execute_query(daily_q),
    )

    # 日別データを月ごとに集計
    by_month: dict[str, dict[int, int]] = {}
    for row in daily_rows:
        m = str(row["sale_month"])[:7]
        d = int(row["day_num"])
        by_month.setdefault(m, {})[d] = int(row.get("contracted") or 0)

    months_sorted = sorted(by_month.keys())
    cur_m = months_sorted[-1] if months_sorted else None
    prev_m = months_sorted[-2] if len(months_sorted) >= 2 else None
    cur_days = by_month.get(cur_m, {})
    prev_days = by_month.get(prev_m, {})
    cur_max_day = max(cur_days.keys(), default=0)
    prev_max_day = max(prev_days.keys(), default=0)

    all_max = max(cur_max_day, prev_max_day)
    daily_trend = []
    cur_cum = prev_cum = 0
    for d in range(1, all_max + 1):
        cur_cum += cur_days.get(d, 0)
        prev_cum += prev_days.get(d, 0)
        point: dict = {"day": d}
        if d <= cur_max_day:
            point["current"] = cur_cum
        if d <= prev_max_day:
            point["last_month"] = prev_cum
        daily_trend.append(point)

    cur_to_date = sum(cur_days.get(d, 0) for d in range(1, cur_max_day + 1))
    prev_to_same = sum(prev_days.get(d, 0) for d in range(1, cur_max_day + 1))
    same_period_diff = round((cur_to_date - prev_to_same) / prev_to_same * 100, 1) if prev_to_same > 0 else None

    projected_total = None
    if cur_m and cur_max_day > 0:
        year, month = int(cur_m[:4]), int(cur_m[5:7])
        days_in_month = calendar.monthrange(year, month)[1]
        projected_total = round(cur_to_date / cur_max_day * days_in_month)
    last_month_total = sum(prev_days.values()) if prev_days else None

    if monthly:
        current = monthly[0]
        previous = monthly[1] if len(monthly) > 1 else {}
        rate_diff = None
        if current.get("contract_rate") is not None and previous.get("contract_rate") is not None:
            rate_diff = round(float(current["contract_rate"]) - float(previous["contract_rate"]), 1)

        return {
            "success": True,
            "data": {
                "current_month": current,
                "rate_diff_from_last_month": rate_diff,
                "same_period_diff": same_period_diff,
                "projected_total": projected_total,
                "last_month_total": last_month_total,
                "daily_trend": daily_trend,
                "loss_reasons": loss_reasons,
                "vehicle_breakdown": vehicle_breakdown,
            },
        }

    return {"success": True, "data": {
        "current_month": {},
        "rate_diff_from_last_month": None,
        "loss_reasons": [],
        "vehicle_breakdown": [],
    }}


@router.get("/loss-actions")
async def get_loss_actions(sales_rep_email: str = Query(...)):
    """失注理由ごとのAI改善アクションを非同期で返す。"""
    full_table = get_full_table_name("sv_sales_results")
    rep_filter, rep_and = _build_filters(sales_rep_email)
    latest_month_sub = f"SELECT date_trunc('month', MAX(sale_date)) FROM {full_table} {rep_filter}"

    loss_q = f"""
        SELECT loss_reason, COUNT(*) AS cnt
        FROM {full_table}
        WHERE outcome = '失注' {rep_and}
          AND date_trunc('month', sale_date) = ({latest_month_sub})
          AND loss_reason IS NOT NULL AND loss_reason != ''
        GROUP BY 1 ORDER BY 2 DESC
    """
    vehicle_q = f"""
        SELECT
            vehicle_category,
            COUNT(*) AS total,
            SUM(CASE WHEN outcome = '成約' THEN 1 ELSE 0 END) AS contracted,
            ROUND(SUM(CASE WHEN outcome = '成約' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) AS rate
        FROM {full_table}
        WHERE date_trunc('month', sale_date) = ({latest_month_sub}) {rep_and}
        GROUP BY 1 ORDER BY rate DESC
    """
    try:
        loss_reasons, vehicle_breakdown = await asyncio.gather(
            db.execute_query(loss_q),
            db.execute_query(vehicle_q),
        )
        actions = await _generate_loss_actions(
            loss_reasons=loss_reasons,
            vehicle_breakdown=vehicle_breakdown,
            same_period_diff=None,
        )
    except Exception as e:
        print(f"[loss-actions] error: {e}")
        actions = {}
    return {"success": True, "data": actions}


class MypageChatRequest(BaseModel):
    session_id: str
    sales_rep_email: str
    message: str


def _build_summary_prompt(
    user_question: str,
    text_items: list[dict],
    table_items: list[dict],
) -> str:
    """Genie の結果テーブルを Claude に分析させるプロンプトを構築する。"""
    table_md_parts = []
    for t in table_items:
        cols = t["columns"]
        rows = t["rows"][:30]
        header = "| " + " | ".join(cols) + " |"
        sep = "| " + " | ".join("---" for _ in cols) + " |"
        body = "\n".join("| " + " | ".join(str(c) for c in row) + " |" for row in rows)
        if len(t["rows"]) > 30:
            body += f"\n（...他 {len(t['rows']) - 30} 件）"
        table_md_parts.append(f"{header}\n{sep}\n{body}")

    genie_text = "\n".join(i["content"] for i in text_items) if text_items else ""
    tables_md = "\n\n".join(table_md_parts)

    genie_section = f"\n## Genieの説明\n{genie_text}\n" if genie_text else ""

    return f"""あなたは中古車販売の営業データアナリストです。
ユーザーの質問に対して、以下のクエリ結果データを分析し、わかりやすく回答してください。

## ユーザーの質問
{user_question}
{genie_section}
## クエリ結果データ
{tables_md}

## 回答ルール
- 質問に直接答える形で回答する
- 重要な数字は**太字**で強調する
- 比較・ランキングがあれば明確に示す
- 金額は万円単位で表示
- 3〜5文で簡潔にまとめる（長すぎない）
- 最後に1文でインサイトや示唆を添える
- マークダウン形式で出力（見出しは ## ではなく ### を使う）"""


async def _genie_start_or_continue(
    host: str, token: str, space_id: str, session_id: str, message: str
) -> tuple[str, str]:
    """Genie に質問を送り (conversation_id, message_id) を返す。"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    conv_id = _genie_sessions.get(session_id)
    if conv_id:
        url = f"{host}/api/2.0/genie/spaces/{space_id}/conversations/{conv_id}/messages"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json={"content": message}, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        return conv_id, data["id"]
    else:
        url = f"{host}/api/2.0/genie/spaces/{space_id}/start-conversation"
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json={"content": message}, headers=headers)
            resp.raise_for_status()
            data = resp.json()
        conv_id = data["conversation_id"]
        _genie_sessions[session_id] = conv_id
        return conv_id, data["message"]["id"]


async def _genie_poll(
    host: str, token: str, space_id: str, conv_id: str, msg_id: str, timeout: int = 180
) -> list[dict]:
    """Genie のメッセージが COMPLETED になるまでポーリングし、結果アイテムのリストを返す。"""
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{host}/api/2.0/genie/spaces/{space_id}/conversations/{conv_id}/messages/{msg_id}"
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout

    async with httpx.AsyncClient(timeout=60.0) as client:
        while loop.time() < deadline:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "")

            if status == "COMPLETED":
                # Genie Space UI 相当の構造: text / sql / table の 3 要素
                items: list[dict] = []
                for att in data.get("attachments", []):
                    if "text" in att and att["text"].get("content"):
                        items.append({"type": "text", "content": att["text"]["content"]})
                    elif "query" in att:
                        q = att["query"]
                        if q.get("description"):
                            items.append({"type": "text", "content": q["description"]})
                        if q.get("query"):
                            items.append({"type": "sql", "query": q["query"]})
                        att_id = att.get("attachment_id", "")
                        if att_id:
                            result_url = (
                                f"{host}/api/2.0/genie/spaces/{space_id}"
                                f"/conversations/{conv_id}/messages/{msg_id}"
                                f"/attachments/{att_id}/query-result"
                            )
                            try:
                                r = await client.get(result_url, headers=headers)
                                if r.status_code == 200:
                                    qr = r.json()
                                    sr = qr.get("statement_response", {})
                                    cols = [
                                        c["name"]
                                        for c in sr.get("manifest", {}).get("schema", {}).get("columns", [])
                                    ]
                                    rows = sr.get("result", {}).get("data_array", [])
                                    if cols and rows:
                                        items.append({"type": "table", "columns": cols, "rows": rows[:50]})
                            except Exception:
                                pass
                return items if items else [{"type": "text", "content": "（回答を取得できませんでした）"}]

            if status in ("ERROR", "FAILED"):
                raise RuntimeError(data.get("error", f"Genie returned {status}"))

            await asyncio.sleep(2)

    raise TimeoutError("Genie response timeout")


@router.get("/genie/space-info")
async def get_genie_space_info() -> dict:
    """マイページ Genie Space の埋め込み URL と ID を返す (iframe 用)。"""
    settings = get_settings()
    host = get_databricks_host()
    space_id = settings.sales_mypage_genie_space_id
    if not (host and space_id):
        return {"space_id": "", "embed_url": ""}
    # Databricks 公式 Genie Space UI を iframe で埋め込むための URL
    embed_url = f"{host}/genie/rooms/{space_id}"
    return {"space_id": space_id, "embed_url": embed_url}


@router.get("/genie/sample-questions")
async def get_genie_sample_questions() -> dict:
    """マイページ Genie Space の sample_questions を返す (UI のクイック質問チップ用)。

    失敗時は空配列を返して UI 側でフォールバック表示。
    """
    settings = get_settings()
    host = get_databricks_host()
    token = get_oauth_token()
    space_id = settings.sales_mypage_genie_space_id
    if not (host and token and space_id):
        return {"questions": []}
    url = f"{host}/api/2.0/genie/spaces/{space_id}?include_serialized_space=true"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
            if not resp.is_success:
                return {"questions": []}
            data = resp.json()
            serialized = data.get("serialized_space")
            if not serialized:
                return {"questions": []}
            parsed = json.loads(serialized) if isinstance(serialized, str) else serialized
            raw = parsed.get("config", {}).get("sample_questions", [])
            questions: list[str] = []
            for q in raw:
                v = q.get("question")
                if isinstance(v, list) and v:
                    questions.append(v[0])
                elif isinstance(v, str):
                    questions.append(v)
            return {"questions": questions}
    except Exception as e:
        print(f"[mypage/genie/sample-questions] error: {e}")
        return {"questions": []}


@router.get("/debug/genie")
async def debug_genie():
    """Genie接続テスト用デバッグエンドポイント（一時）"""
    settings = get_settings()
    host = get_databricks_host()
    token = get_oauth_token()
    space_id = settings.sales_mypage_genie_space_id
    result = {
        "host": host,
        "has_token": bool(token),
        "token_prefix": token[:20] + "..." if token else None,
        "space_id": space_id,
    }
    if host and token and space_id:
        try:
            import uuid as _uuid
            session_id = str(_uuid.uuid4())
            conv_id, msg_id = await _genie_start_or_continue(host, token, space_id, session_id, "鈴木一郎の成約率は？")
            result["start_ok"] = True
            result["conv_id"] = conv_id
            result["msg_id"] = msg_id
            items = await _genie_poll(host, token, space_id, conv_id, msg_id, timeout=60)
            result["poll_ok"] = True
            result["items_count"] = len(items)
            result["items_preview"] = str(items)[:500]
        except Exception as e:
            import traceback
            result["error"] = f"{type(e).__name__}: {e}"
            result["traceback"] = traceback.format_exc()
    return result


@router.post("/chat/stream")
async def mypage_chat_stream(request: MypageChatRequest):
    """Genie API を呼び出し、SSE で回答を返す。"""
    settings = get_settings()
    host = get_databricks_host()
    token = get_oauth_token()
    space_id = settings.sales_mypage_genie_space_id

    async def generate():
        try:
            yield f"data: {json.dumps({'type': 'progress', 'message': 'データを分析中...'})}\n\n"

            if not host or not token or not space_id:
                await asyncio.sleep(0.5)
                demo_answer = "Genie への接続情報が設定されていません。管理者にお問い合わせください。"
                yield f"data: {json.dumps({'type': 'content', 'content': demo_answer})}\n\n"
                yield "data: [DONE]\n\n"
                return

            conv_id, msg_id = await _genie_start_or_continue(
                host, token, space_id, request.session_id, request.message
            )

            items = await _genie_poll(host, token, space_id, conv_id, msg_id)

            # Genie 生回答をそのまま text / sql / table の順序で流す (LLM 後処理なし、公式 Space UI 相当)
            if not items or all(
                i.get("type") == "text" and not i.get("content", "").strip() for i in items
            ):
                yield f"data: {json.dumps({'type': 'content', 'content': '該当するデータが見つかりませんでした。別の質問をお試しください。'})}\n\n"
            else:
                for item in items:
                    itype = item.get("type")
                    if itype == "text":
                        content = item.get("content", "")
                        if content:
                            chunk_size = 40
                            for i in range(0, len(content), chunk_size):
                                yield f"data: {json.dumps({'type': 'content', 'content': content[i:i+chunk_size]})}\n\n"
                                await asyncio.sleep(0.01)
                    elif itype == "sql":
                        yield f"data: {json.dumps({'type': 'sql', 'query': item['query']})}\n\n"
                    elif itype == "table":
                        yield f"data: {json.dumps({'type': 'table', 'columns': item['columns'], 'rows': item['rows']})}\n\n"

            yield "data: [DONE]\n\n"
        except Exception as e:
            print(f"[mypage/chat] error: {type(e).__name__}: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Encoding": "none",
            "X-Accel-Buffering": "no",
        },
    )
