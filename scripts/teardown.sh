#!/usr/bin/env bash
# =====================================================================
# scripts/teardown.sh — car-agent デモの全削除スクリプト
#
# このスクリプトは現在デプロイされている car-agent デモのリソースを
# すべて削除します。他 SA への配布前に「真っさらな状態から再デプロイする」
# フローを検証するために使ってください。
#
# 削除順序 (依存関係に従う):
#   1. _app_config からリソース ID を取得
#   2. AI/BI Dashboard        (Lakeview API)
#   3. Multi-Agent Supervisor  (Serving endpoint)
#   4. Knowledge Assistant     (Serving endpoint)
#   5. Genie Spaces ×3         (Genie API)
#   6. DAB 管理リソース        (Job / App / workspace files) via bundle destroy
#   7. [optional] UC Schema    (--drop-schema 指定時のみ)
#
# 使い方:
#   ./scripts/teardown.sh --profile <profile>                             # UC 以外を全削除
#   ./scripts/teardown.sh --profile <profile> --drop-schema               # UC Schema も削除
#   ./scripts/teardown.sh --profile <profile> --drop-schema --yes         # 確認なしで実行
#
# 依存: databricks CLI v0.230+, python3 (JSON パース用)
# =====================================================================
set -euo pipefail

# ---- デフォルト値 (databricks.yml と同期) ----
PROFILE=""
TARGET="dev"
CATALOG="konomi_demo_catalog"
SCHEMA="car_agent"
WAREHOUSE_ID="348478745ad64b30"
YES="false"
DROP_SCHEMA="false"

usage() {
  cat <<EOF
Usage: $0 --profile <profile> [options]

Options:
  --profile <name>       Databricks CLI profile (必須)
  --target <name>        DAB target (default: dev)
  --catalog <name>       UC catalog 名 (default: $CATALOG)
  --schema <name>        UC schema 名 (default: $SCHEMA)
  --warehouse-id <id>    _app_config 読み取り用 warehouse ID (default: $WAREHOUSE_ID)
  --drop-schema          UC schema も DROP CASCADE で削除
  --yes, -y              確認プロンプトをスキップ
  -h, --help             このヘルプ表示
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)       PROFILE="$2"; shift 2;;
    --target|-t)     TARGET="$2"; shift 2;;
    --catalog)       CATALOG="$2"; shift 2;;
    --schema)        SCHEMA="$2"; shift 2;;
    --warehouse-id)  WAREHOUSE_ID="$2"; shift 2;;
    --drop-schema)   DROP_SCHEMA="true"; shift;;
    --yes|-y)        YES="true"; shift;;
    -h|--help)       usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 1;;
  esac
done

if [[ -z "$PROFILE" ]]; then
  echo "ERROR: --profile は必須です" >&2
  usage
  exit 1
fi

# 新 CLI を PATH 優先（legacy CLI 回避）
export PATH="/opt/homebrew/bin:$PATH"

echo "======================================================================"
echo "  car-agent teardown"
echo "  Profile      : $PROFILE"
echo "  Target       : $TARGET"
echo "  Catalog      : $CATALOG"
echo "  Schema       : $SCHEMA"
echo "  Warehouse    : $WAREHOUSE_ID"
echo "  Drop schema  : $DROP_SCHEMA"
echo "======================================================================"

# =====================================================================
# 1. _app_config からリソース ID を取得
# =====================================================================
echo ""
echo "=== 1. _app_config から ID を取得 ==="

CFG_JSON=$(
  databricks api post /api/2.0/sql/statements \
    --profile "$PROFILE" \
    --json "$(cat <<JSON
{
  "warehouse_id": "$WAREHOUSE_ID",
  "statement": "SELECT key, value FROM \`$CATALOG\`.\`$SCHEMA\`._app_config",
  "wait_timeout": "30s"
}
JSON
)" 2>&1 || echo '{}'
)

# python3 で JSON を shell 変数に展開
CFG_ENV=$(echo "$CFG_JSON" | python3 <<'PYEOF'
import json, sys, shlex
try:
    raw = sys.stdin.read()
    d = json.loads(raw) if raw.strip() else {}
    rows = d.get("result", {}).get("data_array") or []
    for row in rows:
        if len(row) >= 2 and row[0]:
            k, v = row[0], row[1] or ""
            varname = "CFG_" + k.upper().replace("-", "_").replace(".", "_")
            print(f"{varname}={shlex.quote(v)}")
    print(f"CFG_ROWS={len(rows)}")
except Exception as e:
    print(f"CFG_ROWS=0", file=sys.stderr)
    print(f"# parse failed: {e}", file=sys.stderr)
    sys.exit(0)
PYEOF
)

if [[ -n "$CFG_ENV" ]]; then
  eval "$CFG_ENV"
fi

