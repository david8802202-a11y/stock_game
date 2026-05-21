with col_action:
    # 💡 修正 1：改用 session_state 當作 number_input 的儲存庫
    # 這樣即使 st.rerun() 執行，張數也不會莫名其妙跳回 0
    input_key = f"num_input_{sid}"
    
    shares_buy = st.number_input(
        f"張數", 
        min_value=0, 
        value=st.session_state.get(input_key, 0), # 從狀態取值，預設為 0
        step=1, 
        key=input_key, 
        label_visibility="collapsed"
    )
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        # 這裡的 key 必須保持唯一
        if st.button(f"買 {shares_buy} 張", key=f"btn_buy_{sid}", 
                     disabled=(shares_buy == 0), use_container_width=True):
            
            ok, msg = buy_stock(player, sid, shares_buy * 1000)
            
            # 💡 修正 2：與其用會消失的 toast，不如直接寫進你原本就有的 last_messages
            if ok:
                st.session_state.last_messages = [f"✅ 成功買進: {msg}"]
                # 交易成功後，把該檔股票的輸入框歸零
                st.session_state[input_key] = 0 
            else:
                st.session_state.last_messages = [f"❌ 買進失敗: {msg}"]
                
            st.rerun()
            
    with btn_col2:
        if st.button(f"賣 {shares_buy} 張", key=f"btn_sell_{sid}",
                     disabled=(shares_buy == 0), use_container_width=True):
            
            ok, msg = sell_stock(player, sid, shares_buy * 1000)
            
            if ok:
                st.session_state.last_messages = [f"✅ 成功賣出: {msg}"]
                st.session_state[input_key] = 0
            else:
                st.session_state.last_messages = [f"❌ 賣出失敗: {msg}"]
                
            st.rerun()
