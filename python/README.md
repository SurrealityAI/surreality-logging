# Surreality Logging - Python

Standardized logging configuration for Surreality AI Python services using Loguru.

## Format

```
YYYY-MM-DD HH:MM:SS.mmm | LEVEL    | module:function:line - message
```

Example:
```
2025-11-09 01:38:06.072 | DEBUG    | pipecat.services.mcp_service:_convert_mcp_schema_to_pipecat:140 - Converting schema for tool 'get_unread_count'
2025-11-09 01:38:06.072 | INFO     | gmail.auth:authenticate_user:45 - User authenticated successfully
2025-11-09 01:38:06.072 | WARNING  | gmail.rate_limit:check_limit:23 - Rate limit exceeded
2025-11-09 01:38:06.072 | ERROR    | gmail.connection:connect:89 - Connection failed
```

## Installation

```bash
pip install git+https://github.com/SurrealityAI/surreality-logging.git#subdirectory=python
```

Or in `requirements.txt`:
```
surreality-logging @ git+https://github.com/SurrealityAI/surreality-logging.git#subdirectory=python
```

## Usage

### Basic Setup

```python
from surreality_logging import configure_logging, logger

# Console only
configure_logging("INFO")

# Use the logger
logger.info("Processing request")
logger.debug("Debug information")
logger.warning("Rate limit exceeded")
logger.error("Connection failed")
```

### With File Rotation

```python
from surreality_logging import configure_logging, logger

configure_logging(
    level="INFO",
    log_file="/var/log/myapp/app.log",
    max_bytes=50 * 1024 * 1024,  # 50MB
    backup_count=10  # Keep 10 backup files
)

logger.info("Application started")
```

### Intercept Standard Library Logging

By default, standard library logging (including uvicorn) is intercepted and redirected to loguru:

```python
from surreality_logging import configure_logging, logger

# Automatically intercepts uvicorn logging
configure_logging("INFO", intercept_stdlib=True)

# Intercept additional libraries
configure_logging(
    "INFO",
    additional_loggers=["requests", "httpx", ("boto3", "WARNING")]
)
```

### FastAPI/Uvicorn Integration

```python
from surreality_logging import configure_logging
import uvicorn

# Configure logging before starting uvicorn
configure_logging("INFO")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
```

All uvicorn logs will automatically use the loguru format!

## API Reference

### `configure_logging()`

```python
def configure_logging(
    level: str = "INFO",
    service_name: Optional[str] = None,
    intercept_stdlib: bool = True,
    additional_loggers: list = None,
    log_file: Optional[str] = None,
    max_bytes: int = 100 * 1024 * 1024,
    backup_count: int = 5,
    colorize: bool = True
) -> None:
```

**Parameters:**
- `level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `service_name`: Service name (currently unused, reserved for future use)
- `intercept_stdlib`: Whether to intercept standard library logging (default: True)
- `additional_loggers`: Additional loggers to intercept (e.g., `["requests", ("boto3", "WARNING")]`)
- `log_file`: Path to log file for rotation (optional)
- `max_bytes`: Maximum file size before rotation (default: 100MB)
- `backup_count`: Number of backup files to keep (default: 5)
- `colorize`: Use colors in console output (default: True)

### `intercept_standard_logging()`

```python
def intercept_standard_logging(
    level: str = "INFO",
    additional_loggers: list = None
) -> None:
```

Intercept standard library logging and redirect to loguru. Can be called after initial setup to add more loggers.

**Parameters:**
- `level`: Logging level for intercepted loggers
- `additional_loggers`: List of logger names to intercept

### `get_logger()`

```python
def get_logger(name: Optional[str] = None):
```

Returns the loguru logger instance. The `name` parameter is optional and currently unused (loguru automatically captures context).

### `logger`

The global loguru logger instance. Can be imported and used directly:

```python
from surreality_logging import logger

logger.info("Hello world!")
```

## Features

- **Colored Output**: Automatic color coding in terminals
- **File Rotation**: Size-based log rotation with configurable limits
- **Standard Library Interception**: Captures all standard `logging` calls
- **Uvicorn Integration**: Seamless integration with FastAPI/Uvicorn
- **Zero Configuration**: Works out of the box with sensible defaults

## Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical errors

## Examples

### Intercept Multiple Libraries

```python
from surreality_logging import configure_logging, logger

configure_logging(
    "INFO",
    additional_loggers=[
        "requests",           # INFO level
        "httpx",              # INFO level
        ("boto3", "WARNING"), # WARNING level
        ("sqlalchemy.engine", "WARNING")
    ]
)

# All logs from these libraries now use loguru format!
```

### Disable Colors

```python
from surreality_logging import configure_logging

configure_logging("INFO", colorize=False)
```

### Add Loggers Dynamically

```python
from surreality_logging import configure_logging, intercept_standard_logging

# Initial setup
configure_logging("INFO")

# Later, add more loggers
intercept_standard_logging("DEBUG", ["asyncio"])
```

## Best Practices

1. Call `configure_logging()` early in your application startup
2. Use the imported `logger` directly for logging
3. Use appropriate log levels
4. Avoid logging sensitive information (passwords, tokens, PII)
5. Include context in log messages

## License

MIT
