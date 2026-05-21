"""遊戲核心邏輯 - 玩家狀態管理、交易、強制平倉、結局判定"""
from jobs import get_job
from market import init_market, calculate_dividend, STOCKS


def create_player(name, job_id="engineer"):
    """建立新玩家"""
    job = get_job(job_id)
    return {
        "name": name,
        "job_id": job_id,
        "turn": 1,                                  # 第幾個月
        
        "cash": job["starting_cash"],
        "monthly_salary": job["starting_salary"],
        "monthly_expense": job["starting_expense"],
        
        "holdings": {},                             # {"2330": {"shares": 1000, "avg_cost": 1000}}
        
        "stats": dict(job["starting_stats"]),
        
        "flags": {},                                # 旗標 {"married": True, ...}
        "triggered_once": set(),                    # 已觸發過的一次性事件
        
        "log": [],                                  # 歷史紀錄
        "event_history": [],                        # 事件履歷
        "unemployed_months": 0,                     # 失業剩餘月數
        
        "market_prices": init_market(),             # 當前股價
        "price_history": {sid: [info["initial_price"]] 
                          for sid, info in STOCKS.items()},  # 歷史股價
        
        "game_over": False,
        "ending": None,
    }


def buy_stock(player, stock_id, shares):
    """買股票 (1 張 = 1000 股)"""
    price = player["market_prices"][stock_id]
    cost = price * shares
    fee = max(20, cost * 0.001425)  # 手續費 (最低 20 元)
    total = cost + fee
    
    if player["cash"] < total:
        return False, f"現金不足 (需要 ${int(total):,})"
    
    player["cash"] -= total
    
    if stock_id in player["holdings"]:
        h = player["holdings"][stock_id]
        new_shares = h["shares"] + shares
        new_cost = (h["shares"] * h["avg_cost"] + cost) / new_shares
        h["shares"] = new_shares
        h["avg_cost"] = round(new_cost, 2)
    else:
        player["holdings"][stock_id] = {
            "shares": shares,
            "avg_cost": price,
        }
    
    player["log"].append(f"買進 {STOCKS[stock_id]['name']} {shares} 股 @ ${price}")
    return True, "成交"


def sell_stock(player, stock_id, shares):
    """賣股票"""
    if stock_id not in player["holdings"]:
        return False, "你沒有這檔股票"
    
    h = player["holdings"][stock_id]
    if h["shares"] < shares:
        return False, f"你只有 {h['shares']} 股"
    
    price = player["market_prices"][stock_id]
    revenue = price * shares
    fee = max(20, revenue * 0.001425)
    tax = revenue * 0.003  # 證交稅
    net = revenue - fee - tax
    
    player["cash"] += net
    h["shares"] -= shares
    
    if h["shares"] == 0:
        del player["holdings"][stock_id]
    
    profit = (price - h["avg_cost"]) * shares if h["shares"] > 0 else (price - h["avg_cost"]) * shares
    player["log"].append(f"賣出 {STOCKS[stock_id]['name']} {shares} 股 @ ${price} (損益 ${int(profit):,})")
    return True, f"成交,實得 ${int(net):,}"


