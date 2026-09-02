import streamlit as st

def apply_terminal_theme():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
        
        /* Global Background & Font */
        .stApp {
            background-color: #0B0E14;
            color: #E2E8F0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        /* Headers */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            letter-spacing: -0.02em;
        }
        
        /* Custom Quant Card */
        .quant-card {
            background: #121722;
            border: 1px solid #1E293B;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
            margin-bottom: 20px;
        }
        
        /* Hero Metric Card */
        .hero-metric-box {
            background: linear-gradient(180deg, #161F30 0%, #0F172A 100%);
            border: 1px solid #00F0FF33;
            border-radius: 12px;
            padding: 18px;
            text-align: center;
            box-shadow: 0 0 15px rgba(0, 240, 255, 0.08);
        }
        .hero-metric-val {
            font-size: 2.4rem;
            font-weight: 800;
            font-family: 'JetBrains Mono', monospace;
            color: #00F0FF;
            line-height: 1.1;
        }
        .hero-metric-label {
            font-size: 0.78rem;
            font-weight: 600;
            color: #94A3B8;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-top: 6px;
        }
        
        /* Status Badges */
        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.75rem;
            font-weight: 700;
            font-family: 'JetBrains Mono', monospace;
            letter-spacing: 0.05em;
        }
        .badge-completed { background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid #10B98155; }
        .badge-potential { background: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid #F59E0B55; }
        .badge-forming { background: rgba(0, 240, 255, 0.15); color: #00F0FF; border: 1px solid #00F0FF55; }
        .badge-invalidated { background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid #EF444455; }
        .badge-bullish { background: rgba(16, 185, 129, 0.2); color: #10B981; font-weight: 800; }
        .badge-bearish { background: rgba(239, 68, 68, 0.2); color: #EF4444; font-weight: 800; }
        
        /* Monospace Numbers */
        .mono-num {
            font-family: 'JetBrains Mono', monospace;
        }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #080B10;
            border-right: 1px solid #1E293B;
        }
    </style>
    """, unsafe_allow_html=True)
