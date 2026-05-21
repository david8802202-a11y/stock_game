"""股海人生 - 股市投資 × 人生模擬遊戲
MVP 版本 - 升級零股交易、即時成本試算與每月抉擇事件
"""
import streamlit as st
import pandas as pd
import random
from datetime import datetime

from game_core import (
    create_player, buy_stock, sell_stock, apply_effects,
    monthly_settlement, get_total_holdings_value, get_net_worth,
    determine_ending,
)
from market import STOCKS, roll_market_sentiment
from events import roll_event, can_afford
from jobs import JOBS


# ==================== Streamlit 設定 ====================
st.set_page_config(page_title="股海人生 v2", page_icon="📈", layout="wide")

# 5 年 = 60 個月
TOTAL_TURNS = 60


# ==================== 初始化 session_state ====================
if "page" not in st.session_state:
    st.session_state.page = "start"
if "player" not in st.session_state:
    st.session_state.player = None
if "pending_event" not in st.session_state:
    st.session_state.pending_event = None
if "last_messages" not in st.session_state:
    st.session_state.last_messages = []


# ==================== 開始畫面 ====================
if st.session_state.page == "start":
    st.title("📈 股海人生 (零股交易微調版)")
    st.subheader("一場 5 年的投資與人生模擬")
    
    st.markdown("""
    ### 遊戲規則
    - 你扮演一個 **25 歲的上班族**,要存錢、投資、應對人生意外
    - 本版本支援 **零股交易**,你可以自由輸入想買賣的「股數」（非張數）
    - 每月結算時若觸發 **臨時人生事件**，你可以選擇保留現金或變賣持股應對！
    - 5 年 (60 個月) 後結算,看你能達到什麼結局
    
    ### 你的目標
    - **S 級結局**: 淨值 500 萬以上 (財富自由)
    - **A 級結局**: 300 萬以上
    - **B 級結局**: 150 萬以上
    - **C 級以下**: 月光族或負債
    """)
    
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("你的名字", value="小王")
    with col2:
        job_id = st.selectbox(
            "選擇職業",
            options=list(JOBS.keys()),
            format_func=lambda x: JOBS[x]["name"]
        )
    
    job = JOBS[job_id]
    st.info(f"""
    **{job['name']}**: {job['desc']}
    - 起始現金: ${job['starting_cash']:,}
    - 月薪: ${job['starting_salary']:,}
    - 月支出: ${job['starting_expense']:,}
    """)
    
    if st.button("🎬 開始遊戲", type="primary", use_container_width=True):
        st.session_state.player = create_player(name, job_id)
        st.session_state.page = "main"
        st.rerun()


