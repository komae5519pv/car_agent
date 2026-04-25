# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC # 07_Agent Bricks マルチエージェントスーパーバイザー
# MAGIC <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1B3139 100%); padding: 20px 30px; border-radius: 10px; margin-bottom: 20px;">
# MAGIC   <div style="display: flex; align-items: center; gap: 15px;">
# MAGIC     <img src="https://www.databricks.com/wp-content/uploads/2022/06/db-nav-logo.svg" width="40" style="filter: brightness(2);"/>
# MAGIC     <div>
# MAGIC       <div style="color: #8FB8DE; font-size: 13px; font-weight: 500;">中古車販売 AI デモ</div>
# MAGIC       <div style="color: #FFFFFF; font-size: 22px; font-weight: 700; letter-spacing: 0.5px;">07_Agent Bricks マルチエージェントスーパーバイザー</div>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <a href="https://docs.databricks.com/aws/ja/generative-ai/agent-bricks/multi-agent-supervisor" target="_blank">Agent Bricksの使用: Multi-Agent Supervisor</a><br/><br/>
# MAGIC   Genie（構造化データ）・ナレッジアシスタント（RAG）を統合し、営業担当者のあらゆる質問に対応するスーパーバイザーを構築します。
# MAGIC </div>

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 1. マルチエージェントスーパーバイザーを作る
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   Agent Bricks → マルチエージェントスーパーバイザー → <b>ビルド</b>
# MAGIC </div>
# MAGIC
# MAGIC <table style="width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1);">
# MAGIC   <thead>
# MAGIC     <tr style="background: #1565C0; color: white;">
# MAGIC       <th style="padding: 10px 16px; text-align: left;">設定項目</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">値</th>
# MAGIC     </tr>
# MAGIC   </thead>
# MAGIC   <tbody>
# MAGIC     <tr style="background: #FFFFFF;"><td style="padding: 8px 16px;"><b>名前</b></td><td style="padding: 8px 16px;"><code>car-ai-assistant</code></td></tr>
# MAGIC     <tr style="background: #F5F5F5;"><td style="padding: 8px 16px;"><b>説明</b></td><td style="padding: 8px 16px;">自動車営業チーム向けの総合AIアシスタント。顧客データ・在庫・推薦実績（Genie）、車両スペック・営業トーク・金融知識（RAG）を統合し、商談準備から提案・クロージングまで一貫してサポートします。</td></tr>
# MAGIC   </tbody>
# MAGIC </table>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### エージェントを設定
# MAGIC <div style="border-left: 4px solid #7B1FA2; background-color: #F3E5F5; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   以下の 2 つの子エージェントを追加します。
# MAGIC </div>
# MAGIC
# MAGIC <table style="width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1);">
# MAGIC   <thead>
# MAGIC     <tr style="background: #7B1FA2; color: white;">
# MAGIC       <th style="padding: 10px 16px; text-align: left;">タイプ</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">エージェント</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">エージェント名</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">説明</th>
# MAGIC     </tr>
# MAGIC   </thead>
# MAGIC   <tbody>
# MAGIC     <tr style="background: #FFFFFF;">
# MAGIC       <td style="padding: 8px 16px;">Genieスペース</td>
# MAGIC       <td style="padding: 8px 16px;">車両営業アシスタント<br/>（05_Genie作成手順で作成した Genie スペース）</td>
# MAGIC       <td style="padding: 8px 16px;"><code>agent</code></td>
# MAGIC       <td style="padding: 8px 16px;">sv_customers・sv_vehicle_inventory・sv_interactions・gd_customer_insights・gd_recommendationsテーブルを参照し、顧客プロフィール・在庫状況・商談履歴・推薦実績などの構造化データを検索・分析するエージェント</td>
# MAGIC     </tr>
# MAGIC     <tr style="background: #F5F5F5;">
# MAGIC       <td style="padding: 8px 16px;">ナレッジアシスタント</td>
# MAGIC       <td style="padding: 8px 16px;"><code>car-knowledge-bot</code><br/>（06_ナレッジアシスタントで作成した KA）</td>
# MAGIC       <td style="padding: 8px 16px;"><code>agent</code></td>
# MAGIC       <td style="padding: 8px 16px;">車両カタログ・スペック、営業トーク集・商談ガイド、維持費・ローン・保険の基礎知識を参照し、商談準備・顧客提案・金融アドバイスを支援するナレッジアシスタント</td>
# MAGIC     </tr>
# MAGIC   </tbody>
# MAGIC </table>

# COMMAND ----------

