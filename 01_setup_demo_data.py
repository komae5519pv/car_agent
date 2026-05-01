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

import json
import os
import random
from datetime import date, datetime, timedelta

random.seed(42)

# ---------- 営業担当者 10名 ----------
SALES_REPS = [
    ("REP-001", SALES_REP_NAME, SALES_REP_EMAIL),
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

# ---------- 詳細インタラクションデータ（setup/demo_interactions_data.json から読込）----------
# デモ主役 10 名（OPP-0001 〜 OPP-0010）の商談録音・LINE会話・コールセンターログを
# 外部 JSON から読み込み、各 Step で参照するリストを構築します。
# JSON を編集することでコード本体を触らずに台本内容を更新できます。
_interact_json_candidates = [
    # Workspace / Job 実行時
    f"/Workspace{os.path.dirname(dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())}/setup/demo_interactions_data.json",
    # ローカル開発時
    "setup/demo_interactions_data.json",
]
_interact_raw = None
for _p in _interact_json_candidates:
    try:
        with open(_p, encoding='utf-8') as _f:
            _interact_raw = json.load(_f)
            print(f"✓ インタラクションデータ読込: {_p}")
            break
    except Exception:
        continue
if _interact_raw is None:
    raise RuntimeError("setup/demo_interactions_data.json が見つかりません。リポジトリ同期を確認してください。")

_interact_by_opp = _interact_raw["interactions_by_opp"]

# SALES_REP_NAME の苗字を抽出して staff 自己紹介のプレースホルダを置換
# 例: SALES_REP_NAME = "大前 このみ" → STAFF_SURNAME = "大前"
#     SALES_REP_NAME = "加藤" (苗字のみ) → STAFF_SURNAME = "加藤"
# LINE メッセージ内の "{STAFF_SURNAME}です" が置き換わる
STAFF_SURNAME = SALES_REP_NAME.strip().split()[0] if SALES_REP_NAME else "担当"
print(f"  Staff surname (for LINE self-intro): {STAFF_SURNAME}")

DETAILED_TRANSCRIPTS = [
    _interact_by_opp[f"OPP-{i+1:04d}"]["transcript_text"].replace("{STAFF_SURNAME}", STAFF_SURNAME)
    for i in range(10)
]
DETAILED_LINE_CONVERSATIONS = [
    [(m["sender"], m["text"].replace("{STAFF_SURNAME}", STAFF_SURNAME))
     for m in _interact_by_opp[f"OPP-{i+1:04d}"]["line_messages"]]
    for i in range(10)
]
DETAILED_CALLCENTER_LOGS = [
    {
        "reason": _interact_by_opp[f"OPP-{i+1:04d}"]["callcenter_log"]["reason"],
        "duration": _interact_by_opp[f"OPP-{i+1:04d}"]["callcenter_log"]["duration_seconds"],
        "text": _interact_by_opp[f"OPP-{i+1:04d}"]["callcenter_log"]["transcript_text"].replace("{STAFF_SURNAME}", STAFF_SURNAME),
    }
    for i in range(10)
]
print(f"  transcripts={len(DETAILED_TRANSCRIPTS)}, line_conversations={len(DETAILED_LINE_CONVERSATIONS)}, callcenter_logs={len(DETAILED_CALLCENTER_LOGS)}")

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
        "sales_rep_email": SALES_REP_EMAIL,
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
# DETAILED_TRANSCRIPTS は setup/demo_interactions_data.json から読み込み済み（冒頭のローダーセル参照）

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

# DETAILED_LINE_CONVERSATIONS は setup/demo_interactions_data.json から読み込み済み（冒頭のローダーセル参照）

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
        cumulative_minutes = 0  # 累積時間。メッセージ順序を必ず保つ
        for j, (sender, text) in enumerate(conversation):
            # 返信は 5 分〜3 時間後（単調増加）
            cumulative_minutes += random.randint(5, 180)
            m_counter += 1
            messages.append({
                "message_id": f"MSG-{m_counter:06d}",
                "sf_opportunity_id": opp_id,
                "conversation_id": conv_id,
                "sender": sender,
                "message_text": text,
                "sent_at": (base_time + timedelta(minutes=cumulative_minutes)).isoformat(),
            })
    else:
        n_messages = random.randint(2, 4)
        cumulative_minutes = 0
        for j in range(n_messages):
            cumulative_minutes += random.randint(30, 24 * 60)  # 30分〜24時間
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
                "sent_at": (base_time + timedelta(minutes=cumulative_minutes)).isoformat(),
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

# DETAILED_CALLCENTER_LOGS は setup/demo_interactions_data.json から読み込み済み（冒頭のローダーセル参照）

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
