import streamlit as st
import pandas as pd
import numpy as np
import textwrap
import importlib
from datetime import datetime, timezone, timedelta
from ui.formatting import InstrumentFormatter
import ui.charts
importlib.reload(ui.charts)
from ui.charts import HarmonicChartBuilder
from prediction.outcome_tracker import OutcomeTracker

def calculate_data_freshness(last_time: pd.Timestamp, timeframe: str) -> dict:
    if last_time is None:
        return {'age_str': 'Unknown', 'status': 'UNKNOWN', 'is_stale': False, 'is_closed': False}
        
    now = datetime.now(timezone.utc)
    if last_time.tz is None:
        last_dt = last_time.tz_localize('UTC')
    else:
        last_dt = last_time.tz_convert('UTC')
        
    delta = now - last_dt
    total_sec = max(0, delta.total_seconds())
    mins = int(total_sec // 60)
    hours = int(mins // 60)
    days = int(hours // 24)
    
    if days > 0:
        age_str = f"{days}d {hours % 24}h {mins % 60}m"
    elif hours > 0:
        age_str = f"{hours}h {mins % 60}m"
    else:
        age_str = f"{mins}m"
        
    # Check if weekend (Forex market closed Saturday/Sunday)
    weekday = now.weekday()
    # Market closes Friday ~21:00 UTC and opens Sunday ~21:00 UTC
    is_weekend = (weekday == 5) or (weekday == 6 and now.hour < 21) or (weekday == 4 and now.hour >= 22)
    
    tf_min_map = {'M15': 15, 'M30': 30, 'H1': 60, 'H4': 240, 'D1': 1440}
    bar_mins = tf_min_map.get(timeframe, 60)
    
    if is_weekend or days >= 2:
        status = 'MARKET CLOSED / LAST AVAILABLE DATA'
        is_closed = True
        is_stale = False
    elif mins > (bar_mins * 3.5):
        status = 'STALE DATA'
        is_stale = True
        is_closed = False
    else:
        status = 'DATA CURRENT'
        is_stale = False
        is_closed = False
        
    return {
        'age_str': age_str,
        'status': status,
        'is_stale': is_stale,
        'is_closed': is_closed,
        'last_dt_str': last_dt.strftime('%Y-%m-%d %H:%M UTC')
    }

def render_page():
    provider = st.session_state.data_provider
    scanner = st.session_state.scanner
    from storage.database import HarmonicDatabase
    db = st.session_state.get('db')
    if db is None or not hasattr(db, 'insert_prediction'):
        db = HarmonicDatabase()
        st.session_state.db = db
    prov_status = provider.get_status()
    
    # Check for query params / session state selection from Active Scanner
    default_sym = st.session_state.get('selected_symbol', 'EURUSD')
    default_tf = st.session_state.get('selected_timeframe', 'H1')
    
    all_syms = ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD", "EURJPY", "GBPJPY", "XAUUSD"]
    all_tfs = ["M15", "M30", "H1", "H4"]
    
    sym_idx = all_syms.index(default_sym) if default_sym in all_syms else 0
    tf_idx = all_tfs.index(default_tf) if default_tf in all_tfs else 2
    
    # 1. Page Header
    st.markdown(textwrap.dedent("""
    <div style="border-bottom: 1px solid #1E293B; padding-bottom: 10px; margin-bottom: 15px;">
        <div style="font-size: 1.6rem; font-weight: 800; color: #FFFFFF;">
            📈 LIVE MARKET
        </div>
        <div style="font-size: 0.85rem; color: #94A3B8;">
            Current Forex Market • Causal Harmonic Overlay & Real-Time Inspection
        </div>
    </div>
    """), unsafe_allow_html=True)
    
    # 2. Controls Top Bar
    c_s1, c_s2, c_s3, c_s4, c_s5 = st.columns([3, 2, 2, 2, 2])
    with c_s1:
        sel_symbol = st.selectbox("Pair", all_syms, index=sym_idx)
        st.session_state.selected_symbol = sel_symbol
    with c_s2:
        sel_tf = st.selectbox("Timeframe", all_tfs, index=tf_idx)
        st.session_state.selected_timeframe = sel_tf
    with c_s3:
        auto_ref = st.checkbox("Auto-Refresh", value=False)
        ref_int = st.selectbox("Interval", ["1 min", "5 min", "15 min", "30 min"], index=1)
    with c_s4:
        bars_count = st.selectbox("Candles", [150, 200, 250, 300], index=1)
    with c_s5:
        st.write("")
        st.write("")
        btn_refresh = st.button("⚡ REFRESH NOW", type="primary", use_container_width=True)

    # 3. Fetch Market Data
    now_utc = datetime.now(timezone.utc)
    df = provider.get_ohlcv(sel_symbol, sel_tf, bars=bars_count)
    
    if df is None or df.empty or len(df) < 15:
        st.error(f"⚠️ **MARKET DATA TEMPORARILY UNAVAILABLE** for `{sel_symbol}` on `{sel_tf}`.")
        return

    last_candle_time = df.index[-1]
    last_price = float(df['close'].iloc[-1])
    prec = InstrumentFormatter.get_precision(sel_symbol)
    freshness = calculate_data_freshness(last_candle_time, sel_tf)
    
    # 4. Mode Label Resolution
    mode_raw = prov_status.get('mode', 'DEMO')
    if mode_raw == 'CLOUD':
        mode_label = "CLOUD / DELAYED"
        mode_color = "#38BDF8"
    elif mode_raw == 'MT5' and prov_status.get('is_live', False):
        mode_label = "MT5 LIVE"
        mode_color = "#10B981"
    else:
        mode_label = "DEMO DATA"
        mode_color = "#F59E0B"
        
    # 5. Top Data Freshness Bar
    st.markdown(textwrap.dedent(f"""
    <div class="quant-card" style="margin-bottom: 15px; padding: 12px 18px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; font-family: 'JetBrains Mono'; font-size: 0.85rem;">
            <div>
                <span style="font-size: 1.2rem; font-weight: 800; color: #FFFFFF;">{sel_symbol}</span>
                <span style="background: #1E293B; padding: 3px 8px; border-radius: 4px; color: #00F0FF; margin-left: 6px;">{sel_tf}</span>
            </div>
            <div>
                <span style="color: #64748B;">PROVIDER:</span>
                <span style="color: #E2E8F0; font-weight: 600;">{prov_status.get('provider_name')}</span>
                <span style="background: rgba(255,255,255,0.06); color: {mode_color}; padding: 2px 6px; border-radius: 4px; font-weight: 700; margin-left: 4px;">{mode_label}</span>
            </div>
            <div>
                <span style="color: #64748B;">LAST CANDLE:</span>
                <span style="color: #E2E8F0;">{freshness['last_dt_str']}</span>
            </div>
            <div>
                <span style="color: #64748B;">DATA AGE:</span>
                <span style="color: {'#EF4444' if freshness['is_stale'] else '#10B981'}; font-weight: 700;">{freshness['age_str']}</span>
            </div>
            <div>
                <span style="color: #64748B;">LAST PRICE:</span>
                <span style="color: #00F0FF; font-weight: 800; font-size: 1.1rem;">{last_price:.{prec}f}</span>
            </div>
        </div>
    </div>
    """), unsafe_allow_html=True)
    
    if freshness['is_closed']:
        st.info(f"ℹ️ **{freshness['status']}**: The market is currently closed or displaying the latest available settlement session candles.")
    elif freshness['is_stale']:
        st.warning(f"⚠️ **{freshness['status']}**: Latest received candle is {freshness['age_str']} old.")

    # 6. Run Causal Harmonic Detector on the Chart
    patterns = scanner.detector.scan_dataframe(df, sel_symbol, sel_tf)
    
    # Synchronize forward predictions for completed patterns
    for p in patterns:
        if p.get('state') == 'COMPLETED':
            rec = {
                'pattern_id': p['pattern_id'],
                'symbol': p['symbol'],
                'timeframe': p['timeframe'],
                'pattern_type': p['pattern_type'],
                'direction': p['direction'],
                'detected_at': p.get('detected_at', now_utc),
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
                'prediction_price': p.get('current_price', last_price),
                'sl': p.get('structural_stop'),
                'tp1': p.get('target_1'),
                'tp2': p.get('target_2'),
                'p_tp1': None,
                'p_tp2': None,
                'confidence': 'NO_EDGE',
                'model_name': 'None',
                'model_version': 'NO_EDGE_NOT_DEPLOYED',
                'data_provider': prov_status.get('provider_name'),
                'data_mode': mode_label,
                'status': 'ACTIVE'
            }
            if hasattr(db, 'insert_prediction'):
                db.insert_prediction(rec)
            elif hasattr(db, 'insert_forward_prediction'):
                db.insert_forward_prediction(rec)
            
            # Evaluate outcome if forward bars exist
            outcome = OutcomeTracker.evaluate_outcome(p, df)
            p['forward_status'] = outcome.get('status', 'ACTIVE')
        else:
            p['forward_status'] = p.get('state')

    # 7. Pattern Selection & Banner
    selected_pattern = None
    if patterns:
        if len(patterns) == 1:
            selected_pattern = patterns[0]
            st.success(f"⚡ **HARMONIC PATTERN ACTIVE**: `{selected_pattern['direction']}` `{selected_pattern['pattern_type']}` (`{selected_pattern['state']}`) detected.")
        else:
            pat_labels = [f"{p['direction']} {p['pattern_type']} ({p['state']}) [Q:{p['quality_score']}]" for p in patterns]
            c_sel_pat, _ = st.columns([5, 7])
            with c_sel_pat:
                p_idx = st.selectbox("Detected Harmonic Overlays", range(len(patterns)), format_func=lambda i: pat_labels[i])
                selected_pattern = patterns[p_idx]
    else:
        st.info("ℹ️ **NO ACTIVE HARMONIC PATTERN**: Displaying current candlestick price action.")
        
    # 8. Main Chart & Inspector Layout
    col_chart, col_insp = st.columns([8, 4])
    
    with col_chart:
        fig = HarmonicChartBuilder.build_harmonic_chart(
            df=df,
            pattern=selected_pattern,
            show_levels=True,
            show_current_price=True,
            height=620
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Last Refreshed: `{now_utc.strftime('%H:%M:%S UTC')}` | Showing {len(df)} candles through current market.")
        
    with col_insp:
        st.markdown("<div style='font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 10px;'>🎯 PATTERN INSPECTOR</div>", unsafe_allow_html=True)
        if selected_pattern:
            dir_emoji = "🟢" if selected_pattern.get('direction') == 'BULLISH' else "🔴"
            with st.container(border=True):
                st.markdown(f"### {sel_symbol} `{sel_tf}`")
                st.markdown(f"{dir_emoji} **{selected_pattern.get('direction')} {selected_pattern.get('pattern_type')}**")
                st.markdown(f"**State:** `{selected_pattern.get('state')}` | **Quality:** `{selected_pattern.get('quality_score')}/100`")
                
                st.divider()
                
                c_p1, c_p2 = st.columns(2)
                with c_p1:
                    st.caption("D PRICE")
                    st.markdown(f"`{selected_pattern.get('D_price', 0):.{prec}f}`")
                with c_p2:
                    st.caption("CURRENT MARKET")
                    st.markdown(f"`{last_price:.{prec}f}`")
                    
                prz_l = selected_pattern.get('prz_low', 0)
                prz_h = selected_pattern.get('prz_high', 0)
                st.caption("PRZ ZONE")
                st.markdown(f"`{prz_l:.{prec}f} – {prz_h:.{prec}f}`")
                
                st.divider()
                
                st.caption("RESEARCH TRADE LEVELS")
                sl = selected_pattern.get('structural_stop', 0)
                tp1 = selected_pattern.get('target_1', 0)
                tp2 = selected_pattern.get('target_2', 0)
                
                st.markdown(f"🔴 **Research SL:** `{sl:.{prec}f}`")
                st.markdown(f"🟢 **Research TP1:** `{tp1:.{prec}f}`")
                st.markdown(f"🟢 **Research TP2:** `{tp2:.{prec}f}`")
                
                st.divider()
                
                st.caption("ACTIVE PREDICTION ENGINE")
                st.markdown("**P(TP1 before SL):** `Not Validated`")
                st.markdown("**P(TP2 before SL):** `Not Validated`")
                st.caption("Model Version: `NO_EDGE_NOT_DEPLOYED` (Zero fabricated probabilities)")
                
                st.divider()
                
                st.caption(f"FORWARD STATUS: **{selected_pattern.get('forward_status', selected_pattern.get('state'))}**")
        else:
            st.markdown(textwrap.dedent(f"""
            <div class="quant-card" style="text-align: center; padding: 40px 15px;">
                <div style="font-size: 2.5rem; margin-bottom: 10px;">📊</div>
                <div style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 8px;">
                    NO ACTIVE PATTERN
                </div>
                <div style="font-size: 0.85rem; color: #64748B;">
                    No causal harmonic geometry currently detected on {sel_symbol} {sel_tf}. Market price action is streaming directly from {prov_status.get('provider_name')}.
                </div>
            </div>
            """), unsafe_allow_html=True)
