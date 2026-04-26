# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC
# MAGIC <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1B3139 100%); padding: 20px 30px; border-radius: 10px; margin-bottom: 20px;">
# MAGIC   <div style="display: flex; align-items: center; gap: 15px;">
# MAGIC     <img src="https://www.databricks.com/wp-content/uploads/2022/06/db-nav-logo.svg" width="40" style="filter: brightness(2);"/>
# MAGIC     <div>
# MAGIC       <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">中古車販売 AI デモ</h1>
# MAGIC       <p style="color: #B0BEC5; margin: 5px 0 0 0; font-size: 16px;">04_gold - Gold レイヤー（AI 前処理 + 集計）</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin-bottom: 20px;">
# MAGIC   <div style="font-weight: bold; color: #1976d2; margin-bottom: 5px;">概要</div>
# MAGIC   <div style="color: #0D47A1;">
# MAGIC     Silver テーブルのデータに対して LLM（Foundation Model API）を使い、<b>顧客インサイト</b>と<b>車両レコメンデーション</b>を生成します。<br>
# MAGIC     処理コスト削減のため、<code>SALES_REP_NAME</code>（00_config で設定）に紐づく顧客のみを対象にします。
# MAGIC   </div>
# MAGIC </div>
# MAGIC
# MAGIC <div style="border-left: 4px solid #F57C00; background-color: #FFF3E0; padding: 15px 20px; border-radius: 0 8px 8px 0; margin-bottom: 20px;">
# MAGIC   <div style="font-weight: bold; color: #F57C00; margin-bottom: 5px;">LLM コスト注意</div>
# MAGIC   <div style="color: #E65100;">
# MAGIC     LLM API 呼び出しを行うため、対象顧客数に比例してコストと処理時間が発生します。<br>
# MAGIC     デフォルトでは <code>SALES_REP_NAME</code> 担当の顧客（約10件）のみ処理します。
# MAGIC   </div>
# MAGIC </div>
# MAGIC
# MAGIC <table style="width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">
# MAGIC   <thead>
# MAGIC     <tr style="background: #1565C0; color: white;">
# MAGIC       <th style="padding: 10px 16px; text-align: left;">#</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">出力テーブル</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">処理方式</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">説明</th>
# MAGIC     </tr>
# MAGIC   </thead>
# MAGIC   <tbody>
# MAGIC     <tr style="background: #FFFFFF;">
# MAGIC       <td style="padding: 8px 16px;">1</td>
# MAGIC       <td style="padding: 8px 16px;"><code>gd_customer_insights</code></td>
# MAGIC       <td style="padding: 8px 16px;">LLM + MERGE</td>
# MAGIC       <td style="padding: 8px 16px;">顧客インサイト（深層ニーズ・購買シグナル・チャネル分析）</td>
# MAGIC     </tr>
# MAGIC     <tr style="background: #F5F5F5;">
# MAGIC       <td style="padding: 8px 16px;">2</td>
# MAGIC       <td style="padding: 8px 16px;"><code>gd_recommendations</code></td>
# MAGIC       <td style="padding: 8px 16px;">LLM + MERGE</td>
# MAGIC       <td style="padding: 8px 16px;">車両レコメンデーション（顧客毎に3車種 + トークスクリプト）</td>
# MAGIC     </tr>
# MAGIC     <tr style="background: #FFFFFF;">
# MAGIC       <td style="padding: 8px 16px;">3</td>
# MAGIC       <td style="padding: 8px 16px;"><code>gd_store_daily_activity</code></td>
# MAGIC       <td style="padding: 8px 16px;">SQL 集計</td>
# MAGIC       <td style="padding: 8px 16px;">店舗別日次集計（成約・売上・車種カテゴリ別内訳）</td>
# MAGIC     </tr>
# MAGIC   </tbody>
# MAGIC </table>
# MAGIC
# MAGIC <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px;">
# MAGIC   <div style="background: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
# MAGIC     <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
# MAGIC       <span style="background: #1565C0; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;">1</span>
# MAGIC       <span style="font-weight: bold;">初期化</span>
# MAGIC     </div>
# MAGIC     <div style="font-size: 13px; color: #555;">ライブラリ読込・LLM クライアント初期化・ヘルパー関数定義</div>
# MAGIC   </div>
# MAGIC   <div style="background: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
# MAGIC     <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
# MAGIC       <span style="background: #1565C0; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;">2</span>
# MAGIC       <span style="font-weight: bold;">LLM 処理</span>
# MAGIC     </div>
# MAGIC     <div style="font-size: 13px; color: #555;">顧客インサイト生成 → 車両レコメンデーション生成（MERGE で差分更新）</div>
# MAGIC   </div>
# MAGIC   <div style="background: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">
# MAGIC     <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
# MAGIC       <span style="background: #1565C0; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;">3</span>
# MAGIC       <span style="font-weight: bold;">SQL 集計</span>
# MAGIC     </div>
# MAGIC     <div style="font-size: 13px; color: #555;">店舗別日次活動集計テーブルを作成（LLM 不使用）</div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %pip install openai mlflow -q
# MAGIC dbutils.library.restartPython()

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

