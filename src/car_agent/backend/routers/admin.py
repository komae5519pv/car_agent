"""Admin API endpoints for monitoring and management.

MLflow TracingおよびServing Endpointの実際のデータ構造を反映したモックデータ。
LLMOps導入を検討している顧客へのデモ用。
"""

import uuid
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Request

from car_agent.backend.database import db
from car_agent.backend.models import (
    TraceRecord,
    GatewayMetrics,
    TableInfo,
    EvaluationRecord,
    EvaluationRequest,
    APIResponse,
)
from car_agent.backend.config import get_settings, get_full_table_name
from car_agent.backend.demo_data import DEMO_CUSTOMERS

router = APIRouter(prefix="/api/admin", tags=["admin"])

# =============================================================================
# MLflow Tracing モックデータ（実際のMLflow Trace構造を反映）
# =============================================================================
DEMO_TRACES = [
    {
        "trace_id": "tr-8f2a4b6c-1234-5678-9abc-def012345678",
        "request_id": "req-001",
        "timestamp_ms": int((datetime.now() - timedelta(minutes=5)).timestamp() * 1000),
        "status": "OK",
        "execution_time_ms": 1847,
        "request": {
            "messages": [
                {"role": "system", "content": "あなたは自動車販売のエキスパートです。顧客の深層ニーズを理解し、最適な車両を推薦してください。"},
                {"role": "user", "content": "以下の顧客に最適な車両を3台推薦してください。\n\n顧客情報:\n- 名前: 山田 優子\n- 年齢: 38歳\n- 職業: パート勤務（スーパー）\n- 家族構成: 夫（42歳・物流会社）、長女（小4）、長男（小1）、義母（72歳・同居）\n- 予算: 1,800,000円 〜 2,800,000円\n- 好み: 乗り降りしやすい、安全装備、運転しやすいサイズ\n\n商談録音テキスト:\n「義母も乗りやすいだろうし」「運転そんな上手くないんで大きい車だとちょっと不安」「アルファードとかママ友が乗ってて正直いいなーって思う」"}
            ],
            "model": "databricks-claude-sonnet-4",
            "max_tokens": 4096,
            "temperature": 0.7
        },
        "response": {
            "choices": [
                {
                    "message": {
                        "content": "{\n  \"recommendations\": [\n    {\n      \"vehicle_id\": \"V001\",\n      \"match_score\": 95,\n      \"reason\": \"シエンタは山田様の「義母の乗り降り」というお気持ちに最適です。低床設計で乗り降りが楽、コンパクトなのに3列シートで急な送迎にも対応。\"\n    },\n    {\n      \"vehicle_id\": \"V002\",\n      \"match_score\": 92,\n      \"reason\": \"フリードもシエンタと同様に低床フロアで乗り降り楽々。Honda SENSINGの安全装備は定評があります。\"\n    }\n  ]\n}"
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 1523,
                "completion_tokens": 324,
                "total_tokens": 1847
            }
        },
        "spans": [
            {
                "span_id": "span-001",
                "name": "ChatCompletion",
                "parent_span_id": None,
                "start_time_ms": 0,
                "end_time_ms": 1847,
                "status": "OK",
                "attributes": {
                    "llm.model": "databricks-claude-sonnet-4",
                    "llm.token_count.prompt": 1523,
                    "llm.token_count.completion": 324
                }
            }
        ],
        "tags": {
            "mlflow.traceName": "vehicle_recommendation",
            "application": "car-agent",
            "customer_id": "C001"
        }
    },
    {
        "trace_id": "tr-9e3b5c7d-2345-6789-abcd-ef0123456789",
        "request_id": "req-002",
        "timestamp_ms": int((datetime.now() - timedelta(minutes=12)).timestamp() * 1000),
        "status": "OK",
        "execution_time_ms": 2134,
        "request": {
            "messages": [
                {"role": "system", "content": "あなたは自動車販売のエキスパートです。"},
                {"role": "user", "content": "以下の顧客に最適な車両を3台推薦してください。\n\n顧客情報:\n- 名前: 佐藤 健一\n- 年齢: 52歳\n- 職業: 中堅メーカー 営業部長\n- 予算: 3,000,000円 〜 4,500,000円\n- 好み: ある程度の格、ゴルフバッグが積める"}
            ],
            "model": "databricks-claude-sonnet-4",
            "max_tokens": 4096,
            "temperature": 0.7
        },
        "response": {
            "choices": [
                {
                    "message": {
                        "content": "{\n  \"recommendations\": [\n    {\"vehicle_id\": \"V005\", \"match_score\": 94, \"reason\": \"ハリアーは営業部長としての格とスポーツカーへの憧れを両立できます。\"}\n  ]\n}"
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 1821,
                "completion_tokens": 313,
                "total_tokens": 2134
            }
        },
        "spans": [
            {
                "span_id": "span-002",
                "name": "ChatCompletion",
                "parent_span_id": None,
                "start_time_ms": 0,
                "end_time_ms": 2134,
                "status": "OK",
                "attributes": {
                    "llm.model": "databricks-claude-sonnet-4",
                    "llm.token_count.prompt": 1821,
                    "llm.token_count.completion": 313
                }
            }
        ],
        "tags": {
            "mlflow.traceName": "vehicle_recommendation",
            "application": "car-agent",
            "customer_id": "C002"
        }
    },
    {
        "trace_id": "tr-af4c6d8e-3456-789a-bcde-f01234567890",
        "request_id": "req-003",
        "timestamp_ms": int((datetime.now() - timedelta(minutes=25)).timestamp() * 1000),
        "status": "OK",
        "execution_time_ms": 956,
        "request": {
            "messages": [
                {"role": "system", "content": "あなたは自動車販売アシスタントです。"},
                {"role": "user", "content": "ヴェゼルの燃費について教えてください"}
            ],
            "model": "databricks-claude-sonnet-4",
            "max_tokens": 2048,
            "temperature": 0.7
        },
        "response": {
            "choices": [
                {
                    "message": {
                        "content": "ホンダ ヴェゼルの燃費についてご説明します。\n\ne:HEV（ハイブリッド）モデルの場合、WLTCモード燃費は約24.8km/Lと非常に優秀です。特に市街地モードでは25.0km/L以上を記録することもあります。\n\nガソリンモデル（G）の場合は、WLTCモードで約17.0km/Lとなります。\n\n実燃費としては、e:HEVで20-22km/L程度、ガソリンモデルで14-16km/L程度が目安になります。"
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 234,
                "completion_tokens": 189,
                "total_tokens": 423
            }
        },
        "spans": [
            {
                "span_id": "span-003",
                "name": "ChatCompletion",
                "parent_span_id": None,
                "start_time_ms": 0,
                "end_time_ms": 956,
                "status": "OK",
                "attributes": {
                    "llm.model": "databricks-claude-sonnet-4",
                    "llm.token_count.prompt": 234,
                    "llm.token_count.completion": 189
                }
            }
        ],
        "tags": {
            "mlflow.traceName": "chat_completion",
            "application": "car-agent",
            "session_id": "sess-abc123"
        }
    },
    {
        "trace_id": "tr-bg5d7e9f-4567-89ab-cdef-012345678901",
        "request_id": "req-004",
        "timestamp_ms": int((datetime.now() - timedelta(minutes=38)).timestamp() * 1000),
        "status": "ERROR",
        "execution_time_ms": 30250,
        "error": {
            "error_code": "RATE_LIMIT_EXCEEDED",
            "message": "Rate limit exceeded: Too many requests. Please retry after 60 seconds.",
            "details": {
                "retry_after_ms": 60000,
                "current_rpm": 125,
                "limit_rpm": 100
            }
        },
        "request": {
            "messages": [
                {"role": "system", "content": "あなたは自動車販売のエキスパートです。"},
                {"role": "user", "content": "バッチ処理: 50件の顧客に対する推薦を生成してください..."}
            ],
            "model": "databricks-claude-sonnet-4",
            "max_tokens": 8192,
            "temperature": 0.7
        },
        "response": None,
        "spans": [
            {
                "span_id": "span-004",
                "name": "ChatCompletion",
                "parent_span_id": None,
                "start_time_ms": 0,
                "end_time_ms": 30250,
                "status": "ERROR",
                "attributes": {
                    "llm.model": "databricks-claude-sonnet-4",
                    "error.type": "RateLimitError"
                }
            }
        ],
        "tags": {
            "mlflow.traceName": "batch_recommendation",
            "application": "car-agent",
            "batch_job_id": "job-batch-001"
        }
    },
    {
        "trace_id": "tr-ch6e8f0g-5678-9abc-def0-123456789012",
        "request_id": "req-005",
        "timestamp_ms": int((datetime.now() - timedelta(minutes=45)).timestamp() * 1000),
        "status": "OK",
        "execution_time_ms": 1523,
        "request": {
            "messages": [
                {"role": "system", "content": "顧客との会話から深層ニーズを抽出してください。"},
                {"role": "user", "content": "会話テキスト: 「子供が2人いて、上が小4で下が小1なんですけど、習い事とか送り迎えがすごい多くて。あと義母も一緒に住んでて、足が悪いわけじゃないんですけどまあ歳なんで病院とか連れてったりとか。だから乗り降りしやすい車がいいなって。アルファードとかママ友が乗ってて正直いいなーって思うんですけどさすがに予算が...」"}
            ],
            "model": "databricks-claude-sonnet-4",
            "max_tokens": 2048,
            "temperature": 0.5
        },
        "response": {
            "choices": [
                {
                    "message": {
                        "content": "{\n  \"needs\": [\n    \"義母の乗り降りがしやすい低床設計の車\",\n    \"子供2人の習い事送迎に便利な使い勝手\",\n    \"運転に自信がなくても扱いやすいサイズ\"\n  ],\n  \"priorities\": [\"乗り降りのしやすさ\", \"安全装備\", \"運転しやすさ\"],\n  \"avoid\": [\"大きすぎる車\", \"高額な維持費\"],\n  \"key_insight\": \"表面的には『広さ』を求めているが、本質は義母への気遣いと自身の運転への不安。アルファードへの憧れはあるが現実的な選択を理解している。\"\n}"
                    }
                }
            ],
            "usage": {
                "prompt_tokens": 892,
                "completion_tokens": 267,
                "total_tokens": 1159
            }
        },
        "spans": [
            {
                "span_id": "span-005",
                "name": "ChatCompletion",
                "parent_span_id": None,
                "start_time_ms": 0,
                "end_time_ms": 1523,
                "status": "OK",
                "attributes": {
                    "llm.model": "databricks-claude-sonnet-4",
                    "llm.token_count.prompt": 892,
                    "llm.token_count.completion": 267
                }
            }
        ],
        "tags": {
            "mlflow.traceName": "insight_extraction",
            "application": "car-agent",
            "customer_id": "C001"
        }
    },
]

# =============================================================================
# Serving Endpoint メトリクス（時系列データ）
# =============================================================================
def _generate_timeseries_metrics():
    """過去1時間の時系列メトリクスを生成"""
    now = datetime.now()
    data_points = []
    for i in range(60):  # 過去60分
        ts = now - timedelta(minutes=59-i)
        # リアルな変動パターン
        base_rpm = 45 + (i % 10) * 2  # 基本RPM
        spike = 20 if i in [15, 30, 45] else 0  # スパイク
        data_points.append({
            "timestamp": ts.isoformat(),
            "requests_per_minute": base_rpm + spike + (i % 5),
            "avg_latency_ms": 800 + (i % 20) * 30,
            "p50_latency_ms": 650 + (i % 15) * 20,
            "p95_latency_ms": 1200 + (i % 25) * 50,
            "p99_latency_ms": 1800 + (i % 30) * 60,
            "error_count": 1 if i in [22, 38] else 0,
            "token_throughput": (base_rpm + spike) * 1500,
        })
    return data_points

# =============================================================================
# 評価データ（MLflow Evaluation形式）
# =============================================================================
DEMO_EVALUATIONS = [
    {
        "evaluation_id": "eval-001",
        "trace_id": "tr-8f2a4b6c-1234-5678-9abc-def012345678",
        "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
        "input_preview": "顧客: 山田優子（38歳）義母同居、予算180-280万",
        "output_preview": "推薦: シエンタ(95%), フリード(92%)",
        "rating": 5,
        "feedback": "顧客の『義母の乗り降り』という隠れたニーズを的確に捉え、低床設計のシエンタを推薦したのは素晴らしい。商談録音の「義母も乗りやすいだろうし」という発言を根拠に使っている点も良い。",
        "evaluator": "sales_manager_01",
        "metrics": {
            "relevance": 5,
            "faithfulness": 5,
            "helpfulness": 4
        }
    },
    {
        "evaluation_id": "eval-002",
        "trace_id": "tr-9e3b5c7d-2345-6789-abcd-ef0123456789",
        "timestamp": (datetime.now() - timedelta(hours=5)).isoformat(),
        "input_preview": "顧客: 佐藤健一（52歳）営業部長、予算300-450万",
        "output_preview": "推薦: ハリアー(94%)",
        "rating": 4,
        "feedback": "予算に合った車両を推薦できている。「営業部長としての格」を理解している点は良いが、ゴルフバッグの積載性についてもう少し言及があると良かった。",
        "evaluator": "sales_manager_02",
        "metrics": {
            "relevance": 4,
            "faithfulness": 5,
            "helpfulness": 4
        },
        "ground_truth": "ハリアーのラゲッジスペースは456Lで、ゴルフバッグ2個と同乗者の荷物が余裕で入ることを伝えるべき"
    },
    {
        "evaluation_id": "eval-003",
        "trace_id": "tr-ch6e8f0g-5678-9abc-def0-123456789012",
        "timestamp": (datetime.now() - timedelta(hours=8)).isoformat(),
        "input_preview": "インサイト抽出: 山田優子の商談録音",
        "output_preview": "ニーズ: 義母の乗り降り、子供の送迎、運転への不安",
        "rating": 5,
        "feedback": "商談録音から「所帯じみた車は嫌」という潜在ニーズを読み取れていないが、表層ニーズは正確に抽出できている。",
        "evaluator": "sales_manager_01",
        "metrics": {
            "relevance": 4,
            "faithfulness": 5,
            "helpfulness": 5
        }
    },
]


# MLflow Traces
@router.get("/traces", response_model=APIResponse)
async def list_traces(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = None,
) -> APIResponse:
    """Get list of MLflow traces.

    本番環境では MLflow Tracking Server API を使用:
    GET /api/2.0/mlflow/traces?experiment_ids=...
    """
    try:
        traces = DEMO_TRACES.copy()

        # フィルタリング
        if status:
            traces = [t for t in traces if t["status"] == status]

        # ページネーション
        traces = traces[offset:offset + limit]

        return APIResponse(success=True, data=traces)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/traces/{trace_id}", response_model=APIResponse)
async def get_trace(trace_id: str) -> APIResponse:
    """Get trace details by ID.

    本番環境では MLflow Tracking Server API を使用:
    GET /api/2.0/mlflow/traces/{trace_id}
    """
    try:
        for trace in DEMO_TRACES:
            if trace["trace_id"] == trace_id:
                return APIResponse(success=True, data=trace)

        raise HTTPException(status_code=404, detail="Trace not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# AI Gateway / Serving Endpoint Metrics
@router.get("/gateway/metrics", response_model=APIResponse)
async def get_gateway_metrics() -> APIResponse:
    """Get Serving Endpoint metrics.

    本番環境では Databricks REST API を使用:
    GET /api/2.0/serving-endpoints/{name}/metrics
    """
    try:
        settings = get_settings()

        # サービングエンドポイント情報
        endpoint_info = {
            "name": settings.llm_model,
            "state": "READY",
            "creator": "konomi.omae@databricks.com",
            "creation_timestamp": int((datetime.now() - timedelta(days=30)).timestamp() * 1000),
            "last_updated_timestamp": int((datetime.now() - timedelta(hours=2)).timestamp() * 1000),
            "config": {
                "served_models": [
                    {
                        "name": "claude-sonnet-4",
                        "model_name": "databricks-claude-sonnet-4",
                        "model_version": "1",
                        "workload_size": "Small",
                        "scale_to_zero_enabled": False,
                        "min_provisioned_throughput": 0,
                        "max_provisioned_throughput": 10000
                    }
                ],
                "traffic_config": {
                    "routes": [
                        {"served_model_name": "claude-sonnet-4", "traffic_percentage": 100}
                    ]
                }
            },
            "pending_config": None
        }

        # 時系列メトリクス
        timeseries = _generate_timeseries_metrics()

        # 現在のサマリー（直近5分の平均）
        recent = timeseries[-5:]
        current_summary = {
            "requests_per_minute": sum(d["requests_per_minute"] for d in recent) / 5,
            "avg_latency_ms": sum(d["avg_latency_ms"] for d in recent) / 5,
            "p50_latency_ms": sum(d["p50_latency_ms"] for d in recent) / 5,
            "p95_latency_ms": sum(d["p95_latency_ms"] for d in recent) / 5,
            "p99_latency_ms": sum(d["p99_latency_ms"] for d in recent) / 5,
            "error_rate": sum(d["error_count"] for d in recent) / sum(d["requests_per_minute"] for d in recent) if sum(d["requests_per_minute"] for d in recent) > 0 else 0,
            "total_requests_1h": sum(d["requests_per_minute"] for d in timeseries),
            "total_tokens_1h": sum(d["token_throughput"] for d in timeseries),
            "estimated_cost_1h_usd": sum(d["token_throughput"] for d in timeseries) * 0.000015  # $0.015/1K tokens
        }

        return APIResponse(success=True, data={
            "endpoint": endpoint_info,
            "current": current_summary,
            "timeseries": timeseries
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Unity Catalog
@router.get("/catalog/tables", response_model=APIResponse)
async def list_catalog_tables() -> APIResponse:
    """Get list of tables in Unity Catalog."""
    try:
        settings = get_settings()

        # Demo table info
        tables = [
            TableInfo(
                catalog=settings.catalog,
                schema_name=settings.schema_name,
                table_name="customers",
                table_type="MANAGED",
                row_count=1500,
                columns=[
                    {"name": "customer_id", "type": "STRING"},
                    {"name": "name", "type": "STRING"},
                    {"name": "age", "type": "INT"},
                    {"name": "occupation", "type": "STRING"},
                    {"name": "family_structure", "type": "STRING"},
                    {"name": "budget_min", "type": "INT"},
                    {"name": "budget_max", "type": "INT"},
                    {"name": "preferences", "type": "STRING"},
                ]
            ),
            TableInfo(
                catalog=settings.catalog,
                schema_name=settings.schema_name,
                table_name="vehicles",
                table_type="MANAGED",
                row_count=850,
                columns=[
                    {"name": "vehicle_id", "type": "STRING"},
                    {"name": "make", "type": "STRING"},
                    {"name": "model", "type": "STRING"},
                    {"name": "year", "type": "INT"},
                    {"name": "mileage", "type": "INT"},
                    {"name": "price", "type": "INT"},
                    {"name": "body_type", "type": "STRING"},
                    {"name": "fuel_type", "type": "STRING"},
                ]
            ),
            TableInfo(
                catalog=settings.catalog,
                schema_name=settings.schema_name,
                table_name="recommendations",
                table_type="MANAGED",
                row_count=5200,
                columns=[
                    {"name": "recommendation_id", "type": "STRING"},
                    {"name": "customer_id", "type": "STRING"},
                    {"name": "vehicle_id", "type": "STRING"},
                    {"name": "match_score", "type": "FLOAT"},
                    {"name": "reason", "type": "STRING"},
                    {"name": "created_at", "type": "TIMESTAMP"},
                ]
            ),
        ]

        return APIResponse(success=True, data=[t.model_dump() for t in tables])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/catalog/tables/{table_name}/preview", response_model=APIResponse)
async def preview_table(
    table_name: str,
    limit: int = Query(default=10, le=100),
) -> APIResponse:
    """Get preview data from a table."""
    try:
        full_table = get_full_table_name(table_name)
        query = f"SELECT * FROM {full_table} LIMIT {limit}"
        results = await db.execute_query(query)
        return APIResponse(success=True, data=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Evaluations
@router.get("/evaluations", response_model=APIResponse)
async def list_evaluations(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
) -> APIResponse:
    """Get list of evaluations with trace context.

    本番環境では MLflow Model Evaluation API または Delta テーブルから取得:
    - mlflow.evaluate() 結果
    - カスタム評価テーブル
    """
    try:
        # 評価サマリー統計
        all_ratings = [e["rating"] for e in DEMO_EVALUATIONS]
        summary = {
            "total_evaluations": len(DEMO_EVALUATIONS),
            "avg_rating": sum(all_ratings) / len(all_ratings) if all_ratings else 0,
            "rating_distribution": {
                "5": sum(1 for r in all_ratings if r == 5),
                "4": sum(1 for r in all_ratings if r == 4),
                "3": sum(1 for r in all_ratings if r == 3),
                "2": sum(1 for r in all_ratings if r == 2),
                "1": sum(1 for r in all_ratings if r == 1),
            },
            "with_ground_truth": sum(1 for e in DEMO_EVALUATIONS if e.get("ground_truth")),
        }

        # ページネーション適用
        evaluations = DEMO_EVALUATIONS[offset:offset + limit]

        return APIResponse(success=True, data={
            "summary": summary,
            "evaluations": evaluations
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# In-memory store for dynamically created evaluations (trace_id → evaluation dict)
# PRODUCTION: Replace with:
#   INSERT INTO {catalog}.{schema}.human_evaluations (trace_id, rating, feedback, ground_truth, evaluator, evaluated_at)
#   VALUES (:trace_id, :rating, :feedback, :ground_truth, :evaluator, NOW())
_created_evaluations: dict[str, dict] = {}


@router.post("/evaluations", response_model=APIResponse)
async def create_evaluation(body: EvaluationRequest, http_request: Request) -> APIResponse:
    """Create a new evaluation.

    PRODUCTION IMPLEMENTATION:
      await db.execute_query(
          f"INSERT INTO {catalog}.{schema}.human_evaluations VALUES (:trace_id, :rating, ...)",
          params={...}
      )
    """
    try:
        # Databricks Apps injects the authenticated user's email via X-Forwarded-Email header.
        # PRODUCTION: same header works in production. Falls back to username or default.
        evaluator = (
            http_request.headers.get("X-Forwarded-Email")
            or http_request.headers.get("X-Forwarded-User")
            or "admin"
        )
        evaluation = {
            "rating": body.rating,
            "feedback": body.feedback or "",
            "ground_truth": body.ground_truth,
            "evaluator": evaluator,
            "evaluated_at": datetime.now(JST).isoformat(),
        }
        _created_evaluations[body.trace_id] = evaluation

        return APIResponse(success=True, data=evaluation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# 統合品質ログ（MLflow Tracing + LLM Judge スコア + 人間評価）
# =============================================================================
# PRODUCTION IMPLEMENTATION:
#   本番環境では以下のデータソースを統合して取得:
#   1. MLflow Traces:
#      GET {DATABRICKS_HOST}/api/2.0/mlflow/traces
#      params: experiment_ids, filter_string="tags.application='car-agent'", max_results, page_token
#
#   2. LLM Judge スコア（mlflow.evaluate() が Delta table に保存）:
#      query = f"SELECT * FROM {catalog}.{schema}.llm_judge_scores WHERE trace_id IN (...)"
#      await db.execute_query(query)
#
#   3. Inference Tables（全リクエスト記録）:
#      table = f"`{catalog}`.`{schema}`.`{endpoint_name}_payload`"
#      query = f"SELECT * FROM {table} ORDER BY timestamp DESC LIMIT {limit} OFFSET {offset}"
#
#   4. 人間評価テーブル:
#      query = f"SELECT * FROM {catalog}.{schema}.human_evaluations WHERE trace_id IN (...)"
#
#   接続切り替え: DATABRICKS_WAREHOUSE_ID 環境変数を設定し、
#   database.execute_query() を使用してクエリを実行。
# =============================================================================
_q = datetime.now()

DEMO_QUALITY_LOGS = [
    # QL-001: 正常ケース - 山田優子の車両推薦（高スコア）
    {
        "id": "ql-001",
        "trace_id": "tr-8f2a4b6c-1234-5678-9abc-def012345678",
        "timestamp": (_q - timedelta(minutes=5)).isoformat(),
        "trace_type": "vehicle_recommendation",
        "customer_id": "C001",
        "customer_name": "山田優子",
        "question": "山田優子（38歳）義母同居・子供2人・予算180-280万円の最適車両を推薦してください",
        "answer": "【第1推薦】シエンタ(マッチ度95%) 義母の乗り降りに最適な低床設計。【第2推薦】フリード(92%) Honda SENSINGで安全性◎。",
        "execution_time_ms": 1847,
        "tokens": {"prompt": 1523, "completion": 324, "total": 1847},
        "status": "OK",
        "needs_review": False,
        "judge_scores": {"relevance": 5.0, "faithfulness": 4.5, "helpfulness": 4.5, "overall": 4.7},
        "judge_reasoning": (
            "顧客の商談録音から『義母も乗りやすいだろうし』という発言を根拠にシエンタ（低床設計）を"
            "第一推薦としており、深層ニーズの把握が優れています。推薦車両はすべて予算内（188〜270万円）"
            "に収まっており、顧客データへの忠実性も高い。予算・家族構成・使用シーン全ての制約を満たしています。"
        ),
        "spans": [
            {
                "span_id": "sp-001-a", "name": "retrieve_customer_data",
                "parent_span_id": None, "start_time_ms": 0, "end_time_ms": 185, "status": "OK",
                "attributes": {"customer_id": "C001", "budget_min": 1800000, "budget_max": 2800000,
                               "family_structure": "夫・長女(小4)・長男(小1)・義母(72歳)",
                               "retrieved_fields": "name, age, budget_min, budget_max, family_structure, preferences"},
            },
            {
                "span_id": "sp-001-b", "name": "search_vehicle_inventory",
                "parent_span_id": "sp-001-a", "start_time_ms": 185, "end_time_ms": 412, "status": "OK",
                "attributes": {"filter": "price BETWEEN 1800000 AND 2800000", "results_count": 23},
            },
            {
                "span_id": "sp-001-c", "name": "ChatCompletion",
                "parent_span_id": "sp-001-a", "start_time_ms": 412, "end_time_ms": 1847, "status": "OK",
                "attributes": {"llm.model": "databricks-claude-sonnet-4",
                               "llm.token_count.prompt": 1523, "llm.token_count.completion": 324},
            },
        ],
        "human_evaluation": {
            "rating": 5,
            "feedback": "義母の乗り降りという隠れたニーズを的確に捉え、商談録音の発言を根拠として使っている点が素晴らしい。",
            "ground_truth": None,
            "evaluator": "sales_manager_01",
            "evaluated_at": (_q - timedelta(hours=2)).isoformat(),
        },
    },

    # QL-002: 要対応 - 松本あかねへの予算オーバー推薦（低スコア）← デモのメインストーリー
    {
        "id": "ql-002",
        "trace_id": "tr-fail-budget-2a3b4c5d-6789",
        "timestamp": (_q - timedelta(minutes=42)).isoformat(),
        "trace_type": "vehicle_recommendation",
        "customer_id": "C008",
        "customer_name": "松本あかね",
        "question": "松本あかね（26歳・独身OL）予算150-220万円の最適車両を推薦してください",
        "answer": "【第1推薦】ハリアー(マッチ度91%) 洗練されたデザインと上質な内装が人気。【第2推薦】レクサスRX(88%)。",
        "execution_time_ms": 2145,
        "tokens": {"prompt": 1289, "completion": 312, "total": 1601},
        "status": "OK",
        "needs_review": True,
        "judge_scores": {"relevance": 4.0, "faithfulness": 1.5, "helpfulness": 1.5, "overall": 2.3},
        "judge_reasoning": (
            "【問題検出】推薦されたハリアー（332〜438万円）とレクサスRX（550万円〜）は"
            "いずれも顧客の予算上限（220万円）を大幅に超えています。\n"
            "【原因分析】retrieve_customer_dataスパンでは budget_max=2,200,000 が正しく取得されていますが、"
            "search_vehicle_inventoryスパンで予算フィルターが適用されておらず、全車両が候補に含まれています。"
            "その結果、ChatCompletionに予算外車両が渡されました。\n"
            "【推奨アクション】search_vehicle_inventoryの検索クエリに "
            "「price BETWEEN budget_min AND budget_max」フィルターを追加してください。"
        ),
        "spans": [
            {
                "span_id": "sp-002-a", "name": "retrieve_customer_data",
                "parent_span_id": None, "start_time_ms": 0, "end_time_ms": 198, "status": "OK",
                "attributes": {"customer_id": "C008", "budget_min": 1500000, "budget_max": 2200000,
                               "family_structure": "独身",
                               "retrieved_fields": "name, age, budget_min, budget_max, family_structure, preferences"},
            },
            {
                "span_id": "sp-002-b", "name": "search_vehicle_inventory",
                "parent_span_id": "sp-002-a", "start_time_ms": 198, "end_time_ms": 389, "status": "WARNING",
                "attributes": {"filter": "price > 0",
                               "results_count": 45,
                               "warning": "予算フィルター未適用: budget_max=2,200,000 が検索クエリに反映されていません"},
            },
            {
                "span_id": "sp-002-c", "name": "ChatCompletion",
                "parent_span_id": "sp-002-a", "start_time_ms": 389, "end_time_ms": 2145, "status": "OK",
                "attributes": {"llm.model": "databricks-claude-sonnet-4",
                               "llm.token_count.prompt": 1289, "llm.token_count.completion": 312,
                               "warning": "推薦車両が顧客の予算上限を超過しています"},
            },
        ],
        "human_evaluation": None,
    },

    # QL-003: 正常ケース - 佐藤健一の推薦（良スコア、軽微な改善余地）
    {
        "id": "ql-003",
        "trace_id": "tr-9e3b5c7d-2345-6789-abcd-ef0123456789",
        "timestamp": (_q - timedelta(minutes=12)).isoformat(),
        "trace_type": "vehicle_recommendation",
        "customer_id": "C002",
        "customer_name": "佐藤健一",
        "question": "佐藤健一（52歳・営業部長）予算300-450万・格があってゴルフバッグが積める車を推薦してください",
        "answer": "【第1推薦】ハリアー(マッチ度94%) 営業部長としての格とスポーツカーへの憧れを両立できます。",
        "execution_time_ms": 2134,
        "tokens": {"prompt": 1821, "completion": 313, "total": 2134},
        "status": "OK",
        "needs_review": False,
        "judge_scores": {"relevance": 4.5, "faithfulness": 4.5, "helpfulness": 4.0, "overall": 4.3},
        "judge_reasoning": (
            "予算に合った車両を推薦できており、営業部長としての格という要求も理解されています。"
            "ただし、ゴルフバッグの積載性（ハリアー: 456L）についての具体的な言及が薄く、"
            "顧客の明示的な要求に対してもう少し詳しく答えることができた点が改善余地です。"
        ),
        "spans": [
            {
                "span_id": "sp-003-a", "name": "retrieve_customer_data",
                "parent_span_id": None, "start_time_ms": 0, "end_time_ms": 201, "status": "OK",
                "attributes": {"customer_id": "C002", "budget_min": 3000000, "budget_max": 4500000,
                               "preferences": "格、ゴルフバッグが積める"},
            },
            {
                "span_id": "sp-003-b", "name": "search_vehicle_inventory",
                "parent_span_id": "sp-003-a", "start_time_ms": 201, "end_time_ms": 389, "status": "OK",
                "attributes": {"filter": "price BETWEEN 3000000 AND 4500000", "results_count": 18},
            },
            {
                "span_id": "sp-003-c", "name": "ChatCompletion",
                "parent_span_id": "sp-003-a", "start_time_ms": 389, "end_time_ms": 2134, "status": "OK",
                "attributes": {"llm.model": "databricks-claude-sonnet-4",
                               "llm.token_count.prompt": 1821, "llm.token_count.completion": 313},
            },
        ],
        "human_evaluation": {
            "rating": 4,
            "feedback": "予算に合った推薦ができている。ゴルフバッグの積載性についてもう少し言及があると良かった。",
            "ground_truth": "ハリアーのラゲッジスペースは456Lで、ゴルフバッグ2個と同乗者の荷物が余裕で入ることを伝えるべき",
            "evaluator": "sales_manager_02",
            "evaluated_at": (_q - timedelta(hours=5)).isoformat(),
        },
    },

    # QL-004: 正常ケース - ヴェゼルの燃費チャット（高スコア）
    {
        "id": "ql-004",
        "trace_id": "tr-af4c6d8e-3456-789a-bcde-f01234567890",
        "timestamp": (_q - timedelta(minutes=25)).isoformat(),
        "trace_type": "chat_completion",
        "customer_id": None,
        "customer_name": None,
        "question": "ヴェゼルの燃費について教えてください",
        "answer": "ホンダ ヴェゼルe:HEVのWLTCモード燃費は約24.8km/L。市街地では25.0km/L以上も。実燃費は20-22km/L程度が目安です。",
        "execution_time_ms": 956,
        "tokens": {"prompt": 234, "completion": 189, "total": 423},
        "status": "OK",
        "needs_review": False,
        "judge_scores": {"relevance": 5.0, "faithfulness": 4.5, "helpfulness": 4.5, "overall": 4.7},
        "judge_reasoning": (
            "質問に対して正確な燃費情報（WLTCモード・実燃費）を提供しています。"
            "e:HEVとガソリンモデルの違いも明確に説明されており、数値は実際のスペックと一致しています。"
        ),
        "spans": [
            {
                "span_id": "sp-004-a", "name": "knowledge_retrieval",
                "parent_span_id": None, "start_time_ms": 0, "end_time_ms": 134, "status": "OK",
                "attributes": {"query": "ヴェゼル 燃費 WLTCモード", "retrieved_documents": 3, "top_score": 0.94},
            },
            {
                "span_id": "sp-004-b", "name": "ChatCompletion",
                "parent_span_id": "sp-004-a", "start_time_ms": 134, "end_time_ms": 956, "status": "OK",
                "attributes": {"llm.model": "databricks-claude-sonnet-4",
                               "llm.token_count.prompt": 234, "llm.token_count.completion": 189},
            },
        ],
        "human_evaluation": None,
    },

    # QL-005: 正常ケース - インサイト抽出（高スコア）
    {
        "id": "ql-005",
        "trace_id": "tr-ch6e8f0g-5678-9abc-def0-123456789012",
        "timestamp": (_q - timedelta(minutes=45)).isoformat(),
        "trace_type": "insight_extraction",
        "customer_id": "C001",
        "customer_name": "山田優子",
        "question": "商談録音から山田優子の深層ニーズを抽出してください",
        "answer": "主要ニーズ: ①義母の乗り降りしやすさ ②子供2人の送迎 ③コンパクトで運転しやすいサイズ。核心: アルファードへの憧れと予算の現実を理解した上での選択。",
        "execution_time_ms": 1523,
        "tokens": {"prompt": 892, "completion": 267, "total": 1159},
        "status": "OK",
        "needs_review": False,
        "judge_scores": {"relevance": 5.0, "faithfulness": 5.0, "helpfulness": 4.5, "overall": 4.8},
        "judge_reasoning": (
            "商談録音のテキストから複数の深層ニーズを正確に抽出しています。"
            "アルファードへの憧れと予算の現実を理解した上での分析は高品質で、"
            "抽出されたニーズは推薦ロジックに直接活用可能な形式です。"
        ),
        "spans": [
            {
                "span_id": "sp-005-a", "name": "ChatCompletion",
                "parent_span_id": None, "start_time_ms": 0, "end_time_ms": 1523, "status": "OK",
                "attributes": {"llm.model": "databricks-claude-sonnet-4",
                               "llm.token_count.prompt": 892, "llm.token_count.completion": 267},
            },
        ],
        "human_evaluation": None,
    },
]


@router.get("/quality", response_model=APIResponse)
async def list_quality_logs(
    filter: Optional[str] = Query(default=None, description="needs_review | ok"),
    evaluated: Optional[str] = Query(default=None, description="yes | no"),
    evaluator: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    trace_type: Optional[str] = Query(default=None),
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
) -> APIResponse:
    """統合品質ログ: MLflow Tracing + LLM Judge スコア + 人間評価 を結合して返す。

    PRODUCTION IMPLEMENTATION:
      デモモード以外では以下のデータソースを統合:
        - MLflow Traces: GET /api/2.0/mlflow/traces?experiment_ids=...&max_results={limit}
        - LLM Judge スコア: SELECT * FROM {catalog}.{schema}.llm_judge_scores WHERE trace_id IN (...)
        - Inference Tables: SELECT * FROM `{catalog}`.`{schema}`.`{endpoint_name}_payload` ORDER BY timestamp DESC
        - 人間評価: SELECT * FROM {catalog}.{schema}.human_evaluations WHERE trace_id IN (...)
      フィルタ・検索はSQLのWHERE句で代替。
      接続切り替え: DATABRICKS_WAREHOUSE_ID を設定し database.execute_query() を使用。
    """
    # 評価をマージしてから全フィルタを適用
    # PRODUCTION: SQLのJOINで代替
    #   SELECT q.*, e.* FROM quality_logs q LEFT JOIN human_evaluations e ON q.trace_id = e.trace_id
    all_merged = []
    for log in DEMO_QUALITY_LOGS:
        if log["trace_id"] in _created_evaluations:
            log = {**log, "human_evaluation": _created_evaluations[log["trace_id"]]}
        all_merged.append(log)

    logs = all_merged.copy()

    # 品質フィルタ
    if filter == "needs_review":
        logs = [l for l in logs if l["needs_review"]]
    elif filter == "ok":
        logs = [l for l in logs if not l["needs_review"]]

    # 評価済みフィルタ
    if evaluated == "yes":
        logs = [l for l in logs if l.get("human_evaluation") is not None]
    elif evaluated == "no":
        logs = [l for l in logs if l.get("human_evaluation") is None]

    # 担当者フィルタ
    if evaluator:
        logs = [l for l in logs
                if l.get("human_evaluation") and l["human_evaluation"].get("evaluator") == evaluator]

    # トレースタイプフィルタ
    if trace_type:
        logs = [l for l in logs if l["trace_type"] == trace_type]

    # テキスト検索（顧客名 / 質問文）
    if search:
        q = search.lower()
        logs = [l for l in logs if
                q in (l.get("customer_name") or "").lower() or
                q in l.get("question", "").lower() or
                q in l.get("answer", "").lower()]

    # サマリー（フィルタ前の全件から計算）
    # alert_count = LLM Judgeが要対応フラグ かつ 人間評価がまだない件数
    # → 人間評価を入力するとアラートから外れる（確認済みとみなす）
    alert_count = sum(1 for l in all_merged if l["needs_review"] and l.get("human_evaluation") is None)
    avg_score = sum(l["judge_scores"]["overall"] for l in all_merged) / len(all_merged) if all_merged else 0
    evaluated_count = sum(1 for l in all_merged if l.get("human_evaluation") is not None)
    evaluators = sorted({
        l["human_evaluation"]["evaluator"]
        for l in all_merged if l.get("human_evaluation") and l["human_evaluation"].get("evaluator")
    })

    summary = {
        "total": len(all_merged),
        "needs_review": alert_count,
        "ok": len(all_merged) - alert_count,
        "avg_judge_score": round(avg_score, 2),
        "evaluated_count": evaluated_count,
        "unevaluated_count": len(all_merged) - evaluated_count,
        "evaluators": evaluators,
    }

    return APIResponse(success=True, data={
        "summary": summary,
        "logs": logs[offset:offset + limit],
        "filtered_total": len(logs),
    })


# Dashboard Stats
@router.get("/stats", response_model=APIResponse)
async def get_dashboard_stats() -> APIResponse:
    """Get LLMOps dashboard statistics.

    本番環境では以下から集計:
    - MLflow Traces: 推論回数、レイテンシー
    - Serving Metrics: エラー率、スループット
    - 評価テーブル: 顧客満足度
    """
    try:
        # トレース統計
        ok_traces = [t for t in DEMO_TRACES if t["status"] == "OK"]
        error_traces = [t for t in DEMO_TRACES if t["status"] == "ERROR"]

        total_tokens = sum(
            t.get("response", {}).get("usage", {}).get("total_tokens", 0)
            for t in ok_traces
        )

        avg_latency = (
            sum(t["execution_time_ms"] for t in ok_traces) / len(ok_traces)
            if ok_traces else 0
        )

        # 評価統計
        avg_rating = (
            sum(e["rating"] for e in DEMO_EVALUATIONS) / len(DEMO_EVALUATIONS)
            if DEMO_EVALUATIONS else 0
        )

        error_rate = len(error_traces) / len(DEMO_TRACES) if DEMO_TRACES else 0

        stats = {
            # Dashboard.tsx required fields
            "total_inferences": len(DEMO_TRACES),
            "avg_response_time_ms": round(avg_latency, 1),
            "error_rate": error_rate,
            "active_sessions": 12,
            "recommendations_today": 47,
            "customer_satisfaction": round(avg_rating, 2),
            "top_recommended_makes": [
                {"make": "トヨタ", "count": 156},
                {"make": "ホンダ", "count": 98},
                {"make": "マツダ", "count": 67},
                {"make": "日産", "count": 54},
                {"make": "スバル", "count": 42},
            ],

            # Detailed LLMOps stats
            "traces": {
                "total": len(DEMO_TRACES),
                "success": len(ok_traces),
                "error": len(error_traces),
                "error_rate": error_rate,
            },
            "performance": {
                "avg_latency_ms": round(avg_latency, 1),
                "total_tokens": total_tokens,
                "estimated_cost_usd": round(total_tokens * 0.000015, 4),
            },
            "evaluations": {
                "total": len(DEMO_EVALUATIONS),
                "avg_rating": round(avg_rating, 2),
            },
            "usage_by_type": {
                "vehicle_recommendation": sum(1 for t in DEMO_TRACES if "recommendation" in t.get("tags", {}).get("mlflow.traceName", "")),
                "insight_extraction": sum(1 for t in DEMO_TRACES if "insight" in t.get("tags", {}).get("mlflow.traceName", "")),
                "chat_completion": sum(1 for t in DEMO_TRACES if "chat" in t.get("tags", {}).get("mlflow.traceName", "")),
            },
            "alert_count": sum(1 for l in DEMO_QUALITY_LOGS if l["needs_review"]),
        }
        return APIResponse(success=True, data=stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
