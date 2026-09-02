import streamlit as st
import pandas as pd
from typing import List, Dict, Any
from ui.formatting import InstrumentFormatter

def render_scanner_table(patterns: List[Dict[str, Any]]) -> pd.DataFrame:
    if not patterns:
        st.info("No active harmonic patterns detected matching current filters.")
        return pd.DataFrame()
        
    rows = []
    for p in patterns:
        sym = p['symbol']
        prec = InstrumentFormatter.get_precision(sym)
        dir_emoji = "▲" if p['direction'] == "BULLISH" else "▼"
        
        # Ratio summary
        ratios = p.get('ratios', {})
        r_str = " | ".join([f"{k}:{v:.2f}" for k, v in list(ratios.items())[:2]])
        
        prz_str = f"{p.get('prz_low', 0):.{prec}f} - {p.get('prz_high', 0):.{prec}f}"
        d_str = f"{p.get('D_price', 0):.{prec}f}" if p.get('D_price') else "—"
        
        rows.append({
            'ID': p['pattern_id'],
            'Pair': sym,
            'TF': p['timeframe'],
            'Pattern': p['pattern_type'],
            'Direction': f"{dir_emoji} {p['direction']}",
            'State': p['state'],
            'Quality': p['quality_score'],
            'PRZ Zone': prz_str,
            'D Price': d_str,
            'Key Ratios': r_str
        })
        
    df_view = pd.DataFrame(rows)
    return df_view
