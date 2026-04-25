# docs/ — 手動セットアップ用の参考ノートブック

通常は `databricks bundle run setup_demo` で **Genie / KA / MAS が自動作成**されます。
このディレクトリのノートブックは**参考用**で、以下のような場合にお使いください。

- 自動セットアップが使えない環境（権限不足など）で**手動で UI から作成**したい
- デモ当日に**受講者に見せながら**作成ステップを解説したい
- Agent Bricks の**内部を理解するため**に UI の挙動を追いたい

## ファイル

| ファイル | 対応する自動化スクリプト |
|---|---|
| `【参考】Genie作成手順.py` | `setup/create_genies.py` + `setup/genie_spaces.yaml` |
| `【参考】AgentBricksナレッジアシスタント.py` | `setup/create_ka.py`（Phase 3 で追加予定） |
| `【参考】AgentBricksマルチエージェントスーパーバイザー.py` | `setup/create_mas.py`（Phase 4 で追加予定） |

## 注意

これらのノートブックは手動操作の手順書です。**実行しても何も作成されません**。
実体は UI で操作してもらう前提の説明書になっています。
