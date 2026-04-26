# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC # 02_bronze — Bronze レイヤー取り込み
# MAGIC <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1B3139 100%); padding: 20px 30px; border-radius: 10px; margin-bottom: 20px;">
# MAGIC   <div style="display: flex; align-items: center; gap: 15px;">
# MAGIC     <img src="https://www.databricks.com/wp-content/uploads/2022/06/db-nav-logo.svg" width="40" style="filter: brightness(2);"/>
# MAGIC     <div>
# MAGIC       <div style="color: #8FB8DE; font-size: 13px; font-weight: 500;">中古車販売 AI デモ</div>
# MAGIC       <div style="color: #FFFFFF; font-size: 22px; font-weight: 700; letter-spacing: 0.5px;">02_bronze — Bronze レイヤー取り込み</div>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 14px 18px; border-radius: 6px; margin-bottom: 18px;">
# MAGIC   <strong>📘 概要</strong><br/>
# MAGIC   Raw Volume（Parquet）のデータを読み込み、<code>_ingested_at</code> 列を付与して Delta テーブル（<code>bz_*</code>）に書き出します。
# MAGIC </div>

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

from pyspark.sql import functions as F

def write_bronze(df, table_name, comment, col_comments):
    """Parquet → Bronze Delta テーブル書き出し + テーブル/カラムコメント設定"""
    (df.withColumn("_ingested_at", F.current_timestamp())
       .write.format("delta").mode("overwrite")
       .option("overwriteSchema", "true")
       .saveAsTable(table_name))
    spark.sql(f"ALTER TABLE {table_name} SET TBLPROPERTIES ('comment' = '{comment}')")
    for col, desc in col_comments.items():
        spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {col} COMMENT '{desc}'")
    cnt = spark.table(table_name).count()
    print(f"✓ {table_name}: {cnt:,} 件（コメント {len(col_comments)} 列）")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 1. bz_sf_opportunities
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 14px 18px; border-radius: 6px; margin-bottom: 10px;">
# MAGIC   <strong>📘 1. bz_sf_opportunities</strong> — SalesForce（SFDC）から取り込んだ商談パイプライン生データ
# MAGIC </div>

# COMMAND ----------

