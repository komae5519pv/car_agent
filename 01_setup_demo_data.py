# Databricks notebook source
# MAGIC %md-sandbox
# MAGIC # 01_setup_demo_data - デモデータ生成
# MAGIC <div style="background: linear-gradient(135deg, #1B2A4A 0%, #2C3E6B 50%, #1B3139 100%); padding: 20px 30px; border-radius: 10px; margin-bottom: 20px;">
# MAGIC   <div style="display: flex; align-items: center; gap: 15px;">
# MAGIC     <img src="https://www.databricks.com/wp-content/uploads/2022/06/db-nav-logo.svg" width="40" style="filter: brightness(2);"/>
# MAGIC     <div>
# MAGIC       <div style="color: #8FB8DE; font-size: 13px; font-weight: 500;">中古車販売 AI デモ</div>
# MAGIC       <div style="color: #FFFFFF; font-size: 22px; font-weight: 700; letter-spacing: 0.5px;">01_setup_demo_data - デモデータ生成</div>
# MAGIC     </div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %run ./00_config

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## 概要
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 16px 20px; border-radius: 0 8px 8px 0; margin-bottom: 20px;">
# MAGIC   <div style="font-size: 16px; font-weight: 700; color: #1565c0; margin-bottom: 6px;">概要</div>
# MAGIC   <div style="color: #333;">
# MAGIC     このノートブックは、中古車販売 AI デモで使用するサンプルデータを生成し、<br/>
# MAGIC     <code>/Volumes/{catalog_name}/{schema_name}/raw_data/</code> に Parquet ファイルとして書き出します。
# MAGIC   </div>
# MAGIC </div>
# MAGIC
# MAGIC <div style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-top: 10px;">
# MAGIC   <div style="background: #f8f9fb; border-radius: 10px; padding: 18px 14px; text-align: center; border: 1px solid #e0e0e0;">
# MAGIC     <div style="background: #1976d2; color: white; width: 32px; height: 32px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: 700; font-size: 16px; margin-bottom: 8px;">1</div>
# MAGIC     <div style="font-weight: 600; font-size: 13px; color: #333;">SFDC 商談</div>
# MAGIC     <div style="font-size: 11px; color: #888; margin-top: 4px;">sf_opportunities<br/>1,200 件</div>
# MAGIC   </div>
# MAGIC   <div style="background: #f8f9fb; border-radius: 10px; padding: 18px 14px; text-align: center; border: 1px solid #e0e0e0;">
# MAGIC     <div style="background: #1976d2; color: white; width: 32px; height: 32px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: 700; font-size: 16px; margin-bottom: 8px;">2</div>
# MAGIC     <div style="font-weight: 600; font-size: 13px; color: #333;">Web 閲覧履歴</div>
# MAGIC     <div style="font-size: 11px; color: #888; margin-top: 4px;">web_browsing_events<br/>~15,000 件</div>
# MAGIC   </div>
# MAGIC   <div style="background: #f8f9fb; border-radius: 10px; padding: 18px 14px; text-align: center; border: 1px solid #e0e0e0;">
# MAGIC     <div style="background: #1976d2; color: white; width: 32px; height: 32px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: 700; font-size: 16px; margin-bottom: 8px;">3</div>
# MAGIC     <div style="font-weight: 600; font-size: 13px; color: #333;">来店文字起こし</div>
# MAGIC     <div style="font-size: 11px; color: #888; margin-top: 4px;">visit_transcripts<br/>~200 件</div>
# MAGIC   </div>
# MAGIC   <div style="background: #f8f9fb; border-radius: 10px; padding: 18px 14px; text-align: center; border: 1px solid #e0e0e0;">
# MAGIC     <div style="background: #1976d2; color: white; width: 32px; height: 32px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: 700; font-size: 16px; margin-bottom: 8px;">4</div>
# MAGIC     <div style="font-weight: 600; font-size: 13px; color: #333;">LINE</div>
# MAGIC     <div style="font-size: 11px; color: #888; margin-top: 4px;">line_messages<br/>~600 件</div>
# MAGIC   </div>
# MAGIC   <div style="background: #f8f9fb; border-radius: 10px; padding: 18px 14px; text-align: center; border: 1px solid #e0e0e0;">
# MAGIC     <div style="background: #1976d2; color: white; width: 32px; height: 32px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: 700; font-size: 16px; margin-bottom: 8px;">5</div>
# MAGIC     <div style="font-weight: 600; font-size: 13px; color: #333;">コールセンター</div>
# MAGIC     <div style="font-size: 11px; color: #888; margin-top: 4px;">callcenter_logs<br/>~150 件</div>
# MAGIC   </div>
# MAGIC </div>

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## Step 1: SFDC 商談データ生成（1,200 件）
# MAGIC <div style="border-left: 4px solid #388E3C; background: #E8F5E9; padding: 14px 20px; border-radius: 0 8px 8px 0; margin-bottom: 16px;">
# MAGIC   <div style="font-size: 15px; font-weight: 700; color: #2E7D32;">Step 1: SFDC 商談データ生成（1,200 件）</div>
# MAGIC </div>

# COMMAND ----------

import random
from datetime import date, datetime, timedelta

random.seed(42)

# ---------- 営業担当者 10名 ----------
SALES_REPS = [
    ("REP-001", SALES_REP_NAME, "konomi.omae@databricks.com"),
    ("REP-002", "山田 花子", "hanako.yamada@example.com"),
    ("REP-003", "鈴木 一郎", "ichiro.suzuki@example.com"),
    ("REP-004", "高橋 健太", "kenta.takahashi@example.com"),
    ("REP-005", "田村 直樹", "naoki.tamura@example.com"),
    ("REP-006", "山本 美咲", "misaki.yamamoto@example.com"),
    ("REP-007", "佐藤 洋介", "yosuke.sato@example.com"),
    ("REP-008", "中村 愛", "ai.nakamura@example.com"),
    ("REP-009", "小林 大輔", "daisuke.kobayashi@example.com"),
    ("REP-010", "渡辺 真理", "mari.watanabe@example.com"),
]

# ---------- ペルソナ ----------
PERSONA_TYPES = ["子育てファミリー", "シニア夫婦", "若手社会人", "ハイクラス", "セカンドカー検討", "初めての車購入"]

# ---------- 地域 ----------
PREFECTURES = {
    "東京都": ["世田谷区", "江東区", "練馬区", "港区", "品川区", "渋谷区"],
    "神奈川県": ["横浜市青葉区", "横浜市西区", "川崎市中原区", "相模原市"],
    "千葉県": ["船橋市", "松戸市", "柏市", "市川市"],
    "埼玉県": ["さいたま市", "川口市", "所沢市", "越谷市"],
    "大阪府": ["大阪市北区", "大阪市中央区", "豊中市", "吹田市"],
    "愛知県": ["名古屋市中区", "名古屋市千種区", "豊田市"],
    "宮城県": ["仙台市青葉区", "仙台市泉区"],
    "福岡県": ["福岡市博多区", "福岡市中央区", "北九州市"],
}

OCCUPATIONS = [
    "会社員", "公務員", "自営業", "パート勤務", "主婦", "IT企業エンジニア",
    "営業職", "教師", "看護師", "医師", "弁護士", "コンサルタント",
    "メーカー勤務", "金融機関勤務", "不動産業", "飲食業",
]

VEHICLES = [
    "トヨタ アクア（2018年式）", "ホンダ フィット（2019年式）",
    "日産 ノート（2020年式）", "トヨタ プリウス（2017年式）",
    "日産 セレナ（2016年式）", "トヨタ クラウン（2018年式）",
    "ホンダ ステップワゴン（2019年式）", "スズキ ワゴンR（2021年式）",
    "ダイハツ タント（2020年式）", "トヨタ ヴィッツ（2017年式）",
    "マツダ CX-5（2020年式）", "スバル フォレスター（2019年式）",
    "ボルボ XC60（2019年式）", "BMW X3（2020年式）",
    "なし（初めての車購入）",
]

STAGES = ["リード", "来店予定", "来店済み", "試乗済み", "見積提示", "成約", "失注"]
LEAD_SOURCES = ["Web", "来店", "紹介", "SNS", "チラシ", "電話"]
LOSS_REASONS = ["予算超過", "競合他社で成約", "タイミングが合わない", "保留・検討中", "条件不一致"]

PREFERENCES_LIST = [
    "安全装備重視", "燃費重視", "広い室内", "乗り降りしやすい",
    "スタイリッシュ", "ゴルフバッグが積める", "運転しやすいサイズ",
    "SUV希望", "ミニバン希望", "軽自動車希望", "ステータス重視",
    "コスパ重視", "子育て向き", "通勤用", "アウトドア向き",
]

FAMILY_NAMES = [
    "佐藤", "鈴木", "高橋", "田中", "伊藤", "渡辺", "山本", "中村", "小林", "加藤",
    "吉田", "山田", "松本", "井上", "木村", "林", "斎藤", "清水", "山口", "阿部",
    "森", "池田", "橋本", "石川", "前田", "藤田", "岡田", "後藤", "長谷川", "村上",
]
MALE_NAMES = [
    "太郎", "一郎", "健太", "翔太", "大輔", "拓也", "直樹", "洋介", "正雄", "和也",
    "慎一", "浩二", "雅人", "達也", "康介", "裕二", "誠", "剛", "隆", "学",
]
FEMALE_NAMES = [
    "花子", "美咲", "愛", "優子", "さくら", "真理", "恵", "あかね", "陽子", "雅子",
    "千恵", "裕子", "美穂", "明美", "和子", "幸子", "由美", "直美", "智子", "麻衣",
]

# COMMAND ----------