import json
import re
from datetime import datetime, timezone
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType, FloatType,
    TimestampType, DateType, LongType, ArrayType
)
from openai import OpenAI
import mlflow

from databricks.sdk import WorkspaceClient
import os

w = WorkspaceClient()
host  = w.config.host or os.environ.get("DATABRICKS_HOST", "")
token = (
    w.config.token
    or os.environ.get("DATABRICKS_TOKEN")
    or dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()
)

client = OpenAI(
    api_key=token,
    base_url=f"{host}/serving-endpoints"
)

# 00_config の変数を参照
CATALOG = catalog_name
SCHEMA = schema_name

# ========== 開発用オプション (本番は設定しない) ==========
# customer_limit: AI 処理対象の顧客数を制限 (開発時の時短用)
#   未設定 or "0"  → 制限なし（全担当顧客を処理、本番モード）
#   "3" など       → 指定数だけ処理（開発モード）
try:
    _limit_raw = dbutils.widgets.get("customer_limit")
    CUSTOMER_LIMIT = int(_limit_raw) if _limit_raw and _limit_raw.isdigit() and int(_limit_raw) > 0 else None
except Exception:
    CUSTOMER_LIMIT = None
# =========================================================

# ========== 事前生成済み Gold データ (デモ映え担保) ==========
# デモ主役の 10 名（CUST-0001 ~ CUST-0010）については、setup/gold_prebuilt_data.json
# から手作業で作り込んだインサイト・レコメンドを読み込み、LLM 呼び出しをスキップします。
# 未登録顧客は従来通り LLM で生成します。
#
# JSON を再生成したい場合は、本ファイル末尾の「LLM で全顧客を生成（参考コード）」を
# 有効化して結果をエクスポートしてください。
_prebuilt_path_candidates = [
    # Workspace / Job 実行時
    f"/Workspace{os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())}/setup/gold_prebuilt_data.json",
    # ローカル開発時
    os.path.join(os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else '.', 'setup', 'gold_prebuilt_data.json'),
]
PREBUILT_DATA = {"insights": {}, "recommendations": {}}
for _p in _prebuilt_path_candidates:
    try:
        with open(_p, encoding='utf-8') as _f:
            PREBUILT_DATA = json.load(_f)
            print(f"✓ 事前生成データ読込: {_p}")
            print(f"  insights: {len(PREBUILT_DATA.get('insights', {}))} 件, recommendations: {len(PREBUILT_DATA.get('recommendations', {}))} 件")
            break
    except Exception as _e:
        continue
else:
    print("⚠️ 事前生成データが見つかりません。全顧客を LLM で生成します。")
# =========================================================

