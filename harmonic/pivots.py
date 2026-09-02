import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional

class PivotPoint:
    def __init__(self, bar_index: int, occurrence_time: pd.Timestamp, confirmation_time: pd.Timestamp, price: float, is_high: bool):
        self.bar_index = bar_index
        self.occurrence_time = occurrence_time
        self.confirmation_time = confirmation_time
        self.price = price
        self.is_high = is_high

    def to_dict(self) -> Dict[str, Any]:
        return {
            'bar_index': self.bar_index,
            'occurrence_time': self.occurrence_time,
            'confirmation_time': self.confirmation_time,
            'price': self.price,
            'is_high': self.is_high
        }

class CausalPivotEngine:
    """
    Causal, Non-Repainting Pivot Engine.
    Enforces that a pivot occurring at candle t is available ONLY at candle t + right_bars.
    """
    def __init__(self, left_bars: int = 5, right_bars: int = 5, min_leg_bars: int = 3):
        self.left_bars = left_bars
        self.right_bars = right_bars
        self.min_leg_bars = min_leg_bars

    def find_pivots(self, df: pd.DataFrame) -> List[PivotPoint]:
        if df.empty or len(df) < (self.left_bars + self.right_bars + 1):
            return []
            
        highs = df['high'].values.astype(float)
        lows = df['low'].values.astype(float)
        times = df.index
        n = len(df)
        
        pivots = []
        
        for i in range(self.left_bars, n - self.right_bars):
            # Check Pivot High
            is_pivot_high = True
            val_h = highs[i]
            for l in range(1, self.left_bars + 1):
                if highs[i - l] >= val_h:
                    is_pivot_high = False
                    break
            if is_pivot_high:
                for r in range(1, self.right_bars + 1):
                    if highs[i + r] > val_h: # Strict inequality on right
                        is_pivot_high = False
                        break
                        
            if is_pivot_high:
                conf_idx = i + self.right_bars
                pivots.append(PivotPoint(
                    bar_index=i,
                    occurrence_time=times[i],
                    confirmation_time=times[conf_idx],
                    price=val_h,
                    is_high=True
                ))
                continue
                
            # Check Pivot Low
            is_pivot_low = True
            val_l = lows[i]
            for l in range(1, self.left_bars + 1):
                if lows[i - l] <= val_l:
                    is_pivot_low = False
                    break
            if is_pivot_low:
                for r in range(1, self.right_bars + 1):
                    if lows[i + r] < val_l:
                        is_pivot_low = False
                        break
                        
            if is_pivot_low:
                conf_idx = i + self.right_bars
                pivots.append(PivotPoint(
                    bar_index=i,
                    occurrence_time=times[i],
                    confirmation_time=times[conf_idx],
                    price=val_l,
                    is_high=False
                ))
                
        return pivots

    def build_alternating_pivots(self, raw_pivots: List[PivotPoint]) -> List[PivotPoint]:
        if not raw_pivots:
            return []
            
        clean = []
        for p in raw_pivots:
            if not clean:
                clean.append(p)
                continue
            prev = clean[-1]
            if p.is_high == prev.is_high:
                if p.is_high:
                    if p.price >= prev.price:
                        clean[-1] = p
                else:
                    if p.price <= prev.price:
                        clean[-1] = p
            else:
                if (p.bar_index - prev.bar_index) >= self.min_leg_bars:
                    clean.append(p)
        return clean
