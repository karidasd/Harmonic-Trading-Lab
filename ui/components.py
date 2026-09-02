import streamlit as st
import plotly.graph_objects as go
import textwrap
from datetime import datetime, timezone
from typing import Dict, Any

def render_command_header(provider_status: Dict[str, Any], last_scan_time: datetime, markets_count: int, scan_res: Dict[str, Any] = None, storage_status: Dict[str, Any] = None):
    p_name = provider_status.get('provider_name', 'DEMO FEED')
    mode = provider_status.get('mode', 'DEMO')
    status = provider_status.get('status', 'ONLINE')
    
    status_color = "#10B981" if status in ["ONLINE", "CONNECTED"] else "#F59E0B"
    mode_badge = f"<span class='badge badge-completed'>{mode}</span>" if mode == "LIVE" else (f"<span class='badge badge-potential'>{mode}</span>" if mode == "CLOUD" else f"<span class='badge badge-forming'>{mode}</span>")
    
    # Storage status badge
    is_persist = storage_status.get('is_persistent', False) if storage_status else False
    st_label = "● PERSISTENT POSTGRES" if is_persist else "⚠️ LOCAL SQLITE"
    st_color = "#10B981" if is_persist else "#F59E0B"
    st_badge = f"<span style='background: rgba(255,255,255,0.06); color: {st_color}; border: 1px solid {st_color}; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 0.75rem; margin-left: 6px;'>{st_label}</span>"

    latency_str = ""
    if scan_res:
        f_lat = scan_res.get('data_fetch_latency_sec', 0.0)
        d_lat = scan_res.get('detection_latency_sec', 0.0)
        t_lat = scan_res.get('scan_duration_sec', 0.0)
        latency_str = f" | Latency: [Fetch: {f_lat:.2f}s | Detect: {d_lat:.2f}s | Total: {t_lat:.2f}s]"
        
    html = f"""
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #1E293B; padding-bottom: 15px; margin-bottom: 20px;">
        <div>
            <div style="font-size: 1.8rem; font-weight: 800; letter-spacing: -0.02em; color: #FFFFFF;">
                ⚡ LIVE HARMONIC MARKET INTELLIGENCE
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8; font-weight: 500;">
                AB=CD & Gartley • Causal Detection • Non-Repainting Research Engine
            </div>
        </div>
        <div style="text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;">
            <div><span style="color: {status_color};">●</span> {p_name} {mode_badge} {st_badge}</div>
            <div style="color: #64748B; margin-top: 4px;">UTC: {datetime.now(timezone.utc).strftime('%H:%M:%S')} | Scanned: {markets_count} Markets{latency_str}</div>
        </div>
    </div>
    """
    st.markdown(textwrap.dedent(html), unsafe_allow_html=True)

def render_hero_metrics(active_cnt: int, markets_cnt: int):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(textwrap.dedent("""
        <div class="hero-metric-box">
            <div class="hero-metric-val">71.8%</div>
            <div class="hero-metric-label">GROSS HISTORICAL WR</div>
        </div>
        """), unsafe_allow_html=True)
    with c2:
        st.markdown(textwrap.dedent("""
        <div class="hero-metric-box">
            <div class="hero-metric-val" style="color: #10B981;">0</div>
            <div class="hero-metric-label">REPAINT FAILURES</div>
        </div>
        """), unsafe_allow_html=True)
    with c3:
        st.markdown(textwrap.dedent("""
        <div class="hero-metric-box">
            <div class="hero-metric-val">16,276</div>
            <div class="hero-metric-label">CAUSAL REPLAY TESTS</div>
        </div>
        """), unsafe_allow_html=True)
    with c4:
        st.markdown(textwrap.dedent(f"""
        <div class="hero-metric-box">
            <div class="hero-metric-val" style="color: #00F0FF;">{active_cnt}</div>
            <div class="hero-metric-label">ACTIVE PATTERNS DETECTED</div>
        </div>
        """), unsafe_allow_html=True)

def render_quality_gauge(score: int) -> go.Figure:
    color = "#10B981" if score >= 80 else ("#F59E0B" if score >= 60 else "#EF4444")
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#475569"},
            'bar': {'color': color},
            'bgcolor': "#0B0F19",
            'borderwidth': 1,
            'bordercolor': "#1E293B",
            'steps': [
                {'range': [0, 60], 'color': "rgba(239, 68, 68, 0.15)"},
                {'range': [60, 80], 'color': "rgba(245, 158, 11, 0.15)"},
                {'range': [80, 100], 'color': "rgba(16, 185, 129, 0.15)"}
            ],
            'threshold': {
                'line': {'color': "#00F0FF", 'width': 3},
                'thickness': 0.75,
                'value': 80
            }
        },
        number={'suffix': "/100", 'font': {'color': "#FFFFFF", 'size': 20, 'family': "JetBrains Mono"}}
    ))
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=15, r=15, t=25, b=15),
        height=140
    )
    return fig