echo "  取得行数 : ${CFG_ROWS:-0}"
echo "  主要 ID:"
echo "    dashboard_id        : ${CFG_DASHBOARD_ID:-<none>}"
echo "    mas_endpoint        : ${CFG_MAS_ENDPOINT:-<none>}"
echo "    ka_endpoint         : ${CFG_KA_ENDPOINT:-<none>}"
echo "    genie_vehicle_id    : ${CFG_GENIE_VEHICLE_ID:-<none>}"
echo "    genie_mypage_id     : ${CFG_GENIE_MYPAGE_ID:-<none>}"
echo "    genie_dashboard_id  : ${CFG_GENIE_DASHBOARD_ID:-<none>}"

# =====================================================================
# 2. 確認
# =====================================================================
if [[ "$YES" != "true" ]]; then
  echo ""
  echo "----------------------------------------------------------------------"
  echo "  これから削除します:"
  echo "    - AI/BI Dashboard / MAS / KA / Genie Spaces ×3"
  echo "    - DAB 管理: Job / App / workspace files (bundle destroy -t $TARGET)"
  if [[ "$DROP_SCHEMA" == "true" ]]; then
    echo "    - UC Schema: $CATALOG.$SCHEMA (DROP ... CASCADE)"
  fi
  echo "----------------------------------------------------------------------"
  read -p "続行しますか？ (yes/No): " CONFIRM
  if [[ "$CONFIRM" != "yes" ]]; then
    echo "キャンセル"
    exit 0
  fi
fi

# ヘルパ関数: エラーを握りつぶして継続
try_delete() {
  local desc="$1"; shift
  echo ""
  echo "=== $desc ==="
  if "$@" 2>&1 | tail -20; then
    echo "  ✓ OK"
  else
    echo "  ⚠️  失敗/既に削除済み (続行)"
  fi
}

# =====================================================================
# 3. Dashboard 削除
# =====================================================================
if [[ -n "${CFG_DASHBOARD_ID:-}" ]]; then
  try_delete "AI/BI Dashboard (id=$CFG_DASHBOARD_ID)" \
    databricks api delete "/api/2.0/lakeview/dashboards/$CFG_DASHBOARD_ID" --profile "$PROFILE"
fi

# =====================================================================
# 4. MAS endpoint 削除
# =====================================================================
if [[ -n "${CFG_MAS_ENDPOINT:-}" ]]; then
  try_delete "MAS serving endpoint ($CFG_MAS_ENDPOINT)" \
    databricks serving-endpoints delete "$CFG_MAS_ENDPOINT" --profile "$PROFILE"
fi

# =====================================================================
# 5. KA endpoint 削除
# =====================================================================
if [[ -n "${CFG_KA_ENDPOINT:-}" ]]; then
  try_delete "KA serving endpoint ($CFG_KA_ENDPOINT)" \
    databricks serving-endpoints delete "$CFG_KA_ENDPOINT" --profile "$PROFILE"
fi

# =====================================================================
# 6. Genie Spaces 削除
# =====================================================================
for gkey in CFG_GENIE_VEHICLE_ID CFG_GENIE_MYPAGE_ID CFG_GENIE_DASHBOARD_ID; do
  gid="${!gkey:-}"
  if [[ -n "$gid" ]]; then
    try_delete "Genie Space $gkey=$gid" \
      databricks api delete "/api/2.0/genie/spaces/$gid" --profile "$PROFILE"
  fi
done

# =====================================================================
# 7. DAB リソース削除 (Job + App + workspace files)
# =====================================================================
echo ""
echo "=== DAB 管理リソース削除 (bundle destroy -t $TARGET) ==="
echo "  cmd: databricks bundle destroy -t $TARGET --profile $PROFILE --auto-approve"
databricks bundle destroy -t "$TARGET" --profile "$PROFILE" --auto-approve || echo "  ⚠️  bundle destroy failed"

# =====================================================================
# 8. UC Schema 削除 (optional)
# =====================================================================
if [[ "$DROP_SCHEMA" == "true" ]]; then
  echo ""
  echo "=== UC Schema 削除: $CATALOG.$SCHEMA CASCADE ==="
  databricks api post /api/2.0/sql/statements \
    --profile "$PROFILE" \
    --json "$(cat <<JSON
{
  "warehouse_id": "$WAREHOUSE_ID",
  "statement": "DROP SCHEMA IF EXISTS \`$CATALOG\`.\`$SCHEMA\` CASCADE",
  "wait_timeout": "60s"
}
JSON
)" && echo "  ✓ Schema dropped" || echo "  ⚠️  Drop failed"
fi

echo ""
echo "======================================================================"
echo "  teardown 完了"
echo ""
echo "  次のステップ（真のクリーンスレート検証）:"
echo "    1. ローカルの clone を削除して git から再取得:"
echo "       rm -rf car_agent && git clone <repo-url>"
echo "    2. databricks.yml の catalog/schema/warehouse_id を自分用に書き換え"
echo "    3. databricks bundle deploy --profile $PROFILE"
echo "    4. databricks bundle run setup_demo --profile $PROFILE"
echo "    5. databricks bundle run car_agent --profile $PROFILE"
echo "======================================================================"
