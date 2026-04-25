"""Vehicle recommendation API endpoints with demo data support."""

import json
import os
from typing import Optional

from fastapi import APIRouter, HTTPException

from car_agent.backend.database import db
from car_agent.backend.llm import llm
from car_agent.backend.models import (
    Vehicle,
    VehicleRecommendation,
    RecommendationResponse,
    APIResponse,
)
from car_agent.backend.config import get_full_table_name
from car_agent.backend.demo_data import (
    get_demo_customer,
    get_demo_recommendations,
    get_demo_talk_script,
    get_demo_vehicles_for_customer,
    get_demo_interaction,
    DEMO_VEHICLES,
)

router = APIRouter(prefix="/api", tags=["recommendations"])

# Use demo data when DEMO_MODE is set or database is not configured
USE_DEMO = os.getenv("DEMO_MODE", "false").lower() == "true"

# sv_customers column aliasing for frontend compatibility
_COLUMN_ALIASES = {
    "contact_name": "name",
    "family_detail": "family_structure",
}

def _alias_row(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        out[_COLUMN_ALIASES.get(k, k)] = v
    return out


@router.get("/vehicles", response_model=APIResponse)
async def list_vehicles(
    limit: int = 20,
    offset: int = 0,
    body_type: Optional[str] = None,
    min_price: Optional[int] = None,
    max_price: Optional[int] = None,
) -> APIResponse:
    """Get list of available vehicles."""
    try:
        if USE_DEMO:
            vehicles = DEMO_VEHICLES.copy()

            # Apply filters
            if body_type:
                vehicles = [v for v in vehicles if v["body_type"] == body_type]
            if min_price:
                vehicles = [v for v in vehicles if v["price"] >= min_price]
            if max_price:
                vehicles = [v for v in vehicles if v["price"] <= max_price]

            # Apply pagination
            vehicles = vehicles[offset : offset + limit]

            return APIResponse(success=True, data=vehicles)

        # Use database
        table = get_full_table_name("sv_vehicle_inventory")
        conditions = []

        if body_type:
            conditions.append(f"body_type = '{body_type}'")
        if min_price:
            conditions.append(f"price >= {min_price}")
        if max_price:
            conditions.append(f"price <= {max_price}")

        where_clause = " AND ".join(conditions) if conditions else "1=1"
        query = f"""
            SELECT * FROM {table}
            WHERE {where_clause}
            LIMIT {limit} OFFSET {offset}
        """

        results = await db.execute_query(query)
        for v in results:
            if 'image_path' in v and 'image_url' not in v:
                v['image_url'] = v['image_path']
        return APIResponse(success=True, data=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/customers/{customer_id}/recommendations", response_model=APIResponse)
async def get_recommendations(customer_id: str) -> APIResponse:
    """Get vehicle recommendations - reads from gd_recommendations table."""
    try:
        if USE_DEMO:
            return _build_demo_recommendations(customer_id)

        rec_table = get_full_table_name("gd_recommendations")
        veh_table = get_full_table_name("sv_vehicle_inventory")

        rows = await db.execute_query(
            f"""SELECT r.customer_id, r.rank, r.vehicle_key, r.vehicle_name,
                       r.match_score, r.recommendation_reason, r.talk_script,
                       r.key_selling_points, r.image_path,
                       v.price, v.body_type, v.model_year,
                       v.fuel_type, v.description
                FROM {rec_table} r
                LEFT JOIN {veh_table} v ON r.vehicle_key = v.vehicle_key
                WHERE r.customer_id = '{customer_id}'
                ORDER BY r.rank"""
        )

        if not rows:
            raise HTTPException(status_code=404, detail="推薦データが見つかりません。再生成ボタンを押してください。")

        recommendations = []
        talk_script_parts = []
        for i, row in enumerate(rows, 1):
            image_path = row.get("image_path", "")
            # image_path is "images/harrier.jpg" — extract just the filename
            image_filename = image_path.split("/")[-1] if image_path else ""
            image_url = f"/api/images/{image_filename}" if image_filename else ""
            price = row.get("price", 0)
            try:
                price_str = f"¥{int(price):,}" if price else ""
            except (ValueError, TypeError):
                price_str = ""
            vehicle_name = row.get("vehicle_name", "")
            vehicle = {
                "vehicle_id": row.get("vehicle_key", ""),
                "vehicle_key": row.get("vehicle_key", ""),
                "make": "",
                "maker": "",
                "model": vehicle_name,
                "vehicle_name": vehicle_name,
                "price": price,
                "price_min": price,
                "price_max": price,
                "body_type": row.get("body_type", ""),
                "category": row.get("body_type", ""),
                "year": row.get("model_year", ""),
                "fuel_type": row.get("fuel_type", ""),
                "features": row.get("key_selling_points", ""),
                "image_url": image_url,
                "image_path": image_path,
            }
            recommendations.append({
                "vehicle": vehicle,
                "match_score": row.get("match_score", 0),
                "reason": row.get("recommendation_reason", ""),
            })
            # Build combined talk script
            pitch = row.get("talk_script", "")
            if pitch:
                label = "── 一番のおすすめです" if i == 1 else ""
                heading = f"### 第{i}位：{vehicle_name}（{price_str}）{label}"
                talk_script_parts.append(f"{heading}\n{pitch}")

        talk_script = "\n\n".join(talk_script_parts)

        return APIResponse(success=True, data={
            "customer_id": customer_id,
            "recommendations": recommendations,
            "talk_script": talk_script,
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _build_demo_recommendations(customer_id: str) -> APIResponse:
    """Build response from demo data."""
    recommendations = get_demo_recommendations(customer_id)
    talk_script = get_demo_talk_script(customer_id)
    if recommendations:
        vehicle_map = {v['vehicle_id']: v for v in DEMO_VEHICLES}
        enriched = [
            {"vehicle": vehicle_map[r['vehicle_id']], "match_score": r['match_score'], "reason": r['reason']}
            for r in recommendations if r['vehicle_id'] in vehicle_map
        ]
        return APIResponse(success=True, data={"customer_id": customer_id, "recommendations": enriched, "talk_script": talk_script})
    raise HTTPException(status_code=404, detail="Customer not found")


async def _generate_talk_script(
    customer: dict,
    recommendations: list[dict],
    interaction: Optional[dict] = None
) -> str:
    """Generate talk script for the recommendations (Format B: car-by-car)."""
    cust_name = customer.get('name', customer.get('contact_name', ''))
    vehicles_ranked = []
    for i, rec in enumerate(recommendations[:3], 1):
        v = rec['vehicle']
        price = v.get('price', 0)
        try:
            price_str = f"{int(price):,}円"
        except (ValueError, TypeError):
            price_str = str(price)
        model = v.get('vehicle_name', v.get('model', ''))
        vehicles_ranked.append(
            f"第{i}位: {model}（{price_str}）\n"
            f"  推薦理由: {rec.get('reason','')}"
        )
    vehicles_info = "\n".join(vehicles_ranked)

    transcript_context = ""
    if interaction and interaction.get("transcript"):
        transcript_context = f"\n商談録音テキスト（参考）:\n{interaction['transcript'][:2000]}\n"

    key_quotes_context = ""
    if interaction and interaction.get("key_quotes"):
        quotes = "、".join([f'「{q}」' for q in interaction["key_quotes"]])
        key_quotes_context = f"\n顧客の印象的な発言: {quotes}\n"

    prompt = f"""あなたは経験豊富な自動車営業担当者です。以下の顧客に向けた営業トークスクリプトを作成してください。

顧客情報:
- 名前: {cust_name}（{customer['age']}歳・{customer.get('occupation', '')}）
- 家族構成: {customer.get('family_structure', customer.get('family_detail', ''))}
- 現在の車: {customer.get('current_vehicle', '')}
- 予算: {customer.get('budget_min', 0):,}〜{customer.get('budget_max', 0):,}円
- 重視点: {customer.get('preferences', '')}
{key_quotes_context}{transcript_context}
推薦車両（ランク順）:
{vehicles_info}

【出力フォーマット】必ず以下の見出し構成で出力してください:

## {cust_name}様へのご提案トーク

### 導入
（この顧客の状況・背景に踏み込んだ自然な一言。商談での発言や具体的な生活シーンに触れ、「この人は自分のことをわかってくれている」と感じさせる。1〜3文程度。）

### 第1位：[車名]（[価格]）── 一番のおすすめです
- **[推薦ポイント1]**：この顧客固有の事情・ニーズに直結した理由。例えば〜〜という場面でこの機能が効く、という形で具体的な生活シーンを自然に盛り込む
- **[推薦ポイント2]**：具体的な数字や使用シーンを交えた理由
- **[推薦ポイント3]**：他との差別化ポイント
*営業としての一言：なぜこの人にこの車が最も合うか、自分の意見を一言*

### 第2位：[車名]（[価格]）
- **[推薦ポイント1]**：この顧客固有の事情に紐付けた理由。例えば〜〜という場面を自然に盛り込む
- **[推薦ポイント2]**：具体的な理由
*（第1位と比較した際の位置づけを一言）*

### 第3位：[車名]（[価格]）
- **[推薦ポイント1]**：この顧客固有の事情に紐付けた理由。例えば〜〜という場面を自然に盛り込む
- **[推薦ポイント2]**：具体的な理由
*（第1位・第2位と比較した際の位置づけを一言）*

### クロージング
（具体的な次のアクションへの自然な誘導。試乗・実車確認など。1〜2文。）

【重要な注意点】
- 導入は「先日はありがとうございました」だけで終わらせず、この顧客の具体的な状況（商談での発言・生活背景）に必ず言及する
- 各推薦ポイントは「この人だからこそ」の理由にする。汎用的なスペック説明にならないこと
- 機能・特徴の説明には「例えば〜〜」の形で顧客の実際の生活シーンを自然に織り込む（「〜〜をご想像ください」「〜〜をイメージしてみてください」などの押しつけ表現は使わない）
- 第1位には営業担当者自身の意見・判断を入れる（「私が一番おすすめする理由は〜」）
- 顧客の呼び方は必ず「苗字＋様」（例：渡辺様、山田様、佐藤様）。役職名（部長・課長・社長など）は絶対に使わない。下の名前でも呼ばない。どんな肩書きの人でも「○○様」で統一
- 文体は自然な日本語で、押しつけがましくなく、でも確信を持って伝える口調
- Markdown形式で出力"""

    messages = [
        {"role": "system", "content": "あなたは顧客の深層ニーズを理解し、シャープに刺さる提案ができる優秀な自動車営業担当者です。"},
        {"role": "user", "content": prompt}
    ]

    return await llm.chat(messages)


@router.post("/customers/{customer_id}/recommendations/regenerate", response_model=APIResponse)
async def regenerate_recommendations(customer_id: str) -> APIResponse:
    """Generate new recommendations via LLM (does NOT auto-save)."""
    try:
        if USE_DEMO:
            return _build_demo_recommendations(customer_id)

        # Get customer data
        customers_table = get_full_table_name("sv_customers")
        customer_results = await db.execute_query(
            f"SELECT * FROM {customers_table} WHERE customer_id = '{customer_id}'"
        )
        if not customer_results:
            raise HTTPException(status_code=404, detail="Customer not found")
        customer = customer_results[0]

        # Get vehicles within budget
        vehicles_table = get_full_table_name("sv_vehicle_inventory")
        budget_min = customer.get("budget_min") or 0
        budget_max = customer.get("budget_max") or 99999999
        vehicle_results = await db.execute_query(
            f"SELECT * FROM {vehicles_table} WHERE price >= {budget_min} AND price <= {budget_max} LIMIT 20"
        )
        if not vehicle_results:
            vehicle_results = await db.execute_query(f"SELECT * FROM {vehicles_table} LIMIT 20")

        for v in vehicle_results:
            if "image_path" in v and "image_url" not in v:
                v["image_url"] = v["image_path"]

        # Get interaction for context
        interactions_table = get_full_table_name("sv_interactions")
        interaction_results = await db.execute_query(
            f"SELECT * FROM {interactions_table} WHERE customer_id = '{customer_id}' ORDER BY interaction_date DESC LIMIT 1"
        )
        interaction = interaction_results[0] if interaction_results else None

        vehicles_info = "\n".join([
            f"- {v['vehicle_key']}: {v['vehicle_name']} ({v.get('model_year','')}年) {v.get('price',0):,}円 {v.get('body_type','')} {v.get('fuel_type','')}"
            for v in vehicle_results
        ])
        transcript_context = f"\n\n商談録音:\n{interaction.get('content','')}" if interaction and interaction.get("content") else ""

        prompt = f"""以下の顧客に最適な車両を3台推薦してください。

顧客: {customer['contact_name']}（{customer['age']}歳・{customer.get('occupation','')}）
家族: {customer.get('family_detail','')}
予算: {budget_min:,}〜{budget_max:,}円
重視: {customer.get('preferences','')}
{transcript_context}

利用可能な車両:
{vehicles_info}

JSON形式のみで回答:
{{"recommendations": [{{"vehicle_id": "harrier", "match_score": 95, "reason": "推薦理由2〜3文"}}, {{"vehicle_id": "sienta", "match_score": 88, "reason": "..."}}, {{"vehicle_id": "freed", "match_score": 82, "reason": "..."}}]}}"""

        messages = [
            {"role": "system", "content": "あなたは自動車販売のエキスパートです。顧客の状況に合わせた説得力ある推薦理由を作成してください。"},
            {"role": "user", "content": prompt}
        ]
        response = await llm.chat(messages)

        # Parse
        json_str = response
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]
        start = json_str.find('{')
        end = json_str.rfind('}') + 1
        rec_data = json.loads(json_str[start:end].strip())

        vehicle_map = {v['vehicle_key']: v for v in vehicle_results}
        recommendations = []
        for r in rec_data.get("recommendations", [])[:3]:
            vid = r["vehicle_id"]
            if vid not in vehicle_map:
                continue
            vm = vehicle_map[vid]
            image_path = vm.get("image_path", "")
            image_filename = image_path.split("/")[-1] if image_path else ""
            maker = vm.get("vehicle_name", "").split()[0] if " " in vm.get("vehicle_name", "") else ""
            recommendations.append({
                "vehicle": {
                    "vehicle_id": vid,
                    "vehicle_key": vid,
                    "make": maker,
                    "maker": maker,
                    "model": vm.get("vehicle_name", ""),
                    "vehicle_name": vm.get("vehicle_name", ""),
                    "price": vm.get("price", 0),
                    "price_min": vm.get("price", 0),
                    "price_max": vm.get("price", 0),
                    "body_type": vm.get("body_type", ""),
                    "category": vm.get("body_type", ""),
                    "year": vm.get("model_year", ""),
                    "fuel_type": vm.get("fuel_type", ""),
                    "features": "",
                    "image_url": f"/api/images/{image_filename}" if image_filename else "",
                    "image_path": image_path,
                },
                "match_score": r["match_score"],
                "reason": r["reason"],
            })

        customer_aliased = _alias_row(customer)
        talk_script = await _generate_talk_script(customer_aliased, recommendations, interaction)

        return APIResponse(success=True, data={
            "customer_id": customer_id,
            "recommendations": recommendations,
            "talk_script": talk_script,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/customers/{customer_id}/recommendations/save", response_model=APIResponse)
async def save_recommendations(customer_id: str, body: dict) -> APIResponse:
    """Save generated recommendations to gd_recommendations table."""
    try:
        if USE_DEMO:
            return APIResponse(success=True, data={"message": "Demo mode: save skipped"})

        recs = body.get("recommendations", [])
        talk_script = body.get("talk_script", "")
        talk_escaped = talk_script.replace("'", "''")

        rec_table = get_full_table_name("gd_recommendations")
        await db.execute_query(
            f"DELETE FROM {rec_table} WHERE customer_id = '{customer_id}'"
        )

        # Get contact_name and sales_rep_name for this customer
        customers_table = get_full_table_name("sv_customers")
        cust_rows = await db.execute_query(
            f"SELECT contact_name, sales_rep_name FROM {customers_table} WHERE customer_id = '{customer_id}' LIMIT 1"
        )
        contact_name = (cust_rows[0].get("contact_name", "") if cust_rows else "").replace("'", "''")
        sales_rep_name = (cust_rows[0].get("sales_rep_name", "") if cust_rows else "").replace("'", "''")

        for rank, rec in enumerate(recs, 1):
            v = rec.get("vehicle", {})
            vehicle_key = (v.get("vehicle_key") or v.get("vehicle_id") or "").replace("'", "''")
            vehicle_name = v.get("vehicle_name", v.get("model", "")).replace("'", "''")
            match_score = rec.get("match_score", 0)
            reason = rec.get("reason", "").replace("'", "''")
            image_path = v.get("image_path", v.get("image_url", "")).replace("'", "''")
            key_selling_points = json.dumps([], ensure_ascii=False)
            # Only insert talk_script on first row
            ts = talk_escaped if rank == 1 else ""

            await db.execute_query(
                f"""INSERT INTO {rec_table}
                (customer_id, contact_name, sales_rep_name, rank, vehicle_key, vehicle_name, match_score,
                 recommendation_reason, talk_script, key_selling_points, image_path, generated_at)
                VALUES ('{customer_id}', '{contact_name}', '{sales_rep_name}', {rank}, '{vehicle_key}', '{vehicle_name}',
                        {match_score}, '{reason}', '{ts}', '{key_selling_points}', '{image_path}', current_timestamp())"""
            )

        return APIResponse(success=True, data={"message": "保存しました"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
