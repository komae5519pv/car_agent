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
#   2. AI/BI Dashboard         (Lakeview API: /api/2.0/lakeview/dashboards/{id})
#   3. Multi-Agent Supervisor  (Agent Bricks tile: /api/2.0/tiles/{id})
#   4. Knowledge Assistant     (Agent Bricks tile: /api/2.0/tiles/{id})
#   5. Genie Spaces ×3         (Genie API: /api/2.0/genie/spaces/{id})
#   6. [optional] DAB 管理     (--destroy-app 指定時のみ、bundle destroy で
#                              Job / App / workspace files 削除)
#   7. [optional] UC Schema    (--drop-schema 指定時のみ)
#
# 既定では DAB 管理 (Job / App / workspace files) は削除しません。
# 理由: App を消すと OAuth integration が再発行され、ブラウザ cookie が
#      stale 化して次回アクセス時に session 切れになるため (デモ運用で頻発)。
# 完全消去したい場合のみ --destroy-app を付けてください。
#
# 使い方:
#   ./scripts/teardown.sh --profile <profile>                                  # Dashboard/MAS/KA/Genies のみ削除（推奨）
#   ./scripts/teardown.sh --profile <profile> --drop-schema                    # UC Schema も削除
#   ./scripts/teardown.sh --profile <profile> --drop-schema --destroy-app      # App/Job 含めて完全消去
#   ./scripts/teardown.sh --profile <profile> --drop-schema --destroy-app --yes # 確認なしで完全消去
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
DESTROY_APP="false"

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
  --destroy-app            App/Job/workspace files も削除 (bundle destroy 実行)
                           既定では App/Job は残して次回 bundle deploy で更新扱いにする
                           (App SP の OAuth integration 維持のため、ブラウザ session 切れ防止)
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
    --destroy-app)            DESTROY_APP="true"; shift;;
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
echo "  Destroy app  : $DESTROY_APP"
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

# ヘルパ: 空白区切り文字列に ID を追加（既出なら追加しない）
# 使用: list=$(add_unique "$list" "$new_id")
add_unique() {
  local list="$1"
  local item="$2"
  [[ -z "$item" ]] && { echo "$list"; return; }
  for existing in $list; do
    if [[ "$existing" == "$item" ]]; then
      echo "$list"
      return
    fi
  done
  if [[ -z "$list" ]]; then
    echo "$item"
  else
    echo "$list $item"
  fi
}

# ヘルパ: Databricks API をページネーション対応で全件取得
# bash でループさせると quoting が複雑なので、各ページを databricks CLI で取り、
# Python に渡してマージする（Python は stdin から空行区切りで複数の JSON を受け取る）
# 使用: fetch_all_pages <endpoint> <page_size_param_name> <response_array_key>
# 返り値: stdout に 1 つの JSON オブジェクト {"<array_key>": [...全件]}
fetch_all_pages() {
  local endpoint="$1"
  local page_size_param="${2:-page_size}"
  local array_key="$3"
  local page_token=""
  local page_num=0
  local tmpfile
  tmpfile=$(mktemp)

  while true; do
    page_num=$((page_num + 1))
    local query
    if [[ -n "$page_token" ]]; then
      query="${page_size_param}=1000&page_token=${page_token}"
    else
      query="${page_size_param}=1000"
    fi
    local resp
    resp=$(databricks api get "${endpoint}?${query}" --profile "$PROFILE" 2>/dev/null || echo '{}')
    printf '%s\n---PAGE---\n' "$resp" >> "$tmpfile"
    page_token=$(echo "$resp" | python3 -c "import json,sys; d=json.loads(sys.stdin.read() or '{}'); print(d.get('next_page_token',''))")
    [[ -z "$page_token" ]] && break
    [[ $page_num -ge 50 ]] && { echo "  ⚠️  ページ数 50 到達、打ち切り" >&2; break; }
  done

  ARRAY_KEY="$array_key" PAGES_FILE="$tmpfile" python3 <<'PYEOF'
import json, os
key = os.environ['ARRAY_KEY']
with open(os.environ['PAGES_FILE']) as f:
    raw = f.read()
merged = {key: []}
for chunk in raw.split('\n---PAGE---\n'):
    chunk = chunk.strip()
    if not chunk:
        continue
    try:
        d = json.loads(chunk)
        merged[key].extend(d.get(key, []))
    except Exception:
        pass
print(json.dumps(merged))
PYEOF

  rm -f "$tmpfile"
}

