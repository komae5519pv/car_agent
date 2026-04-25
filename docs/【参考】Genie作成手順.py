# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC # 05_Genie スペース作成手順
# MAGIC <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1B3139 100%); padding: 20px 30px; border-radius: 10px; margin-bottom: 20px;">
# MAGIC   <div style="display: flex; align-items: center; gap: 15px;">
# MAGIC     <img src="https://www.databricks.com/wp-content/uploads/2022/06/db-nav-logo.svg" width="40" style="filter: brightness(2);"/>
# MAGIC     <div>
# MAGIC       <h1 style="color: #FFFFFF; margin: 0; font-size: 28px;">中古車販売 AI デモ</h1>
# MAGIC       <p style="color: #B0BEC5; margin: 5px 0 0 0; font-size: 16px;">05_Genie スペース作成手順</p>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 📋 概要
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h3 style="color: #1976d2; margin-top: 0;">📋 概要</h3>
# MAGIC   <p>このノートブックでは、3 つの Genie スペースを手動で作成する手順を説明します。</p>
# MAGIC   <p>Genie スペースは現在 UI から作成する必要があります。作成後、各スペースの ID を <code>00_config</code> に設定してください。</p>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 作成する Genie スペース一覧
# MAGIC <div style="border-left: 4px solid #388E3C; background-color: #E8F5E9; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h3 style="color: #388E3C; margin-top: 0;">作成する Genie スペース一覧</h3>
# MAGIC   <table style="width: 100%; border-collapse: collapse; border-radius: 8px; overflow: hidden;">
# MAGIC     <thead>
# MAGIC       <tr style="background-color: #388E3C; color: white;">
# MAGIC         <th style="padding: 10px 15px; text-align: left;">#</th>
# MAGIC         <th style="padding: 10px 15px; text-align: left;">Genie スペース名</th>
# MAGIC         <th style="padding: 10px 15px; text-align: left;">用途</th>
# MAGIC         <th style="padding: 10px 15px; text-align: left;">Config 変数</th>
# MAGIC       </tr>
# MAGIC     </thead>
# MAGIC     <tbody>
# MAGIC       <tr style="background-color: #f9f9f9;"><td style="padding: 8px 15px;">1</td><td style="padding: 8px 15px;">車両営業アシスタント</td><td style="padding: 8px 15px;">Agent Bricks MAS の Ask AI</td><td style="padding: 8px 15px;"><code>GENIE_VEHICLE_ASSISTANT_ID</code></td></tr>
# MAGIC       <tr><td style="padding: 8px 15px;">2</td><td style="padding: 8px 15px;">営業マイページ アシスタント</td><td style="padding: 8px 15px;">営業担当の成績確認</td><td style="padding: 8px 15px;"><code>GENIE_MYPAGE_ID</code></td></tr>
# MAGIC       <tr style="background-color: #f9f9f9;"><td style="padding: 8px 15px;">3</td><td style="padding: 8px 15px;">営業データ Genie</td><td style="padding: 8px 15px;">ダッシュボード連携</td><td style="padding: 8px 15px;"><code>GENIE_DASHBOARD_ID</code></td></tr>
# MAGIC     </tbody>
# MAGIC   </table>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <hr style="border: 2px solid #1976d2; margin: 30px 0;">
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h2 style="color: #1976d2; margin-top: 0;">Genie 1: 車両営業アシスタント</h2>
# MAGIC   <p>Agent Bricks マルチエージェントスーパーバイザーの「Ask AI」ツールとして使用します。</p>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #7B1FA2; background-color: #F3E5F5; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h4 style="color: #7B1FA2; margin-top: 0;">設定内容</h4>
# MAGIC   <table style="width: 100%; border-collapse: collapse; border-radius: 8px; overflow: hidden;">
# MAGIC     <thead>
# MAGIC       <tr style="background-color: #7B1FA2; color: white;">
# MAGIC         <th style="padding: 10px 15px; text-align: left;">設定項目</th>
# MAGIC         <th style="padding: 10px 15px; text-align: left;">値</th>
# MAGIC       </tr>
# MAGIC     </thead>
# MAGIC     <tbody>
# MAGIC       <tr style="background-color: #f9f9f9;"><td style="padding: 8px 15px;"><b>タイトル</b></td><td style="padding: 8px 15px;">車両営業アシスタント</td></tr>
# MAGIC       <tr><td style="padding: 8px 15px;"><b>テーブル</b></td><td style="padding: 8px 15px;">
# MAGIC         <code>{catalog_name}.{schema_name}.sv_customers</code><br/>
# MAGIC         <code>{catalog_name}.{schema_name}.sv_vehicle_inventory</code><br/>
# MAGIC         <code>{catalog_name}.{schema_name}.sv_interactions</code><br/>
# MAGIC         <code>{catalog_name}.{schema_name}.gd_customer_insights</code><br/>
# MAGIC         <code>{catalog_name}.{schema_name}.gd_recommendations</code>
# MAGIC       </td></tr>
# MAGIC       <tr style="background-color: #f9f9f9;"><td style="padding: 8px 15px;"><b>Config 変数</b></td><td style="padding: 8px 15px;"><code>GENIE_VEHICLE_ASSISTANT_ID</code></td></tr>
# MAGIC     </tbody>
# MAGIC   </table>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #F57C00; background-color: #FFF3E0; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h4 style="color: #F57C00; margin-top: 0;">⚠️ General Instructions（以下をそのままコピー）</h4>
# MAGIC </div>
# MAGIC
# MAGIC ```
# MAGIC あなたは中古車販売の営業アシスタントです。
# MAGIC 営業担当者からの質問に対し、顧客データ・在庫データ・商談履歴を参照して回答します。
# MAGIC
# MAGIC 主な対応範囲:
# MAGIC - 顧客の購入履歴・嗜好・予算に基づく車両提案
# MAGIC - 在庫車両の検索・絞り込み（車種、価格帯、年式、走行距離など）
# MAGIC - 商談進捗の確認と次のアクション提案
# MAGIC - 顧客インサイト（購買傾向、おすすめ車両）の参照
# MAGIC
# MAGIC 回答のルール:
# MAGIC - 顧客名は「苗字＋様」で表記してください
# MAGIC - 金額は日本円（万円単位）で表示してください
# MAGIC - 在庫状況は最新データを参照してください
# MAGIC - 不明な場合は「該当データが見つかりません」と回答してください
# MAGIC ```

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h4 style="color: #1976d2; margin-top: 0;">💬 サンプル質問</h4>
# MAGIC   <ul>
# MAGIC     <li>田中様に合うSUVの在庫を教えてください</li>
# MAGIC     <li>予算200万円以内のミニバンは何台ありますか？</li>
# MAGIC     <li>先月の商談で未フォローの顧客一覧を出してください</li>
# MAGIC     <li>購入検討中の顧客で、おすすめ車両が一致する方は？</li>
# MAGIC   </ul>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <hr style="border: 2px solid #1976d2; margin: 30px 0;">
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h2 style="color: #1976d2; margin-top: 0;">Genie 2: 営業マイページ アシスタント</h2>
# MAGIC   <p>中古車販売企業｜営業担当者の個人実績データを自然言語で分析できます。成約率・売上・車種別・月別トレンドなどの質問に答えます。</p>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #7B1FA2; background-color: #F3E5F5; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h4 style="color: #7B1FA2; margin-top: 0;">設定内容</h4>
# MAGIC   <table style="width: 100%; border-collapse: collapse; border-radius: 8px; overflow: hidden;">
# MAGIC     <thead>
# MAGIC       <tr style="background-color: #7B1FA2; color: white;">
# MAGIC         <th style="padding: 10px 15px; text-align: left;">設定項目</th>
# MAGIC         <th style="padding: 10px 15px; text-align: left;">値</th>
# MAGIC       </tr>
# MAGIC     </thead>
# MAGIC     <tbody>
# MAGIC       <tr style="background-color: #f9f9f9;"><td style="padding: 8px 15px;"><b>タイトル</b></td><td style="padding: 8px 15px;">営業マイページ アシスタント</td></tr>
# MAGIC       <tr><td style="padding: 8px 15px;"><b>テーブル</b></td><td style="padding: 8px 15px;"><code>{catalog_name}.{schema_name}.sv_sales_results</code></td></tr>
# MAGIC       <tr style="background-color: #f9f9f9;"><td style="padding: 8px 15px;"><b>Config 変数</b></td><td style="padding: 8px 15px;"><code>GENIE_MYPAGE_ID</code></td></tr>
# MAGIC     </tbody>
# MAGIC   </table>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #F57C00; background-color: #FFF3E0; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h4 style="color: #F57C00; margin-top: 0;">⚠️ General Instructions（以下をそのままコピー）</h4>
# MAGIC </div>
# MAGIC
# MAGIC ```
# MAGIC あなたは中古車販売の営業成績アナリストです。
# MAGIC 営業担当者の売上実績・目標達成率・商談状況を分析し、回答します。
# MAGIC
# MAGIC 主な対応範囲:
# MAGIC - 個人の売上実績と目標達成率の確認
# MAGIC - 期間別（月次・四半期・年次）の成績推移
# MAGIC - 同僚との比較・ランキング
# MAGIC - 成約率・商談単価の分析
# MAGIC
# MAGIC 回答のルール:
# MAGIC - 営業担当名は「苗字＋様」で表記してください
# MAGIC - 金額は日本円（万円単位）で表示してください
# MAGIC - 達成率はパーセントで表示してください
# MAGIC - ポジティブな表現を心がけてください
# MAGIC ```

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h4 style="color: #1976d2; margin-top: 0;">💬 サンプル質問</h4>
# MAGIC   <ul>
# MAGIC     <li>SUVとミニバンで成約単価が高いのはどっち？車種別に比較して</li>
# MAGIC     <li>今月の営業トップ3と、それぞれの得意車種を教えて</li>
# MAGIC     <li>「他社購入」で失注した案件の車種と価格帯の傾向は？</li>
# MAGIC     <li>関東 vs 関西、店舗あたりの成約率が高いのはどちら？</li>
# MAGIC   </ul>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <hr style="border: 2px solid #1976d2; margin: 30px 0;">
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h2 style="color: #1976d2; margin-top: 0;">Genie 3: 営業データ Genie</h2>
# MAGIC   <p>ダッシュボードの Genie 連携用スペースです。Metric View を活用します。</p>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #7B1FA2; background-color: #F3E5F5; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h4 style="color: #7B1FA2; margin-top: 0;">設定内容</h4>
# MAGIC   <table style="width: 100%; border-collapse: collapse; border-radius: 8px; overflow: hidden;">
# MAGIC     <thead>
# MAGIC       <tr style="background-color: #7B1FA2; color: white;">
# MAGIC         <th style="padding: 10px 15px; text-align: left;">設定項目</th>
# MAGIC         <th style="padding: 10px 15px; text-align: left;">値</th>
# MAGIC       </tr>
# MAGIC     </thead>
# MAGIC     <tbody>
# MAGIC       <tr style="background-color: #f9f9f9;"><td style="padding: 8px 15px;"><b>タイトル</b></td><td style="padding: 8px 15px;">営業データ Genie</td></tr>
# MAGIC       <tr><td style="padding: 8px 15px;"><b>テーブル</b></td><td style="padding: 8px 15px;">
# MAGIC         <code>{catalog_name}.{schema_name}.gd_store_daily_activity</code><br/>
# MAGIC         <code>{catalog_name}.{schema_name}.mv_store_sales</code>（Metric View）
# MAGIC       </td></tr>
# MAGIC       <tr style="background-color: #f9f9f9;"><td style="padding: 8px 15px;"><b>Config 変数</b></td><td style="padding: 8px 15px;"><code>GENIE_DASHBOARD_ID</code></td></tr>
# MAGIC     </tbody>
# MAGIC   </table>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #F57C00; background-color: #FFF3E0; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h4 style="color: #F57C00; margin-top: 0;">⚠️ General Instructions（以下をそのままコピー）</h4>
# MAGIC </div>
# MAGIC
# MAGIC ```
# MAGIC あなたは中古車販売の営業データアナリストです。
# MAGIC 店舗別の売上・ファネル転換率データを分析し、経営層や店舗マネージャーの質問に回答します。
# MAGIC
# MAGIC 主な対応範囲:
# MAGIC - 店舗別・地域別の売上実績と比較
# MAGIC - ファネル転換率（問合せ→試乗→見積→成約）の分析
# MAGIC - 月次・四半期トレンドの把握
# MAGIC - 車種カテゴリ別の販売傾向
# MAGIC
# MAGIC 回答のルール:
# MAGIC - 金額は日本円（万円単位）で表示してください
# MAGIC - 転換率はパーセントで表示してください
# MAGIC - グラフや表での表示を積極的に活用してください
# MAGIC - データに基づいた改善提案も添えてください
# MAGIC ```

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h4 style="color: #1976d2; margin-top: 0;">💬 サンプル質問</h4>
# MAGIC   <ul>
# MAGIC     <li>今月の店舗別売上ランキングを見せてください</li>
# MAGIC     <li>問合せから成約までの転換率が最も高い地域は？</li>
# MAGIC     <li>SUVカテゴリの月次販売トレンドを教えてください</li>
# MAGIC     <li>試乗から見積への転換率が低い店舗はどこですか？</li>
# MAGIC   </ul>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <hr style="border: 2px solid #388E3C; margin: 30px 0;">
# MAGIC <div style="border-left: 4px solid #388E3C; background-color: #E8F5E9; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h2 style="color: #388E3C; margin-top: 0;">Genie スペース ID の設定</h2>
# MAGIC   <p>各 Genie スペースを作成したら、URL から Space ID をコピーし、<code>00_config</code> に設定してください。</p>
# MAGIC   <p>URL 例: <code>https://&lt;workspace&gt;.databricks.com/genie/rooms/<b>&lt;SPACE_ID&gt;</b></code></p>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## データ確認
# MAGIC <div style="border-left: 4px solid #1976d2; background-color: #e3f2fd; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <h3 style="color: #1976d2; margin-top: 0;">データ確認</h3>
# MAGIC   <p>Genie スペースに追加するテーブルのデータを確認します。</p>
# MAGIC </div>

# COMMAND ----------

# Genie 1 用テーブル確認
print("=== Genie 1: 車両営業アシスタント ===")
for t in ["sv_customers", "sv_vehicle_inventory", "sv_interactions", "gd_customer_insights", "gd_recommendations"]:
    print(f"  {t}: {spark.table(t).count():,} 件")

# COMMAND ----------

# Genie 2 用テーブル確認
print("=== Genie 2: 営業マイページ アシスタント ===")
print(f"  sv_sales_results: {spark.table('sv_sales_results').count():,} 件")

# COMMAND ----------

# Genie 3 用テーブル確認
print("=== Genie 3: 営業データ Genie ===")
print(f"  gd_store_daily_activity: {spark.table('gd_store_daily_activity').count():,} 件")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #388E3C; background-color: #E8F5E9; padding: 15px 20px; border-radius: 0 8px 8px 0; margin: 10px 0;">
# MAGIC   <p style="color: #388E3C; margin: 0;">✅ <b>次のステップ:</b> <code>06_AgentBricksナレッジアシスタント</code> に進み、ナレッジアシスタント（RAG）を設定してください。</p>
# MAGIC </div>
