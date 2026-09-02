"""
Harmonic Trading Lab — SQLite to PostgreSQL Forward Migration Script
Migrates historical forward tracking signals and telemetry from local SQLite into persistent PostgreSQL.
Preserves all pattern IDs, immutable levels, and timestamps.
"""
import os
import sys
import argparse
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.sqlite_store import SQLiteForwardStore
from storage.postgres_store import PostgresForwardStore
from storage.factory import mask_database_url

def migrate_database(sqlite_path: str, postgres_url: str) -> Dict[str, Any]:
    print(f"Opening SQLite database at: {sqlite_path}")
    sqlite_store = SQLiteForwardStore(db_path=sqlite_path)
    
    masked_url = mask_database_url(postgres_url)
    print(f"Connecting to PostgreSQL database: {masked_url}")
    pg_store = PostgresForwardStore(database_url=postgres_url)
    
    # 1. Migrate Forward Predictions
    sqlite_records = sqlite_store.get_forward_predictions(limit=10000)
    source_rows = len(sqlite_records)
    print(f"Found {source_rows} forward prediction rows in SQLite.")
    
    inserted_rows = 0
    duplicates_skipped = 0
    errors = 0
    
    for rec in sqlite_records:
        pid = rec.get('pattern_id')
        if not pid:
            continue
            
        try:
            if pg_store.prediction_exists(pid):
                duplicates_skipped += 1
            else:
                success = pg_store.insert_prediction(rec)
                if success:
                    # If outcome fields are set, update outcome
                    if rec.get('status') != 'ACTIVE':
                        pg_store.update_outcome(
                            pattern_id=pid,
                            status=rec.get('status', 'ACTIVE'),
                            tp1_hit_at=rec.get('tp1_hit_at'),
                            tp2_hit_at=rec.get('tp2_hit_at'),
                            sl_hit_at=rec.get('sl_hit_at'),
                            resolved_at=rec.get('resolved_at')
                        )
                    inserted_rows += 1
                else:
                    duplicates_skipped += 1
        except Exception as e:
            print(f"Error migrating pattern_id {pid}: {e}")
            errors += 1
            
    summary = {
        'SOURCE_ROWS': source_rows,
        'INSERTED_ROWS': inserted_rows,
        'DUPLICATES_SKIPPED': duplicates_skipped,
        'ERRORS': errors,
        'POSTGRES_STORE_STATUS': pg_store.health_check().get('status', 'UNKNOWN')
    }
    
    print("\n=== MIGRATION SUMMARY ===")
    for k, v in summary.items():
        print(f"  {k:<24}: {v}")
        
    return summary

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Migrate forward predictions from SQLite to PostgreSQL.")
    parser.add_argument("--sqlite-path", default="storage/harmonic_scanner.db", help="Path to source SQLite file")
    parser.add_argument("--postgres-url", default=os.environ.get("DATABASE_URL", ""), help="Target PostgreSQL connection URL")
    
    args = parser.parse_args()
    
    if not args.postgres_url:
        print("Error: PostgreSQL connection string required via --postgres-url or DATABASE_URL environment variable.")
        sys.exit(1)
        
    res = migrate_database(args.sqlite_path, args.postgres_url)
