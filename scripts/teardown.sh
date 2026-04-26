#!/usr/bin/env bash
# =====================================================================
# scripts/teardown.sh — car-agent デモの全削除スクリプト
#
# このスクリプトは現在デプロイされている car-agent デモのリソースを
# すべて削除します。他 SA への配布前に「真っさらな状態から再デプロイする」
# フローを検証するために使ってください。
#
# 削除順序 (依存関係に従う):
#   1. _app_config からリソース ID を取得 (カタログ/スキーマは引数指定)
#   2. AI/BI Dashboard        (Lakeview API: /api/2.0/lakeview/dashboards/{id})
#   3. Multi-Agent Supervisor  (Agent Bricks tile: /api/2.0/tiles/{id})
#   4. Knowledge Assistant     (Agent Bricks tile: /api/2.0/tiles/{id})
#   5. Genie Spaces ×3         (Genie API: /api/2.0/genie/spaces/{id})
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
KA_NAME="car-agent-knowledge"
MAS_NAME="car-agent-supervisor"
GENIE_VEHICLE_NAME="[car-agent] 車両営業アシスタント"
GENIE_MYPAGE_NAME="[car-agent] 営業マイページ"
GENIE_DASHBOARD_NAME="[car-agent] 営業データ"
DASHBOARD_NAME="[car-agent] 車両販売ダッシュボード"
YES="false"
DROP_SCHEMA="false"

usage() {
  cat <<EOF
Usage: $0 --profile <profile> [options]

Options:
  --profile <name>         Databricks CLI profile (必須)
  --target <name>          DAB target (default: dev)
  --catalog <name>         UC catalog 名 (default: $CATALOG)
  --schema <name>          UC schema 名 (default: $SCHEMA)
  --ka-name <name>         Knowledge Assistant 名 (default: $KA_NAME)
  --mas-name <name>        Multi-Agent Supervisor 名 (default: $MAS_NAME)
  --genie-vehicle-name <n> Genie 車両営業 Space 名 (default: "$GENIE_VEHICLE_NAME")
  --genie-mypage-name <n>  Genie マイページ Space 名 (default: "$GENIE_MYPAGE_NAME")
  --genie-dashboard-name <n> Genie 営業データ Space 名 (default: "$GENIE_DASHBOARD_NAME")
  --dashboard-name <name>  AI/BI ダッシュボード名 (default: "$DASHBOARD_NAME")
  --warehouse-id <id>      _app_config 読み取り用 warehouse ID (default: $WAREHOUSE_ID)
  --drop-schema            UC schema も DROP CASCADE で削除
  --yes, -y                確認プロンプトをスキップ
  -h, --help               このヘルプ表示
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --profile)                PROFILE="$2"; shift 2;;
    --target|-t)              TARGET="$2"; shift 2;;
    --catalog)                CATALOG="$2"; shift 2;;
    --schema)                 SCHEMA="$2"; shift 2;;
    --ka-name)                KA_NAME="$2"; shift 2;;
    --mas-name)               MAS_NAME="$2"; shift 2;;
    --genie-vehicle-name)     GENIE_VEHICLE_NAME="$2"; shift 2;;
    --genie-mypage-name)      GENIE_MYPAGE_NAME="$2"; shift 2;;
    --genie-dashboard-name)   GENIE_DASHBOARD_NAME="$2"; shift 2;;
    --dashboard-name)         DASHBOARD_NAME="$2"; shift 2;;
    --warehouse-id)           WAREHOUSE_ID="$2"; shift 2;;
    --drop-schema)            DROP_SCHEMA="true"; shift;;
    --yes|-y)                 YES="true"; shift;;
    -h|--help)                usage; exit 0;;
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
echo "  KA name      : $KA_NAME"
echo "  MAS name     : $MAS_NAME"
echo "  Warehouse    : $WAREHOUSE_ID"
echo "  Drop schema  : $DROP_SCHEMA"
echo "======================================================================"

