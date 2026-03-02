"""
Schema configuration management for file formats
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..core.logger import get_logger

logger = get_logger(__name__)


class SchemaConfig:
    """Manages schema configuration for different object types"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize schema configuration
        
        Args:
            config_path: Path to schemas.yaml configuration file
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "schemas.yaml"
        
        self.config_path = Path(config_path)
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.load_config()
    
    def load_config(self):
        """Load schema configuration from YAML file"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Schema config file not found: {self.config_path}")
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            self.schemas = config_data.get('schemas', {})
            
            for schema_name in self.schemas.keys():
                logger.info(f"Loaded schema configuration: {schema_name}")
        
        except Exception as e:
            logger.error(f"Error loading schema configuration: {str(e)}")
    
    def get_schema(self, object_type: str) -> Optional[Dict[str, Any]]:
        """
        Get schema configuration for object type
        
        Args:
            object_type: Type of object (emp, org, job, skill, etc.)
        
        Returns:
            Schema configuration dictionary or None if not found
        """
        return self.schemas.get(object_type.lower())
    
    def get_required_fields(self, object_type: str) -> List[str]:
        """
        Get required fields for object type
        
        Args:
            object_type: Type of object
        
        Returns:
            List of required field names
        """
        schema = self.get_schema(object_type)
        if schema:
            return schema.get('required_fields', [])
        return []
    
    def get_field_types(self, object_type: str) -> Dict[str, str]:
        """
        Get field types for object type
        
        Args:
            object_type: Type of object
        
        Returns:
            Dictionary mapping field names to types
        """
        schema = self.get_schema(object_type)
        if schema:
            return schema.get('field_types', {})
        return {}
    
    def get_unique_fields(self, object_type: str) -> List[str]:
        """
        Get unique fields for object type
        
        Args:
            object_type: Type of object
        
        Returns:
            List of unique field names
        """
        schema = self.get_schema(object_type)
        if schema:
            return schema.get('unique_fields', [])
        return []
    
    def list_object_types(self) -> List[str]:
        """List all configured object types"""
        return list(self.schemas.keys())

