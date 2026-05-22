"""股海人生 - 股市投資 × 人生模擬遊戲
MVP 版本 - 完整穩定版 (支援零股、多單位切換、獨立事件整合)
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
st.set_page_config(page_title="股海人生", page_icon="📈", layout="wide")

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

# 建立一個安全的獨立儲存庫，用來存放使用者在各個股票輸入框的數量，避免 Streamlit Key 衝突
if "trade_amounts" not in st.session_state:
    st.session_state.trade_amounts = {}

# 新增：用來存放單檔股票交易即時回報的狀態字典
if "trade_alerts" not in st.session_state:
    st.session_state.trade_alerts = {}


# ==================== 開始畫面 ====================
if st.session_state.page == "start":
    st.title("📈 股海人生")
    st.subheader("一場 5 年的投資與人生模擬")
    
    st.markdown("""
    ### 遊戲規則
    - 你扮演一個 **25 歲的上班族**,要存錢、投資、應對人生意外
    - 本版本支援 **多元單位交易**,你可以自由選擇用「1股/10股/100股/1張」來彈性下單
    - 每月結算時有機率觸發 **人生開銷事件**,考驗你的現金流規劃，**現金不夠時記得去賣股變現**
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
        # 初始化所有股票的輸入格數值為 0
        st.session_state.trade_amounts = {sid: 0 for sid in STOCKS.keys()}
        st.session_state.trade_alerts = {}  # 重置交易提示
        st.rerun()


