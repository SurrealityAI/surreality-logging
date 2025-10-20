"""
Standardized logging configuration for all Surreality AI Python services.

Format: [YYYY-MM-DD HH:MM:SS,mmm] [LEVEL] [module:line] message

This module provides:
- Unified log format across all services
- Colored console output
- Automatic Sentry integration for errors
- Uvicorn logging configuration
- Log rotation with size limits
"""
import logging
import logging.handlers
import sys
import os
from typing import Optional


class StandardizedFormatter(logging.Formatter):
    """
    Standardized formatter with colors and consistent format.

    Format: [YYYY-MM-DD HH:MM:SS,mmm] [LEVEL] [module:line] message

    Colors:
    - DEBUG/INFO: Gray (dim)
    - WARNING: Yellow
    - ERROR: Red
    - CRITICAL: Red + Bold
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[90m',      # Gray (dim)
        'INFO': '\033[90m',       # Gray (dim)
        'WARNING': '\033[93m',    # Yellow
        'ERROR': '\033[91m',      # Red
        'CRITICAL': '\033[91;1m'  # Red + Bold
    }
    RESET = '\033[0m'

    def format(self, record):
        # Add color to levelname for terminal output
        levelname = record.levelname
        colored_levelname = levelname

        # Only add colors if outputting to a terminal
        if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
            if levelname in self.COLORS:
                colored_levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"

        # Store original and set colored version
        original_levelname = record.levelname
        record.levelname = colored_levelname

        # Format the message
        formatted = super().format(record)

        # Restore original levelname
        record.levelname = original_levelname

        return formatted


def configure_logging(
    level: int = logging.INFO,
    service_name: Optional[str] = None,
    include_uvicorn: bool = True,
    log_file: Optional[str] = None,
    max_bytes: int = 100 * 1024 * 1024,  # 100MB default
    backup_count: int = 5
) -> None:
    """
    Configure standardized Python logging for Surreality AI services.

    Format: [YYYY-MM-DD HH:MM:SS,mmm] [LEVEL] [module:line] message

    Args:
        level: Logging level (default: INFO)
        service_name: Service name to include in logs (optional)
        include_uvicorn: Whether to configure Uvicorn logging (default: True)
        log_file: Path to log file (optional). If provided, logs to both console and file with rotation.
        max_bytes: Maximum size per log file in bytes (default: 100MB)
        backup_count: Number of backup files to keep (default: 5)

    Example:
        # Console only
        configure_logging(logging.INFO, "gmail-services")

        # Console + rotating file
        configure_logging(
            logging.INFO,
            "gmail-services",
            log_file="/var/log/gmail-services/app.log",
            max_bytes=50 * 1024 * 1024,  # 50MB
            backup_count=10
        )
    """
    # Create standardized formatter with timestamp, level, module:line, and message
    log_format = '[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s'
    if service_name:
        log_format = f'[%(asctime)s] [%(levelname)s] [{service_name}] [%(name)s:%(lineno)d] %(message)s'

    formatter = StandardizedFormatter(
        fmt=log_format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Override formatTime to include milliseconds
    original_format_time = formatter.formatTime
    def format_time_with_ms(record, datefmt=None):
        ct = original_format_time(record, datefmt)
        # Add milliseconds
        msecs = f"{record.msecs:03.0f}"
        return f"{ct},{msecs}"
    formatter.formatTime = format_time_with_ms

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add console handler
    root_logger.addHandler(console_handler)

    # Add rotating file handler if log_file is specified
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Create rotating file handler
        # When max_bytes is reached, the file is closed and a new file is opened
        # Old files are renamed: app.log.1, app.log.2, etc.
        # After backup_count files, the oldest is deleted
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        logging.info(f"File logging enabled: {log_file} (max {max_bytes / (1024*1024):.0f}MB, {backup_count} backups)")

    # Configure Uvicorn logging if needed
    if include_uvicorn:
        configure_uvicorn_logging(formatter, level, log_file, max_bytes, backup_count)

    logging.info("Standardized logging configured")


def configure_uvicorn_logging(
    formatter: logging.Formatter,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    max_bytes: int = 100 * 1024 * 1024,
    backup_count: int = 5
) -> None:
    """
    Configure Uvicorn's logging to use our standardized format.

    Uvicorn has its own loggers:
    - uvicorn: Main uvicorn logger
    - uvicorn.error: Error logger
    - uvicorn.access: Access logger (HTTP requests)

    Args:
        formatter: The formatter to use
        level: Logging level
        log_file: Optional log file path for file logging
        max_bytes: Maximum size per log file in bytes
        backup_count: Number of backup files to keep
    """
    # Configure uvicorn loggers
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        logger.setLevel(level)
        logger.propagate = False

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler (if configured)
        if log_file:
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    # Reduce verbosity of uvicorn.access (HTTP requests) to WARNING by default
    # This prevents flooding logs with HTTP 200 OK messages
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a standardized logger instance.

    Use this for all logs. Errors (ERROR, CRITICAL) are automatically
    sent to Sentry via Sentry SDK integration.

    Args:
        name: The logger name (typically __name__)

    Returns:
        A configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Processing request")        # [2025-01-15 10:30:45,123] [INFO] [module:45] Processing request
        logger.warning("Rate limit exceeded")    # [2025-01-15 10:30:45,456] [WARNING] [module:50] Rate limit exceeded
        logger.error("Connection failed")        # [2025-01-15 10:30:45,789] [ERROR] [module:55] Connection failed (sent to Sentry)
    """
    return logging.getLogger(name)


# Uvicorn configuration dict for use in uvicorn.run()
UVICORN_LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "python_logging_config.StandardizedFormatter",
            "fmt": "[%(asctime)s] [%(levelname)s] [uvicorn] [%(name)s:%(lineno)d] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "access": {
            "()": "python_logging_config.StandardizedFormatter",
            "fmt": "[%(asctime)s] [%(levelname)s] [uvicorn.access] %(client_addr)s - \"%(request_line)s\" %(status_code)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
        },
    },
    "loggers": {
        "uvicorn": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False
        },
        "uvicorn.error": {
            "handlers": ["default"],
            "level": "INFO",
            "propagate": False
        },
        "uvicorn.access": {
            "handlers": ["access"],
            "level": "WARNING",  # Reduce HTTP request noise
            "propagate": False
        },
    },
}