def force_sell(player, amount_needed):
    """強制賣股,直到湊到 amount_needed
    優先賣賺最多的 (鎖利) → 賣賠最少的"""
    raised = 0
    sold_log = []
    
    # 計算每檔股票的現價值,排序 (賺最多的先賣)
    holdings_with_pnl = []
    for sid, h in list(player["holdings"].items()):
        price = player["market_prices"][sid]
        pnl_pct = (price - h["avg_cost"]) / h["avg_cost"]
        holdings_with_pnl.append((sid, h, pnl_pct))
    holdings_with_pnl.sort(key=lambda x: -x[2])  # 賺最多的優先
    
    for sid, h, pnl_pct in holdings_with_pnl:
        if raised >= amount_needed:
            break
        
        price = player["market_prices"][sid]
        # 算還需要多少股,加上手續費稅金估算 (約 0.45%)
        need = (amount_needed - raised) / 0.9955
        shares_needed = int(need / price) + 1
        shares_to_sell = min(shares_needed, h["shares"])
        
        revenue = price * shares_to_sell
        fee = max(20, revenue * 0.001425)
        tax = revenue * 0.003
        net = revenue - fee - tax
        
        player["cash"] += net
        h["shares"] -= shares_to_sell
        raised += net
        
        sold_log.append(f"強制賣 {STOCKS[sid]['name']} {shares_to_sell} 股 (${int(net):,})")
        
        if h["shares"] == 0:
            del player["holdings"][sid]
    
    if raised < amount_needed:
        # 賣光了還不夠 → 負債或破產
        shortage = amount_needed - raised
        player["cash"] -= shortage  # 變負值代表負債
        sold_log.append(f"⚠️ 賣光持股還缺 ${int(shortage):,},負債中!")
    
    player["log"].extend(sold_log)
    return sold_log


def apply_effects(player, effects):
    """套用事件後果"""
    messages = []
    
    if "cash" in effects:
        player["cash"] += effects["cash"]
        if effects["cash"] > 0:
            messages.append(f"💰 現金 +${effects['cash']:,}")
        else:
            messages.append(f"💸 現金 ${effects['cash']:,}")
    
    if "force_sell" in effects:
        amount = effects["force_sell"]
        messages.append(f"🚨 需要 ${amount:,},強制賣股")
        sold = force_sell(player, amount)
        messages.extend(sold)
        # 強制賣完後扣掉這筆錢
        player["cash"] -= amount
    
    for stat in ["health", "mood", "skill", "social"]:
        if stat in effects:
            old = player["stats"][stat]
            player["stats"][stat] = max(0, min(100, old + effects[stat]))
            diff = effects[stat]
            label = {"health": "健康", "mood": "心情", "skill": "技能", "social": "人脈"}[stat]
            if diff > 0:
                messages.append(f"📈 {label} +{diff}")
            else:
                messages.append(f"📉 {label} {diff}")
    
    if "flag_set" in effects:
        player["flags"][effects["flag_set"]] = True
    
    if "flag_clear" in effects:
        if effects["flag_clear"] in player["flags"]:
            del player["flags"][effects["flag_clear"]]
    
    if "expense_change" in effects:
        player["monthly_expense"] += effects["expense_change"]
        if effects["expense_change"] > 0:
            messages.append(f"📅 每月支出 +${effects['expense_change']:,}")
        else:
            messages.append(f"📅 每月支出 ${effects['expense_change']:,}")
    
    if "salary_multiplier" in effects:
        player["monthly_salary"] = int(player["monthly_salary"] * effects["salary_multiplier"])
        messages.append(f"💼 月薪變為 ${player['monthly_salary']:,}")
    
    if "cash_multiplier_salary" in effects:
        bonus = player["monthly_salary"] * effects["cash_multiplier_salary"]
        player["cash"] += bonus
        messages.append(f"🎉 領到 ${bonus:,} (年終/獎金)")
    
    if "auto_buy" in effects:
        stock_id, amount = effects["auto_buy"]
        price = player["market_prices"][stock_id]
        shares = int(amount / price / 1000) * 1000
        if shares > 0:
            buy_stock(player, stock_id, shares)
            messages.append(f"📊 自動買進 {STOCKS[stock_id]['name']} {shares} 股")
    
    # 失業旗標
    if effects.get("flag_set") == "unemployed_3m":
        player["unemployed_months"] = 3
    
    return messages


