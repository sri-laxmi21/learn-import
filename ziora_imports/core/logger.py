"""
Centralized logging module for all file processing and validation.

Features:
- Outputs ONLY message text (no timestamp, level, filename, etc.)
- Supports per-tenant log directories
- Supports per-object log files
- Structured SUCCESS / WARNING / ERROR logging
- Import summary logging support
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


class ZioraLogger:
    """Centralized logger for Ziora imports with per-tenant log support"""

    _loggers = {}
    _base_log_dir = Path("logs")

    # ==========================================================
    # Logger Setup
    # ==========================================================
    @classmethod
    def setup_logger(
        cls,
        name: str = "ziora_imports",
        log_level: str = "INFO",
        log_dir: Optional[str] = None,
        tenant_name: Optional[str] = None,
        object_type: Optional[str] = None,
    ) -> logging.Logger:

        # Unique logger key
        if tenant_name and object_type:
            logger_key = f"{name}_{tenant_name}_{object_type}"
        elif tenant_name:
            logger_key = f"{name}_{tenant_name}"
        else:
            logger_key = name

        if logger_key in cls._loggers:
            return cls._loggers[logger_key]

        # Log directory creation
        base_log_dir = Path(log_dir) if log_dir else cls._base_log_dir
        actual_log_dir = base_log_dir / tenant_name if tenant_name else base_log_dir
        actual_log_dir.mkdir(parents=True, exist_ok=True)

        # Create logger
        logger = logging.getLogger(logger_key)
        logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        logger.propagate = False

        if logger.handlers:
            return logger

        # Console handler (ONLY MESSAGE)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(console_handler)

        # File handler (ONLY MESSAGE)
        prefix = object_type.lower() if object_type else "ziora_imports"
        log_file = actual_log_dir / f"{prefix}_{datetime.now().strftime('%Y%m%d')}.log"

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(file_handler)

        cls._loggers[logger_key] = logger
        return logger

    # ==========================================================
    # Get Logger
    # ==========================================================
    @classmethod
    def get_logger(
        cls,
        name: str = "ziora_imports",
        tenant_name: Optional[str] = None,
        object_type: Optional[str] = None,
    ) -> logging.Logger:

        if tenant_name and object_type:
            logger_key = f"{name}_{tenant_name}_{object_type}"
        elif tenant_name:
            logger_key = f"{name}_{tenant_name}"
        else:
            logger_key = name

        if logger_key not in cls._loggers:
            return cls.setup_logger(
                name=name,
                tenant_name=tenant_name,
                object_type=object_type,
            )

        return cls._loggers[logger_key]

    # ==========================================================
    # Structured Logging Helpers
    # ==========================================================
    @staticmethod
    def log_success(logger: logging.Logger, message: str):
        logger.info(f"[SUCCESS] {message}")

    @staticmethod
    def log_warning(logger: logging.Logger, message: str):
        logger.warning(f"[WARNING] {message}")

    @staticmethod
    def log_error(logger: logging.Logger, message: str):
        logger.error(f"[ERROR] {message}")

    # ==========================================================
    # Record-Level Logging
    # ==========================================================
    @staticmethod
    def record_inserted(logger: logging.Logger, org_id: str, org_name: str):
        logger.info(
            f"[SUCCESS] org_id={org_id} | org_name={org_name} | Inserted successfully"
        )

    @staticmethod
    def record_warning(logger: logging.Logger, org_id: str, org_name: str, reason: str):
        logger.warning(
            f"[WARNING] org_id={org_id} | org_name={org_name} | {reason}"
        )

    @staticmethod
    def record_error(logger: logging.Logger, org_id: str, org_name: str, reason: str):
        logger.error(
            f"[ERROR] org_id={org_id} | org_name={org_name} | {reason}"
        )

    @staticmethod
    def record_detailed(logger: logging.Logger, status: str, fields: dict, message: str = ""):
        """Log a record with all provided fields dynamically"""
        field_str = " | ".join([f"{k}={v}" for k, v in fields.items() if v is not None])
        msg_suffix = f" | {message}" if message else ""
        log_msg = f"[{status.upper()}] {field_str}{msg_suffix}"
        
        if status.upper() == 'SUCCESS':
            logger.info(log_msg)
        elif status.upper() == 'WARNING':
            logger.warning(log_msg)
        else:
            logger.error(log_msg)

    # ==========================================================
    # Import Summary Logging
    # ==========================================================
    @staticmethod
    def log_summary(
        logger: logging.Logger,
        total: int,
        success: int,
        warnings: int,
        failed: int,
    ):
        logger.info("--------------------------------------------------")
        logger.info("[IMPORT SUMMARY]")
        logger.info(f"Total Records   : {total}")
        logger.info(f"Successful      : {success}")
        logger.info(f"Warnings        : {warnings}")
        logger.info(f"Failed          : {failed}")
        logger.info("--------------------------------------------------")


# ==========================================================
# Shortcut functions (optional use)
# ==========================================================

def setup_logger(
    name: str = "ziora_imports",
    log_level: str = "INFO",
    log_dir: Optional[str] = None,
    tenant_name: Optional[str] = None,
    object_type: Optional[str] = None,
) -> logging.Logger:
    return ZioraLogger.setup_logger(
        name, log_level, log_dir, tenant_name, object_type
    )


def get_logger(
    name: str = "ziora_imports",
    tenant_name: Optional[str] = None,
    object_type: Optional[str] = None,
) -> logging.Logger:
    return ZioraLogger.get_logger(name, tenant_name, object_type)