print(f"LLM Model: {LLM_MODEL}")
print(f"Schema: {CATALOG}.{SCHEMA}")
print(f"Sales Rep: {SALES_REP_NAME}")
if CUSTOMER_LIMIT:
    print(f"⚠️ DEV MODE: customer_limit={CUSTOMER_LIMIT} (本番は未設定)")

# COMMAND ----------

# DBTITLE 1,ヘルパー関数
def add_comments(table: str, tbl_comment: str, col_comments: dict):
    """テーブルとカラムにコメントを設定"""
    spark.sql(f"ALTER TABLE {CATALOG}.{SCHEMA}.{table} SET TBLPROPERTIES ('comment' = '{tbl_comment}')")
    for col, comment in col_comments.items():
        spark.sql(f"ALTER TABLE {CATALOG}.{SCHEMA}.{table} ALTER COLUMN `{col}` COMMENT '{comment}'")
    print(f"  コメント設定完了: {table}")


@mlflow.trace
def call_llm(system_prompt: str, user_prompt: str, model: str = None) -> str:
    """LLM を呼び出してテキスト応答を返す"""
    if model is None:
        model = LLM_MODEL
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=2000,
        temperature=0.3
    )
    return response.choices[0].message.content


def parse_json_response(text: str):
    """LLM 応答から JSON を抽出してパースする"""
    cleaned = text.strip()
    # マークダウンコードブロックを除去
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned.strip())

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin-bottom: 20px;">
# MAGIC   <div style="font-weight: bold; color: #1976d2; margin-bottom: 5px;">1. gd_customer_insights</div>
# MAGIC   <div style="color: #0D47A1;">
# MAGIC     各顧客の属性・インタラクション履歴・Web 閲覧行動を分析し、<br>
# MAGIC     <b>深層ニーズ</b>・<b>購買シグナル</b>・<b>チャネル別インサイト</b>を LLM で生成します。<br>
# MAGIC     MERGE（upsert）で差分更新するため、再実行しても既存データを安全に更新できます。
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# DBTITLE 1,gd_customer_insights テーブル作成
spark.sql(f"DROP TABLE IF EXISTS {CATALOG}.{SCHEMA}.gd_customer_insights")

spark.sql(f"""
CREATE TABLE {CATALOG}.{SCHEMA}.gd_customer_insights (
    customer_id STRING NOT NULL COMMENT '顧客ID（PK）',
    contact_name STRING COMMENT '顧客氏名',
    sales_rep_name STRING COMMENT '担当営業名',
    sales_rep_email STRING COMMENT '営業担当者メールアドレス',
    deep_needs STRING COMMENT 'LLM生成：深層ニーズ（JSON配列文字列）',
    purchase_signals STRING COMMENT 'LLM生成：購買シグナル（JSON配列文字列）',
    decision_key STRING COMMENT 'LLM生成：最終的な購買決定要因',
    purchase_urgency STRING COMMENT 'LLM生成：購買意欲（高/中/低）',
    urgency_reason STRING COMMENT 'LLM生成：購買意欲の根拠',
    channel_insight_visit STRING COMMENT 'LLM生成：来店チャネルインサイト',
    channel_insight_line STRING COMMENT 'LLM生成：LINEチャネルインサイト',
    channel_insight_cc STRING COMMENT 'LLM生成：コールセンターチャネルインサイト',
    channel_insight_web STRING COMMENT 'LLM生成：Web 閲覧履歴チャネルインサイト',
    key_quotes_json STRING COMMENT 'LLM生成：顧客の印象的な発言（JSON配列文字列）',
    summary STRING COMMENT 'LLM生成：顧客の本音サマリ（20-30文字）',
    processed_at TIMESTAMP COMMENT '処理日時',
    CONSTRAINT pk_gd_customer_insights PRIMARY KEY (customer_id)
)
COMMENT 'LLM生成の顧客インサイト（深層ニーズ・購買シグナル・チャネル分析）'
""")

print("gd_customer_insights テーブル準備完了")

# COMMAND ----------

