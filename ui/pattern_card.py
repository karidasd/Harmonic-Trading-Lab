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
    
    dir_color = "#10B981" if dir_str == "BULLISH" else "#EF4444"
    state_badge_cls = {
        'COMPLETED': 'badge-completed',
        'POTENTIAL_D': 'badge-potential',
        'FORMING': 'badge-forming',
        'INVALIDATED': 'badge-invalidated'
    }.get(state, 'badge-forming')
    
    prec = InstrumentFormatter.get_precision(sym)
    
    st.markdown(f"""
    <div class="quant-card">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1E293B; padding-bottom: 10px; margin-bottom: 15px;">
            <div>
                <span style="font-size: 1.4rem; font-weight: 800; font-family: 'JetBrains Mono';">{sym}</span>
                <span style="font-size: 0.9rem; color: #94A3B8; margin-left: 8px;">{tf}</span>
            </div>
            <div>
                <span class="badge {state_badge_cls}">{state}</span>
            </div>
        </div>
        
        <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
            <div>
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 600;">PATTERN & DIRECTION</div>
                <div style="font-size: 1.05rem; font-weight: 700; color: {dir_color}; font-family: 'JetBrains Mono';">{dir_str} {ptype}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.75rem; color: #64748B; font-weight: 600;">GEOMETRY QUALITY</div>
                <div style="font-size: 1.05rem; font-weight: 800; color: #00F0FF; font-family: 'JetBrains Mono';">{quality} / 100</div>
            </div>
        </div>
        
        <div style="background: #080B10; border-radius: 6px; padding: 12px; margin-bottom: 15px; font-family: 'JetBrains Mono'; font-size: 0.85rem;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="color: #64748B;">PRZ Zone:</span>
                <span>{pattern.get('prz_low', 0):.{prec}f} – {pattern.get('prz_high', 0):.{prec}f}</span>
            </div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span style="color: #64748B;">D Price / Target:</span>
                <span>{pattern.get('D_price', 0):.{prec}f}</span>
            </div>
            <div style="display: flex; justify-content: space-between;">
                <span style="color: #64748B;">Current Market:</span>
                <span style="color: #00F0FF;">{pattern.get('current_price', 0):.{prec}f}</span>
            </div>
        </div>
        
        <div style="border-top: 1px solid #1E293B; padding-top: 12px;">
            <div style="font-size: 0.75rem; color: #94A3B8; font-weight: 600; text-transform: uppercase; margin-bottom: 8px;">RESEARCH LEVELS (Descriptive)</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; text-align: center; font-family: 'JetBrains Mono'; font-size: 0.8rem;">
                <div style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 4px; padding: 6px;">
                    <div style="color: #EF4444; font-size: 0.7rem;">STRUCTURAL SL</div>
                    <div>{pattern.get('structural_stop', 0):.{prec}f}</div>
                </div>
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 4px; padding: 6px;">
                    <div style="color: #10B981; font-size: 0.7rem;">RESEARCH T1</div>
                    <div>{pattern.get('target_1', 0):.{prec}f}</div>
                </div>
                <div style="background: rgba(52, 211, 153, 0.1); border: 1px solid rgba(52, 211, 153, 0.3); border-radius: 4px; padding: 6px;">
                    <div style="color: #34D399; font-size: 0.7rem;">RESEARCH T2</div>
                    <div>{pattern.get('target_2', 0):.{prec}f}</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
