import streamlit as st
import time
import importlib
from datetime import datetime, timezone
import ui.components
importlib.reload(ui.components)
from ui.components import render_command_header, render_hero_metrics
from ui.scanner_table import render_scanner_table
from ui.pattern_card import render_pattern_card
import ui.charts
importlib.reload(ui.charts)
from ui.charts import HarmonicChartBuilder

def render_page():
    scanner = st.session_state.scanner
    from storage.database import HarmonicDatabase
    db = st.session_state.get('db')
    if db is None or not hasattr(db, 'save_pattern'):
        db = HarmonicDatabase()
        st.session_state.db = db
    prov_status = st.session_state.data_provider.get_status()
    
    # Auto-Refresh & Top Controls
    c_flt1, c_flt2, c_flt3, c_flt4, c_flt5, c_flt6 = st.columns([3, 2, 2, 2, 2, 2])
    with c_flt1:
        symbols = st.multiselect("Pairs", ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD", "EURJPY", "GBPJPY", "XAUUSD"], default=["EURUSD", "GBPUSD", "USDJPY", "EURJPY", "GBPJPY"])
    with c_flt2:
        timeframes = st.multiselect("Timeframes", ["M15", "M30", "H1", "H4"], default=["H1", "H4", "M30"])
    with c_flt3:
        pattern_types = st.multiselect("Patterns", ["ABCD", "GARTLEY"], default=["ABCD", "GARTLEY"])
    with c_flt4:
        states = st.multiselect("States", ["COMPLETED", "POTENTIAL_D", "FORMING"], default=["COMPLETED", "POTENTIAL_D", "FORMING"])
    with c_flt5:
        auto_ref = st.checkbox("Auto-Refresh", value=False)
        ref_int = st.selectbox("Interval", ["1 min", "5 min", "15 min", "30 min"], index=1)
    with c_flt6:
        st.write("")
        st.write("")
        run_scan = st.button("⚡ SCAN NOW", type="primary", use_container_width=True)

    if run_scan or st.session_state.last_scan_result is None:
        with st.spinner("Scanning market universe causally..."):
            res = scanner.scan_market(symbols, timeframes)
            st.session_state.last_scan_result = res
            
            # Persist patterns & forward predictions
            for p in res['patterns']:
                if hasattr(db, 'save_pattern'):
                    db.save_pattern(p)
                if p.get('state') == 'COMPLETED':
                    rec = {
                        'pattern_id': p['pattern_id'],
                        'symbol': p['symbol'],
                        'timeframe': p['timeframe'],
                        'pattern_type': p['pattern_type'],
                        'direction': p['direction'],
                        'detected_at': p.get('detected_at', datetime.now(timezone.utc)),
                        'prediction_at': p.get('signal_available_time'),
                        'x_time': p.get('X_time'),
                        'a_time': p.get('A_time'),
                        'b_time': p.get('B_time'),
                        'c_time': p.get('C_time'),
                        'd_time': p.get('D_time'),
                        'x_price': p.get('X_price'),
                        'a_price': p.get('A_price'),
                        'b_price': p.get('B_price'),
                        'c_price': p.get('C_price'),
                        'd_price': p.get('D_price'),
                        'prediction_price': p.get('current_price'),
                        'sl': p.get('structural_stop'),
                        'tp1': p.get('target_1'),
                        'tp2': p.get('target_2'),
                        'p_tp1': p.get('p_tp1'),
                        'p_tp2': p.get('p_tp2'),
                        'confidence': p.get('confidence', 'NO_EDGE'),
                        'model_name': p.get('model_name', 'None'),
                        'model_version': p.get('model_version', 'NO_EDGE_NOT_DEPLOYED'),
                        'data_provider': prov_status.get('provider_name'),
                        'data_mode': prov_status.get('mode'),
                        'status': p.get('forward_status', 'ACTIVE')
                    }
                    if hasattr(db, 'insert_prediction'):
                        db.insert_prediction(rec)
                    elif hasattr(db, 'insert_forward_prediction'):
                        db.insert_forward_prediction(rec)
                    
            for ev in res['events']:
                if hasattr(db, 'record_event'):
                    db.record_event(ev.to_dict() if hasattr(ev, 'to_dict') else ev)
                
            try:
                if hasattr(db, 'record_scanner_run'):
                    db.record_scanner_run(
                        prov_status.get('provider_name', 'FEED'),
                        prov_status.get('mode', 'DEMO'),
                        res['markets_scanned'],
                        len(res['patterns']),
                        res['scan_duration_sec']
                    )
            except Exception:
                pass

    res = st.session_state.last_scan_result
    all_patterns = res['patterns'] if res else []
    
    # Filter Patterns
    filtered_patterns = [
        p for p in all_patterns
        if p['pattern_type'] in pattern_types and p['state'] in states
    ]
    
    st_status = {'is_persistent': getattr(db, 'is_persistent', False)}
    render_command_header(prov_status, res.get('timestamp', datetime.now(timezone.utc)), res.get('markets_scanned', 0), scan_res=res, storage_status=st_status)
    render_hero_metrics(len(filtered_patterns), res.get('markets_scanned', 0))
    
    # New Pattern Alert Banner
    new_cnt = res.get('new_patterns_count', 0) if res else 0
    if new_cnt > 0:
        st.success(f"⚡ **NEW HARMONIC STRUCTURES DETECTED**: {new_cnt} newly formed/completed patterns observed in the current scan.")
        
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    
    # Main 2-Column Split: Active Scanner Table (Left) + Interactive Quick Inspector (Right)
    col_table, col_preview = st.columns([7, 5])
    
    with col_table:
        st.markdown("<div style='font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 10px;'>📊 DETECTED HARMONIC PATTERNS</div>", unsafe_allow_html=True)
        if filtered_patterns:
            df_table = render_scanner_table(filtered_patterns)
            st.dataframe(df_table, use_container_width=True, height=450)
        else:
            st.info("No harmonic patterns detected matching active filters. Try selecting more pairs or timeframes.")
            
    with col_preview:
        st.markdown("<div style='font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 10px;'>🎯 PATTERN INSPECTOR</div>", unsafe_allow_html=True)
        if filtered_patterns:
            pat_options = [f"{p['symbol']} {p['timeframe']} - {p['direction']} {p['pattern_type']} ({p['state']}) [Q:{p['quality_score']}]" for p in filtered_patterns]
            sel_idx = st.selectbox("Select Signal to Inspect", range(len(pat_options)), format_func=lambda i: pat_options[i])
            sel_pat = filtered_patterns[sel_idx]
            
            render_pattern_card(sel_pat)
            
            # View Current Chart Navigation Button
            if st.button("📈 VIEW CURRENT CHART", type="secondary", use_container_width=True):
                st.session_state.selected_symbol = sel_pat['symbol']
                st.session_state.selected_timeframe = sel_pat['timeframe']
                st.session_state.nav_target_page = "02 LIVE MARKET"
                st.rerun()
            
            # Mini Quick Chart Preview (ensure bars span through current market)
            df_chart = st.session_state.data_provider.get_ohlcv(sel_pat['symbol'], sel_pat['timeframe'], bars=300)
            if df_chart is not None and not df_chart.empty:
                fig = HarmonicChartBuilder.build_harmonic_chart(df_chart, sel_pat, show_levels=True, show_current_price=True)
                fig.update_layout(height=290, margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("<div class='quant-card' style='text-align: center; color: #64748B;'>Select an active pattern from the table to preview geometry, predictions, and research levels.</div>", unsafe_allow_html=True)
