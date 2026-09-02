import pandas as pd
from typing import List, Dict, Any, Optional
from harmonic.pivots import CausalPivotEngine
from harmonic.abcd import ABCDDetector
from harmonic.gartley import GartleyDetector

class HarmonicDetector:
    def __init__(self, left_bars: int = 5, right_bars: int = 5, min_leg_bars: int = 3):
        self.pivot_engine = CausalPivotEngine(left_bars, right_bars, min_leg_bars)
        self.abcd_detector = ABCDDetector()
        self.gartley_detector = GartleyDetector()

    def scan_dataframe(self, df: pd.DataFrame, symbol: str, timeframe: str) -> List[Dict[str, Any]]:
        if df.empty or len(df) < 25:
            return []
            
        raw_pivots = self.pivot_engine.find_pivots(df)
        alt_pivots = self.pivot_engine.build_alternating_pivots(raw_pivots)
        
        p_abcd = self.abcd_detector.detect(alt_pivots, df, symbol, timeframe)
        p_gartley = self.gartley_detector.detect(alt_pivots, df, symbol, timeframe)
        
        all_pats = p_abcd + p_gartley
        return all_pats
