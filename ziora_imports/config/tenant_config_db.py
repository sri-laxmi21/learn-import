"""
Tenant configuration management from database (Tenants table)
"""


import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from ..core.logger import get_logger

logger = get_logger(__name__)


class TenantInfo(BaseModel):
    """Tenant information model"""
    TenantPK: int
    TenantId: str
    Name: str
    DBString: str
    Enabled: int  # 0 or 1
    ContactEmail: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    @property
    def name(self) -> str:
        """Alias for TenantId"""
        return self.TenantId
    
    @property
    def display_name(self) -> str:
        """Alias for Name"""
        return self.Name
    
    @property
    def enabled(self) -> bool:
        """Convert Enabled (0/1) to boolean"""
        return self.Enabled == 1


class TenantConfigDB:
    """Manages tenant configuration from database"""
    
    def __init__(self, common_db_url: Optional[str] = None):
        """
        Initialize tenant configuration from database
        
        Args:
            common_db_url: Common database connection string. If None, loads from dbConfig.json
        """
        self.common_db_url = common_db_url or self._load_common_db_url()
        self._engine: Optional[Engine] = None
        self._tenants: Dict[str, TenantInfo] = {}
        
        if self.common_db_url:
            try:
                self._engine = create_engine(
                    self.common_db_url,
                    pool_pre_ping=True,
                    poolclass=None
                )
                self.load_config()
            except Exception as e:
                logger.error(f"Error initializing database connection: {str(e)}")
                self._engine = None
        else:
            logger.warning("Common database URL not configured. Tenant configuration will not be loaded.")
    
    def _load_common_db_url(self) -> Optional[str]:
        """Load common DB URL from dbConfig.json"""
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "dbConfig.json"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    return config_data.get('common_db', {}).get('connection_string')
            else:
                logger.warning(f"dbConfig.json not found at: {config_path}")
                return None
        except Exception as e:
            logger.error(f"Error loading dbConfig.json: {str(e)}")
            return None
    
    def load_config(self):
        """Load tenant configuration from Tenants table"""
        if not self._engine:
            logger.warning("Database engine not initialized. Cannot load tenant configuration.")
            return
        
        try:
            with self._engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT TenantPK, TenantId, Name, DBString, Enabled, ContactEmail, metadata
                        FROM Tenants
                        WHERE Enabled = 1
                    """)
                )
                
                for row in result:
                    try:
                        # Access columns by index (SQLAlchemy Row objects support indexing)
                        tenant_pk = row[0]
                        tenant_id = row[1]
                        name = row[2]
                        db_string = row[3]
                        enabled = row[4]
                        contact_email = row[5] if len(row) > 5 and row[5] is not None else None
                        metadata = row[6] if len(row) > 6 and row[6] is not None else {}
                        
                        tenant_info = TenantInfo(
                            TenantPK=tenant_pk,
                            TenantId=tenant_id,
                            Name=name,
                            DBString=db_string,
                            Enabled=enabled,
                            ContactEmail=contact_email,
                            metadata=metadata if isinstance(metadata, dict) else {}
                        )
                        # Store with lowercase TenantId as key for case-insensitive lookup
                        self._tenants[tenant_id.lower()] = tenant_info
                        logger.info(f"Loaded tenant configuration: {tenant_id} (PK: {tenant_pk})")
                    except Exception as e:
                        logger.error(f"Error loading tenant row: {str(e)}", exc_info=True)
            
            logger.info(f"Loaded {len(self._tenants)} tenant(s) from database")
        
        except Exception as e:
            logger.error(f"Error loading tenant configuration from database: {str(e)}")
    
    def get_tenant(self, tenant_id: str) -> Optional[TenantInfo]:
        """
        Get tenant information by TenantId (case-insensitive)
        
        Args:
            tenant_id: Tenant identifier (case-insensitive)
        
        Returns:
            TenantInfo object or None if not found
        """
        # Convert to lowercase for case-insensitive lookup
        tenant_id_lower = tenant_id.lower()
        return self._tenants.get(tenant_id_lower)
    
    def get_tenant_db_string(self, tenant_id: str) -> Optional[str]:
        """
        Get database connection string for tenant
        
        Args:
            tenant_id: Tenant identifier (case-insensitive)
        
        Returns:
            Database connection string or None if tenant not found
        """
        tenant = self.get_tenant(tenant_id)
        return tenant.DBString if tenant else None
    
    def is_tenant_enabled(self, tenant_id: str) -> bool:
        """
        Check if tenant exists and is enabled
        
        Args:
            tenant_id: Tenant identifier (case-insensitive)
        
        Returns:
            True if tenant exists and is enabled
        """
        tenant = self.get_tenant(tenant_id)
        return tenant is not None and tenant.enabled
    
    def list_tenants(self) -> list[str]:
        """List all configured tenant IDs"""
        return [tenant.TenantId for tenant in self._tenants.values()]
    
    def list_enabled_tenants(self) -> list[str]:
        """List all enabled tenant IDs"""
        return [tenant.TenantId for tenant in self._tenants.values() if tenant.enabled]
    
    def reload(self):
        """Reload tenant configuration from database"""
        self._tenants.clear()
        self.load_config()
    
    def close(self):
        """Close database connection"""
        if self._engine:
            self._engine.dispose()
            self._engine = None

