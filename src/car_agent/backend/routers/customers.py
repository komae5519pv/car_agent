"""Customer-related API endpoints with demo data support."""

import json
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from car_agent.backend.database import db
from car_agent.backend.llm import llm
from car_agent.backend.models import Customer, CustomerInsight, CustomerInteraction, APIResponse
from car_agent.backend.config import get_full_table_name
from car_agent.backend.demo_data import (
    get_all_demo_customers,
    get_demo_customer,
    get_demo_insight,
    get_demo_interaction,
)

router = APIRouter(prefix="/api/customers", tags=["customers"])

# Use demo data when DEMO_MODE is set or database is not configured
USE_DEMO = os.getenv("DEMO_MODE", "false").lower() == "true"

# sv_customers のカラム名 → フロントエンドが期待するカラム名へのマッピング
_COLUMN_ALIASES = {
    "contact_name": "name",
    "family_detail": "family_structure",
}

def _alias_row(row: dict) -> dict:
    """sv_customers のカラム名をフロントエンド互換に変換"""
    out = {}
    for k, v in row.items():
        out[_COLUMN_ALIASES.get(k, k)] = v
    return out


@router.get("", response_model=APIResponse)
async def list_customers(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    search: Optional[str] = None,
    sales_rep_name: Optional[str] = None,
) -> APIResponse:
    """Get list of customers with optional search."""
    try:
        if USE_DEMO:
            # Use demo data
            customers = get_all_demo_customers()

            # Apply search filter
            if search:
                search_lower = search.lower()
                customers = [
                    c for c in customers
                    if search_lower in c["name"].lower()
                    or search_lower in c.get("occupation", "").lower()
                ]

            # Apply pagination
            customers = customers[offset : offset + limit]

            return APIResponse(success=True, data=customers)

        # Use database
        table = get_full_table_name("sv_customers")
        conditions = []
        if search:
            conditions.append(f"(contact_name LIKE '%{search}%' OR occupation LIKE '%{search}%')")
        if sales_rep_name and sales_rep_name != "ALL":
            conditions.append(f"sales_rep_name = '{sales_rep_name}'")
        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        query = f"SELECT * FROM {table}{where} LIMIT {limit} OFFSET {offset}"

        results = await db.execute_query(query)
        return APIResponse(success=True, data=[_alias_row(r) for r in results])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}", response_model=APIResponse)
async def get_customer(customer_id: str) -> APIResponse:
    """Get customer by ID."""
    try:
        if USE_DEMO:
            customer = get_demo_customer(customer_id)
            if not customer:
                raise HTTPException(status_code=404, detail="Customer not found")
            return APIResponse(success=True, data=customer)

        table = get_full_table_name("sv_customers")
        query = f"SELECT * FROM {table} WHERE customer_id = '{customer_id}'"

        results = await db.execute_query(query)

        if not results:
            raise HTTPException(status_code=404, detail="Customer not found")

        return APIResponse(success=True, data=_alias_row(results[0]))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/interaction", response_model=APIResponse)
async def get_customer_interaction(customer_id: str) -> APIResponse:
    """Get customer interaction (conversation transcript)."""
    try:
        if USE_DEMO:
            interaction = get_demo_interaction(customer_id)
            if not interaction:
                raise HTTPException(status_code=404, detail="Interaction not found")
            return APIResponse(success=True, data=interaction)

        table = get_full_table_name("sv_interactions")
        results = await db.execute_query(
            f"SELECT * FROM {table} WHERE customer_id = '{customer_id}' ORDER BY interaction_date ASC"
        )

        if not results:
            raise HTTPException(status_code=404, detail="Interaction not found")

        # key_quotes_json から印象的な発言を取得（顧客単位で1回だけ）
        key_quotes: list = []
        insights_table = get_full_table_name("gd_customer_insights")
        try:
            ins_rows = await db.execute_query(
                f"SELECT key_quotes_json FROM {insights_table} WHERE customer_id = '{customer_id}' LIMIT 1"
            )
            if ins_rows and ins_rows[0].get("key_quotes_json"):
                key_quotes = json.loads(ins_rows[0]["key_quotes_json"])
        except Exception:
            pass

        interactions = []
        for row in results:
            row["transcript"] = row.get("content", "")
            row["key_quotes"] = key_quotes
            interactions.append(row)

        return APIResponse(success=True, data=interactions)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{customer_id}/insights", response_model=APIResponse)