# ヘルパ: Python で JSON payload を組み立てて `databricks api post` に渡す
# (bash heredoc の backtick / quote escape 問題を回避)
sql_execute() {
  local statement="$1"
  local payload
  payload=$(python3 -c "
import json
print(json.dumps({
    'warehouse_id': '$WAREHOUSE_ID',
    'statement': '''$statement''',
    'wait_timeout': '30s'
}))
")
  databricks api post /api/2.0/sql/statements \
    --profile "$PROFILE" \
    --json "$payload"
}

# =====================================================================
# 1. _app_config からリソース ID を取得
# =====================================================================
echo ""
echo "=== 1. _app_config から ID を取得 ==="

CFG_JSON=$(sql_execute "SELECT key, value FROM \`$CATALOG\`.\`$SCHEMA\`._app_config" 2>/dev/null || echo '{}')

CFG_ENV=$(echo "$CFG_JSON" | python3 <<'PYEOF'
import json, sys, shlex
try:
    raw = sys.stdin.read()
    d = json.loads(raw) if raw.strip() else {}
    rows = d.get("result", {}).get("data_array") or []
    for row in rows:
        if isinstance(row, list) and len(row) >= 2 and row[0]:
            k, v = row[0], row[1] or ""
            varname = "CFG_" + str(k).upper().replace("-", "_").replace(".", "_")
            print(f"{varname}={shlex.quote(str(v))}")
    print(f"CFG_ROWS={len(rows)}")
except Exception as e:
    print(f"CFG_ROWS=0")
    print(f"# parse failed: {e}", file=sys.stderr)
PYEOF
)

if [[ -n "$CFG_ENV" ]]; then
  eval "$CFG_ENV"
fi

echo "  取得行数 : ${CFG_ROWS:-0}"
echo "  主要 ID:"
echo "    dashboard_id        : ${CFG_DASHBOARD_ID:-<none>}"
echo "    ka_endpoint         : ${CFG_KA_ENDPOINT:-<none>}"
echo "    mas_endpoint        : ${CFG_MAS_ENDPOINT:-<none>}"
echo "    genie_vehicle_id    : ${CFG_GENIE_VEHICLE_ID:-<none>}"
echo "    genie_mypage_id     : ${CFG_GENIE_MYPAGE_ID:-<none>}"
echo "    genie_dashboard_id  : ${CFG_GENIE_DASHBOARD_ID:-<none>}"

# Tile ID は _app_config になくても、name で /api/2.0/tiles を検索して解決
echo ""
echo "  Agent Bricks tile 検索 (name ベース):"
TILES_JSON=$(databricks api get /api/2.0/tiles --profile "$PROFILE" 2>/dev/null || echo '{}')
TILE_ENV=$(echo "$TILES_JSON" | python3 -c "
import json, sys
d = json.loads(sys.stdin.read() or '{}')
ka = mas = ''
for t in d.get('tiles', []):
    name = t.get('name', '')
    ttype = t.get('tile_type', '')
    if name == '$KA_NAME' and ttype == 'KA':
        ka = t.get('tile_id', '')
    if name == '$MAS_NAME' and ttype == 'MAS':
        mas = t.get('tile_id', '')
print(f'CFG_KA_TILE_ID={ka}')
print(f'CFG_MAS_TILE_ID={mas}')
")
eval "$TILE_ENV"
echo "    ka_tile_id  : ${CFG_KA_TILE_ID:-<none>}"
echo "    mas_tile_id : ${CFG_MAS_TILE_ID:-<none>}"

# Genie Space: _app_config で取得できなかった分を name 検索でフォールバック
echo ""
echo "  Genie Space 検索 (name ベース・未取得 ID のフォールバック):"
GENIE_JSON=$(databricks api get /api/2.0/genie/spaces --profile "$PROFILE" 2>/dev/null || echo '{}')
GENIE_ENV=$(echo "$GENIE_JSON" | GENIE_VEHICLE_NAME="$GENIE_VEHICLE_NAME" GENIE_MYPAGE_NAME="$GENIE_MYPAGE_NAME" GENIE_DASHBOARD_NAME="$GENIE_DASHBOARD_NAME" python3 -c "
import json, sys, os
d = json.loads(sys.stdin.read() or '{}')
spaces = d.get('spaces', [])
wants = {
    'CFG_GENIE_VEHICLE_ID_FB':   os.environ['GENIE_VEHICLE_NAME'],
    'CFG_GENIE_MYPAGE_ID_FB':    os.environ['GENIE_MYPAGE_NAME'],
    'CFG_GENIE_DASHBOARD_ID_FB': os.environ['GENIE_DASHBOARD_NAME'],
}
for k, want_name in wants.items():
    found = ''
    for s in spaces:
        if s.get('title', '') == want_name:
            found = s.get('space_id', '')
            break
    print(f'{k}={found}')
")
eval "$GENIE_ENV"
# _app_config 側の ID がなければ name 検索結果を使う
CFG_GENIE_VEHICLE_ID="${CFG_GENIE_VEHICLE_ID:-${CFG_GENIE_VEHICLE_ID_FB:-}}"
CFG_GENIE_MYPAGE_ID="${CFG_GENIE_MYPAGE_ID:-${CFG_GENIE_MYPAGE_ID_FB:-}}"
CFG_GENIE_DASHBOARD_ID="${CFG_GENIE_DASHBOARD_ID:-${CFG_GENIE_DASHBOARD_ID_FB:-}}"
echo "    genie_vehicle_id    : ${CFG_GENIE_VEHICLE_ID:-<none>}"
echo "    genie_mypage_id     : ${CFG_GENIE_MYPAGE_ID:-<none>}"
echo "    genie_dashboard_id  : ${CFG_GENIE_DASHBOARD_ID:-<none>}"

# Dashboard: _app_config で取得できなかったら name 検索でフォールバック
if [[ -z "${CFG_DASHBOARD_ID:-}" ]]; then
  echo ""
  echo "  AI/BI Dashboard 検索 (name ベース):"
  DASH_JSON=$(databricks api get /api/2.0/lakeview/dashboards --profile "$PROFILE" 2>/dev/null || echo '{}')
  CFG_DASHBOARD_ID=$(echo "$DASH_JSON" | DASHBOARD_NAME="$DASHBOARD_NAME" python3 -c "
import json, sys, os
d = json.loads(sys.stdin.read() or '{}')
want = os.environ['DASHBOARD_NAME']
for x in d.get('dashboards', []):
    if x.get('display_name', '') == want:
        print(x.get('dashboard_id', ''))
        break
")
  echo "    dashboard_id        : ${CFG_DASHBOARD_ID:-<none>}"
fi

# =====================================================================
# 2. 確認
# =====================================================================
if [[ "$YES" != "true" ]]; then
  echo ""
  echo "----------------------------------------------------------------------"
  echo "  これから削除します:"
  echo "    - AI/BI Dashboard / MAS tile / KA tile / Genie Spaces ×3"
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
  if "$@" 2>&1 | tail -10; then
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
# 4. MAS tile 削除 (Agent Bricks)
# =====================================================================
if [[ -n "${CFG_MAS_TILE_ID:-}" ]]; then
  try_delete "MAS tile (id=$CFG_MAS_TILE_ID, name=$MAS_NAME)" \
    databricks api delete "/api/2.0/tiles/$CFG_MAS_TILE_ID" --profile "$PROFILE"
fi

# =====================================================================
# 5. KA tile 削除 (Agent Bricks)
# =====================================================================
if [[ -n "${CFG_KA_TILE_ID:-}" ]]; then
  try_delete "KA tile (id=$CFG_KA_TILE_ID, name=$KA_NAME)" \
    databricks api delete "/api/2.0/tiles/$CFG_KA_TILE_ID" --profile "$PROFILE"
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
  sql_execute "DROP SCHEMA IF EXISTS \`$CATALOG\`.\`$SCHEMA\` CASCADE" 2>/dev/null \
    && echo "  ✓ Schema dropped" \
    || echo "  ⚠️  Drop failed"
fi

echo ""
echo "======================================================================"
echo "  teardown 完了"
echo ""
echo "  次のステップ（真のクリーンスレート検証）:"
echo "    1. ローカルの clone を削除して git から再取得:"
echo "       cd .. && rm -rf car_ai_agent && \\"
echo "       git clone https://github.com/komae5519pv/car_agent.git car_ai_agent && \\"
echo "       cd car_ai_agent"
echo "    2. databricks.yml の catalog/schema/warehouse_id を自分用に書き換え"
echo "    3. databricks bundle deploy --profile $PROFILE"
echo "    4. databricks bundle run setup_demo --profile $PROFILE"
echo "       (本番フル: 15-20 分 / 軽量: --params customer_limit=3 で 5-10 分)"
echo "    5. databricks bundle run car_agent --profile $PROFILE"
echo "======================================================================"
