"""事件系統 - 隨機人生事件 + 觸發邏輯

事件格式:
{
    "id": 唯一識別碼,
    "name": 顯示名稱,
    "category": 類別 (意外/感情/職場/家庭/幸運/健康/人生突發開銷),
    "weight": 基礎權重 (越高越常發生),
    "min_age": 最小年齡 (歲),
    "max_age": 最大年齡 (歲),
    "once_only": 是否一輩子只能觸發一次,
    "text": 事件描述,
    "choices": 選項列表,
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
                "text": "賣股票支付 (手動前往持股變賣，或選擇攤空承擔後果)",
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
    
    # ============ 💡 新增：每月人生突發開銷抉擇類 (迫使玩家思考是否要賣股換現) ============
    {
        "id": "house_leakage",
        "name": "老家屋頂漏水修繕",
        "category": "人生突發開銷",
        "weight": 4,
        "min_age": 25, "max_age": 60,
        "once_only": False,
        "text": "老家大雨漏水，身為孝子/女的你需要支援修繕費用。需要支付現金 **$80,000** 元！如果現金不足，可以前往「我的持股」分頁賣出股票換現，否則將承擔家庭與心情懲罰！",
        "choices": [
            {
                "text": "👍 沒問題，用現金支援老家 ($80,000)",
                "requires": {"cash_min": 80000},
                "effects": {"cash": -80000, "mood": +5, "social": +10}
            },
            {
                "text": "❌ 兩手攤空：我付不出來 (扣除 20 點心情與 15 點人脈)",
                "effects": {"stats": {"mood": -20, "social": -15}}
            }
        ]
    },
    {
        "id": "car_repair",
        "name": "通勤車輛大修",
        "category": "人生突發開銷",
        "weight": 4,
        "min_age": 22, "max_age": 60,
        "once_only": False,
        "text": "上下班的通勤工具無預警拋錨，汽缸損壞需要大整修！需要支付現金 **$45,000** 元，若不修好會嚴重打擊工作效率與心情。",
        "choices": [
            {
                "text": "🔧 乖乖付錢修車 ($45,000)",
                "requires": {"cash_min": 45000},
                "effects": {"cash": -45000, "mood": -2, "stats": {"skill": +1}}
            },
            {
                "text": "🚌 不修了，天天走路擠公車 (扣除 15 點健康與 15 點心情)",
                "effects": {"stats": {"health": -15, "mood": -15}}
            }
        ]
    },
    {
        "id": "health_checkup",
        "name": "年度自費精密健檢",
        "category": "人生突發開銷",
        "weight": 3,
        "min_age": 25, "max_age": 65,
        "once_only": False,
        "text": "為了預防久坐辦公室引發的職業病，你決定自費安排全身精密健檢，費用為 **$30,000** 元。健康是無價的投資！",
        "choices": [
            {
                "text": "🩺 疼愛自己，預約健檢 ($30,000)",
                "requires": {"cash_min": 30000},
                "effects": {"cash": -30000, "stats": {"health": +20, "mood": +5}}
            },
            {
                "text": "👻 鴕鳥心態：不期不待，沒有傷害 (省下錢，但心情 -5)",
                "effects": {"stats": {"mood": -5}}
            }
        ]
    },
    {
        "id": "wedding_bombs",
        "name": "紅色炸彈連發潮",
        "category": "人生突發開銷",
        "weight": 4,
        "min_age": 25, "max_age":
