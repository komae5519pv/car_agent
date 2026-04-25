# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1B3139 100%); padding: 20px 30px; border-radius: 10px; margin-bottom: 20px;">
# MAGIC   <div style="display: flex; align-items: center; gap: 15px;">
# MAGIC     <img src="https://www.databricks.com/wp-content/uploads/2022/06/db-nav-logo.svg" width="40" style="filter: brightness(2);"/>
# MAGIC     <div>
# MAGIC       <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">car-agent セットアップ</h1>
# MAGIC       <p style="color: #B0BEC5; margin: 5px 0 0 0; font-size: 16px;">_app_config テーブルへ ID 登録</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h3 style="color: #1976d2; margin-top: 0;">📋 このノートブックの目的</h3>
# MAGIC   <p>Genie / KA / MAS / App の ID を <code>{catalog}.{schema}._app_config</code> テーブルに登録します。</p>
# MAGIC   <p>アプリは起動時にこのテーブルを参照するため、ID を環境変数にベタ書きしなくて良くなります。</p>
# MAGIC </div>

# COMMAND ----------

# DBTITLE 1,パラメータ取得
def _get_widget(name: str, default: str) -> str:
    try:
        return dbutils.widgets.get(name)
    except Exception:
        return default

catalog_name         = _get_widget("catalog",              "konomi_demo_catalog")
schema_name          = _get_widget("schema",               "car_agent")
app_name             = _get_widget("app_name",             "car-agent")
ka_name              = _get_widget("ka_name",              "car-agent-knowledge")
mas_name             = _get_widget("mas_name",             "car-agent-supervisor")
genie_vehicle_name   = _get_widget("genie_vehicle_name",   "[car-agent] 車両営業アシスタント")
genie_mypage_name    = _get_widget("genie_mypage_name",    "[car-agent] 営業マイページ")
genie_dashboard_name = _get_widget("genie_dashboard_name", "[car-agent] 営業データ")

print(f"  Catalog    : {catalog_name}")
print(f"  Schema     : {schema_name}")
print(f"  App name   : {app_name}")

# COMMAND ----------

# DBTITLE 1,各リソースの ID / endpoint を名前で検索
import requests
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
host = w.config.host.rstrip("/")
headers = w.config.authenticate()

def _api(method: str, path: str, body: dict | None = None) -> dict:
    resp = requests.request(method, f"{host}{path}", headers=headers, json=body)
    if not resp.ok:
        raise RuntimeError(f"{method} {path}: {resp.status_code} {resp.text[:500]}")
    return resp.json() if resp.text else {}

# Genie Space IDs
genie_resp = _api("GET", "/api/2.0/genie/spaces")
genie_by_name = {s["title"]: s["space_id"] for s in genie_resp.get("spaces", [])}
genie_vehicle_id   = genie_by_name.get(genie_vehicle_name,   "")
genie_mypage_id    = genie_by_name.get(genie_mypage_name,    "")
genie_dashboard_id = genie_by_name.get(genie_dashboard_name, "")

# KA endpoint
ka_resp = _api("GET", "/api/2.1/knowledge-assistants")
ka_by_name = {k["display_name"]: k for k in ka_resp.get("knowledge_assistants", [])}
ka_endpoint = ka_by_name.get(ka_name, {}).get("endpoint_name", "")

# MAS endpoint (tiles 経由)
tiles_resp = _api("GET", "/api/2.0/tiles")
mas_endpoint = ""
for t in tiles_resp.get("tiles", []):
    if t.get("tile_type") == "MAS" and t.get("name") == mas_name:
        mas_endpoint = t.get("serving_endpoint_name", "")
        break

# App URL + SP ID
app = w.apps.get(name=app_name)
app_url = app.url or ""
app_sp_client_id = app.service_principal_client_id or ""

print(f"  Genie vehicle    : {genie_vehicle_id}")
print(f"  Genie mypage     : {genie_mypage_id}")
print(f"  Genie dashboard  : {genie_dashboard_id}")
print(f"  KA endpoint      : {ka_endpoint}")
print(f"  MAS endpoint     : {mas_endpoint}")
print(f"  App URL          : {app_url}")
print(f"  App SP           : {app_sp_client_id}")

