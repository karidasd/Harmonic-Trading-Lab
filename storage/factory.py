import os
import re
import logging
from urllib.parse import urlparse, urlunparse
from typing import Optional
from storage.base import BaseForwardStore
from storage.sqlite_store import SQLiteForwardStore
from storage.postgres_store import PostgresForwardStore

logger = logging.getLogger(__name__)

def mask_database_url(url: Optional[str]) -> str:
    """
    Safely masks sensitive credentials in a database connection URL.
    Replaces user:password@host with user:****@host.
    """
    if not url:
        return "None"
    try:
        parsed = urlparse(url)
        if parsed.password:
            user_part = parsed.username or ''
            host_part = parsed.hostname or ''
            port_part = f":{parsed.port}" if parsed.port else ''
            netloc = f"{user_part}:****@{host_part}{port_part}"
            return urlunparse(parsed._replace(netloc=netloc))
        return url
    except Exception:
        return re.sub(r'://([^:]+):(.*)@([^/]+)', r'://\1:****@\3', url)

class StoreFactory:
    """
    Factory for instantiating the appropriate forward prediction storage backend.
    Enforces security, fallback resilience, and configuration transparency.
    """

    _instance: Optional[BaseForwardStore] = None

    @classmethod
    def get_database_url(cls) -> Optional[str]:
        # 1. Check OS Environment Variable
        env_url = os.environ.get("DATABASE_URL")
        if env_url and env_url.strip():
            return env_url.strip()

        # 2. Check Streamlit Cloud Secrets (if running in Streamlit context)
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "DATABASE_URL" in st.secrets:
                secret_url = st.secrets["DATABASE_URL"]
                if secret_url and str(secret_url).strip():
                    return str(secret_url).strip()
        except Exception:
            pass

        return None

    @classmethod
    def get_store(cls, force_sqlite: bool = False, custom_url: Optional[str] = None) -> BaseForwardStore:
        if force_sqlite:
            return SQLiteForwardStore()

        db_url = custom_url or cls.get_database_url()

        if db_url:
            masked = mask_database_url(db_url)
            try:
                pg_store = PostgresForwardStore(db_url)
                check = pg_store.health_check()
                if check.get('status') == 'HEALTHY':
                    logger.info(f"Connected to persistent PostgreSQL store: {masked}")
                    return pg_store
                else:
                    logger.warning(f"PostgreSQL store at {masked} failed health check: {check.get('error')}. Falling back to degraded SQLite mode.")
            except Exception as e:
                logger.error(f"Failed to initialize PostgreSQL store ({masked}): {e}. Falling back to SQLite.")

        # Fallback to local SQLite storage
        return SQLiteForwardStore()

    @classmethod
    def reset_instance(cls):
        cls._instance = None
