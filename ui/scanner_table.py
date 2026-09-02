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
        
        # Prices & targets
        d_str = f"{p.get('D_price', 0):.{prec}f}" if p.get('D_price') else "—"
        cur_str = f"{p.get('current_price', 0):.{prec}f}" if p.get('current_price') else "—"
        sl_str = f"{p.get('structural_stop', 0):.{prec}f}" if p.get('structural_stop') else "—"
        tp1_str = f"{p.get('target_1', 0):.{prec}f}" if p.get('target_1') else "—"
        tp2_str = f"{p.get('target_2', 0):.{prec}f}" if p.get('target_2') else "—"
        
        # Probabilities
        p1 = p.get('p_tp1')
        p2 = p.get('p_tp2')
        p1_str = f"{p1:.1f}%" if p1 is not None else "—"
        p2_str = f"{p2:.1f}%" if p2 is not None else "—"
        
        # New alert indicator
        is_new = p.get('is_new_in_session', False)
        new_tag = "⚡ NEW" if is_new else ""
        
        rows.append({
            'Alert': new_tag,
            'Pair': sym,
            'TF': p['timeframe'],
            'Pattern': p['pattern_type'],
            'Side': f"{dir_emoji} {p['direction']}",
            'State': p['state'],
            'Quality': f"{p['quality_score']}/100",
            'Current Price': cur_str,
            'D Price': d_str,
            'SL': sl_str,
            'TP1': tp1_str,
            'TP2': tp2_str,
            'P(TP1)': p1_str,
            'P(TP2)': p2_str,
            'Confidence': p.get('confidence', 'N/A'),
            'Status': p.get('forward_status', p.get('state'))
        })
        
    df_view = pd.DataFrame(rows)
    return df_view
