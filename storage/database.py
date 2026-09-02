from typing import Dict, Any, List, Optional
from storage.base import BaseForwardStore
from storage.sqlite_store import SQLiteForwardStore
from storage.factory import StoreFactory

class HarmonicDatabase:
    """
    Backward-compatible facade delegating to the active BaseForwardStore.
    Automatically connects to persistent PostgreSQL if DATABASE_URL is configured,
    or falls back to local SQLite.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is not None:
            self._store: BaseForwardStore = SQLiteForwardStore(db_path=db_path)
        else:
            self._store: BaseForwardStore = StoreFactory.get_store()

    @property
    def store_type(self) -> str:
        return self._store.store_type

    @property
    def is_persistent(self) -> bool:
        return self._store.is_persistent

    def health_check(self) -> Dict[str, Any]:
        return self._store.health_check()

    def insert_prediction(self, record: Dict[str, Any]) -> bool:
        return self._store.insert_prediction(record)

    def insert_forward_prediction(self, record: Dict[str, Any]) -> bool:
        return self._store.insert_prediction(record)

    def get_prediction(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        return self._store.get_prediction(pattern_id)

    def prediction_exists(self, pattern_id: str) -> bool:
        return self._store.prediction_exists(pattern_id)

    def update_outcome(
        self,
        pattern_id: str,
        status: str,
        tp1_hit_at: Optional[str] = None,
        tp2_hit_at: Optional[str] = None,
        sl_hit_at: Optional[str] = None,
        resolved_at: Optional[str] = None
    ) -> bool:
        return self._store.update_outcome(pattern_id, status, tp1_hit_at, tp2_hit_at, sl_hit_at, resolved_at)

    def update_forward_outcome(
        self,
        pattern_id: str,
        status: str,
        tp1_hit_at: Optional[str] = None,
        tp2_hit_at: Optional[str] = None,
        sl_hit_at: Optional[str] = None,
        resolved_at: Optional[str] = None
    ) -> bool:
        return self._store.update_outcome(pattern_id, status, tp1_hit_at, tp2_hit_at, sl_hit_at, resolved_at)

    def get_forward_predictions(self, limit: int = 200) -> List[Dict[str, Any]]:
        return self._store.get_forward_predictions(limit=limit)

    def get_forward_metrics(self) -> Dict[str, Any]:
        return self._store.get_forward_metrics()

    def save_pattern(self, pattern: Dict[str, Any]):
        self._store.save_pattern(pattern)

    def save_patterns(self, patterns: List[Dict[str, Any]]):
        self._store.save_patterns(patterns)

    def record_event(self, event_dict: Dict[str, Any]):
        self._store.record_event(event_dict)

    def save_events(self, events: List[Dict[str, Any]]):
        self._store.save_events(events)

    def record_scanner_run(self, provider_name: str, mode: str, markets: int, patterns: int, duration: float):
        self._store.record_scanner_run(provider_name, mode, markets, patterns, duration)

    def get_recent_patterns(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._store.get_recent_patterns(limit=limit)

    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        return self._store.get_recent_events(limit=limit)
