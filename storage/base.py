from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class BaseForwardStore(ABC):
    """
    Abstract interface for Harmonic Trading Lab forward signal storage and telemetry persistence.
    Decouples application code from underlying database engine (PostgreSQL or SQLite).
    """

    @property
    @abstractmethod
    def store_type(self) -> str:
        """Returns storage mode identifier ('POSTGRES_PERSISTENT' or 'SQLITE_LOCAL')."""
        pass

    @property
    @abstractmethod
    def is_persistent(self) -> bool:
        """Returns True if storage persists across container restarts."""
        pass

    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Performs database ping/liveness verification."""
        pass

    @abstractmethod
    def insert_prediction(self, record: Dict[str, Any]) -> bool:
        """
        Atomically inserts an immutable forward prediction record.
        Returns True if newly inserted, False if pattern_id already exists.
        """
        pass

    @abstractmethod
    def get_prediction(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a forward prediction record by unique pattern_id."""
        pass

    @abstractmethod
    def prediction_exists(self, pattern_id: str) -> bool:
        """Checks if pattern_id has already been recorded."""
        pass

    @abstractmethod
    def update_outcome(
        self,
        pattern_id: str,
        status: str,
        tp1_hit_at: Optional[str] = None,
        tp2_hit_at: Optional[str] = None,
        sl_hit_at: Optional[str] = None,
        resolved_at: Optional[str] = None
    ) -> bool:
        """
        Updates only mutable forward outcome fields.
        Original geometric, price, and prediction levels must remain immutable.
        """
        pass

    @abstractmethod
    def get_forward_predictions(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Retrieves most recent forward prediction records."""
        pass

    @abstractmethod
    def get_forward_metrics(self) -> Dict[str, Any]:
        """Calculates prospective forward outcome performance statistics."""
        pass

    @abstractmethod
    def save_pattern(self, pattern: Dict[str, Any]):
        """Persists or updates pattern state in active scanner cache table."""
        pass

    @abstractmethod
    def save_patterns(self, patterns: List[Dict[str, Any]]):
        """Batch saves patterns."""
        pass

    @abstractmethod
    def record_event(self, event_dict: Dict[str, Any]):
        """Records a discrete pattern lifecycle event."""
        pass

    @abstractmethod
    def save_events(self, events: List[Dict[str, Any]]):
        """Batch saves pattern lifecycle events."""
        pass

    @abstractmethod
    def record_scanner_run(self, provider_name: str, mode: str, markets: int, patterns: int, duration: float):
        """Records telemetry for a scanner iteration."""
        pass

    @abstractmethod
    def get_recent_patterns(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recently detected patterns."""
        pass

    @abstractmethod
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent pattern lifecycle events."""
        pass
