# docs/ — デモシナリオ & 手動セットアップ参考ドキュメント

## デモ用

| ファイル | 用途 |
|---|---|
| `DEMO_SCENARIO_COMPETITION.md` | デモ当日の画面遷移・入力プロンプト集 |

## 手動セットアップ参考（UI 操作の手順書）

通常は `databricks bundle run setup_demo` で **Genie / KA / MAS が自動作成**されるので、下記ノートブックは**参考情報**です。

| ファイル | 内容 | 用途 |
|---|---|---|
| `【参考】Genie作成手順.py` | 3 Genie の作成 + 一般的指示コピペ文 + UC 関数 `current_sales_rep_email()` の Curated functions 登録 | **⚠️ パイプライン後に Genie 3 つへ手動で「一般的指示」と「UC関数」を UI 入力するための必須参照ファイル**（API で自動化不可のため） |
| `【参考】AgentBricksナレッジアシスタント.py` | KA の手動作成手順 | 自動化済み。参考のみ |
| `【参考】AgentBricksマルチエージェントスーパーバイザー.py` | MAS の手動作成手順 | 自動化済み。参考のみ |

> これらは説明用ノートブックなので **実行可能なコードは含まれていません**（markdown セルのみ）。Databricks workspace にインポートしてブラウザ上で読んでください。
