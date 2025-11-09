"""
Standardized logging configuration for all Surreality AI Python services using Loguru.

Format: YYYY-MM-DD HH:MM:SS.mmm | LEVEL    | module:function:line - message

This module provides:
- Unified log format across all services using Loguru
- Colored console output
- Uvicorn logging configuration
- Log rotation with size limits
"""
import sys
import os
from typing import Optional
from loguru import logger
import logging


def configure_logging(
    level: str = "INFO",
    service_name: Optional[str] = None,
    intercept_stdlib: bool = True,
    additional_loggers: list = None,
    log_file: Optional[str] = None,
    max_bytes: int = 100 * 1024 * 1024,  # 100MB default
    backup_count: int = 5,
    colorize: bool = True
) -> None:
    """
    Configure standardized Python logging for Surreality AI services using Loguru.

    Format: YYYY-MM-DD HH:MM:SS.mmm | LEVEL    | module:function:line - message

    Args:
        level: Logging level (default: "INFO")
        service_name: Service name to include in logs (optional, currently unused)
        intercept_stdlib: Whether to intercept standard library logging (default: True)
                         This includes uvicorn and any additional_loggers
        additional_loggers: Additional standard library loggers to intercept (e.g., ["requests", "httpx"])
                           Each can be a string (logger name) or tuple (logger_name, level)
        log_file: Path to log file (optional). If provided, logs to both console and file with rotation.
        max_bytes: Maximum size per log file in bytes (default: 100MB)
        backup_count: Number of backup files to keep (default: 5)
        colorize: Whether to use colors in console output (default: True)

    Example:
        # Console only with uvicorn interception
        configure_logging("INFO")

        # Console + rotating file + intercept additional libraries
        configure_logging(
            "INFO",
            log_file="/var/log/app/app.log",
            additional_loggers=["requests", "httpx", ("boto3", "WARNING")],
            max_bytes=50 * 1024 * 1024,  # 50MB
            backup_count=10
        )
    """
    # Remove default logger
    logger.remove()

    # Define format string matching the requested format
    # Format: YYYY-MM-DD HH:MM:SS.mmm | LEVEL    | module:function:line - message
    log_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"

    if not colorize:
        log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}"

    # Add console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=level,
        colorize=colorize
    )

    # Add rotating file handler if log_file is specified
    if log_file:
        # Create log directory if it doesn't exist
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # Add file handler with rotation
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level=level,
            rotation=max_bytes,  # Rotate when file reaches max_bytes
            retention=backup_count,  # Keep backup_count old files
            compression="zip",  # Compress rotated files
            encoding='utf-8'
        )

        logger.info(f"File logging enabled: {log_file} (max {max_bytes / (1024*1024):.0f}MB, {backup_count} backups)")

    # Configure standard library logging interception if needed
    if intercept_stdlib:
        intercept_standard_logging(level, additional_loggers)

    logger.info("Standardized logging configured with Loguru")


def intercept_standard_logging(level: str = "INFO", additional_loggers: list = None) -> None:
    """
    Intercept standard library logging and redirect it to Loguru.

    This function sets up an InterceptHandler that captures logs from Python's
    standard logging module and redirects them to loguru. By default, it configures
    uvicorn loggers, but can be extended to intercept any standard library logger.

    Args:
        level: Logging level (default: "INFO")
        additional_loggers: List of additional logger names to intercept (e.g., ["requests", "httpx"])
                           Each can be a string (logger name) or tuple (logger_name, level)

    Example:
        # Intercept uvicorn only (default)
        intercept_standard_logging("INFO")

        # Intercept uvicorn + other libraries
        intercept_standard_logging("INFO", additional_loggers=["requests", "httpx", ("boto3", "WARNING")])
    """
    # Intercept handler that redirects standard logging to loguru
    class InterceptHandler(logging.Handler):
        def emit(self, record):
            # Get corresponding Loguru level if it exists
            try:
                level = logger.level(record.levelname).name
            except ValueError:
                level = record.levelno

            # Find caller from where originated the logged message
            frame, depth = logging.currentframe(), 2
            while frame.f_code.co_filename == logging.__file__:
                frame = frame.f_back
                depth += 1

            logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

    # Configure standard library logging to use our intercept handler
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Default loggers to intercept (uvicorn)
    loggers_to_configure = [
        ("uvicorn", level),
        ("uvicorn.error", level),
        ("uvicorn.access", "WARNING"),  # Reduce HTTP request noise
    ]

    # Add additional loggers if specified
    if additional_loggers:
        for logger_spec in additional_loggers:
            if isinstance(logger_spec, tuple):
                loggers_to_configure.append(logger_spec)
            else:
                loggers_to_configure.append((logger_spec, level))

    # Configure all specified loggers
    for logger_name, logger_level in loggers_to_configure:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False

        # Convert string level to logging constant
        if isinstance(logger_level, str):
            logger_level = getattr(logging, logger_level.upper(), logging.INFO)
        logging_logger.setLevel(logger_level)


def get_logger(name: Optional[str] = None):
    """
    Get a standardized logger instance using Loguru.

    Args:
        name: The logger name (typically __name__). Optional with Loguru.

    Returns:
        The configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Processing request")
        logger.warning("Rate limit exceeded")
        logger.error("Connection failed")
    """
    # Loguru uses a single global logger instance
    # The name is captured automatically from the calling context
    return logger


# Export the logger directly for convenience
__all__ = ['logger', 'configure_logging', 'get_logger', 'intercept_standard_logging']
