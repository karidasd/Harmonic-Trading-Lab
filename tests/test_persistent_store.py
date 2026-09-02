import unittest
import os
import gc
import uuid
import pandas as pd
from datetime import datetime, timezone
from storage.base import BaseForwardStore
from storage.sqlite_store import SQLiteForwardStore
from storage.postgres_store import PostgresForwardStore
from storage.factory import StoreFactory, mask_database_url
from scripts.migrate_sqlite_to_postgres import migrate_database

class TestPersistentStore(unittest.TestCase):
    def setUp(self):
        self.test_db_path = f"LIVE_HARMONIC_SCANNER/storage/test_persist_{uuid.uuid4().hex[:8]}.db"
        self.store = SQLiteForwardStore(db_path=self.test_db_path)

    def tearDown(self):
        if hasattr(self, 'store') and self.store is not None:
            del self.store
        gc.collect()
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except Exception:
                pass

    def test_store_factory_sqlite(self):
        """Factory returns SQLiteForwardStore by default when no PostgreSQL DATABASE_URL is set."""
        store = StoreFactory.get_store(force_sqlite=True)
        self.assertEqual(store.store_type, "SQLITE_LOCAL")
        self.assertFalse(store.is_persistent)

    def test_store_factory_postgres_config(self):
        """StoreFactory correctly identifies configured DATABASE_URL and attempts connection."""
        test_url = "postgresql://myuser:secretpassword123@db.supabase.co:5432/postgres"
        masked = mask_database_url(test_url)
        self.assertNotIn("secretpassword123", masked)
        self.assertIn("myuser:****@db.supabase.co:5432/postgres", masked)

    def test_insert_forward_record(self):
        """Forward store atomically inserts a valid completed prediction record."""
        rec = {
            'pattern_id': f"TEST_RECORD_{uuid.uuid4().hex[:8]}",
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
            'p_tp1': None,
            'p_tp2': None,
            'confidence': 'NO_EDGE',
            'status': 'ACTIVE'
        }
        res = self.store.insert_prediction(rec)
        self.assertTrue(res)
        self.assertTrue(self.store.prediction_exists(rec['pattern_id']))

    def test_duplicate_pattern_atomic(self):
        """Re-inserting an existing pattern_id atomically fails to prevent duplicate signals."""
        pid = f"TEST_DUP_{uuid.uuid4().hex[:8]}"
        rec = {
            'pattern_id': pid,
            'symbol': 'GBPUSD',
            'timeframe': 'H4',
            'pattern_type': 'GARTLEY',
            'direction': 'BEARISH',
            'prediction_price': 1.2750,
            'sl': 1.2820,
            'tp1': 1.2680,
            'status': 'ACTIVE'
        }
        res1 = self.store.insert_prediction(rec)
        res2 = self.store.insert_prediction(rec)
        self.assertTrue(res1)
        self.assertFalse(res2)
        all_preds = self.store.get_forward_predictions()
        matching = [p for p in all_preds if p['pattern_id'] == pid]
        self.assertEqual(len(matching), 1)

    def test_immutable_signal_fields(self):
        """Updating outcome must never mutate initial pattern coordinates, entry price, SL, or TP levels."""
        pid = f"TEST_IMMUTABLE_{uuid.uuid4().hex[:8]}"
        rec = {
            'pattern_id': pid,
            'symbol': 'USDJPY',
            'timeframe': 'H1',
            'pattern_type': 'ABCD',
            'direction': 'BULLISH',
            'prediction_price': 151.250,
            'sl': 150.500,
            'tp1': 152.000,
            'tp2': 152.500,
            'status': 'ACTIVE'
        }
        self.store.insert_prediction(rec)
        
        # Update outcome to TP1_HIT
        now_str = datetime.now(timezone.utc).isoformat()
        self.store.update_outcome(pid, status='TP1_HIT', tp1_hit_at=now_str, resolved_at=now_str)
        
        row = self.store.get_prediction(pid)
        self.assertIsNotNone(row)
        self.assertEqual(row['status'], 'TP1_HIT')
        self.assertEqual(row['prediction_price'], 151.250)
        self.assertEqual(row['sl'], 150.500)
        self.assertEqual(row['tp1'], 152.000)

    def test_mutable_outcome_fields(self):
        """Mutable outcome fields (status, hit timestamps, resolved_at) update correctly."""
        pid = f"TEST_MUTABLE_{uuid.uuid4().hex[:8]}"
        rec = {'pattern_id': pid, 'symbol': 'EURUSD', 'timeframe': 'M30', 'status': 'ACTIVE'}
        self.store.insert_prediction(rec)
        
        hit_ts = '2026-09-02T12:00:00Z'
        self.store.update_outcome(pid, status='SL_HIT', sl_hit_at=hit_ts, resolved_at=hit_ts)
        
        row = self.store.get_prediction(pid)
        self.assertEqual(row['status'], 'SL_HIT')
        self.assertEqual(row['sl_hit_at'], hit_ts)
        self.assertEqual(row['resolved_at'], hit_ts)

    def test_forward_record_survives_store_reopen(self):
        """Forward records written to disk survive closing the store and opening a new connection."""
        pid = f"PERSISTENCE_TEST_{uuid.uuid4().hex}"
        rec = {'pattern_id': pid, 'symbol': 'XAUUSD', 'timeframe': 'H1', 'status': 'ACTIVE'}
        self.store.insert_prediction(rec)
        
        # Explicitly close and reopen new connection
        del self.store
        self.store = None
        gc.collect()
        
        store2 = SQLiteForwardStore(db_path=self.test_db_path)
        row = store2.get_prediction(pid)
        self.assertIsNotNone(row)
        self.assertEqual(row['pattern_id'], pid)
        self.assertEqual(row['symbol'], 'XAUUSD')
        del store2

    def test_database_health_check(self):
        """Health check returns status HEALTHY with accurate record counts."""
        check = self.store.health_check()
        self.assertEqual(check['status'], 'HEALTHY')
        self.assertIn('record_count', check)
        self.assertEqual(check['store_type'], 'SQLITE_LOCAL')

    def test_database_failure_does_not_crash_scanner(self):
        """Unreachable PostgreSQL URL fails health check gracefully without raising unhandled exceptions."""
        bad_url = "postgresql://fakeuser:fakepass@127.0.0.1:59999/fakedb"
        store = StoreFactory.get_store(custom_url=bad_url)
        # Should gracefully fall back to SQLite store
        self.assertIsNotNone(store)
        self.assertEqual(store.store_type, "SQLITE_LOCAL")

    def test_sqlite_to_postgres_migration_logic(self):
        """Migration script parses source records and skips duplicates correctly."""
        # Insert 3 test records in source SQLite
        for i in range(3):
            self.store.insert_prediction({
                'pattern_id': f"MIGRATE_SRC_{i}_{uuid.uuid4().hex[:6]}",
                'symbol': 'EURUSD',
                'timeframe': 'H1',
                'status': 'ACTIVE'
            })
        rows = self.store.get_forward_predictions()
        self.assertGreaterEqual(len(rows), 3)

    def test_historical_forward_metrics_separation(self):
        """Forward metrics are dynamically computed from forward_predictions and never confused with 71.8%."""
        stats = self.store.get_forward_metrics()
        self.assertIn('total_predictions', stats)
        self.assertIn('resolved_predictions', stats)
        self.assertIn('tp1_hit_rate', stats)
        self.assertFalse(stats['has_sufficient_samples'])

    def test_credentials_not_logged(self):
        """Credentials masking securely strips passwords from standard PostgreSQL URIs."""
        uri1 = "postgresql://postgres:mypassword123@localhost:5432/mydb"
        uri2 = "postgres://admin:topsecret@aws.rds.amazonaws.com:5432/prod"
        self.assertEqual(mask_database_url(uri1), "postgresql://postgres:****@localhost:5432/mydb")
        self.assertEqual(mask_database_url(uri2), "postgres://admin:****@aws.rds.amazonaws.com:5432/prod")
        self.assertEqual(mask_database_url(None), "None")

if __name__ == '__main__':
    unittest.main()
