"""
Main entry point for Ziora data imports
"""

import argparse
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(override=True)

from ziora_imports.core.logger import setup_logger, get_logger
from ziora_imports.core.database import db_manager
from ziora_imports.config.tenant_config_db import TenantConfigDB
from ziora_imports.config.schema_config import SchemaConfig
from ziora_imports.processors import (
    EmpProcessor,
    OrgProcessor,
    JobProcessor,
    SkillProcessor,
    EmpAssociationsProcessor
)


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


def get_processor(object_type: str, tenant_name: str, schema_config: SchemaConfig):
    """
    Get processor instance for object type
    
    Args:
        object_type: Type of object (emp, org, job, skill)
        tenant_name: Name of the tenant
        schema_config: Schema configuration instance
    
    Returns:
        Processor instance
    """
    processor_class = PROCESSOR_MAP.get(object_type.lower())
    
    if not processor_class:
        raise ValueError(
            f"Unknown object type: {object_type}. "
            f"Supported types: {', '.join(PROCESSOR_MAP.keys())}"
        )
    
    return processor_class(tenant_name, schema_config, db_manager)


def process_batch_import(tenant_id: str, files_dir: str, logger, tenant_config, schema_config):
    """
    Process all files for a tenant in the correct order
    
    Processing order: org → job → skill → emp → emp_associations
    
    Args:
        tenant_id: Tenant identifier (case-insensitive, will be lowercased)
        files_dir: Directory containing import files
        logger: Logger instance
        tenant_config: Tenant configuration instance
        schema_config: Schema configuration instance
    
    Returns:
        Dictionary with batch processing results
    """
    from pathlib import Path
    
    files_path = Path(files_dir)
    if not files_path.exists():
        raise ValueError(f"Files directory does not exist: {files_dir}")
    
    # File name mapping (object_type -> expected filename patterns)
    # Supports .csv, .xlsx, and .txt (pipe-delimited) file extensions
    file_patterns = {
        'org': [
            'org.csv', 'org.xlsx', 'org.txt',
            'organization.csv', 'organization.xlsx', 'organization.txt'
        ],
        'job': [
            'job.csv', 'job.xlsx', 'job.txt',
            'jobs.csv', 'jobs.xlsx', 'jobs.txt'
        ],
        'skill': [
            'skill.csv', 'skill.xlsx', 'skill.txt',
            'skills.csv', 'skills.xlsx', 'skills.txt'
        ],
        'emp': [
            'emp.csv', 'emp.xlsx', 'emp.txt',
            'employee.csv', 'employee.xlsx', 'employee.txt',
            'person.csv', 'person.xlsx', 'person.txt'
        ],
        'emp_associations': [
            'emp_associations.csv', 'emp_associations.xlsx', 'emp_associations.txt',
            'associations.csv', 'associations.xlsx', 'associations.txt'
        ]
    }
    
    batch_results = {
        'success': True,
        'processed': [],
        'failed': [],
        'skipped': []
    }
    
    logger.info("=" * 60)
    logger.info("Batch Import - Processing files in order")
    logger.info("=" * 60)
    logger.info(f"Processing order: {' → '.join(PROCESSING_ORDER)}")
    
    # Process files in order
    for object_type in PROCESSING_ORDER:
        logger.info(f"\n--- Processing {object_type.upper()} ---")
        
        # Find file for this object type
        file_path = None
        for pattern in file_patterns.get(object_type, [f"{object_type}.csv"]):
            potential_file = files_path / pattern
            if potential_file.exists():
                file_path = potential_file
                break
        
        if not file_path:
            logger.warning(f"No file found for {object_type}, skipping...")
            batch_results['skipped'].append({
                'object_type': object_type,
                'reason': 'File not found'
            })
            continue
        
        try:
            # Get processor
            processor = get_processor(object_type, tenant_id, schema_config)
            
            # Process file
            logger.info(f"Processing: {file_path.name}")
            result = processor.process_file(str(file_path))
            
            if result['success']:
                logger.info(f"✓ {object_type}: {result['processed_rows']} rows processed")
                batch_results['processed'].append({
                    'object_type': object_type,
                    'file': str(file_path),
                    'processed_rows': result['processed_rows'],
                    'failed_rows': result['failed_rows']
                })
            else:
                logger.error(f"✗ {object_type}: Failed - {result['failed_rows']} rows failed")
                batch_results['failed'].append({
                    'object_type': object_type,
                    'file': str(file_path),
                    'errors': result['errors'][:5]  # First 5 errors
                })
                batch_results['success'] = False
                
        except Exception as e:
            logger.error(f"✗ {object_type}: Error - {str(e)}", exc_info=True)
            batch_results['failed'].append({
                'object_type': object_type,
                'file': str(file_path) if file_path else 'unknown',
                'error': str(e)
            })
            batch_results['success'] = False
    
    return batch_results


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Ziora Data Imports - Multi-tenant data import system'
    )
    
    parser.add_argument(
        '--tenant',
        required=True,
        help='Tenant name (e.g., acme_corp, technova)'
    )
    
    parser.add_argument(
        '--object',
        required=False,
        choices=['emp', 'org', 'job', 'skill', 'emp_associations'],
        help='Object type to import (optional if using --batch)'
    )
    
    parser.add_argument(
        '--file',
        required=False,
        help='Path to the import file (optional if using --batch)'
    )
    
    parser.add_argument(
        '--batch',
        action='store_true',
        help='Process all files for tenant in correct order (org, job, skill, emp, emp_associations)'
    )
    
    parser.add_argument(
        '--files-dir',
        help='Directory containing import files (used with --batch). Files should be named: org.csv, job.csv, skill.csv, emp.csv, emp_associations.csv'
    )
    
    parser.add_argument(
        '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        help='Logging level'
    )
    
    parser.add_argument(
        '--log-dir',
        default='logs',
        help='Directory for log files'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.batch:
        if not args.files_dir:
            parser.error("--files-dir is required when using --batch")
    else:
        if not args.object or not args.file:
            parser.error("--object and --file are required when not using --batch")
    
    # Setup logging
    logger = setup_logger(
        log_level=args.log_level,
        log_dir=args.log_dir,
        tenant_name=args.tenant,
        object_type=args.object if not args.batch else 'batch'
    )
    
    logger.info("=" * 60)
    logger.info("Ziora Data Imports - Starting Import Process")
    logger.info("=" * 60)
    logger.info(f"Tenant: {args.tenant}")
    
    try:
        # Load configurations
        tenant_config = TenantConfigDB()
        schema_config = SchemaConfig()
        
        # Validate tenant exists and is enabled (case-insensitive lookup)
        tenant_id_lower = args.tenant.lower()
        if not tenant_config.is_tenant_enabled(tenant_id_lower):
            logger.error(f"Tenant '{args.tenant}' not found in Tenants table or not enabled")
            available_tenants = tenant_config.list_enabled_tenants()
            if available_tenants:
                logger.info(f"Available tenants: {', '.join(available_tenants)}")
            else:
                logger.info("No enabled tenants found in Tenants table")
            sys.exit(1)
        
        # Get actual tenant info for logging
        tenant_info = tenant_config.get_tenant(tenant_id_lower)
        if tenant_info:
            logger.info(f"Tenant found: {tenant_info.Name} (ID: {tenant_info.TenantId}, PK: {tenant_info.TenantPK})")
        
        # Test database connection (uses tenant_id from database)
        logger.info(f"Testing database connection for tenant: {args.tenant}")
        if not db_manager.test_connection(tenant_id_lower):
            logger.error(f"Database connection test failed for tenant: {args.tenant}")
            logger.error("Processing stopped - tenant not found or database connection failed")
            sys.exit(1)
        
        # Batch processing
        if args.batch:
            logger.info(f"Batch mode: Processing all files from {args.files_dir}")
            batch_results = process_batch_import(
                tenant_id_lower,  # Use lowercase tenant_id
                args.files_dir,
                logger,
                tenant_config,
                schema_config
            )
            
            # Print batch results summary
            logger.info("\n" + "=" * 60)
            logger.info("Batch Import Summary")
            logger.info("=" * 60)
            logger.info(f"Success: {batch_results['success']}")
            logger.info(f"Processed: {len(batch_results['processed'])} files")
            logger.info(f"Failed: {len(batch_results['failed'])} files")
            logger.info(f"Skipped: {len(batch_results['skipped'])} files")
            
            if batch_results['processed']:
                logger.info("\nProcessed Files:")
                for item in batch_results['processed']:
                    logger.info(f"  ✓ {item['object_type']}: {item['processed_rows']} rows")
            
            if batch_results['failed']:
                logger.error("\nFailed Files:")
                for item in batch_results['failed']:
                    logger.error(f"  ✗ {item['object_type']}: {item.get('error', 'See errors above')}")
            
            sys.exit(0 if batch_results['success'] else 1)
        
        # Single file processing
        else:
            logger.info(f"Object Type: {args.object}")
            logger.info(f"File: {args.file}")
            
            # Validate object type
            if args.object.lower() not in schema_config.list_object_types():
                logger.error(f"Object type '{args.object}' is not configured")
                logger.info(f"Available object types: {', '.join(schema_config.list_object_types())}")
                sys.exit(1)
            
            # Get processor (use lowercase tenant_id)
            processor = get_processor(args.object, tenant_id_lower, schema_config)
            
            # Process file
            logger.info(f"Processing file: {args.file}")
            result = processor.process_file(args.file)
            
            # Print results
            logger.info("=" * 60)
            logger.info("Import Results")
            logger.info("=" * 60)
            logger.info(f"Success: {result['success']}")
            logger.info(f"Total Rows: {result['total_rows']}")
            logger.info(f"Processed Rows: {result['processed_rows']}")
            logger.info(f"Failed Rows: {result['failed_rows']}")
            
            if result['errors']:
                logger.error(f"Errors: {len(result['errors'])}")
                for error in result['errors'][:10]:  # Show first 10 errors
                    logger.error(f"  - {error}")
                if len(result['errors']) > 10:
                    logger.error(f"  ... and {len(result['errors']) - 10} more errors")
            
            if result['warnings']:
                logger.warning(f"Warnings: {len(result['warnings'])}")
                for warning in result['warnings'][:10]:  # Show first 10 warnings
                    logger.warning(f"  - {warning}")
                if len(result['warnings']) > 10:
                    logger.warning(f"  ... and {len(result['warnings']) - 10} more warnings")
            
            # Exit with appropriate code
            if result['success']:
                logger.info("Import completed successfully")
                sys.exit(0)
            else:
                logger.error("Import completed with errors")
                sys.exit(1)
    
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)
    
    finally:
        # Cleanup
        db_manager.close_all()


if __name__ == '__main__':
    main()