# ---------- デモ担当者の詳細顧客 10名 ----------
DETAILED_CUSTOMERS = [
    {
        "contact_name": "山田 優子", "age": 38, "gender": "女性",
        "occupation": "パート勤務（スーパー）", "prefecture": "千葉県", "city": "船橋市",
        "family_detail": "夫（42歳・物流会社）、長女（小4）、長男（小1）、義母（72歳・同居）",
        "family_size": 5, "current_vehicle": "日産 セレナ（2016年式、12万km）",
        "current_mileage": 120000, "budget": 2800000, "budget_min": 1800000, "budget_max": 2800000,
        "preferences": "乗り降りしやすい、安全装備、運転しやすいサイズ",
        "persona_type": "子育てファミリー", "stage": "来店済み",
    },
    {
        "contact_name": "佐藤 健一", "age": 52, "gender": "男性",
        "occupation": "中堅メーカー 営業部長", "prefecture": "埼玉県", "city": "さいたま市",
        "family_detail": "妻（50歳・専業主婦）、長女（社会人・独立）、長男（大学4年・就活中）",
        "family_size": 3, "current_vehicle": "トヨタ クラウン（2018年式、6万km）",
        "current_mileage": 60000, "budget": 4500000, "budget_min": 3000000, "budget_max": 4500000,
        "preferences": "ある程度の格、ゴルフバッグが積める、スタイリッシュ",
        "persona_type": "シニア夫婦", "stage": "来店済み",
    },
    {
        "contact_name": "田中 翔太", "age": 29, "gender": "男性",
        "occupation": "IT企業 システムエンジニア", "prefecture": "東京都", "city": "江東区",
        "family_detail": "独身、彼女あり（1年半）",
        "family_size": 1, "current_vehicle": "なし（初めての車購入）",
        "current_mileage": 0, "budget": 2300000, "budget_min": 1500000, "budget_max": 2300000,
        "preferences": "彼女がSUV希望、かっこよければOK、実用的",
        "persona_type": "初めての車購入", "stage": "来店済み",
    },
    {
        "contact_name": "渡辺 雅子", "age": 45, "gender": "女性",
        "occupation": "外資系コンサル シニアマネージャー", "prefecture": "神奈川県", "city": "横浜市青葉区",
        "family_detail": "夫（47歳・医師）、長女（中2）、長男（小5）",
        "family_size": 4, "current_vehicle": "ボルボ XC60（2019年式、4万km）",
        "current_mileage": 40000, "budget": 6000000, "budget_min": 4000000, "budget_max": 6000000,
        "preferences": "安全性最優先、上質、積載量、ステータス",
        "persona_type": "ハイクラス", "stage": "来店済み",
    },
    {
        "contact_name": "木村 裕二", "age": 35, "gender": "男性",
        "occupation": "公務員", "prefecture": "東京都", "city": "練馬区",
        "family_detail": "妻（33歳・看護師）、長男（3歳）、次男（0歳）",
        "family_size": 4, "current_vehicle": "ホンダ フィット（2019年式、5万km）",
        "current_mileage": 50000, "budget": 3000000, "budget_min": 2000000, "budget_max": 3000000,
        "preferences": "安全装備、チャイルドシート対応、燃費",
        "persona_type": "子育てファミリー", "stage": "来店予定",
    },
    {
        "contact_name": "松本 あかね", "age": 26, "gender": "女性",
        "occupation": "事務職", "prefecture": "神奈川県", "city": "川崎市中原区",
        "family_detail": "独身",
        "family_size": 1, "current_vehicle": "なし（初めての車購入）",
        "current_mileage": 0, "budget": 2000000, "budget_min": 1500000, "budget_max": 2200000,
        "preferences": "コンパクト、かわいい、駐車しやすい",
        "persona_type": "初めての車購入", "stage": "リード",
    },
    {
        "contact_name": "伊藤 正雄", "age": 62, "gender": "男性",
        "occupation": "定年退職（元銀行員）", "prefecture": "埼玉県", "city": "所沢市",
        "family_detail": "妻（60歳）、子供は独立",
        "family_size": 2, "current_vehicle": "トヨタ マークX（2015年式、8万km）",
        "current_mileage": 80000, "budget": 3500000, "budget_min": 2500000, "budget_max": 3500000,
        "preferences": "乗り心地、静粛性、高級感",
        "persona_type": "シニア夫婦", "stage": "試乗済み",
    },
    {
        "contact_name": "高橋 美穂", "age": 42, "gender": "女性",
        "occupation": "自営業（カフェ経営）", "prefecture": "東京都", "city": "世田谷区",
        "family_detail": "夫（44歳・デザイナー）、長女（小6）、長男（小3）",
        "family_size": 4, "current_vehicle": "トヨタ ヴォクシー（2018年式、7万km）",
        "current_mileage": 70000, "budget": 3500000, "budget_min": 2500000, "budget_max": 3500000,
        "preferences": "おしゃれ、積載量、アウトドア向き",
        "persona_type": "子育てファミリー", "stage": "見積提示",
    },
    {
        "contact_name": "中島 康介", "age": 48, "gender": "男性",
        "occupation": "商社勤務（課長）", "prefecture": "大阪府", "city": "豊中市",
        "family_detail": "妻（45歳・パート）、長女（高1）、次女（中1）",
        "family_size": 4, "current_vehicle": "マツダ CX-5（2020年式、3万km）",
        "current_mileage": 30000, "budget": 4000000, "budget_min": 3000000, "budget_max": 4000000,
        "preferences": "走りの楽しさ、SUV、ゴルフ",
        "persona_type": "ハイクラス", "stage": "来店済み",
    },
    {
        "contact_name": "藤田 さくら", "age": 31, "gender": "女性",
        "occupation": "看護師", "prefecture": "千葉県", "city": "柏市",
        "family_detail": "夫（33歳・会社員）、長女（2歳）",
        "family_size": 3, "current_vehicle": "ダイハツ タント（2020年式、3万km）",
        "current_mileage": 30000, "budget": 2500000, "budget_min": 1800000, "budget_max": 2500000,
        "preferences": "スライドドア、安全装備、子育て向き",
        "persona_type": "子育てファミリー", "stage": "来店予定",
    },
]

# COMMAND ----------

# ---------- レコード生成 ----------
records = []

# まず: デモ担当者の詳細顧客 10名
for i, cust in enumerate(DETAILED_CUSTOMERS):
    opp_id = f"OPP-{i+1:04d}"
    base_date = date(2026, 3, 1)
    created = base_date - timedelta(days=random.randint(10, 90))
    records.append({
        "sf_opportunity_id": opp_id,
        "customer_id": f"CUST-{i+1:04d}",
        "sales_rep_id": "REP-001",
        "sales_rep_name": SALES_REP_NAME,
        "sales_rep_email": "konomi.omae@databricks.com",
        "contact_name": cust["contact_name"],
        "age": cust["age"],
        "gender": cust["gender"],
        "occupation": cust["occupation"],
        "family_detail": cust["family_detail"],
        "family_size": cust["family_size"],
        "prefecture": cust["prefecture"],
        "city": cust["city"],
        "current_vehicle": cust["current_vehicle"],
        "current_mileage": cust["current_mileage"],
        "budget": cust["budget"],
        "budget_min": cust["budget_min"],
        "budget_max": cust["budget_max"],
        "preferences": cust["preferences"],
        "stage": cust["stage"],
        "lead_source": random.choice(LEAD_SOURCES),
        "persona_type": cust["persona_type"],
        "visit_scheduled_date": (base_date + timedelta(days=random.randint(1, 30))).isoformat(),
        "created_date": created.isoformat(),
        "last_activity_date": (created + timedelta(days=random.randint(1, 30))).isoformat(),
        "close_date": (base_date + timedelta(days=random.randint(30, 90))).isoformat(),
        "loss_reason": random.choice(LOSS_REASONS) if cust["stage"] == "失注" else None,
    })

# 次に: ランダム顧客 1,190名（全10担当者に分配）
for i in range(10, 1200):
    opp_id = f"OPP-{i+1:04d}"
    rep = random.choice(SALES_REPS)
    gender = random.choice(["男性", "女性"])
    age = random.randint(22, 68)
    pref_key = random.choice(list(PREFECTURES.keys()))
    city = random.choice(PREFECTURES[pref_key])
    persona = random.choice(PERSONA_TYPES)
    stage = random.choices(STAGES, weights=[15, 15, 20, 10, 10, 20, 10])[0]
    budget_min = random.choice([1200000, 1500000, 1800000, 2000000, 2500000, 3000000, 3500000, 4000000])
    budget_max = budget_min + random.choice([500000, 800000, 1000000, 1500000, 2000000])

    if gender == "男性":
        name = f"{random.choice(FAMILY_NAMES)} {random.choice(MALE_NAMES)}"
    else:
        name = f"{random.choice(FAMILY_NAMES)} {random.choice(FEMALE_NAMES)}"

    family_size = random.randint(1, 6)
    created = date(2026, 1, 1) + timedelta(days=random.randint(0, 100))

    records.append({
        "sf_opportunity_id": opp_id,
        "customer_id": f"CUST-{i+1:04d}",
        "sales_rep_id": rep[0],
        "sales_rep_name": rep[1],
        "sales_rep_email": rep[2],
        "contact_name": name,
        "age": age,
        "gender": gender,
        "occupation": random.choice(OCCUPATIONS),
        "family_detail": f"家族{family_size}人",
        "family_size": family_size,
        "prefecture": pref_key,
        "city": city,
        "current_vehicle": random.choice(VEHICLES),
        "current_mileage": random.randint(0, 150000),
        "budget": budget_max,
        "budget_min": budget_min,
        "budget_max": budget_max,
        "preferences": "、".join(random.sample(PREFERENCES_LIST, k=random.randint(2, 4))),
        "stage": stage,
        "lead_source": random.choice(LEAD_SOURCES),
        "persona_type": persona,
        "visit_scheduled_date": (created + timedelta(days=random.randint(7, 60))).isoformat(),
        "created_date": created.isoformat(),
        "last_activity_date": (created + timedelta(days=random.randint(1, 30))).isoformat(),
        "close_date": (created + timedelta(days=random.randint(30, 120))).isoformat(),
        "loss_reason": random.choice(LOSS_REASONS) if stage == "失注" else None,
    })

sf_df = spark.createDataFrame(records)
sf_df.write.mode("overwrite").parquet(f"/Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/sf_opportunities")
print(f"✓ sf_opportunities: {sf_df.count():,} 件 → /Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/sf_opportunities")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## Step 2: Web 閲覧行動ログ生成（~15,000 件）
# MAGIC <div style="border-left: 4px solid #388E3C; background: #E8F5E9; padding: 14px 20px; border-radius: 0 8px 8px 0; margin-bottom: 16px;">
# MAGIC   <div style="font-size: 15px; font-weight: 700; color: #2E7D32;">Step 2: Web 閲覧行動ログ生成（~15,000 件）</div>
# MAGIC </div>

# COMMAND ----------

