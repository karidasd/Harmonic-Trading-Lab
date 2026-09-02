import streamlit as st
from typing import Dict, Any
from ui.formatting import InstrumentFormatter

def render_pattern_card(pattern: Dict[str, Any]):
    sym = pattern.get('symbol', 'UNKNOWN')
    tf = pattern.get('timeframe', 'H1')
    ptype = pattern.get('pattern_type', 'ABCD')
    dir_str = pattern.get('direction', 'BULLISH')
    state = pattern.get('state', 'FORMING')
    quality = pattern.get('quality_score', 0)
    
    prec = InstrumentFormatter.get_precision(sym)
    dir_emoji = "🟢" if dir_str == "BULLISH" else "🔴"
    
    with st.container(border=True):
        # Header Row
        col_hdr_left, col_hdr_right = st.columns([7, 5])
        with col_hdr_left:
            st.markdown(f"### {sym} `{tf}`")
            st.markdown(f"{dir_emoji} **{dir_str} {ptype}**")
        with col_hdr_right:
            st.markdown(f"**State:** `{state}`")
            st.markdown(f"**Quality:** `{quality}/100`")
            
        st.divider()
        
        # Price & PRZ Row
        prz_l = pattern.get('prz_low', 0)
        prz_h = pattern.get('prz_high', 0)
        d_p = pattern.get('D_price', 0)
        cur_p = pattern.get('current_price', 0)
        
        c1, c2, c3 = st.columns(3)
        with c1:
            st.caption("PRZ ZONE")
            st.markdown(f"`{prz_l:.{prec}f} – {prz_h:.{prec}f}`")
        with c2:
            st.caption("D PRICE")
            st.markdown(f"`{d_p:.{prec}f}`")
        with c3:
            st.caption("CURRENT PRICE")
            st.markdown(f"`{cur_p:.{prec}f}`")
            
        # Ratios Row
        ratios = pattern.get('ratios', {})
        if ratios:
            r_str = "  •  ".join([f"**{k}:** `{v:.3f}`" for k, v in ratios.items()])
            st.markdown(f"<span style='font-size:0.85rem; color:#94A3B8;'>{r_str}</span>", unsafe_allow_html=True)
            
        st.divider()
        
        # Research Levels
        st.caption("DESCRIPTIVE RESEARCH LEVELS")
        sl = pattern.get('structural_stop', 0)
        t1 = pattern.get('target_1', 0)
        t2 = pattern.get('target_2', 0)
        
        c_l1, c_l2, c_l3 = st.columns(3)
        with c_l1:
            st.markdown(f"🔴 **SL:** `{sl:.{prec}f}`")
        with c_l2:
            st.markdown(f"🟢 **T1:** `{t1:.{prec}f}`")
        with c_l3:
            st.markdown(f"🟢 **T2:** `{t2:.{prec}f}`")
