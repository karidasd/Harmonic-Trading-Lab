import streamlit as st
import pandas as pd
from ui.charts import HarmonicChartBuilder
from ui.pattern_card import render_pattern_card

def render_page():
    st.markdown("""
    <div style="border-bottom: 1px solid #1E293B; padding-bottom: 10px; margin-bottom: 20px;">
        <div style="font-size: 1.6rem; font-weight: 800; color: #FFFFFF;">
            🔍 HISTORICAL PATTERN EXPLORER
        </div>
        <div style="font-size: 0.85rem; color: #94A3B8;">
            Deterministic Exploration of Validated Historical Patterns with Exact Confirmation Coordinates
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    db = st.session_state.db
    recent_patterns = db.get_recent_patterns(limit=100)
    
    if not recent_patterns:
        st.info("No historical patterns recorded in database yet. Run a market scan from the Live Scanner page to populate history.")
        return
        
    df_pats = pd.DataFrame(recent_patterns)
    
    c1, c2, c3 = st.columns([3, 3, 3])
    with c1:
        sel_sym = st.selectbox("Filter Symbol", ["ALL"] + sorted(df_pats['symbol'].unique().tolist()))
    with c2:
        sel_pat = st.selectbox("Filter Pattern Type", ["ALL"] + sorted(df_pats['pattern_type'].unique().tolist()))
    with c3:
        sel_state = st.selectbox("Filter State", ["ALL"] + sorted(df_pats['state'].unique().tolist()))
        
    filtered = df_pats.copy()
    if sel_sym != "ALL":
        filtered = filtered[filtered['symbol'] == sel_sym]
    if sel_pat != "ALL":
        filtered = filtered[filtered['pattern_type'] == sel_pat]
    if sel_state != "ALL":
        filtered = filtered[filtered['state'] == sel_state]
        
    st.markdown(f"<div style='font-size: 0.85rem; color: #94A3B8; margin-bottom: 10px;'>Found <b>{len(filtered)}</b> matching historical patterns in local database.</div>", unsafe_allow_html=True)
    
    if not filtered.empty:
        st.dataframe(filtered[['pattern_id', 'symbol', 'timeframe', 'pattern_type', 'direction', 'state', 'quality_score', 'prz_low', 'prz_high', 'd_price', 'first_detected_at']], use_container_width=True)
