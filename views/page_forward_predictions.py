import streamlit as st
import pandas as pd
import textwrap
from datetime import datetime, timezone
from ui.formatting import InstrumentFormatter

def render_page():
    db = st.session_state.db
    store_type = getattr(db, 'store_type', 'SQLITE_LOCAL')
    is_persistent = getattr(db, 'is_persistent', False)
    
    # 1. Header & Storage Health Badge
    st.markdown(textwrap.dedent(f"""
    <div style="border-bottom: 1px solid #1E293B; padding-bottom: 10px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div>
                <div style="font-size: 1.6rem; font-weight: 800; color: #FFFFFF;">
                    🔮 FORWARD PREDICTIONS & OUTCOME TRACKING
                </div>
                <div style="font-size: 0.85rem; color: #94A3B8;">
                    Immutable prospective forward recording and causal outcome evaluation (STOP-FIRST Rule).
                </div>
            </div>
            <div style="margin-top: 5px;">
                <span style="font-size: 0.75rem; color: #64748B; margin-right: 6px;">FORWARD STORAGE:</span>
                <span style="background: {'rgba(16, 185, 129, 0.15)' if is_persistent else 'rgba(245, 158, 11, 0.15)'}; color: {'#10B981' if is_persistent else '#F59E0B'}; border: 1px solid {'#10B981' if is_persistent else '#F59E0B'}; padding: 4px 10px; border-radius: 4px; font-weight: 700; font-size: 0.85rem;" title="{'Forward records survive application restarts and redeployments.' if is_persistent else 'Local fallback storage may not persist on Streamlit Cloud.'}">
                    {'● PERSISTENT POSTGRES' if is_persistent else '⚠️ LOCAL SQLITE'}
                </span>
            </div>
        </div>
    </div>
    """), unsafe_allow_html=True)
    
    # 2. Forward Metrics Banner
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
    
    # 3. Filters Bar
    raw_rows = db.get_forward_predictions(limit=300)
    
    c_f1, c_f2, c_f3, c_f4, c_f5 = st.columns(5)
    with c_f1:
        flt_pair = st.multiselect("Filter Pair", ["EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD", "EURJPY", "GBPJPY", "XAUUSD"], default=[])
    with c_f2:
        flt_tf = st.multiselect("Filter TF", ["M15", "M30", "H1", "H4"], default=[])
    with c_f3:
        flt_pat = st.multiselect("Filter Pattern", ["ABCD", "GARTLEY"], default=[])
    with c_f4:
        flt_dir = st.multiselect("Filter Direction", ["BULLISH", "BEARISH"], default=[])
    with c_f5:
        flt_st = st.multiselect("Filter Status", ["ACTIVE", "TP1_HIT", "TP2_HIT", "SL_HIT", "EXPIRED"], default=[])
        
    # Apply Filters
    filtered_rows = []
    for r in raw_rows:
        if flt_pair and r.get('symbol') not in flt_pair:
            continue
        if flt_tf and r.get('timeframe') not in flt_tf:
            continue
        if flt_pat and r.get('pattern_type') not in flt_pat:
            continue
        if flt_dir and r.get('direction') not in flt_dir:
            continue
        if flt_st and r.get('status') not in flt_st:
            continue
        filtered_rows.append(r)
        
    # 4. Forward Ledger Table
    st.markdown("<div style='font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 10px;'>📋 PROSPECTIVE FORWARD LEDGER</div>", unsafe_allow_html=True)
    
    if filtered_rows:
        display_list = []
        now_dt = datetime.now(timezone.utc)
        for r in filtered_rows:
            sym = r.get('symbol', 'UNKNOWN')
            prec = InstrumentFormatter.get_precision(sym)
            dir_emoji = "▲" if r.get('direction') == 'BULLISH' else "▼"
            
            det_dt = r.get('detected_at')
            age_str = "—"
            if det_dt:
                try:
                    ts = pd.to_datetime(det_dt, utc=True)
                    delta = now_dt - ts
                    mins = int(delta.total_seconds() // 60)
                    hours = mins // 60
                    days = hours // 24
                    age_str = f"{days}d {hours % 24}h" if days > 0 else (f"{hours}h {mins % 60}m" if hours > 0 else f"{mins}m")
                except Exception:
                    pass
                    
            d_p = r.get('d_price')
            sl_p = r.get('sl')
            tp1_p = r.get('tp1')
            tp2_p = r.get('tp2')
            
            display_list.append({
                'Detected': str(r.get('detected_at', ''))[:16],
                'Pair': sym,
                'TF': r.get('timeframe'),
                'Pattern': r.get('pattern_type'),
                'Side': f"{dir_emoji} {r.get('direction')}",
                'D Price': f"{d_p:.{prec}f}" if d_p else "—",
                'SL': f"{sl_p:.{prec}f}" if sl_p else "—",
                'TP1': f"{tp1_p:.{prec}f}" if tp1_p else "—",
                'TP2': f"{tp2_p:.{prec}f}" if tp2_p else "—",
                'Status': r.get('status', 'ACTIVE'),
                'TP1 Hit At': str(r.get('tp1_hit_at', '—'))[:16] if r.get('tp1_hit_at') else "—",
                'TP2 Hit At': str(r.get('tp2_hit_at', '—'))[:16] if r.get('tp2_hit_at') else "—",
                'SL Hit At': str(r.get('sl_hit_at', '—'))[:16] if r.get('sl_hit_at') else "—",
                'Age': age_str
            })
            
        df_ledger = pd.DataFrame(display_list)
        st.dataframe(df_ledger, use_container_width=True, height=450)
    else:
        st.info("No forward predictions match active filters. Run the Active Scanner to prospectively record new completed harmonic patterns.")
        
    # 5. Storage Persistence & Architecture Notice
    st.markdown(textwrap.dedent(f"""
    <div class="quant-card" style="margin-top: 30px;">
        <div style="font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-bottom: 6px;">
            DURABLE FORWARD STORAGE ARCHITECTURE
        </div>
        <div style="font-size: 0.85rem; color: #94A3B8;">
            <b>Active Mode:</b> <code>{store_type}</code> ({'Durable PostgreSQL — Forward records persist across redeployments and restarts.' if is_persistent else 'Local SQLite — Storage is maintained on local disk.'})<br>
            <b>Provenance & Scientific Rigor:</b> Every confirmed harmonic signal creates an immutable forward prediction record with frozen coordinates, entry prices, and structural target levels. Intrabar collision resolution strictly enforces the conservative <b>STOP-FIRST</b> rule.
        </div>
    </div>
    """), unsafe_allow_html=True)
