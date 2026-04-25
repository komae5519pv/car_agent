# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1B3139 100%); padding: 20px 30px; border-radius: 10px; margin-bottom: 20px;">
# MAGIC   <div style="display: flex; align-items: center; gap: 15px;">
# MAGIC     <img src="https://www.databricks.com/wp-content/uploads/2022/06/db-nav-logo.svg" width="40" style="filter: brightness(2);"/>
# MAGIC     <div>
# MAGIC       <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">car-agent セットアップ</h1>
# MAGIC       <p style="color: #B0BEC5; margin: 5px 0 0 0; font-size: 16px;">Multi-Agent Supervisor 自動作成</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h3 style="color: #1976d2; margin-top: 0;">📋 このノートブックの目的</h3>
# MAGIC   <p><code>setup/multi_agent_supervisor.yaml</code> を読み込み、Multi-Agent Supervisor を自動作成/更新します（冪等）。</p>
# MAGIC   <p>依存タスク: create_genies, create_ka（配下エージェントの ID をこれらから取得）</p>
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

mas_name              = _get_widget("mas_name",              "car-agent-supervisor")
ka_name               = _get_widget("ka_name",               "car-agent-knowledge")
genie_vehicle_name    = _get_widget("genie_vehicle_name",    "[car-agent] 車両営業アシスタント")
genie_mypage_name     = _get_widget("genie_mypage_name",     "[car-agent] 営業マイページ")
genie_dashboard_name  = _get_widget("genie_dashboard_name",  "[car-agent] 営業データ")

print(f"  MAS name         : {mas_name}")
print(f"  KA name          : {ka_name}")
print(f"  Genie vehicle    : {genie_vehicle_name}")
print(f"  Genie mypage     : {genie_mypage_name}")
print(f"  Genie dashboard  : {genie_dashboard_name}")

# COMMAND ----------

# DBTITLE 1,YAML 読込
import os
import yaml

notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
yaml_path = f"/Workspace{os.path.dirname(notebook_path)}/multi_agent_supervisor.yaml"

with open(yaml_path) as f:
    config = yaml.safe_load(f)

# name variable → actual value マッピング
name_map = {
    "mas_name":             mas_name,
    "ka_name":              ka_name,
    "genie_vehicle_name":   genie_vehicle_name,
    "genie_mypage_name":    genie_mypage_name,
    "genie_dashboard_name": genie_dashboard_name,
}

print(f"  MAS agents defined: {len(config['agents'])}")

# COMMAND ----------

# DBTITLE 1,API ヘルパー
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

# COMMAND ----------

# DBTITLE 1,配下エージェントの ID を名前から解決
# Genie Space の ID を display_name で検索
genie_resp = _api("GET", "/api/2.0/genie/spaces")
genie_by_name = {s["title"]: s["space_id"] for s in genie_resp.get("spaces", [])}

# Knowledge Assistant の endpoint_name を display_name で検索
ka_resp = _api("GET", "/api/2.1/knowledge-assistants")
ka_by_name = {k["display_name"]: k for k in ka_resp.get("knowledge_assistants", [])}

# YAML の各 agent を API payload に変換
agents_payload = []
for agent_def in config["agents"]:
    if agent_def["type"] == "genie-space":
        name_var = agent_def["genie_space_name_var"]
        genie_display_name = name_map[name_var]
        if genie_display_name not in genie_by_name:
            raise RuntimeError(f"Genie Space 未発見: {genie_display_name} (先に create_genies を実行してください)")
        space_id = genie_by_name[genie_display_name]
        agents_payload.append({
            "name":        agent_def["name"],
            "description": agent_def["description"].strip(),
            "agent_type":  "genie-space",
            "genie_space": {"id": space_id},
        })
        print(f"  ✓ {agent_def['name']:20s} → Genie({genie_display_name}, id={space_id})")

    elif agent_def["type"] == "knowledge-assistant":
        name_var = agent_def["ka_name_var"]
        ka_display_name = name_map[name_var]
        if ka_display_name not in ka_by_name:
            raise RuntimeError(f"Knowledge Assistant 未発見: {ka_display_name} (先に create_ka を実行してください)")
        endpoint_name = ka_by_name[ka_display_name]["endpoint_name"]
        agents_payload.append({
            "name":             agent_def["name"],
            "description":      agent_def["description"].strip(),
            "agent_type":       "knowledge-assistant",
            "serving_endpoint": {"name": endpoint_name},
        })
        print(f"  ✓ {agent_def['name']:20s} → KA({ka_display_name}, endpoint={endpoint_name})")

    else:
        raise RuntimeError(f"未対応の agent type: {agent_def['type']}")

# COMMAND ----------

# DBTITLE 1,MAS の作成/更新（冪等）
# 既存 MAS を tiles 経由で検索 (tile_type=MAS, name=mas_name)
tiles_resp = _api("GET", "/api/2.0/tiles")
existing_mas = None
for t in tiles_resp.get("tiles", []):
    if t.get("tile_type") == "MAS" and t.get("name") == mas_name:
        existing_mas = t
        break

payload = {
    "name":         mas_name,
    "description":  config["description"].strip(),
    "instructions": config["instructions"].strip(),
    "agents":       agents_payload,
}

if existing_mas:
    # 既存 MAS を削除して作り直し（agents の完全置換が必要なため）
    tile_id = existing_mas["tile_id"]
    print(f"  既存 MAS 発見: tile_id={tile_id} → 再作成します")
    _api("DELETE", f"/api/2.0/tiles/{tile_id}")

resp = _api("POST", "/api/2.0/multi-agent-supervisors", body=payload)
mas_tile = resp["multi_agent_supervisor"]["tile"]
mas_tile_id = mas_tile["tile_id"]
mas_endpoint = mas_tile["serving_endpoint_name"]

print(f"  ✓ MAS 作成完了: tile_id={mas_tile_id}")
print(f"    endpoint: {mas_endpoint}")

# COMMAND ----------

# DBTITLE 1,Endpoint プロビジョン完了待ち (最大 20 分)
import time
from databricks.sdk.service.serving import EndpointStateReady

max_wait_sec = 20 * 60
poll_interval = 30
elapsed = 0

while elapsed < max_wait_sec:
    try:
        ep = w.serving_endpoints.get(name=mas_endpoint)
        state = ep.state.ready if ep.state else None
        print(f"  [{elapsed:4d}s] endpoint state = {state}")
        if state == EndpointStateReady.READY:
            break
    except Exception as e:
        print(f"  [{elapsed:4d}s] not accessible yet: {str(e)[:100]}")
    time.sleep(poll_interval)
    elapsed += poll_interval

if elapsed >= max_wait_sec:
    print(f"  ⚠️ Endpoint not READY within {max_wait_sec}s, continuing anyway")

# COMMAND ----------

# DBTITLE 1,サマリー
print("=" * 60)
print(f"  ✅ Multi-Agent Supervisor セットアップ完了")
print("=" * 60)
print(f"  Name      : {mas_name}")
print(f"  Tile ID   : {mas_tile_id}")
print(f"  Endpoint  : {mas_endpoint}")
print(f"  Agents    : {len(agents_payload)}")
for a in agents_payload:
    print(f"    - {a['name']:20s} ({a['agent_type']})")
print("=" * 60)

dbutils.notebook.exit(
    '{"mas_tile_id":"' + mas_tile_id + '","mas_endpoint":"' + mas_endpoint + '"}'
)
