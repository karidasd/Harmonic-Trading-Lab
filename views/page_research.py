import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import textwrap
import json
import os
from research.research_metrics import ResearchDataLoader
from ui.components import render_win_rate_gauge

def render_page():
    res_data = ResearchDataLoader.load_frozen_results()
    val_fx = res_data.get('validation_baseline_fx_only', {})
    
    st.markdown(textwrap.dedent("""
    <div style="border-bottom: 1px solid #1E293B; padding-bottom: 10px; margin-bottom: 20px;">
        <div style="font-size: 1.6rem; font-weight: 800; color: #FFFFFF;">
            🔬 HARMONIC EDGE RESEARCH & BASELINE VALIDATION
        </div>
        <div style="font-size: 0.85rem; color: #94A3B8;">
            Frozen Baseline Out-of-Sample Economic Results (Protocol SHA256: 1df0110e1870be701734b952a6a201fa4fc9beef219fd99620a628a774c92482)
        </div>
    </div>
    """), unsafe_allow_html=True)
    
    # 1. Hero Visualizer Section
    c_gauge, c_details = st.columns([5, 7])
    
    with c_gauge:
        fig_gauge = render_win_rate_gauge(
            gross_wr=val_fx.get('gross_win_rate_pct', 71.78),
            avg_win_r=val_fx.get('avg_gross_winner_R', 0.401),
            avg_loss_r=val_fx.get('avg_gross_loser_R', -1.000)
        )
        st.plotly_chart(fig_gauge, use_container_width=True)
        
    with c_details:
        st.markdown(textwrap.dedent("""
        <div class="quant-card">
            <div style="font-size: 1.2rem; font-weight: 800; color: #FFFFFF; margin-bottom: 6px;">
                71.8% GROSS HISTORICAL WIN RATE
            </div>
            <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 15px;">
                Verified across 202 frozen FX out-of-sample validation trades under causal, non-repainting detection.
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px; font-family: 'JetBrains Mono'; font-size: 0.85rem;">
                <div style="background: #080B10; padding: 10px; border-radius: 6px;">
                    <div style="color: #64748B; font-size: 0.75rem;">AVERAGE GROSS WINNER</div>
                    <div style="color: #10B981; font-weight: 700; font-size: 1.1rem;">+0.401R</div>
                </div>
                <div style="background: #080B10; padding: 10px; border-radius: 6px;">
                    <div style="color: #64748B; font-size: 0.75rem;">AVERAGE GROSS LOSER</div>
                    <div style="color: #EF4444; font-weight: 700; font-size: 1.1rem;">-1.000R</div>
                </div>
                <div style="background: #080B10; padding: 10px; border-radius: 6px;">
                    <div style="color: #64748B; font-size: 0.75rem;">PAYOFF RATIO (WIN / LOSS)</div>
                    <div style="color: #00F0FF; font-weight: 700; font-size: 1.1rem;">0.401 : 1</div>
                </div>
                <div style="background: #080B10; padding: 10px; border-radius: 6px;">
                    <div style="color: #64748B; font-size: 0.75rem;">IMPLIED BREAK-EVEN WR</div>
                    <div style="color: #F59E0B; font-weight: 700; font-size: 1.1rem;">71.40%</div>
                </div>
            </div>
        </div>
        """), unsafe_allow_html=True)
        
    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)
    
    # 2. Detailed Economic Transparency Section
    st.markdown(textwrap.dedent("""
    <div class="quant-card">
        <div style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 10px;">
            📊 AFTER TRANSACTION COSTS (TRANSPARENT SCIENTIFIC REPORTING)
        </div>
        <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 15px;">
            Harmonic patterns exhibit high gross directional accuracy (71.8%), but target geometry (T1 = 0.382 AD) produces asymmetric payoffs (0.40R win vs 1.00R loss). When realistic ECN spread, slippage, and commissions (0.083R) are deducted, net expectancy turns slightly negative (-0.078R).
        </div>
        
        <table style="width: 100%; text-align: left; border-collapse: collapse; font-family: 'JetBrains Mono'; font-size: 0.85rem;">
            <thead>
                <tr style="border-bottom: 1px solid #334155; color: #94A3B8;">
                    <th style="padding: 8px;">Metric</th>
                    <th style="padding: 8px;">Gross Diagnostic (C0)</th>
                    <th style="padding: 8px;">Realistic Synthetic Friction (C1)</th>
                    <th style="padding: 8px;">Stress Cost Model (C2)</th>
                </tr>
            </thead>
            <tbody>
                <tr style="border-bottom: 1px solid #1E293B;">
                    <td style="padding: 8px; color: #E2E8F0;">Sample Size (N)</td>
                    <td style="padding: 8px;">202 trades</td>
                    <td style="padding: 8px;">202 trades</td>
                    <td style="padding: 8px;">202 trades</td>
                </tr>
                <tr style="border-bottom: 1px solid #1E293B;">
                    <td style="padding: 8px; color: #E2E8F0;">Win Rate</td>
                    <td style="padding: 8px; color: #10B981;">71.78%</td>
                    <td style="padding: 8px; color: #00F0FF;">62.38%</td>
                    <td style="padding: 8px; color: #F59E0B;">58.91%</td>
                </tr>
                <tr style="border-bottom: 1px solid #1E293B;">
                    <td style="padding: 8px; color: #E2E8F0;">Mean Expectancy (R)</td>
                    <td style="padding: 8px; color: #10B981;">+0.0054R</td>
                    <td style="padding: 8px; color: #EF4444;">-0.0777R</td>
                    <td style="padding: 8px; color: #EF4444;">-0.1096R</td>
                </tr>
                <tr style="border-bottom: 1px solid #1E293B;">
                    <td style="padding: 8px; color: #E2E8F0;">Profit Factor</td>
                    <td style="padding: 8px;">1.04</td>
                    <td style="padding: 8px;">0.75</td>
                    <td style="padding: 8px;">0.67</td>
                </tr>
                <tr>
                    <td style="padding: 8px; color: #E2E8F0;">95% Bootstrap CI</td>
                    <td style="padding: 8px;">[-0.094R, +0.095R]</td>
                    <td style="padding: 8px;">[-0.177R, +0.022R]</td>
                    <td style="padding: 8px;">[-0.206R, -0.013R]</td>
                </tr>
            </tbody>
        </table>
    </div>
    """), unsafe_allow_html=True)
    
    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)
    
    # 3. Prediction Model Walk-Forward Validation & Acceptance Gate Section
    st.markdown(textwrap.dedent("""
    <div class="quant-card">
        <div style="font-size: 1.1rem; font-weight: 700; color: #FFFFFF; margin-bottom: 10px;">
            🤖 PREDICTION MODEL WALK-FORWARD RESEARCH & ACCEPTANCE AUDIT
        </div>
        <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 15px;">
            Rigorous evaluation of point-in-time machine learning models predicting <code>P(TP1 before SL)</code> across chronological walk-forward splits on pre-2025 Forex market data.
        </div>
    </div>
    """), unsafe_allow_html=True)
    
    # Load model metadata
    meta_path = "LIVE_HARMONIC_SCANNER/models/model_metadata.json"
    if not os.path.exists(meta_path):
        meta_path = "models/model_metadata.json"
        
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            
        gate_pass = meta.get('gate_passed', False)
        
        if not gate_pass:
            st.error("⚠️ **MODEL NOT DEPLOYED — NO ROBUST OOS PREDICTIVE EDGE FOUND**")
            st.markdown("""
            > **Scientific Integrity Notice**: The walk-forward machine learning models evaluated on pre-2025 point-in-time features failed to beat the naive base-rate Brier score out-of-sample. To maintain strict quantitative rigor, **no fabricated prediction probabilities are displayed in the live scanner**. The scanner operates purely on causal geometric detection.
            """)
        else:
            st.success("✅ **MODEL DEPLOYED — VALIDATED OOS PREDICTIVE EDGE**")
            
        c_m1, c_m2, c_m3 = st.columns(3)
        with c_m1:
            st.metric("Model Architecture", meta.get('model_name', 'HistGradientBoosting'))
            st.metric("Dataset Size (N)", meta.get('dataset_size_n', 289))
        with c_m2:
            st.metric("Out-of-Sample ROC-AUC", f"{meta.get('best_model', {}).get('oos_auc', 0.50):.4f}")
            st.metric("Model Version", meta.get('model_version', 'v1'))
        with c_m3:
            st.metric("OOS Brier Score", f"{meta.get('best_model', {}).get('oos_brier', 0.1621):.4f}")
            st.metric("Naive Climatology Brier", f"{meta.get('naive_baseline_brier', 0.1562):.4f}")
            
        # Probability Bucket Breakdown Table
        st.markdown("<div style='font-size: 0.95rem; font-weight: 700; color: #FFFFFF; margin-top: 15px; margin-bottom: 8px;'>Probability Bucket Reliability Breakdown</div>", unsafe_allow_html=True)
        buckets = meta.get('bucket_table', [])
        if buckets:
            df_b = pd.DataFrame(buckets)
            st.dataframe(df_b, use_container_width=True)
