import os
import glob
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from harmonic.detector import HarmonicDetector
from prediction.feature_extractor import PointInTimeFeatureExtractor
from prediction.outcome_tracker import OutcomeTracker

class PredictionDatasetBuilder:
    """
    Constructs historical feature & label datasets exclusively from pre-2025 approved data.
    Strictly forbids access to sealed historical holdout (>= 2025-01-01).
    """

    @classmethod
    def build_dataset_from_parquets(
        cls,
        data_dir: str = "../HARMONIC_EDGE_RESEARCH_V01/data/raw/forex_feed"
    ) -> pd.DataFrame:
        detector = HarmonicDetector(left_bars=5, right_bars=5, min_leg_bars=3)
        files = glob.glob(os.path.join(data_dir, "*.parquet"))
        
        records = []
        
        for fp in files:
            base = os.path.basename(fp).replace(".parquet", "")
            parts = base.split("_")
            if len(parts) != 2:
                continue
            symbol, timeframe = parts[0], parts[1]
            if timeframe not in ['M15', 'M30', 'H1', 'H4']:
                continue
                
            try:
                df = pd.read_parquet(fp)
                # Ensure UTC datetime index
                if not isinstance(df.index, pd.DatetimeIndex):
                    if 'timestamp' in df.columns:
                        df.index = pd.to_datetime(df['timestamp'], utc=True)
                    elif 'time' in df.columns:
                        df.index = pd.to_datetime(df['time'], utc=True)
                if df.index.tz is None:
                    df.index = df.index.tz_localize('UTC')
                else:
                    df.index = df.index.tz_convert('UTC')
                    
                # Strict holdout cutoff: Only data <= 2024-12-31 is permitted
                df = df.loc[df.index < pd.Timestamp("2025-01-01", tz="UTC")]
                if len(df) < 100:
                    continue
                    
                patterns = detector.scan_dataframe(df, symbol, timeframe)
                completed_pats = [p for p in patterns if p.get('state') == 'COMPLETED']
                
                for p in completed_pats:
                    conf_time = p.get('signal_available_time') or p.get('D_confirmation_time')
                    if conf_time is None or conf_time >= pd.Timestamp("2025-01-01", tz="UTC"):
                        continue
                        
                    # Extract point-in-time features strictly up to conf_time
                    feats = PointInTimeFeatureExtractor.extract_features(p, df)
                    if feats is None:
                        continue
                        
                    # Evaluate ground-truth outcome on subsequent bars
                    outcome = OutcomeTracker.evaluate_outcome(p, df, max_bars=120)
                    if outcome['status'] not in ['TP1_HIT', 'TP2_HIT', 'SL_HIT']:
                        continue
                        
                    rec = dict(feats)
                    rec['pattern_id'] = p['pattern_id']
                    rec['symbol'] = symbol
                    rec['timeframe'] = timeframe
                    rec['confirmation_time'] = conf_time
                    rec['year'] = pd.Timestamp(conf_time).year
                    rec['y_tp1'] = 1 if outcome['tp1_hit'] else 0
                    rec['y_tp2'] = 1 if outcome['tp2_hit'] else 0
                    rec['outcome_status'] = outcome['status']
                    
                    records.append(rec)
            except Exception as e:
                pass
                
        df_out = pd.DataFrame(records)
        if not df_out.empty:
            df_out.sort_values('confirmation_time', inplace=True)
            df_out.reset_index(drop=True, inplace=True)
        return df_out
