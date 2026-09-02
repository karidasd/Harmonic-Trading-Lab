import streamlit as st
from datetime import datetime, timezone
from ui.components import render_command_header, render_hero_metrics
from ui.scanner_table import render_scanner_table
from ui.pattern_card import render_pattern_card
from ui.charts import HarmonicChartBuilder

def render_page():
    scanner = st.session_state.scanner
    db = st.session_state.db
    prov_status = st.session_state.data_provider.get_status()
    
    # Filter Bar
    c_sym, c_tf, c_pat, c_st, c_scan = st.columns([3, 2, 2, 2, 2])
    with c_sym:
        symbols = st.multiselect("Pairs", ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD", "EURJPY", "GBPJPY", "XAUUSD"], default=["EURUSD", "GBPUSD", "USDJPY", "EURJPY", "GBPJPY"])
    with c_tf:
        timeframes = st.multiselect("Timeframes", ["M15", "M30", "H1", "H4"], default=["H1", "H4", "M30"])
    with c_pat:
        pattern_types = st.multiselect("Patterns", ["ABCD", "GARTLEY"], default=["ABCD", "GARTLEY"])
    with c_st:
        states = st.multiselect("States", ["COMPLETED", "POTENTIAL_D", "FORMING"], default=["COMPLETED", "POTENTIAL_D", "FORMING"])
    with c_scan:
        st.write("")
        st.write("")
        run_scan = st.button("⚡ SCAN NOW", type="primary", use_container_width=True)

    if run_scan or st.session_state.last_scan_result is None:
        with st.spinner("Scanning market universe causally..."):
            res = scanner.scan_market(symbols, timeframes)
            st.session_state.last_scan_result = res
            db.save_patterns(res['patterns'])
            db.save_events(res['events'])
            db.record_scanner_run(prov_status.get('mode', 'DEMO'), res['markets_scanned'], len(res['patterns']), res['scan_duration_sec'])
            
    res = st.session_state.last_scan_result
    all_patterns = res['patterns'] if res else []
    
    # Filter Patterns
    filtered_patterns = [
        p for p in all_patterns
        if p['pattern_type'] in pattern_types and p['state'] in states
    ]
    
    render_command_header(prov_status, res.get('timestamp', datetime.now(timezone.utc)), res.get('markets_scanned', 0), scan_res=res)
    render_hero_metrics(len(filtered_patterns), res.get('markets_scanned', 0))
    
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    
    # Main 2-Column Split: Active Scanner Table (Left) + Interactive Quick Inspector (Right)
    col_table, col_preview = st.columns([7, 5])
    
    with col_table:
        st.markdown("<div style='font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 10px;'>📊 ACTIVE HARMONIC SIGNALS</div>", unsafe_allow_html=True)
        if filtered_patterns:
            df_table = render_scanner_table(filtered_patterns)
            st.dataframe(df_table, use_container_width=True, height=420)
        else:
            st.info("No harmonic patterns detected matching active filters. Try selecting more pairs or timeframes.")
            
    with col_preview:
        st.markdown("<div style='font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 10px;'>🎯 PATTERN INSPECTOR</div>", unsafe_allow_html=True)
        if filtered_patterns:
            pat_options = [f"{p['symbol']} {p['timeframe']} - {p['direction']} {p['pattern_type']} ({p['state']}) [Q:{p['quality_score']}]" for p in filtered_patterns]
            sel_idx = st.selectbox("Select Signal to Inspect", range(len(pat_options)), format_func=lambda i: pat_options[i])
            sel_pat = filtered_patterns[sel_idx]
            
            render_pattern_card(sel_pat)
            
            # Mini Quick Chart Preview
            df_chart = st.session_state.data_provider.get_ohlcv(sel_pat['symbol'], sel_pat['timeframe'], bars=120)
            if df_chart is not None and not df_chart.empty:
                fig = HarmonicChartBuilder.build_harmonic_chart(df_chart, sel_pat, show_levels=True)
                fig.update_layout(height=280, margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.markdown("<div class='quant-card' style='text-align: center; color: #64748B;'>Select an active pattern from the table to preview geometry and research levels.</div>", unsafe_allow_html=True)
