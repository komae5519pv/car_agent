# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1B3139 100%); padding: 20px 30px; border-radius: 10px; margin-bottom: 20px;">
# MAGIC   <div style="display: flex; align-items: center; gap: 15px;">
# MAGIC     <img src="https://www.databricks.com/wp-content/uploads/2022/06/db-nav-logo.svg" width="40" style="filter: brightness(2);"/>
# MAGIC     <div>
# MAGIC       <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">car-agent セットアップ</h1>
# MAGIC       <p style="color: #B0BEC5; margin: 5px 0 0 0; font-size: 16px;">最終サマリ出力</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #388E3C; background-color: #E8F5E9; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h3 style="color: #388E3C; margin-top: 0;">🎉 このノートブックの目的</h3>
# MAGIC   <p>setup_demo job の最後に実行され、作成された全リソースの情報をサマリ表示します。</p>
# MAGIC   <p>SA は Job の出力 or この notebook を開いて「何がどこに作られたか」を一覧確認できます。</p>
# MAGIC </div>

# COMMAND ----------

# DBTITLE 1,パラメータ取得
def _get_widget(name: str, default: str) -> str:
    try:
        return dbutils.widgets.get(name)
    except Exception:
        return default

catalog_name = _get_widget("catalog", "konomi_demo_catalog")
schema_name  = _get_widget("schema",  "car_agent")

# COMMAND ----------

# DBTITLE 1,_app_config から全情報取得
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
host = w.config.host.rstrip("/")

rows = spark.sql(
    f"SELECT key, value FROM `{catalog_name}`.`{schema_name}`._app_config"
).collect()
cfg = {row["key"]: row["value"] for row in rows}

# テーブル数を数える
table_count = spark.sql(
    f"SHOW TABLES IN `{catalog_name}`.`{schema_name}`"
).count()

# Volume 一覧
volumes = [r["volume_name"] for r in spark.sql(
    f"SHOW VOLUMES IN `{catalog_name}`.`{schema_name}`"
).collect()]

# COMMAND ----------

# DBTITLE 1,サマリー出力
def _box_line(label: str, value: str, width: int = 70) -> str:
    return f"  {label:<22s}: {value}"

print()
print("=" * 70)
print("  🎉  [car-agent] セットアップ完了サマリ")
print("=" * 70)
print()
print("  ── Unity Catalog ──")
print(_box_line("Catalog / Schema",    f"{catalog_name}.{schema_name}"))
print(_box_line("Tables",              f"{table_count} 件"))
print(_box_line("Volumes",             ", ".join(volumes)))
print(_box_line("Config table",        f"{catalog_name}.{schema_name}._app_config"))
print()
print("  ── Genie Spaces ──")
for label, key in [
    ("車両営業アシスタント",    "genie_vehicle_id"),
    ("営業マイページ",          "genie_mypage_id"),
    ("営業データ",              "genie_dashboard_id"),
]:
    space_id = cfg.get(key, "")
    url = f"{host}/genie/rooms/{space_id}" if space_id else "(未作成)"
    print(_box_line(label, f"{space_id}"))
    print(_box_line("",    f"→ {url}"))
print()
print("  ── Agent Bricks ──")
print(_box_line("Knowledge Assistant", cfg.get("ka_name", "(未作成)")))
print(_box_line("  endpoint",          cfg.get("ka_endpoint", "(未作成)")))
print(_box_line("Multi-Agent Supv",    cfg.get("mas_name", "(未作成)")))
print(_box_line("  endpoint",          cfg.get("mas_endpoint", "(未作成)")))
print()
print("  ── Databricks App ──")
print(_box_line("App name",            cfg.get("app_name", "")))
print(_box_line("App URL",             cfg.get("app_url", "(未デプロイ)")))
print(_box_line("Service Principal",   cfg.get("app_sp_client_id", "")))
print()
print("  ── AI/BI Dashboard ──")
print(_box_line("Dashboard",           cfg.get("dashboard_id", "(未作成)")))
print(_box_line("URL",                 cfg.get("dashboard_url", "(未作成)")))
print()
print("=" * 70)
print("  ✅  全セットアップタスク正常終了")
print("=" * 70)
print()
print(f"  📋 各リソースの確認:")
print(f"     ・ Catalog Explorer: {host}/explore/data/{catalog_name}/{schema_name}")
print(f"     ・ Genie:             {host}/genie")
print(f"     ・ Agent Bricks:      {host}/agent-bricks")
print(f"     ・ Apps:              {host}/apps")
print(f"     ・ Jobs:              {host}/jobs")
print()
print("-" * 70)
print("  ⚠️  残作業: Genie Space 3 つに手動で以下を設定してください（API 非対応）:")
print("     1. 「一般的な指示」テキスト")
print("     2. UC 関数 current_sales_rep_email() の curated tool 登録")
print(f"     手順: docs/MANUAL_GENIE_SETUP.md 参照")
print("-" * 70)
print()
print(f"  🔎 再セットアップしたい場合:")
print(f"     databricks bundle run setup_demo")
print()
print("=" * 70)
