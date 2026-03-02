"""
Schema configuration management for file formats - JSON version
Supports enhanced field attributes like length, data type, required, etc.
"""

import json
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
            config_path: Path to schemas.json configuration file
        """
        if config_path is None:
            # Try JSON first, fallback to YAML for backward compatibility
            json_path = Path(__file__).parent.parent.parent / "config" / "schemas.json"
            yaml_path = Path(__file__).parent.parent.parent / "config" / "schemas.yaml"
            
            if json_path.exists():
                config_path = json_path
            elif yaml_path.exists():
                config_path = yaml_path
            else:
                config_path = json_path  # Default to JSON
        
        self.config_path = Path(config_path)
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self.load_config()
    
    def load_config(self):
        """Load schema configuration from JSON or YAML file"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Schema config file not found: {self.config_path}")
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
            
            self.schemas = config_data.get('schemas', {})
            
            # Expand field patterns and normalize field_types structure
            for schema_name, schema in self.schemas.items():
                # Expand field patterns into individual fields
                field_patterns = schema.get('field_patterns', {})
                field_types = schema.get('field_types', {})
                
                # Expand patterns
                for pattern_name, pattern_config in field_patterns.items():
                    prefix = pattern_config.get('prefix', pattern_name)
                    range_start, range_end = pattern_config.get('range', [1, 1])
                    description_template = pattern_config.get('description_template', "{prefix} {n}")
                    
                    # Create base field config from pattern (excluding pattern-specific keys)
                    base_config = {k: v for k, v in pattern_config.items() 
                                 if k not in ['prefix', 'range', 'description_template']}
                    
                    # Generate fields for the range
                    for n in range(range_start, range_end + 1):
                        field_name = f"{prefix}{n}"
                        field_config = base_config.copy()
                        # Replace {n} and {prefix} in description
                        if 'description' in field_config:
                            field_config['description'] = field_config['description'].replace('{n}', str(n)).replace('{prefix}', prefix)
                        elif description_template:
                            field_config['description'] = description_template.replace('{n}', str(n)).replace('{prefix}', prefix)
                        field_types[field_name] = field_config
                
                # Normalize field_types structure for backward compatibility
                # If field_types is a dict of strings (old format), convert to new format
                if field_types and isinstance(list(field_types.values())[0] if field_types else None, str):
                    # Old format: {"field_name": "string"}
                    # Convert to new format: {"field_name": {"type": "string", "required": false}}
                    normalized = {}
                    required_fields = set(schema.get('required_fields', []))
                    for field_name, field_type in field_types.items():
                        normalized[field_name] = {
                            "type": field_type,
                            "required": field_name in required_fields
                        }
                    schema['field_types'] = normalized
                else:
                    schema['field_types'] = field_types
                
                # Remove field_patterns from schema (already expanded)
                if 'field_patterns' in schema:
                    del schema['field_patterns']
            
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
    
    def get_field_types(self, object_type: str) -> Dict[str, Any]:
        """
        Get field types for object type (enhanced format with attributes)
        
        Args:
            object_type: Type of object
        
        Returns:
            Dictionary mapping field names to type info (dict with type, length, required, etc.)
            or simple string type for backward compatibility
        """
        schema = self.get_schema(object_type)
        if schema:
            return schema.get('field_types', {})
        return {}
    
    def get_field_type(self, object_type: str, field_name: str) -> Optional[str]:
        """
        Get simple field type string for a specific field
        
        Args:
            object_type: Type of object
            field_name: Name of the field
        
        Returns:
            Field type string (e.g., "string", "integer", "float", "date", "boolean")
        """
        field_types = self.get_field_types(object_type)
        field_info = field_types.get(field_name)
        
        if isinstance(field_info, dict):
            return field_info.get('type')
        elif isinstance(field_info, str):
            return field_info
        return None
    
    def get_field_length(self, object_type: str, field_name: str) -> Optional[int]:
        """
        Get maximum length for a field
        
        Args:
            object_type: Type of object
            field_name: Name of the field
        
        Returns:
            Maximum length or None if not specified
        """
        field_types = self.get_field_types(object_type)
        field_info = field_types.get(field_name)
        
        if isinstance(field_info, dict):
            return field_info.get('length')
        return None
    
    def is_field_required(self, object_type: str, field_name: str) -> bool:
        """
        Check if a field is required
        
        Args:
            object_type: Type of object
            field_name: Name of the field
        
        Returns:
            True if field is required
        """
        required_fields = self.get_required_fields(object_type)
        if field_name in required_fields:
            return True
        
        # Also check field_types for required attribute
        field_types = self.get_field_types(object_type)
        field_info = field_types.get(field_name)
        if isinstance(field_info, dict):
            return field_info.get('required', False)
        
        return False
    
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
    
    def get_validations(self, object_type: str) -> Dict[str, Dict[str, Any]]:
        """
        Get validation rules for object type
        
        Args:
            object_type: Type of object
        
        Returns:
            Dictionary mapping field names to validation rules
        """
        schema = self.get_schema(object_type)
        if schema:
            return schema.get('validations', {})
        return {}
    
    def list_object_types(self) -> List[str]:
        """List all configured object types"""
        return list(self.schemas.keys())

