import streamlit as st
from ui.market_matrix import render_market_matrix

def render_page():
    st.markdown("""
    <div style="border-bottom: 1px solid #1E293B; padding-bottom: 10px; margin-bottom: 20px;">
        <div style="font-size: 1.6rem; font-weight: 800; color: #FFFFFF;">
            🌐 MULTI-TIMEFRAME MARKET MATRIX
        </div>
        <div style="font-size: 0.85rem; color: #94A3B8;">
            Cross-Instrument Opportunity Radar across Primary FX Pairs and Higher Timeframes
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    symbols = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD", "EURJPY", "GBPJPY", "XAUUSD"]
    timeframes = ["M15", "M30", "H1", "H4"]
    
    res = st.session_state.last_scan_result
    all_patterns = res['patterns'] if res else []
    
    render_market_matrix(all_patterns, symbols, timeframes)
    
    st.markdown("""
    <div class="quant-card" style="margin-top: 20px;">
        <div style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-bottom: 8px;">MATRIX LEGEND</div>
        <div style="display: flex; gap: 20px; font-size: 0.8rem; color: #94A3B8; font-family: 'JetBrains Mono';">
            <div><span style="color: #10B981;">ABCD ↑</span> Bullish AB=CD</div>
            <div><span style="color: #EF4444;">ABCD ↓</span> Bearish AB=CD</div>
            <div><span style="color: #10B981;">GART ↑</span> Bullish Gartley</div>
            <div><span style="color: #EF4444;">GART ↓</span> Bearish Gartley</div>
            <div><span style="color: #00F0FF;">(Q:85)</span> Geometry Quality Score</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
