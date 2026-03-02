"""
FastAPI service for HTTP-based import invocation
Supports React → .NET API → Python Service architecture
"""

import os
from typing import Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

from ..core.logger import setup_logger, get_logger
from ..core.database import db_manager
from ..core.job_tracker import JobTracker
from ..config.tenant_config import TenantConfig
from ..config.schema_config import SchemaConfig
from ..processors import (
    EmpProcessor,
    OrgProcessor,
    JobProcessor,
    SkillProcessor,
    EmpAssociationsProcessor
)

# Load environment variables
load_dotenv()

# Initialize components
app = FastAPI(
    title="Ziora Data Imports API",
    description="Multi-tenant data import service for Ziora",
    version="1.0.0"
)

tenant_config = TenantConfig()
schema_config = SchemaConfig()
job_tracker = JobTracker()

# Processor mapping
PROCESSOR_MAP = {
    'emp': EmpProcessor,
    'org': OrgProcessor,
    'job': JobProcessor,
    'skill': SkillProcessor,
    'emp_associations': EmpAssociationsProcessor
}

# Processing order for batch imports
PROCESSING_ORDER = ['org', 'job', 'skill', 'emp', 'emp_associations']


class ImportRequest(BaseModel):
    """Import request model"""
    tenant_id: str
    customer_id: str
    object_type: str
    file_path: str
    task_id: Optional[str] = None


class ImportResponse(BaseModel):
    """Import response model"""
    status: str
    job_id: str
    message: str


class JobStatusResponse(BaseModel):
    """Job status response model"""
    job_id: str
    status: str
    tenant_id: str
    customer_id: str
    object_type: str
    source_file: str
    total_rows: int
    processed_rows: int
    failed_rows: int
    started_at: Optional[str]
    completed_at: Optional[str]
    error_summary: Optional[str]


def get_processor(object_type: str, tenant_name: str, schema_config: SchemaConfig):
    """Get processor instance for object type"""
    processor_class = PROCESSOR_MAP.get(object_type.lower())
    
    if not processor_class:
        raise ValueError(
            f"Unknown object type: {object_type}. "
            f"Supported types: {', '.join(PROCESSOR_MAP.keys())}"
        )
    
    return processor_class(tenant_name, schema_config, db_manager)


def process_file_import(
    tenant_id: str,
    customer_id: str,
    object_type: str,
    file_path: str,
    job_id: str
):
    """
    Process file import in background
    
    Args:
        tenant_id: Tenant identifier
        customer_id: Customer identifier
        object_type: Type of object being imported
        file_path: Path to the import file
        job_id: Job ID for tracking
    """
    # Setup tenant-specific logger with object_type for filename prefix
    logger = setup_logger(
        name="ziora_imports",
        tenant_name=tenant_id,
        object_type=object_type,
        log_level=os.getenv('LOG_LEVEL', 'INFO')
    )
    
    logger.info(f"Starting background import job {job_id}")
    logger.info(f"Tenant: {tenant_id}, Customer: {customer_id}, Object: {object_type}")
    logger.info(f"File: {file_path}")
    
    try:
        # Update job status to processing
        job_tracker.update_job_status(job_id, 'processing')
        
        # Validate tenant
        if not tenant_config.is_tenant_enabled(tenant_id):
            error_msg = f"Tenant '{tenant_id}' is not enabled or does not exist"
            logger.error(error_msg)
            job_tracker.update_job_status(job_id, 'failed', error_summary=error_msg)
            return
        
        # Validate object type
        if object_type.lower() not in schema_config.list_object_types():
            error_msg = f"Object type '{object_type}' is not configured"
            logger.error(error_msg)
            job_tracker.update_job_status(job_id, 'failed', error_summary=error_msg)
            return
        
        # Test database connection
        if not db_manager.test_connection(tenant_id):
            error_msg = f"Database connection test failed for tenant: {tenant_id}"
            logger.error(error_msg)
            job_tracker.update_job_status(job_id, 'failed', error_summary=error_msg)
            return
        
        # Get processor
        processor = get_processor(object_type, tenant_id, schema_config)
        
        # Process file
        logger.info(f"Processing file: {file_path}")
        result = processor.process_file(file_path)
        
        # Update job status
        if result['success']:
            job_tracker.update_job_status(
                job_id,
                'completed',
                total_rows=result.get('total_rows', 0),
                processed_rows=result.get('processed_rows', 0),
                failed_rows=result.get('failed_rows', 0)
            )
            logger.info(
                f"Import completed successfully: "
                f"{result.get('processed_rows', 0)} rows processed"
            )
        else:
            error_summary = f"Failed to process {result.get('failed_rows', 0)} rows"
            if result.get('errors'):
                error_summary += f". First error: {result['errors'][0]}"
            
            job_tracker.update_job_status(
                job_id,
                'failed',
                error_summary=error_summary,
                total_rows=result.get('total_rows', 0),
                processed_rows=result.get('processed_rows', 0),
                failed_rows=result.get('failed_rows', 0)
            )
            logger.error(f"Import failed: {error_summary}")
    
    except Exception as e:
        error_msg = f"Fatal error during import: {str(e)}"
        logger.error(error_msg, exc_info=True)
        job_tracker.update_job_status(job_id, 'failed', error_summary=error_msg)


@app.post("/import", response_model=ImportResponse)
async def create_import_job(
    request: ImportRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new import job
    
    This endpoint is called by .NET API to trigger file import
    """
    logger = get_logger("ziora_imports")
    
    try:
        # Validate tenant
        if not tenant_config.is_tenant_enabled(request.tenant_id):
            raise HTTPException(
                status_code=400,
                detail=f"Tenant '{request.tenant_id}' is not enabled or does not exist"
            )
        
        # Validate object type
        if request.object_type.lower() not in schema_config.list_object_types():
            raise HTTPException(
                status_code=400,
                detail=f"Object type '{request.object_type}' is not supported"
            )
        
        # Create job
        job_id = job_tracker.create_job(
            tenant_id=request.tenant_id,
            customer_id=request.customer_id,
            object_type=request.object_type,
            source_file=request.file_path
        )
        
        # Queue background task
        background_tasks.add_task(
            process_file_import,
            request.tenant_id,
            request.customer_id,
            request.object_type,
            request.file_path,
            job_id
        )
        
        logger.info(f"Created import job {job_id} for tenant {request.tenant_id}")
        
        return ImportResponse(
            status="queued",
            job_id=job_id,
            message=f"Import job {job_id} has been queued for processing"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating import job: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get status of an import job
    
    This endpoint is called by .NET API for React to poll job status
    """
    logger = get_logger("ziora_imports")
    
    try:
        status = job_tracker.get_job_status(job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return JobStatusResponse(**status)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status: {job_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Ziora Data Imports API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