VEHICLE_KEYS = [
    ("harrier", "トヨタ ハリアー"), ("sienta", "トヨタ シエンタ"), ("freed", "ホンダ フリード"),
    ("voxy", "トヨタ ヴォクシー"), ("alphard", "トヨタ アルファード"), ("vezel", "ホンダ ヴェゼル"),
    ("prius", "トヨタ プリウス"), ("nbox", "ホンダ N-BOX"), ("lexus_rx", "レクサス RX"),
]
SEARCH_KEYWORDS = [
    "SUV おすすめ", "ミニバン 安い", "燃費 いい車", "安全装備 充実",
    "ファミリーカー", "中古車 200万以下", "ハイブリッド", "スライドドア",
    "コンパクトSUV", "レクサス 中古", "軽自動車 広い",
]
DEVICES = ["スマートフォン", "PC", "タブレット"]
EVENT_TYPES = ["search", "view", "click", "favorite"]

events = []
event_counter = 0

for rec in records:
    opp_id = rec["sf_opportunity_id"]
    is_detailed = int(opp_id.split("-")[1]) <= 10
    n_events = random.randint(20, 40) if is_detailed else random.randint(5, 15)
    n_sessions = random.randint(3, 8) if is_detailed else random.randint(1, 4)
    sessions = [f"SES-{opp_id}-{s+1:02d}" for s in range(n_sessions)]

    base_ts = datetime(2026, 2, 1) + timedelta(days=random.randint(0, 60))
    device = random.choice(DEVICES)

    for _ in range(n_events):
        event_counter += 1
        ev_type = random.choices(EVENT_TYPES, weights=[20, 40, 25, 15])[0]
        if ev_type == "search":
            vk, vn = "", ""
            kw = random.choice(SEARCH_KEYWORDS)
        else:
            vk, vn = random.choice(VEHICLE_KEYS)
            kw = ""

        events.append({
            "event_id": f"EVT-{event_counter:06d}",
            "sf_opportunity_id": opp_id,
            "session_id": random.choice(sessions),
            "event_type": ev_type,
            "vehicle_key": vk,
            "vehicle_name": vn,
            "search_keyword": kw,
            "device_type": device,
            "event_timestamp": (base_ts + timedelta(hours=random.randint(0, 1440))).isoformat(),
        })

web_df = spark.createDataFrame(events)
web_df.write.mode("overwrite").parquet(f"/Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/web_browsing_events")
print(f"✓ web_browsing_events: {web_df.count():,} 件 → /Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/web_browsing_events")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## Step 3: 来店時の文字起こしデータ生成（~200 件）
# MAGIC <div style="border-left: 4px solid #388E3C; background: #E8F5E9; padding: 14px 20px; border-radius: 0 8px 8px 0; margin-bottom: 16px;">
# MAGIC   <div style="font-size: 15px; font-weight: 700; color: #2E7D32;">Step 3: 来店時の文字起こしデータ生成（~200 件）</div>
# MAGIC </div>

# COMMAND ----------

# ---------- 店舗マスタ ----------
STORES = {
    "関東": ["新宿店", "渋谷店", "池袋店", "横浜店", "千葉店", "埼玉店"],
    "関西": ["梅田店", "難波店", "京都店", "神戸店"],
    "東海": ["名古屋栄店", "名古屋北店", "静岡店"],
    "東北": ["仙台店", "盛岡店"],
    "九州": ["福岡天神店", "博多店", "北九州店"],
}

# ---------- 詳細トランスクリプト（デモ担当 10 名分）----------
DETAILED_TRANSCRIPTS = [
    # 山田 優子 (OPP-0001) - 子育てファミリー、義母同居
    "えっとですねあの今乗ってるのがセレナなんですけど もう8年くらいになるんですよねー 走行距離もけっこういっちゃってて12万キロ超えてるんです そうなんですよ最近ちょっとエアコンの調子も悪くて夏場とかやばいんですよね 子供乗せてるのにって思っちゃって あーそうなんです子供が2人いて 上が小4で下が小1なんですけど まあ元気で習い事とか送り迎えがすごい多くて 週に何回だろうえっとピアノと水泳と塾で まあほぼ毎日どっか行ってますね はい使うのはほぼ私ですね主人は別の車で通勤してるんで そうなんですあと義母も一緒に住んでて 足が悪いわけじゃないんですけどまあ歳なんで病院とか連れてったりとか 週2くらいで乗せることがあるんですよ だから乗り降りしやすい車がいいなって思ってて うーん予算はですねえっと諸費用込みで280万くらいまでで抑えたいなって思ってるんですけど どうですかね厳しいですか そうなんですよね広さも欲しいし安全なやつがいいし でも高いのは無理だしって はいアルファードとかママ友が乗ってて正直いいなーって思うんですけどさすがに予算が ははは夢ですよね いやでも広いのはいいですよね義母も乗りやすいだろうし シエンタとかフリードとかってどうなんですか 小さくないですか 実は見たことなくて そうなんですか3列あるんですね知らなかったです あと私運転そんな上手くないんで大きい車だとちょっと不安で 駐車とかいつも何回も切り返しちゃうんですよね",

    # 佐藤 健一 (OPP-0002) - シニア夫婦、元営業部長のプライド
    "あのね今クラウン乗ってるんだけど 2018年のやつ そろそろ乗り換えようかなと思って まあ不満があるわけじゃないんだけどね 維持費がね結構かかるでしょ ガソリン代とか税金とか まあ会社の車じゃないからさ全部自腹なわけ そう定年がね来年見えてきたから ちょっと考えないとなって 妻がねあんまり運転しないんだけど 最近買い物とか一緒に行くことが増えてさ 俺が運転手よ はは 娘はもう独立してて息子は大学4年なんだけど就活中でさ 車貸してくれって言うんだけどクラウンはちょっとな やっぱり自分のとして愛着あるからさ 週末ゴルフ行くのが唯一の趣味でね バッグ積めないと困るんだよ あと友達乗せることもあるから4人は乗れないと まあ予算はねどれくらいだろう400万くらいまでかな もうちょいいけるかもしれないけど まあ450万が上限だね 妻は小さい車がいいって言うんだけど 俺としてはさ営業部長やってきたプライドっていうの まあある程度の車には乗りたいわけ 軽とかは絶対無理ね 本当はさスポーツカーとか乗りたい気持ちもあるんだけど 現実的じゃないよな 歳も歳だし いやでもハリアーとかカッコいいよね 見た目がさ嫌いじゃない SUVって燃費どうなの 前はセダン一筋だったから全然わかんないんだよね",

    # 田中 翔太 (OPP-0003) - 初めての車購入、彼女と結婚視野
    "あ初めまして田中です えっと今日車探しに来たんですけど 実は車買うの初めてで全然わからなくて すいません何聞いていいかもわからない状態で えっとですね今まで車持ってなかったんですけど 最近会社が週2出社になって通勤で使えたらいいなと思って 今カーシェアとか使ってたんですけど週末取れないこと多くて彼女に会いに行くのにちょっと困ってて そう彼女が千葉に住んでてそこまで行くのに電車だと結構かかるんですよね 予算はですねえっと150から200ちょい万くらいで考えてて 駐車場代が月3万するんで車自体はあんま高くできないんですよ 彼女はSUVがいいって言うんですけど自分は正直よくわかんなくて かっこよければなんでもいいかなみたいな 適当ですよね すいません あと来年あたり結婚とかも考えてて まあまだプロポーズしてないんですけど だから子供とか考えるとまた変わるのかなとは思うんですけど 今はとりあえず2人で使えればいいかなって ヴェゼルってなんですか あホンダの そうなんですか人気なんですね 見た目はいい感じですね あ中古であるんですか そっか新車じゃなくてもいいのか 全然考えてなかったです",

    # 渡辺 雅子 (OPP-0004) - ハイクラス、安全性最優先
    "お忙しいところありがとうございます渡辺です えっと今ボルボのXC60乗ってるんですけど リースがもうすぐ終わるんですね 2019年式で走行距離は4万キロくらいかな特に不満はないんですけど 再リースするか買い取るか新しいのにするか迷っていて それでいろいろ見てみようかなと 主人は別で車持ってるんですけどBMWの 家族で出かける時は私の車使うこと多いんですよね なぜか広いからかな 子供が2人いて中2と小5なんですけど 上の子がテニス部で荷物がすごいんですよ ラケット何本も持ってくし遠征とか行くと大荷物で 安全性は絶対妥協したくないですね 子供乗せる車なんで 前にボルボにしたのもそれが理由で あのボルボって安全性能いいじゃないですか 衝突試験とかでも評価高くて でも最近周りでレクサス乗ってる人多くて ちょっと気になってて RXとかNXとか 見た目も素敵だなって 予算は400万から600万くらいで考えてます 中古でも全然いいんですけど やっぱり安全装備は最新がいいのかなとも思うし 主人は好きなの選べばって言うんですけど 家計管理してるの私なんでそんな気軽に言わないでって感じですよね",

    # 木村 裕二 (OPP-0005) - 若い子育てファミリー、0歳児のチャイルドシート
    "木村と申しますよろしくお願いします えっと今乗ってるのがホンダのフィットなんですけどね 2019年のやつで5万キロくらいです 買った時は独身だったんですよ それが結婚して子供ができて去年二人目が生まれて あのーもう限界で チャイルドシート2つ積むとね後部座席がキツキツで 妻がね後ろに座って授乳とかするんですけど腰が痛いって言ってて そうですね下の子がまだ0歳で上は3歳になったばかりで 妻が看護師で夜勤もあるんで 僕が送り迎えすることも多くて 休日は家族で公園行ったりとか ベビーカー積んで 正直フィットじゃ厳しくなってきたんですよね あと安全面が気になってて 子供乗せるんで 自動ブレーキとかが最新のやつがいいなって 予算はあの諸費用込みで300万以内 できれば250万くらいで考えてます 公務員なんで安定はしてるんですけど そんな贅沢もできなくて 妻と相談してシエンタかフリードかなって思ってるんですけど あれ3列目って実際使うんですかね 祖父母が遠方なんで年に数回しか来ないし でも下の子がもう少し大きくなったら使うかなとか あと燃費もちゃんと見たいですね フィットが燃費よかったんで同じくらいは欲しくて",

    # 松本 あかね (OPP-0006) - 独身OL、初めての車、コンパクト希望 ★AI失敗デモ対象
    "こんにちは松本ですよろしくお願いします 車を買うのが初めてで全然わからなくて まずどこから見ていいかも それで今日ちょっと見てみようかなって 車なかった理由はですね 都心に住んでたし電車で何とかなってたんですけど 今年実家の母が入退院してまして 川崎なんですけど横浜の病院に通うことが多くて 電車だと乗り換えも多くて 母が辛そうで そう だから車があったほうが便利かなって やっぱ自分で動けるのが安心で 普段は友達とカフェ行ったりドライブしたりできたらいいなって 予算はですね150万から220万円以内で 最大でも220までですね貯金との兼ね合いで それ以上は無理です 無理です 絶対無理なので むしろもう少し安く抑えたいくらい あとできれば可愛い見た目の車がいいなって 女の子っぽいというか シンプルでおしゃれなやつ あの色も大事で 白かな ピンクとかもあるんですかね そう あと運転初心者なので コンパクトで駐車しやすいのがいいです 実家のマンションの駐車場もあんまり広くなくて 大きい車だと絶対ぶつけちゃうから 友達がヤリスとかアクアに乗ってるんですけど あれくらいのサイズ感で探してます SUVとかは大きすぎて無理です 燃費も大事ですよね毎月のガソリン代もあるし とにかく予算重視で あと運転しやすさと可愛さ それだけです",

    # 伊藤 正雄 (OPP-0007) - 退職後の夫婦、静粛性・高級感
    "伊藤と申します お時間ありがとうございます 今マークXに乗ってるんですよ 2015年式の8万キロ 定年で銀行を退職したのが一昨年でね 今は妻と二人で悠々自適といきたいところなんですが そうこのマークXがね もう8万キロでね 大きな故障はないんだけど 音がね 静かじゃなくなってきて 昔は気にならなかったんだけど 歳とったのかな 耳が敏感になったのか ロードノイズというのかな それが気になって もう少し静かな車に乗りたいなって思ってね 予算は250万から350万くらいで 中古で構いません ていうかむしろ中古のほうが気楽というか 新車買っても死ぬまで乗れるかもわからないですしね はは 妻はですね こう 一緒に旅行したがっててね 行くたびに車で行きたいって言うんです 日帰り温泉とかね だから長距離乗っても疲れない車がいいかなと 乗り心地がね 一番大事です 高級感もあるといいですね セダンにこだわってるわけじゃないんですが やっぱり車内はある程度上質であってほしいと ゴルフは最近膝が痛くてあまり行かないんですが ブリッドポートの絨毯みたいな上質な内装がいいんですよ 本革とかね あとナビとか最近のは便利そうなので そういうのも欲しい 正直あまり詳しくないので レクサスとかそういう選択肢もあるんですかね 予算が合えば",

    # 高橋 美穂 (OPP-0008) - カフェ経営、アウトドア、おしゃれ重視
    "高橋です よろしくお願いします えっと自営業でカフェ経営してるんですが 今乗ってるのがヴォクシーで 子供の送り迎えと仕事の両方で使ってて そうなんです 店の仕入れとかもこれで行ってて 無印とかIKEAで什器買ってきたり ちょっと大物を運ぶこともあって 今のヴォクシーが2018年式で7万キロ使い倒してて まあ広いし便利なんですけど ちょっと飽きたっていうのと もう少しおしゃれな車に乗りたいなって 仕事柄インスタとかに車が映ることもあるし 来てくださるお客様もおしゃれな方が多くて ヴォクシーってどうしてもファミリーカーって感じで 主人がデザイナーなんですけど あの人がね最近キャンプとかアウトドアにハマってて 4人でキャンプ行こうよとか言い出して 子供が小6と小3でね 道具も増えてきて 屋根に積むやつ何ていうんでしたっけ ルーフボックス ああそうそう あれとかも載せられるといいなって あと週末は河原でBBQしたりとか 結構アクティブに使ってるんですよ 予算は250から350万くらいで見ていて これは中古前提です 新車はちょっと手が出ないので ハスラーとかジムニーとかカッコいいなって思うんですけど 子供2人乗せて仕事の荷物も運ぶって考えると狭すぎるかな CX-5とかハリアーとか SUVも素敵だなって思ってて 何がいいんですかね",

    # 中島 康介 (OPP-0009) - ハイクラス、走りの楽しさ、ゴルフ
    "中島です よろしくお願いします 商社で課長やってましてね 今マツダのCX-5に乗ってるんですよ 2020年式の3万キロ 正直まだ乗り換えタイミングじゃないんだけど 最近ね 決算のご褒美というか まあそういう気分で 見に来ました 今のCX-5気に入ってるんですよ 走りが楽しくて やっぱりマツダの走りってのは他とは違うというか ハンドリングがね 俺はそういうの好きなんで でも子供が娘2人でね 高1と中1なんですけど 中学生になってから部活の送り迎えがまあ増えまして テニス部と吹奏楽部で 楽器積んだりするんで もう少し荷室広いほうがいいかなと あと妻がパートで 平日は妻が運転することもあるので 取り回しがそんなに悪くないほうがいいと 休日はね ゴルフが趣味でね 月2くらいで仲間と行くんですが バッグ4つ積めるといいな あと長距離走るので 高速の安定感も大事 予算はね 400万以内 中古OK 300万台で買えたら理想 外車も気にはなるんですよ BMWのX3とか でも維持費考えるとちょっとね 国産のが安心かな 一番は走りの楽しさ損ねたくないってとこですかね SUVでしばるなら ハリアーとかも見たいけど あれ走りはどうなんですか",

    # 藤田 さくら (OPP-0010) - 若い子育て、スライドドア絶対
    "藤田です よろしくお願いします 看護師やってましてね 今はタントに乗ってるんですけど 軽自動車 2020年式で3万キロ 独身の時から乗ってて 結婚して子供ができてもまだ乗ってるんですけど そろそろ限界かなって 子供が2歳の娘なんですけど チャイルドシート積むとね後部座席狭くて もう1人欲しいねって夫と話してて そうなると軽じゃもう無理だねって 旦那は会社員で 私が夜勤もあるので 娘の送迎とか夫に頼むこともあって 夫も乗るんで 夫は大きい車運転したことないから コンパクトなほうがいいって言ってるんですけど でもスライドドア絶対なんですよね うちの駐車場狭くて 隣の車にドアぶつけそうになったことあって あと子供抱っこして荷物持って 普通のドアだと開閉が大変で スライドドアって便利じゃないですか あと安全装備は絶対最新のがいいです 子供乗せるから あれよくCMでやってる自動ブレーキとか 予算は180から250万くらい 夫が家計の大蔵省なんでそこまでしか出せないって もう中古で全然OKです 新車じゃなくても ファミリアカーぽくなくて可愛い感じのも少し気にはなってるんですけど とにかくスライドドア あと安全 それが外せない条件ですね フリードとかシエンタが良さそうって調べて 今日はその辺を見てみたいんですけど",
]