async def get_customer_insights(customer_id: str) -> APIResponse:
    """Get AI-extracted insights for a customer."""
    try:
        if USE_DEMO:
            # Use pre-defined insights from demo data
            insight = get_demo_insight(customer_id)
            if insight:
                return APIResponse(success=True, data=insight)

        if not USE_DEMO:
            # Try to read pre-computed insights from gd_customer_insights
            insights_table = get_full_table_name("gd_customer_insights")
            insights_rows = await db.execute_query(
                f"SELECT * FROM {insights_table} WHERE customer_id = '{customer_id}' ORDER BY processed_at DESC LIMIT 1"
            )
            if insights_rows:
                row = insights_rows[0]
                # Parse JSON columns
                def _parse_json_list(val):
                    if not val:
                        return []
                    if isinstance(val, list):
                        return val
                    try:
                        return json.loads(val)
                    except Exception:
                        return [str(val)]

                deep_needs = _parse_json_list(row.get("deep_needs"))
                purchase_signals = _parse_json_list(row.get("purchase_signals"))
                urgency = row.get("purchase_urgency", "")
                urgency_reason = row.get("urgency_reason", "")
                purchase_intent = f"{urgency}：{urgency_reason}" if urgency_reason else urgency
                return APIResponse(success=True, data={
                    "needs": deep_needs,
                    "priorities": purchase_signals,
                    "avoid": [],
                    "purchase_intent": purchase_intent,
                    "key_insight": row.get("summary", ""),
                    "detected_keywords": [],
                    "decision_key": row.get("decision_key", ""),
                })

        # Get customer data (fallback: generate via LLM)
        if USE_DEMO:
            customer = get_demo_customer(customer_id)
            interaction = get_demo_interaction(customer_id)
        else:
            table = get_full_table_name("sv_customers")
            query = f"SELECT * FROM {table} WHERE customer_id = '{customer_id}'"
            results = await db.execute_query(query)

            if not results:
                raise HTTPException(status_code=404, detail="Customer not found")

            customer = results[0]
            interaction = None

        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")

        # Generate insights using LLM if no pre-defined insight
        transcript_text = ""
        if interaction and interaction.get("transcript"):
            transcript_text = f"\n\n商談録音テキスト:\n{interaction['transcript']}"

        prompt = f"""以下の顧客データを分析し、車両購入に関するインサイトを抽出してください。

顧客情報:
- 名前: {customer['name']}
- 年齢: {customer['age']}歳
- 職業: {customer.get('occupation', '不明')}
- 家族構成: {customer.get('family_structure', '不明')}
- 予算: {customer.get('budget_min', 0):,}円 〜 {customer.get('budget_max', 0):,}円
- 好み: {customer.get('preferences', 'なし')}
{transcript_text}

以下のJSON形式で回答してください:
{{
    "needs": ["ニーズ1", "ニーズ2", "ニーズ3", "ニーズ4"],
    "priorities": ["優先事項1", "優先事項2", "優先事項3"],
    "avoid": ["避けるべき要素1", "避けるべき要素2"],
    "purchase_intent": "購買意欲レベル（高/中/低）と理由の詳細説明",
    "key_insight": "この顧客の深層心理や本当のニーズについての洞察",
    "detected_keywords": ["印象的な発言1", "印象的な発言2"]
}}"""

        messages = [
            {"role": "system", "content": "あなたは自動車販売のエキスパートです。顧客の発言から深層心理を読み取り、的確なインサイトを提供してください。単なる表面的なニーズだけでなく、『なぜそれを求めているのか』という本質を見抜いてください。"},
            {"role": "user", "content": prompt}
        ]

        response = await llm.chat(messages)

        # Parse JSON response
        try:
            # Extract JSON from response (handle markdown code blocks)
            json_str = response
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]

            insights_data = json.loads(json_str.strip())
            return APIResponse(success=True, data=insights_data)
        except (json.JSONDecodeError, IndexError):
            # Fallback to default insights
            insights = {
                "needs": ["ファミリー向けの広い車内", "安全装備の充実", "燃費の良さ"],
                "priorities": ["安全性", "居住性", "経済性"],
                "avoid": ["スポーツカー", "2シーター"],
                "purchase_intent": "高（3ヶ月以内に購入予定）",
                "key_insight": "家族のための車選びを重視している",
                "detected_keywords": []
            }
            return APIResponse(success=True, data=insights)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

