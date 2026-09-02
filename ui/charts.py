import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from ui.formatting import InstrumentFormatter

class HarmonicChartBuilder:
    @staticmethod
    def build_harmonic_chart(
        df: pd.DataFrame,
        pattern: Optional[Dict[str, Any]] = None,
        show_levels: bool = True
    ) -> go.Figure:
        fig = go.Figure()
        
        if df.empty:
            fig.update_layout(template="plotly_dark", title="No market data available")
            return fig
            
        symbol = pattern.get('symbol', 'MARKET') if pattern else 'MARKET'
        prec = InstrumentFormatter.get_precision(symbol)
        
        # 1. Candlestick Trace
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df['open'],
            high=df['high'],
            low=df['low'],
            close=df['close'],
            name=symbol,
            increasing_line_color='#10B981',
            increasing_fillcolor='#10B981',
            decreasing_line_color='#EF4444',
            decreasing_fillcolor='#EF4444'
        ))
        
        if pattern:
            ptype = pattern.get('pattern_type', 'ABCD')
            direction = pattern.get('direction', 'BULLISH')
            color_leg = '#00F0FF' if direction == 'BULLISH' else '#F59E0B'
            
            # 2. XABCD Legs & Markers
            if ptype == 'GARTLEY' and pattern.get('X_time') is not None:
                x_pts = [pattern['X_time'], pattern['A_time'], pattern['B_time'], pattern['C_time'], pattern['D_time']]
                y_pts = [pattern['X_price'], pattern['A_price'], pattern['B_price'], pattern['C_price'], pattern['D_price']]
                labels = ['X', 'A', 'B', 'C', 'D']
            else: # ABCD
                x_pts = [pattern['A_time'], pattern['B_time'], pattern['C_time'], pattern['D_time']]
                y_pts = [pattern['A_price'], pattern['B_price'], pattern['C_price'], pattern['D_price']]
                labels = ['A', 'B', 'C', 'D']
                
            # Filter valid points
            valid_x, valid_y, valid_labels = [], [], []
            for xp, yp, lp in zip(x_pts, y_pts, labels):
                if xp is not None and yp is not None:
                    valid_x.append(xp)
                    valid_y.append(yp)
                    valid_labels.append(lp)
                    
            if len(valid_x) >= 2:
                # Harmonic Leg Lines
                fig.add_trace(go.Scatter(
                    x=valid_x,
                    y=valid_y,
                    mode='lines+markers+text',
                    name='Harmonic Legs',
                    line=dict(color=color_leg, width=2.5, dash='solid'),
                    marker=dict(size=9, color=color_leg, symbol='circle'),
                    text=valid_labels,
                    textposition="top center",
                    textfont=dict(family="JetBrains Mono", size=14, color="#FFFFFF")
                ))
                
                # Intermediate Triangles (X-A-B, B-C-D)
                if ptype == 'GARTLEY' and len(valid_x) == 5:
                    fig.add_trace(go.Scatter(
                        x=[valid_x[0], valid_x[1], valid_x[2], valid_x[0]],
                        y=[valid_y[0], valid_y[1], valid_y[2], valid_y[0]],
                        fill='toself',
                        fillcolor='rgba(0, 240, 255, 0.06)',
                        line=dict(color='rgba(0, 240, 255, 0.3)', width=1, dash='dot'),
                        showlegend=False
                    ))
                    fig.add_trace(go.Scatter(
                        x=[valid_x[2], valid_x[3], valid_x[4], valid_x[2]],
                        y=[valid_y[2], valid_y[3], valid_y[4], valid_y[2]],
                        fill='toself',
                        fillcolor='rgba(245, 158, 11, 0.06)',
                        line=dict(color='rgba(245, 158, 11, 0.3)', width=1, dash='dot'),
                        showlegend=False
                    ))
                    
            # 3. Potential Reversal Zone (PRZ Box)
            prz_l = pattern.get('prz_low')
            prz_h = pattern.get('prz_high')
            if prz_l is not None and prz_h is not None and not np.isnan(prz_l):
                t_start = pattern.get('C_time', df.index[-20])
                t_end = df.index[-1]
                fig.add_shape(
                    type="rect",
                    x0=t_start, x1=t_end,
                    y0=prz_l, y1=prz_h,
                    fillcolor="rgba(0, 240, 255, 0.15)",
                    line=dict(color="#00F0FF", width=1.5, dash="dash"),
                    name="PRZ"
                )
                
            # 4. Research Trade Levels
            if show_levels and pattern.get('state') == 'COMPLETED':
                sl = pattern.get('structural_stop')
                t1 = pattern.get('target_1')
                t2 = pattern.get('target_2')
                
                if sl:
                    fig.add_hline(y=sl, line_dash="dash", line_color="#EF4444", annotation_text=f"Research SL ({sl:.{prec}f})", annotation_position="top right")
                if t1:
                    fig.add_hline(y=t1, line_dash="dash", line_color="#10B981", annotation_text=f"Research T1 ({t1:.{prec}f})", annotation_position="top right")
                if t2:
                    fig.add_hline(y=t2, line_dash="dot", line_color="#34D399", annotation_text=f"Research T2 ({t2:.{prec}f})", annotation_position="bottom right")

        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0B0E14",
            plot_bgcolor="#0B0E14",
            height=580,
            margin=dict(l=20, r=20, t=40, b=20),
            xaxis=dict(
                rangeslider=dict(visible=False),
                showgrid=True,
                gridcolor="#1E293B",
                linecolor="#334155"
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor="#1E293B",
                linecolor="#334155",
                tickformat=f".{prec}f"
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(family="Inter", size=11)
            )
        )
        return fig
