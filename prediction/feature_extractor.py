import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional

class PointInTimeFeatureExtractor:
    """
    Extracts strictly causal point-in-time features for a confirmed harmonic pattern.
    Guarantees zero lookahead bias by truncating the market series at D confirmation time (T_pred).
    """

    FEATURE_NAMES = [
        'is_gartley',
        'is_bullish',
        'quality_score',
        'ratio_ab_xa',
        'ratio_bc_ab',
        'ratio_cd_bc',
        'ratio_cd_ab',
        'ratio_ad_xa',
        'leg_ab_bars',
        'leg_bc_bars',
        'leg_cd_bars',
        'total_bars',
        'atr_14',
        'prz_width_atr',
        'd_prz_center_dist_atr',
        'rsi_14',
        'rsi_slope_5',
        'ema50_dist_atr',
        'mom_5_atr',
        'conf_body_ratio',
        'conf_upper_wick_ratio',
        'conf_lower_wick_ratio',
        'conf_range_atr',
        'hour_of_day',
        'day_of_week',
        'dist_sl_atr',
        'dist_tp1_atr',
        'dist_tp2_atr',
        'rr_ratio_tp1'
    ]

    @classmethod
    def extract_features(
        cls,
        pattern: Dict[str, Any],
        df: pd.DataFrame
    ) -> Optional[Dict[str, float]]:
        """
        Extracts feature vector computed at or prior to signal_available_time (D confirmation bar).
        """
        conf_time = pattern.get('signal_available_time') or pattern.get('D_confirmation_time')
        if conf_time is None:
            return None

        # Truncate market data up to the confirmation timestamp strictly
        df_hist = df.loc[:conf_time]
        if len(df_hist) < 55:
            return None

        # 1. Base Geometry Features
        ptype = pattern.get('pattern_type', 'ABCD')
        direction = pattern.get('direction', 'BULLISH')
        quality = float(pattern.get('quality_score', 50.0))
        ratios = pattern.get('ratios', {})

        is_gartley = 1.0 if ptype == 'GARTLEY' else 0.0
        is_bullish = 1.0 if direction == 'BULLISH' else 0.0

        r_ab_xa = float(ratios.get('AB/XA', 0.618 if is_gartley else 0.0))
        r_bc_ab = float(ratios.get('BC/AB', 0.618))
        r_cd_bc = float(ratios.get('CD/BC', 1.618))
        r_cd_ab = float(ratios.get('CD/AB', 1.000))
        r_ad_xa = float(ratios.get('AD/XA', 0.786 if is_gartley else 0.0))

        # Temporal leg counts
        x_time = pattern.get('X_time')
        a_time = pattern.get('A_time')
        b_time = pattern.get('B_time')
        c_time = pattern.get('C_time')
        d_time = pattern.get('D_time')

        try:
            ab_bars = float(len(df_hist.loc[a_time:b_time])) if a_time and b_time and a_time in df_hist.index and b_time in df_hist.index else 10.0
            bc_bars = float(len(df_hist.loc[b_time:c_time])) if b_time and c_time and b_time in df_hist.index and c_time in df_hist.index else 8.0
            cd_bars = float(len(df_hist.loc[c_time:d_time])) if c_time and d_time and c_time in df_hist.index and d_time in df_hist.index else 12.0
            start_t = x_time if (is_gartley and x_time and x_time in df_hist.index) else a_time
            tot_bars = float(len(df_hist.loc[start_t:d_time])) if start_t and d_time and start_t in df_hist.index and d_time in df_hist.index else (ab_bars + bc_bars + cd_bars)
        except Exception:
            ab_bars, bc_bars, cd_bars, tot_bars = 10.0, 8.0, 12.0, 30.0

        # 2. Technical & Volatility Indicators
        closes = df_hist['close'].values
        highs = df_hist['high'].values
        lows = df_hist['low'].values
        opens = df_hist['open'].values

        # ATR 14
        tr = np.maximum(highs[1:] - lows[1:], np.maximum(np.abs(highs[1:] - closes[:-1]), np.abs(lows[1:] - closes[:-1])))
        if len(tr) < 14:
            return None
        atr_14 = float(np.mean(tr[-14:]))
        if atr_14 <= 1e-6:
            atr_14 = 0.0001

        # PRZ Geometry in ATR terms
        prz_l = float(pattern.get('prz_low', closes[-1]))
        prz_h = float(pattern.get('prz_high', closes[-1]))
        prz_w_atr = float(abs(prz_h - prz_l) / atr_14)
        prz_center = (prz_l + prz_h) / 2.0
        d_price = float(pattern.get('D_price', closes[-1]))
        d_center_dist_atr = float(abs(d_price - prz_center) / atr_14)

        # RSI 14
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        avg_gain = np.mean(gains[-14:]) if len(gains) >= 14 else 0.001
        avg_loss = np.mean(losses[-14:]) if len(losses) >= 14 else 0.001
        rs = avg_gain / (avg_loss + 1e-9)
        rsi_14 = float(100.0 - (100.0 / (1.0 + rs)))

        # RSI Slope 5
        if len(gains) >= 19:
            rs_prev = np.mean(gains[-19:-5]) / (np.mean(losses[-19:-5]) + 1e-9)
            rsi_prev = 100.0 - (100.0 / (1.0 + rs_prev))
            rsi_slope_5 = float((rsi_14 - rsi_prev) / 5.0)
        else:
            rsi_slope_5 = 0.0

        # EMA 50
        ema_50 = float(pd.Series(closes).ewm(span=50, adjust=False).mean().iloc[-1])
        ema50_dist_atr = float((closes[-1] - ema_50) / atr_14)
        mom_5_atr = float((closes[-1] - closes[-6]) / atr_14) if len(closes) >= 6 else 0.0

        # Confirmation Bar Morphology
        conf_o = opens[-1]
        conf_h = highs[-1]
        conf_l = lows[-1]
        conf_c = closes[-1]
        conf_range = max(conf_h - conf_l, 1e-6)
        conf_body = abs(conf_c - conf_o)
        conf_upper_wick = conf_h - max(conf_o, conf_c)
        conf_lower_wick = min(conf_o, conf_c) - conf_l

        conf_body_ratio = float(conf_body / conf_range)
        conf_upper_wick_ratio = float(conf_upper_wick / conf_range)
        conf_lower_wick_ratio = float(conf_lower_wick / conf_range)
        conf_range_atr = float(conf_range / atr_14)

        # Context features
        ts = pd.Timestamp(conf_time)
        hour_of_day = float(ts.hour)
        day_of_week = float(ts.dayofweek)

        # Payoff geometry
        sl = float(pattern.get('structural_stop', closes[-1]))
        tp1 = float(pattern.get('target_1', closes[-1]))
        tp2 = float(pattern.get('target_2', closes[-1]))
        cur_price = closes[-1]

        dist_sl_atr = float(abs(cur_price - sl) / atr_14)
        dist_tp1_atr = float(abs(cur_price - tp1) / atr_14)
        dist_tp2_atr = float(abs(cur_price - tp2) / atr_14)
        rr_ratio_tp1 = float(dist_tp1_atr / (dist_sl_atr + 1e-6))

        return {
            'is_gartley': is_gartley,
            'is_bullish': is_bullish,
            'quality_score': quality,
            'ratio_ab_xa': r_ab_xa,
            'ratio_bc_ab': r_bc_ab,
            'ratio_cd_bc': r_cd_bc,
            'ratio_cd_ab': r_cd_ab,
            'ratio_ad_xa': r_ad_xa,
            'leg_ab_bars': ab_bars,
            'leg_bc_bars': bc_bars,
            'leg_cd_bars': cd_bars,
            'total_bars': tot_bars,
            'atr_14': atr_14,
            'prz_width_atr': prz_w_atr,
            'd_prz_center_dist_atr': d_center_dist_atr,
            'rsi_14': rsi_14,
            'rsi_slope_5': rsi_slope_5,
            'ema50_dist_atr': ema50_dist_atr,
            'mom_5_atr': mom_5_atr,
            'conf_body_ratio': conf_body_ratio,
            'conf_upper_wick_ratio': conf_upper_wick_ratio,
            'conf_lower_wick_ratio': conf_lower_wick_ratio,
            'conf_range_atr': conf_range_atr,
            'hour_of_day': hour_of_day,
            'day_of_week': day_of_week,
            'dist_sl_atr': dist_sl_atr,
            'dist_tp1_atr': dist_tp1_atr,
            'dist_tp2_atr': dist_tp2_atr,
            'rr_ratio_tp1': rr_ratio_tp1
        }
