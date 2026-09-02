import unittest
import pandas as pd
from harmonic.pivots import CausalPivotEngine

class TestCausalPivots(unittest.TestCase):
    def test_causal_pivot_delay(self):
        n = 25
        times = pd.date_range('2024-01-01', periods=n, freq='1h', tz='UTC')
        prices = [10.0] * n
        prices[10] = 15.0 # Peak High
        
        df = pd.DataFrame({
            'open': prices, 'high': prices, 'low': prices, 'close': prices, 'volume': 100
        }, index=times)
        
        engine = CausalPivotEngine(left_bars=5, right_bars=5)
        pivots = engine.find_pivots(df)
        
        self.assertEqual(len(pivots), 1)
        p = pivots[0]
        self.assertTrue(p.is_high)
        self.assertEqual(p.bar_index, 10)
        self.assertEqual(p.price, 15.0)
        self.assertEqual(p.occurrence_time, times[10])
        self.assertEqual(p.confirmation_time, times[15])

if __name__ == '__main__':
    unittest.main()