# COMMAND ----------

# DBTITLE 1,_app_config テーブル作成 + 値登録
# ---- 登録するエントリ ----
entries = [
    ("catalog",                  catalog_name,         "Unity Catalog 名"),
    ("schema",                   schema_name,          "スキーマ名"),
    ("app_name",                 app_name,             "Databricks App 名"),
    ("app_url",                  app_url,              "App URL"),
    ("app_sp_client_id",         app_sp_client_id,     "App Service Principal の client_id"),
    ("genie_vehicle_id",         genie_vehicle_id,     "車両営業アシスタント Genie Space ID"),
    ("genie_mypage_id",          genie_mypage_id,      "営業マイページ Genie Space ID"),
    ("genie_dashboard_id",       genie_dashboard_id,   "営業データ Genie Space ID"),
    ("ka_name",                  ka_name,              "Knowledge Assistant 表示名"),
    ("ka_endpoint",              ka_endpoint,          "KA serving endpoint 名"),
    ("mas_name",                 mas_name,             "Multi-Agent Supervisor 表示名"),
    ("mas_endpoint",             mas_endpoint,         "MAS serving endpoint 名 (アプリが呼び出す)"),
    ("agent_endpoint_name",      mas_endpoint,         "アプリが参照する Agent エンドポイント (=MAS)"),
    ("sales_mypage_genie_space_id", genie_mypage_id,   "マイページ画面から呼ばれる Genie (=mypage)"),
]

# スキーマがない場合は作成 (00_config が既に作っている想定だが念の為)
spark.sql(f"USE CATALOG `{catalog_name}`")
spark.sql(f"USE SCHEMA `{schema_name}`")

# テーブル作成 (MERGE で upsert するため primary key はなくても key で JOIN)
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS `{catalog_name}`.`{schema_name}`._app_config (
        key         STRING NOT NULL,
        value       STRING,
        description STRING,
        updated_at  TIMESTAMP
    )
    COMMENT 'car-agent runtime configuration (auto-populated by setup_demo job)'
""")

# MERGE で upsert
from pyspark.sql import Row
from pyspark.sql.functions import current_timestamp, lit

new_df = spark.createDataFrame(
    [Row(key=k, value=v, description=d) for k, v, d in entries]
).withColumn("updated_at", current_timestamp())

new_df.createOrReplaceTempView("_app_config_new")

spark.sql(f"""
    MERGE INTO `{catalog_name}`.`{schema_name}`._app_config AS target
    USING _app_config_new AS source
    ON target.key = source.key
    WHEN MATCHED THEN UPDATE SET
        value = source.value,
        description = source.description,
        updated_at = source.updated_at
    WHEN NOT MATCHED THEN INSERT (key, value, description, updated_at)
        VALUES (source.key, source.value, source.description, source.updated_at)
""")

# App SP に SELECT 権限を付与 (起動時にこのテーブルを読む)
if app_sp_client_id:
    spark.sql(
        f"GRANT SELECT ON TABLE `{catalog_name}`.`{schema_name}`._app_config TO `{app_sp_client_id}`"
    )
    print(f"  ✓ GRANT SELECT TO {app_sp_client_id}")

# COMMAND ----------

# DBTITLE 1,登録結果の確認
print(f"\n=== {catalog_name}.{schema_name}._app_config ===")
display(spark.sql(
    f"SELECT key, value, description FROM `{catalog_name}`.`{schema_name}`._app_config ORDER BY key"
))

# COMMAND ----------

# DBTITLE 1,完了
print("=" * 60)
print(f"  ✅ _app_config セットアップ完了 ({len(entries)} 件登録)")
print("=" * 60)
print(f"  Table: {catalog_name}.{schema_name}._app_config")
print(f"  App はこのテーブルを起動時に読み込んで設定を取得します。")
print("=" * 60)

dbutils.notebook.exit(
    '{"config_table":"' + f"{catalog_name}.{schema_name}._app_config" + '","entries":' + str(len(entries)) + '}'
)
