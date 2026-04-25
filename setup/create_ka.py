# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1B3139 100%); padding: 20px 30px; border-radius: 10px; margin-bottom: 20px;">
# MAGIC   <div style="display: flex; align-items: center; gap: 15px;">
# MAGIC     <img src="https://www.databricks.com/wp-content/uploads/2022/06/db-nav-logo.svg" width="40" style="filter: brightness(2);"/>
# MAGIC     <div>
# MAGIC       <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">car-agent セットアップ</h1>
# MAGIC       <p style="color: #B0BEC5; margin: 5px 0 0 0; font-size: 16px;">Knowledge Assistant 自動作成</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h3 style="color: #1976d2; margin-top: 0;">📋 このノートブックの目的</h3>
# MAGIC   <p><code>setup/knowledge_assistant.yaml</code> を読み込み、Agent Bricks の Knowledge Assistant を自動作成/更新します（冪等）。</p>
# MAGIC   <p>処理フロー:</p>
# MAGIC   <ol>
# MAGIC     <li>display_name で既存 KA を検索</li>
# MAGIC     <li>存在しなければ create、存在すれば update</li>
# MAGIC     <li>Knowledge Sources を作成 (Volume 配下のファイルをインデックス化)</li>
# MAGIC     <li>endpoint が READY になるまでポーリング (最大 20 分)</li>
# MAGIC   </ol>
# MAGIC </div>

# COMMAND ----------

# MAGIC %pip install pyyaml -q

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

# DBTITLE 1,パラメータ取得
def _get_widget(name: str, default: str) -> str:
    try:
        return dbutils.widgets.get(name)
    except Exception:
        return default

catalog_name = _get_widget("catalog", "konomi_demo_catalog")
schema_name  = _get_widget("schema",  "car_agent")
ka_name      = _get_widget("ka_name", "car-agent-knowledge")

print(f"  Catalog  : {catalog_name}")
print(f"  Schema   : {schema_name}")
print(f"  KA name  : {ka_name}")

# COMMAND ----------

# DBTITLE 1,YAML 読込 + 変数置換
import os
import yaml

notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
yaml_path = f"/Workspace{os.path.dirname(notebook_path)}/knowledge_assistant.yaml"

with open(yaml_path) as f:
    raw = f.read()
config = yaml.safe_load(
    raw.replace("${catalog}", catalog_name).replace("${schema}", schema_name)
)

print(f"  KA definition loaded: {config['display_name_var']}")
print(f"  Sources             : {len(config['sources'])}")

# COMMAND ----------

# DBTITLE 1,Knowledge Assistant の作成/更新（冪等）
import requests
import time
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
host = w.config.host.rstrip("/")
headers = w.config.authenticate()
API_BASE = f"{host}/api/2.1/knowledge-assistants"

def _api(method: str, path: str, body: dict | None = None) -> dict:
    resp = requests.request(method, f"{host}{path}", headers=headers, json=body)
    if not resp.ok:
        raise RuntimeError(f"{method} {path}: {resp.status_code} {resp.text[:500]}")
    return resp.json() if resp.text else {}

# 既存 KA を検索
list_resp = _api("GET", "/api/2.1/knowledge-assistants")
existing = None
for ka in list_resp.get("knowledge_assistants", []):
    if ka.get("display_name") == ka_name:
        existing = ka
        break

payload = {
    "display_name": ka_name,
    "description":  config["description"].strip(),
    "instructions": config["instructions"].strip(),
}

if existing:
    ka_id = existing["id"]
    ka_full_name = existing["name"]  # "knowledge-assistants/{id}"
    # update (PATCH with update_mask)
    update_path = f"/api/2.1/{ka_full_name}?update_mask=description,instructions"
    _api("PATCH", update_path, body=payload)
    action = "updated"
else:
    # create
    resp = _api("POST", "/api/2.1/knowledge-assistants", body=payload)
    ka_id = resp["id"]
    ka_full_name = resp["name"]
    action = "created"

endpoint_name = (existing or resp).get("endpoint_name")
print(f"  ✓ KA [{action}] {ka_name} (id={ka_id}, endpoint={endpoint_name})")

# COMMAND ----------

# DBTITLE 1,Knowledge Sources の作成/更新（冪等）
# 既存 sources を取得
sources_resp = _api("GET", f"/api/2.1/{ka_full_name}/knowledge-sources")
existing_sources = {s.get("display_name"): s for s in sources_resp.get("knowledge_sources", [])}

for src in config["sources"]:
    src_payload = {
        "display_name": src["display_name"],
        "description":  src["description"].strip(),
        "source_type":  src["source_type"],
        "files":        {"path": src["path"]},
    }
    if src["display_name"] in existing_sources:
        existing_src = existing_sources[src["display_name"]]
        _api(
            "PATCH",
            f"/api/2.1/{existing_src['name']}?update_mask=description,files",
            body=src_payload,
        )
        print(f"  ✓ Source [updated] {src['display_name']} ({src['path']})")
    else:
        _api("POST", f"/api/2.1/{ka_full_name}/knowledge-sources", body=src_payload)
        print(f"  ✓ Source [created] {src['display_name']} ({src['path']})")

# COMMAND ----------

# DBTITLE 1,Endpoint プロビジョン完了待ち
# KA 再取得して endpoint_name を取得
ka_resp = _api("GET", f"/api/2.1/{ka_full_name}")
endpoint_name = ka_resp["endpoint_name"]
print(f"  Endpoint: {endpoint_name}")

# Serving endpoint のステータスをポーリング (最大 20 分)
from databricks.sdk.service.serving import EndpointStateReady

max_wait_sec = 20 * 60
poll_interval = 30
elapsed = 0

while elapsed < max_wait_sec:
    try:
        ep = w.serving_endpoints.get(name=endpoint_name)
        state = ep.state.ready if ep.state else None
        print(f"  [{elapsed:4d}s] endpoint state = {state}")
        if state == EndpointStateReady.READY:
            break
    except Exception as e:
        print(f"  [{elapsed:4d}s] endpoint not accessible yet: {str(e)[:100]}")
    time.sleep(poll_interval)
    elapsed += poll_interval

if elapsed >= max_wait_sec:
    print(f"  ⚠️ Endpoint not READY within {max_wait_sec}s, continuing anyway")

# COMMAND ----------

# DBTITLE 1,サマリー
print("=" * 60)
print(f"  ✅ Knowledge Assistant セットアップ完了")
print("=" * 60)
print(f"  Name         : {ka_name}")
print(f"  ID           : {ka_id}")
print(f"  Endpoint     : {endpoint_name}")
print(f"  Volume path  : {config['sources'][0]['path']}")
print("=" * 60)

dbutils.notebook.exit(
    '{"ka_id":"' + ka_id + '","ka_endpoint":"' + endpoint_name + '"}'
)