# ---------- テンプレート（その他の顧客向け）----------
TRANSCRIPT_TEMPLATES = [
    "えっと今{current_vehicle}に乗ってるんですけど そろそろ乗り換えようかなと思って 予算は{budget}万円くらいで考えてます {preferences}な車がいいですね 家族は{family}なので広さも必要です",
    "初めまして 今日は車を見に来ました 予算は{budget}万円以内で {preferences}な車を探してます 今は{current_vehicle}に乗ってます",
    "こんにちは 今乗ってるのが{current_vehicle}で もう古くなってきたので買い替えを考えてます {preferences}を重視してます 予算は{budget}万円くらいまでで",
]

# ---------- 都道府県→地域マッピング ----------
PREF_TO_REGION = {}
for _region, _prefs in [
    ("関東", ["東京都", "神奈川県", "千葉県", "埼玉県"]),
    ("関西", ["大阪府", "京都府", "兵庫県"]),
    ("東海", ["愛知県", "静岡県"]),
    ("東北", ["宮城県", "岩手県"]),
    ("九州", ["福岡県"]),
]:
    for _p in _prefs:
        PREF_TO_REGION[_p] = _region

# ---------- 生成 ----------
transcripts = []
t_counter = 0

for rec in records:
    if rec["stage"] not in ["来店済み", "試乗済み", "見積提示", "成約"]:
        continue
    t_counter += 1
    opp_id = rec["sf_opportunity_id"]
    opp_num = int(opp_id.split("-")[1])

    # 詳細トランスクリプト（大前このみ担当の主要 10 名）
    if opp_num <= 10:
        text = DETAILED_TRANSCRIPTS[opp_num - 1]
    else:
        tmpl = random.choice(TRANSCRIPT_TEMPLATES)
        text = tmpl.format(
            current_vehicle=rec["current_vehicle"],
            budget=rec["budget"] // 10000,
            preferences=rec["preferences"],
            family=rec["family_detail"],
        )

    region = PREF_TO_REGION.get(rec["prefecture"], "関東")
    store = random.choice(STORES[region])

    transcripts.append({
        "transcript_id": f"TR-{t_counter:04d}",
        "sf_opportunity_id": opp_id,
        "visit_date": rec["last_activity_date"],
        "store_name": store,
        "sales_rep_name": rec["sales_rep_name"],
        "duration_minutes": random.randint(8, 25) if opp_num <= 10 else random.randint(5, 15),
        "transcript_text": text,
        "created_at": datetime.now().isoformat(),
    })

vt_df = spark.createDataFrame(transcripts)
vt_df.write.mode("overwrite").parquet(f"/Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/visit_transcripts")
print(f"✓ visit_transcripts: {vt_df.count():,} 件 → /Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/visit_transcripts")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## Step 4: LINE メッセージデータ生成（~600 件）
# MAGIC <div style="border-left: 4px solid #388E3C; background: #E8F5E9; padding: 14px 20px; border-radius: 0 8px 8px 0; margin-bottom: 16px;">
# MAGIC   <div style="font-size: 15px; font-weight: 700; color: #2E7D32;">Step 4: LINE メッセージデータ生成（~600 件）</div>
# MAGIC </div>

# COMMAND ----------

