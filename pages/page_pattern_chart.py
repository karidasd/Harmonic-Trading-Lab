import streamlit as st
from ui.charts import HarmonicChartBuilder
from ui.pattern_card import render_pattern_card

def render_page():
    st.markdown("""
    <div style="border-bottom: 1px solid #1E293B; padding-bottom: 10px; margin-bottom: 20px;">
        <div style="font-size: 1.6rem; font-weight: 800; color: #FFFFFF;">
            📈 PATTERN CHART & DEEP GEOMETRY
        </div>
        <div style="font-size: 0.85rem; color: #94A3B8;">
            High-Resolution Candlestick Chart with Causal XABCD Legs, PRZ Zone, and Research Levels
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    scanner = st.session_state.scanner
    res = st.session_state.last_scan_result
    all_patterns = res['patterns'] if res else []
    
    c_sym, c_tf, c_bars, c_levels = st.columns([3, 2, 2, 2])
    with c_sym:
        sym = st.selectbox("Symbol", ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD", "EURJPY", "GBPJPY", "XAUUSD"], index=0)
    with c_tf:
        tf = st.selectbox("Timeframe", ["M15", "M30", "H1", "H4"], index=2)
    with c_bars:
        bars_cnt = st.slider("Lookback Bars", min_value=60, max_value=500, value=200, step=20)
    with c_levels:
        show_levels = st.checkbox("Show Research Levels", value=True)
        
    df_ohlcv = st.session_state.data_provider.get_ohlcv(sym, tf, bars=bars_cnt)
    
    # Find matching active pattern if any
    matched_pat = next((p for p in all_patterns if p['symbol'] == sym and p['timeframe'] == tf), None)
    if not matched_pat:
        # Detect on-the-fly for this specific chart
        on_the_fly_pats = scanner.detector.scan_dataframe(df_ohlcv, sym, tf)
        if on_the_fly_pats:
            matched_pat = on_the_fly_pats[0]
            
    col_chart, col_side = st.columns([8, 4])
    
    with col_chart:
        if df_ohlcv is not None and not df_ohlcv.empty:
            fig = HarmonicChartBuilder.build_harmonic_chart(df_ohlcv, matched_pat, show_levels=show_levels)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error(f"Unable to load market data for {sym} {tf}.")
            
    with col_side:
        if matched_pat:
            render_pattern_card(matched_pat)
        else:
            st.markdown(f"""
            <div class="quant-card">
                <div style="font-size: 1.1rem; font-weight: 700; color: #94A3B8; margin-bottom: 10px;">MARKET STATUS</div>
                <div style="color: #64748B; font-size: 0.85rem;">No active harmonic pattern currently formed on <b>{sym} {tf}</b>.</div>
            </div>
            """, unsafe_allow_html=True)
