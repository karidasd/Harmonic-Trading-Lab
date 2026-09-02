import streamlit as st
import pandas as pd
import textwrap
from datetime import datetime, timezone

def render_page():
    db = st.session_state.db
    
    st.markdown(textwrap.dedent("""
    <div style="border-bottom: 1px solid #1E293B; padding-bottom: 10px; margin-bottom: 20px;">
        <div style="font-size: 1.6rem; font-weight: 800; color: #FFFFFF;">
            🔮 FORWARD PREDICTIONS & OUTCOME TRACKING
        </div>
        <div style="font-size: 0.85rem; color: #94A3B8;">
            Immutable prospective forward recording and causal outcome evaluation (STOP-FIRST Rule).
        </div>
    </div>
    """), unsafe_allow_html=True)
    
    # 1. Forward Metrics Banner (Strictly Separated from Historical 71.8% Gross WR)
    metrics = db.get_forward_metrics()
    
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(textwrap.dedent(f"""
        <div class="hero-metric-box">
            <div class="hero-metric-val">{metrics['total_predictions']}</div>
            <div class="hero-metric-label">FORWARD SIGNALS RECORDED</div>
        </div>
        """), unsafe_allow_html=True)
    with c2:
        st.markdown(textwrap.dedent(f"""
        <div class="hero-metric-box">
            <div class="hero-metric-val" style="color: #00F0FF;">{metrics['active_predictions']}</div>
            <div class="hero-metric-label">ACTIVE UNRESOLVED</div>
        </div>
        """), unsafe_allow_html=True)
    with c3:
        st.markdown(textwrap.dedent(f"""
        <div class="hero-metric-box">
            <div class="hero-metric-val" style="color: #10B981;">{metrics['resolved_predictions']}</div>
            <div class="hero-metric-label">RESOLVED OUTCOMES</div>
        </div>
        """), unsafe_allow_html=True)
    with c4:
        rate_val = f"{metrics['tp1_hit_rate']}%" if metrics['has_sufficient_samples'] else "INSUFFICIENT N"
        st.markdown(textwrap.dedent(f"""
        <div class="hero-metric-box">
            <div class="hero-metric-val" style="color: #F59E0B; font-size: 1.5rem;">{rate_val}</div>
            <div class="hero-metric-label">FORWARD TP1 HIT RATE</div>
        </div>
        """), unsafe_allow_html=True)
        
    if not metrics['has_sufficient_samples']:
        st.warning("⚠️ **INSUFFICIENT FORWARD SAMPLE**: Forward performance metrics require at least N >= 30 resolved predictions to prevent small-sample distortion. Historical baseline metrics (71.8% Gross WR) are maintained separately.")
        
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    
    # 2. Forward Predictions Database Table
    st.markdown("<div style='font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 10px;'>📋 PROSPECTIVE FORWARD LEDGER</div>", unsafe_allow_html=True)
    
    rows = db.get_forward_predictions(limit=150)
    if rows:
        df_view = pd.DataFrame(rows)
        # Select and format display columns
        display_cols = ['id', 'symbol', 'timeframe', 'pattern_type', 'direction', 'status', 'p_tp1', 'p_tp2', 'confidence', 'sl', 'tp1', 'tp2', 'prediction_at', 'resolved_at']
        avail_cols = [c for c in display_cols if c in df_view.columns]
        st.dataframe(df_view[avail_cols], use_container_width=True, height=450)
    else:
        st.info("No forward predictions recorded yet. Run the Active Scanner on live/delayed market data to prospectively log new completed harmonic patterns.")
        
    # 3. Streamlit Cloud Persistence Notice
    st.markdown(textwrap.dedent("""
    <div class="quant-card" style="margin-top: 30px;">
        <div style="font-size: 0.85rem; color: #64748B;">
            <b>Storage Notice:</b> When hosted on Streamlit Community Cloud, local SQLite storage is ephemeral and resets during container redeployments. For multi-month enterprise forward tracking, external PostgreSQL/Supabase replication can be attached.
        </div>
    </div>
    """), unsafe_allow_html=True)