CUSTOMER_MSGS = [
    "お世話になっております。先日は丁寧にご案内いただきありがとうございました。",
    "予算のことで相談したいのですが、ローンの場合はどのくらいになりますか？",
    "家族に相談したところ、やはり安全装備が充実している車がいいとのことでした。",
    "週末に試乗させていただくことは可能でしょうか？",
    "他のカラーバリエーションはありますか？",
    "納車までどのくらいかかりますか？",
    "下取り価格はどのくらいになりそうですか？",
]
STAFF_MSGS = [
    "お問い合わせありがとうございます！はい、喜んでご案内させていただきます。",
    "ローンの場合は月々約3万円からご利用いただけます。詳細はご来店時にご説明いたします。",
    "かしこまりました。安全装備が充実した車種をいくつかピックアップしてお待ちしております。",
    "週末でしたら土曜日の午前中が空いております。ご都合はいかがでしょうか？",
    "承知いたしました。カタログをお送りいたしますね。",
]

# ---------- 詳細 LINE 会話（大前このみ担当の主要 10 名、OPP-0001 ~ OPP-0010）----------
# 各顧客のペルソナに沿った会話を 6-8 往復で展開
DETAILED_LINE_CONVERSATIONS = [
    # OPP-0001 山田 優子 - 子育てファミリー、義母同居、シエンタ検討
    [
        ("customer", "先日はお世話になりました、山田です。シエンタのカタログ、早速家で見てみました！義母も興味津々です笑"),
        ("staff", "山田様こんにちは！大前です。ご家族でご覧いただけたようで嬉しいです😊 義母様にも気に入っていただけそうで何よりです。"),
        ("customer", "1つ質問なんですが、シエンタの低床設計って、義母の足でも本当にラクに乗り降りできますか？身長150cmないくらいで、膝も少し弱いんです。"),
        ("staff", "ご安心ください。シエンタは地上高約330mmで、ミニバンの中でも最低クラスの低床です。膝への負担が少なく、ステップも不要です。試乗で義母様にも実際にお試しいただくのが一番かと思います。"),
        ("customer", "ありがとうございます。あと子供2人乗せて習い事の送迎で使うのですが、3列目って日常的に畳んでおくことってできますか？"),
        ("staff", "もちろんです。シエンタの3列目は床下に完全収納できる構造になっていて、普段は広いラゲッジとしてお使いいただけます。ベビーカーや習い事の荷物も余裕です。"),
        ("customer", "すごい！じゃあ来週の土曜に義母も連れて試乗行ってもいいですか？子供も一緒で大丈夫でしょうか"),
        ("staff", "ぜひお越しください！お子様用のチャイルドシートもご用意してお待ちしております。土曜10:30でお取りしますね。"),
    ],
    # OPP-0002 佐藤 健一 - 元営業部長、プライドとSUV
    [
        ("customer", "佐藤です。先日のハリアーの件、いろいろ考えました。やっぱり気になるのは燃費ですね。セダン一筋だったので正直わからない。"),
        ("staff", "佐藤様、お問い合わせありがとうございます。ハリアーのハイブリッドは22.3km/Lで、クラウンより実は燃費が良いんです。高速中心なら差はさらに広がります。"),
        ("customer", "へぇ、それは意外だね。あと気になるのは乗り心地かな。妻が腰あまり強くなくてね。"),
        ("staff", "ハリアーは専用サスペンションで長距離でも疲れにくい設計です。妻様にもぜひお試しいただきたいです。日曜のゴルフ前に軽く試乗などいかがでしょうか。"),
        ("customer", "そうだな、今度の日曜にでも寄らせてもらうよ。息子も連れてっていいかな？"),
        ("staff", "もちろんです！息子様もご一緒にお越しください。ご家族みなさまでの試乗をご用意いたします。"),
        ("customer", "それとゴルフバッグ4つ積めるか、どうしても確認したいんだ。仲間連れていくこと多いから。"),
        ("staff", "ハリアーは後席を倒せば大人4人+ゴルフバッグ4つ余裕で入ります。試乗の際にトランクに実際に積んでご確認いただきましょう。"),
    ],
    # OPP-0003 田中 翔太 - 初めての車、彼女、ヴェゼル
    [
        ("customer", "田中です。先日はいろいろ教えていただきありがとうございました！ヴェゼル調べたらめっちゃかっこよくて、彼女にも見せたら「これいいね」って。"),
        ("staff", "田中様、彼女様にも気に入っていただけてよかったです😊 ヴェゼルは若いカップルに本当に人気ですよ。"),
        ("customer", "中古って何年落ちくらいまでなら安心ですか？5年以内とかですか？全然わからなくて..."),
        ("staff", "初めてのお車でしたら、3-5年落ち・走行5万km以内がおすすめです。私どもは修復歴なし・整備記録ありの車両しか扱っていませんのでご安心ください。"),
        ("customer", "ローンって審査厳しいですか？社会人3年目で年収450万くらいなんですけど。"),
        ("staff", "十分ご通過いただける水準かと思います。月々2.5万円程度で頭金なしでも可能なプランもあります。詳しいシミュレーションをお送りしますね。"),
        ("customer", "ありがとうございます！あと彼女と一緒に見に行きたいのですが、土日だと何時がおすすめですか？"),
        ("staff", "日曜の午後なら比較的ゆっくりご案内できます。次の日曜14時など、いかがですか？彼女様の好きなカラーも見ていただけますよ。"),
    ],
    # OPP-0004 渡辺 雅子 - ハイクラス、安全性最優先、レクサス検討
    [
        ("customer", "渡辺です。先日はお時間ありがとうございました。主人とも相談して、やはり安全性が最優先で見ています。レクサスNXかRXで迷っています。"),
        ("staff", "渡辺様、ご連絡ありがとうございます。ご家族、特にお子様の安全を考えるとどちらも素晴らしい選択肢です。"),
        ("customer", "上の子が中2でテニス部で、ラケット何本も積むんです。NXとRXだとラゲッジスペースはどれくらい違いますか？"),
        ("staff", "RXの方が約130L広く、テニスラケット・遠征バッグも余裕です。ただNXも通常利用には十分広く、取り回しが良いメリットがあります。"),
        ("customer", "ボルボXC60から乗り換えるとなると、安全装備の違いも気になるんですよね。レクサスセーフティシステム＋ってボルボのシティセーフティと比較してどうですか？"),
        ("staff", "どちらも最新規格に対応していますが、レクサスは日本の交通環境に最適化されており、市街地での歩行者検知精度が特に高いです。詳細資料をお送りします。"),
        ("customer", "ありがとうございます。主人も一緒に見たいと言っていまして、今週末に行けそうです。"),
        ("staff", "お待ちしております。ご主人様にもご満足いただけるよう、NXとRXの乗り比べ試乗をご用意しますね。"),
    ],
    # OPP-0005 木村 裕二 - 公務員、0歳/3歳子育て、フリード検討
    [
        ("customer", "木村です。お世話になります。妻とフリードとシエンタで迷ってるんですけど、決定的な違いってなんですか？"),
        ("staff", "木村様こんにちは！大前です。ご質問ありがとうございます。一番の違いは3列目の使いやすさです。フリードは3列目が少し広く、長距離でも大人が座れます。"),
        ("customer", "なるほど。うち下の子0歳で上が3歳なんで、当面3列目は使わないと思うんですよね。それでもフリードのメリットありますか？"),
        ("staff", "あります！Honda SENSINGの先進安全装備がシエンタより一部上位で、特にACC（追従クルコン）が全車速対応です。高速での運転負担が大きく減ります。"),
        ("customer", "それいいですね。妻が夜勤明けに実家まで運転することあるので。あとチャイルドシート2つ並べて大人も後ろに座れますか？"),
        ("staff", "2列目キャプテンシートタイプなら、中央の通路を通って3列目にアクセスできるので、チャイルドシート2つ+大人も乗れます。安全で便利な配置です。"),
        ("customer", "完璧じゃないですか。試乗って平日でもできますか？妻が夜勤で土日合わないことあって。"),
        ("staff", "もちろんです。平日夕方以降もご対応できます。お子様連れでも大丈夫ですよ。ご都合のよい日をお知らせください。"),
    ],
    # OPP-0006 松本 あかね - 26歳OL、初めての車、予算220万上限、コンパクト希望 ★AI失敗デモ対象
    [
        ("customer", "松本です。先日はありがとうございました。家でいろいろ調べたんですけど、ヤリスクロスっていうのもかわいいなって思ったんですけど、どうですか？"),
        ("staff", "松本様、こんにちは😊 ヤリスクロスとても人気です！コンパクトSUVですが、ヤリスより少し背が高く視界も良いので運転しやすいですよ。"),
        ("customer", "ほんとですか！可愛いのとSUVは無理かと思ってたんですけど、予算内でいけます？"),
        ("staff", "中古なら2022年式・3万km程度で180-210万円くらいです。ご予算220万円の範囲で十分にお探しできますよ。"),
        ("customer", "うわ、よかった！実家の母の病院の送り迎えにも使えそうですか？荷物とか杖とか持って乗せたいんですけど。"),
        ("staff", "ヤリスクロスは後席の乗降性もよく、床も低めなので乗り降りしやすいです。お母様にも気に入っていただけると思います。"),
        ("customer", "決めました！土曜日に試乗予約したいです。白かパールホワイトみたいな色ありますか？"),
        ("staff", "ございます！プラチナホワイトパールマイカなど、松本様に似合いそうな色もご用意あります。土曜11時にお取りしますね。"),
    ],
    # OPP-0007 伊藤 正雄 - 退職後、静粛性・高級感、レクサス中古
    [
        ("customer", "伊藤です。ご連絡ありがとうございます。先日ご提案いただいたレクサスES、興味あります。中古でどのくらいありますか？"),
        ("staff", "伊藤様、ご連絡ありがとうございます。レクサスESは2019-2021年式の良質な中古車を複数ご用意できます。価格帯は280-380万円程度です。"),
        ("customer", "300万くらいでいいのがあればと思ってます。音の静かさはESが一番と思っていいですか？"),
        ("staff", "おっしゃる通りです。ESは遮音ガラスと制振材を贅沢に使用しており、高速巡航時の静粛性はトヨタ車の中でもトップクラスです。"),
        ("customer", "妻が温泉旅行行きたがってるんで、長距離で疲れないやつがいいんです。ESのシートはどうですか？"),
        ("staff", "ESは本革シート＋ベンチレーション＋ランバーサポート標準装備で、数時間の運転でも疲れが残りにくい設計です。奥様のお席も電動調整可能です。"),
        ("customer", "それは素晴らしい。一度実物を見せていただけますか？妻も連れていきます。"),
        ("staff", "ぜひお越しください。奥様にも乗り心地をご体感いただけるよう、2-3台を比較できるようご用意しますね。"),
    ],
    # OPP-0008 高橋 美穂 - カフェ経営、アウトドア、おしゃれ
    [
        ("customer", "高橋です！先日はありがとうございました😊 CX-5とハリアーで迷ってて、インスタ映えするのはどっちですか？笑"),
        ("staff", "高橋様、こんにちは！見た目のデザインは好みですが、CX-5は「魂動デザイン」で彫刻的な美しさ、ハリアーはラグジュアリーで都会的な雰囲気です。"),
        ("customer", "うーん、どっちも素敵ですよね💦 キャンプ道具とか積めるのはどちらですか？屋根にルーフボックスも考えてて。"),
        ("staff", "両車ともルーフレール装着可能です。ラゲッジ容量はCX-5が522L、ハリアーが409Lなので、キャンプ道具を多く積むならCX-5が有利です。"),
        ("customer", "CX-5の方がいいかも！お店の什器運ぶにも使うので。色はどんなのありますか？"),
        ("staff", "CX-5はソウルレッドクリスタルメタリックが有名ですが、マシーングレーやソニックシルバーも上品でおしゃれです。インスタ映え抜群です📸"),
        ("customer", "ソウルレッドいいなぁ！ご主人のデザイナー目線でも気に入ると思います。試乗予約お願いしたいです。"),
        ("staff", "ありがとうございます！土日どちらがご都合よろしいですか？ご主人様とのキャンプ計画も試乗しながらご相談できます。"),
    ],
    # OPP-0009 中島 康介 - 商社課長、走りの楽しさ、ハリアー検討
    [
        ("customer", "中島です。お世話になってます。先日のハリアーの話、気になってます。CX-5からの乗り換えで走りに不満は出ませんか？"),
        ("staff", "中島様、ご連絡ありがとうございます。正直に申し上げますと、ハンドリングの切れ味はCX-5の方が上です。ハリアーは快適性・高級感を重視した設計です。"),
        ("customer", "やっぱりそうなんですね。走り好きとしてはCX-5継続か、いっそCX-60とか考えた方がいいですか？"),
        ("staff", "CX-60は素晴らしい選択肢です。FRベースの新世代プラットフォームで、走りの質が一段上です。価格帯は400万円台ですが、中古で狙える可能性もあります。"),
        ("customer", "おお！それ気になります。娘たちのテニスバッグと楽器積んでも大丈夫ですか？"),
        ("staff", "ラゲッジ570Lで、後席も広いです。テニスラケット・楽器・ゴルフバッグも余裕です。"),
        ("customer", "いいですね。週末にCX-5とCX-60の乗り比べさせてもらえますか？"),
        ("staff", "ぜひ！ハンドリングの違いを体感いただきたいです。土曜午後で2台試乗できるようご用意します。"),
    ],
    # OPP-0010 藤田 さくら - 看護師、2歳娘、スライドドア必須
    [
        ("customer", "藤田です、こんにちは！先日はありがとうございました。フリードとシエンタで迷ってて、結局どっちがおすすめですか？🤔"),
        ("staff", "藤田様こんにちは！大前です。藤田様のご家族にはフリードをおすすめします。理由はHonda SENSINGの先進性と、2列目のゆとりです。"),
        ("customer", "フリードなんですね！なんで2列目が大事なんですか？"),
        ("staff", "2歳のお子様がチャイルドシートで前向きになる時、親御さんが横に座って世話をする場面が増えます。フリードの2列目は大人が座っても広いので、夜泣き対応などもラクです。"),
        ("customer", "確かに！今タントだと狭くて腰痛くなるんです😭 あと、2人目が生まれた時に耐えられますか？"),
        ("staff", "全く問題ありません。6人乗りタイプならチャイルドシート2つ+大人2人で余裕ですし、3列目は祖父母が来られた時に使えます。"),
        ("customer", "完璧じゃないですか！旦那も運転するので、運転しやすさもポイントですが、軽からの乗り換えで大丈夫ですか？"),
        ("staff", "フリードは全長4.3mと、普通車の中で最もコンパクトな部類です。軽より少し大きい程度なので、ご主人様もすぐ慣れていただけます。"),
        ("customer", "安心しました！試乗予約お願いできますか？夜勤明けの平日昼でも大丈夫ですか？"),
        ("staff", "もちろんです。平日はゆっくりご案内できるのでおすすめです。お子様同伴で大丈夫ですよ。"),
    ],
]