def monthly_settlement(player, market_sentiment):
    """月結算 - 領薪/扣支出/股價變動/職業數值漂移"""
    from market import simulate_month
    
    messages = []
    job = get_job(player["job_id"])
    
    # 1. 領薪 (失業期間沒薪水)
    if player["unemployed_months"] > 0:
        player["unemployed_months"] -= 1
        messages.append(f"😩 失業中 (剩 {player['unemployed_months']} 個月)")
    else:
        # 每年加薪 4%
        years_worked = (player["turn"] - 1) // 12
        salary = int(player["monthly_salary"] * ((1 + job["salary_growth_yearly"]) ** years_worked))
        player["cash"] += salary
        messages.append(f"💼 領薪 +${salary:,}")
    
    # 2. 扣支出
    player["cash"] -= player["monthly_expense"]
    messages.append(f"🏠 月支出 -${player['monthly_expense']:,}")
    
    # 3. 月內股價走勢
    new_prices, paths = simulate_month(player["market_prices"], market_sentiment)
    player["market_prices"] = new_prices
    for sid, path in paths.items():
        player["price_history"][sid].extend(path[1:])  # 去掉重複的第一個
    
    sentiment_msg = {
        -0.8: "📉 大空頭來襲!",
        -0.3: "📉 市場走弱",
        0.0: "↔️ 盤整中",
        0.3: "📈 市場走強",
        0.8: "🚀 大多頭行情!",
    }.get(market_sentiment, "")
    if sentiment_msg:
        messages.append(sentiment_msg)
    
    # 4. 職業數值漂移
    for stat, change in job["monthly_stat_drift"].items():
        old = player["stats"][stat]
        player["stats"][stat] = max(0, min(100, old + change))
    
    # 5. 配息 (每年 7 月,即 turn % 12 == 7)
    if player["turn"] % 12 == 7:
        total_div = 0
        for sid, h in player["holdings"].items():
            div = calculate_dividend(sid, h["shares"], player["market_prices"][sid])
            total_div += div
        if total_div > 0:
            player["cash"] += total_div
            messages.append(f"💰 收到股息 ${total_div:,}")
    
    # 6. 現金為負 → 強制賣股
    if player["cash"] < 0:
        debt = abs(player["cash"])
        player["cash"] = 0
        if get_total_holdings_value(player) > 0:
            messages.append(f"⚠️ 現金不足!強制賣股 ${debt:,}")
            force_sell(player, debt)
        else:
            # 沒股票可賣 → 破產
            messages.append(f"💀 破產!欠 ${debt:,} 無法償還")
            player["game_over"] = True
            player["ending"] = "破產"
    
    return messages


def get_total_holdings_value(player):
    """計算持股總市值"""
    total = 0
    for sid, h in player["holdings"].items():
        total += h["shares"] * player["market_prices"][sid]
    return int(total)


def get_net_worth(player):
    """計算淨值"""
    return player["cash"] + get_total_holdings_value(player)


def determine_ending(player):
    """根據結局判定"""
    net_worth = get_net_worth(player)
    
    if player["game_over"] and player["ending"] == "破產":
        return {
            "title": "💀 破產結局",
            "desc": "你的人生規劃失敗,陷入債務無法翻身。",
            "rank": "F",
        }
    
    # 5 年後的結局
    if net_worth >= 5000000:
        return {"title": "🏆 財富自由", "desc": "5 年內累積超過 500 萬,投資與人生兩得意!", "rank": "S"}
    elif net_worth >= 3000000:
        return {"title": "🌟 成功投資人", "desc": "5 年內累積 300 萬以上,前途無量。", "rank": "A"}
    elif net_worth >= 1500000:
        return {"title": "😊 穩健發展", "desc": "5 年穩健累積資產,生活還算順遂。", "rank": "B"}
    elif net_worth >= 500000:
        return {"title": "😐 普通上班族", "desc": "資產普通,還在為生活打拼。", "rank": "C"}
    elif net_worth >= 0:
        return {"title": "😟 月光族", "desc": "5 年下來幾乎沒存到錢,投資需要更謹慎。", "rank": "D"}
    else:
        return {"title": "💸 負債累累", "desc": "投資與消費失衡,陷入負債。", "rank": "F"}