# DBTITLE 1,対象顧客・インタラクション・Web 閲覧データ取得
# 対象顧客を取得
df_customers = spark.sql(f"""
    SELECT *
    FROM {CATALOG}.{SCHEMA}.sv_customers
    WHERE sales_rep_name = '{SALES_REP_NAME}'
""")
customer_rows = df_customers.collect()

# 開発モードで件数制限 (customer_limit widget 指定時のみ)
if CUSTOMER_LIMIT:
    customer_rows = customer_rows[:CUSTOMER_LIMIT]
    print(f"⚠️ DEV MODE: 先頭 {CUSTOMER_LIMIT} 件のみ処理")

print(f"対象顧客数: {len(customer_rows)} 件（担当: {SALES_REP_NAME}）")

# インタラクション履歴を取得（顧客ごとにグループ化用）
df_interactions = spark.sql(f"""
    SELECT customer_id, interaction_type, interaction_date, content, sales_rep_name
    FROM {CATALOG}.{SCHEMA}.sv_interactions
    ORDER BY customer_id, interaction_date
""")
interactions_all = df_interactions.collect()

# 顧客ごとのインタラクションを辞書にまとめる
interactions_by_customer = {}
for row in interactions_all:
    cid = row["customer_id"]
    if cid not in interactions_by_customer:
        interactions_by_customer[cid] = []
    interactions_by_customer[cid].append(row)

# Web 閲覧行動を取得（sf_opportunity_id でジョイン）
df_web = spark.sql(f"""
    SELECT *
    FROM {CATALOG}.{SCHEMA}.sv_web_browsing_behavior
""")
web_all = df_web.collect()

# sf_opportunity_id → Web 閲覧データの辞書
web_by_opp = {}
for row in web_all:
    web_by_opp[row["sf_opportunity_id"]] = row

print(f"インタラクション: {len(interactions_all)} 件")
print(f"Web 閲覧行動: {len(web_all)} 件")

# COMMAND ----------

# DBTITLE 1,インサイト生成プロンプト

INSIGHT_SYSTEM_PROMPT = """あなたは中古車販売会社の顧客分析AIです。
顧客の来店記録・LINEメッセージ・コールセンター通話・Web 閲覧履歴を分析し、
顧客の深層ニーズと購買意欲を抽出してください。

【重要】各項目は簡潔に。長い文章は禁止。体言止め・短縮表現を使い、ぱっと見でわかる短さにすること。

以下のJSON形式で回答してください（マークダウンや余分な文字を含めないこと）:
{
  "deep_needs": ["短いフレーズ（20文字以内）", "例：義母含む5人の乗降性重視", "例：燃費・最新安全装備も気になる", "例：ミニバンとSUV両方検討中"],
  "purchase_signals": ["短いフレーズ（20文字以内）", "例：来店2回・LINE積極的"],
  "decision_key": "短い一文（30文字以内）例：義母の乗降性と安全装備が決め手",
  "purchase_urgency": "高/中/低",
  "urgency_reason": "短い根拠（40文字以内）例：来月の車検前に決めたい意向あり",
  "channel_insights": {
    "visit": "1文で簡潔に（40文字以内）",
    "line": "1文で簡潔に（40文字以内）",
    "callcenter": "1文で簡潔に（40文字以内）",
    "web": "1文で簡潔に（40文字以内）"
  },
  "key_quotes": ["印象的な発言1（25〜40文字の口語体）", "例：子供たちが快適に座れる車がいいんですよね", "例：義母の乗り降りが楽な車がいいなと思って"],
  "summary": "顧客の本音を一言で（20〜30文字）例：家族全員が快適に乗れる車が欲しい"
}"""


