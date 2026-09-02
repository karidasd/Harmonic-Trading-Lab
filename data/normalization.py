import pandas as pd
import numpy as np

class DataNormalizer:
    @staticmethod
    def normalize_ohlcv(df: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame()
            
        df = df.copy()
        
        # Standardize column names
        col_map = {c: c.lower() for c in df.columns}
        df.rename(columns=col_map, inplace=True)
        
        # Check required columns
        reqs = ['open', 'high', 'low', 'close']
        for r in reqs:
            if r not in df.columns:
                raise ValueError(f"Missing required column: {r}")
                
        if 'volume' not in df.columns:
            df['volume'] = 0.0
            
        # Ensure UTC Datetime Index
        if not isinstance(df.index, pd.DatetimeIndex):
            if 'time' in df.columns:
                df['time'] = pd.to_datetime(df['time'], utc=True)
                df.set_index('time', inplace=True)
            elif 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], utc=True)
                df.set_index('date', inplace=True)
            else:
                df.index = pd.to_datetime(df.index, utc=True)
        else:
            if df.index.tz is None:
                df.index = df.index.tz_localize('UTC')
            else:
                df.index = df.index.tz_convert('UTC')
                
        df = df.sort_index()
        df = df[~df.index.duplicated(keep='last')]
        
        # Numeric coercion
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
        df.dropna(subset=['open', 'high', 'low', 'close'], inplace=True)
        return df[['open', 'high', 'low', 'close', 'volume']]
