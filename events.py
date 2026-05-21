"""事件系統 - 隨機人生事件 + 觸發邏輯

事件格式:
{
    "id": 唯一識別碼,
    "name": 顯示名稱,
    "category": 類別 (意外/感情/職場/家庭/幸運/健康),
    "weight": 基礎權重 (越高越常發生),
    "min_age": 最小年齡 (歲),
    "max_age": 最大年齡 (歲),
    "once_only": 是否一輩子只能觸發一次,
    "text": 事件描述,
    "choices": 選項列表,
}

選項格式:
{
    "text": 選項文字,
    "requires": 觸發條件 (例: 現金>=30000),
    "effects": 後果 (現金/技能/心情/旗標變化, 或 force_sell),
}
"""

EVENTS = [
    # ============ 意外類 ============
    {
        "id": "motor_accident",
        "name": "機車車禍",
        "category": "意外",
        "weight": 3,
        "min_age": 22, "max_age": 50,
        "once_only": False,
        "text": "下班途中,你騎機車被汽車追撞。雖然沒大礙,但要付醫藥費跟修車費,共需 $35,000。",
        "choices": [
            {
                "text": "用現金支付",
                "requires": {"cash_min": 35000},
                "effects": {"cash": -35000, "mood": -5, "health": -10},
            },
            {
                "text": "賣股票支付",
                "effects": {"force_sell": 35000, "mood": -10, "health": -10},
            },
            {
                "text": "向家人借錢 (社交 -8)",
                "effects": {"cash": -35000, "social": -8, "mood": -5, "health": -10},
            },
        ],
    },
    {
        "id": "phone_broken",
        "name": "手機摔壞",
        "category": "意外",
        "weight": 5,
        "min_age": 20, "max_age": 60,
        "once_only": False,
        "text": "你的手機從口袋滑出來摔壞了,需要換新機。",
        "choices": [
            {
                "text": "買旗艦機 $35,000",
                "requires": {"cash_min": 35000},
                "effects": {"cash": -35000, "mood": +5},
            },
            {
                "text": "買中階機 $15,000",
                "requires": {"cash_min": 15000},
                "effects": {"cash": -15000, "mood": -2},
            },
            {
                "text": "找二手機 $5,000",
                "requires": {"cash_min": 5000},
                "effects": {"cash": -5000, "mood": -8},
            },
        ],
    },
    {
        "id": "appliance_broken",
        "name": "家電壞掉",
        "category": "意外",
        "weight": 4,
        "min_age": 22, "max_age": 70,
        "once_only": False,
        "text": "你的冷氣 (或冰箱) 突然故障,夏天沒這個會生病的。",
        "choices": [
            {
                "text": "買新的 $25,000",
                "requires": {"cash_min": 25000},
                "effects": {"cash": -25000},
            },
            {
                "text": "修舊的 $8,000",
                "requires": {"cash_min": 8000},
                "effects": {"cash": -8000, "mood": -3, "flag_set": "appliance_old"},
            },
            {
                "text": "撐著不買",
                "effects": {"mood": -10, "health": -5},
            },
        ],
    },
    
    # ============ 健康類 ============
    {
        "id": "back_pain",
        "name": "嚴重背痛",
        "category": "健康",
        "weight": 3,
        "min_age": 25, "max_age": 60,
        "once_only": False,
        "text": "長期坐辦公室讓你下背疼痛難忍,需要去看醫生與物理治療。",
        "choices": [
            {
                "text": "完整療程 $15,000 (健康 +15)",
                "requires": {"cash_min": 15000},
                "effects": {"cash": -15000, "health": +15},
            },
            {
                "text": "只看一次門診 $2,000",
                "requires": {"cash_min": 2000},
                "effects": {"cash": -2000, "health": +3},
            },
            {
                "text": "忍著繼續工作",
                "effects": {"health": -15, "mood": -10},
            },
        ],
    },
    {
        "id": "eye_strain",
        "name": "眼睛出問題",
        "category": "健康",
        "weight": 2,
        "min_age": 25, "max_age": 55,
        "once_only": False,
        "text": "盯著螢幕太久,眼睛出現乾澀和視力模糊。需要配新眼鏡或看眼科。",
        "choices": [
            {
                "text": "配新眼鏡 + 看眼科 $12,000",
                "requires": {"cash_min": 12000},
                "effects": {"cash": -12000, "health": +5},
            },
            {
                "text": "只買眼藥水 $500",
                "effects": {"cash": -500, "health": -3},
            },
        ],
    },
    {
        "id": "serious_illness",
        "name": "親人重病",
        "category": "健康",
        "weight": 1,
        "min_age": 28, "max_age": 60,
        "once_only": True,
        "text": "媽媽 (或爸爸) 突然檢查出重病,需要你出錢協助醫療。家人開口要 $200,000。",
        "choices": [
            {
                "text": "全額支援 $200,000",
                "requires": {"cash_min": 200000},
                "effects": {"cash": -200000, "social": +15, "mood": -10},
            },
            {
                "text": "賣股票支援",
                "effects": {"force_sell": 200000, "social": +15, "mood": -15},
            },
            {
                "text": "只能拿 $50,000 (家人失望)",
                "requires": {"cash_min": 50000},
                "effects": {"cash": -50000, "social": -20, "mood": -20},
            },
        ],
    },
    
    # ============ 感情類 ============
    {
        "id": "dating_start",
        "name": "開始交往",
        "category": "感情",
        "weight": 2,
        "min_age": 22, "max_age": 38,
        "once_only": False,
        "text": "你跟一個對象越走越近,對方暗示想交往。要展開新戀情嗎?",
        "choices": [
            {
                "text": "在一起 (心情 +20, 每月多花 $5,000)",
                "effects": {"mood": +20, "flag_set": "dating", "expense_change": +5000},
            },
            {
                "text": "保持距離 (心情 -5)",
                "effects": {"mood": -5},
            },
        ],
    },
    {
        "id": "anniversary",
        "name": "紀念日",
        "category": "感情",
        "weight": 4,
        "min_age": 22, "max_age": 45,
        "once_only": False,
        "required_flag": "dating",
        "text": "情人/紀念日到了,該送什麼禮物?",
        "choices": [
            {
                "text": "精心禮物 $20,000",
                "requires": {"cash_min": 20000},
                "effects": {"cash": -20000, "mood": +15},
            },
            {
                "text": "簡單晚餐 $3,000",
                "effects": {"cash": -3000, "mood": +3},
            },
            {
                "text": "忘記了 (戀情 -10)",
                "effects": {"mood": -15, "flag_set": "relationship_warning"},
            },
        ],
    },
    {
        "id": "marriage",
        "name": "求婚與結婚",
        "category": "感情",
        "weight": 1,
        "min_age": 26, "max_age": 40,
        "once_only": True,
        "required_flag": "dating",
        "text": "交往多年的伴侶開始討論結婚。婚禮基本費用約 $500,000,還有蜜月、聘金。",
        "choices": [
            {
                "text": "盛大婚禮 $700,000",
                "requires": {"cash_min": 700000},
                "effects": {"cash": -700000, "mood": +25, "flag_set": "married"},
            },
            {
                "text": "簡單公證 $50,000",
                "requires": {"cash_min": 50000},
                "effects": {"cash": -50000, "mood": +10, "flag_set": "married"},
            },
            {
                "text": "賣股票辦婚禮 $500,000",
                "effects": {"force_sell": 500000, "mood": +20, "flag_set": "married"},
            },
            {
                "text": "再拖一陣子",
                "effects": {"mood": -10, "flag_set": "relationship_warning"},
            },
        ],
    },
    {
        "id": "breakup",
        "name": "感情生變",
        "category": "感情",
        "weight": 3,
        "min_age": 22, "max_age": 45,
        "once_only": False,
        "required_flag": "relationship_warning",
        "text": "你最近忽略了感情,對方提出分手。要挽回嗎?",
        "choices": [
            {
                "text": "盡力挽回 $30,000",
                "requires": {"cash_min": 30000},
                "effects": {"cash": -30000, "mood": -10, "flag_clear": "relationship_warning"},
            },
            {
                "text": "接受分手",
                "effects": {"mood": -25, "flag_clear": "dating", "flag_clear": "relationship_warning", "expense_change": -5000},
            },
        ],
    },
    
    # ============ 家庭類 ============
    {
        "id": "have_baby",
        "name": "懷孕了",
        "category": "家庭",
        "weight": 2,
        "min_age": 28, "max_age": 42,
        "once_only": True,
        "required_flag": "married",
        "text": "你太太/你懷孕了!生產、坐月子、嬰兒用品要 $300,000,之後每月還要多 $15,000 育兒費。",
        "choices": [
            {
                "text": "迎接新生命 $300,000",
                "requires": {"cash_min": 300000},
                "effects": {"cash": -300000, "mood": +30, "flag_set": "has_child", "expense_change": +15000},
            },
            {
                "text": "賣股票準備 $300,000",
                "effects": {"force_sell": 300000, "mood": +25, "flag_set": "has_child", "expense_change": +15000},
            },
        ],
    },
    {
        "id": "parents_retirement",
        "name": "父母退休要孝親費",
        "category": "家庭",
        "weight": 2,
        "min_age": 30, "max_age": 55,
        "once_only": True,
        "text": "父母即將退休,希望你每個月給 $10,000 孝親費。",
        "choices": [
            {
                "text": "答應 (每月 -$10,000, 社交 +15)",
                "effects": {"social": +15, "mood": +5, "expense_change": +10000},
            },
            {
                "text": "答應一半 (每月 -$5,000)",
                "effects": {"social": +5, "expense_change": +5000},
            },
            {
                "text": "婉拒 (社交 -20)",
                "effects": {"social": -20, "mood": -15},
            },
        ],
    },
    {
        "id": "buy_house",
        "name": "看中一間房",
        "category": "家庭",
        "weight": 1,
        "min_age": 30, "max_age": 45,
        "once_only": True,
        "text": "你看中一間房,頭期款需要 $1,500,000。買了之後房貸每月 $20,000 (但不再付房租)。",
        "choices": [
            {
                "text": "用現金 + 賣股票買 (要 $1.5M)",
                "effects": {"force_sell": 1500000, "mood": +25, "flag_set": "has_house", "expense_change": +20000 - 18000},  # 房貸 - 不用付房租
            },
            {
                "text": "再等等",
                "effects": {"mood": -5},
            },
        ],
    },
    
    # ============ 職場類 ============
    {
        "id": "year_end_bonus",
        "name": "年終獎金",
        "category": "職場",
        "weight": 1,  # 一年一次,在每年 1 月固定發放
        "min_age": 22, "max_age": 65,
        "once_only": False,
        "text": "公司發年終獎金了!",
        "choices": [
            {
                "text": "領取 (+ 2 個月薪水)",
                "effects": {"cash_multiplier_salary": 2, "mood": +15},
            },
        ],
    },
    {
        "id": "tech_layoff",
        "name": "公司裁員",
        "category": "職場",
        "weight": 2,
        "min_age": 25, "max_age": 55,
        "once_only": False,
        "text": "公司營運不佳,你被裁員了。資遣費 = 月薪 x 2,但要重新找工作。",
        "choices": [
            {
                "text": "領資遣費,休息找工作 (3 個月無薪)",
                "effects": {"cash_multiplier_salary": 2, "flag_set": "unemployed_3m", "mood": -25, "skill": +5},
            },
            {
                "text": "趕快接過勞低薪工作 (薪水 -30%)",
                "effects": {"cash_multiplier_salary": 2, "salary_multiplier": 0.7, "mood": -15, "health": -10},
            },
        ],
    },
    {
        "id": "promotion",
        "name": "升職機會",
        "category": "職場",
        "weight": 3,
        "min_age": 25, "max_age": 55,
        "once_only": False,
        "required_skill": 65,  # 技能要 65 以上
        "text": "主管考慮升你做小主管,薪水會多 25%,但工作壓力會增加。",
        "choices": [
            {
                "text": "接下挑戰",
                "effects": {"salary_multiplier": 1.25, "mood": +15, "health": -8, "skill": +5},
            },
            {
                "text": "婉拒",
                "effects": {"mood": -5},
            },
        ],
    },
    {
        "id": "side_project",
        "name": "接副業機會",
        "category": "職場",
        "weight": 3,
        "min_age": 22, "max_age": 50,
        "once_only": False,
        "required_skill": 50,
        "text": "朋友介紹你接一個副業專案,做完可拿 $80,000,但會佔用個人時間。",
        "choices": [
            {
                "text": "接 (+$80,000, 健康 -10, 心情 -5)",
                "effects": {"cash": +80000, "health": -10, "mood": -5, "skill": +3},
            },
            {
                "text": "不接",
                "effects": {},
            },
        ],
    },
    
    # ============ 幸運類 ============
    {
        "id": "lottery_small",
        "name": "中發票獎金",
        "category": "幸運",
        "weight": 3,
        "min_age": 18, "max_age": 80,
        "once_only": False,
        "text": "對發票中了 $4,000!",
        "choices": [
            {
                "text": "收下",
                "effects": {"cash": +4000, "mood": +5},
            },
        ],
    },
    {
        "id": "lottery_big",
        "name": "中大獎",
        "category": "幸運",
        "weight": 1,
        "min_age": 18, "max_age": 80,
        "once_only": False,
        "text": "你買的彩券中了 $200,000!",
        "choices": [
            {
                "text": "全部存起來",
                "effects": {"cash": +200000, "mood": +25},
            },
            {
                "text": "All in 股票 (買 0050)",
                "effects": {"cash": +200000, "mood": +30, "auto_buy": ("0050", 200000)},
            },
        ],
    },
    {
        "id": "tax_refund",
        "name": "退稅",
        "category": "幸運",
        "weight": 2,
        "min_age": 22, "max_age": 65,
        "once_only": False,
        "text": "你收到退稅 $15,000!",
        "choices": [
            {
                "text": "收下",
                "effects": {"cash": +15000, "mood": +8},
            },
        ],
    },
    {
        "id": "inheritance",
        "name": "意外遺產",
        "category": "幸運",
        "weight": 0.3,
        "min_age": 35, "max_age": 60,
        "once_only": True,
        "text": "遠房親戚過世,留給你一筆遺產 $500,000。",
        "choices": [
            {
                "text": "收下",
                "effects": {"cash": +500000, "mood": +10},
            },
        ],
    },
    
    # ============ 詐騙/陷阱類 ============
    {
        "id": "investment_scam",
        "name": "投資詐騙",
        "category": "陷阱",
        "weight": 2,
        "min_age": 22, "max_age": 60,
        "once_only": False,
        "text": "朋友介紹你一個「保證年化 30%」的投資機會,只要先付 $100,000...",
        "choices": [
            {
                "text": "我才不信 (心情 +3)",
                "effects": {"mood": +3, "skill": +2},
            },
            {
                "text": "拿 $100,000 試試看",
                "requires": {"cash_min": 100000},
                "effects": {"cash": -100000, "mood": -30, "skill": +10},
            },
            {
                "text": "賣股票 ALL IN $200,000",
                "effects": {"force_sell": 200000, "mood": -40, "skill": +15},
            },
        ],
    },
    {
        "id": "credit_card_debt",
        "name": "刷卡買名牌",
        "category": "陷阱",
        "weight": 3,
        "min_age": 22, "max_age": 45,
        "once_only": False,
        "text": "百貨週年慶,你看上一個包/錶/3C 產品,需 $50,000。",
        "choices": [
            {
                "text": "刷下去! (-$50,000, 心情 +15)",
                "requires": {"cash_min": 50000},
                "effects": {"cash": -50000, "mood": +15},
            },
            {
                "text": "忍住 (心情 -3)",
                "effects": {"mood": -3, "skill": +1},
            },
        ],
    },
    
    # ============ 進修/成長類 ============
    {
        "id": "study_course",
        "name": "進修機會",
        "category": "成長",
        "weight": 3,
        "min_age": 22, "max_age": 50,
        "once_only": False,
        "text": "你發現一個專業課程,$30,000,完成後技能會大幅提升。",
        "choices": [
            {
                "text": "報名 (-$30,000, 技能 +15)",
                "requires": {"cash_min": 30000},
                "effects": {"cash": -30000, "skill": +15, "mood": +5},
            },
            {
                "text": "看免費 YouTube 自學 (技能 +3)",
                "effects": {"skill": +3},
            },
            {
                "text": "沒興趣",
                "effects": {},
            },
        ],
    },
    {
        "id": "yoga_gym",
        "name": "健身房推銷",
        "category": "成長",
        "weight": 2,
        "min_age": 22, "max_age": 55,
        "once_only": False,
        "text": "健身房推銷年費 $24,000,健康會大幅提升。",
        "choices": [
            {
                "text": "辦年費 (-$24,000, 健康 +20)",
                "requires": {"cash_min": 24000},
                "effects": {"cash": -24000, "health": +20, "mood": +8},
            },
            {
                "text": "辦半年 (-$15,000, 健康 +10)",
                "requires": {"cash_min": 15000},
                "effects": {"cash": -15000, "health": +10, "mood": +3},
            },
            {
                "text": "在家運動就好 (健康 +3)",
                "effects": {"health": +3},
            },
        ],
    },
]


