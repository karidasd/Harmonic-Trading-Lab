import pandas as pd
from typing import Dict, Any, Optional

class OutcomeTracker:
    """
    Causal forward outcome evaluator.
    Evaluates forward market bars sequentially against frozen pattern levels (SL, TP1, TP2).
    Enforces the project's immutable STOP-FIRST rule for intrabar ambiguity.
    """

    @staticmethod
    def evaluate_outcome(
        pattern: Dict[str, Any],
        df_forward: pd.DataFrame,
        max_bars: int = 150
    ) -> Dict[str, Any]:
        """
        Evaluates forward candles strictly starting after signal_available_time.
        """
        conf_time = pattern.get('signal_available_time') or pattern.get('D_confirmation_time')
        direction = pattern.get('direction', 'BULLISH')
        sl = float(pattern.get('structural_stop', 0))
        tp1 = float(pattern.get('target_1', 0))
        tp2 = float(pattern.get('target_2', 0))

        if conf_time is None or df_forward.empty:
            return {'status': 'ACTIVE', 'tp1_hit': False, 'tp2_hit': False, 'sl_hit': False, 'resolved_at': None}

        # Select only forward bars after confirmation
        bars_after = df_forward.loc[df_forward.index > conf_time].head(max_bars)
        if bars_after.empty:
            return {'status': 'ACTIVE', 'tp1_hit': False, 'tp2_hit': False, 'sl_hit': False, 'resolved_at': None}

        tp1_hit = False
        tp2_hit = False
        sl_hit = False
        tp1_hit_time = None
        tp2_hit_time = None
        sl_hit_time = None

        for ts, row in bars_after.iterrows():
            h, l = row['high'], row['low']

            if direction == 'BULLISH':
                # Bullish: SL is below entry (l <= sl), TP1 is above entry (h >= tp1), TP2 is above TP1 (h >= tp2)
                is_sl = l <= sl
                is_tp1 = h >= tp1
                is_tp2 = h >= tp2

                # Conservative STOP-FIRST Rule: If both SL and TP occur in the same bar
                if is_sl and is_tp1:
                    sl_hit = True
                    sl_hit_time = ts
                    break
                elif is_sl:
                    sl_hit = True
                    sl_hit_time = ts
                    break
                elif is_tp2:
                    tp1_hit = True
                    tp2_hit = True
                    tp1_hit_time = tp1_hit_time or ts
                    tp2_hit_time = ts
                elif is_tp1:
                    tp1_hit = True
                    tp1_hit_time = tp1_hit_time or ts
            else: # BEARISH
                # Bearish: SL is above entry (h >= sl), TP1 is below entry (l <= tp1), TP2 is below TP1 (l <= tp2)
                is_sl = h >= sl
                is_tp1 = l <= tp1
                is_tp2 = l <= tp2

                # Conservative STOP-FIRST Rule: If both SL and TP occur in the same bar
                if is_sl and is_tp1:
                    sl_hit = True
                    sl_hit_time = ts
                    break
                elif is_sl:
                    sl_hit = True
                    sl_hit_time = ts
                    break
                elif is_tp2:
                    tp1_hit = True
                    tp2_hit = True
                    tp1_hit_time = tp1_hit_time or ts
                    tp2_hit_time = ts
                elif is_tp1:
                    tp1_hit = True
                    tp1_hit_time = tp1_hit_time or ts

        # Determine overall terminal or active state
        if sl_hit:
            status = 'SL_HIT'
            resolved_at = sl_hit_time
        elif tp2_hit:
            status = 'TP2_HIT'
            resolved_at = tp2_hit_time
        elif tp1_hit:
            status = 'TP1_HIT'
            resolved_at = tp1_hit_time
        elif len(bars_after) >= max_bars:
            status = 'EXPIRED'
            resolved_at = bars_after.index[-1]
        else:
            status = 'ACTIVE'
            resolved_at = None

        return {
            'status': status,
            'tp1_hit': tp1_hit,
            'tp2_hit': tp2_hit,
            'sl_hit': sl_hit,
            'tp1_hit_at': tp1_hit_time,
            'tp2_hit_at': tp2_hit_time,
            'sl_hit_at': sl_hit_time,
            'resolved_at': resolved_at
        }
