# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC # 06_Agent Bricks ナレッジアシスタント（RAG）
# MAGIC <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1B3139 100%); padding: 20px 30px; border-radius: 10px; margin-bottom: 20px;">
# MAGIC   <div style="display: flex; align-items: center; gap: 15px;">
# MAGIC     <img src="https://www.databricks.com/wp-content/uploads/2022/06/db-nav-logo.svg" width="40" style="filter: brightness(2);"/>
# MAGIC     <div>
# MAGIC       <div style="color: #8FB8DE; font-size: 13px; font-weight: 500;">中古車販売 AI デモ</div>
# MAGIC       <div style="color: #FFFFFF; font-size: 22px; font-weight: 700; letter-spacing: 0.5px;">06_Agent Bricks ナレッジアシスタント（RAG）</div>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <a href="https://docs.databricks.com/aws/ja/generative-ai/agent-bricks/knowledge-assistant" target="_blank">Agent Bricksの使用: Knowledge Assistant</a><br/><br/>
# MAGIC   Genie（構造化データ）と組み合わせる RAG エージェントを構築します。
# MAGIC </div>
# MAGIC
# MAGIC <table style="width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1);">
# MAGIC   <thead>
# MAGIC     <tr style="background: #1565C0; color: white;">
# MAGIC       <th style="padding: 10px 16px; text-align: left;">ナレッジソース</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">フォルダ</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">内容</th>
# MAGIC     </tr>
# MAGIC   </thead>
# MAGIC   <tbody>
# MAGIC     <tr style="background: #FFFFFF;"><td style="padding: 8px 16px;">車両カタログ</td><td style="padding: 8px 16px;"><code>catalogs/</code></td><td style="padding: 8px 16px;">取扱い車両のスペック・装備・燃費・強み（テキスト形式）</td></tr>
# MAGIC     <tr style="background: #F5F5F5;"><td style="padding: 8px 16px;">営業トーク集</td><td style="padding: 8px 16px;"><code>sales/</code></td><td style="padding: 8px 16px;">顧客タイプ別アプローチ・試乗誘導・クロージング手法</td></tr>
# MAGIC     <tr style="background: #FFFFFF;"><td style="padding: 8px 16px;">金融知識</td><td style="padding: 8px 16px;"><code>finance/</code></td><td style="padding: 8px 16px;">維持費・ローン・残クレ・リース比較</td></tr>
# MAGIC   </tbody>
# MAGIC </table>
# MAGIC
# MAGIC <div style="border-left: 4px solid #388E3C; background: #E8F5E9; padding: 12px 16px; border-radius: 6px; margin-top: 15px;">
# MAGIC   ドキュメントは <b>01_setup_demo_data（Step 7）</b> で <code>/Volumes/{catalog_name}/{schema_name}/knowledge/</code> に生成済みです。
# MAGIC </div>

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 1. ナレッジアシスタントを作る
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   Agent Bricks → ナレッジアシスタント → <b>ビルド</b>
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
# MAGIC     <tr style="background: #FFFFFF;"><td style="padding: 8px 16px;"><b>名前</b></td><td style="padding: 8px 16px;"><code>car-knowledge-bot</code></td></tr>
# MAGIC     <tr style="background: #F5F5F5;"><td style="padding: 8px 16px;"><b>説明</b></td><td style="padding: 8px 16px;">車両カタログ・スペック、営業トーク集・商談ガイド、維持費・ローン・保険の基礎知識を参照し、営業担当者の商談準備・顧客提案・金融アドバイスを支援するナレッジアシスタント</td></tr>
# MAGIC   </tbody>
# MAGIC </table>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### ナレッジソースを設定
# MAGIC <div style="border-left: 4px solid #7B1FA2; background-color: #F3E5F5; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   以下の 3 フォルダをそれぞれナレッジソースとして登録します。
# MAGIC </div>
# MAGIC
# MAGIC <table style="width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1);">
# MAGIC   <thead>
# MAGIC     <tr style="background: #7B1FA2; color: white;">
# MAGIC       <th style="padding: 10px 16px; text-align: left;">No</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">タイプ</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">ソース</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">名前</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">コンテンツを説明</th>
# MAGIC     </tr>
# MAGIC   </thead>
# MAGIC   <tbody>
# MAGIC     <tr style="background: #FFFFFF;">
# MAGIC       <td style="padding: 8px 16px;">1</td>
# MAGIC       <td style="padding: 8px 16px;">UCファイル</td>
# MAGIC       <td style="padding: 8px 16px;"><code>/Volumes/{catalog_name}/{schema_name}/knowledge/catalogs/</code></td>
# MAGIC       <td style="padding: 8px 16px;"><code>catalogs</code></td>
# MAGIC       <td style="padding: 8px 16px;">取扱い車両のスペック・グレード・標準装備・燃費・特徴をまとめた車両カタログ資料。各メーカー・モデルの強み・弱み・競合比較に活用。</td>
# MAGIC     </tr>
# MAGIC     <tr style="background: #F5F5F5;">
# MAGIC       <td style="padding: 8px 16px;">2</td>
# MAGIC       <td style="padding: 8px 16px;">UCファイル</td>
# MAGIC       <td style="padding: 8px 16px;"><code>/Volumes/{catalog_name}/{schema_name}/knowledge/sales/</code></td>
# MAGIC       <td style="padding: 8px 16px;"><code>sales</code></td>
# MAGIC       <td style="padding: 8px 16px;">営業トーク集・商談ガイド。顧客タイプ別アプローチ、試乗誘導・クロージングトーク、NGワード集など、商談品質向上のための実践資料。</td>
# MAGIC     </tr>
# MAGIC     <tr style="background: #FFFFFF;">
# MAGIC       <td style="padding: 8px 16px;">3</td>
# MAGIC       <td style="padding: 8px 16px;">UCファイル</td>
# MAGIC       <td style="padding: 8px 16px;"><code>/Volumes/{catalog_name}/{schema_name}/knowledge/finance/</code></td>
# MAGIC       <td style="padding: 8px 16px;"><code>finance</code></td>
# MAGIC       <td style="padding: 8px 16px;">自動車維持費・ローン・残クレ・リース・保険の基礎知識。顧客への金融オプション説明、ハイブリッドvsガソリンのコスト比較など。</td>
# MAGIC     </tr>
# MAGIC   </tbody>
# MAGIC </table>

