"""
Base processor for data imports
"""

import pandas as pd
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path

from ..core.logger import get_logger
from ..core.database import DatabaseManager
from ..core.validator import DataValidator
from ..config.schema_config import SchemaConfig

logger = get_logger(__name__)


class BaseProcessor(ABC):
    """Base class for all import processors"""
    
    def __init__(
        self,
        tenant_name: str,
        object_type: str,
        schema_config: SchemaConfig,
        db_manager: DatabaseManager
    ):
        """
        Initialize processor
        
        Args:
            tenant_name: Name of the tenant
            object_type: Type of object being imported
            schema_config: Schema configuration instance
            db_manager: Database manager instance
        """
        self.tenant_name = tenant_name
        self.object_type = object_type
        self.schema_config = schema_config
        self.db_manager = db_manager
        # Use tenant-specific logger with object_type for filename prefix
        self.logger = get_logger(
            f"{__name__}.{object_type}", 
            tenant_name=tenant_name,
            object_type=object_type
        )
        self.validator = DataValidator(schema_config.schemas)
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """
        Process import file
        
        Args:
            file_path: Path to the import file
        
        Returns:
            Dictionary with processing results
        """
        self.logger.info(f"Starting file processing: {file_path}")
        
        result = {
            'success': False,
            'total_rows': 0,
            'processed_rows': 0,
            'failed_rows': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            # Load file
            df = self._load_file(file_path)
            result['total_rows'] = len(df)
            
            # Validate schema
            validation_result = self.validator.validate_schema(df, self.object_type)
            
            if not validation_result.is_valid:
                result['errors'].extend(validation_result.errors)
                result['failed_rows'] = validation_result.invalid_rows
                self.logger.error(f"Schema validation failed: {len(validation_result.errors)} errors")
            
            # Validate duplicates
            unique_fields = self.schema_config.get_unique_fields(self.object_type)
            if unique_fields:
                duplicate_result = self.validator.validate_duplicates(df, unique_fields)
                result['warnings'].extend(duplicate_result.warnings)
            
            # Transform data
            df_transformed = self._transform_data(df)
            
            # Store file path in dataframe attributes for use in _import_data
            df_transformed.attrs['file_path'] = file_path
            
            # Import data
            import_result = self._import_data(df_transformed)
            
            result['processed_rows'] = import_result.get('processed_rows', 0)
            result['failed_rows'] += import_result.get('failed_rows', 0)
            result['success'] = import_result.get('success', False)
            
            if result['success']:
                self.logger.info(
                    f"File processing completed successfully: "
                    f"{result['processed_rows']} rows processed"
                )
            else:
                self.logger.error(
                    f"File processing failed: {result['failed_rows']} rows failed"
                )
        
        except Exception as e:
            self.logger.error(f"Error processing file: {str(e)}", exc_info=True)
            result['errors'].append({
                'type': 'processing_error',
                'message': str(e)
            })
        
        return result
    
    def _load_file(self, file_path: str) -> pd.DataFrame:
        """
        Load file into DataFrame
        
        Supports multiple file formats:
        - CSV files (.csv) - comma-delimited
        - Excel files (.xlsx, .xls) - Excel format
        - Text files (.txt) - pipe-delimited (|)
        
        Args:
            file_path: Path to the file
        
        Returns:
            DataFrame with file data
        
        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file format is not supported
        """
        file_path_obj = Path(file_path)
        
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = file_path_obj.suffix.lower()
        self.logger.info(f"Loading file: {file_path} (format: {file_ext})")
        
        # Determine file type and load accordingly
        try:
            if file_ext == '.csv':
                # CSV file - comma-delimited
                df = pd.read_csv(file_path, encoding='utf-8')
                self.logger.debug("Loaded CSV file with comma delimiter")
                
            elif file_ext in ['.xlsx', '.xls']:
                # Excel file
                df = pd.read_excel(file_path, engine='openpyxl' if file_ext == '.xlsx' else None)
                self.logger.debug("Loaded Excel file")
            elif file_ext == '.txt':
                # Text file - pipe-delimited
                df = pd.read_csv(file_path, delimiter='|', encoding='utf-8')
                self.logger.debug("Loaded TXT file with pipe (|) delimiter")
                
            else:
                raise ValueError(
                    f"Unsupported file format: {file_ext}. "
                    f"Supported formats: .csv, .xlsx, .xls, .txt"
                )
            
            self.logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns from file")
            return df
            
        except pd.errors.EmptyDataError:
            raise ValueError(f"File is empty: {file_path}")
        except pd.errors.ParserError as e:
            raise ValueError(f"Error parsing file {file_path}: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error loading file {file_path}: {str(e)}")
    
    def _transform_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform data before import
        
        Args:
            df: Input DataFrame
        
        Returns:
            Transformed DataFrame
        """
        # Base implementation - can be overridden by subclasses
        return df
    
    @abstractmethod
    def _import_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Import data into database
        
        Args:
            df: DataFrame to import
        
        Returns:
            Dictionary with import results
        """
        pass
    
    def _get_session(self):
        """Get database session for tenant"""
        return self.db_manager.get_session(self.tenant_name)

