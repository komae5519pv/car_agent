"""Chat API endpoints - Multi-Agent Supervisor経由."""

import asyncio
import json
import re
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from car_agent.backend.models import ChatRequest, ChatResponse, APIResponse
from car_agent.backend.config import get_settings, get_oauth_token, get_databricks_host, get_full_table_name
from car_agent.backend.database import db
from car_agent.backend.demo_data import get_demo_customer

router = APIRouter(prefix="/api/chat", tags=["chat"])

# In-memory chat history (セッションIDごと)
chat_sessions: dict[str, list[dict]] = {}


async def _call_agent_raw(messages: list[dict]) -> dict:
    """マルチエージェントスーパーバイザーエンドポイントを呼び出し、フル結果dictを返す。"""
    settings = get_settings()
    host = get_databricks_host()
    token = get_oauth_token()

    if not host or not token:
        return {"_no_connection": True}

    url = f"{host}/serving-endpoints/{settings.agent_endpoint_name}/invocations"

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            url,
            json={"input": messages},
            headers={"Authorization": f"Bearer {token}"},
        )
        resp.raise_for_status()
        return resp.json()


_NAME_TAG_RE = re.compile(r'^<name>([^<]*)</name>\s*', re.DOTALL)


def _agent_progress_label(name: str) -> str:
    """エージェント名からプログレスラベルを返す。"""
    n = name.lower()
    if "knowledge" in n:
        return "ナレッジベース（車両知識）を検索中..."
    if "assistant" in n or "genie" in n:
        return "社内データ（Genie）を検索中..."
    if "tavily" in n or "search" in n:
        return "Web検索中..."
    return "エージェントに問い合わせ中..."


def _extract_thinking_and_answer(output: list) -> tuple[list[dict], str]:
    """outputリストから思考ステップリストと最終回答を抽出する。

    思考ステップ形式:
      {"type": "tool",     "content": "function_name", "agent": ""}
      {"type": "progress", "content": "ラベルテキスト", "agent": "agent-name"}
      {"type": "text",     "content": "中間テキスト",   "agent": "agent-name"}

    最終回答 = 全assistantメッセージのうち末尾のもの（<name>タグ剥がし済み）。
    それより前のassistantメッセージ＋function_callが思考ステップになる。
    """
    raw_items: list[dict] = []  # {kind: 'tool'|'message', text: str, agent: str}

    for item in output:
        item_type = item.get("type")

        if item_type == "function_call":
            raw_items.append({"kind": "tool", "text": item.get("name", ""), "agent": ""})
            continue

        if item_type != "message" or item.get("role") != "assistant":
            continue

        text = ""
        for content in item.get("content", []):
            if content.get("type") == "output_text" and content.get("text"):
                text = content["text"]
                break

        if not text:
            continue

        name_match = _NAME_TAG_RE.match(text)
        if name_match:
            agent = name_match.group(1)
            remaining = text[name_match.end():].strip()
            raw_items.append({"kind": "message", "text": remaining, "agent": agent})
        else:
            raw_items.append({"kind": "message", "text": text, "agent": ""})

    # 末尾のmessageアイテムを最終回答とする
    final_answer = ""
    final_idx = -1
    for i in range(len(raw_items) - 1, -1, -1):
        if raw_items[i]["kind"] == "message":
            final_answer = raw_items[i]["text"]
            final_idx = i
            break

    # 最終回答より前のアイテムを思考ステップに変換
    thinking_steps: list[dict] = []
    for i, item in enumerate(raw_items):
        if i >= final_idx:
            break
        if item["kind"] == "tool":
            thinking_steps.append({
                "type": "progress",
                "content": f"🔧 {item['text']}",
                "agent": "",
            })
        elif item["text"]:
            thinking_steps.append({
                "type": "text",
                "content": item["text"],
                "agent": item["agent"],
            })
        else:
            # テキストなし = ルーティング通知のみ → プログレスラベルとして扱う
            thinking_steps.append({
                "type": "progress",
                "content": _agent_progress_label(item["agent"]),
                "agent": item["agent"],
            })

    return thinking_steps, final_answer