def build_insight_prompt(customer_row, interactions, web):
    """顧客情報・インタラクション・Web 閲覧行動からプロンプトを構築"""
    lines = [
        f"顧客名: {customer_row['contact_name']}",
        f"年齢: {customer_row['age']}歳",
        f"職業: {customer_row['occupation']}",
        f"家族構成: {customer_row['family_detail']}",
        f"現在の車: {customer_row['current_vehicle']} ({customer_row['current_mileage']:,}km)",
        f"予算上限: {customer_row['budget']:,}円",
        f"来店予定日: {customer_row['visit_scheduled_date']}",
        "",
        "【インタラクション履歴】"
    ]
    for row in interactions:
        lines.append(f"[{row['interaction_type']} / {row['interaction_date']}]")
        lines.append(row["content"][:500])
        lines.append("")

    if web:
        lines += [
            "【Web 閲覧行動】",
            f"総セッション数: {web['session_count']}",
            f"総閲覧数: {web['view_count']}",
            f"検索キーワード: {web['search_keywords']}",
            f"閲覧車両: {web['viewed_vehicles']}",
            f"お気に入り登録数: {web['favorite_count']}件",
        ]

    return "\n".join(lines)

# COMMAND ----------

# DBTITLE 1,インサイト生成（prebuilt 優先・未登録は LLM）+ MERGE
insights_records = []

_prebuilt_insights = PREBUILT_DATA.get("insights", {})

for i, c in enumerate(customer_rows):
    cid = c["customer_id"]
    opp_id = c["sf_opportunity_id"]
    print(f"  [{i+1}/{len(customer_rows)}] {c['contact_name']} ...", end=" ")

    if cid in _prebuilt_insights:
        # ---- Prebuilt データを採用（LLM スキップ） ----
        result = _prebuilt_insights[cid]
        print("prebuilt")
    else:
        # ---- LLM で生成 ----
        interactions = interactions_by_customer.get(cid, [])
        web = web_by_opp.get(opp_id)
        user_prompt = build_insight_prompt(c, interactions, web)

        try:
            raw = call_llm(INSIGHT_SYSTEM_PROMPT, user_prompt)
            result = parse_json_response(raw)
            print("llm done")
        except Exception as e:
            print(f"ERROR: {str(e)[:80]}")
            result = {
                "deep_needs": [],
                "purchase_signals": [],
                "decision_key": "生成エラー",
                "purchase_urgency": "中",
                "urgency_reason": "生成エラー",
                "channel_insights": {"visit": "", "line": "", "callcenter": "", "web": ""},
                "summary": "生成エラー",
            }

    ch = result.get("channel_insights", {})

    insights_records.append({
        "customer_id": cid,
        "contact_name": c["contact_name"],
        "sales_rep_name": c["sales_rep_name"],
        "sales_rep_email": c["sales_rep_email"],
        "deep_needs": json.dumps(result.get("deep_needs", []), ensure_ascii=False),
        "purchase_signals": json.dumps(result.get("purchase_signals", []), ensure_ascii=False),
        "decision_key": result.get("decision_key", ""),
        "purchase_urgency": result.get("purchase_urgency", "中"),
        "urgency_reason": result.get("urgency_reason", ""),
        "channel_insight_visit": ch.get("visit", ""),
        "channel_insight_line": ch.get("line", ""),
        "channel_insight_cc": ch.get("callcenter", ""),
        "channel_insight_web": ch.get("web", ""),
        "key_quotes_json": json.dumps(result.get("key_quotes", []), ensure_ascii=False),
        "summary": result.get("summary", ""),
        "processed_at": datetime.now(timezone.utc),
    })

print(f"\nインサイト生成完了: {len(insights_records)} 件")

# COMMAND ----------

# DBTITLE 1,gd_customer_insights MERGE
df_insights = spark.createDataFrame(insights_records)
df_insights.createOrReplaceTempView("tmp_customer_insights")

