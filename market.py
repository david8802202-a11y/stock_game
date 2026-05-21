"""模擬股市引擎 - 用幾何布朗運動 (GBM) 產生擬真股價走勢

每檔股票有不同的:
- 波動率 (volatility): 0050 低、生技股高
- 漂移率 (drift): 長期年化報酬
- 配息率 (yield): 每年除息
"""
import math
import random


STOCKS = {
    "2330": {
        "name": "台積電",
        "initial_price": 1000,
        "annual_drift": 0.12,        # 年化 12% 報酬
        "annual_vol": 0.28,          # 年化波動 28%
        "yield_rate": 0.025,         # 殖利率 2.5%
        "category": "半導體",
    },
    "2317": {
        "name": "鴻海",
        "initial_price": 200,
        "annual_drift": 0.08,
        "annual_vol": 0.25,
        "yield_rate": 0.045,
        "category": "電子代工",
    },
    "0050": {
        "name": "元大台灣50",
        "initial_price": 195,
        "annual_drift": 0.09,
        "annual_vol": 0.18,           # ETF 波動較低
        "yield_rate": 0.035,
        "category": "ETF",
    },
    "2603": {
        "name": "長榮",
        "initial_price": 180,
        "annual_drift": 0.05,
        "annual_vol": 0.45,           # 航運高波動
        "yield_rate": 0.06,
        "category": "航運",
    },
    "6531": {
        "name": "愛普(模擬小型股)",
        "initial_price": 450,
        "annual_drift": 0.18,         # 高報酬
        "annual_vol": 0.55,           # 高風險
        "yield_rate": 0.01,
        "category": "IC設計",
    },
}


def init_market():
    """初始化市場狀態,回傳每檔股票的當前價格"""
    return {sid: info["initial_price"] for sid, info in STOCKS.items()}


def simulate_month(current_prices, market_sentiment=0.0):
    """模擬一個月的股價變動
    
    market_sentiment: -1 (大空頭) ~ +1 (大多頭),會影響所有股票
    回傳: (新價格 dict, 月內每日價格 list)
    """
    new_prices = {}
    monthly_paths = {}
    
    dt = 1 / 252  # 一交易日 (年化轉日化)
    trading_days = 21  # 每月約 21 個交易日
    
    for sid, info in STOCKS.items():
        price = current_prices[sid]
        path = [price]
        
        # 加上市場情緒
        drift = info["annual_drift"] + market_sentiment * 0.15
        vol = info["annual_vol"]
        
        for _ in range(trading_days):
            # GBM 公式: S(t+dt) = S(t) * exp((mu - 0.5*sigma^2)*dt + sigma*sqrt(dt)*Z)
            z = random.gauss(0, 1)
            drift_term = (drift - 0.5 * vol ** 2) * dt
            vol_term = vol * math.sqrt(dt) * z
            price = price * math.exp(drift_term + vol_term)
            path.append(round(price, 2))
        
        new_prices[sid] = round(price, 2)
        monthly_paths[sid] = path
    
    return new_prices, monthly_paths


def roll_market_sentiment():
    """每月擲市場情緒
    大部分時候是平的,偶爾大牛/大熊"""
    r = random.random()
    if r < 0.05:
        return -0.8  # 大空頭 (5%)
    elif r < 0.15:
        return -0.3  # 小空頭 (10%)
    elif r < 0.75:
        return 0.0   # 平盤 (60%)
    elif r < 0.92:
        return 0.3   # 小多頭 (17%)
    else:
        return 0.8   # 大多頭 (8%)


def get_stock_info(stock_id):
    return STOCKS.get(stock_id)


def calculate_dividend(stock_id, shares, current_price):
    """計算配息 (年度一次,簡化:每年 7 月除息)"""
    info = STOCKS.get(stock_id)
    if not info:
        return 0
    return int(shares * current_price * info["yield_rate"])