async def _build_system_message(customer_id: Optional[str]) -> dict:
    """顧客コンテキストを含むシステムメッセージを生成する。"""
    content = "現在、営業担当者向けのCar AI Demoアシスタントとして動作しています。"
    if customer_id:
        customer = None
        try:
            table = get_full_table_name("sv_customers")
            results = await db.execute_query(
                f"SELECT * FROM {table} WHERE customer_id = '{customer_id}' LIMIT 1"
            )
            if results:
                customer = results[0]
        except Exception:
            pass
        if not customer:
            customer = get_demo_customer(customer_id)
        if customer:
            name = customer.get("name", "")
            age = customer.get("age", "")
            occupation = customer.get("occupation", "")
            budget_min = customer.get("budget_min", 0)
            budget_max = customer.get("budget_max", 0)
            preferences = customer.get("preferences", "")
            current_vehicle = customer.get("current_vehicle", "なし")
            family_structure = customer.get("family_structure", "")
            content += (
                f"\n\n【現在対応中の顧客情報】\n"
                f"顧客名: {name}様\n"
                f"顧客ID: {customer_id}\n"
                f"年齢: {age}歳 / 職業: {occupation}\n"
                f"家族構成: {family_structure}\n"
                f"現在の車: {current_vehicle}\n"
                f"予算: {budget_min:,}〜{budget_max:,}円\n"
                f"希望条件: {preferences}\n\n"
                f"この顧客について質問された場合は必ず「{name}様」と名前で呼んでください。"
                f"顧客データを参照する際は顧客ID「{customer_id}」を使用してください。"
            )
        else:
            content += f"\n\n現在表示中の顧客ID: {customer_id}。この顧客に関する質問には必ずこのIDで顧客データを参照してください。"
    return {"role": "system", "content": content}


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """チャットメッセージを送信してエージェントから回答を得る。"""
    try:
        session_id = request.session_id
        customer_id = request.customer_id
        message = request.message

        if session_id not in chat_sessions:
            chat_sessions[session_id] = []

        chat_sessions[session_id].append({"role": "user", "content": message})
        messages = [await _build_system_message(customer_id)] + chat_sessions[session_id]
        result = await _call_agent_raw(messages)

        if result.get("_no_connection"):
            response = "デモモード: エージェントエンドポイントに接続できません。"
        else:
            _, response = _extract_thinking_and_answer(result.get("output", []))
            if not response:
                try:
                    response = result["choices"][0]["message"]["content"]
                except (KeyError, IndexError):
                    response = ""

        if response:
            chat_sessions[session_id].append({"role": "assistant", "content": response})

        return ChatResponse(session_id=session_id, response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(request: ChatRequest):
    """エージェント呼び出しをSSEストリームとして返す（エージェントはnon-streaming）。"""
    try:
        session_id = request.session_id
        customer_id = request.customer_id
        message = request.message

        if session_id not in chat_sessions:
            chat_sessions[session_id] = []

        chat_sessions[session_id].append({"role": "user", "content": message})
        messages = [await _build_system_message(customer_id)] + chat_sessions[session_id]

        async def generate():
            try:
                yield f"data: {json.dumps({'type': 'progress', 'message': 'マルチエージェントに接続中...'})}\n\n"

                host = get_databricks_host()
                token = get_oauth_token()

                if not host or not token:
                    yield f"data: {json.dumps({'type': 'content', 'content': 'デモモード: エージェントエンドポイントに接続できません。'})}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                settings = get_settings()
                url = f"{host}/serving-endpoints/{settings.agent_endpoint_name}/invocations"
                final_answer_buf = ""
                current_fn_name = ""
                current_fn_args = ""

                async with httpx.AsyncClient(timeout=180.0) as client:
                    async with client.stream(
                        "POST", url,
                        json={"input": messages, "stream": True},
                        headers={"Authorization": f"Bearer {token}"},
                    ) as resp:
                        resp.raise_for_status()
                        buf = ""
                        async for chunk in resp.aiter_raw():
                            buf += chunk.decode("utf-8", errors="replace")
                            while "\n" in buf:
                                line, buf = buf.split("\n", 1)
                                line = line.strip()
                                if not line.startswith("data: "):
                                    continue
                                data_str = line[6:]
                                if data_str == "[DONE]":
                                    break
                                try:
                                    event = json.loads(data_str)
                                    etype = event.get("type", "")

                                    # [DEBUG] 全イベントタイプをログ出力（tool_call確認用）
                                    if etype not in ("response.output_text.delta", ""):
                                        print(f"[SSE event] type={etype} keys={list(event.keys())}", flush=True)

                                    if etype == "response.output_item.added":
                                        item = event.get("item", {})
                                        itype = item.get("type", "")
                                        if itype == "function_call":
                                            current_fn_name = item.get("name", "")
                                            current_fn_args = ""
                                        elif itype == "function_call_output":
                                            output_raw = item.get("output", "")
                                            yield f"data: {json.dumps({'type': 'tool_result', 'name': current_fn_name, 'output': output_raw})}\n\n"

                                    elif etype == "response.function_call_arguments.delta":
                                        current_fn_args += event.get("delta", "")

                                    elif etype == "response.function_call_arguments.done":
                                        yield f"data: {json.dumps({'type': 'tool_call', 'name': current_fn_name, 'args': current_fn_args})}\n\n"

                                    elif etype == "response.output_text.delta":
                                        delta = event.get("delta", "")
                                        if delta:
                                            final_answer_buf += delta
                                            yield f"data: {json.dumps({'type': 'content', 'content': delta})}\n\n"
                                except json.JSONDecodeError:
                                    pass

                if final_answer_buf:
                    chat_sessions[session_id].append({"role": "assistant", "content": final_answer_buf})

                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

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
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{session_id}", response_model=APIResponse)
async def get_chat_history(session_id: str) -> APIResponse:
    """セッションのチャット履歴を返す。"""
    if session_id not in chat_sessions:
        return APIResponse(success=True, data=[])

    history = [msg for msg in chat_sessions[session_id] if msg["role"] != "system"]
    return APIResponse(success=True, data=history)


@router.delete("/history/{session_id}", response_model=APIResponse)
async def clear_chat_history(session_id: str) -> APIResponse:
    """セッションのチャット履歴を削除する。"""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
    return APIResponse(success=True, data={"message": "Chat history cleared"})