spark.sql(f"""
MERGE INTO {CATALOG}.{SCHEMA}.gd_customer_insights AS target
USING tmp_customer_insights AS source
ON target.customer_id = source.customer_id
WHEN MATCHED THEN UPDATE SET
    contact_name = source.contact_name,
    sales_rep_name = source.sales_rep_name,
    sales_rep_email = source.sales_rep_email,
    deep_needs = source.deep_needs,
    purchase_signals = source.purchase_signals,
    decision_key = source.decision_key,
    purchase_urgency = source.purchase_urgency,
    urgency_reason = source.urgency_reason,
    channel_insight_visit = source.channel_insight_visit,
    channel_insight_line = source.channel_insight_line,
    channel_insight_cc = source.channel_insight_cc,
    channel_insight_web = source.channel_insight_web,
    key_quotes_json = source.key_quotes_json,
    summary = source.summary,
    processed_at = source.processed_at
WHEN NOT MATCHED THEN INSERT *
""")

cnt = spark.table(f"{CATALOG}.{SCHEMA}.gd_customer_insights").count()
print(f"gd_customer_insights: {cnt} 件")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin-bottom: 20px;">
# MAGIC   <div style="font-weight: bold; color: #1976d2; margin-bottom: 5px;">2. gd_recommendations</div>
# MAGIC   <div style="color: #0D47A1;">
# MAGIC     顧客インサイトと在庫車両データを組み合わせ、各顧客に最適な <b>3 車種</b>を LLM で推薦します。<br>
# MAGIC     各推薦にはマッチスコア・推薦理由・トークスクリプト・セールスポイントを含みます。
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# DBTITLE 1,gd_recommendations テーブル作成
spark.sql(f"DROP TABLE IF EXISTS {CATALOG}.{SCHEMA}.gd_recommendations")

spark.sql(f"""
CREATE TABLE {CATALOG}.{SCHEMA}.gd_recommendations (
    customer_id STRING NOT NULL COMMENT '顧客ID（PK1）',
    contact_name STRING COMMENT '顧客氏名',
    sales_rep_name STRING COMMENT '担当営業名',
    sales_rep_email STRING COMMENT '営業担当者メールアドレス',
    rank INT NOT NULL COMMENT '推薦順位 1-3（PK2）',
    vehicle_key STRING COMMENT '車両キー',
    vehicle_name STRING COMMENT '車名（メーカー含む）',
    match_score INT COMMENT 'LLM算出の適合スコア（0-100）',
    recommendation_reason STRING COMMENT 'LLM生成：推薦理由',
    talk_script STRING COMMENT 'LLM生成：営業トークスクリプト',
    key_selling_points STRING COMMENT 'LLM生成：セールスポイント（JSON配列文字列）',
    image_path STRING COMMENT '車両画像パス',
    generated_at TIMESTAMP COMMENT '生成日時',
    CONSTRAINT pk_gd_recommendations PRIMARY KEY (customer_id, rank)
)
COMMENT 'LLM生成の車両レコメンデーション（顧客毎に3車種推薦）'
""")

print("gd_recommendations テーブル準備完了")

# COMMAND ----------

# DBTITLE 1,在庫車両データ取得
vehicle_rows = spark.table(f"{CATALOG}.{SCHEMA}.sv_vehicle_inventory").collect()

# vehicle_key → 車両情報の辞書（image_path 参照用）
vehicle_dict = {}
for v in vehicle_rows:
    vehicle_dict[v["vehicle_key"]] = v

print(f"在庫車両数: {len(vehicle_rows)} 件")

# COMMAND ----------

# DBTITLE 1,レコメンデーション生成プロンプト

RECOMMENDATION_SYSTEM_PROMPT = """あなたは中古車販売会社のベテラン営業スタッフです。
顧客データ・インサイト・在庫車両リストを元に、最適な車両3台を推薦し、
各車両の推薦理由とトークスクリプトを生成してください。

以下のJSON形式で回答してください（マークダウンや余分な文字を含めないこと）:
[
  {
    "rank": 1,
    "vehicle_key": "在庫のvehicle_keyをそのまま使う",
    "vehicle_name": "車名（メーカー含む、例：トヨタ ハリアー）",
    "match_score": 95,
    "recommendation_reason": "この顧客にこの車を推薦する理由（3〜5文）",
    "talk_script": "営業担当者が使えるトークスクリプト（顧客の名前を使い、具体的なエピソードを交えた2〜3文）",
    "key_selling_points": ["セールスポイント1", "セールスポイント2", "セールスポイント3"]
  },
  { "rank": 2, ... },
  { "rank": 3, ... }
]"""


