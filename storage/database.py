import numpy as np
import pandas as pd
import sqlite3
import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

class HarmonicDatabase:
    """
    Lightweight SQLite storage for live patterns, events, scanner runs, and prospective forward tracking.
    """
    def __init__(self, db_path: str = "LIVE_HARMONIC_SCANNER/storage/harmonic_scanner.db"):
        self.db_path = db_path
        if os.path.dirname(db_path): os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 1. Patterns Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patterns (
                    pattern_id TEXT PRIMARY KEY,
                    symbol TEXT,
                    timeframe TEXT,
                    pattern_type TEXT,
                    direction TEXT,
                    state TEXT,
                    quality_score INTEGER,
                    prz_low REAL,
                    prz_high REAL,
                    d_price REAL,
                    d_confirmation_time TEXT,
                    signal_available_time TEXT,
                    first_detected_at TEXT,
                    last_updated_at TEXT,
                    raw_data_json TEXT
                )
            """)
            
            # 2. Pattern Events Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pattern_events (
                    event_id TEXT PRIMARY KEY,
                    pattern_id TEXT,
                    symbol TEXT,
                    timeframe TEXT,
                    pattern_type TEXT,
                    direction TEXT,
                    state TEXT,
                    geometry_quality INTEGER,
                    detected_at TEXT
                )
            """)
            
            # 3. Scanner Runs Table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scanner_runs (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_timestamp TEXT,
                    provider_mode TEXT,
                    markets_scanned INTEGER,
                    active_patterns_count INTEGER,
                    scan_duration_sec REAL
                )
            """)
            
            # 4. Forward Tracking Signals (Prospective Immutable Signals)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS forward_signals (
                    pattern_id TEXT PRIMARY KEY,
                    detected_at TEXT,
                    signal_available_time TEXT,
                    symbol TEXT,
                    timeframe TEXT,
                    pattern_type TEXT,
                    direction TEXT,
                    entry_price REAL,
                    stop_price REAL,
                    target_1 REAL,
                    target_2 REAL,
                    quality_score INTEGER,
                    status TEXT,
                    exit_time TEXT,
                    exit_price REAL,
                    gross_R REAL,
                    net_R REAL
                )
            """)
            conn.commit()

    def save_patterns(self, patterns: List[Dict[str, Any]]):
        now_str = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for p in patterns:
                pid = p['pattern_id']
                raw_json = json.dumps({k: str(v) if isinstance(v, (datetime, pd.Timestamp)) else (bool(v) if isinstance(v, (bool, np.bool_)) else v) for k, v in p.items() if k not in ['entry_zone', 'ratios']}, default=str)
                cursor.execute("""
                    INSERT INTO patterns (
                        pattern_id, symbol, timeframe, pattern_type, direction, state,
                        quality_score, prz_low, prz_high, d_price, d_confirmation_time,
                        signal_available_time, first_detected_at, last_updated_at, raw_data_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(pattern_id) DO UPDATE SET
                        state=excluded.state,
                        quality_score=excluded.quality_score,
                        last_updated_at=excluded.last_updated_at
                """, (
                    pid, p['symbol'], p['timeframe'], p['pattern_type'], p['direction'],
                    p['state'], p['quality_score'], p['prz_low'], p['prz_high'], p['D_price'],
                    str(p.get('D_confirmation_time')), str(p.get('signal_available_time')),
                    now_str, now_str, raw_json
                ))
            conn.commit()

    def save_events(self, events: List[Any]):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for ev in events:
                d = ev.to_dict()
                cursor.execute("""
                    INSERT OR IGNORE INTO pattern_events (
                        event_id, pattern_id, symbol, timeframe, pattern_type, direction,
                        state, geometry_quality, detected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    d['event_id'], d['pattern_id'], d['symbol'], d['timeframe'],
                    d['pattern_type'], d['direction'], d['state'], d['geometry_quality'],
                    d['detected_at']
                ))
            conn.commit()

    def record_scanner_run(self, provider_mode: str, markets: int, active_cnt: int, duration: float):
        now_str = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scanner_runs (run_timestamp, provider_mode, markets_scanned, active_patterns_count, scan_duration_sec)
                VALUES (?, ?, ?, ?, ?)
            """, (now_str, provider_mode, markets, active_cnt, duration))
            conn.commit()

    def get_recent_patterns(self, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patterns ORDER BY last_updated_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_forward_tracking_summary(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), COUNT(CASE WHEN status='CLOSED' THEN 1 END) FROM forward_signals")
            row = cursor.fetchone()
            total_sigs = row[0] if row else 0
            closed_sigs = row[1] if row else 0
            return {
                'forward_start_date': "2026-09-02",
                'total_signals': total_sigs,
                'closed_signals': closed_sigs,
                'open_signals': total_sigs - closed_sigs
            }
