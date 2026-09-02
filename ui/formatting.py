import numpy as np

class InstrumentFormatter:
    @staticmethod
    def get_precision(symbol: str) -> int:
        sym = symbol.upper()
        if 'JPY' in sym:
            return 3
        elif 'XAU' in sym or 'GOLD' in sym:
            return 2
        elif 'BTC' in sym or 'ETH' in sym:
            return 2
        else:
            return 5 # EURUSD, GBPUSD, etc.

    @staticmethod
    def format_price(price: float, symbol: str) -> str:
        if price is None or np.isnan(price):
            return "—"
        prec = InstrumentFormatter.get_precision(symbol)
        return f"{price:.{prec}f}"

    @staticmethod
    def get_pip_size(symbol: str) -> float:
        sym = symbol.upper()
        if 'JPY' in sym:
            return 0.01
        elif 'XAU' in sym:
            return 0.10
        else:
            return 0.0001