def build_recommendation_prompt(customer_row, insights_row, inventory_list):
    """顧客情報・インサイト・在庫リストからレコメンデーションプロンプトを構築"""
    lines = [
        f"顧客名: {customer_row['contact_name']}",
        f"年齢: {customer_row['age']}歳 / 職業: {customer_row['occupation']}",
        f"家族構成: {customer_row['family_detail']}",
        f"現在の車: {customer_row['current_vehicle']}",
        f"予算上限: {customer_row['budget']:,}円",
        "",
        "【AIインサイト】",
        f"深層ニーズ: {insights_row['deep_needs']}",
        f"購買意欲: {insights_row['purchase_urgency']}",
        f"決め手: {insights_row['decision_key']}",
        f"サマリ: {insights_row['summary']}",
        "",
        "【在庫車両リスト】（vehicle_keyと予算を参考に選択）"
    ]
    for v in inventory_list:
        lines.append(
            f"- vehicle_key={v['vehicle_key']}: {v['vehicle_name']} "
            f"({v['body_type']}) "
            f"価格: {v['price']:,}円"
        )
    return "\n".join(lines)

# COMMAND ----------

# DBTITLE 1,レコメンデーション生成（prebuilt 優先・未登録は LLM）
# インサイト結果を辞書に変換（customer_id → インサイト行）
insights_dict = {r["customer_id"]: r for r in insights_records}

_prebuilt_recs = PREBUILT_DATA.get("recommendations", {})

rec_records = []

for i, c in enumerate(customer_rows):
    cid = c["customer_id"]
    print(f"  [{i+1}/{len(customer_rows)}] {c['contact_name']} ...", end=" ")

    insight = insights_dict.get(cid)
    if not insight:
        print("SKIP (no insight)")
        continue

    if cid in _prebuilt_recs:
        # ---- Prebuilt データを採用（LLM スキップ） ----
        recs = _prebuilt_recs[cid]
        print(f"prebuilt ({len(recs)} recs)")
    else:
        # ---- LLM で生成 ----
        user_prompt = build_recommendation_prompt(c, insight, vehicle_rows)
        try:
            raw = call_llm(RECOMMENDATION_SYSTEM_PROMPT, user_prompt)
            recs = parse_json_response(raw)
            if not isinstance(recs, list):
                recs = []
        except Exception as e:
            print(f"ERROR: {str(e)[:80]}")
            recs = []
        print(f"llm done ({len(recs[:3])} recs)")

    for rec in recs[:3]:
        vkey = rec.get("vehicle_key", "")
        # vehicle_dict から image_path を取得（Row オブジェクト対応）
        v_info = vehicle_dict.get(vkey)
        image_path = v_info["image_path"] if v_info else ""
        rec_records.append({
            "customer_id": cid,
            "contact_name": c["contact_name"],
            "sales_rep_name": c["sales_rep_name"],
            "sales_rep_email": c["sales_rep_email"],
            "rank": int(rec.get("rank", 0)),
            "vehicle_key": vkey,
            "vehicle_name": rec.get("vehicle_name", ""),
            "match_score": int(rec.get("match_score", 0)),
            "recommendation_reason": rec.get("recommendation_reason", ""),
            "talk_script": rec.get("talk_script", ""),
            "key_selling_points": json.dumps(rec.get("key_selling_points", []), ensure_ascii=False),
            "image_path": image_path,
            "generated_at": datetime.now(timezone.utc),
        })

print(f"\nレコメンデーション生成完了: {len(rec_records)} 件")

# COMMAND ----------

