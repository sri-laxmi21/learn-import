"""
Job tracking module for import jobs
Supports shared database for job status tracking across tenants
"""

import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker,Session, relationship
import os

# Try to import UUID support, fallback to String if not available
try:
    from sqlalchemy.dialects.postgresql import UUID as PG_UUID
    UUID_TYPE = PG_UUID(as_uuid=True)
except ImportError:
    UUID_TYPE = String(36)  # Fallback to string UUID

from .logger import get_logger

logger = get_logger(__name__)

Base = declarative_base()


class ImportJob(Base):
    """Import job tracking table"""
    __tablename__ = 'import_jobs'
    
    job_id = Column(UUID_TYPE, primary_key=True, default=uuid.uuid4)
    tenant_id = Column(String, nullable=False, index=True)
    customer_id = Column(String, nullable=False, index=True)
    object_type = Column(String, nullable=False)
    source_file = Column(String, nullable=False)
    status = Column(String, nullable=False, default='queued')  # queued, processing, completed, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_summary = Column(Text, nullable=True)
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to import logs
    logs = relationship("ImportLog", back_populates="job", cascade="all, delete-orphan")


class ImportLog(Base):
    """Import log table for row-level tracking"""
    __tablename__ = 'import_logs'
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(UUID_TYPE, ForeignKey('import_jobs.job_id'), nullable=False, index=True)
    row_number = Column(Integer, nullable=False)
    status = Column(String, nullable=False)  # success, error, warning
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to import job
    job = relationship("ImportJob", back_populates="logs")


def _to_uuid(job_id: str):
    """Convert job_id string to UUID object"""
    try:
        return uuid.UUID(job_id) if isinstance(job_id, str) else job_id
    except (ValueError, AttributeError, TypeError):
        return job_id


class JobTracker:
    """Manages job tracking in shared database"""
    
    def __init__(self, shared_db_url: Optional[str] = None):
        """
        Initialize job tracker
        
        Args:
            shared_db_url: Database URL for shared job tracking database
                          If None, reads from SHARED_DB_URL environment variable
        """
        if shared_db_url is None:
            shared_db_url = os.getenv('SHARED_DB_URL')
        
        if not shared_db_url:
            logger.warning(
                "SHARED_DB_URL not configured. Job tracking will be disabled. "
                "Set SHARED_DB_URL environment variable to enable job tracking."
            )
            self.enabled = False
            self.engine = None
            self.Session = None
            return
        
        self.enabled = True
        self.engine = create_engine(shared_db_url, pool_pre_ping=True)
        self.Session = sessionmaker(bind=self.engine)
        
        # Create tables if they don't exist
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Job tracking tables initialized")
        except Exception as e:
            logger.error(f"Error initializing job tracking tables: {str(e)}")
            self.enabled = False
    
    def create_job(
        self,
        tenant_id: str,
        customer_id: str,
        object_type: str,
        source_file: str
    ) -> str:
        """
        Create a new import job
        
        Args:
            tenant_id: Tenant identifier
            customer_id: Customer identifier
            object_type: Type of object being imported
            source_file: Path to source file
        
        Returns:
            Job ID (UUID string)
        """
        if not self.enabled:
            return str(uuid.uuid4())
        
        session = self.Session()
        try:
            job = ImportJob(
                tenant_id=tenant_id,
                customer_id=customer_id,
                object_type=object_type,
                source_file=source_file,
                status='queued'
            )
            session.add(job)
            session.commit()
            job_id = str(job.job_id)
            logger.info(f"Created import job: {job_id} for tenant {tenant_id}, customer {customer_id}")
            return job_id
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating job: {str(e)}")
            raise
        finally:
            session.close()
    
    def update_job_status(
        self,
        job_id: str,
        status: str,
        error_summary: Optional[str] = None,
        total_rows: Optional[int] = None,
        processed_rows: Optional[int] = None,
        failed_rows: Optional[int] = None
    ):
        """
        Update job status
        
        Args:
            job_id: Job ID
            status: New status (queued, processing, completed, failed)
            error_summary: Error summary if failed
            total_rows: Total number of rows
            processed_rows: Number of processed rows
            failed_rows: Number of failed rows
        """
        if not self.enabled:
            return
        
        session = self.Session()
        try:
            job_uuid = _to_uuid(job_id)
            job = session.query(ImportJob).filter(ImportJob.job_id == job_uuid).first()
            if not job:
                logger.warning(f"Job not found: {job_id}")
                return
            
            job.status = status
            
            if status == 'processing' and not job.started_at:
                job.started_at = datetime.utcnow()
            elif status in ['completed', 'failed']:
                job.completed_at = datetime.utcnow()
            
            if error_summary is not None:
                job.error_summary = error_summary
            if total_rows is not None:
                job.total_rows = total_rows
            if processed_rows is not None:
                job.processed_rows = processed_rows
            if failed_rows is not None:
                job.failed_rows = failed_rows
            
            session.commit()
            logger.debug(f"Updated job {job_id} status to {status}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating job status: {str(e)}")
        finally:
            session.close()
    
    def add_log_entry(
        self,
        job_id: str,
        row_number: int,
        status: str,
        error_message: Optional[str] = None
    ):
        """
        Add log entry for a row
        
        Args:
            job_id: Job ID
            row_number: Row number in the file
            status: Status (success, error, warning)
            error_message: Error message if any
        """
        if not self.enabled:
            return
        
        session = self.Session()
        try:
            log_entry = ImportLog(
                job_id=_to_uuid(job_id),
                row_number=row_number,
                status=status,
                error_message=error_message
            )
            session.add(log_entry)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error adding log entry: {str(e)}")
        finally:
            session.close()
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status
        
        Args:
            job_id: Job ID
        
        Returns:
            Dictionary with job status information
        """
        if not self.enabled:
            return None
        
        session = self.Session()
        try:
            job_uuid = _to_uuid(job_id)
            job = session.query(ImportJob).filter(ImportJob.job_id == job_uuid).first()
            if not job:
                return None
            
            return {
                'job_id': str(job.job_id),
                'tenant_id': job.tenant_id,
                'customer_id': job.customer_id,
                'object_type': job.object_type,
                'source_file': job.source_file,
                'status': job.status,
                'started_at': job.started_at.isoformat() if job.started_at else None,
                'completed_at': job.completed_at.isoformat() if job.completed_at else None,
                'error_summary': job.error_summary,
                'total_rows': job.total_rows,
                'processed_rows': job.processed_rows,
                'failed_rows': job.failed_rows,
                'created_at': job.created_at.isoformat() if job.created_at else None
            }
        except Exception as e:
            logger.error(f"Error getting job status: {str(e)}")
            return None
        finally:
            session.close()
    
    def get_job_logs(self, job_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get log entries for a job
        
        Args:
            job_id: Job ID
            limit: Maximum number of log entries to return
        
        Returns:
            List of log entry dictionaries
        """
        if not self.enabled:
            return []
        
        session = self.Session()
        try:
            logs = session.query(ImportLog).filter(
                ImportLog.job_id == _to_uuid(job_id)
            ).order_by(ImportLog.row_number).limit(limit).all()
            
            return [
                {
                    'log_id': log.log_id,
                    'row_number': log.row_number,
                    'status': log.status,
                    'error_message': log.error_message,
                    'created_at': log.created_at.isoformat() if log.created_at else None
                }
                for log in logs
            ]
        except Exception as e:
            logger.error(f"Error getting job logs: {str(e)}")
            return []
        finally:
            session.close()

