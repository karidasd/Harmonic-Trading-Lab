import pandas as pd
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from data.providers.base import BaseMarketDataProvider
from data.normalization import DataNormalizer

class MT5MarketDataProvider(BaseMarketDataProvider):
    """
    Local MetaTrader 5 Terminal Provider for authentic LIVE streaming quotes.
    Fails gracefully if MT5 is not installed or initialized.
    """
    def __init__(self):
        self.mt5 = None
        self.initialized = False
        try:
            import MetaTrader5 as mt5
            self.mt5 = mt5
            if self.mt5.initialize():
                self.initialized = True
        except Exception:
            self.initialized = False

    def get_ohlcv(self, symbol: str, timeframe: str, bars: int = 300) -> Optional[pd.DataFrame]:
        if not self.initialized or self.mt5 is None:
            return None
            
        tf_map = {
            'M15': self.mt5.TIMEFRAME_M15, 'M30': self.mt5.TIMEFRAME_M30,
            'H1': self.mt5.TIMEFRAME_H1, 'H4': self.mt5.TIMEFRAME_H4
        }
        mt5_tf = tf_map.get(timeframe, self.mt5.TIMEFRAME_H1)
        
        try:
            rates = self.mt5.copy_rates_from_pos(symbol, mt5_tf, 0, bars)
            if rates is None or len(rates) == 0:
                return None
            df = pd.DataFrame(rates)
            df['time'] = pd.to_datetime(df['time'], unit='s', utc=True)
            df.set_index('time', inplace=True)
            return DataNormalizer.normalize_ohlcv(df, symbol, timeframe)
        except Exception:
            return None

    def get_status(self) -> Dict[str, Any]:
        return {
            'provider_name': 'METATRADER 5 (LOCAL)',
            'mode': 'LIVE' if self.initialized else 'OFFLINE',
            'status': 'CONNECTED' if self.initialized else 'DISCONNECTED',
            'is_live': self.initialized,
            'is_demo': False,
            'description': 'Real-time broker market quotes via local MT5 IPC'
        }
