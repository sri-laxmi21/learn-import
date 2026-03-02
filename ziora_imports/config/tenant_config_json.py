"""
Tenant configuration management - JSON version
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel

from ..core.logger import get_logger

logger = get_logger(__name__)


class TenantInfo(BaseModel):
    """Tenant information model"""
    name: str
    display_name: str
    database_url_env: str
    enabled: bool = True
    metadata: Dict[str, Any] = {}


class TenantConfig:
    """Manages tenant configuration"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize tenant configuration
        
        Args:
            config_path: Path to tenants.json or tenants.yaml configuration file
        """
        if config_path is None:
            # Try JSON first, fallback to YAML for backward compatibility
            json_path = Path(__file__).parent.parent.parent / "config" / "tenants.json"
            yaml_path = Path(__file__).parent.parent.parent / "config" / "tenants.yaml"
            
            if json_path.exists():
                config_path = json_path
            elif yaml_path.exists():
                config_path = yaml_path
            else:
                config_path = json_path  # Default to JSON
        
        self.config_path = Path(config_path)
        self.tenants: Dict[str, TenantInfo] = {}
        self.load_config()
    
    def load_config(self):
        """Load tenant configuration from JSON or YAML file"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Tenant config file not found: {self.config_path}")
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                if self.config_path.suffix.lower() == '.json':
                    config_data = json.load(f)
                elif self.config_path.suffix.lower() in ['.yaml', '.yml']:
                    import yaml
                    config_data = yaml.safe_load(f)
                else:
                    # Try JSON first, then YAML
                    try:
                        f.seek(0)
                        config_data = json.load(f)
                    except json.JSONDecodeError:
                        f.seek(0)
                        import yaml
                        config_data = yaml.safe_load(f)
            
            tenants_data = config_data.get('tenants', {})
            
            for tenant_name, tenant_data in tenants_data.items():
                try:
                    tenant_info = TenantInfo(
                        name=tenant_name,
                        display_name=tenant_data.get('display_name', tenant_name),
                        database_url_env=tenant_data.get('database_url_env', f"{tenant_name.upper()}_DB_URL"),
                        enabled=tenant_data.get('enabled', True),
                        metadata=tenant_data.get('metadata', {})
                    )
                    self.tenants[tenant_name] = tenant_info
                    logger.info(f"Loaded tenant configuration: {tenant_name}")
                except Exception as e:
                    logger.error(f"Error loading tenant {tenant_name}: {str(e)}")
        
        except Exception as e:
            logger.error(f"Error loading tenant configuration: {str(e)}")
    
    def get_tenant(self, tenant_name: str) -> Optional[TenantInfo]:
        """
        Get tenant information
        
        Args:
            tenant_name: Name of the tenant
        
        Returns:
            TenantInfo object or None if not found
        """
        return self.tenants.get(tenant_name)
    
    def is_tenant_enabled(self, tenant_name: str) -> bool:
        """
        Check if tenant is enabled
        
        Args:
            tenant_name: Name of the tenant
        
        Returns:
            True if tenant exists and is enabled
        """
        tenant = self.get_tenant(tenant_name)
        return tenant is not None and tenant.enabled
    
    def list_tenants(self) -> list[str]:
        """List all configured tenants"""
        return list(self.tenants.keys())
    
    def list_enabled_tenants(self) -> list[str]:
        """List all enabled tenants"""
        return [name for name, tenant in self.tenants.items() if tenant.enabled]

