"""
Common fields configuration management
Fields that are common across all object types (Lang, Timezone, Country)
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from ..core.logger import get_logger

logger = get_logger(__name__)


class CommonFieldsConfig:
    """Manages common fields configuration"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize common fields configuration
        
        Args:
            config_path: Path to common_fields.json configuration file
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "common_fields.json"
        
        self.config_path = Path(config_path)
        self.common_fields: Dict[str, Dict[str, Any]] = {}
        self.load_config()
    
    def load_config(self):
        """Load common fields configuration from JSON file"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Common fields config file not found: {self.config_path}")
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            self.common_fields = config_data.get('common_fields', {})
            
            for field_name in self.common_fields.keys():
                logger.info(f"Loaded common field: {field_name}")
        
        except Exception as e:
            logger.error(f"Error loading common fields configuration: {str(e)}")
    
    def get_common_field(self, field_name: str) -> Optional[Dict[str, Any]]:
        """
        Get common field configuration
        
        Args:
            field_name: Name of the common field
        
        Returns:
            Field configuration dictionary or None if not found
        """
        return self.common_fields.get(field_name)
    
    def get_all_common_fields(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all common fields
        
        Returns:
            Dictionary of all common field configurations
        """
        return self.common_fields.copy()
    
    def is_common_field(self, field_name: str) -> bool:
        """
        Check if a field is a common field
        
        Args:
            field_name: Name of the field
        
        Returns:
            True if field is a common field
        """
        return field_name in self.common_fields

