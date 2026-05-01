# docs/ — 手動セットアップ参考ノートブック

通常は `databricks bundle run setup_demo` で **Genie / KA / MAS が自動作成**されます。下記は**参考情報**として残してあります。

| ファイル | 内容 | 使いどき |
|---|---|---|
| `【参考】Genie作成手順.py` | 3 Genie の UI 手動作成手順 + **一般的指示のコピペ文** + **UC 関数 `current_sales_rep_email()` の Curated functions 登録** | **パイプライン後に手動で必要**（API 非対応のため）。デモ前に一度開いて設定 |
| `【参考】AgentBricksナレッジアシスタント.py` | KA の手動作成手順 + 3 sources 設定 + 手順設定 | 自動化失敗時のフォールバック用 |
| `【参考】AgentBricksマルチエージェントスーパーバイザー.py` | MAS の手動作成手順 + 子エージェント設定 + 手順設定 | 自動化失敗時のフォールバック用 |

> これらは**説明用ノートブック**で実行可能なコードは含まれていません（markdown セルのみ）。Databricks Workspace にインポートしてブラウザで開いてください。
>
> デモ当日の台本・プロンプト集は**ルートの [`DEMO.md`](../DEMO.md)** を参照。
