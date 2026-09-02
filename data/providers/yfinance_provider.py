import pandas as pd
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from data.providers.base import BaseMarketDataProvider
from data.normalization import DataNormalizer

class YFinanceMarketDataProvider(BaseMarketDataProvider):
    """
    Cloud-compatible public market data provider using Yahoo Finance / CCXT fallback.
    """
    def __init__(self):
        self.symbol_map = {
            'EURUSD': 'EURUSD=X', 'GBPUSD': 'GBPUSD=X', 'USDJPY': 'USDJPY=X',
            'USDCHF': 'USDCHF=X', 'AUDUSD': 'AUDUSD=X', 'USDCAD': 'USDCAD=X',
            'NZDUSD': 'NZDUSD=X', 'EURJPY': 'EURJPY=X', 'GBPJPY': 'GBPJPY=X',
            'XAUUSD': 'GC=F'
        }
        self.tf_map = {'M15': '15m', 'M30': '30m', 'H1': '1h', 'H4': '1h'} # Note: H4 resampled from H1
        self.last_fetch = None

    def get_ohlcv(self, symbol: str, timeframe: str, bars: int = 300) -> Optional[pd.DataFrame]:
        try:
            import yfinance as yf
            yf_sym = self.symbol_map.get(symbol, f"{symbol}=X")
            yf_tf = self.tf_map.get(timeframe, '1h')
            
            period = '5d' if timeframe in ['M15', 'M30'] else '60d'
            ticker = yf.Ticker(yf_sym)
            df = ticker.history(period=period, interval=yf_tf)
            
            if df is None or df.empty:
                return None
                
            if timeframe == 'H4':
                df = df.resample('4h').agg({
                    'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'
                }).dropna()
                
            norm = DataNormalizer.normalize_ohlcv(df, symbol, timeframe)
            self.last_fetch = datetime.now(timezone.utc)
            return norm.tail(bars)
        except Exception:
            return None

    def get_status(self) -> Dict[str, Any]:
        return {
            'provider_name': 'YAHOO FINANCE (CLOUD)',
            'mode': 'CLOUD',
            'status': 'ONLINE' if self.last_fetch else 'READY',
            'is_live': False,
            'is_demo': False,
            'description': 'Delayed public cloud market data feed'
        }
