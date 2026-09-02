import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import sqlalchemy as sa
from sqlalchemy.sql import text
from storage.base import BaseForwardStore

logger = logging.getLogger(__name__)

class PostgresForwardStore(BaseForwardStore):
    """
    Persistent PostgreSQL implementation of BaseForwardStore.
    Provides durable, multi-month prospective signal tracking for Streamlit Cloud & production deployments.
    Compatible with Supabase, Neon, Railway, and self-hosted PostgreSQL.
    """

    def __init__(self, database_url: str):
        # Normalize connection string protocol for SQLAlchemy + psycopg2
        url = database_url.strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+psycopg2://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
            
        self.database_url = url
        self.engine = sa.create_engine(
            self.database_url,
            pool_size=5,
            max_overflow=10,
            pool_recycle=300,
            pool_pre_ping=True
        )
        self._init_db()

    @property
    def store_type(self) -> str:
        return "POSTGRES_PERSISTENT"

    @property
    def is_persistent(self) -> bool:
        return True

    def _init_db(self):
        try:
            with self.engine.begin() as conn:
                # 1. Forward Predictions Table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS forward_predictions (
                        id SERIAL PRIMARY KEY,
                        pattern_id VARCHAR(128) UNIQUE NOT NULL,
                        symbol VARCHAR(32) NOT NULL,
                        timeframe VARCHAR(16) NOT NULL,
                        pattern_type VARCHAR(32) NOT NULL,
                        direction VARCHAR(16) NOT NULL,
                        state VARCHAR(32) DEFAULT 'COMPLETED',
                        detected_at TIMESTAMPTZ,
                        prediction_at TIMESTAMPTZ,
                        x_time TIMESTAMPTZ,
                        a_time TIMESTAMPTZ,
                        b_time TIMESTAMPTZ,
                        c_time TIMESTAMPTZ,
                        d_time TIMESTAMPTZ,
                        x_price DOUBLE PRECISION,
                        a_price DOUBLE PRECISION,
                        b_price DOUBLE PRECISION,
                        c_price DOUBLE PRECISION,
                        d_price DOUBLE PRECISION,
                        prediction_price DOUBLE PRECISION,
                        prz_low DOUBLE PRECISION,
                        prz_high DOUBLE PRECISION,
                        sl DOUBLE PRECISION,
                        tp1 DOUBLE PRECISION,
                        tp2 DOUBLE PRECISION,
                        p_tp1 DOUBLE PRECISION,
                        p_tp2 DOUBLE PRECISION,
                        confidence VARCHAR(32),
                        model_name VARCHAR(64),
                        model_version VARCHAR(64),
                        geometry_quality INTEGER,
                        data_provider VARCHAR(64),
                        data_mode VARCHAR(64),
                        detector_version VARCHAR(32),
                        app_version VARCHAR(32),
                        status VARCHAR(32) DEFAULT 'ACTIVE',
                        tp1_hit_at TIMESTAMPTZ,
                        tp2_hit_at TIMESTAMPTZ,
                        sl_hit_at TIMESTAMPTZ,
                        resolved_at TIMESTAMPTZ,
                        first_seen_at TIMESTAMPTZ,
                        last_checked_at TIMESTAMPTZ,
                        created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                
                # 2. Active Patterns Cache Table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS patterns (
                        pattern_id VARCHAR(128) PRIMARY KEY,
                        symbol VARCHAR(32),
                        timeframe VARCHAR(16),
                        pattern_type VARCHAR(32),
                        direction VARCHAR(16),
                        state VARCHAR(32),
                        quality_score INTEGER,
                        prz_low DOUBLE PRECISION,
                        prz_high DOUBLE PRECISION,
                        d_price DOUBLE PRECISION,
                        d_confirmation_time TIMESTAMPTZ,
                        signal_available_time TIMESTAMPTZ,
                        first_detected_at TIMESTAMPTZ,
                        last_updated_at TIMESTAMPTZ,
                        raw_data_json TEXT
                    )
                """))
                
                # 3. Pattern Events Table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS pattern_events (
                        event_id VARCHAR(128) PRIMARY KEY,
                        pattern_id VARCHAR(128),
                        symbol VARCHAR(32),
                        timeframe VARCHAR(16),
                        pattern_type VARCHAR(32),
                        direction VARCHAR(16),
                        state VARCHAR(32),
                        geometry_quality INTEGER,
                        detected_at TIMESTAMPTZ
                    )
                """))
                
                # 4. Scanner Runs Telemetry Table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS scanner_runs (
                        run_id SERIAL PRIMARY KEY,
                        scan_timestamp TIMESTAMPTZ,
                        provider_name VARCHAR(64),
                        mode VARCHAR(32),
                        markets_scanned INTEGER,
                        patterns_found INTEGER,
                        scan_duration_sec DOUBLE PRECISION
                    )
                """))
        except Exception as e:
            logger.error(f"PostgreSQL initialization failed: {e}")

    def health_check(self) -> Dict[str, Any]:
        try:
            with self.engine.connect() as conn:
                res = conn.execute(text("SELECT 1")).scalar()
                count = conn.execute(text("SELECT COUNT(*) FROM forward_predictions")).scalar()
                return {
                    'status': 'HEALTHY',
                    'store_type': self.store_type,
                    'is_persistent': self.is_persistent,
                    'record_count': count,
                    'database': 'PostgreSQL'
                }
        except Exception as e:
            return {
                'status': 'UNHEALTHY',
                'store_type': self.store_type,
                'is_persistent': False,
                'error': str(e)
            }

    def insert_prediction(self, record: Dict[str, Any]) -> bool:
        sql = text("""
            INSERT INTO forward_predictions (
                pattern_id, symbol, timeframe, pattern_type, direction, state,
                detected_at, prediction_at,
                x_time, a_time, b_time, c_time, d_time,
                x_price, a_price, b_price, c_price, d_price,
                prediction_price, prz_low, prz_high, sl, tp1, tp2,
                p_tp1, p_tp2, confidence,
                model_name, model_version, geometry_quality,
                data_provider, data_mode, detector_version, app_version,
                status, first_seen_at, last_checked_at, created_at, updated_at
            ) VALUES (
                :pattern_id, :symbol, :timeframe, :pattern_type, :direction, :state,
                :detected_at, :prediction_at,
                :x_time, :a_time, :b_time, :c_time, :d_time,
                :x_price, :a_price, :b_price, :c_price, :d_price,
                :prediction_price, :prz_low, :prz_high, :sl, :tp1, :tp2,
                :p_tp1, :p_tp2, :confidence,
                :model_name, :model_version, :geometry_quality,
                :data_provider, :data_mode, :detector_version, :app_version,
                :status, :first_seen_at, :last_checked_at, :created_at, :updated_at
            )
            ON CONFLICT (pattern_id) DO NOTHING
        """)
        now_dt = datetime.now(timezone.utc)
        params = {
            'pattern_id': record.get('pattern_id'),
            'symbol': record.get('symbol'),
            'timeframe': record.get('timeframe'),
            'pattern_type': record.get('pattern_type'),
            'direction': record.get('direction'),
            'state': record.get('state', 'COMPLETED'),
            'detected_at': record.get('detected_at') or now_dt,
            'prediction_at': record.get('prediction_at') or now_dt,
            'x_time': record.get('x_time'),
            'a_time': record.get('a_time'),
            'b_time': record.get('b_time'),
            'c_time': record.get('c_time'),
            'd_time': record.get('d_time'),
            'x_price': record.get('x_price'),
            'a_price': record.get('a_price'),
            'b_price': record.get('b_price'),
            'c_price': record.get('c_price'),
            'd_price': record.get('d_price'),
            'prediction_price': record.get('prediction_price'),
            'prz_low': record.get('prz_low'),
            'prz_high': record.get('prz_high'),
            'sl': record.get('sl'),
            'tp1': record.get('tp1'),
            'tp2': record.get('tp2'),
            'p_tp1': record.get('p_tp1'),
            'p_tp2': record.get('p_tp2'),
            'confidence': record.get('confidence', 'NO_EDGE'),
            'model_name': record.get('model_name', 'None'),
            'model_version': record.get('model_version', 'NO_EDGE_NOT_DEPLOYED'),
            'geometry_quality': record.get('geometry_quality', 80),
            'data_provider': record.get('data_provider'),
            'data_mode': record.get('data_mode'),
            'detector_version': record.get('detector_version', '2.2.0'),
            'app_version': record.get('app_version', 'v2.2'),
            'status': record.get('status', 'ACTIVE'),
            'first_seen_at': now_dt,
            'last_checked_at': now_dt,
            'created_at': now_dt,
            'updated_at': now_dt
        }
        try:
            with self.engine.begin() as conn:
                res = conn.execute(sql, params)
                return res.rowcount > 0
        except Exception as e:
            logger.error(f"PostgreSQL insert_prediction error: {e}")
            return False

    # Legacy alias
    def insert_forward_prediction(self, record: Dict[str, Any]) -> bool:
        return self.insert_prediction(record)

    def get_prediction(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        try:
            with self.engine.connect() as conn:
                res = conn.execute(
                    text("SELECT * FROM forward_predictions WHERE pattern_id = :pid"),
                    {'pid': pattern_id}
                ).mappings().first()
                return dict(res) if res else None
        except Exception:
            return None

    def prediction_exists(self, pattern_id: str) -> bool:
        try:
            with self.engine.connect() as conn:
                val = conn.execute(
                    text("SELECT 1 FROM forward_predictions WHERE pattern_id = :pid LIMIT 1"),
                    {'pid': pattern_id}
                ).scalar()
                return val is not None
        except Exception:
            return False

    def update_outcome(
        self,
        pattern_id: str,
        status: str,
        tp1_hit_at: Optional[str] = None,
        tp2_hit_at: Optional[str] = None,
        sl_hit_at: Optional[str] = None,
        resolved_at: Optional[str] = None
    ) -> bool:
        now_dt = datetime.now(timezone.utc)
        sql = text("""
            UPDATE forward_predictions
            SET status = :status,
                tp1_hit_at = COALESCE(:tp1_hit_at, tp1_hit_at),
                tp2_hit_at = COALESCE(:tp2_hit_at, tp2_hit_at),
                sl_hit_at = COALESCE(:sl_hit_at, sl_hit_at),
                resolved_at = COALESCE(:resolved_at, resolved_at),
                last_checked_at = :last_checked_at,
                updated_at = :updated_at
            WHERE pattern_id = :pattern_id
        """)
        params = {
            'status': status,
            'tp1_hit_at': tp1_hit_at,
            'tp2_hit_at': tp2_hit_at,
            'sl_hit_at': sl_hit_at,
            'resolved_at': resolved_at,
            'last_checked_at': now_dt,
            'updated_at': now_dt,
            'pattern_id': pattern_id
        }
        try:
            with self.engine.begin() as conn:
                res = conn.execute(sql, params)
                return res.rowcount > 0
        except Exception as e:
            logger.error(f"PostgreSQL update_outcome error: {e}")
            return False

    # Legacy alias
    def update_forward_outcome(self, pattern_id: str, status: str, tp1_hit_at=None, tp2_hit_at=None, sl_hit_at=None, resolved_at=None):
        return self.update_outcome(pattern_id, status, tp1_hit_at, tp2_hit_at, sl_hit_at, resolved_at)

    def get_forward_predictions(self, limit: int = 200) -> List[Dict[str, Any]]:
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(
                    text("SELECT * FROM forward_predictions ORDER BY id DESC LIMIT :limit"),
                    {'limit': limit}
                ).mappings().all()
                return [dict(r) for r in rows]
        except Exception:
            return []

    def get_forward_metrics(self) -> Dict[str, Any]:
        try:
            with self.engine.connect() as conn:
                total = conn.execute(text("SELECT COUNT(*) FROM forward_predictions")).scalar() or 0
                resolved = conn.execute(text("SELECT COUNT(*) FROM forward_predictions WHERE status IN ('TP1_HIT', 'TP2_HIT', 'SL_HIT', 'EXPIRED')")).scalar() or 0
                active = conn.execute(text("SELECT COUNT(*) FROM forward_predictions WHERE status = 'ACTIVE'")).scalar() or 0
                tp1_hits = conn.execute(text("SELECT COUNT(*) FROM forward_predictions WHERE tp1_hit_at IS NOT NULL")).scalar() or 0
                tp2_hits = conn.execute(text("SELECT COUNT(*) FROM forward_predictions WHERE tp2_hit_at IS NOT NULL")).scalar() or 0
                sl_hits = conn.execute(text("SELECT COUNT(*) FROM forward_predictions WHERE sl_hit_at IS NOT NULL")).scalar() or 0
                
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
                    'has_sufficient_samples': resolved >= 30,
                    'store_type': self.store_type,
                    'is_persistent': self.is_persistent
                }
        except Exception:
            return {
                'total_predictions': 0, 'resolved_predictions': 0, 'active_predictions': 0,
                'tp1_hits': 0, 'tp2_hits': 0, 'sl_hits': 0,
                'tp1_hit_rate': 0.0, 'tp2_hit_rate': 0.0, 'sl_hit_rate': 0.0,
                'has_sufficient_samples': False,
                'store_type': self.store_type,
                'is_persistent': False
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
        now_dt = datetime.now(timezone.utc)
        sql = text("""
            INSERT INTO patterns (
                pattern_id, symbol, timeframe, pattern_type, direction, state,
                quality_score, prz_low, prz_high, d_price, d_confirmation_time,
                signal_available_time, first_detected_at, last_updated_at, raw_data_json
            ) VALUES (
                :pattern_id, :symbol, :timeframe, :pattern_type, :direction, :state,
                :quality_score, :prz_low, :prz_high, :d_price, :d_confirmation_time,
                :signal_available_time, :first_detected_at, :last_updated_at, :raw_data_json
            )
            ON CONFLICT (pattern_id) DO UPDATE SET
                state = EXCLUDED.state,
                quality_score = EXCLUDED.quality_score,
                prz_low = EXCLUDED.prz_low,
                prz_high = EXCLUDED.prz_high,
                d_price = EXCLUDED.d_price,
                last_updated_at = EXCLUDED.last_updated_at,
                raw_data_json = EXCLUDED.raw_data_json
        """)
        params = {
            'pattern_id': pattern.get('pattern_id'),
            'symbol': pattern.get('symbol'),
            'timeframe': pattern.get('timeframe'),
            'pattern_type': pattern.get('pattern_type'),
            'direction': pattern.get('direction'),
            'state': pattern.get('state'),
            'quality_score': pattern.get('quality_score'),
            'prz_low': pattern.get('prz_low'),
            'prz_high': pattern.get('prz_high'),
            'd_price': pattern.get('D_price'),
            'd_confirmation_time': pattern.get('D_confirmation_time'),
            'signal_available_time': pattern.get('signal_available_time'),
            'first_detected_at': now_dt,
            'last_updated_at': now_dt,
            'raw_data_json': json.dumps(pattern, default=str)
        }
        try:
            with self.engine.begin() as conn:
                conn.execute(sql, params)
        except Exception:
            pass

    def record_event(self, event_dict: Dict[str, Any]):
        sql = text("""
            INSERT INTO pattern_events (
                event_id, pattern_id, symbol, timeframe, pattern_type,
                direction, state, geometry_quality, detected_at
            ) VALUES (
                :event_id, :pattern_id, :symbol, :timeframe, :pattern_type,
                :direction, :state, :geometry_quality, :detected_at
            )
            ON CONFLICT (event_id) DO NOTHING
        """)
        try:
            with self.engine.begin() as conn:
                conn.execute(sql, event_dict)
        except Exception:
            pass

    def record_scanner_run(self, provider_name: str, mode: str, markets: int, patterns: int, duration: float):
        sql = text("""
            INSERT INTO scanner_runs (
                scan_timestamp, provider_name, mode, markets_scanned,
                patterns_found, scan_duration_sec
            ) VALUES (
                :scan_timestamp, :provider_name, :mode, :markets_scanned,
                :patterns_found, :scan_duration_sec
            )
        """)
        now_dt = datetime.now(timezone.utc)
        try:
            with self.engine.begin() as conn:
                conn.execute(sql, {
                    'scan_timestamp': now_dt,
                    'provider_name': provider_name,
                    'mode': mode,
                    'markets_scanned': markets,
                    'patterns_found': patterns,
                    'scan_duration_sec': duration
                })
        except Exception:
            pass

    def get_recent_patterns(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(
                    text("SELECT * FROM patterns ORDER BY first_detected_at DESC LIMIT :limit"),
                    {'limit': limit}
                ).mappings().all()
                return [dict(r) for r in rows]
        except Exception:
            return []

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            with self.engine.connect() as conn:
                rows = conn.execute(
                    text("SELECT * FROM pattern_events ORDER BY detected_at DESC LIMIT :limit"),
                    {'limit': limit}
                ).mappings().all()
                return [dict(r) for r in rows]
        except Exception:
            return []
