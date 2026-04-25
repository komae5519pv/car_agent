# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC
# MAGIC <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1B3139 100%); padding: 20px 30px; border-radius: 10px; margin-bottom: 20px;">
# MAGIC   <div style="display: flex; align-items: center; gap: 15px;">
# MAGIC     <img src="https://www.databricks.com/wp-content/uploads/2022/06/db-nav-logo.svg" width="40" style="filter: brightness(2);"/>
# MAGIC     <div>
# MAGIC       <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">中古車販売 AI デモ</h1>
# MAGIC       <p style="color: #B0BEC5; margin: 5px 0 0 0; font-size: 16px;">00_config - 共通設定</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left:4px solid #D32F2F;background:#FFEBEE;border-radius:8px;padding:16px 20px;margin:16px 0;">
# MAGIC   <div style="display:flex;align-items:flex-start;gap:12px;">
# MAGIC     <span style="font-size:20px;">⚠️</span>
# MAGIC     <div>
# MAGIC       <div style="font-weight:700;font-size:15px;margin-bottom:4px;color:#D32F2F;">このファイルは編集しないでください</div>
# MAGIC       <div style="font-size:14px;color:#333;line-height:1.6;">
# MAGIC         Catalog/Schema/モデル名/営業担当者名などを変更したい場合は、<br/>
# MAGIC         プロジェクトルートの <code><strong>databricks.yml</strong></code> の <code>variables:</code> セクションを編集してください。<br/><br/>
# MAGIC         このファイルは <code>databricks bundle run setup_demo</code> から実行された際、<br/>
# MAGIC         databricks.yml の variables を widget 経由で受け取る<strong>橋渡し役</strong>です。<br/>
# MAGIC         下のベタ書き値は「ノートブック単独デバッグ」用のフォールバックです。
# MAGIC       </div>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# DBTITLE 1,設定値の取得（databricks.yml の variables を widget 経由で受け取る）
'''
実行モードごとの設定ソース:

  ① bundle run setup_demo 経由の場合（推奨）
      databricks.yml の variables ──→ job parameters ──→ widget ──→ ここに反映

  ② ノートブック単独実行の場合（デバッグ用）
      widget は未設定 → 各 _get_widget() の第2引数（フォールバック値）が使われる
'''

# Unity Catalog / 環境設定の取得ヘルパー（widget 優先、未設定ならフォールバック）
def _get_widget(name: str, default: str) -> str:
    try:
        return dbutils.widgets.get(name)
    except Exception:
        return default

# ---- widget 経由で DAB variables から注入される（★ここの値は編集しないで） ----
#      ↓ databricks.yml の variables: セクションを編集すれば自動で反映されます
catalog_name   = _get_widget("catalog",        "konomi_demo_catalog")   # ← var.catalog
schema_name    = _get_widget("schema",         "car_agent")             # ← var.schema
LLM_MODEL      = _get_widget("llm_model",      "databricks-claude-sonnet-4")  # ← var.llm_model
SALES_REP_NAME = _get_widget("sales_rep_name", "大前 このみ")            # ← var.sales_rep_name

# ---- 固定の設定（通常は変更不要） ----
VOLUME_NAME           = "images"      # 車両画像を格納するボリューム名
RAW_VOLUME_NAME       = "raw_data"    # 生データ格納用ボリューム名
KNOWLEDGE_VOLUME_NAME = "knowledge"   # ナレッジアシスタント用テキスト格納ボリューム名

# ---- Genie / Agent Bricks の ID について ----
# 自動セットアップ (`databricks bundle run setup_demo`) を使う場合:
#   セットアップ完了後、`{catalog}.{schema}._app_config` テーブルに ID が自動記録されます。
#   アプリはそこから参照するので、ここに書く必要はありません。
#
# 手動で作成する場合（05〜07 のノートブック参照）:
#   作成後にここに記入してください。
GENIE_VEHICLE_ASSISTANT_ID = ""   # 車両営業アシスタント Genie Space ID
GENIE_MYPAGE_ID            = ""   # 営業マイページ Genie Space ID
GENIE_DASHBOARD_ID         = ""   # 営業データ Genie Space ID
KA_ENDPOINT_NAME           = ""   # Knowledge Assistant serving endpoint 名
MAS_ENDPOINT_NAME          = ""   # Multi-Agent Supervisor serving endpoint 名

# COMMAND ----------

# DBTITLE 1,リセット用（必要な場合のみコメント解除）
# spark.sql(f"DROP SCHEMA IF EXISTS {catalog_name}.{schema_name} CASCADE")

# COMMAND ----------

# DBTITLE 1,カタログ・スキーマ作成
spark.sql(f"""
    CREATE SCHEMA IF NOT EXISTS {catalog_name}.{schema_name}
    COMMENT '中古車販売 AI デモ用スキーマ — 車両推薦 AI エージェント'
""")

spark.sql(f"USE CATALOG {catalog_name};")
spark.sql(f"USE SCHEMA {schema_name};")

spark.sql(f"CREATE VOLUME IF NOT EXISTS {VOLUME_NAME} COMMENT '車両画像を格納するボリューム'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {RAW_VOLUME_NAME} COMMENT '生データ格納用ボリューム'")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {KNOWLEDGE_VOLUME_NAME} COMMENT 'ナレッジアシスタント用テキストファイル格納ボリューム'")

# COMMAND ----------

print("=" * 50)
print("  設定サマリー")
print("=" * 50)
print(f"  Catalog         : {catalog_name}")
print(f"  Schema          : {schema_name}")
print(f"  LLM Model       : {LLM_MODEL}")
print(f"  Sales Rep       : {SALES_REP_NAME}")
print("=" * 50)
print("  セットアップ完了！")
print("=" * 50)
