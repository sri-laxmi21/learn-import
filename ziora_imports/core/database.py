"""
Database connection management for multi-tenant setup
"""

from typing import Dict, Optional
from sqlalchemy import create_engine, Engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os

from .logger import get_logger

logger = get_logger(__name__)

# Lazy import to avoid circular dependency
_tenant_config_db = None

def _get_tenant_config_db():
    """Get tenant config DB instance (lazy import)"""
    global _tenant_config_db
    if _tenant_config_db is None:
        from ..config.tenant_config_db import TenantConfigDB
        _tenant_config_db = TenantConfigDB()
    return _tenant_config_db


class DatabaseManager:
    """Manages database connections for multiple tenants"""
    
    def __init__(self):
        self._engines: Dict[str, Engine] = {}
        self._sessions: Dict[str, sessionmaker] = {}
    
    def get_connection_string(self, tenant_id: str) -> str:
        """
        Get database connection string for tenant from Tenants table
        
        Args:
            tenant_id: Tenant identifier (case-insensitive)
        
        Returns:
            Database connection string
        
        Raises:
            ValueError: If tenant not found or not enabled
        """
        # Try to get from database first
        tenant_config = _get_tenant_config_db()
        db_string = tenant_config.get_tenant_db_string(tenant_id)
        
        if db_string:
            logger.debug(f"Found tenant '{tenant_id}' in database")
            return db_string
        
        # Fallback to environment variable (for backward compatibility)
        env_var = f"{tenant_id.upper().replace('-', '_')}_DB_URL"
        db_url = os.getenv(env_var)
        
        if db_url:
            logger.warning(
                f"Tenant '{tenant_id}' not found in database, using environment variable {env_var}. "
                f"Consider migrating to Tenants table."
            )
            return db_url
        
        # Tenant not found
        raise ValueError(
            f"Tenant '{tenant_id}' not found in Tenants table and no environment variable {env_var} set. "
            f"Please add tenant to Tenants table or set the environment variable."
        )
    
    def get_engine(self, tenant_id: str) -> Engine:
        """
        Get or create database engine for tenant
        
        Args:
            tenant_id: Tenant identifier (case-insensitive)
        
        Returns:
            SQLAlchemy engine
        
        Raises:
            ValueError: If tenant not found or not enabled
        """
        # Use lowercase for consistent key storage
        tenant_key = tenant_id.lower()
        
        if tenant_key not in self._engines:
            db_url = self.get_connection_string(tenant_id)
            logger.info(f"Creating database engine for tenant: {tenant_id}")
            
            self._engines[tenant_key] = create_engine(
                db_url,
                poolclass=NullPool,
                echo=False,
                pool_pre_ping=True
            )
        
        return self._engines[tenant_key]
    
    def get_session(self, tenant_id: str) -> Session:
        """
        Get database session for tenant
        
        Args:
            tenant_id: Tenant identifier (case-insensitive)
        
        Returns:
            SQLAlchemy session
        
        Raises:
            ValueError: If tenant not found or not enabled
        """
        tenant_key = tenant_id.lower()
        
        if tenant_key not in self._sessions:
            engine = self.get_engine(tenant_id)
            self._sessions[tenant_key] = sessionmaker(bind=engine)
        
        Session = self._sessions[tenant_key]
        return Session()
    
    def close_all(self):
        """Close all database connections"""
        for tenant_name, engine in self._engines.items():
            logger.info(f"Closing database engine for tenant: {tenant_name}")
            engine.dispose()
        
        self._engines.clear()
        self._sessions.clear()
    
    def test_connection(self, tenant_id: str) -> bool:
        """
        Test database connection for tenant
        
        Args:
            tenant_id: Tenant identifier (case-insensitive)
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # First check if tenant exists
            tenant_config = _get_tenant_config_db()
            if not tenant_config.is_tenant_enabled(tenant_id):
                logger.error(f"Tenant '{tenant_id}' not found or not enabled")
                return False
            
            engine = self.get_engine(tenant_id)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info(f"Database connection test successful for tenant: {tenant_id}")
            return True
        except ValueError as e:
            # Tenant not found
            logger.error(f"Tenant validation failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Database connection test failed for tenant {tenant_id}: {str(e)}")
            return False


# Global database manager instance
db_manager = DatabaseManager()

