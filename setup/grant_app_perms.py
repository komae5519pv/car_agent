# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC
# MAGIC <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1B3139 100%); padding: 20px 30px; border-radius: 10px; margin-bottom: 20px;">
# MAGIC   <div style="display: flex; align-items: center; gap: 15px;">
# MAGIC     <img src="https://www.databricks.com/wp-content/uploads/2022/06/db-nav-logo.svg" width="40" style="filter: brightness(2);"/>
# MAGIC     <div>
# MAGIC       <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">car-agent セットアップ</h1>
# MAGIC       <p style="color: #B0BEC5; margin: 5px 0 0 0; font-size: 16px;">App Service Principal への全権限付与</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h3 style="color: #1976d2; margin-top: 0;">📋 このノートブックの目的</h3>
# MAGIC   <p>Databricks App の service principal に、実行に必要な全権限を付与します。</p>
# MAGIC   <p>付与する権限:</p>
# MAGIC   <ul>
# MAGIC     <li><b>Unity Catalog</b>: USE CATALOG / USE SCHEMA / SELECT / READ VOLUME</li>
# MAGIC     <li><b>Genie Space ×3</b>: CAN_RUN</li>
# MAGIC     <li><b>Knowledge Assistant endpoint</b>: CAN_QUERY</li>
# MAGIC     <li><b>Multi-Agent Supervisor endpoint</b>: CAN_QUERY</li>
# MAGIC   </ul>
# MAGIC   <p><strong>実行者要件:</strong> catalog / schema の MANAGE 権限、serving endpoints / Genie の CAN_MANAGE</p>
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

print(f"  Catalog   : {catalog_name}")
print(f"  Schema    : {schema_name}")
print(f"  App name  : {app_name}")

# COMMAND ----------

# DBTITLE 1,API ヘルパー & App SP 取得
import requests
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
host = w.config.host.rstrip("/")
headers = w.config.authenticate()

def _api(method: str, path: str, body: dict | None = None, ok_404: bool = False) -> dict:
    resp = requests.request(method, f"{host}{path}", headers=headers, json=body)
    if ok_404 and resp.status_code == 404:
        return {}
    if not resp.ok:
        raise RuntimeError(f"{method} {path}: {resp.status_code} {resp.text[:500]}")
    return resp.json() if resp.text else {}

app = w.apps.get(name=app_name)
sp_client_id = app.service_principal_client_id
print(f"  App URL      : {app.url}")
print(f"  App SP       : {sp_client_id}")

# COMMAND ----------

# DBTITLE 1,Unity Catalog 権限付与
grants_sql = [
    (f"GRANT USE CATALOG ON CATALOG `{catalog_name}` TO `{sp_client_id}`", "USE CATALOG on catalog"),
    (f"GRANT USE SCHEMA ON SCHEMA `{catalog_name}`.`{schema_name}` TO `{sp_client_id}`", "USE SCHEMA"),
    (f"GRANT SELECT ON SCHEMA `{catalog_name}`.`{schema_name}` TO `{sp_client_id}`", "SELECT on schema"),
    (f"GRANT READ VOLUME ON SCHEMA `{catalog_name}`.`{schema_name}` TO `{sp_client_id}`", "READ VOLUME on schema"),
]

for sql, desc in grants_sql:
    try:
        spark.sql(sql)
        print(f"  ✓ UC: {desc}")
    except Exception as e:
        print(f"  ✗ UC: {desc}: {str(e)[:150]}")

# COMMAND ----------

# DBTITLE 1,Genie Space 権限付与 (CAN_RUN)
# Genie Space ID を display_name で解決
genie_resp = _api("GET", "/api/2.0/genie/spaces")
genie_by_name = {s["title"]: s["space_id"] for s in genie_resp.get("spaces", [])}

genie_targets = [
    (genie_vehicle_name,   "車両営業"),
    (genie_mypage_name,    "マイページ"),
    (genie_dashboard_name, "ダッシュボード"),
]

for display_name, label in genie_targets:
    space_id = genie_by_name.get(display_name)
    if not space_id:
        print(f"  ⚠️ Genie [{label}] が見つからない: {display_name}")
        continue
    try:
        # Genie Space permissions: PATCH /api/2.0/permissions/genie/{space_id}
        _api(
            "PATCH",
            f"/api/2.0/permissions/genie/{space_id}",
            body={
                "access_control_list": [{
                    "service_principal_name": sp_client_id,
                    "permission_level": "CAN_RUN",
                }]
            },
        )
        print(f"  ✓ Genie [{label}]: CAN_RUN ({space_id})")
    except Exception as e:
        print(f"  ✗ Genie [{label}]: {str(e)[:150]}")

# COMMAND ----------

# DBTITLE 1,Serving Endpoint (KA / MAS) 権限付与 (CAN_QUERY)
# KA endpoint 名を解決
ka_resp = _api("GET", "/api/2.1/knowledge-assistants")
ka_by_name = {k["display_name"]: k for k in ka_resp.get("knowledge_assistants", [])}
ka_endpoint = ka_by_name.get(ka_name, {}).get("endpoint_name", "")

# MAS endpoint 名を解決
tiles_resp = _api("GET", "/api/2.0/tiles")
mas_endpoint = ""
for t in tiles_resp.get("tiles", []):
    if t.get("tile_type") == "MAS" and t.get("name") == mas_name:
        mas_endpoint = t.get("serving_endpoint_name", "")
        break

def _grant_endpoint_query(endpoint_name: str, label: str):
    if not endpoint_name:
        print(f"  ⚠️ {label} endpoint 名が不明")
        return
    try:
        ep = w.serving_endpoints.get(name=endpoint_name)
        ep_id = ep.id
        _api(
            "PATCH",
            f"/api/2.0/permissions/serving-endpoints/{ep_id}",
            body={
                "access_control_list": [{
                    "service_principal_name": sp_client_id,
                    "permission_level": "CAN_QUERY",
                }]
            },
        )
        print(f"  ✓ Endpoint [{label}]: CAN_QUERY ({endpoint_name})")
    except Exception as e:
        print(f"  ✗ Endpoint [{label}]: {str(e)[:150]}")

_grant_endpoint_query(ka_endpoint, "KA")
_grant_endpoint_query(mas_endpoint, "MAS")

# COMMAND ----------

# DBTITLE 1,サマリー
print("=" * 60)
print(f"  ✅ 権限付与完了: {app_name}")
print("=" * 60)
print(f"  App URL       : {app.url}")
print(f"  App SP        : {sp_client_id}")
print(f"  Target UC     : {catalog_name}.{schema_name}")
print(f"  Genie Spaces  : 3 (vehicle / mypage / dashboard) - CAN_RUN")
print(f"  KA endpoint   : {ka_endpoint} - CAN_QUERY")
print(f"  MAS endpoint  : {mas_endpoint} - CAN_QUERY")
print("=" * 60)