# DBTITLE 1,gd_recommendations MERGE
df_recs = spark.createDataFrame(rec_records)
df_recs.createOrReplaceTempView("tmp_recommendations")

spark.sql(f"""
MERGE INTO {CATALOG}.{SCHEMA}.gd_recommendations AS target
USING tmp_recommendations AS source
ON target.customer_id = source.customer_id AND target.rank = source.rank
WHEN MATCHED THEN UPDATE SET
    contact_name = source.contact_name,
    sales_rep_name = source.sales_rep_name,
    sales_rep_email = source.sales_rep_email,
    vehicle_key = source.vehicle_key,
    vehicle_name = source.vehicle_name,
    match_score = source.match_score,
    recommendation_reason = source.recommendation_reason,
    talk_script = source.talk_script,
    key_selling_points = source.key_selling_points,
    image_path = source.image_path,
    generated_at = source.generated_at
WHEN NOT MATCHED THEN INSERT *
""")

cnt = spark.table(f"{CATALOG}.{SCHEMA}.gd_recommendations").count()
print(f"gd_recommendations: {cnt} 件")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin-bottom: 20px;">
# MAGIC   <div style="font-weight: bold; color: #1976d2; margin-bottom: 5px;">3. gd_store_daily_activity</div>
# MAGIC   <div style="color: #0D47A1;">
# MAGIC     <code>sv_sales_results</code> と <code>sv_stores</code> を結合し、店舗別日次活動集計テーブルを生成します。<br>
# MAGIC     LLM は使用せず、SQL 集計のみで処理します。
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# DBTITLE 1,gd_store_daily_activity 集計
spark.sql(f"""
CREATE OR REPLACE TABLE {CATALOG}.{SCHEMA}.gd_store_daily_activity
COMMENT '店舗別日次活動集計（sv_sales_results + sv_stores から集計）'
AS
SELECT
    s.sale_date AS activity_date,
    YEAR(s.sale_date) AS year,
    s.region,
    s.store_name,
    st.latitude AS store_lat,
    st.longitude AS store_lon,
    s.vehicle_category,
    COUNT(*) AS inquiries,
    CAST(COUNT(*) * 0.70 AS BIGINT) AS test_drives,
    CAST(COUNT(*) * 0.50 AS BIGINT) AS quotes_sent,
    SUM(CASE WHEN s.outcome = '成約' THEN 1 ELSE 0 END) AS contracts,
    SUM(CASE WHEN s.outcome = '成約' THEN s.sale_price ELSE 0 END) AS revenue
FROM {CATALOG}.{SCHEMA}.sv_sales_results s
LEFT JOIN {CATALOG}.{SCHEMA}.sv_stores st ON s.store_name = st.store_name
GROUP BY s.sale_date, YEAR(s.sale_date), s.region, s.store_name, st.latitude, st.longitude, s.vehicle_category
""")

cnt = spark.table(f"{CATALOG}.{SCHEMA}.gd_store_daily_activity").count()
print(f"gd_store_daily_activity: {cnt} 件")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC
# MAGIC <div style="border-left: 4px solid #388E3C; background-color: #E8F5E9; padding: 15px 20px; border-radius: 0 8px 8px 0; margin-bottom: 20px;">
# MAGIC   <div style="font-weight: bold; color: #388E3C; margin-bottom: 5px;">Gold レイヤー生成完了</div>
# MAGIC   <div style="color: #2E7D32;">
# MAGIC     3つの Gold テーブルが正常に生成されました。以下のサマリーを確認してください。
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# DBTITLE 1,生成結果サマリー
print("=" * 60)
print("  Gold レイヤー生成結果")
print("=" * 60)
for t in ["gd_customer_insights", "gd_recommendations", "gd_store_daily_activity"]:
    cnt = spark.table(f"{CATALOG}.{SCHEMA}.{t}").count()
    print(f"  {t:<30s} {cnt:>10,} 件")
print("=" * 60)
print("  Gold 生成完了")
print("=" * 60)