write_bronze(
    spark.read.parquet(f"/Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/sf_opportunities"),
    "bz_sf_opportunities",
    "SalesForce（SFDC）から取り込んだ商談パイプライン生データ",
    {
        "sf_opportunity_id": "SFDC商談ID（一意識別子）",
        "customer_id": "会員ID（顧客一意識別子）",
        "sales_rep_id": "営業担当者ID",
        "sales_rep_name": "営業担当者氏名",
        "sales_rep_email": "営業担当者メールアドレス",
        "contact_name": "顧客氏名",
        "age": "顧客年齢",
        "gender": "性別（男性/女性）",
        "occupation": "職業",
        "family_detail": "家族構成の詳細テキスト",
        "family_size": "家族人数",
        "prefecture": "居住都道府県",
        "city": "居住市区町村",
        "current_vehicle": "現在乗っている車種",
        "current_mileage": "現在の車の走行距離（km）",
        "budget": "購入予算（円）",
        "budget_min": "購入予算下限（円）",
        "budget_max": "購入予算上限（円）",
        "preferences": "車両嗜好・重視ポイント",
        "stage": "商談ステージ（リード/来店予定/来店済み/試乗済み/見積提示/成約/失注）",
        "lead_source": "リードの流入元（Web/来店/紹介/SNS/チラシ/電話）",
        "persona_type": "顧客ペルソナタイプ（6分類）",
        "visit_scheduled_date": "来店予定日",
        "created_date": "商談作成日",
        "last_activity_date": "最終アクティビティ日",
        "close_date": "クローズ予定日",
        "loss_reason": "失注理由",
        "_ingested_at": "Bronzeに取り込んだ日時",
    },
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 2. bz_web_browsing_events
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 14px 18px; border-radius: 6px; margin-bottom: 10px;">
# MAGIC   <strong>📘 2. bz_web_browsing_events</strong> — Web 閲覧履歴の顧客Web行動ログ（生データ）
# MAGIC </div>

# COMMAND ----------

write_bronze(
    spark.read.parquet(f"/Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/web_browsing_events"),
    "bz_web_browsing_events",
    "Web 閲覧履歴の顧客Web行動ログ（生データ）",
    {
        "event_id": "イベント一意ID",
        "sf_opportunity_id": "SFDC商談ID（顧客紐付けキー）",
        "session_id": "セッションID",
        "event_type": "イベント種別（search/view/click/favorite）",
        "vehicle_key": "閲覧・クリックした車両キー",
        "vehicle_name": "閲覧・クリックした車両名（日本語）",
        "search_keyword": "検索キーワード",
        "device_type": "使用デバイス（スマートフォン/PC/タブレット）",
        "event_timestamp": "イベント発生日時",
        "_ingested_at": "Bronzeに取り込んだ日時",
    },
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 3. bz_visit_transcripts
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 14px 18px; border-radius: 6px; margin-bottom: 10px;">
# MAGIC   <strong>📘 3. bz_visit_transcripts</strong> — 来店時の商談音声を文字起こしした生データ
# MAGIC </div>

# COMMAND ----------

write_bronze(
    spark.read.parquet(f"/Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/visit_transcripts"),
    "bz_visit_transcripts",
    "来店時の商談音声を文字起こしした生データ",
    {
        "transcript_id": "文字起こしレコードの一意ID",
        "sf_opportunity_id": "SFDC商談ID",
        "visit_date": "来店日",
        "store_name": "来店店舗名",
        "sales_rep_name": "担当営業スタッフ名",
        "duration_minutes": "商談時間（分）",
        "transcript_text": "音声文字起こし本文（対話形式）",
        "created_at": "レコード作成日時",
        "_ingested_at": "Bronzeに取り込んだ日時",
    },
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 4. bz_line_messages
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 14px 18px; border-radius: 6px; margin-bottom: 10px;">
# MAGIC   <strong>📘 4. bz_line_messages</strong> — LINEチャットの顧客・スタッフ間メッセージ生データ
# MAGIC </div>

# COMMAND ----------

write_bronze(
    spark.read.parquet(f"/Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/line_messages"),
    "bz_line_messages",
    "LINEチャットの顧客・スタッフ間メッセージ生データ",
    {
        "message_id": "メッセージ一意ID",
        "sf_opportunity_id": "SFDC商談ID",
        "conversation_id": "会話スレッドID",
        "sender": "送信者（customer/staff）",
        "message_text": "メッセージ本文",
        "sent_at": "送信日時",
        "_ingested_at": "Bronzeに取り込んだ日時",
    },
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 5. bz_callcenter_logs
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 14px 18px; border-radius: 6px; margin-bottom: 10px;">
# MAGIC   <strong>📘 5. bz_callcenter_logs</strong> — コールセンターへの問い合わせ通話記録生データ
# MAGIC </div>

# COMMAND ----------

write_bronze(
    spark.read.parquet(f"/Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/callcenter_logs"),
    "bz_callcenter_logs",
    "コールセンターへの問い合わせ通話記録生データ",
    {
        "call_id": "通話レコードの一意ID",
        "sf_opportunity_id": "SFDC商談ID",
        "call_date": "通話日",
        "duration_seconds": "通話時間（秒）",
        "call_reason": "問い合わせ理由",
        "transcript_text": "通話文字起こし本文（対話形式）",
        "created_at": "レコード作成日時",
        "_ingested_at": "Bronzeに取り込んだ日時",
    },
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## ✅ Bronze レイヤー取り込み完了
# MAGIC <div style="border-left: 4px solid #388E3C; background: #E8F5E9; padding: 14px 18px; border-radius: 6px; margin-bottom: 10px;">
# MAGIC   <strong>✅ Bronze レイヤー取り込み完了</strong> — 全 5 テーブルの件数を確認します。
# MAGIC </div>

# COMMAND ----------

for t in ["bz_sf_opportunities", "bz_web_browsing_events", "bz_visit_transcripts", "bz_line_messages", "bz_callcenter_logs"]:
    print(f"  {t:<30s} {spark.table(t).count():>8,} 件")
print("✓ Bronze 取り込み完了")
