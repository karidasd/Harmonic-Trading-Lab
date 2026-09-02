import numpy as np
import pandas as pd
import sqlite3
import os
import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

def _clean_json_val(v):
    if isinstance(v, (np.floating, float)):
        return float(v)
    elif isinstance(v, (np.integer, int)):
        return int(v)
    elif isinstance(v, (np.bool_, bool)):
        return bool(v)
    elif isinstance(v, pd.Timestamp):
        return v.isoformat()
    elif isinstance(v, dict):
        return {k: _clean_json_val(val) for k, val in v.items()}
    elif isinstance(v, list):
        return [_clean_json_val(x) for x in v]
    return v

class HarmonicDatabase:
    """
    SQLite storage for live patterns, events, forward predictions, and prospective outcome tracking.
    """
    def __init__(self, db_path: str = "LIVE_HARMONIC_SCANNER/storage/harmonic_scanner.db"):
        self.db_path = db_path
        if os.path.dirname(db_path):
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
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
                    scan_timestamp TEXT,
                    provider_name TEXT,
                    mode TEXT,
                    markets_scanned INTEGER,
                    patterns_found INTEGER,
                    scan_duration_sec REAL
                )
            """)
            
            # 4. Forward Predictions Table (Immutable Prediction Attributes)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS forward_predictions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern_id TEXT UNIQUE,
                    symbol TEXT,
                    timeframe TEXT,
                    pattern_type TEXT,
                    direction TEXT,
                    detected_at TEXT,
                    prediction_at TEXT,
                    x_time TEXT,
                    a_time TEXT,
                    b_time TEXT,
                    c_time TEXT,
                    d_time TEXT,
                    x_price REAL,
                    a_price REAL,
                    b_price REAL,
                    c_price REAL,
                    d_price REAL,
                    prediction_price REAL,
                    sl REAL,
                    tp1 REAL,
                    tp2 REAL,
                    p_tp1 REAL,
                    p_tp2 REAL,
                    confidence TEXT,
                    model_name TEXT,
                    model_version TEXT,
                    data_provider TEXT,
                    data_mode TEXT,
                    status TEXT,
                    tp1_hit_at TEXT,
                    tp2_hit_at TEXT,
                    sl_hit_at TEXT,
                    resolved_at TEXT,
                    created_at TEXT
                )
            """)
            conn.commit()

    def insert_forward_prediction(self, record: Dict[str, Any]) -> bool:
        """
        Inserts an immutable forward prediction record.
        Returns False if pattern_id has already been recorded.
        """
        sql = """
            INSERT OR IGNORE INTO forward_predictions (
                pattern_id, symbol, timeframe, pattern_type, direction,
                detected_at, prediction_at,
                x_time, a_time, b_time, c_time, d_time,
                x_price, a_price, b_price, c_price, d_price,
                prediction_price, sl, tp1, tp2,
                p_tp1, p_tp2, confidence,
                model_name, model_version, data_provider, data_mode,
                status, created_at
            ) VALUES (
                ?, ?, ?, ?, ?,
                ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?,
                ?, ?
            )
        """
        now_str = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                record.get('pattern_id'),
                record.get('symbol'),
                record.get('timeframe'),
                record.get('pattern_type'),
                record.get('direction'),
                str(record.get('detected_at')),
                str(record.get('prediction_at')),
                str(record.get('x_time')),
                str(record.get('a_time')),
                str(record.get('b_time')),
                str(record.get('c_time')),
                str(record.get('d_time')),
                record.get('x_price'),
                record.get('a_price'),
                record.get('b_price'),
                record.get('c_price'),
                record.get('d_price'),
                record.get('prediction_price'),
                record.get('sl'),
                record.get('tp1'),
                record.get('tp2'),
                record.get('p_tp1'),
                record.get('p_tp2'),
                record.get('confidence'),
                record.get('model_name'),
                record.get('model_version'),
                record.get('data_provider'),
                record.get('data_mode'),
                record.get('status', 'ACTIVE'),
                now_str
            ))
            conn.commit()
            return cursor.rowcount > 0

    def update_forward_outcome(
        self,
        pattern_id: str,
        status: str,
        tp1_hit_at: Optional[str] = None,
        tp2_hit_at: Optional[str] = None,
        sl_hit_at: Optional[str] = None,
        resolved_at: Optional[str] = None
    ):
        """
        Safely updates only the outcome fields of a forward prediction.
        Original prediction features and coordinates remain strictly immutable.
        """
        sql = """
            UPDATE forward_predictions
            SET status = ?,
                tp1_hit_at = COALESCE(?, tp1_hit_at),
                tp2_hit_at = COALESCE(?, tp2_hit_at),
                sl_hit_at = COALESCE(?, sl_hit_at),
                resolved_at = COALESCE(?, resolved_at)
            WHERE pattern_id = ?
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(sql, (
                status,
                str(tp1_hit_at) if tp1_hit_at else None,
                str(tp2_hit_at) if tp2_hit_at else None,
                str(sl_hit_at) if sl_hit_at else None,
                str(resolved_at) if resolved_at else None,
                pattern_id
            ))
            conn.commit()

    def get_forward_predictions(self, limit: int = 200) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM forward_predictions ORDER BY id DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_forward_metrics(self) -> Dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM forward_predictions")
            total = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM forward_predictions WHERE status IN ('TP1_HIT', 'TP2_HIT', 'SL_HIT', 'EXPIRED')")
            resolved = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM forward_predictions WHERE status = 'ACTIVE'")
            active = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM forward_predictions WHERE tp1_hit_at IS NOT NULL")
            tp1_hits = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM forward_predictions WHERE tp2_hit_at IS NOT NULL")
            tp2_hits = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM forward_predictions WHERE sl_hit_at IS NOT NULL")
            sl_hits = cursor.fetchone()[0]
            
            return {
                'total_predictions': total,
                'resolved_predictions': resolved,
                'active_predictions': active,
                'tp1_hits': tp1_hits,
                'tp2_hits': tp2_hits,
                'sl_hits': sl_hits,
                'tp1_hit_rate': round((tp1_hits / resolved) * 100, 1) if resolved > 0 else 0.0,
                'tp2_hit_rate': round((tp2_hits / resolved) * 100, 1) if resolved > 0 else 0.0,
                'sl_hit_rate': round((sl_hits / resolved) * 100, 1) if resolved > 0 else 0.0,
                'has_sufficient_samples': resolved >= 30
            }

    def save_patterns(self, patterns: List[Dict[str, Any]]):
        for p in patterns:
            self.save_pattern(p)

    def save_events(self, events: List[Dict[str, Any]]):
        for ev in events:
            if hasattr(ev, 'to_dict'):
                self.record_event(ev.to_dict())
            elif isinstance(ev, dict):
                self.record_event(ev)

    def save_pattern(self, pattern: Dict[str, Any]):
        clean_pat = _clean_json_val(pattern)
        pid = clean_pat['pattern_id']
        now_str = datetime.now(timezone.utc).isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO patterns (
                    pattern_id, symbol, timeframe, pattern_type, direction, state,
                    quality_score, prz_low, prz_high, d_price, d_confirmation_time,
                    signal_available_time, first_detected_at, last_updated_at, raw_data_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(pattern_id) DO UPDATE SET
                    state=excluded.state,
                    quality_score=excluded.quality_score,
                    prz_low=excluded.prz_low,
                    prz_high=excluded.prz_high,
                    d_price=excluded.d_price,
                    last_updated_at=excluded.last_updated_at,
                    raw_data_json=excluded.raw_data_json
            """, (
                pid,
                clean_pat.get('symbol'),
                clean_pat.get('timeframe'),
                clean_pat.get('pattern_type'),
                clean_pat.get('direction'),
                clean_pat.get('state'),
                clean_pat.get('quality_score'),
                clean_pat.get('prz_low'),
                clean_pat.get('prz_high'),
                clean_pat.get('D_price'),
                str(clean_pat.get('D_confirmation_time')),
                str(clean_pat.get('signal_available_time')),
                now_str,
                now_str,
                json.dumps(clean_pat)
            ))
            conn.commit()

    def record_event(self, event_dict: Dict[str, Any]):
        clean_ev = _clean_json_val(event_dict)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO pattern_events (
                    event_id, pattern_id, symbol, timeframe, pattern_type,
                    direction, state, geometry_quality, detected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                clean_ev.get('event_id'),
                clean_ev.get('pattern_id'),
                clean_ev.get('symbol'),
                clean_ev.get('timeframe'),
                clean_ev.get('pattern_type'),
                clean_ev.get('direction'),
                clean_ev.get('state'),
                clean_ev.get('geometry_quality'),
                clean_ev.get('detected_at')
            ))
            conn.commit()

    def record_scanner_run(self, provider_name: str, mode: str, markets: int, patterns: int, duration: float):
        now_str = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scanner_runs (
                    scan_timestamp, provider_name, mode, markets_scanned,
                    patterns_found, scan_duration_sec
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (now_str, provider_name, mode, markets, patterns, duration))
            conn.commit()

    def get_recent_patterns(self, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patterns ORDER BY first_detected_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pattern_events ORDER BY detected_at DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
