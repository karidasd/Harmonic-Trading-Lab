import streamlit as st
import pandas as pd
from typing import List, Dict, Any

def render_market_matrix(patterns: List[Dict[str, Any]], symbols: List[str], timeframes: List[str]):
    st.markdown("""
    <div style="margin-bottom: 12px; font-size: 1.1rem; font-weight: 700; color: #FFFFFF;">
        🌐 MULTI-TIMEFRAME HARMONIC MARKET MATRIX
    </div>
    """, unsafe_allow_html=True)
    
    # Map (sym, tf) -> pattern summary
    lookup = {}
    for p in patterns:
        key = (p['symbol'], p['timeframe'])
        if key not in lookup or p['quality_score'] > lookup[key]['quality_score']:
            lookup[key] = p
            
    matrix_data = []
    for sym in symbols:
        row = {'Instrument': sym}
        for tf in timeframes:
            p = lookup.get((sym, tf))
            if p:
                arrow = "↑" if p['direction'] == "BULLISH" else "↓"
                pt = "ABCD" if p['pattern_type'] == "ABCD" else "GART"
                st_code = "✓" if p['state'] == "COMPLETED" else ("⏳" if p['state'] == "POTENTIAL_D" else "⚙")
                row[tf] = f"{pt} {arrow} ({p['quality_score']})"
            else:
                row[tf] = "—"
        matrix_data.append(row)
        
    df_mat = pd.DataFrame(matrix_data).set_index('Instrument')
    st.dataframe(df_mat, use_container_width=True)
