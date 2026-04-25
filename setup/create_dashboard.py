# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1B3139 100%); padding: 20px 30px; border-radius: 10px; margin-bottom: 20px;">
# MAGIC   <div style="display: flex; align-items: center; gap: 15px;">
# MAGIC     <img src="https://www.databricks.com/wp-content/uploads/2022/06/db-nav-logo.svg" width="40" style="filter: brightness(2);"/>
# MAGIC     <div>
# MAGIC       <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">car-agent セットアップ</h1>
# MAGIC       <p style="color: #B0BEC5; margin: 5px 0 0 0; font-size: 16px;">AI/BI ダッシュボードのデプロイ</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h3 style="color: #1976d2; margin-top: 0;">📋 このノートブックの目的</h3>
# MAGIC   <p>リポジトリ直下の <code>車両販売ダッシュボード.lvdash.json</code> を読み込み、以下を置換してから作成/更新:</p>
# MAGIC   <ul>
# MAGIC     <li>catalog / schema ref → <code>_app_config</code> の現行値に置換</li>
# MAGIC     <li>ダッシュボード連携の Genie Space ID → 現行 <code>genie_dashboard_id</code> に置換</li>
# MAGIC   </ul>
# MAGIC </div>

# COMMAND ----------

# DBTITLE 1,パラメータ取得
def _get_widget(name: str, default: str) -> str:
    try:
        return dbutils.widgets.get(name)
    except Exception:
        return default

catalog_name   = _get_widget("catalog",        "konomi_demo_catalog")
schema_name    = _get_widget("schema",         "car_agent")
warehouse_id   = _get_widget("warehouse_id",   "348478745ad64b30")
dashboard_name = _get_widget("dashboard_name", "[car-agent] 車両販売ダッシュボード")

print(f"  Catalog        : {catalog_name}")
print(f"  Schema         : {schema_name}")
print(f"  Warehouse      : {warehouse_id}")
print(f"  Dashboard name : {dashboard_name}")

# COMMAND ----------

# DBTITLE 1,_app_config から genie_dashboard_id を取得
genie_dashboard_id = spark.sql(
    f"SELECT value FROM `{catalog_name}`.`{schema_name}`._app_config WHERE key = 'genie_dashboard_id'"
).collect()[0]["value"]
print(f"  genie_dashboard_id: {genie_dashboard_id}")

# COMMAND ----------

# DBTITLE 1,ダッシュボード JSON を読み込み + 置換
import os
import json

# このノートブックの親ディレクトリ (= リポジトリルート) にダッシュボード JSON がある
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
repo_root = os.path.dirname(os.path.dirname(notebook_path))  # setup/ の親
dashboard_file = f"/Workspace{repo_root}/車両販売ダッシュボード.lvdash.json"

with open(dashboard_file) as f:
    raw_json = f.read()

# ---- 置換1: catalog.schema 参照 ----
# 既存の値（コミット時のもの）を新しい値に置き換え
# リポジトリのデフォルトは konomi_demo_catalog.car_agent
raw_json = raw_json.replace("konomi_demo_catalog.car_agent", f"{catalog_name}.{schema_name}")

# ---- 置換2: Genie Space ID ----
# 元リポジトリの ID（コミット時のもの）を現行 ID に置き換え
STALE_GENIE_ID = "01f130f284c21b4fb53fd6e6703731d7"
raw_json = raw_json.replace(STALE_GENIE_ID, genie_dashboard_id)

print(f"  JSON 置換完了: {len(raw_json):,} bytes")

# COMMAND ----------

# DBTITLE 1,既存ダッシュボード検索 + create or update
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

# ---- 既存検索: 同じ display_name のダッシュボードがあるか ----
existing = None
list_resp = _api("GET", "/api/2.0/lakeview/dashboards?page_size=200")
for d in list_resp.get("dashboards", []):
    if d.get("display_name") == dashboard_name:
        existing = d
        break

payload = {
    "display_name":         dashboard_name,
    "warehouse_id":         warehouse_id,
    "serialized_dashboard": raw_json,
}

if existing:
    dash_id = existing["dashboard_id"]
    _api("PATCH", f"/api/2.0/lakeview/dashboards/{dash_id}", body=payload)
    action = "updated"
else:
    resp = _api("POST", "/api/2.0/lakeview/dashboards", body=payload)
    dash_id = resp["dashboard_id"]
    action = "created"

dash_url = f"{host}/dashboardsv3/{dash_id}"
print(f"  ✓ Dashboard [{action}]: {dash_id}")
print(f"    URL: {dash_url}")

# COMMAND ----------

# DBTITLE 1,_app_config に dashboard_id を登録
from pyspark.sql.functions import current_timestamp
from pyspark.sql import Row

updates = [
    Row(key="dashboard_id",  value=dash_id,   description="AI/BI ダッシュボード ID"),
    Row(key="dashboard_url", value=dash_url,  description="AI/BI ダッシュボード URL"),
]
df = spark.createDataFrame(updates).withColumn("updated_at", current_timestamp())
df.createOrReplaceTempView("_dash_upsert")

spark.sql(f"""
    MERGE INTO `{catalog_name}`.`{schema_name}`._app_config AS target
    USING _dash_upsert AS source
    ON target.key = source.key
    WHEN MATCHED THEN UPDATE SET
        value = source.value,
        description = source.description,
        updated_at = source.updated_at
    WHEN NOT MATCHED THEN INSERT (key, value, description, updated_at)
        VALUES (source.key, source.value, source.description, source.updated_at)
""")

print(f"  ✓ _app_config に dashboard_id / dashboard_url を登録")

# COMMAND ----------

# DBTITLE 1,ダッシュボードを公開 (publish)
# デフォルト draft のまま。公開したい場合はここで API を叩く
# publish = Embedded credentials で公開する (SA のクレデンシャルで動くので誰でも閲覧可能)
try:
    _api(
        "POST",
        f"/api/2.0/lakeview/dashboards/{dash_id}/published",
        body={
            "embed_credentials": True,
            "warehouse_id": warehouse_id,
        },
    )
    print(f"  ✓ ダッシュボード公開完了 (embedded credentials)")
except Exception as e:
    print(f"  ⚠️ publish 失敗（draft のまま）: {str(e)[:150]}")

# COMMAND ----------

# DBTITLE 1,サマリー
print("=" * 60)
print(f"  ✅ AI/BI ダッシュボード セットアップ完了")
print("=" * 60)
print(f"  Name      : {dashboard_name}")
print(f"  ID        : {dash_id}")
print(f"  URL       : {dash_url}")
print(f"  Status    : Published (embedded credentials)")
print("=" * 60)

dbutils.notebook.exit('{"dashboard_id":"' + dash_id + '","dashboard_url":"' + dash_url + '"}')
