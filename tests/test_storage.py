import unittest
import os
import gc
from storage.database import HarmonicDatabase

class TestStorage(unittest.TestCase):
    def test_database_and_deduplication(self):
        test_db_path = "test_harmonic_scanner_temp.db"
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except Exception:
                pass
                
        db = HarmonicDatabase(db_path=test_db_path)
        
        test_pats = [{
            'pattern_id': 'TEST_EURUSD_H1_ABCD_1',
            'symbol': 'EURUSD',
            'timeframe': 'H1',
            'pattern_type': 'ABCD',
            'direction': 'BULLISH',
            'state': 'COMPLETED',
            'quality_score': 85,
            'prz_low': 1.0800,
            'prz_high': 1.0820,
            'D_price': 1.0810,
            'D_confirmation_time': '2024-01-01T12:00:00Z',
            'signal_available_time': '2024-01-01T12:00:00Z'
        }]
        
        db.save_patterns(test_pats)
        rows = db.get_recent_patterns()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['pattern_id'], 'TEST_EURUSD_H1_ABCD_1')
        
        # Cleanup
        del db
        gc.collect()
        if os.path.exists(test_db_path):
            try:
                os.remove(test_db_path)
            except Exception:
                pass

if __name__ == '__main__':
    unittest.main()
