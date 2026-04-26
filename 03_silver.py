# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC # 03_silver — Silver レイヤー加工
# MAGIC <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1B3139 100%); padding: 20px 30px; border-radius: 10px; margin-bottom: 20px;">
# MAGIC   <div style="display: flex; align-items: center; gap: 15px;">
# MAGIC     <img src="https://www.databricks.com/wp-content/uploads/2022/06/db-nav-logo.svg" width="40" style="filter: brightness(2);"/>
# MAGIC     <div>
# MAGIC       <div style="color: #8FB8DE; font-size: 13px; font-weight: 500;">中古車販売 AI デモ</div>
# MAGIC       <div style="color: #FFFFFF; font-size: 22px; font-weight: 700; letter-spacing: 0.5px;">03_silver — Silver レイヤー加工</div>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>
# MAGIC
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 14px 18px; border-radius: 6px; margin-bottom: 18px;">
# MAGIC   <strong>📘 概要</strong><br/>
# MAGIC   Bronze テーブルを加工し Silver テーブル（<code>sv_*</code>）を作成。車両在庫・店舗・売上実績はインライン生成します。
# MAGIC </div>

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

from pyspark.sql import functions as F
from pyspark.sql.types import *

def write_silver(df, table_name, comment, col_comments, pk=None, fks=None):
    """Silver テーブル書き出し + コメント・PK/FK 設定を一括実行"""
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(table_name)
    spark.sql(f"ALTER TABLE {table_name} SET TBLPROPERTIES ('comment' = '{comment}')")
    if pk:
        pk_cols = [pk] if isinstance(pk, str) else pk
        for col in pk_cols:
            spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {col} SET NOT NULL")
        spark.sql(f"ALTER TABLE {table_name} ADD CONSTRAINT pk_{table_name} PRIMARY KEY ({', '.join(pk_cols)})")
    for name, ref_table, ref_col in (fks or []):
        spark.sql(f"ALTER TABLE {table_name} ADD CONSTRAINT {name} FOREIGN KEY ({ref_col}) REFERENCES {ref_table}({ref_col})")
    for col, desc in col_comments.items():
        spark.sql(f"ALTER TABLE {table_name} ALTER COLUMN {col} COMMENT '{desc}'")
    cnt = spark.table(table_name).count()
    print(f"✓ {table_name}: {cnt:,} 件")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 1. sv_customers
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 14px 18px; border-radius: 6px; margin-bottom: 10px;">
# MAGIC   <strong>📘 1. sv_customers</strong> — SFDC 商談データを顧客マスタとして整形（型変換・NULL 処理）
# MAGIC </div>

# COMMAND ----------

df_customers = spark.table("bz_sf_opportunities").select(
    F.col("sf_opportunity_id"),
    F.col("customer_id"),
    F.col("sales_rep_id"),
    F.col("sales_rep_name"),
    F.col("sales_rep_email"),
    F.col("contact_name"),
    F.col("age").cast("int"),
    F.col("gender"),
    F.col("occupation"),
    F.col("family_detail"),
    F.col("family_size").cast("int"),
    F.col("prefecture"),
    F.col("city"),
    F.col("current_vehicle"),
    F.col("current_mileage").cast("int"),
    F.col("budget").cast("long"),
    F.col("budget_min").cast("long"),
    F.col("budget_max").cast("long"),
    F.col("preferences"),
    F.col("stage"),
    F.col("lead_source"),
    F.col("persona_type"),
    F.col("visit_scheduled_date").cast("date"),
    F.col("created_date").cast("date"),
    F.col("last_activity_date").cast("date"),
    F.col("close_date").cast("date"),
    F.col("loss_reason"),
)

