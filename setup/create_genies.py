# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1B3139 100%); padding: 20px 30px; border-radius: 10px; margin-bottom: 20px;">
# MAGIC   <div style="display: flex; align-items: center; gap: 15px;">
# MAGIC     <img src="https://www.databricks.com/wp-content/uploads/2022/06/db-nav-logo.svg" width="40" style="filter: brightness(2);"/>
# MAGIC     <div>
# MAGIC       <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">car-agent セットアップ</h1>
# MAGIC       <p style="color: #B0BEC5; margin: 5px 0 0 0; font-size: 16px;">Genie Space ×3 の自動作成</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h3 style="color: #1976d2; margin-top: 0;">📋 このノートブックの目的</h3>
# MAGIC   <p><code>setup/genie_spaces.yaml</code> を読み込み、3 つの Genie Space を自動作成/更新します（冪等）。</p>
# MAGIC   <p>作成されるもの:</p>
# MAGIC   <ul>
# MAGIC     <li>車両営業アシスタント Genie（MAS の Ask AI ツール用）</li>
# MAGIC     <li>営業マイページ Genie（アプリのマイページ用）</li>
# MAGIC     <li>営業データ Genie（AI/BI ダッシュボード用）</li>
# MAGIC   </ul>
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
warehouse_id         = _get_widget("warehouse_id",         "348478745ad64b30")
genie_vehicle_name   = _get_widget("genie_vehicle_name",   "[car-agent] 車両営業アシスタント")
genie_mypage_name    = _get_widget("genie_mypage_name",    "[car-agent] 営業マイページ")
genie_dashboard_name = _get_widget("genie_dashboard_name", "[car-agent] 営業データ")

print(f"  Catalog        : {catalog_name}")
print(f"  Schema         : {schema_name}")
print(f"  Warehouse ID   : {warehouse_id}")

# COMMAND ----------

# DBTITLE 1,YAML 定義ファイルの読込
# MAGIC %pip install pyyaml -q
# COMMAND ----------
dbutils.library.restartPython()

# COMMAND ----------

import os
import yaml

# widget 再取得（restartPython 後）
def _get_widget(name: str, default: str) -> str:
    try:
        return dbutils.widgets.get(name)
    except Exception:
        return default

catalog_name         = _get_widget("catalog",              "konomi_demo_catalog")
schema_name          = _get_widget("schema",               "car_agent")
warehouse_id         = _get_widget("warehouse_id",         "348478745ad64b30")
genie_vehicle_name   = _get_widget("genie_vehicle_name",   "[car-agent] 車両営業アシスタント")
genie_mypage_name    = _get_widget("genie_mypage_name",    "[car-agent] 営業マイページ")
genie_dashboard_name = _get_widget("genie_dashboard_name", "[car-agent] 営業データ")

# このノートブック (setup/create_genies.py) と同じ階層の genie_spaces.yaml を読む
notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
notebook_dir = os.path.dirname(notebook_path)
yaml_path = f"/Workspace{notebook_dir}/genie_spaces.yaml"

with open(yaml_path) as f:
    config = yaml.safe_load(f)

display_name_map = {
    "genie_vehicle_name":   genie_vehicle_name,
    "genie_mypage_name":    genie_mypage_name,
    "genie_dashboard_name": genie_dashboard_name,
}

print(f"  Loaded: {len(config['spaces'])} Genie Space definitions")

# COMMAND ----------

# DBTITLE 1,Genie Space 作成/更新 (REST API)
import requests
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()
host = w.config.host.rstrip("/")
headers = w.config.authenticate()

def _api(method: str, path: str, body: dict | None = None) -> dict:
    url = f"{host}{path}"
    resp = requests.request(method, url, headers=headers, json=body)
    if not resp.ok:
        raise RuntimeError(f"{method} {path}: {resp.status_code} {resp.text[:500]}")
    return resp.json() if resp.text else {}

# 既存 Space を list して、同じ display_name のものを探す
list_resp = _api("GET", "/api/2.0/genie/spaces")
existing_by_name = {s.get("title") or s.get("display_name"): s for s in list_resp.get("spaces", [])}
print(f"  既存 Genie Space: {len(existing_by_name)} 件")

# COMMAND ----------

# DBTITLE 1,各 Space を idempotent に作成
import json as _json
import uuid

def _build_serialized_space(tables: list[str], sample_questions: list[str]) -> str:
    """Genie Space の serialized_space JSON を構築する。

    POST /api/2.0/genie/spaces では serialized_space が必須で、
    中に sample_questions と data_sources.tables を入れる。
    """
    body = {
        "version": 2,
        "config": {
            "sample_questions": [
                {"id": uuid.uuid4().hex, "question": [q]} for q in sample_questions
            ],
        },
        "data_sources": {
            # API requires tables sorted by identifier
            "tables": [{"identifier": t} for t in sorted(tables)],
        },
    }
    return _json.dumps(body, ensure_ascii=False)


results = {}
for sp in config["spaces"]:
    key = sp["key"]
    display_name = display_name_map[sp["display_name_var"]]
    tables = [
        t.replace("${catalog}", catalog_name).replace("${schema}", schema_name)
        for t in sp["tables"]
    ]
    serialized = _build_serialized_space(tables, sp["sample_questions"])

    if display_name in existing_by_name:
        # UPDATE: サブ構造をバラで送る形式でOK
        space_id = existing_by_name[display_name].get("space_id") or existing_by_name[display_name].get("id")
        _api("PATCH", f"/api/2.0/genie/spaces/{space_id}", body={
            "title": display_name,
            "description": sp["description"].strip(),
            "warehouse_id": warehouse_id,
            "tables": [{"full_name": t} for t in tables],
            "sample_questions": [{"question": q} for q in sp["sample_questions"]],
        })
        action = "updated"
    else:
        # CREATE: serialized_space が必須
        resp = _api("POST", "/api/2.0/genie/spaces", body={
            "title": display_name,
            "description": sp["description"].strip(),
            "warehouse_id": warehouse_id,
            "serialized_space": serialized,
        })
        space_id = resp.get("space_id") or resp.get("id")
        action = "created"

    results[key] = {"space_id": space_id, "display_name": display_name, "action": action}
    print(f"  ✓ [{action}] {display_name}  →  {space_id}")

# COMMAND ----------

# DBTITLE 1,サマリー
print("=" * 60)
print(f"  ✅ Genie Space セットアップ完了 ({len(results)} 件)")
print("=" * 60)
for key, info in results.items():
    print(f"  {key:20s} : {info['space_id']}  ({info['display_name']})")
print("=" * 60)

# 後続タスク (register_config) から参照できるよう notebook の task output に記録
dbutils.notebook.exit(
    '{"genie_vehicle_id":"' + results["vehicle_assistant"]["space_id"] +
    '","genie_mypage_id":"' + results["sales_mypage"]["space_id"] +
    '","genie_dashboard_id":"' + results["sales_dashboard"]["space_id"] + '"}'
)
