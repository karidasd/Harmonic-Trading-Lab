import unittest
from harmonic.detector import HarmonicDetector
from data.providers.demo_provider import DemoMarketDataProvider

class TestNonRepainting(unittest.TestCase):
    def test_adversarial_future_candle_appending(self):
        provider = DemoMarketDataProvider(seed=42)
        df_base = provider.get_ohlcv('EURUSD', 'H1', bars=150)
        
        detector = HarmonicDetector(left_bars=5, right_bars=5)
        pats_t0 = detector.scan_dataframe(df_base, 'EURUSD', 'H1')
        completed_t0 = [p for p in pats_t0 if p['state'] == 'COMPLETED']
        
        if not completed_t0:
            return # Skip if no completed pattern in synthetic slice
            
        p0 = completed_t0[0]
        p0_id = p0['pattern_id']
        p0_d_price = p0['D_price']
        p0_d_time = p0['D_time']
        p0_conf_time = p0['D_confirmation_time']
        
        df_extended = provider.get_ohlcv('EURUSD', 'H1', bars=200)
        pats_t1 = detector.scan_dataframe(df_extended, 'EURUSD', 'H1')
        
        matched_t1 = next((p for p in pats_t1 if p['pattern_id'] == p0_id), None)
        self.assertIsNotNone(matched_t1, "Previously confirmed pattern disappeared after future bars appended!")
        self.assertEqual(matched_t1['D_price'], p0_d_price, "D price mutated!")
        self.assertEqual(matched_t1['D_time'], p0_d_time, "D time mutated!")
        self.assertEqual(matched_t1['D_confirmation_time'], p0_conf_time, "D confirmation time mutated!")

if __name__ == '__main__':
    unittest.main()