# ==================== 主遊戲畫面 ====================
elif st.session_state.page == "main":
    player = st.session_state.player
    
    # 計算年齡
    age = 25 + (player["turn"] - 1) // 12
    months_in_year = (player["turn"] - 1) % 12 + 1
    
    # ========== 頂部狀態列 ==========
    st.markdown(f"### {player['name']} · {age} 歲 · 第 {player['turn']} / {TOTAL_TURNS} 月")
    progress = player["turn"] / TOTAL_TURNS
    st.progress(progress, text=f"已過 {player['turn']} 個月")
    
    # 資產卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 現金", f"${player['cash']:,.0f}")
    with col2:
        holdings_value = get_total_holdings_value(player)
        st.metric("📊 持股市值", f"${holdings_value:,}")
    with col3:
        net = get_net_worth(player)
        st.metric("💎 總淨值", f"${net:,}")
    with col4:
        st.metric("💼 月薪", f"${player['monthly_salary']:,}")
    
    # 數值狀態
    st.markdown("**個人狀態**")
    sc1, sc2, sc3, sc4 = st.columns(4)
    stats_emoji = {"health": "❤️ 健康", "mood": "😊 心情", "skill": "🎯 技能", "social": "👥 人脈"}
    for col, (stat, label) in zip([sc1, sc2, sc3, sc4], stats_emoji.items()):
        with col:
            val = player["stats"][stat]
            st.progress(val / 100, text=f"{label} {val}")
    
    # 旗標顯示
    active_flags = []
    if player["flags"].get("married"): active_flags.append("💍 已婚")
    if player["flags"].get("has_child"): active_flags.append("👶 有小孩")
    if player["flags"].get("has_house"): active_flags.append("🏠 有房")
    if player["flags"].get("dating"): active_flags.append("💕 交往中")
    if player["unemployed_months"] > 0: active_flags.append(f"😩 失業中 ({player['unemployed_months']}月)")
    if active_flags:
        st.caption(" · ".join(active_flags))
    
    st.divider()
    
    # ========== 事件對話框 (包含第3點：每月臨時事件抉擇) ==========
    if st.session_state.pending_event:
        ev = st.session_state.pending_event
        
        with st.container(border=True):
            st.markdown(f"### 🎲 {ev['name']}")
            st.markdown(f"*類別: {ev['category']}*")
            st.markdown(ev["text"])
            st.markdown("---")
            
            st.markdown("**你的選擇:**")
            for i, choice in enumerate(ev["choices"]):
                can_do = can_afford(player, choice.get("requires", {}))
                
                if can_do:
                    if st.button(choice["text"], key=f"choice_{i}", use_container_width=True):
                        # 套用後果
                        messages = apply_effects(player, choice["effects"])
                        
                        # 記錄事件
                        player["event_history"].append({
                            "turn": player["turn"],
                            "event": ev["name"],
                            "choice": choice["text"],
                        })
                        if ev.get("once_only"):
                            player["triggered_once"].add(ev["id"])
                        
                        st.session_state.last_messages = [f"📌 {ev['name']}: {choice['text']}"] + messages
                        st.session_state.pending_event = None
                        st.rerun()
                else:
                    # 如果是因為沒現金，提示玩家去旁邊的「我的持股」分頁先主動賣股，再來按這個按鈕
                    st.button(f"❌ {choice['text']} (現金不足！你需要 ${choice['requires']['cash_min']:,}。請前往變賣股票換取現金)", 
                            key=f"choice_{i}", disabled=True, use_container_width=True)
    
    else:
        # ========== 主要操作介面 ==========
        tab1, tab2, tab3, tab4 = st.tabs(["📊 股市交易", "💼 我的持股", "📜 事件履歷", "📈 走勢"])
        
        # ----- 股市 Tab (修正功能 1, 2, 4) -----
        with tab1:
            st.markdown("#### 即時零股下單")
            for sid, info in STOCKS.items():
                price = player["market_prices"][sid]
                
                # 計算月漲跌
                history = player["price_history"][sid]
                if len(history) >= 22:
                    prev_price = history[-22]
                    change = (price - prev_price) / prev_price * 100
                else:
                    change = 0
                
                col_info, col_price, col_action = st.columns([2, 1, 2])
                with col_info:
                    st.markdown(f"**{sid} {info['name']}**")
                    st.caption(f"{info['category']} · 殖利率 {info['yield_rate']*100:.1f}%")
                with col_price:
                    color = "🟢" if change >= 0 else "🔴"
                    st.markdown(f"### ${price:.1f}")
                    st.caption(f"{color} 月變動 {change:+.1f}%")
                
                with col_action:
                    input_key = f"num_input_{sid}"
                    # 修正 1：改為「股數」輸入（零股最小單位為 1 股）
                    shares_buy = st.number_input(
                        f"股數", 
                        min_value=0, 
                        value=st.session_state.get(input_key, 0), 
                        step=10, 
                        key=input_key, 
                        label_visibility="collapsed"
                    )
                    
                    # 修正 4：動態提供「當前單價」與「預估成交總額」
                    total_estimated_cost = shares_buy * price
                    if shares_buy > 0:
                        st.markdown(f"💰 現價: `${price:.1f}` | 預估總額: `${total_estimated_cost:,.0f}`")
                    else:
                        st.caption("請輸入股數進行試算")
                    
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button(f"買進零股", key=f"btn_buy_{sid}", 
                                     disabled=(shares_buy == 0), use_container_width=True):
                            
                            # 核心邏輯防呆檢查
                            if player["cash"] < total_estimated_cost:
                                st.session_state.last_messages = [f"❌ 交易失敗：現金餘額不足！欲購買總額 ${total_estimated_cost:,.0f}，當前僅有 ${player['cash']:,.0f}。"]
                            else:
                                # 修正 1：不乘 1000，直接傳入真實股數進 game_core 的函數
                                ok, msg = buy_stock(player, sid, shares_buy) 
                                if ok:
                                    # 修正 2：明確回報交易明細與餘額
                                    remaining_cash = player["cash"]
                                    st.session_state.last_messages = [
                                        f"✅ 交易成功！",
                                        f"▪️ 標的：{sid} {info['name']}",
                                        f"▪️ 成交股數：{shares_buy:,} 股",
                                        f"▪️ 成交單價：${price:.1f}",
                                        f"▪️ 總成交金額：${total_estimated_cost:,.0f}",
                                        f"▪️ 帳戶剩餘現金：${remaining_cash:,.0f}"
                                    ]
                                    st.session_state[input_key] = 0  # 歸零
                                else:
                                    st.session_state.last_messages = [f"❌ 交易失敗: {msg}"]
                            st.rerun()
                            
                    with btn_col2:
                        if st.button(f"賣出零股", key=f"btn_sell_{sid}",
                                     disabled=(shares_buy == 0), use_container_width=True):
                            
                            # 檢查玩家是不是真的有這麼多持股
                            player_owned_shares = player["holdings"].get(sid, {}).get("shares", 0)
                            if player_owned_shares < shares_buy:
                                st.session_state.last_messages = [f"❌ 交易失敗：券商庫存不足！你目前僅持有該股 {player_owned_shares:,} 股，無法賣出 {shares_buy:,} 股。"]
                            else:
                                ok, msg = sell_stock(player, sid, shares_buy)
                                if ok:
                                    # 修正 2：回報賣出細節與剩餘金額
                                    remaining_cash = player["cash"]
                                    st.session_state.last_messages = [
                                        f"✅ 變賣成功！",
                                        f"▪️ 標的：{sid} {info['name']}",
                                        f"▪️ 賣出股數：{shares_buy:,} 股",
                                        f"▪️ 成交單價：${price:.1f}",
                                        f"▪️ 獲得現金：${total_estimated_cost:,.0f}",
                                        f"▪️ 帳戶當前現金：${remaining_cash:,.0f}"
                                    ]
                                    st.session_state[input_key] = 0  # 歸零
                                else:
                                    st.session_state.last_messages = [f"❌ 交易失敗: {msg}"]
                            st.rerun()
                st.divider()
        
        # ----- 我的持股 Tab -----
        with tab2:
            if player["holdings"]:
                holdings_data = []
                for sid, h in player["holdings"].items():
                    if h["shares"] <= 0:
                        continue
                    price = player["market_prices"][sid]
                    value = h["shares"] * price
                    cost = h["shares"] * h["avg_cost"]
                    pnl = value - cost
                    pnl_pct = (pnl / cost * 100) if cost > 0 else 0
                    holdings_data.append({
                        "代號": sid,
                        "名稱": STOCKS[sid]["name"],
                        "持股數(零股)": f"{h['shares']:,} 股",
                        "平均成本": f"${h['avg_cost']:.1f}",
                        "當前現價": f"${price:.1f}",
                        "目前市值": f"${int(value):,}",
                        "累積損益": f"${int(pnl):+,}",
                        "投資報酬率": f"{pnl_pct:+.1f}%",
                    })
                if holdings_data:
                    df = pd.DataFrame(holdings_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)
                else:
                    st.info("還沒有任何持股,去股市買進吧!")
            else:
                st.info("還沒有任何持股,去股市買進吧!")
        
        # ----- 事件履歷 Tab -----
        with tab3:
            if player["event_history"]:
                df = pd.DataFrame([
                    {"月份": e["turn"], "事件": e["event"], "選擇": e["choice"]}
                    for e in reversed(player["event_history"])
                ])
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("還沒有經歷任何事件")
        
        # ----- 走勢 Tab -----
        with tab4:
            df_data = {}
            for sid, info in STOCKS.items():
                history = player["price_history"][sid]
                df_data[f"{sid} {info['name']}"] = history
            
            # 對齊長度
            max_len = max(len(v) for v in df_data.values())
            for k in df_data:
                df_data[k] = df_data[k] + [None] * (max_len - len(df_data[k]))
            
            df = pd.DataFrame(df_data)
            st.line_chart(df)
        
        # ========== 上回合事件/交易訊息 ==========
        if st.session_state.last_messages:
            with st.expander("📬 本月即時動態 / 交易成交回報", expanded=True):
                for msg in st.session_state.last_messages:
                    st.write(msg)
        
        st.divider()
        
        # ========== 下個月按鈕 ==========
        col_btn1, col_btn2 = st.columns([3, 1])
        with col_btn1:
            if st.button("⏭️ 結束本月 (進入下個月)", type="primary", use_container_width=True):
                # 1. 月結算
                sentiment = roll_market_sentiment()
                messages = monthly_settlement(player, sentiment)
                
                # 檢查破產
                if player["game_over"]:
                    st.session_state.last_messages = messages
                    st.session_state.page = "ending"
                    st.rerun()
                
                # 2. 推進回合
                player["turn"] += 1
                
                # 3. 看看是否到結局
                if player["turn"] > TOTAL_TURNS:
                    st.session_state.page = "ending"
                    st.rerun()
                
                # 4. 修正 3：加入高機率觸發的「人生抉擇隨機事件」
                # 丟骰子，讓玩家面臨需要巨額現金、迫使他們決定要不要去賣股的場景
                event = roll_event(player, player["turn"])
                
                # 萬一 events.py 沒抽到，我們在此 MVP 內建一個需要金錢抉擇的臨時事件
                if not event and random.random() < 0.4:
                    random_expenses = random.choice([
                        {"name": "老家屋頂漏水修繕", "cash": 80000, "desc": "老家大雨漏水，身為孝子需要支援修繕費用。"},
                        {"name": "機車/汽車引擎大修", "cash": 45000, "desc": "上下班工具無預警拋錨，汽缸損壞需要大整修。"},
                        {"name": "年度高階健康檢查", "cash": 30000, "desc": "為了預防職業病，你決定自費安排全身精密健檢。"},
                        {"name": "朋友結婚與聚會潮", "cash": 20000, "desc": "這個月炸彈連發，死黨結婚加上各種人脈應酬聚餐。"}
                    ])
                    
                    event = {
                        "id": "temp_life_expense",
                        "name": random_expenses["name"],
                        "category": "人生突發開銷",
                        "text": f"{random_expenses['desc']} 需要支付現金 **${random_expenses['cash']:,}** 元。如果現金不足，請點擊旁邊分頁賣出股票換現，否則將會違約扣除健康或心情！",
                        "choices": [
                            {
                                "text": f"👍 沒問題，直接用現金大方支付 (${random_expenses['cash']:,} 元)",
                                "requires": {"cash_min": random_expenses["cash"]},
                                "effects": {"cash": -random_expenses["cash"], "stats": {"mood": 5}}
                            },
                            {
                                "text": "❌ 兩手攤空：我付不出來 (扣除 20 點健康與 20 點心情)",
                                "requires": {"cash_min": 0},
                                "effects": {"stats": {"health": -20, "mood": -20}}
                            }
                        ]
                    }
                
                if event:
                    st.session_state.pending_event = event
                
                st.session_state.last_messages = messages
                st.rerun()
        
        with col_btn2:
            if st.button("🏠 放棄重來", use_container_width=True):
                st.session_state.page = "start"
                st.session_state.player = None
                st.session_state.pending_event = None
                st.session_state.last_messages = []
                st.rerun()


# ==================== 結局畫面 ====================
elif st.session_state.page == "ending":
    player = st.session_state.player
    ending = determine_ending(player)
    
    st.title("🎬 遊戲結束")
    st.balloons()
    
    st.markdown(f"## {ending['title']}")
    st.markdown(f"### 評價: **{ending['rank']}**")
    st.info(ending["desc"])
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("最終淨值", f"${get_net_worth(player):,}")
    with col2:
        st.metric("現金", f"${player['cash']:,.0f}")
    with col3:
        st.metric("持股市值", f"${get_total_holdings_value(player):,}")
    
    st.divider()
    
    st.markdown("### 你的人生大事")
    if player["event_history"]:
        df = pd.DataFrame([
            {"月份": e["turn"], "事件": e["event"], "選擇": e["choice"]}
            for e in player["event_history"]
        ])
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    if st.button("🔄 再玩一次", type="primary", use_container_width=True):
        st.session_state.page = "start"
        st.session_state.player = None
        st.session_state.pending_event = None
        st.session_state.last_messages = []
        st.rerun()