# Tile ID: _app_config に入れていないので、必ず /api/2.0/tiles を name で検索
# 同一名の orphan が残っていても全件拾うために、すべてのマッチを拾う
echo ""
echo "  Agent Bricks tile 検索 (name ベース・ページング対応・同名全件):"
TILES_JSON=$(fetch_all_pages /api/2.0/tiles page_size tiles)
TILE_ENV=$(echo "$TILES_JSON" | KA_NAME="$KA_NAME" MAS_NAME="$MAS_NAME" python3 -c "
import json, sys, os
d = json.loads(sys.stdin.read() or '{}')
ka_ids, mas_ids = [], []
for t in d.get('tiles', []):
    name  = t.get('name', '')
    ttype = t.get('tile_type', '')
    tid   = t.get('tile_id', '')
    if not tid:
        continue
    if name == os.environ['KA_NAME']  and ttype == 'KA':
        ka_ids.append(tid)
    if name == os.environ['MAS_NAME'] and ttype == 'MAS':
        mas_ids.append(tid)
print('CFG_KA_TILE_IDS=\"'  + ' '.join(ka_ids)  + '\"')
print('CFG_MAS_TILE_IDS=\"' + ' '.join(mas_ids) + '\"')
")
eval "$TILE_ENV"
echo "    ka_tile_ids  : ${CFG_KA_TILE_IDS:-<none>}"
echo "    mas_tile_ids : ${CFG_MAS_TILE_IDS:-<none>}"

# Genie Space: 同名 Space の orphan が残っていることがあるので、name で全件検索
# _app_config の ID とマージして重複排除
echo ""
echo "  Genie Space 検索 (name ベース・ページング対応・同名全件):"
GENIE_JSON=$(fetch_all_pages /api/2.0/genie/spaces page_size spaces)
GENIE_ENV=$(echo "$GENIE_JSON" | GENIE_VEHICLE_NAME="$GENIE_VEHICLE_NAME" GENIE_MYPAGE_NAME="$GENIE_MYPAGE_NAME" GENIE_DASHBOARD_NAME="$GENIE_DASHBOARD_NAME" python3 -c "
import json, sys, os
d = json.loads(sys.stdin.read() or '{}')
spaces = d.get('spaces', [])
wants = {
    'CFG_GENIE_VEHICLE_IDS_FB':   os.environ['GENIE_VEHICLE_NAME'],
    'CFG_GENIE_MYPAGE_IDS_FB':    os.environ['GENIE_MYPAGE_NAME'],
    'CFG_GENIE_DASHBOARD_IDS_FB': os.environ['GENIE_DASHBOARD_NAME'],
}
for varname, want_name in wants.items():
    ids = []
    for s in spaces:
        if s.get('title', '') == want_name:
            sid = s.get('space_id', '')
            if sid:
                ids.append(sid)
    print(varname + '=\"' + ' '.join(ids) + '\"')
")
eval "$GENIE_ENV"
# _app_config の ID + 名前検索の全件をマージ (重複排除)
CFG_GENIE_VEHICLE_IDS=$(add_unique   "${CFG_GENIE_VEHICLE_IDS_FB:-}"   "${CFG_GENIE_VEHICLE_ID:-}")
CFG_GENIE_MYPAGE_IDS=$(add_unique    "${CFG_GENIE_MYPAGE_IDS_FB:-}"    "${CFG_GENIE_MYPAGE_ID:-}")
CFG_GENIE_DASHBOARD_IDS=$(add_unique "${CFG_GENIE_DASHBOARD_IDS_FB:-}" "${CFG_GENIE_DASHBOARD_ID:-}")
echo "    genie_vehicle_ids    : ${CFG_GENIE_VEHICLE_IDS:-<none>}"
echo "    genie_mypage_ids     : ${CFG_GENIE_MYPAGE_IDS:-<none>}"
echo "    genie_dashboard_ids  : ${CFG_GENIE_DASHBOARD_IDS:-<none>}"

# Dashboard: 同名 Dashboard の orphan (別フォルダ配置など) を確実に拾うため、常に
# name で全件検索し、_app_config の ID とマージして重複排除
# 注: /api/2.0/lakeview/dashboards はページネーション (default 20/page) があるため、
#     next_page_token を追って全ページ走査しないと orphan を取りこぼす
echo ""
echo "  AI/BI Dashboard 検索 (name ベース・ページング対応・同名全件):"
DASH_JSON=$(fetch_all_pages /api/2.0/lakeview/dashboards page_size dashboards)
DASH_IDS_FB=$(echo "$DASH_JSON" | DASHBOARD_NAME="$DASHBOARD_NAME" python3 -c "
import json, sys, os
d = json.loads(sys.stdin.read() or '{}')
want = os.environ['DASHBOARD_NAME']
ids = []
for x in d.get('dashboards', []):
    if x.get('display_name', '') == want:
        did = x.get('dashboard_id', '')
        if did:
            ids.append(did)
print(' '.join(ids))
")
CFG_DASHBOARD_IDS=$(add_unique "$DASH_IDS_FB" "${CFG_DASHBOARD_ID:-}")
echo "    dashboard_ids        : ${CFG_DASHBOARD_IDS:-<none>}"

# =====================================================================
# 2. 確認
# =====================================================================
if [[ "$YES" != "true" ]]; then
  echo ""
  echo "----------------------------------------------------------------------"
  echo "  これから削除します:"
  echo "    - AI/BI Dashboard / MAS tile / KA tile / Genie Spaces ×3"
  if [[ "$DESTROY_APP" == "true" ]]; then
    echo "    - DAB 管理: Job / App / workspace files (bundle destroy -t $TARGET)"
  else
    echo "    - (App / Job は維持。次の bundle deploy で上書き更新される)"
  fi
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
# 3. Dashboard 削除 (同名全件)
# =====================================================================
for did in ${CFG_DASHBOARD_IDS:-}; do
  try_delete "AI/BI Dashboard (id=$did)" \
    databricks api delete "/api/2.0/lakeview/dashboards/$did" --profile "$PROFILE"
done

# =====================================================================
# 4. MAS tile 削除 (Agent Bricks・同名全件)
# =====================================================================
for tid in ${CFG_MAS_TILE_IDS:-}; do
  try_delete "MAS tile (id=$tid, name=$MAS_NAME)" \
    databricks api delete "/api/2.0/tiles/$tid" --profile "$PROFILE"
done

# =====================================================================
# 5. KA tile 削除 (Agent Bricks・同名全件)
# =====================================================================
for tid in ${CFG_KA_TILE_IDS:-}; do
  try_delete "KA tile (id=$tid, name=$KA_NAME)" \
    databricks api delete "/api/2.0/tiles/$tid" --profile "$PROFILE"
done

# =====================================================================
# 6. Genie Spaces 削除 (同名全件)
# =====================================================================
for gkey in CFG_GENIE_VEHICLE_IDS CFG_GENIE_MYPAGE_IDS CFG_GENIE_DASHBOARD_IDS; do
  gids="${!gkey:-}"
  for gid in $gids; do
    try_delete "Genie Space $gkey=$gid" \
      databricks api delete "/api/2.0/genie/spaces/$gid" --profile "$PROFILE"
  done
done

# =====================================================================
# 7. DAB リソース削除 (Job + App + workspace files) — opt-in
# =====================================================================
if [[ "$DESTROY_APP" == "true" ]]; then
  echo ""
  echo "=== DAB 管理リソース削除 (bundle destroy -t $TARGET) ==="
  echo "  cmd: databricks bundle destroy -t $TARGET --profile $PROFILE --auto-approve"
  databricks bundle destroy -t "$TARGET" --profile "$PROFILE" --auto-approve || echo "  ⚠️  bundle destroy failed"
else
  echo ""
  echo "=== DAB 管理リソース (App / Job / workspace files) はスキップ ==="
  echo "  理由: App SP の OAuth integration 維持のため (ブラウザ session 切れ防止)。"
  echo "        次の 'databricks bundle deploy' で App/Job は in-place 更新されます。"
  echo "        完全消去したい場合は --destroy-app を追加して再実行してください。"
fi

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
