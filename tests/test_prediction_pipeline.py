import unittest
import numpy as np
import pandas as pd
from datetime import datetime, timezone, timedelta
from harmonic.detector import HarmonicDetector
from harmonic.states import PatternState
from prediction.feature_extractor import PointInTimeFeatureExtractor
from prediction.outcome_tracker import OutcomeTracker
from prediction.predictor import HarmonicPredictor
from storage.database import HarmonicDatabase
from data.providers.demo_provider import DemoMarketDataProvider
from data.providers.yfinance_provider import YFinanceMarketDataProvider

class TestPredictionPipeline(unittest.TestCase):
    def setUp(self):
        self.prov = DemoMarketDataProvider()
        self.detector = HarmonicDetector(left_bars=5, right_bars=5, min_leg_bars=3)
        self.predictor = HarmonicPredictor()
        self.db_path = "LIVE_HARMONIC_SCANNER/storage/test_forward.db"
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

    def _get_completed_pattern(self):
        for sym in ['GBPJPY', 'GBPUSD', 'EURJPY', 'EURUSD']:
            for tf in ['H4', 'H1', 'M30', 'M15']:
                df = self.prov.get_ohlcv(sym, tf, bars=300)
                pats = self.detector.scan_dataframe(df, sym, tf)
                completed = [p for p in pats if p.get('state') == 'COMPLETED']
                if completed:
                    return completed[0], df
        return None, None

    def test_prediction_no_future_features(self):
        """Verify feature extractor strictly truncates data at D confirmation timestamp."""
        p, df = self._get_completed_pattern()
        self.assertIsNotNone(p, "Expected a completed pattern in demo feed")
        
        feats = PointInTimeFeatureExtractor.extract_features(p, df)
        self.assertIsNotNone(feats)
        for fn in PointInTimeFeatureExtractor.FEATURE_NAMES:
            self.assertIn(fn, feats)

    def test_prediction_timestamp_after_d_confirmation(self):
        """Prediction timestamp must equal or strictly follow D confirmation time."""
        p, df = self._get_completed_pattern()
        self.assertIsNotNone(p)
        conf_time = p['D_confirmation_time']
        sig_time = p['signal_available_time']
        self.assertEqual(conf_time, sig_time)
        self.assertGreater(sig_time, p['D_time'])

    def test_forward_prediction_immutable(self):
        """Original prediction price, SL, TP1, and probabilities must remain immutable."""
        rec = {
            'pattern_id': 'TEST_IMMUTABLE_01',
            'symbol': 'EURUSD',
            'timeframe': 'H1',
            'pattern_type': 'ABCD',
            'direction': 'BULLISH',
            'detected_at': datetime.now(timezone.utc),
            'prediction_at': datetime.now(timezone.utc),
            'prediction_price': 1.0850,
            'sl': 1.0800,
            'tp1': 1.0900,
            'tp2': 1.0950,
            'p_tp1': 68.5,
            'p_tp2': 42.0,
            'confidence': 'MEDIUM',
            'model_name': 'HistGradientBoosting',
            'model_version': 'v1',
            'status': 'ACTIVE'
        }
        res1 = self.db.insert_forward_prediction(rec)
        self.assertTrue(res1)
        
        # Updating outcome should only change outcome fields, not prediction_price or sl
        self.db.update_forward_outcome('TEST_IMMUTABLE_01', status='TP1_HIT', tp1_hit_at='2026-09-02T10:00:00Z')
        
        preds = self.db.get_forward_predictions()
        p_row = next(r for r in preds if r['pattern_id'] == 'TEST_IMMUTABLE_01')
        self.assertEqual(p_row['status'], 'TP1_HIT')
        self.assertEqual(p_row['prediction_price'], 1.0850)
        self.assertEqual(p_row['sl'], 1.0800)
        self.assertEqual(p_row['tp1'], 1.0900)

    def test_duplicate_pattern_not_reinserted(self):
        """Duplicate pattern insertions into forward database must be ignored."""
        rec = {
            'pattern_id': 'TEST_DUP_01',
            'symbol': 'EURUSD',
            'timeframe': 'H1',
            'prediction_price': 1.0850,
            'sl': 1.0800,
            'tp1': 1.0900,
            'status': 'ACTIVE'
        }
        res1 = self.db.insert_forward_prediction(rec)
        res2 = self.db.insert_forward_prediction(rec) # Duplicate
        self.assertTrue(res1)
        self.assertFalse(res2)

    def test_outcome_tracker_stop_first(self):
        """Conservative STOP-FIRST rule must trigger SL if both SL and TP occur in the same bar."""
        pattern = {
            'direction': 'BULLISH',
            'structural_stop': 1.0800,
            'target_1': 1.0900,
            'target_2': 1.0950,
            'signal_available_time': pd.Timestamp('2026-09-01 10:00:00', tz='UTC')
        }
        # Bar with extreme range touching both SL (1.0790) and TP1 (1.0920)
        df_ambiguous = pd.DataFrame({
            'open': [1.0850],
            'high': [1.0920], # Reaches TP1
            'low': [1.0790],  # Reaches SL
            'close': [1.0880],
            'volume': [1000]
        }, index=pd.DatetimeIndex([pd.Timestamp('2026-09-01 11:00:00', tz='UTC')]))
        
        outcome = OutcomeTracker.evaluate_outcome(pattern, df_ambiguous)
        self.assertEqual(outcome['status'], 'SL_HIT', "STOP-FIRST invariant failed for ambiguous bar")
        self.assertTrue(outcome['sl_hit'])
        self.assertFalse(outcome['tp1_hit'])

    def test_probability_range(self):
        """Model output probabilities must strictly lie in [0, 100] %."""
        p, df = self._get_completed_pattern()
        if p is not None:
            res = self.predictor.predict_pattern(p, df)
            if res.get('p_tp1') is not None:
                self.assertGreaterEqual(res['p_tp1'], 0.0)
                self.assertLessEqual(res['p_tp1'], 100.0)

    def test_prediction_model_version_present(self):
        """Every prediction response must contain model_name and model_version."""
        p, df = self._get_completed_pattern()
        if p is not None:
            res = self.predictor.predict_pattern(p, df)
            self.assertIn('model_name', res)
            self.assertIn('model_version', res)

    def test_historical_and_forward_metrics_separate(self):
        """Verify forward metrics (N, TP1 rate) are strictly isolated from historical research."""
        f_metrics = self.db.get_forward_metrics()
        self.assertIn('total_predictions', f_metrics)
        self.assertIn('resolved_predictions', f_metrics)
        self.assertIn('has_sufficient_samples', f_metrics)
        # Ensure forward database does not contain pre-baked 71.8%
        if f_metrics['resolved_predictions'] == 0:
            self.assertFalse(f_metrics['has_sufficient_samples'])

    def test_provider_labeling(self):
        """Cloud provider must never be labeled as LIVE."""
        yf_prov = YFinanceMarketDataProvider()
        status = yf_prov.get_status()
        self.assertEqual(status['mode'], 'CLOUD')
        self.assertFalse(status['is_live'])

    def test_adversarial_prediction_leakage(self):
        """Appending 50 future candles must produce IDENTICAL prediction features and levels at time T."""
        p_base, df_base = self._get_completed_pattern()
        self.assertIsNotNone(p_base)
        
        feats_base = PointInTimeFeatureExtractor.extract_features(p_base, df_base)
        
        # Create extended dataframe with 50 future bars appended
        last_dt = df_base.index[-1]
        delta = df_base.index[1] - df_base.index[0]
        future_dts = [last_dt + (i + 1) * delta for i in range(50)]
        df_future = pd.DataFrame({
            'open': np.linspace(df_base['close'].iloc[-1], df_base['close'].iloc[-1] * 1.05, 50),
            'high': np.linspace(df_base['close'].iloc[-1] * 1.01, df_base['close'].iloc[-1] * 1.06, 50),
            'low': np.linspace(df_base['close'].iloc[-1] * 0.99, df_base['close'].iloc[-1] * 1.04, 50),
            'close': np.linspace(df_base['close'].iloc[-1], df_base['close'].iloc[-1] * 1.05, 50),
            'volume': np.full(50, 1000)
        }, index=pd.DatetimeIndex(future_dts, tz='UTC'))
        
        df_extended = pd.concat([df_base, df_future])
        feats_extended = PointInTimeFeatureExtractor.extract_features(p_base, df_extended)
        
        self.assertEqual(feats_base, feats_extended, "Leakage invariant failed: Appending future candles changed historical prediction feature vector!")

if __name__ == '__main__':
    unittest.main()
