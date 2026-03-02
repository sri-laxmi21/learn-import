"""
File handling utilities
"""

from pathlib import Path
from typing import Optional
import shutil

from ..core.logger import get_logger

logger = get_logger(__name__)


class FileHandler:
    """Utility class for file operations"""
    
    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """
        Validate file path exists and is readable
        
        Args:
            file_path: Path to file
        
        Returns:
            True if file is valid
        """
        path = Path(file_path)
        return path.exists() and path.is_file()
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """
        Get file size in bytes
        
        Args:
            file_path: Path to file
        
        Returns:
            File size in bytes
        """
        return Path(file_path).stat().st_size
    
    @staticmethod
    def move_file(source: str, destination: str) -> bool:
        """
        Move file from source to destination
        
        Args:
            source: Source file path
            destination: Destination file path
        
        Returns:
            True if successful
        """
        try:
            shutil.move(source, destination)
            logger.info(f"File moved: {source} -> {destination}")
            return True
        except Exception as e:
            logger.error(f"Error moving file: {str(e)}")
            return False
    
    @staticmethod
    def archive_file(file_path: str, archive_dir: str) -> Optional[str]:
        """
        Archive file to archive directory
        
        Args:
            file_path: Path to file to archive
            archive_dir: Archive directory path
        
        Returns:
            Path to archived file or None if failed
        """
        try:
            archive_path = Path(archive_dir)
            archive_path.mkdir(parents=True, exist_ok=True)
            
            source_path = Path(file_path)
            archived_file = archive_path / source_path.name
            
            shutil.move(str(source_path), str(archived_file))
            logger.info(f"File archived: {file_path} -> {archived_file}")
            return str(archived_file)
        except Exception as e:
            logger.error(f"Error archiving file: {str(e)}")
            return None

