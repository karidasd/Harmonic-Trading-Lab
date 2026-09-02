import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from data.providers.base import BaseMarketDataProvider
from data.normalization import DataNormalizer

class DemoMarketDataProvider(BaseMarketDataProvider):
    """
    Deterministic, offline demo market data provider with realistic synthetic Forex market dynamics.
    Guarantees instant zero-dependency execution for GitHub showcase visitors.
    """
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.cache = {}

    def get_ohlcv(self, symbol: str, timeframe: str, bars: int = 300) -> Optional[pd.DataFrame]:
        key = (symbol, timeframe)
        if key in self.cache:
            return self.cache[key]
            
        tf_delta_map = {'M15': timedelta(minutes=15), 'M30': timedelta(minutes=30), 'H1': timedelta(hours=1), 'H4': timedelta(hours=4)}
        delta = tf_delta_map.get(timeframe, timedelta(hours=1))
        
        now = datetime.now(timezone.utc)
        start_time = now - (bars * delta)
        times = [start_time + (i * delta) for i in range(bars)]
        
        # Base price per symbol
        base_prices = {
            'EURUSD': 1.0850, 'GBPUSD': 1.2720, 'USDJPY': 151.50, 'USDCHF': 0.8840,
            'AUDUSD': 0.6550, 'USDCAD': 1.3580, 'NZDUSD': 0.6020, 'EURJPY': 164.40,
            'GBPJPY': 192.80, 'XAUUSD': 2350.00
        }
        p0 = base_prices.get(symbol, 1.1000)
        pip = 0.01 if 'JPY' in symbol else (0.10 if 'XAU' in symbol else 0.0001)
        
        # Deterministic random walk with harmonic cyclical oscillations
        rng = np.random.default_rng(abs(hash(symbol + timeframe) % 10000000))
        steps = rng.normal(0, 1.2 * pip, size=bars)
        
        # Inject periodic harmonic swing structure to create clean geometric patterns
        cycles = 3.5 * np.sin(np.linspace(0, 5 * np.pi, bars)) * (25 * pip)
        price_series = p0 + np.cumsum(steps) + cycles
        
        opens, highs, lows, closes, vols = [], [], [], [], []
        
        for i in range(bars):
            c_price = price_series[i]
            bar_noise = rng.normal(0, 0.4 * pip)
            o = c_price + bar_noise
            c = c_price - bar_noise
            h = max(o, c) + abs(rng.normal(0, 0.8 * pip))
            l = min(o, c) - abs(rng.normal(0, 0.8 * pip))
            v = int(rng.uniform(100, 1500))
            
            opens.append(o)
            highs.append(h)
            lows.append(l)
            closes.append(c)
            vols.append(v)
            
        df = pd.DataFrame({
            'open': opens, 'high': highs, 'low': lows, 'close': closes, 'volume': vols
        }, index=pd.DatetimeIndex(times, tz='UTC'))
        
        norm_df = DataNormalizer.normalize_ohlcv(df, symbol, timeframe)
        self.cache[key] = norm_df
        return norm_df

    def get_status(self) -> Dict[str, Any]:
        return {
            'provider_name': 'DEMO MARKET FEED',
            'mode': 'DEMO',
            'status': 'ONLINE',
            'is_live': False,
            'is_demo': True,
            'description': 'Offline deterministic synthetic market feed'
        }