messages = []
m_counter = 0

for rec in records:
    if rec["stage"] == "リード":
        continue

    opp_id = rec["sf_opportunity_id"]
    opp_num = int(opp_id.split("-")[1])
    conv_id = f"CONV-{opp_id}"
    is_detailed = opp_num <= 10

    # 大前このみ担当の主要 10 名以外は約 40% の顧客のみ LINE 履歴あり
    if not is_detailed and random.random() > 0.4:
        continue

    base_time = datetime(2026, 3, 1) + timedelta(days=random.randint(-30, 30))

    # 大前このみ担当の主要 10 名はハードコーディング会話を使用
    if is_detailed:
        conversation = DETAILED_LINE_CONVERSATIONS[opp_num - 1]
        for j, (sender, text) in enumerate(conversation):
            m_counter += 1
            messages.append({
                "message_id": f"MSG-{m_counter:06d}",
                "sf_opportunity_id": opp_id,
                "conversation_id": conv_id,
                "sender": sender,
                "message_text": text,
                "sent_at": (base_time + timedelta(hours=j * random.randint(1, 24))).isoformat(),
            })
    else:
        n_messages = random.randint(2, 4)
        for j in range(n_messages):
            m_counter += 1
            sender = "customer" if j % 2 == 0 else "staff"
            if sender == "customer":
                text = random.choice(CUSTOMER_MSGS)
            else:
                text = random.choice(STAFF_MSGS)

            messages.append({
                "message_id": f"MSG-{m_counter:06d}",
                "sf_opportunity_id": opp_id,
                "conversation_id": conv_id,
                "sender": sender,
                "message_text": text,
                "sent_at": (base_time + timedelta(hours=j * random.randint(1, 24))).isoformat(),
            })

lm_df = spark.createDataFrame(messages)
lm_df.write.mode("overwrite").parquet(f"/Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/line_messages")
print(f"✓ line_messages: {lm_df.count():,} 件 → /Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/line_messages")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## Step 5: コールセンターログ生成（~150 件）
# MAGIC <div style="border-left: 4px solid #388E3C; background: #E8F5E9; padding: 14px 20px; border-radius: 0 8px 8px 0; margin-bottom: 16px;">
# MAGIC   <div style="font-size: 15px; font-weight: 700; color: #2E7D32;">Step 5: コールセンターログ生成（~150 件）</div>
# MAGIC </div>

# COMMAND ----------

CALL_REASONS = ["在庫確認", "価格問い合わせ", "試乗予約", "アフターサービス", "ローン相談", "納期確認"]

CALL_TEMPLATES = [
    "はい、{store}でございます。はい、{vehicle}の在庫についてですね。現在1台ございます。はい、{budget}万円前後でご案内できます。ぜひ一度ご来店ください。",
    "お電話ありがとうございます。ローンのご相談ですね。月々のお支払いは{monthly}万円程度からご利用いただけます。頭金の有無によって変わりますので、詳しくは店頭でご説明させていただきます。",
    "はい、試乗のご予約ですね。{vehicle}でよろしいでしょうか。来週の土曜日はいかがでしょうか。午前10時からでしたらご案内可能です。",
]

