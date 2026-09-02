import os
import sys
import streamlit as st

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.theme import apply_terminal_theme
from data.providers.factory import DataProviderFactory
from harmonic.scanner import LiveHarmonicScanner
from storage.database import HarmonicDatabase

st.set_page_config(
    page_title="Live Harmonic Pattern Scanner",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_terminal_theme()

# Initialize Session State
if 'provider_mode' not in st.session_state:
    st.session_state.provider_mode = "AUTO"
if 'data_provider' not in st.session_state:
    st.session_state.data_provider = DataProviderFactory.get_provider(st.session_state.provider_mode)
if 'scanner' not in st.session_state:
    st.session_state.scanner = LiveHarmonicScanner(st.session_state.data_provider)
if 'db' not in st.session_state:
    st.session_state.db = HarmonicDatabase()
if 'last_scan_result' not in st.session_state:
    st.session_state.last_scan_result = None

# Sidebar Navigation
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0 20px 0; border-bottom: 1px solid #1E293B; margin-bottom: 15px;">
        <div style="font-size: 1.3rem; font-weight: 800; color: #00F0FF; font-family: 'JetBrains Mono';">
            ⚡ HARMONIC TRADING LAB
        </div>
        <div style="font-size: 0.75rem; color: #94A3B8; font-weight: 500;">
            Live Harmonic Scanner
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    pages_list = [
        "01 LIVE SCANNER",
        "02 PATTERN CHART",
        "03 MARKET MATRIX",
        "04 PATTERN EXPLORER",
        "05 RESEARCH",
        "06 METHODOLOGY"
    ]
    
    # Query param routing support
    default_idx = 0
    qp = st.query_params.get("page", "")
    for i, p_name in enumerate(pages_list):
        if qp.lower() in p_name.lower().replace(" ", "_"):
            default_idx = i
            break
            
    page = st.radio(
        "NAVIGATION",
        pages_list,
        index=default_idx
    )
    
    st.markdown("<div style='margin-top: 30px; border-top: 1px solid #1E293B; padding-top: 15px;'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 0.75rem; font-weight: 700; color: #64748B;'>DATA PROVIDER CONFIG</div>", unsafe_allow_html=True)
    
    mode_select = st.selectbox("Feed Mode", ["AUTO", "MT5", "CLOUD", "DEMO"], index=["AUTO", "MT5", "CLOUD", "DEMO"].index(st.session_state.provider_mode))
    if mode_select != st.session_state.provider_mode:
        st.session_state.provider_mode = mode_select
        st.session_state.data_provider = DataProviderFactory.get_provider(mode_select)
        st.session_state.scanner = LiveHarmonicScanner(st.session_state.data_provider)
        st.rerun()
        
    p_status = st.session_state.data_provider.get_status()
    st.caption(f"Active: **{p_status.get('provider_name')}**")
    st.caption(f"State: `{p_status.get('status')}` | Live: `{p_status.get('is_live')}`")
    
    st.markdown("""
    <div style="margin-top: 40px; font-size: 0.75rem; color: #64748B; border-top: 1px solid #1E293B; padding-top: 10px;">
        <div>Version: <b>2.0.0-PROD</b></div>
        <div>Causal Replay: <b>16,276 Pass</b></div>
        <div style="margin-top: 8px;"><a href="https://github.com/karidasd/Harmonic-Trading-Lab" target="_blank" style="color: #00F0FF; text-decoration: none;">GitHub Repository ↗</a></div>
    </div>
    """, unsafe_allow_html=True)

# Page Router
if page == "01 LIVE SCANNER":
    from views.page_live_scanner import render_page
    render_page()
elif page == "02 PATTERN CHART":
    from views.page_pattern_chart import render_page
    render_page()
elif page == "03 MARKET MATRIX":
    from views.page_market_matrix import render_page
    render_page()
elif page == "04 PATTERN EXPLORER":
    from views.page_pattern_explorer import render_page
    render_page()
elif page == "05 RESEARCH":
    from views.page_research import render_page
    render_page()
elif page == "06 METHODOLOGY":
    from views.page_methodology import render_page
    render_page()
