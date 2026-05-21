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
    
    # ========== 事件對話框 ==========
    if st.session_state.pending_event:
        ev = st.session_state.pending_event
        
        with st.