# ---------- 詳細コールセンターログ（大前このみ担当の主要 10 名、OPP-0001 ~ OPP-0010）----------
# 各顧客のペルソナ・ニーズに沿った具体的な問い合わせ内容
DETAILED_CALLCENTER_LOGS = [
    # OPP-0001 山田 優子 - シエンタ試乗前の確認
    {
        "reason": "試乗予約",
        "duration": 420,
        "text": "もしもし、山田と申します。先日お店でシエンタの説明を受けたんですけど、義母も一緒に試乗させてもらえますかというお電話です。はい、義母が72歳で足が少し悪いんですけど、実際に乗り降りしてみたいって言ってて。はい、子供も2人いるので一緒に行きます。日時は土曜日の10時半でお願いしたいです。あと、チャイルドシートって貸してもらえますか？ありがとうございます、助かります。では土曜日にお願いします。",
    },
    # OPP-0002 佐藤 健一 - ハリアー価格・保証
    {
        "reason": "価格問い合わせ",
        "duration": 510,
        "text": "もしもし、佐藤です。ハリアーのハイブリッドですね、2022年式くらいで走行2-3万キロの在庫で、だいたいおいくらくらいになりますかというお電話です。はい、はい、400万前後ですか。クラウンの下取りも込みで考えたいんですけど、2018年式でだいたいどのくらいでしょうか。はい、70-90万程度ですね。わかりました。あと保証の期間が気になるんですが、中古車でも2年保証つけられますか？そうですか、それは安心ですね。一度来店して現車見せてもらいます。日曜の午後に伺います。",
    },
    # OPP-0003 田中 翔太 - ローン相談
    {
        "reason": "ローン相談",
        "duration": 380,
        "text": "あ、もしもし、田中と申します。ヴェゼルの中古を検討してるんですけど、ローンの相談させてもらえますかという電話です。はい、年収は450万くらいで、社会人3年目です。頭金なしで全額ローンの場合、月々いくらくらいになりますか？180万の車体で。ああ、月2.5万くらいですか。はい、5年で考えてます。あと審査って何日くらいかかりますか？3日ですね、わかりました。彼女と一緒に来店予定なんで、土曜日くらいに申し込みしたいです。ありがとうございます。",
    },
    # OPP-0004 渡辺 雅子 - 安全装備確認
    {
        "reason": "アフターサービス",
        "duration": 600,
        "text": "お世話になります、渡辺です。レクサスNXとRXで迷っていて、安全装備について詳しく教えていただきたくお電話しました。はい、子供2人いてテニスの送迎が多いんですけど、レクサスセーフティシステム+の歩行者検知って夜間でも作動しますか？はい、暗闇でも検知できると。それから自動ブレーキの対応速度範囲は？時速5-180kmですね、すごいですね。あとブラインドスポットモニターは標準装備ですか？NXは上級グレードのみと。わかりました。主人とも相談して、RXの方向で検討します。では週末に改めて伺います。",
    },
    # OPP-0005 木村 裕二 - フリード vs シエンタ比較
    {
        "reason": "在庫確認",
        "duration": 450,
        "text": "もしもし、木村と申します。先日お邪魔しました。フリード6人乗りのHonda SENSING付きで、2022年式くらいの在庫ってありますか？はい、2台ありますか。走行距離は？3万キロと5万キロ。価格は280万と250万ですね。わかりました。妻が看護師で夜勤明けに見に来れるのが平日の昼なんですけど、平日試乗って可能ですか？はい、火曜か水曜日でお願いしたいです。子供も連れて行きます。0歳と3歳です。チャイルドシート借りれますか？ありがとうございます。では火曜の13時でお願いします。",
    },
    # OPP-0006 松本 あかね - ハリアー問い合わせ ★AI失敗デモ対象
    {
        "reason": "価格問い合わせ",
        "duration": 520,
        "text": "あ、もしもし、松本です。初めてお電話します。実は先週お店寄らせていただいた時はお店閉まってて、ネットで検索してお電話してます。えっと、ハリアーのハイブリッドって中古でいくらくらいしますか？はい、380万から450万ですか。厳しいですね。実は予算が220万が上限で、初めての車なんです。ハリアーはやっぱり無理ですよね。あ、ヴェゼルやヤリスクロスなら予算内ですか。そうですよね、それを見た方がよさそう。お店で相談に乗ってもらえますか？はい、土曜日の11時で。白い車があれば見せてください。お願いします。",
    },
    # OPP-0007 伊藤 正雄 - レクサスES静粛性確認
    {
        "reason": "在庫確認",
        "duration": 380,
        "text": "もしもし、伊藤と申します。先日お世話になりました。レクサスESの中古在庫の件で確認したくお電話しました。はい、2019年から2020年式で、価格帯280-320万くらいで探してます。はい、何台くらいありますか？3台ですか。走行距離はどのくらいですか？2-4万キロ。本革シートは全部装備されてますよね？はい、よかった。妻と温泉旅行よく行くので、静粛性と乗り心地最優先です。あと年配だと運転支援機能が最新のほうが安心ですよね？はい、レクサスセーフティシステム+A搭載と。わかりました。来週火曜の午後に妻と見に行きます。よろしくお願いします。",
    },
    # OPP-0008 高橋 美穂 - CX-5カラー指定
    {
        "reason": "在庫確認",
        "duration": 410,
        "text": "もしもし、高橋と申します！CX-5のソウルレッドクリスタルメタリックの在庫ありますか？はい、1台あるんですね、2021年式で4万キロ、310万円。ちょっと予算オーバーかも...2020年式でも大丈夫ですが、同じ色の在庫ありますか？あー、現在は赤がなくて、マシーングレーかソニックシルバーなら。うーん、ご主人がデザイナーなんで色こだわりたいんですよね。入荷予定とかってわかりますか？2週間後くらいの可能性。じゃあその時にまた電話します！ルーフレールつきのを特に探してるので、入荷したら連絡ください。お願いします！",
    },
    # OPP-0009 中島 康介 - CX-60試乗予約
    {
        "reason": "試乗予約",
        "duration": 350,
        "text": "もしもし、中島と申します。先日シゲル様からご案内いただいた件でお電話です。CX-60とCX-5の試乗を同時にしたいのですが、予約できますか？はい、土曜日の午後で、走りの違いを体感したいので、できれば高速乗れるルートも含めて。ああ、試乗コース決まってるんですね、承知しました。時間は14時からでお願いします。あとCX-60の中古在庫って今何台ありますか？1台ですか、2023年式で420万。思ったより高いな...。3年落ちとかで値段下がってくるのを待った方がいいかもしれませんね。では土曜日よろしくお願いします。",
    },
    # OPP-0010 藤田 さくら - フリード納期
    {
        "reason": "納期確認",
        "duration": 390,
        "text": "もしもし、藤田です、お世話になります！フリードの6人乗り、Honda SENSING付きを契約するとしたら、納期ってどのくらいかかりますか？はい、中古在庫があればすぐと。在庫車で2022年式・走行3万キロ・230万くらいのってありますか？あ、色がホワイトパールならあるんですね！それでお願いしたいです。正式契約は週末で大丈夫ですか？夫と一緒に来店します。はい、娘も連れていきます。2歳なんでチャイルドシートつけたまま試乗確認したいんですけど、大丈夫ですか？ありがとうございます、安心しました。では土曜の14時でお願いします！",
    },
]

logs = []
c_counter = 0

# まず大前このみ担当の主要 10 名は必ず詳細ログを生成
for rec in records:
    opp_id = rec["sf_opportunity_id"]
    opp_num = int(opp_id.split("-")[1])
    if opp_num > 10:
        continue
    c_counter += 1
    detail = DETAILED_CALLCENTER_LOGS[opp_num - 1]
    logs.append({
        "call_id": f"CALL-{c_counter:04d}",
        "sf_opportunity_id": opp_id,
        "call_date": (date(2026, 2, 1) + timedelta(days=random.randint(0, 60))).isoformat(),
        "duration_seconds": detail["duration"],
        "call_reason": detail["reason"],
        "transcript_text": detail["text"],
        "created_at": datetime.now().isoformat(),
    })

# それ以外の顧客はランダムサンプリング（約 12%）＋テンプレート
for rec in records:
    opp_id = rec["sf_opportunity_id"]
    opp_num = int(opp_id.split("-")[1])
    if opp_num <= 10:
        continue
    if random.random() > 0.12:
        continue

    c_counter += 1
    region = PREF_TO_REGION.get(rec["prefecture"], "関東")
    store = random.choice(STORES[region])

    tmpl = random.choice(CALL_TEMPLATES)
    text = tmpl.format(
        store=store,
        vehicle=random.choice(["シエンタ", "ハリアー", "ヴェゼル", "フリード", "プリウス"]),
        budget=rec["budget"] // 10000,
        monthly=rec["budget"] // 10000 // 60,
    )

    logs.append({
        "call_id": f"CALL-{c_counter:04d}",
        "sf_opportunity_id": opp_id,
        "call_date": (date(2026, 2, 1) + timedelta(days=random.randint(0, 60))).isoformat(),
        "duration_seconds": random.randint(60, 600),
        "call_reason": random.choice(CALL_REASONS),
        "transcript_text": text,
        "created_at": datetime.now().isoformat(),
    })

cc_df = spark.createDataFrame(logs)
cc_df.write.mode("overwrite").parquet(f"/Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/callcenter_logs")
print(f"✓ callcenter_logs: {cc_df.count():,} 件 → /Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/callcenter_logs")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## Step 6: 車両画像コピー
# MAGIC <div style="border-left: 4px solid #388E3C; background: #E8F5E9; padding: 14px 20px; border-radius: 0 8px 8px 0; margin-bottom: 16px;">
# MAGIC   <div style="font-size: 15px; font-weight: 700; color: #2E7D32;">Step 6: 車両画像コピー</div>
# MAGIC </div>

# COMMAND ----------

import os
import shutil

notebook_dir = os.path.dirname(
    dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
)
workspace_images_path = f"/Workspace{notebook_dir}/_images"

required_images = [
    "sienta.jpg", "freed.jpg", "voxy.jpg", "alphard.jpg", "harrier.jpg",
    "vezel.jpg", "prius.jpg", "nbox.jpg", "lexus_rx.jpg", "volvo_xc60.jpg",
]

os.makedirs(f"/Volumes/{catalog_name}/{schema_name}/{VOLUME_NAME}", exist_ok=True)

copied = 0
for img in required_images:
    src = f"{workspace_images_path}/{img}"
    dst = f"/Volumes/{catalog_name}/{schema_name}/{VOLUME_NAME}/{img}"
    try:
        shutil.copy2(src, dst)
        print(f"  ✓ {img}")
        copied += 1
    except Exception as e:
        print(f"  ✗ {img}: {str(e)[:80]}")

print(f"\n画像コピー: {copied}/{len(required_images)} 件完了")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC ## Step 7: ナレッジアシスタント用テキストファイル生成
# MAGIC <div style="border-left: 4px solid #388E3C; background: #E8F5E9; padding: 14px 20px; border-radius: 0 8px 8px 0; margin-bottom: 16px;">
# MAGIC   <div style="font-size: 15px; font-weight: 700; color: #2E7D32;">Step 7: ナレッジアシスタント用テキストファイル生成</div>
# MAGIC   <div style="font-size: 13px; color: #555; margin-top: 4px;">Agent Bricks ナレッジアシスタントが参照するテキストファイルを Volume に書き出します。</div>
# MAGIC </div>

# COMMAND ----------

