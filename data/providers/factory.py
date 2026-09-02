from typing import Optional
from data.providers.base import BaseMarketDataProvider
from data.providers.mt5_provider import MT5MarketDataProvider
from data.providers.yfinance_provider import YFinanceMarketDataProvider
from data.providers.demo_provider import DemoMarketDataProvider

class DataProviderFactory:
    @staticmethod
    def get_provider(mode: str = "AUTO") -> BaseMarketDataProvider:
        mode_upper = mode.upper()
        
        if mode_upper == "MT5":
            prov = MT5MarketDataProvider()
            if prov.initialized:
                return prov
            # Fallback to cloud if MT5 requested but unavailable
            return YFinanceMarketDataProvider()
            
        elif mode_upper in ["CLOUD", "YFINANCE"]:
            return YFinanceMarketDataProvider()
            
        elif mode_upper == "DEMO":
            return DemoMarketDataProvider()
            
        else: # AUTO
            # 1. Try MT5
            mt5_p = MT5MarketDataProvider()
            if mt5_p.initialized:
                return mt5_p
            # 2. Try YFinance
            try:
                yf_p = YFinanceMarketDataProvider()
                df_test = yf_p.get_ohlcv('EURUSD', 'H1', bars=10)
                if df_test is not None and not df_test.empty:
                    return yf_p
            except Exception:
                pass
            # 3. Fallback to Demo
            return DemoMarketDataProvider()