# 子エージェントの設定値確認
print("=== 子エージェント設定値 ===")
print(f"  Genie Space ID : {GENIE_VEHICLE_ASSISTANT_ID or '（未設定 → 05_Genie作成手順 で作成後に 00_config へ記入）'}")
print(f"  KA Endpoint    : {KA_ENDPOINT_NAME or '（未設定 → 06_ナレッジアシスタント で作成後に 00_config へ記入）'}")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### 手順設定（オプション）
# MAGIC <div style="border-left: 4px solid #F57C00; background-color: #FFF3E0; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   以下をそのまま「手順設定（オプション）」にコピーしてください。
# MAGIC </div>
# MAGIC
# MAGIC ```
# MAGIC * あなたは自動車営業チームを支援するAIアシスタントです
# MAGIC * 必ず日本語で回答してください
# MAGIC * 顧客の呼び方は必ず「苗字＋様」（例：渡辺様、山田様）。下の名前では呼ばない
# MAGIC
# MAGIC * エージェントの使い分け（ルーティング基準）:
# MAGIC   - 「Genie（車両営業アシスタント）」: 顧客の予算・家族構成・ニーズ、在庫車両の絞り込み、商談履歴・発言の確認、推薦実績の確認など、テーブルから取得する事実データが必要な場合
# MAGIC   - 「ナレッジアシスタント（car-knowledge-bot）」: 車両スペック比較・燃費・装備の詳細、営業トーク・クロージング手法、維持費・ローン・保険の説明方法など、カタログ・マニュアルに基づくナレッジが必要な場合
# MAGIC   - 複数のエージェントが必要な場合は必ずすべて使用する
# MAGIC
# MAGIC * 最初に結論を簡潔に述べ、その後に詳細を説明してください
# MAGIC
# MAGIC * 最終回答は以下の順で整理してください（該当する項目のみ）:
# MAGIC   1. 顧客・在庫データ（事実）
# MAGIC   2. 車両知識・スペック・ナレッジ
# MAGIC   3. 営業担当者へのアクション提案
# MAGIC   4. 顧客向けトーク例（必要な場合）
# MAGIC
# MAGIC * 商談準備の質問を受けた場合は:
# MAGIC   - Genieで顧客の予算・家族構成・インサイトを確認し
# MAGIC   - RAGで該当車両のスペック・トークポイントを参照して
# MAGIC   - 「この顧客にはこう話すと刺さる」という具体的なトーク例まで出してください
# MAGIC
# MAGIC * 車両比較の質問を受けた場合は:
# MAGIC   - RAGでスペック・装備・価格帯を比較表形式で整理してください
# MAGIC
# MAGIC * 在庫確認の質問を受けた場合は:
# MAGIC   - Genieで条件（予算・ボディタイプ・燃料など）に合う在庫を絞り込み
# MAGIC   - RAGで各車のセールスポイントを補足してください
# MAGIC ```

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 2. マルチエージェントスーパーバイザーを使ってみる
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   Playground でルーティングが正しく動作するか確認します。
# MAGIC </div>
# MAGIC
# MAGIC <table style="width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1);">
# MAGIC   <thead>
# MAGIC     <tr style="background: #7B1FA2; color: white;">
# MAGIC       <th style="padding: 10px 16px; text-align: left;">質問番号</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">質問内容</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">主な参照エージェント</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">狙い</th>
# MAGIC     </tr>
# MAGIC   </thead>
# MAGIC   <tbody>
# MAGIC     <tr style="background: #FFFFFF;">
# MAGIC       <td style="padding: 8px 16px;">Q1</td>
# MAGIC       <td style="padding: 8px 16px;">山田さんの希望条件と予算を教えて。その条件で在庫に合う車は何がある？</td>
# MAGIC       <td style="padding: 8px 16px;">Genie</td>
# MAGIC       <td style="padding: 8px 16px;">顧客データ取得→在庫マッチング。Genie単体の動作確認</td>
# MAGIC     </tr>
# MAGIC     <tr style="background: #F5F5F5;">
# MAGIC       <td style="padding: 8px 16px;">Q2</td>
# MAGIC       <td style="padding: 8px 16px;">ヴェゼルとフリードを比較して。安全装備と維持費の違いを整理して</td>
# MAGIC       <td style="padding: 8px 16px;">RAG（catalogs + finance）</td>
# MAGIC       <td style="padding: 8px 16px;">RAGの車両スペック比較と金融知識の組み合わせ確認</td>
# MAGIC     </tr>
# MAGIC     <tr style="background: #FFFFFF;">
# MAGIC       <td style="padding: 8px 16px;">Q3</td>
# MAGIC       <td style="padding: 8px 16px;">山田さんに今日試乗を提案したい。どう話しかければいい？</td>
# MAGIC       <td style="padding: 8px 16px;">Genie + RAG</td>
# MAGIC       <td style="padding: 8px 16px;">顧客データ（Genie）とトーク知識（RAG）の統合。<b>最大の見せ場</b></td>
# MAGIC     </tr>
# MAGIC   </tbody>
# MAGIC </table>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 3. エンドポイントを確認する
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   デプロイ後、エンドポイント名を <code>00_config</code> の <code>MAS_ENDPOINT_NAME</code> に設定してください。<br/><br/>
# MAGIC   Agent Bricks → マルチエージェントスーパーバイザー → <code>car-ai-assistant</code> → <b>「デプロイ」タブ</b>
# MAGIC </div>

# COMMAND ----------

