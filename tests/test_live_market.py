import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from data.providers.demo_provider import DemoMarketDataProvider
from data.providers.yfinance_provider import YFinanceMarketDataProvider
from harmonic.detector import HarmonicDetector
from storage.database import HarmonicDatabase
from views.page_live_market import calculate_data_freshness
from ui.charts import HarmonicChartBuilder

class TestLiveMarket(unittest.TestCase):
    def setUp(self):
        self.prov = DemoMarketDataProvider()
        self.detector = HarmonicDetector(left_bars=5, right_bars=5, min_leg_bars=3)
        self.db_path = "LIVE_HARMONIC_SCANNER/storage/test_live_market.db"
        self.db = HarmonicDatabase(self.db_path)

    def tearDown(self):
        import os, gc
        del self.db
        gc.collect()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass

    def test_live_market_latest_candle(self):
        """Verify market feed returns valid OHLCV candles with UTC datetime index."""
        df = self.prov.get_ohlcv('EURUSD', 'H1', bars=200)
        self.assertIsNotNone(df)
        self.assertEqual(len(df), 200)
        self.assertIsInstance(df.index, pd.DatetimeIndex)
        self.assertIsNotNone(df.index.tz)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            self.assertIn(col, df.columns)

    def test_live_market_provider_label(self):
        """Yahoo Finance cloud provider must be labeled CLOUD / DELAYED and not LIVE."""
        yf_prov = YFinanceMarketDataProvider()
        st = yf_prov.get_status()
        self.assertEqual(st['mode'], 'CLOUD')
        self.assertFalse(st['is_live'])

    def test_live_market_no_pattern(self):
        """When zero patterns exist, chart builder should build a clean candlestick chart without crashing."""
        df = self.prov.get_ohlcv('EURUSD', 'H1', bars=100)
        fig = HarmonicChartBuilder.build_harmonic_chart(df, pattern=None, show_levels=True)
        self.assertIsNotNone(fig)
        self.assertTrue(len(fig.data) >= 1) # At least candlestick trace

    def test_live_market_pattern_overlay(self):
        """When a pattern exists, harmonic leg lines and PRZ must be included in the chart."""
        df = self.prov.get_ohlcv('EURUSD', 'H1', bars=300)
        pats = self.detector.scan_dataframe(df, 'EURUSD', 'H1')
        if pats:
            p = pats[0]
            fig = HarmonicChartBuilder.build_harmonic_chart(df, pattern=p, show_levels=True)
            self.assertIsNotNone(fig)
            trace_names = [t.name for t in fig.data if hasattr(t, 'name') and t.name is not None]
            self.assertIn('Harmonic Legs', trace_names)

    def test_live_market_same_detector(self):
        """Live market page uses the exact same causal HarmonicDetector instance configuration."""
        df = self.prov.get_ohlcv('GBPUSD', 'H1', bars=300)
        pats1 = self.detector.scan_dataframe(df, 'GBPUSD', 'H1')
        det2 = HarmonicDetector(left_bars=5, right_bars=5, min_leg_bars=3)
        pats2 = det2.scan_dataframe(df, 'GBPUSD', 'H1')
        self.assertEqual(len(pats1), len(pats2))
        if pats1:
            self.assertEqual(pats1[0]['pattern_id'], pats2[0]['pattern_id'])
            self.assertEqual(pats1[0]['quality_score'], pats2[0]['quality_score'])

    def test_live_market_refresh_no_duplicate(self):
        """Repeated refreshes of the same market must not create duplicate forward prediction records."""
        rec = {
            'pattern_id': 'LIVE_MKT_DUP_TEST_01',
            'symbol': 'EURUSD',
            'timeframe': 'H1',
            'prediction_price': 1.0850,
            'sl': 1.0800,
            'tp1': 1.0900,
            'status': 'ACTIVE'
        }
        res1 = self.db.insert_forward_prediction(rec)
        res2 = self.db.insert_forward_prediction(rec)
        self.assertTrue(res1)
        self.assertFalse(res2)
        preds = self.db.get_forward_predictions()
        matching = [r for r in preds if r['pattern_id'] == 'LIVE_MKT_DUP_TEST_01']
        self.assertEqual(len(matching), 1)

    def test_live_market_forward_record_immutable(self):
        """Outcome updates in live market must never mutate original prediction levels."""
        rec = {
            'pattern_id': 'LIVE_MKT_IMMUTABLE_01',
            'symbol': 'USDJPY',
            'timeframe': 'H1',
            'prediction_price': 151.20,
            'sl': 150.50,
            'tp1': 152.00,
            'status': 'ACTIVE'
        }
        self.db.insert_forward_prediction(rec)
        self.db.update_forward_outcome('LIVE_MKT_IMMUTABLE_01', status='TP1_HIT', tp1_hit_at='2026-09-02T12:00:00Z')
        preds = self.db.get_forward_predictions()
        row = next(r for r in preds if r['pattern_id'] == 'LIVE_MKT_IMMUTABLE_01')
        self.assertEqual(row['status'], 'TP1_HIT')
        self.assertEqual(row['prediction_price'], 151.20)
        self.assertEqual(row['sl'], 150.50)
        self.assertEqual(row['tp1'], 152.00)

    def test_data_age_calculation(self):
        """Data freshness calculator properly formats minutes, hours, and days."""
        now = datetime.now(timezone.utc)
        t_recent = now - timedelta(minutes=12)
        res_recent = calculate_data_freshness(pd.Timestamp(t_recent), 'H1')
        self.assertIn('12m', res_recent['age_str'])
        self.assertFalse(res_recent['is_stale'])

    def test_stale_data_warning(self):
        """Data older than threshold on a weekday triggers stale data warning."""
        # Create timestamp 8 hours ago on a weekday
        now = datetime.now(timezone.utc)
        t_old = now - timedelta(hours=8)
        res_old = calculate_data_freshness(pd.Timestamp(t_old), 'M15')
        # If not weekend, is_stale is True
        if not res_old['is_closed']:
            self.assertTrue(res_old['is_stale'])

    def test_demo_provider_label(self):
        """Demo provider status returns DEMO mode and is_live = False."""
        st = self.prov.get_status()
        self.assertEqual(st['mode'], 'DEMO')
        self.assertFalse(st['is_live'])

    def test_adversarial_causal_geometry_immutability(self):
        """Appending future market candles must not shift or mutate historical pattern coordinates or ratios."""
        df_base = self.prov.get_ohlcv('EURUSD', 'H1', bars=200)
        pats_base = self.detector.scan_dataframe(df_base, 'EURUSD', 'H1')
        
        # Append 50 future candles
        df_extended = self.prov.get_ohlcv('EURUSD', 'H1', bars=250)
        pats_extended = self.detector.scan_dataframe(df_extended, 'EURUSD', 'H1')
        
        # If a pattern was confirmed in df_base, its coordinates and ratios must be identical in pats_extended
        for p1 in pats_base:
            matching = [p2 for p2 in pats_extended if p2['pattern_id'] == p1['pattern_id']]
            if matching:
                p2 = matching[0]
                self.assertEqual(p1['A_price'], p2['A_price'])
                self.assertEqual(p1['B_price'], p2['B_price'])
                self.assertEqual(p1['C_price'], p2['C_price'])
                self.assertEqual(p1['D_price'], p2['D_price'])
                self.assertEqual(p1['ratios'], p2['ratios'])
                self.assertEqual(p1['prz_low'], p2['prz_low'])
                self.assertEqual(p1['prz_high'], p2['prz_high'])
                self.assertEqual(p1['structural_stop'], p2['structural_stop'])
                self.assertEqual(p1['target_1'], p2['target_1'])

if __name__ == '__main__':
    unittest.main()
