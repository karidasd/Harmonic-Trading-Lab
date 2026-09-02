import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timezone
from typing import Dict, Any

def render_command_header(provider_status: Dict[str, Any], last_scan_time: datetime, markets_count: int, scan_res: Dict[str, Any] = None):
    p_name = provider_status.get('provider_name', 'DEMO FEED')
    mode = provider_status.get('mode', 'DEMO')
    status = provider_status.get('status', 'ONLINE')
    
    status_color = "#10B981" if status in ["ONLINE", "CONNECTED"] else "#F59E0B"
    mode_badge = f"<span class='badge badge-completed'>{mode}</span>" if mode == "LIVE" else (f"<span class='badge badge-potential'>{mode}</span>" if mode == "CLOUD" else f"<span class='badge badge-forming'>{mode}</span>")
    
    latency_str = ""
    if scan_res:
        f_lat = scan_res.get('data_fetch_latency_sec', 0.0)
        d_lat = scan_res.get('detection_latency_sec', 0.0)
        t_lat = scan_res.get('scan_duration_sec', 0.0)
        latency_str = f" | Latency: [Fetch: {f_lat:.2f}s | Detect: {d_lat:.2f}s | Total: {t_lat:.2f}s]"
        
    st.markdown(f"""
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
            <div><span style="color: {status_color};">●</span> {p_name} {mode_badge}</div>
            <div style="color: #64748B; margin-top: 4px;">UTC: {datetime.now(timezone.utc).strftime('%H:%M:%S')} | Scanned: {markets_count} Markets{latency_str}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_hero_metrics(active_cnt: int, markets_cnt: int):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""
        <div class="hero-metric-box">
            <div class="hero-metric-val">71.8%</div>
            <div class="hero-metric-label">GROSS HISTORICAL WR</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="hero-metric-box">
            <div class="hero-metric-val" style="color: #10B981;">0</div>
            <div class="hero-metric-label">REPAINT FAILURES</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown("""
        <div class="hero-metric-box">
            <div class="hero-metric-val">16,276</div>
            <div class="hero-metric-label">CAUSAL REPLAY TESTS</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="hero-metric-box">
            <div class="hero-metric-val" style="color: #F59E0B;">{active_cnt}</div>
            <div class="hero-metric-label">ACTIVE PATTERNS DETECTED</div>
        </div>
        """, unsafe_allow_html=True)

def render_win_rate_gauge(gross_wr: float = 71.78, avg_win_r: float = 0.401, avg_loss_r: float = -1.000) -> go.Figure:
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=gross_wr,
        number={'suffix': "%", 'font': {'size': 44, 'family': "JetBrains Mono", 'color': "#00F0FF"}},
        title={'text': "GROSS HISTORICAL WIN RATE<br><span style='font-size:0.8em;color:#94A3B8'>Frozen FX Validation Baseline (N=202)</span>", 'font': {'size': 14, 'family': "Inter"}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#334155"},
            'bar': {'color': "#00F0FF"},
            'bgcolor': "#0F172A",
            'borderwidth': 2,
            'bordercolor': "#1E293B",
            'steps': [
                {'range': [0, 50], 'color': "rgba(239, 68, 68, 0.15)"},
                {'range': [50, 71.4], 'color': "rgba(245, 158, 11, 0.15)"},
                {'range': [71.4, 100], 'color': "rgba(16, 185, 129, 0.15)"}
            ],
            'threshold': {
                'line': {'color': "#EF4444", 'width': 3},
                'thickness': 0.75,
                'value': 71.4 # Break-even threshold
            }
        }
    ))
    fig.update_layout(
        paper_bgcolor="#0B0E14",
        font={'color': "#E2E8F0", 'family': "Inter"},
        height=280,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    return fig
