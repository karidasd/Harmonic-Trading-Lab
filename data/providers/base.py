from abc import ABC, abstractmethod
import pandas as pd
from typing import Optional, Dict, Any

class BaseMarketDataProvider(ABC):
    @abstractmethod
    def get_ohlcv(self, symbol: str, timeframe: str, bars: int = 300) -> Optional[pd.DataFrame]:
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        pass