print(f"MAS_ENDPOINT_NAME = '{MAS_ENDPOINT_NAME}'")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 4. サービスプリンシパルの権限設定
# MAGIC <div style="border-left: 4px solid #F57C00; background-color: #FFF3E0; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <b>これを忘れるとチャットがレスポンスを返しません（ハマりポイント）</b><br/><br/>
# MAGIC   Agent Bricks のエンドポイントが Genie スペースやテーブルにアクセスできるよう、サービスプリンシパルに権限を付与します。
# MAGIC </div>
# MAGIC
# MAGIC <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px; margin: 15px 0;">
# MAGIC   <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
# MAGIC     <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
# MAGIC       <div style="background: #F57C00; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;">1</div>
# MAGIC       <b>サービスプリンシパルの確認</b>
# MAGIC     </div>
# MAGIC     <p style="margin: 0; color: #666;">エンドポイント詳細画面 → 「Service principal」欄で名前を確認</p>
# MAGIC   </div>
# MAGIC   <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
# MAGIC     <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
# MAGIC       <div style="background: #F57C00; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;">2</div>
# MAGIC       <b>Genie スペースへのアクセス権</b>
# MAGIC     </div>
# MAGIC     <p style="margin: 0; color: #666;">各 Genie スペースの設定 → 権限 → サービスプリンシパルを「<b>CAN RUN</b>」で追加</p>
# MAGIC   </div>
# MAGIC   <div style="background: #fff; border: 1px solid #e0e0e0; border-radius: 10px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
# MAGIC     <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
# MAGIC       <div style="background: #F57C00; color: white; width: 30px; height: 30px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold;">3</div>
# MAGIC       <b>テーブルへのアクセス権</b>
# MAGIC     </div>
# MAGIC     <p style="margin: 0; color: #666;">以下の SQL を実行（サービスプリンシパル名を置き換え）</p>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# サービスプリンシパルへの権限付与 SQL
print("=== サービスプリンシパルへの権限付与 SQL ===")
print("-- <サービスプリンシパル名> を実際の名前に置き換えて実行してください\n")
print(f"GRANT USE CATALOG ON CATALOG {catalog_name} TO `66fd7c16-fe48-408e-8272-9d2b19513393`;")
print(f"GRANT USE SCHEMA ON SCHEMA {catalog_name}.{schema_name} TO `66fd7c16-fe48-408e-8272-9d2b19513393`;")
print(f"GRANT SELECT ON SCHEMA {catalog_name}.{schema_name} TO `66fd7c16-fe48-408e-8272-9d2b19513393`;")
print(f"GRANT READ VOLUME ON VOLUME {catalog_name}.{schema_name}.{VOLUME_NAME} TO `66fd7c16-fe48-408e-8272-9d2b19513393`;")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 5. Playground テストチェックリスト
# MAGIC <div style="border-left: 4px solid #388E3C; background-color: #E8F5E9; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   権限設定後、Playground で最終動作確認します。
# MAGIC </div>
# MAGIC
# MAGIC <table style="width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1);">
# MAGIC   <thead>
# MAGIC     <tr style="background: #388E3C; color: white;">
# MAGIC       <th style="padding: 10px 16px; text-align: left;">チェック項目</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">確認内容</th>
# MAGIC     </tr>
# MAGIC   </thead>
# MAGIC   <tbody>
# MAGIC     <tr style="background: #FFFFFF;"><td style="padding: 8px 16px;">Genie ルーティング</td><td style="padding: 8px 16px;">Genie が顧客データ・在庫を正しく取得できる</td></tr>
# MAGIC     <tr style="background: #F5F5F5;"><td style="padding: 8px 16px;">RAG ルーティング</td><td style="padding: 8px 16px;">RAG が車両スペック・トーク例を返せる</td></tr>
# MAGIC     <tr style="background: #FFFFFF;"><td style="padding: 8px 16px;">複合質問</td><td style="padding: 8px 16px;">複数エージェントを使い分けて統合回答できる</td></tr>
# MAGIC     <tr style="background: #F5F5F5;"><td style="padding: 8px 16px;">顧客名表記</td><td style="padding: 8px 16px;">顧客の呼び方が苗字+様になっている</td></tr>
# MAGIC     <tr style="background: #FFFFFF;"><td style="padding: 8px 16px;">日本語出力</td><td style="padding: 8px 16px;">回答が日本語で出力されている</td></tr>
# MAGIC   </tbody>
# MAGIC </table>

# COMMAND ----------

# 設定値の最終確認
print("=== 最終設定確認 ===")
print(f"  Catalog                      : {catalog_name}")
print(f"  Schema                       : {schema_name}")
print(f"  GENIE_VEHICLE_ASSISTANT_ID   : {GENIE_VEHICLE_ASSISTANT_ID or '（未設定）'}")
print(f"  KA_ENDPOINT_NAME             : {KA_ENDPOINT_NAME or '（未設定）'}")
print(f"  MAS_ENDPOINT_NAME            : {MAS_ENDPOINT_NAME or '（未設定）'}")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #388E3C; background-color: #E8F5E9; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <p style="color: #388E3C; margin: 0;"><b>完了:</b> マルチエージェントスーパーバイザーのセットアップが完了しました。Playground でテストを実施し、問題がなければデモの準備完了です。</p>
# MAGIC </div>