vehicle_specs = """# 取扱い車両 スペックサマリー

## トヨタ ハリアー（2022年式）
- ボディタイプ：プレミアムSUV / 5人乗り
- 燃料：ガソリン
- 価格帯：350万円〜
- 走行距離：35,000km
- 主な装備：Toyota Safety Sense、JBLサウンド、ムーンルーフ、パノラミックビュー
- 強み：上質な内装、ゴルフバッグ2個以上搭載可能、都市型SUVとしてのスタイリッシュさ
- 燃費：約15km/L（WLTCモード）

## トヨタ シエンタ（2023年式）
- ボディタイプ：コンパクトミニバン / 7人乗り
- 燃料：ハイブリッド
- 価格帯：220万円〜
- 走行距離：12,000km
- 主な装備：Toyota Safety Sense（衝突回避・車線逸脱・先行車発進告知）、両側電動スライドドア、低床設計
- 強み：乗り降りしやすい低床、狭い場所でも扱いやすいコンパクトサイズ、3列シートで家族送迎に最適
- 燃費：約28km/L（WLTCモード）

## ホンダ フリード（2022年式）
- ボディタイプ：コンパクトミニバン / 6人乗り
- 燃料：ハイブリッド（e:HEV）
- 価格帯：240万円〜
- 走行距離：20,000km
- 主な装備：Honda SENSING（衝突軽減ブレーキ・誤発進抑制・後方誤発進抑制）、e:HEV
- 強み：シエンタより小回りが利く、維持費が安い、普段使いしやすいサイズ
- 燃費：約27km/L（WLTCモード）

## トヨタ ヴォクシー（2023年式）
- ボディタイプ：ミニバン / 7人乗り
- 燃料：ハイブリッド
- 価格帯：320万円〜
- 走行距離：8,000km
- 主な装備：Toyota Safety Sense、両側パワースライドドア、ワンタッチスイッチ付パワーバックドア
- 強み：広々とした室内空間、ファミリー層に圧倒的人気、シエンタより大きな3列目シート
- 燃費：約23km/L（WLTCモード）

## トヨタ アルファード（2022年式）
- ボディタイプ：大型ミニバン / 7人乗り
- 燃料：ハイブリッド
- 価格帯：550万円〜
- 走行距離：25,000km
- 主な装備：Toyota Safety Sense、JBLサウンド、本革シート、ツインムーンルーフ
- 強み：圧倒的な室内空間と高級感、VIPの送迎にも使われるプレミアムモデル
- 燃費：約15km/L（WLTCモード）

## ホンダ ヴェゼル（2023年式）
- ボディタイプ：コンパクトSUV / 5人乗り
- 燃料：ハイブリッド（e:HEV）
- 価格帯：280万円〜
- 走行距離：15,000km
- 主な装備：Honda SENSING、9インチナビ、後席テーブル
- 強み：スタイリッシュなデザイン、使い勝手の良いラゲッジ、初めてのSUVに最適
- 燃費：約26km/L（WLTCモード）

## トヨタ プリウス（2023年式）
- ボディタイプ：セダン / 5人乗り
- 燃料：ハイブリッド
- 価格帯：320万円〜
- 走行距離：5,000km
- 主な装備：Toyota Safety Sense、パノラマルーフ、新世代デザイン
- 強み：業界最高水準の燃費、一新されたスタイリッシュなデザイン、低燃費で維持費が安い
- 燃費：約33km/L（WLTCモード）

## ホンダ N-BOX（2023年式）
- ボディタイプ：軽自動車 / 4人乗り
- 燃料：ガソリン
- 価格帯：180万円〜
- 走行距離：10,000km
- 主な装備：Honda SENSING、電動スライドドア、助手席スーパースライドシート
- 強み：軽自動車販売台数No.1、広い室内空間、日常使いに便利なスライドドア
- 燃費：約21km/L（WLTCモード）

## レクサス RX（2022年式）
- ボディタイプ：プレミアムSUV / 5人乗り
- 燃料：ハイブリッド
- 価格帯：650万円〜
- 走行距離：18,000km
- 主な装備：Lexus Safety System+、マークレビンソンプレミアムサウンド、本革シート
- 強み：レクサスブランドの最先端安全装備、圧倒的な静粛性、ステータスと実用性を両立
- 燃費：約19km/L（WLTCモード）
"""

car_finance = """# 自動車維持費・ローン・保険 基礎知識

## 年間維持費の目安（普通車）

| 費用項目 | ガソリン車 | ハイブリッド車 | 備考 |
| 自動車税 | 3〜4万円/年 | 同左 | 排気量によって異なる |
| 自賠責保険 | 約1.7万円/年 | 同左 | 法定費用 |
| 任意保険 | 5〜15万円/年 | 同左 | 年齢・等級・車種による |
| 車検費用 | 8〜12万円/2年 | 同左 | 法定費用＋整備費 |
| ガソリン代 | 12〜18万円/年 | 7〜11万円/年 | 月1,000km走行の場合 |
| 駐車場代 | 地域による | 同左 | 都市部：月2〜5万円 |
| **合計目安** | **約30〜50万円/年** | **約25〜40万円/年** | |

## ハイブリッド vs ガソリン 燃費コスト比較（5年間）

| | ガソリン車（15km/L） | ハイブリッド（25km/L） |
| 燃料代（5年・6万km） | 約55万円 | 約33万円 |
| 差額 | — | 約22万円お得 |
| ハイブリッド車価格差 | — | 20〜40万円高い |
| 結論 | | 5〜7年で元が取れる |

## 購入方法の比較

### 現金一括
- メリット：金利ゼロ、車が完全に自分のもの
- デメリット：まとまった資金が必要
- 向いている人：手元資金がある、長期保有予定

### オートローン（銀行系）
- 金利：年1〜3%（銀行系）
- メリット：低金利
- デメリット：審査に時間がかかる
- 月々の支払い目安：200万円・5年・2%→約3.5万円/月

### 残価設定型クレジット（残クレ）
- 金利：年3〜7%（ディーラー系）
- メリット：月々の支払いを抑えられる、一定期間後に乗り換えやすい
- デメリット：金利が高め、走行距離・傷の制限あり、残価払いが別途必要
- 月々の支払い目安：300万円・3年・残価40%→約4.5万円/月

### リース（カーリース）
- メリット：車検・税金込みで月額一定、初期費用ゼロ
- デメリット：車が自分のものにならない、カスタム不可
- 月額目安：200万円相当の車→月3〜5万円

## 任意保険のポイント
- 初めての購入者は「等級6S」スタートで割引なし → 年間保険料が高め
- 20代：年間15〜20万円が相場（車種・補償内容による）
- 30〜40代（等級が上がった場合）：年間5〜10万円が相場
- ハイブリッド車は保険料がやや高め（修理費が高いため）

## 下取り・買取について
- ディーラー下取り：手間がかからないが査定額が低め
- 一括査定（カービュー等）：競合させることで10〜30万円高くなることも
- 現在の車の走行距離・年式・状態が査定額に大きく影響
"""

sales_playbook = """# 営業トーク集・商談ガイド

## 初回商談の進め方

### ステップ1：ニーズヒアリング（10分）
必ず確認する項目：
- 現在の車：何年乗っている？走行距離は？不満は？
- 家族構成：何人乗りが必要？高齢者・子どもはいる？
- 主な用途：毎日の通勤？週末のお出かけ？遠距離？
- 予算：月々いくらまで？総額で考えている？
- こだわり：安全性？燃費？見た目？ブランド？

### ステップ2：候補絞り込み（10分）
- 予算と用途から2〜3台に絞る
- 「この3台がお客様のご状況に一番合うと思います」と宣言してから説明
- なぜその3台なのか、理由を顧客の言葉を使って説明する

### ステップ3：比較提案（15分）
- 第1位：一番のおすすめを明確にする（「私が一番推す理由は〜」）
- 第2位・第3位：第1位との違いを一言で整理
- 「どれが気になりましたか？」と顧客の反応を確認

### ステップ4：試乗誘導（5分）
試乗への誘導トーク例：
「スペックの話は画面で見るより、実際に乗ってみると全然違います。
お時間30分いただければ、今日このまま試乗していただけますよ。いかがですか？」

### ステップ5：クロージング
- 試乗後：「今日乗ってみていかがでしたか？」から入る
- 迷っている場合：「どの点が気になっていますか？」と絞り込む
- 次のアクションを明確に：「次回、見積もりを出しますね」「ご家族にも見せてあげたいですね」


## よくある顧客タイプ別アプローチ

### ファミリー層（子育て中）
- 重視点：安全装備・乗り降りしやすさ・積載量
- おすすめ車種：シエンタ、フリード、ヴォクシー
- トーク軸：「お子様の送迎に毎日使うなら〜」「習い事の帰りに荷物が多くても〜」
- 刺さるポイント：Toyota Safety Sense・Honda SENSINGの具体的な機能説明

### シニア・高齢者同乗
- 重視点：低床設計・乗り降りしやすさ・視界の良さ
- おすすめ車種：シエンタ、フリード
- トーク軸：「お義母様が乗り降りしやすいのは〜」「病院への送迎でも〜」
- 刺さるポイント：シエンタの低床・手すり・両側電動スライドドア

### ビジネスマン（格・ステータス重視）
- 重視点：見た目・ブランド・走行性能
- おすすめ車種：ハリアー、レクサス RX、アルファード
- トーク軸：「取引先へのご移動でも〜」「週末のゴルフでも〜」
- 刺さるポイント：内装の質感・積載量・維持費とのバランス

### 若者・初めての購入
- 重視点：デザイン・友人の評価・コスパ
- おすすめ車種：ヴェゼル、N-BOX、プリウス
- トーク軸：「見た目がカッコいいのはもちろん〜」「実用性も抜群で〜」
- 刺さるポイント：SUVのスタイル・安全装備・燃費


## NGトーク・注意事項
- 「この車はお客様には合わないと思いますよ」→ まず用途を確認してから提案する
- 「安いモデルでいいんじゃないですか？」→ 予算はあくまで顧客が決める
- 断定的な「これしかない」→ 必ず選択肢を2〜3用意する
- 顧客の名前は苗字+様（例：渡辺様）、下の名前で呼ばない
"""

# COMMAND ----------

import os

knowledge_base = f"/Volumes/{catalog_name}/{schema_name}/{KNOWLEDGE_VOLUME_NAME}"

files = {
    f"{knowledge_base}/catalogs/vehicle_specs_summary.txt": vehicle_specs,
    f"{knowledge_base}/finance/car_finance_guide.txt":      car_finance,
    f"{knowledge_base}/sales/sales_playbook.txt":           sales_playbook,
}

for path, content in files.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  ✓ {path}")

print(f"\n✓ ナレッジアシスタント用テキストファイル生成完了（{len(files)} ファイル）")

# COMMAND ----------

# MAGIC %md-sandbox
# MAGIC <div style="border-left: 4px solid #1976d2; background: #e3f2fd; padding: 14px 20px; border-radius: 0 8px 8px 0; margin-bottom: 16px;">
# MAGIC   <div style="font-size: 15px; font-weight: 700; color: #1565c0;">データ生成結果サマリー</div>
# MAGIC </div>

# COMMAND ----------

print("=" * 60)
print("  デモデータ生成 完了")
print("=" * 60)

datasets = [
    ("sf_opportunities",  "SFDC 商談データ"),
    ("web_browsing_events",  "Web 閲覧行動ログ"),
    ("visit_transcripts", "来店文字起こし"),
    ("line_messages",     "LINE メッセージ"),
    ("callcenter_logs",   "コールセンターログ"),
]

for folder, label in datasets:
    try:
        df = spark.read.parquet(f"/Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/{folder}")
        print(f"  ✓ {label:<20s} : {df.count():>6,} 件")
    except Exception as e:
        print(f"  ✗ {label:<20s} : エラー - {str(e)[:50]}")

print("=" * 60)
print(f"  保存先: /Volumes/{catalog_name}/{schema_name}/{RAW_VOLUME_NAME}/")
print("=" * 60)