write_silver(df_customers, "sv_customers", "顧客マスタ（SFDC商談データから整形）",
    pk="sf_opportunity_id",
    col_comments={
        "sf_opportunity_id": "SFDC商談ID（主キー）",
        "customer_id": "会員ID（顧客一意識別子）",
        "sales_rep_id": "営業担当者ID",
        "sales_rep_name": "営業担当者氏名",
        "sales_rep_email": "営業担当者メールアドレス",
        "contact_name": "顧客氏名",
        "age": "顧客年齢",
        "gender": "性別",
        "occupation": "職業",
        "family_detail": "家族構成の詳細",
        "family_size": "家族人数",
        "prefecture": "都道府県",
        "city": "市区町村",
        "current_vehicle": "現在の車種",
        "current_mileage": "現在の走行距離(km)",
        "budget": "購入予算(円)",
        "budget_min": "予算下限(円)",
        "budget_max": "予算上限(円)",
        "preferences": "車両嗜好・重視ポイント",
        "stage": "商談ステージ",
        "lead_source": "リード流入元",
        "persona_type": "顧客ペルソナタイプ",
        "visit_scheduled_date": "来店予定日",
        "created_date": "商談作成日",
        "last_activity_date": "最終アクティビティ日",
        "close_date": "クローズ予定日",
        "loss_reason": "失注理由（失注時のみ）",
    },
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 2. sv_vehicle_inventory
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 14px 18px; border-radius: 6px; margin-bottom: 10px;">
# MAGIC   <strong>📘 2. sv_vehicle_inventory</strong> — 在庫車両マスタ（9 車種をインライン定義）
# MAGIC </div>

# COMMAND ----------

vehicle_data = [
    ("VH-001", "harrier",   "トヨタ ハリアー",    "SUV",      2022, 35000, 3500000, "ガソリン",     "images/harrier.jpg",   "人気の都市型SUV。スタイリッシュなデザインと快適な乗り心地が特徴。ファミリーにもビジネスにも対応。"),
    ("VH-002", "sienta",    "トヨタ シエンタ",    "ミニバン",  2023, 12000, 2200000, "ハイブリッド", "images/sienta.jpg",    "コンパクトなボディに3列シート。スライドドアで乗り降りしやすく、子育て世代に最適。燃費も優秀。"),
    ("VH-003", "freed",     "ホンダ フリード",    "ミニバン",  2022, 20000, 2400000, "ハイブリッド", "images/freed.jpg",     "取り回しの良いサイズ感で日常使いに最適。3列シートで家族5〜6人でもゆったり。"),
    ("VH-004", "voxy",      "トヨタ ヴォクシー",  "ミニバン",  2023, 8000,  3200000, "ハイブリッド", "images/voxy.jpg",      "広々とした室内空間と先進的なデザイン。ファミリー層に圧倒的人気。安全装備も充実。"),
    ("VH-005", "alphard",   "トヨタ アルファード", "ミニバン",  2022, 25000, 5500000, "ハイブリッド", "images/alphard.jpg",   "最高級ミニバン。圧倒的な室内空間と高級感。VIPの送迎にも使われるプレミアムモデル。"),
    ("VH-006", "vezel",     "ホンダ ヴェゼル",    "SUV",      2023, 15000, 2800000, "ハイブリッド", "images/vezel.jpg",     "コンパクトSUVの大定番。スタイリッシュで燃費が良く、初めてのSUVにも最適。"),
    ("VH-007", "prius",     "トヨタ プリウス",    "セダン",    2023, 5000,  3200000, "ハイブリッド", "images/prius.jpg",     "ハイブリッドの代名詞。最新モデルはスポーティなデザインに進化。燃費性能はクラストップレベル。"),
    ("VH-008", "nbox",      "ホンダ N-BOX",      "軽自動車",  2023, 10000, 1800000, "ガソリン",     "images/nbox.jpg",      "軽自動車販売台数No.1。広い室内と使い勝手の良さが魅力。スライドドアで日常使いに便利。"),
    ("VH-009", "lexus_rx",  "レクサス RX",       "SUV",      2022, 18000, 6500000, "ハイブリッド", "images/lexus_rx.jpg",  "レクサスのプレミアムSUV。上質な内装と先進安全装備。ステータスと実用性を両立。"),
]

schema_v = StructType([
    StructField("vehicle_id", StringType()), StructField("vehicle_key", StringType()),
    StructField("vehicle_name", StringType()), StructField("body_type", StringType()),
    StructField("model_year", IntegerType()), StructField("mileage_km", IntegerType()),
    StructField("price", LongType()), StructField("fuel_type", StringType()),
    StructField("image_path", StringType()), StructField("description", StringType()),
])

write_silver(spark.createDataFrame(vehicle_data, schema=schema_v),
    "sv_vehicle_inventory", "在庫車両マスタ（9車種）",
    pk="vehicle_id",
    col_comments={
        "vehicle_id": "車両ID（主キー）", "vehicle_key": "車両キー（画像ファイル名と対応）",
        "vehicle_name": "車両名（メーカー＋車種名）", "body_type": "ボディタイプ",
        "model_year": "年式", "mileage_km": "走行距離(km)",
        "price": "販売価格(円)", "fuel_type": "燃料タイプ",
        "image_path": "車両画像のパス", "description": "車両紹介テキスト",
    },
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 3. sv_interactions
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 14px 18px; border-radius: 6px; margin-bottom: 10px;">
# MAGIC   <strong>📘 3. sv_interactions</strong> — 来店・LINE・コールセンターを統合したインタラクションログ
# MAGIC </div>

# COMMAND ----------

# customer_id マッピング用（sf_opportunity_id → customer_id）
df_opp_to_cust = spark.table("bz_sf_opportunities").select(
    F.col("sf_opportunity_id"),
    F.col("customer_id"),
)

df_visit = (
    spark.table("bz_visit_transcripts")
    .join(df_opp_to_cust, "sf_opportunity_id", "left")
    .select(
        F.col("transcript_id").alias("interaction_id"), F.col("sf_opportunity_id"),
        F.col("customer_id"),
        F.lit("来店").alias("interaction_type"), F.col("visit_date").cast("date").alias("interaction_date"),
        F.col("store_name"), F.col("sales_rep_name"),
        F.col("transcript_text").alias("content"), F.col("duration_minutes").cast("int"),
    )
)
df_line = (
    spark.table("bz_line_messages")
    .join(df_opp_to_cust, "sf_opportunity_id", "left")
    .select(
        F.col("message_id").alias("interaction_id"), F.col("sf_opportunity_id"),
        F.col("customer_id"),
        F.lit("LINE").alias("interaction_type"), F.col("sent_at").cast("date").alias("interaction_date"),
        F.lit(None).cast("string").alias("store_name"), F.lit(None).cast("string").alias("sales_rep_name"),
        F.concat(F.col("sender"), F.lit(": "), F.col("message_text")).alias("content"),
        F.lit(None).cast("int").alias("duration_minutes"),
    )
)
df_call = (
    spark.table("bz_callcenter_logs")
    .join(df_opp_to_cust, "sf_opportunity_id", "left")
    .select(
        F.col("call_id").alias("interaction_id"), F.col("sf_opportunity_id"),
        F.col("customer_id"),
        F.lit("コールセンター").alias("interaction_type"), F.col("call_date").cast("date").alias("interaction_date"),
        F.lit(None).cast("string").alias("store_name"), F.lit(None).cast("string").alias("sales_rep_name"),
        F.col("transcript_text").alias("content"),
        F.round(F.col("duration_seconds") / 60, 1).cast("int").alias("duration_minutes"),
    )
)

write_silver(df_visit.unionByName(df_line).unionByName(df_call),
    "sv_interactions", "来店・LINE・コールセンター統合インタラクションログ",
    pk="interaction_id",
    fks=[("fk_sv_interactions_customer", "sv_customers", "sf_opportunity_id")],
    col_comments={
        "interaction_id": "インタラクションID（主キー）",
        "sf_opportunity_id": "SFDC商談ID（FK→sv_customers）",
        "customer_id": "顧客ID（sf_opportunity_idと同値。sv_customersとの結合キー）",
        "interaction_type": "チャネル種別（来店/LINE/コールセンター）",
        "interaction_date": "インタラクション発生日",
        "store_name": "店舗名（来店時のみ）",
        "sales_rep_name": "担当営業（来店時のみ）",
        "content": "インタラクション内容テキスト",
        "duration_minutes": "所要時間（分）",
    },
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 4. sv_web_browsing_behavior
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 14px 18px; border-radius: 6px; margin-bottom: 10px;">
# MAGIC   <strong>📘 4. sv_web_browsing_behavior</strong> — Web 閲覧行動データを顧客単位で集約
# MAGIC </div>

# COMMAND ----------

df_behavior = (
    spark.table("bz_web_browsing_events")
    .groupBy("sf_opportunity_id")
    .agg(
        F.count("*").alias("total_events"),
        F.countDistinct("session_id").alias("session_count"),
        F.sum(F.when(F.col("event_type") == "search", 1).otherwise(0)).alias("search_count"),
        F.sum(F.when(F.col("event_type") == "view", 1).otherwise(0)).alias("view_count"),
        F.sum(F.when(F.col("event_type") == "click", 1).otherwise(0)).alias("click_count"),
        F.sum(F.when(F.col("event_type") == "favorite", 1).otherwise(0)).alias("favorite_count"),
        F.countDistinct(F.when(F.col("vehicle_key") != "", F.col("vehicle_key"))).alias("unique_vehicles_viewed"),
        F.collect_set(F.when(F.col("vehicle_key") != "", F.col("vehicle_name"))).alias("_vlist"),
        F.collect_set(F.when(F.col("search_keyword") != "", F.col("search_keyword"))).alias("_klist"),
        F.first(F.col("device_type")).alias("primary_device"),
        F.min("event_timestamp").alias("first_event_at"),
        F.max("event_timestamp").alias("last_event_at"),
    )
    .withColumn("viewed_vehicles", F.concat_ws(", ", F.col("_vlist")))
    .withColumn("search_keywords", F.concat_ws(", ", F.col("_klist")))
    .drop("_vlist", "_klist")
)

write_silver(df_behavior, "sv_web_browsing_behavior", "Web 閲覧行動サマリ（顧客単位集約）",
    fks=[("fk_sv_web_browsing_customer", "sv_customers", "sf_opportunity_id")],
    col_comments={
        "sf_opportunity_id": "SFDC商談ID（FK→sv_customers）",
        "total_events": "イベント総数", "session_count": "セッション数",
        "search_count": "検索回数", "view_count": "閲覧回数",
        "click_count": "クリック回数", "favorite_count": "お気に入り回数",
        "unique_vehicles_viewed": "閲覧ユニーク車種数",
        "viewed_vehicles": "閲覧した車種一覧", "search_keywords": "検索キーワード一覧",
        "primary_device": "主に使用したデバイス",
        "first_event_at": "初回イベント日時", "last_event_at": "最終イベント日時",
    },
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 5. sv_stores
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 14px 18px; border-radius: 6px; margin-bottom: 10px;">
# MAGIC   <strong>📘 5. sv_stores</strong> — 店舗マスタ（18 店舗）
# MAGIC </div>

# COMMAND ----------

store_data = [
    ("STR-001", "新宿店",     "関東", "東京都",   "新宿区",        35.6938, 139.7034),
    ("STR-002", "渋谷店",     "関東", "東京都",   "渋谷区",        35.6580, 139.7016),
    ("STR-003", "池袋店",     "関東", "東京都",   "豊島区",        35.7295, 139.7109),
    ("STR-004", "横浜店",     "関東", "神奈川県", "横浜市西区",    35.4657, 139.6225),
    ("STR-005", "千葉店",     "関東", "千葉県",   "千葉市中央区",  35.6074, 140.1065),
    ("STR-006", "埼玉店",     "関東", "埼玉県",   "さいたま市",    35.8617, 139.6455),
    ("STR-007", "梅田店",     "関西", "大阪府",   "大阪市北区",    34.7024, 135.4959),
    ("STR-008", "難波店",     "関西", "大阪府",   "大阪市中央区",  34.6627, 135.5013),
    ("STR-009", "京都店",     "関西", "京都府",   "京都市下京区",  34.9858, 135.7588),
    ("STR-010", "神戸店",     "関西", "兵庫県",   "神戸市中央区",  34.6901, 135.1956),
    ("STR-011", "名古屋栄店", "東海", "愛知県",   "名古屋市中区",  35.1709, 136.9084),
    ("STR-012", "名古屋北店", "東海", "愛知県",   "名古屋市北区",  35.1975, 136.9130),
    ("STR-013", "静岡店",     "東海", "静岡県",   "静岡市葵区",    34.9756, 138.3827),
    ("STR-014", "仙台店",     "東北", "宮城県",   "仙台市青葉区",  38.2601, 140.8821),
    ("STR-015", "盛岡店",     "東北", "岩手県",   "盛岡市",        39.7036, 141.1527),
    ("STR-016", "福岡天神店", "九州", "福岡県",   "福岡市中央区",  33.5902, 130.3986),
    ("STR-017", "博多店",     "九州", "福岡県",   "福岡市博多区",  33.5890, 130.4208),
    ("STR-018", "北九州店",   "九州", "福岡県",   "北九州市",      33.8834, 130.8751),
]

schema_s = StructType([
    StructField("store_id", StringType()), StructField("store_name", StringType()),
    StructField("region", StringType()), StructField("prefecture", StringType()),
    StructField("city", StringType()), StructField("latitude", DoubleType()),
    StructField("longitude", DoubleType()),
])

write_silver(spark.createDataFrame(store_data, schema=schema_s),
    "sv_stores", "店舗マスタ（18店舗）",
    pk="store_id",
    col_comments={
        "store_id": "店舗ID（主キー）", "store_name": "店舗名",
        "region": "地域（関東/関西/東海/東北/九州）", "prefecture": "都道府県",
        "city": "市区町村", "latitude": "緯度", "longitude": "経度",
    },
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 6. sv_sales_results
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 14px 18px; border-radius: 6px; margin-bottom: 10px;">
# MAGIC   <strong>📘 6. sv_sales_results</strong> — 営業実績トランザクション（2020〜2026年、インライン生成）
# MAGIC </div>

# COMMAND ----------

import random
from datetime import date

random.seed(123)

REGIONS = {
    "関東": ["新宿店", "渋谷店", "池袋店", "横浜店", "千葉店", "埼玉店"],
    "関西": ["梅田店", "難波店", "京都店", "神戸店"],
    "東海": ["名古屋栄店", "名古屋北店", "静岡店"],
    "東北": ["仙台店", "盛岡店"],
    "九州": ["福岡天神店", "博多店", "北九州店"],
}

VEHICLE_CATS = {
    "SUV":    [("harrier", "トヨタ ハリアー", 4000000), ("vezel", "ホンダ ヴェゼル", 2800000), ("lexus_rx", "レクサス RX", 8000000)],
    "ミニバン": [("sienta", "トヨタ シエンタ", 2500000), ("freed", "ホンダ フリード", 2300000), ("voxy", "トヨタ ヴォクシー", 3200000), ("alphard", "トヨタ アルファード", 5500000)],
    "セダン":  [("prius", "トヨタ プリウス", 3500000)],
    "軽自動車":[("nbox", "ホンダ N-BOX", 1800000)],
}

REPS = [
    ("REP-001", "大前 このみ", "関東", "konomi.omae@databricks.com"),
    ("REP-002", "山田 花子",   "関東", "hanako.yamada@example.com"),
    ("REP-003", "鈴木 一郎",   "関東", "ichiro.suzuki@example.com"),
    ("REP-004", "高橋 健太",   "東海", "kenta.takahashi@example.com"),
    ("REP-005", "田村 直樹",   "関西", "naoki.tamura@example.com"),
    ("REP-006", "山本 美咲",   "東北", "misaki.yamamoto@example.com"),
    ("REP-007", "佐藤 洋介",   "関東", "yosuke.sato@example.com"),
    ("REP-008", "中村 愛",     "関西", "ai.nakamura@example.com"),
    ("REP-009", "小林 大輔",   "九州", "daisuke.kobayashi@example.com"),
    ("REP-010", "渡辺 真理",   "東海", "mari.watanabe@example.com"),
]

LOSS_REASONS = ["ローン審査否決", "希望車種なし", "他社購入", "購入見送り", "予算超過", None]

sales_rows = []
for yr in [2020, 2021, 2022, 2023, 2024, 2025, 2026]:
    for month in range(1, 13 if yr < 2026 else 5):   # 2026は1〜4月まで
        days_in_month = 28 if month == 2 else (30 if month in [4,6,9,11] else 31)
        # 2026年4月は19日までのデータに限定（デモ当日4/20に前日実績まで表示）
        max_day = 19 if (yr == 2026 and month == 4) else days_in_month
        for rep_id, rep_name, rep_region, rep_email in REPS:
            stores = REGIONS[rep_region]
            for cat, vehicles in VEHICLE_CATS.items():
                n = random.randint(3, 10)
                for _ in range(n):
                    outcome = random.choices(["成約", "失注"], weights=[0.55, 0.45])[0]
                    vkey, vname, base_price = random.choice(vehicles)
                    store = random.choice(stores)
                    sale_date = date(yr, month, random.randint(1, max_day))
                    price = int(base_price * random.uniform(0.85, 1.15)) if outcome == "成約" else 0
                    sales_rows.append({
                        "sale_id":          f"SALE-{yr}{month:02d}-{len(sales_rows)+1:06d}",
                        "sales_rep_id":     rep_id,
                        "sales_rep_name":   rep_name,
                        "sales_rep_email":  rep_email,
                        "region":           rep_region,
                        "store_name":       store,
                        "vehicle_key":      vkey,
                        "vehicle_name":     vname,
                        "vehicle_category": cat,
                        "sale_price":       price,
                        "sale_date":        sale_date.isoformat(),
                        "outcome":          outcome,
                        "loss_reason":      random.choice(LOSS_REASONS) if outcome == "失注" else None,
                    })

sr_df = (spark.createDataFrame(sales_rows)
    .withColumn("sale_date", F.to_date("sale_date"))
    .withColumn("updated_at", F.current_timestamp()))

write_silver(sr_df, "sv_sales_results", "営業実績トランザクション（2020〜2026年）。マイページ・Genie・ダッシュボード用。",
    pk="sale_id",
    col_comments={
        "sale_id": "商談ID（一意）", "sales_rep_id": "営業担当ID",
        "sales_rep_name": "営業担当氏名", "sales_rep_email": "営業担当者メールアドレス",
        "region": "地域（関東/関西/東海/東北/九州）",
        "store_name": "店舗名", "vehicle_key": "車両キー", "vehicle_name": "車両名（日本語）",
        "vehicle_category": "車種カテゴリ（SUV/ミニバン/セダン/軽自動車）",
        "sale_price": "成約金額（円）。失注の場合は0。", "sale_date": "商談日",
        "outcome": "結果（成約/失注）", "loss_reason": "失注理由（失注の場合のみ）",
        "updated_at": "最終更新日時",
    },
)

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## ✅ Silver レイヤー加工完了
# MAGIC <div style="border-left: 4px solid #388E3C; background: #E8F5E9; padding: 14px 18px; border-radius: 6px; margin-bottom: 10px;">
# MAGIC   <strong>✅ Silver レイヤー加工完了</strong>
# MAGIC </div>

# COMMAND ----------

for t in ["sv_customers", "sv_vehicle_inventory", "sv_interactions", "sv_web_browsing_behavior", "sv_stores", "sv_sales_results"]:
    print(f"  {t:<30s} {spark.table(t).count():>10,} 件")
print("✓ Silver 加工完了")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 🔑 アプリ用サービスプリンシパルへの権限付与
# MAGIC <div style="border-left: 4px solid #F57C00; background: #FFF3E0; padding: 14px 18px; border-radius: 6px; margin-bottom: 10px;">
# MAGIC   <strong>⚠️ 注意</strong> — テーブルを overwrite で再作成するとスキーマレベルの GRANT が消失するため、毎回再付与が必要です。
# MAGIC </div>

# COMMAND ----------

APP_SERVICE_PRINCIPAL = "66fd7c16-fe48-408e-8272-9d2b19513393"
for grant in ["USE SCHEMA", "SELECT", "READ VOLUME"]:
    spark.sql(f"GRANT {grant} ON SCHEMA {schema_name} TO `{APP_SERVICE_PRINCIPAL}`")
    print(f"  ✓ GRANT {grant} ON SCHEMA {schema_name}")
print("✓ サービスプリンシパル権限付与完了")
