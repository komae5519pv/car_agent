# Car Agent — 中古車販売 営業支援 AI デモ

Databricks 上で動く「中古車販売の営業担当者を支援する AI エージェント」デモです。
Genie / Agent Bricks（Knowledge Assistant / Multi-Agent Supervisor）/ Databricks Apps / Unity Catalog を統合した**本番想定の構成**を、**SA がコマンド 3〜4 発で自ワークスペースに再現**できるようにパッケージ化しています。

> 💡 **SA の方へ**：このデモを自分の環境で動かすには、下の [セットアップ手順](#-セットアップ手順4-コマンド) の通りに進めてください。所要時間は初回 10〜15 分（`build_gold` で LLM を呼ばず JSON + テンプレ生成にしているため軽量）。

---

## ⚡ よく使うコマンド（cheat sheet）

プロファイル名は `databricks auth login` 時に作成されたもの（例: `my-workspace`）。

```bash
# === 初回デプロイ（全部作る）===
databricks bundle deploy                           --profile <プロファイル>   # Job + App のガワ作成（~30秒）
databricks bundle run setup_demo                   --profile <プロファイル>   # 全リソース作成（10〜15分）
databricks bundle run car_agent                    --profile <プロファイル>   # App 起動（~2分）

# === 差分だけ更新（コード変えたとき）===
databricks bundle deploy                           --profile <プロファイル>   # ファイル同期
databricks bundle run car_agent                    --profile <プロファイル>   # App 再起動のみ
# パイプラインだけ再実行したければ:
databricks bundle run setup_demo --only build_gold --profile <プロファイル>   # 特定タスクだけ

# === 既定 teardown: UC / Dashboard / MAS / KA / Genies を削除（App/Job は残す）===
./scripts/teardown.sh --profile <プロファイル> --drop-schema --yes
# ↑ App を保持するので OAuth session 切れ（画面が白いまま）を起こしません。
#   次の 'bundle deploy' で App/Job は in-place 更新されます。

# === 完全 teardown: App/Job も消す（SA 間配布前の検証用）===
./scripts/teardown.sh --profile <プロファイル> --drop-schema --destroy-app --yes
# ↑ App SP の OAuth integration も消えるので、既存ブラウザ session は無効化される点注意。

# === 消して作り直す（ワンセット、推奨フロー）===
./scripts/teardown.sh --profile <プロファイル> --drop-schema --yes \
  && databricks bundle deploy       --profile <プロファイル> \
  && databricks bundle run setup_demo --profile <プロファイル> \
  && databricks bundle run car_agent  --profile <プロファイル>
```

詳しい説明は下のセクション：[セットアップ手順](#-セットアップ手順4-コマンド) / [全削除](#-全削除--再現性テスト)

---

## 📺 このデモで見られるもの

| UI | 機能 | 裏側 |
|---|---|---|
| **現場営業画面** `/sales` | 顧客テーブル、顧客インサイト、車両レコメンド、トークスクリプト、Ask AI チャット | UC テーブル、Foundation Model API、Multi-Agent Supervisor |
| **マイページ** `/sales/mypage` | 営業成績の可視化、Genie Space 風チャット（結果 / 可視化 / SQL のタブ切替、結果テーブルの列ソート、「メールで送る」デモボタン） | マイページ用 Genie Space |
| **管理者画面** `/admin` | ダッシュボード、AI 推論ログ、データカタログ | UC、MLflow Tracing |
| **AI/BI ダッシュボード** | 車両販売分析ダッシュボード（営業データ Genie と連携） | Lakeview + UC + 営業データ Genie Space |

---

## 🏗 構成（セットアップ完了後にワークスペースに存在するもの）

```
┌──────────────────────────────────────────────────────────────────────┐
│  Unity Catalog  <catalog>.<schema>                                    │
│  ├─ テーブル: bz_* (Bronze) / sv_* (Silver) / gd_* (Gold)             │
│  ├─ Volume: images / raw_data / knowledge                             │
│  └─ _app_config テーブル (App が起動時に参照する ID 一覧)              │
├──────────────────────────────────────────────────────────────────────┤
│  Genie Spaces ×3                                                      │
│  ├─ [car-agent] 車両営業アシスタント    (顧客・在庫・商談)             │
│  ├─ [car-agent] 営業マイページ         (個人成績分析)                  │
│  └─ [car-agent] 営業データ             (店舗売上・転換率)              │
├──────────────────────────────────────────────────────────────────────┤
│  Agent Bricks                                                         │
│  ├─ Knowledge Assistant「car-agent-knowledge」                        │
│  │     └─ Volume 内の車両カタログ・営業トーク・金融知識を RAG         │
│  └─ Multi-Agent Supervisor「car-agent-supervisor」                    │
│        └─ 上の Genie ×3 + KA を束ねて振り分け                          │
├──────────────────────────────────────────────────────────────────────┤
│  AI/BI Dashboard「[car-agent] 車両販売ダッシュボード」                │
│    └─ UC テーブル + 営業データ Genie Space 連携（埋め込み公開済み）    │
├──────────────────────────────────────────────────────────────────────┤
│  Databricks App「car-agent」 (React + FastAPI)                        │
│    └─ URL: https://car-agent-<workspace-id>.aws.databricksapps.com    │
├──────────────────────────────────────────────────────────────────────┤
│  Databricks Job「[car-agent] 初回セットアップ」                        │
│    └─ 上のリソース全部を一発で作る自動化 Job (11 タスク)                │
└──────────────────────────────────────────────────────────────────────┘
```

上記リソースは `databricks.yml` の `variables:` で名前を自由に変更可能です。

---

## 📋 前提条件

| 項目 | 説明 |
|---|---|
| **Databricks CLI 0.230+** | `brew install databricks/tap/databricks` または [公式インストーラ](https://docs.databricks.com/dev-tools/cli/install.html) |
| **自分のワークスペースでの権限** | Catalog の MANAGE、Genie / Agent Bricks / Apps / SQL Warehouse の作成・使用 |
| **SQL Warehouse** | 稼働中のもの（Serverless 推奨） |
| **Foundation Model API** | `databricks-claude-sonnet-4` が有効（既定） |
| **Agent Bricks 機能** | workspace で有効化されていること |

> 権限が揃っていない場合は管理者に依頼。権限不足はエラーメッセージで顕在化します。

---

## 🚀 セットアップ手順（4 コマンド）

### Step 1. リポジトリ取得

```bash
git clone <このリポジトリの URL>
cd car_ai_agent
```

### Step 2. Databricks 認証

```bash
databricks auth login --host https://<自分のワークスペース>.cloud.databricks.com
```

ブラウザが開いてログインすると `~/.databrickscfg` に保存されます。プロファイル名（例: `my-workspace`）を控えておいてください。

### Step 3. 設定カスタマイズ

`databricks.yml` の `variables:` セクションを開いて **以下 3 つ（または 5 つ）のデフォルト値を自分用に書き換え**：

```yaml
variables:
  # ---- 必須: UC / warehouse（自分のワークスペースの値に）----
  catalog:              { default: konomi_demo_catalog }      # ← 自分のカタログに変更
  warehouse_id:         { default: "348478745ad64b30" }       # ← 自分の warehouse ID

  # ---- 推奨: デモ担当者（自分の名前とメール）----
  sales_rep_name:       { default: "大前 このみ" }            # ← 自分の名前（苗字でLINE自己紹介に使われる）
  sales_rep_email:      { default: "konomi.omae@databricks.com" }  # ← 自分のメール

  # ---- 変更不要（気にしないなら触らない）----
  schema:               { default: car_agent }
  app_name:             { default: car-agent }
  job_display_name:     { default: "[car-agent] 初回セットアップ" }
  ka_name:              { default: car-agent-knowledge }
  mas_name:             { default: car-agent-supervisor }
  genie_vehicle_name:   { default: "[car-agent] 車両営業アシスタント" }
  genie_mypage_name:    { default: "[car-agent] 営業マイページ" }
  genie_dashboard_name: { default: "[car-agent] 営業データ" }
  dashboard_name:       { default: "[car-agent] 車両販売ダッシュボード" }
  llm_model:            { default: "databricks-claude-sonnet-4" }
  customer_limit:       { default: "" }                        # "10" 等で gold 処理対象を先頭 N 顧客に制限（デバッグ用）
```

`targets.dev.workspace` の `host` や `root_path` は **書き換え不要**です。`host` は `--profile` で指定した workspace から自動解決、`root_path` は `${workspace.current_user.userName}` でログインユーザーのホーム配下に自動配置されます。

> **SA が触るのはこのファイル 1 つだけ**です。`app.yaml` / `00_config.py` / `src/car_agent/backend/config.py` などは編集不要。
>
> <details><summary>仕組み（興味ある人向け）</summary>
>
> - **Job / Notebook**：`databricks.yml` の `variables:` → `resources/setup_job.yml` の `parameters:` → notebook の `dbutils.widgets.get(...)` で伝搬
> - **Databricks App**：`databricks.yml` の `variables:` → `resources/app.yml` の `config.env:` で `${var.*}` 展開 → App 起動時の env へ（ルートの `app.yaml` は最小フォールバック、DAB デプロイで上書きされます）
>
> </details>

CLI で一時的に上書きも可能：

```bash
databricks bundle deploy --var catalog=my_catalog --var schema=my_demo
```

### Step 4. リソースのデプロイ + 実行

```bash
# 4-1. バンドルデプロイ (Job + App リソースのガワを作る、約 30 秒)
databricks bundle deploy --profile <自分のプロファイル>

# 4-2. セットアップ Job 実行 (全自動、10〜15 分)
databricks bundle run setup_demo --profile <自分のプロファイル>

# 4-3. App デプロイ (コードを配置して起動、約 2-3 分)
databricks bundle run car_agent --profile <自分のプロファイル>
```

**開発中で対象顧客を絞りたい場合**（デモ主役の 10 名だけ処理）：

```bash
databricks bundle run setup_demo --profile <プロファイル> --params customer_limit=10
```

### Step 5. App とダッシュボードを開く

Step 4-2 の `print_summary` タスクの出力（Job ログ or Job UI の最終タスク）に、作成済みリソースの URL 一覧が出ます。

```
── Databricks App ──
  App URL               : https://car-agent-xxxxxx.aws.databricksapps.com

── AI/BI Dashboard ──
  URL                   : https://<workspace>/dashboardsv3/<dashboard_id>/published
```

Step 4-3 完了後、App URL をブラウザで開けばデモを開始できます。ダッシュボードは別タブで開いて管理者向けの可視化として使います。

> ⚠️ **Genie の残作業（API 非対応のため手動）**: パイプラインは 3 つの Genie Space を作成し使用テーブルを紐付けますが、「一般的な指示」と UC 関数 `current_sales_rep_email()` の curated tool 登録は UI から手動で設定する必要があります。手順は [`docs/【参考】Genie作成手順.py`](docs/【参考】Genie作成手順.py) を参照（各 Genie の General Instructions 本文と末尾の「UC 関数を Genie に登録」セクション）。

---

## 🔍 セットアップで何が起きるか（詳細）

### `databricks bundle deploy` の動作

- ワークスペースの指定パスにリポジトリのファイル一式を同期
- 以下の Databricks リソースを作成（まだ走らない、ガワだけ）：
  - **Job**：`[car-agent] 初回セットアップ`
  - **App**：`car-agent`（Service Principal も同時に自動生成）

### `databricks bundle run setup_demo` の動作（11 タスクが順次実行）

| # | タスク | 所要 | 何をするか |
|---|---|---|---|
| 1 | `setup_demo_data` | 30 秒 | UC Catalog / Schema / Volume 作成、生データ CSV を Volume に配置、車両画像をコピー。デモ主役 10 名の商談録音・LINE・CC ログは `setup/demo_interactions_data.json` から読込 |
| 2 | `build_bronze` | 1 分 | 生データ → Bronze テーブル |
| 3 | `build_silver` | 2 分 | Bronze → Silver（クレンジング・正規化） |
| 4 | `build_gold` | 30-60 秒 | Silver → Gold。**LLM 呼び出しなし**：デモ主役 10 名は `setup/gold_prebuilt_data.json` の手作りインサイト/レコメンドを使用、残りは顧客プロフィールからの決定論テンプレで生成（LLM 生成コードは `04_gold.py` 内にコメントアウトで保持、デモで見せられる状態） |
| 5 | `create_genies` | 30 秒 | Genie Space ×3 を `setup/genie_spaces.yaml` に従って作成 |
| 6 | `create_ka` | 5-10 分 | Knowledge Assistant を作成、Volume のドキュメントをインデックス化 |
| 7 | `create_mas` | 1-3 分 | Multi-Agent Supervisor を作成（Genie ×3 + KA を束ねる） |
| 8 | `grant_app_perms` | 30 秒 | App SP に UC / Genie / KA / MAS の必要権限を付与 |
| 9 | `register_config` | 20 秒 | Genie/KA/MAS の ID を `_app_config` テーブルに記録（App が起動時に参照） |
| 10 | `create_dashboard` | 30 秒 | `車両販売ダッシュボード.lvdash.json` を catalog/schema/Genie ID 置換して Lakeview API でデプロイ、埋め込み認証で公開 |
| 11 | `print_summary` | 10 秒 | 作成物の URL/ID 一覧（App / Dashboard / Genie / KA / MAS）を出力 |

タスク間の依存関係は DAG で管理されており、gold 完了後は Genie と KA が並列実行されます。Job 全体の所要は **10〜15 分**（KA の埋め込み生成がボトルネック）。

### `databricks bundle run car_agent` の動作

- 先に同期されたソース（`src/car_agent/`）を Databricks Apps ランタイムに配置
- `uvicorn car_agent.backend.app:app` を起動
- App 起動時：
  1. `_app_config` テーブルから Genie / KA / MAS の ID を動的取得（環境変数のベタ書き不要）
  2. SQL Warehouse 接続
  3. FastAPI サーバ起動 → URL で使用可能に

---

## 📁 リポジトリ構造

```
car_ai_agent/
├── databricks.yml              ★ SA が編集する唯一の設定ファイル
├── README.md                   ★ セットアップ・cheat sheet・teardown
├── DEMO.md                     ★ デモ当日の台本 + 入力プロンプト集
│
├── 00_config.py                ⚠️ 編集不要（widget から値を受け取るだけ）
├── 01_setup_demo_data.py       データパイプライン（01〜04 は Job 経由で自動実行）
├── 02_bronze.py
├── 03_silver.py
├── 04_gold.py                  LLM 呼ばずに JSON / テンプレから Gold 生成（LLM コードはコメントで保持）
│
├── app.yaml                    ⚠️ 最小フォールバック（本体は resources/app.yml の config.env、DAB 時に上書き）
├── 車両販売ダッシュボード.lvdash.json   AI/BI ダッシュボード定義
├── pyproject.toml / requirements.txt
│
├── _images/                    車両画像（Volume にコピーされる）
├── app/frontend/               React ソース
├── src/car_agent/              Python バックエンド (+ ビルド済みフロントエンド)
│
├── docs/                       📚 手動セットアップ参考ノートブック
│   ├── README.md
│   └── 【参考】Genie作成手順.py / AgentBricksナレッジアシスタント.py / AgentBricksマルチエージェントスーパーバイザー.py
│
├── resources/                  ⚙️ DAB リソース定義（SA は触らない）
│   ├── setup_job.yml           Job 定義 + parameters（databricks.yml の variables を widget に橋渡し）
│   └── app.yml                 App 定義 + config.env（databricks.yml の variables を env に橋渡し）
│
├── setup/                      ⚙️ 自動化スクリプト + デモデータ（Job が読む）
│   ├── demo_interactions_data.json  デモ主役 10 名の商談録音・LINE会話・CC ログ（手作り）
│   ├── gold_prebuilt_data.json      デモ主役 10 名の顧客インサイト・車両レコメンド（手作り）
│   ├── genie_spaces.yaml       Genie の中身（instructions/sample_questions 等）
│   ├── knowledge_assistant.yaml KA の中身
│   ├── multi_agent_supervisor.yaml MAS の中身
│   ├── create_genies.py        ↑の定義を読んで API で作成
│   ├── create_ka.py
│   ├── create_mas.py
│   ├── grant_app_perms.py
│   ├── register_config.py
│   ├── create_dashboard.py     AI/BI ダッシュボードを Lakeview API でデプロイ
│   └── print_summary.py
│
└── scripts/                    🧹 運用スクリプト（ローカルから叩く）
    └── teardown.sh             デモの全削除
```

作成済みリソースの ID/URL を確認するには：

```sql
SELECT key, value FROM <catalog>.<schema>._app_config ORDER BY key;
```

---

## 🧹 全削除 & ワンショット再デプロイ

### teardown スクリプト（推奨・ワンコマンド）

付属の `scripts/teardown.sh` が **DAB 管理外リソース（Dashboard / MAS / KA / Genie ×3）＋（オプション）UC スキーマ** を削除します。

**既定では App / Job は残します**。これは App 消去 → 再作成で OAuth integration が再発行され、ブラウザ cookie が stale 化して session 切れ（画面真っ白）を起こすため。次の `bundle deploy` で App/Job は in-place 更新されます。

```bash
# 【既定】Dashboard/MAS/KA/Genies + UC スキーマ 削除（App/Job は残す、確認スキップ）
./scripts/teardown.sh --profile <プロファイル> --drop-schema --yes

# UC スキーマも残して、Agent 系だけ削除
./scripts/teardown.sh --profile <プロファイル> --yes

# 【完全消去】App/Job まで含めて真っサラに（SA 間配布前の検証用）
./scripts/teardown.sh --profile <プロファイル> --drop-schema --destroy-app --yes
```

<details><summary>オプション詳細</summary>

| フラグ | 効果 |
|---|---|
| `--profile <名前>` | 必須。`databricks auth login` で作成したプロファイル名 |
| `--drop-schema` | UC スキーマ（Bronze/Silver/Gold テーブル + Volume + 生データ）も削除。未指定だとスキーマは残る |
| `--yes` / `-y` | 確認プロンプトをスキップ（CI 用） |
| `--catalog <名前>` | カタログ名を上書き（既定: `konomi_demo_catalog`） |
| `--schema <名前>` | スキーマ名を上書き（既定: `car_agent`） |
| `--ka-name` / `--mas-name` | KA / MAS 名を上書き（既定: `car-agent-knowledge` / `car-agent-supervisor`） |

</details>

<details><summary>内部的な削除順序</summary>

1. `_app_config` テーブルから各リソースの ID を取得
2. AI/BI Dashboard 削除（Lakeview API）
3. Multi-Agent Supervisor tile 削除（Agent Bricks）
4. Knowledge Assistant tile 削除（Agent Bricks）
5. Genie Spaces ×3 削除（UC の `_app_config` に登録された ID 経由）
6. `databricks bundle destroy`（Job / App / workspace files）
7. `DROP SCHEMA ... CASCADE`（`--drop-schema` 指定時のみ）

</details>

### ワンショット「消して作り直し」

デモ準備で一番よく使うシーケンス。**コピペ1回で真っさら→再デプロイまで完了**します。

```bash
./scripts/teardown.sh --profile <プロファイル> --drop-schema --yes \
  && databricks bundle deploy       --profile <プロファイル> \
  && databricks bundle run setup_demo --profile <プロファイル> \
  && databricks bundle run car_agent  --profile <プロファイル>
```

所要時間: 合計 15〜20 分程度（teardown 数十秒 + setup 10〜15 分 + app デプロイ 2-3 分）。

> ⚠️ 同一ワークスペースで dev と test を並行デプロイすることは、DAB の Terraform state 共有の都合でできません。destroy → redeploy の一方通行で運用してください。
>
> 途中のタスクで失敗した場合は、`--only <task_key,...>` で失敗タスク以降だけ再実行できます（例: `databricks bundle run setup_demo --only create_mas,grant_app_perms,register_config,create_dashboard,print_summary --profile <プロファイル>`）。

---

## 🎬 デモシナリオ

デモ当日の画面遷移・入力プロンプト集はルートの [`DEMO.md`](DEMO.md) を参照。

---

## 🧰 技術スタック

- **フロントエンド**: React 19, TypeScript, TailwindCSS, Zustand, React Router
- **バックエンド**: FastAPI, Python 3.11+, Databricks SDK, Databricks SQL Connector, OpenAI SDK (FM API 経由、Ask AI で使用), MLflow Tracing
- **インフラ**: Databricks Apps, Unity Catalog, Foundation Model API (Claude Sonnet 4), Genie, Agent Bricks (KA + MAS), AI/BI Dashboard (Lakeview)
- **デプロイ**: Databricks Asset Bundles (DAB)

> ⓘ パイプラインの `build_gold` は速度優先で LLM を呼ばず JSON / テンプレで生成しています。LLM 生成コードは `04_gold.py` 内にコメントアウトで残してあり、デモの中で「本来なら LLM でこう書ける」と見せられます。

---

## 📜 ライセンス

Demo Use Only
