# docs/ — デモシナリオ & 手動セットアップ参考ドキュメント

## デモ用

| ファイル | 用途 |
|---|---|
| `DEMO_SCENARIO_COMPETITION.md` | デモ当日の画面遷移・入力プロンプト集 |
| `MANUAL_GENIE_SETUP.md` | パイプライン実行後に Genie UI で手動設定する手順（一般的指示＋UC関数登録） |

## 手動セットアップ参考（UI 操作の手順書）

通常は `databricks bundle run setup_demo` で **Genie / KA / MAS が自動作成**されるので、下記ノートブックは**参考情報**です。自動セットアップが使えない環境で UI から手動作成したい場合や、Agent Bricks の内部を理解したい場合に閲覧してください。

| ファイル | 対応する自動化スクリプト |
|---|---|
| `【参考】Genie作成手順.py` | `setup/create_genies.py` + `setup/genie_spaces.yaml` |
| `【参考】AgentBricksナレッジアシスタント.py` | `setup/create_ka.py` |
| `【参考】AgentBricksマルチエージェントスーパーバイザー.py` | `setup/create_mas.py` |

> これらは説明用ノートブックなので **実行可能なコードは含まれていません**（markdown セルのみ）。Databricks workspace にインポートしてブラウザ上で読んでください。