# COMMAND ----------

# ナレッジフォルダの確認
knowledge_base_path = f"/Volumes/{catalog_name}/{schema_name}/{KNOWLEDGE_VOLUME_NAME}"
for folder in ["catalogs", "sales", "finance"]:
    path = f"{knowledge_base_path}/{folder}"
    try:
        files = dbutils.fs.ls(path)
        print(f"  {folder}/: {len(files)} ファイル")
        for f in files:
            print(f"    - {f.name} ({f.size:,} bytes)")
    except Exception as e:
        print(f"  {folder}/: フォルダが見つかりません - {path}")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ### 手順設定（オプション）
# MAGIC <div style="border-left: 4px solid #F57C00; background-color: #FFF3E0; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   以下をそのまま「手順設定（オプション）」にコピーしてください。
# MAGIC </div>
# MAGIC
# MAGIC ```
# MAGIC * あなたは自動車営業ナレッジアシスタントです
# MAGIC * 車両カタログ・営業トーク集・維持費/ローン知識のみを根拠に回答してください
# MAGIC * 顧客の在庫状況・個別データはGenieエージェントが担当します。このアシスタントは知識・ナレッジに特化してください
# MAGIC * 資料に明記されていない場合は「資料上は確認できません」と回答してください
# MAGIC * 必ず日本語で回答してください
# MAGIC * 最初に結論を簡潔に述べ、以下の構造で整理してください：
# MAGIC   【ポイント】
# MAGIC   【詳細・根拠】
# MAGIC   【注意点・例外】
# MAGIC   【接客トーク例（必要な場合のみ）】
# MAGIC * 車両比較の際は表形式で整理してください
# MAGIC * 金額は万円単位で表記してください
# MAGIC ```

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 2. ナレッジアシスタントを使ってみる
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   Playground でサンプル質問を投げて回答品質を確認します。
# MAGIC </div>
# MAGIC
# MAGIC <table style="width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1);">
# MAGIC   <thead>
# MAGIC     <tr style="background: #7B1FA2; color: white;">
# MAGIC       <th style="padding: 10px 16px; text-align: left;">質問番号</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">質問内容</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">主な参照元</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">狙い</th>
# MAGIC     </tr>
# MAGIC   </thead>
# MAGIC   <tbody>
# MAGIC     <tr style="background: #FFFFFF;">
# MAGIC       <td style="padding: 8px 16px;">Q1</td>
# MAGIC       <td style="padding: 8px 16px;">シエンタとフリードを比較して。乗り降りのしやすさと安全装備の違いを教えて</td>
# MAGIC       <td style="padding: 8px 16px;">catalogs</td>
# MAGIC       <td style="padding: 8px 16px;">2車種の同カテゴリ比較。スペックを表形式で整理できるか確認</td>
# MAGIC     </tr>
# MAGIC     <tr style="background: #F5F5F5;">
# MAGIC       <td style="padding: 8px 16px;">Q2</td>
# MAGIC       <td style="padding: 8px 16px;">高齢の義母と一緒に乗る機会が多い顧客に、シエンタをおすすめするトーク例を作って</td>
# MAGIC       <td style="padding: 8px 16px;">sales + catalogs</td>
# MAGIC       <td style="padding: 8px 16px;">ナレッジを組み合わせて具体的なトーク例を生成できるか確認</td>
# MAGIC     </tr>
# MAGIC     <tr style="background: #FFFFFF;">
# MAGIC       <td style="padding: 8px 16px;">Q3</td>
# MAGIC       <td style="padding: 8px 16px;">300万円の車を残クレで買う場合と一括で買う場合、5年間のトータルコストの差は？</td>
# MAGIC       <td style="padding: 8px 16px;">finance</td>
# MAGIC       <td style="padding: 8px 16px;">金融知識の検索・計算説明ができるか確認</td>
# MAGIC     </tr>
# MAGIC   </tbody>
# MAGIC </table>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 3. ナレッジアシスタントを改善する（ラベル付きセッション）
# MAGIC <div style="border-left: 4px solid #388E3C; background-color: #E8F5E9; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   回答にラベル（Good / Bad）を付けて改善サイクルを回します。以下の質問とガイドラインを参考にしてください。
# MAGIC </div>
# MAGIC
# MAGIC <table style="width: 100%; border-collapse: separate; border-spacing: 0; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 4px rgba(0,0,0,0.1);">
# MAGIC   <thead>
# MAGIC     <tr style="background: #388E3C; color: white;">
# MAGIC       <th style="padding: 10px 16px; text-align: left;">質問</th>
# MAGIC       <th style="padding: 10px 16px; text-align: left;">ガイドライン</th>
# MAGIC     </tr>
# MAGIC   </thead>
# MAGIC   <tbody>
# MAGIC     <tr style="background: #FFFFFF;">
# MAGIC       <td style="padding: 8px 16px;">SUVを検討している初めての購入者に、ヴェゼルとハリアーどちらが向いているか教えて</td>
# MAGIC       <td style="padding: 8px 16px;">【ポイント】予算・用途・優先度で異なると明示。【詳細】ヴェゼル：コスパ・デザイン向き、ハリアー：上質感・格重視向き。どちらが絶対良いとは言わず、顧客の状況に依存することを示すこと</td>
# MAGIC     </tr>
# MAGIC     <tr style="background: #F5F5F5;">
# MAGIC       <td style="padding: 8px 16px;">ハイブリッドはガソリン車より本当に得なのか？顧客に聞かれたら何と答える？</td>
# MAGIC       <td style="padding: 8px 16px;">【ポイント】走行距離・保有期間によって異なる。【詳細】5〜7年・年1万km以上走るなら元が取れる目安を数字で示す。「得か損か」の二択ではなく、条件次第であることを明示すること</td>
# MAGIC     </tr>
# MAGIC     <tr style="background: #FFFFFF;">
# MAGIC       <td style="padding: 8px 16px;">レクサス RXとアルファード、どちらがステータス性が高い？それぞれの強みを教えて</td>
# MAGIC       <td style="padding: 8px 16px;">【ポイント】用途・顧客層が異なるため単純比較は不適切と明示。【詳細】RX：プレミアムSUV・安全性・静粛性、アルファード：最高級ミニバン・広さ・VIP送迎。顧客の重視軸を確認するトークを含めること</td>
# MAGIC     </tr>
# MAGIC   </tbody>
# MAGIC </table>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 4. エンドポイントIDを控える
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   マルチエージェントスーパーバイザー（07）の設定で使用します。<br/><br/>
# MAGIC   Agent Bricks → ナレッジアシスタント → <code>car-knowledge-bot</code> → <b>「デプロイ」タブ</b> → エンドポイント名を確認し、<code>00_config</code> の <code>KA_ENDPOINT_NAME</code> に設定してください。
# MAGIC </div>

# COMMAND ----------

print(f"KA_ENDPOINT_NAME = '{KA_ENDPOINT_NAME}'")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #388E3C; background-color: #E8F5E9; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <p style="color: #388E3C; margin: 0;"><b>次のステップ:</b> <code>07_AgentBricksマルチエージェントスーパーバイザー</code> に進み、マルチエージェントを構成してください。</p>
# MAGIC </div>
