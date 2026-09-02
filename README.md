# ⚡ HARMONIC TRADING LAB

### Live AB=CD & Gartley Harmonic Pattern Scanner

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io/karidasd/harmonic-trading-lab/main/dashboard.py)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg)](https://streamlit.io)
[![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-3F4F75.svg)](https://plotly.com)
[![Tests](https://img.shields.io/badge/Causal%20%26%20Market%20Tests-25%2F25%20PASS-10B981.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 71.8% GROSS HISTORICAL WIN RATE

Causal • Non-Repainting • Multi-Market Forex Scanner & Live Market Engine

![Harmonic Trading Lab Live Scanner](./assets/live-scanner.png)

👉 **[▶ Open Harmonic Trading Lab on Streamlit Community Cloud](https://share.streamlit.io/karidasd/harmonic-trading-lab/main/dashboard.py)**

> Can a 71.8% win-rate strategy still fail to produce an economic edge?

---

## Hero Research Findings (Frozen FX Baseline)

| 71.8% | 0 | 16,276 | +0.005R |
| :---: | :---: | :---: | :---: |
| **GROSS HISTORICAL WR** | **REPAINT FAILURES** | **CAUSAL REPLAY TESTS** | **GROSS EXPECTANCY** |

*Verified in the frozen out-of-sample Forex validation baseline ($N=202$ trades, EURUSD, GBPUSD, USDJPY, USDCHF, AUDUSD, USDCAD, NZDUSD, EURJPY, GBPJPY).*

---

## Key Features

- **Live / Current Market Chart**: View the latest available Forex candles and automatically overlay newly detected causal AB=CD and Gartley patterns with real-time price lines and freshness metrics.
- **Active Multi-Market Scanner**: Scans 10 currency pairs across M15, M30, H1, and H4 simultaneously with auto-refresh (1m, 5m, 15m, 30m) and newly detected pattern alerts.
- **100% Causal & Non-Repainting**: Strict 5-bar left / 5-bar right pivot engine ensures zero lookahead bias. Swing points never mutate or shift retroactively.
- **Interactive Quant Charts**: Dark terminal Plotly candlestick charts with XABCD legs, translucent Potential Reversal Zones (PRZ), and objective research levels.
- **Live State Machine**: Tracks patterns through `FORMING` $\rightarrow$ `POTENTIAL_D` $\rightarrow$ `COMPLETED` $\rightarrow$ `ACTIVE` $\rightarrow$ `TP1_HIT` / `TP2_HIT` / `SL_HIT` / `EXPIRED`.
- **Prospective Forward Ledger**: Deduplicated SQLite database logging forward signals with immutable initial predictions and conservative **STOP-FIRST** outcome tracking.
- **Machine Learning Walk-Forward Research**: Includes a rigorous point-in-time machine learning pipeline (`prediction/`) evaluated on pre-2025 data with strict acceptance gates to prevent fabricating unvalidated probabilities.
- **Cloud & MT5 Data Modes**: Operates seamlessly in **Cloud Mode** (Yahoo Finance Cloud / Delayed data) or **Offline Demo Mode**, with optional **MetaTrader 5 Live Mode** when running locally connected to a live broker terminal.

---

## Application Showcase

### Live Current Market Chart

![Live Market Chart](./assets/live-market.png)

### Pattern Chart & Geometry

![Pattern Chart](./assets/pattern-chart.png)

### Market Heatmap Matrix

![Market Matrix](./assets/market-matrix.png)

### Research & Baseline Validation

![Research Dashboard](./assets/research-dashboard.png)

### Causal Non-Repainting Methodology

![Causal Validation](./assets/causal-validation.png)

---

## Non-Repainting Causal Architecture

Many commercial harmonic indicators suffer from lookahead bias: they silently redraw swing points as new candles form.

```
+------------------+      +-------------------+      +------------------+      +------------------+
|  Pivot Point (t) | ---> | 5 Right Bars Close| ---> |  Pivot Confirmed | ---> | Signal Available |
|  Swing Low/High  |      |   (Candle t + 5)  |      |   at Bar t + 5   |      |  at Open (t + 6) |
+------------------+      +-------------------+      +------------------+      +------------------+
```

Every pattern causally tracks:
- `occurrence_time`: Exact bar timestamp where the swing extremity formed.
- `confirmation_time`: Bar timestamp where the pivot satisfied the 5 right-side confirmation bars.
- `signal_available_time`: Exact executable timestamp where the pattern could first be acted upon in real time.

---

## The Economic Reality: Win Rate vs. Payoff Asymmetry

While the geometric detector achieves an impressive **71.78% gross directional accuracy**, classical harmonic targets ($T_1 = 0.382 \times AD$) produce an asymmetric payoff ratio:

- **Average Gross Win**: `+0.401R`
- **Average Gross Loss**: `-1.000R`
- **Payoff Ratio**: `0.401 : 1`
- **Implied Break-Even Win Rate Required**: `71.40%`

When realistic ECN spreads, slippage, and execution commissions ($0.083\text{R}$) are deducted:
- **Net Expectancy**: `-0.0777R`
- **Profit Factor after Costs**: `0.7542`

---

## Storage & Forward Tracking Architecture

Harmonic Trading Lab incorporates a local SQLite database for deduplication and prospective signal recording:
- **Local Runs**: Persisted dynamically at `<REPO_ROOT>/storage/harmonic_scanner.db`.
- **Streamlit Community Cloud Notice**: When running on Streamlit Cloud containers, the local SQLite database is ephemeral and resets during container redeployments or cold restarts. For institutional multi-month forward recording, a persistent external database (e.g. Supabase, PostgreSQL) can be connected.

---

## Quickstart Guide

### 1. Clone the Repository
```bash
git clone https://github.com/karidasd/Harmonic-Trading-Lab.git
cd Harmonic-Trading-Lab
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Launch the Terminal
```bash
streamlit run dashboard.py
```

---

## Deploy to Streamlit Community Cloud

1. Fork or push this repository to GitHub.
2. Visit [share.streamlit.io](https://share.streamlit.io).
3. Connect your repository `Harmonic-Trading-Lab` and set `Main file path` to `dashboard.py`.
4. The application will launch instantly in **Cloud/Demo Mode**!

---

## Running Causal & Market Test Suite

Run the full adversarial future-candle replay, causality, live market, and prediction test suite:

```bash
python -m unittest discover -s tests -t . -v
```

---

## Scientific Disclaimer

*This software is provided for research and educational purposes only. Past or gross historical performance does not guarantee future results. Pattern detection and research levels do not constitute investment advice.*

---

**License**: MIT License. Built with ❤️ for quantitative research and transparent open-source trading engineering.