def get_available_events(player, turn):
    """根據玩家狀態,取得可觸發的事件"""
    age = 25 + (turn - 1) // 12  # 每 12 回合 1 歲
    available = []
    
    for ev in EVENTS:
        # 年齡篩選
        if age < ev["min_age"] or age > ev["max_age"]:
            continue
        
        # 一次性事件已觸發過
        if ev.get("once_only") and ev["id"] in player["triggered_once"]:
            continue
        
        # 需要旗標
        required_flag = ev.get("required_flag")
        if required_flag and not player["flags"].get(required_flag):
            continue
        
        # 需要技能
        required_skill = ev.get("required_skill", 0)
        if player["stats"]["skill"] < required_skill:
            continue
        
        available.append(ev)
    
    return available


def roll_event(player, turn):
    """擲骰,看這個月是否發生事件 (機率 50%),發生就回傳一個事件"""
    import random
    
    # 每月 50% 機率有事件
    if random.random() > 0.5:
        return None
    
    available = get_available_events(player, turn)
    if not available:
        return None
    
    # 加權隨機選擇
    weights = [ev["weight"] for ev in available]
    return random.choices(available, weights=weights, k=1)[0]


def can_afford(player, requires):
    """檢查玩家能否負擔此選項"""
    if not requires:
        return True
    if "cash_min" in requires:
        if player["cash"] < requires["cash_min"]:
            return False
    return True
