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
    page_title="Harmonic Trading Lab — Active Scanner & Live Market",
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
if 'db' not in st.session_state or not hasattr(st.session_state.db, 'insert_prediction'):
    st.session_state.db = HarmonicDatabase()
if 'last_scan_result' not in st.session_state:
    st.session_state.last_scan_result = None
if 'nav_target_page' not in st.session_state:
    st.session_state.nav_target_page = None

# Sidebar Navigation
with st.sidebar:
    st.markdown("""
    <div style="padding: 10px 0 20px 0; border-bottom: 1px solid #1E293B; margin-bottom: 15px;">
        <div style="font-size: 1.3rem; font-weight: 800; color: #00F0FF; font-family: 'JetBrains Mono';">
            ⚡ HARMONIC TRADING LAB
        </div>
        <div style="font-size: 0.75rem; color: #94A3B8; font-weight: 500;">
            Active Harmonic Scanner & Research
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    pages_list = [
        "01 ACTIVE SCANNER",
        "02 LIVE MARKET",
        "03 PATTERN CHART",
        "04 MARKET MATRIX",
        "05 FORWARD PREDICTIONS",
        "06 PATTERN EXPLORER",
        "07 RESEARCH",
        "08 METHODOLOGY"
    ]
    
    # Query param or session state routing support
    default_idx = 0
    if st.session_state.nav_target_page and st.session_state.nav_target_page in pages_list:
        default_idx = pages_list.index(st.session_state.nav_target_page)
        st.session_state.nav_target_page = None
    else:
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
        <div>Version: <b>2.2.0-PROD</b> (Harmonic Trading Lab v2.2)</div>
        <div>Causal Replay: <b>16,276 Pass</b></div>
        <div style="margin-top: 8px;"><a href="https://github.com/karidasd/Harmonic-Trading-Lab" target="_blank" style="color: #00F0FF; text-decoration: none;">GitHub Repository ↗</a></div>
    </div>
    """, unsafe_allow_html=True)

import importlib

# Page Router
if page == "01 ACTIVE SCANNER":
    import views.page_live_scanner
    importlib.reload(views.page_live_scanner)
    views.page_live_scanner.render_page()
elif page == "02 LIVE MARKET":
    import views.page_live_market
    importlib.reload(views.page_live_market)
    views.page_live_market.render_page()
elif page == "03 PATTERN CHART":
    import views.page_pattern_chart
    importlib.reload(views.page_pattern_chart)
    views.page_pattern_chart.render_page()
elif page == "04 MARKET MATRIX":
    import views.page_market_matrix
    importlib.reload(views.page_market_matrix)
    views.page_market_matrix.render_page()
elif page == "05 FORWARD PREDICTIONS":
    import views.page_forward_predictions
    importlib.reload(views.page_forward_predictions)
    views.page_forward_predictions.render_page()
elif page == "06 PATTERN EXPLORER":
    import views.page_pattern_explorer
    importlib.reload(views.page_pattern_explorer)
    views.page_pattern_explorer.render_page()
elif page == "07 RESEARCH":
    import views.page_research
    importlib.reload(views.page_research)
    views.page_research.render_page()
elif page == "08 METHODOLOGY":
    import views.page_methodology
    importlib.reload(views.page_methodology)
    views.page_methodology.render_page()