# ==================== 主遊戲畫面 ====================
elif st.session_state.page == "main":
    player = st.session_state.player
    
    # 計算年齡
    age = 25 + (player["turn"] - 1) // 12
    months_in_year = (player["turn"] - 1) % 12 + 1
    
    # ========== 側邊欄：個人資產與狀態固定欄 ==========
    with st.sidebar:
        st.markdown(f"## 👤 {player['name']}")
        st.markdown(f"### {age} 歲 · 第 {player['turn']} / {TOTAL_TURNS} 月")
        
        progress = player["turn"] / TOTAL_TURNS
        st.progress(progress, text=f"時間進度: {player['turn']}/{TOTAL_TURNS} 月")
        
        st.divider()
        st.markdown("#### 💰 目標與資產")
        st.metric("現 金 餘 額", f"${player['cash']:,.0f}")
        
        holdings_value = get_total_holdings_value(player)
        st.metric("持 股 市 值", f"${holdings_value:,}")
        
        net = get_net_worth(player)
        st.metric("💎 總 淨 值", f"${net:,}")
        st.metric("工 作 月 薪", f"${player['monthly_salary']:,}")
        
        st.divider()
        st.markdown("#### 📊 個人屬性")
        stats_emoji = {"health": "❤️ 健康", "mood": "😊 心情", "skill": "🎯 技能", "social": "👥 人脈"}
        for stat, label in stats_emoji.items():
            val = player["stats"][stat]
            st.progress(val / 100, text=f"{label} {val}")
        
        st.divider()
        active_flags = []
        if player["flags"].get("married"): active_flags.append("💍 已婚")
        if player["flags"].get("has_child"): active_flags.append("👶 有小孩")
        if player["flags"].get("has_house"): active_flags.append("🏠 有房")
        if player["flags"].get("dating"): active_flags.append("💕 交往中")
        if player["unemployed_months"] > 0: active_flags.append(f"😩 失業中 ({player['unemployed_months']}月)")
        if active_flags:
            st.caption("狀態效果：\n" + "\n".join([f"• {f}" for f in active_flags]))
    
    # ========== 主畫面內容開始 ==========
    st.markdown("## 📈 股海人生 主控制台")
    st.divider()
    
    # ========== 事件對話框 ==========
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
                    # 如果是因為沒現金，貼心提示玩家去變賣持股
                    st.button(f"❌ {choice['text']} (需備妥現款 ${choice['requires']['cash_min']:,}。請至下方「我的持股」分頁賣股換現再行選擇)", 
                            key=f"choice_{i}", disabled=True, use_container_width=True)
    
    else:
        # ========== 主要操作介面 ==========
        tab1, tab2, tab3, tab4 = st.tabs(["📊 股市交易", "💼 我的持股", "📜 事件履歷", "📈 走勢"])
        
        # ----- 股市 Tab -----
        with tab1:
            st.markdown("#### 即時彈性下單")
            for sid, info in STOCKS.items():
                price = player["market_prices"][sid]
                
                # 計算過去 21 天漲跌
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
                    # 確保字典結構初始化完成
                    if sid not in st.session_state.trade_amounts:
                        st.session_state.trade_amounts[sid] = 0
                        
                    # 1. 交易單位選擇器 (1股 / 10股 / 100股 / 1張)
                    unit_options = {"1股": 1, "10股": 10, "100股": 100, "1張 (1000股)": 1000}
                    selected_unit_label = st.radio(
                        "交易單位", 
                        options=list(unit_options.keys()), 
                        key=f"unit_{sid}", 
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                    unit_multiplier = unit_options[selected_unit_label]
                    
                    # 2. 數量輸入框
                    input_num = st.number_input(
                        f"下單數量 ({selected_unit_label})", 
                        min_value=0, 
                        value=st.session_state.trade_amounts[sid], 
                        step=1, 
                        key=f"num_widget_{sid}"
                    )
                    
                    # 換算實際零股股數與總成交價
                    actual_shares = input_num * unit_multiplier
                    total_estimated_cost = actual_shares * price
                    
                    # 4. 提供使用者當前成本與總價預估試算
                    if actual_shares > 0:
                        st.markdown(f"📋 **下單試算**：單價 `${price:.1f}` × 換算總計 `{actual_shares:,}` 股")
                        st.markdown(f"💰 預估成交總額：**`${total_estimated_cost:,.0f}`**")
                    else:
                        st.caption("請輸入數量進行金額試算")
                    
                    btn_col1, btn_col2 = st.columns(2)
                    with btn_col1:
                        if st.button(f"買進", key=f"btn_buy_{sid}", 
                                     disabled=(actual_shares == 0), use_container_width=True):
                            
                            if player["cash"] < total_estimated_cost:
                                st.session_state.trade_alerts[sid] = {
                                    "type": "error", 
                                    "msg": f"❌ 交易失敗：現金餘額不足！欲購買總額 ${total_estimated_cost:,.0f}，當前帳戶僅有 ${player['cash']:,.0f}。"
                                }
                            else:
                                ok, msg = buy_stock(player, sid, actual_shares)
                                if ok:
                                    remaining_cash = player["cash"]
                                    st.session_state.trade_alerts[sid] = {
                                        "type": "success",
                                        "msg": f"✅ 交易成功！\n▪️ 標的：{sid} {info['name']}\n▪️ 成交股數：{actual_shares:,} 股 (即 {input_num} {selected_unit_label})\n▪️ 成交單價：${price:.1f}\n▪️ 總成交金額：${total_estimated_cost:,.0f}\n▪️ 帳戶剩餘現金：${remaining_cash:,.0f}"
                                    }
                                    st.session_state.trade_amounts[sid] = 0  # 買成功後清除輸入
                                else:
                                    st.session_state.trade_alerts[sid] = {"type": "error", "msg": f"❌ 交易失敗: {msg}"}
                            st.rerun()
                            
                    with btn_col2:
                        if st.button(f"賣出", key=f"btn_sell_{sid}",
                                     disabled=(actual_shares == 0), use_container_width=True):
                            
                            player_owned_shares = player["holdings"].get(sid, {}).get("shares", 0)
                            if player_owned_shares < actual_shares:
                                st.session_state.trade_alerts[sid] = {
                                    "type": "error",
                                    "msg": f"❌ 交易失敗：券商庫存不足！你目前僅持有該股 {player_owned_shares:,} 股，無法賣出 {actual_shares:,} 股。"
                                }
                            else:
                                ok, msg = sell_stock(player, sid, actual_shares)
                                if ok:
                                    remaining_cash = player["cash"]
                                    st.session_state.trade_alerts[sid] = {
                                        "type": "success",
                                        "msg": f"✅ 變賣成功！\n▪️ 標的：{sid} {info['name']}\n▪️ 賣出股數：{actual_shares:,} 股 (即 {input_num} {selected_unit_label})\n▪️ 成交單價：${price:.1f}\n▪️ 獲得現金：${total_estimated_cost:,.0f}\n▪️ 帳戶當前現金：${remaining_cash:,.0f}"
                                    }
                                    st.session_state.trade_amounts[sid] = 0  # 賣成功後清除輸入
                                else:
                                    st.session_state.trade_alerts[sid] = {"type": "error", "msg": f"❌ 交易失敗: {msg}"}
                            st.rerun()
                
                # 👉 直接在各股元件底部顯示成交結果
                if sid in st.session_state.trade_alerts:
                    alert = st.session_state.trade_alerts[sid]
                    if alert["type"] == "success":
                        st.success(alert["msg"])
                    else:
                        st.error(alert["msg"])
                        
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
                    
                    # 自動換算成「幾張幾股」
                    display_shares = f"{h['shares']:,} 股"
                    if h["shares"] >= 1000:
                        display_shares += f" ({h['shares'] // 1000}張 零 {h['shares'] % 1000}股)"
                        
                    holdings_data.append({
                        "代號": sid,
                        "名稱": STOCKS[sid]["name"],
                        "持股庫存": display_shares,
                        "平均持股成本": f"${h['avg_cost']:.1f}",
                        "目前市價": f"${price:.1f}",
                        "目前總市值": f"${int(value):,}",
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
        
        # ========== 上回合事件/月結算即時動態 ==========
        if st.session_state.last_messages:
            with st.expander("📬 本月即時動態 / 月結算回報", expanded=True):
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
                    
                    # 3. 檢查是否到結局
                    if player["turn"] > TOTAL_TURNS:
                        st.session_state.page = "ending"
                        st.rerun()
                    
                    # 4. 擲事件骰
                    event = roll_event(player, player["turn"])
                    if event:
                        st.session_state.pending_event = event
                    
                    # 月份推進時，把當前所有下單輸入框的快取數字與即時交易提示徹底清空
                    st.session_state.trade_amounts = {sid: 0 for sid in STOCKS.keys()}
                    st.session_state.trade_alerts = {}  # 進入新月份，清清爽爽重新開始
                    st.session_state.last_messages = messages
                    st.rerun()
        
        with col_btn2:
            if st.button("🏠 放棄重來", use_container_width=True):
                st.session_state.page = "start"
                st.session_state.player = None
                st.session_state.pending_event = None
                st.session_state.last_messages = []
                st.session_state.trade_amounts = {}
                st.session_state.trade_alerts = {}
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
        st.session_state.trade_amounts = {}
        st.session_state.trade_alerts = {}
        st.rerun()
