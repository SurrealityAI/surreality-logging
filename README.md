# Surreality Logging

Standardized logging configuration for all Surreality AI services.

Public repository: https://github.com/SurrealityAI/surreality-logging

## Installation

### Python

```bash
pip install git+https://github.com/SurrealityAI/surreality-logging.git
```

Or add to `requirements.txt`:
```
surreality-logging @ git+https://github.com/SurrealityAI/surreality-logging.git
```

### Go

```bash
go get github.com/SurrealityAI/surreality-logging
```

Or add to `go.mod`:
```
require github.com/SurrealityAI/surreality-logging v0.1.0
```

## Log Format

All services use the following standardized format:

```
[YYYY-MM-DD HH:MM:SS,mmm] [LEVEL] [module:line] message
```

Example:
```
[2025-10-20 21:30:45,123] [INFO] [main.go:45] Server started on port 8080
[2025-10-20 21:30:46,456] [ERROR] [handler.go:123] Connection failed: timeout
```

### Format Components

- **Timestamp**: `[YYYY-MM-DD HH:MM:SS,mmm]` - ISO date format with milliseconds
- **Level**: `[LEVEL]` - Log severity (DEBUG, INFO, WARNING, ERROR, CRITICAL, FATAL)
- **Location**: `[module:line]` - Source file and line number
- **Message**: The actual log message

### Color Coding (Terminal Only)

When running in a terminal, logs are color-coded for readability:

- **DEBUG/INFO**: Gray (dim)
- **WARNING**: Yellow
- **ERROR**: Red
- **CRITICAL/FATAL**: Red + Bold

## Log Rotation

Both Python and Go implementations support automatic log rotation based on file size to prevent disk space issues.

### How It Works

- **Size-based rotation**: When a log file reaches the maximum size (default: 100MB), it's automatically rotated
- **Backup files**: Old logs are renamed with numeric suffixes (e.g., `app.log.1`, `app.log.2`, etc.)
- **Automatic cleanup**: After reaching the backup count (default: 5), the oldest file is deleted
- **Dual output**: Logs are written to both console and file simultaneously

### File Naming Convention

```
app.log         # Current log file
app.log.1       # Most recent backup (after first rotation)
app.log.2       # Second backup
app.log.3       # Third backup
app.log.4       # Fourth backup
app.log.5       # Oldest backup (will be deleted on next rotation)
```

### Disk Space Management

**Calculate total disk space usage**:
```
Total disk space = max_bytes * (backup_count + 1)
```

**Examples**:
- `max_bytes=100MB, backup_count=5`: Maximum **600MB** per service
- `max_bytes=50MB, backup_count=10`: Maximum **550MB** per service
- `max_bytes=200MB, backup_count=3`: Maximum **800MB** per service

**Recommended settings**:
- **Development**: `max_bytes=50MB, backup_count=3` (200MB total)
- **Production**: `max_bytes=100MB, backup_count=5` (600MB total)
- **High-traffic**: `max_bytes=200MB, backup_count=10` (2.2GB total)

## Python Services

### Setup

```python
# Import from installed package
from surreality_logging import configure_logging
import logging

# Console only (no file logging)
configure_logging(
    level=logging.INFO,
    service_name="my-service",  # Optional
    include_uvicorn=True  # Set to False if not using Uvicorn
)

# Console + rotating file logging
configure_logging(
    level=logging.INFO,
    service_name="my-service",
    include_uvicorn=True,
    log_file="/var/log/my-service/app.log",  # Enable file logging
    max_bytes=50 * 1024 * 1024,  # 50MB per file
    backup_count=10  # Keep 10 backup files
)

# Get logger for your module
logger = get_logger(__name__)

# Use it
logger.info("Processing request")
logger.warning("Rate limit exceeded")
logger.error("Connection failed")  # Automatically sent to Sentry
```

### Uvicorn Integration

For FastAPI/Uvicorn services, the logging config automatically:

1. Configures `uvicorn`, `uvicorn.error`, and `uvicorn.access` loggers
2. Reduces `uvicorn.access` to WARNING level to prevent HTTP 200 OK spam
3. Uses the same standardized format for all Uvicorn logs

**Option 1: Configure in code**

```python
from python_logging_config import configure_logging
import uvicorn

configure_logging(logging.INFO, "my-service", include_uvicorn=True)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
```

**Option 2: Pass log config to uvicorn.run()**

```python
from python_logging_config import UVICORN_LOG_CONFIG
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_config=UVICORN_LOG_CONFIG
    )
```

### Service-Specific Configuration

#### gmail-services

```python
# In gmail-services/run.py or src/__init__.py
import sys
sys.path.append('../shared-logging')
from python_logging_config import configure_logging
import logging

configure_logging(logging.INFO, "gmail-services", include_uvicorn=True)
```

#### whatsapp-services (Python MCP)

```python
# In whatsapp-services MCP server
import sys
sys.path.append('../shared-logging')
from python_logging_config import configure_logging
import logging

configure_logging(logging.INFO, "whatsapp-mcp")
```

#### slack-services

```python
# In slack-services/src/api/main.py
import sys
sys.path.append('../../shared-logging')
from python_logging_config import configure_logging
import logging

configure_logging(logging.INFO, "slack-services", include_uvicorn=True)
```

#### linkedin-services

```python
# In linkedin-services/src/api/main.py
import sys
sys.path.append('../../shared-logging')
from python_logging_config import configure_logging
import logging

configure_logging(logging.INFO, "linkedin-services", include_uvicorn=True)
```

#### voice-pipeline

```python
# In voice-pipeline/voice_pipeline/server.py
import sys
sys.path.append('../shared-logging')
from python_logging_config import configure_logging
import logging

configure_logging(logging.INFO, "voice-pipeline", include_uvicorn=True)
```

## Go Services

### Setup

```go
import (
    logging "github.com/SurrealityAI/surreality-logging"
)

func main() {
    // Console only (no file logging)
    logger := logging.ConfigureLogging("my-service")

    // Console + rotating file logging
    logger := logging.ConfigureLoggingWithConfig(logging.LogConfig{
        ServiceName: "my-service",
        LogFile:     "/var/log/my-service/app.log",
        MaxBytes:    50 * 1024 * 1024, // 50MB
        BackupCount: 10,                // Keep 10 backups
    })

    // IMPORTANT: Close logger on shutdown to flush file writes
    defer logger.Close()

    // Use it
    logger.Info("Server started")
    logger.Warningf("Rate limit: %d requests", count)
    logger.Error("Connection failed")  // Automatically sent to Sentry
}
```

### Package-Level Functions

For convenience, you can use package-level functions:

```go
import (
    "path/to/shared-logging"
)

func processRequest() {
    logging.Info("Processing request")
    logging.Debugf("Request ID: %s", requestID)
    logging.Error("Failed to process")
}
```

### Service-Specific Configuration

#### whatsapp-services

```go
// In whatsapp-services/main.go
import (
    "github.com/SurrealityAI/voice-messaging/shared-logging"
    "os"
    "path/filepath"
)

func main() {
    // Get log directory from environment or use default
    logDir := os.Getenv("LOG_DIR")
    if logDir == "" {
        logDir = "/var/log/whatsapp-services"
    }

    logger := logging.ConfigureLoggingWithConfig(logging.LogConfig{
        ServiceName: "whatsapp-services",
        LogFile:     filepath.Join(logDir, "whatsapp.log"),
        MaxBytes:    100 * 1024 * 1024, // 100MB
        BackupCount: 5,
    })
    defer logger.Close()

    logger.Info("WhatsApp service starting")

    // Use logger throughout the application
    // Pass logger to other packages/components
}
```

## Sentry Integration

Both Python and Go logging configurations automatically integrate with Sentry:

- **WARNING**: Added as breadcrumbs in Sentry
- **ERROR/CRITICAL/FATAL**: Sent as errors to Sentry

### Setup Requirements

Ensure Sentry SDK is initialized before configuring logging:

**Python**:
```python
import sentry_sdk
sentry_sdk.init(dsn="...", environment="production")

from python_logging_config import configure_logging
configure_logging()
```

**Go**:
```go
import "github.com/getsentry/sentry-go"

sentry.Init(sentry.ClientOptions{
    Dsn: "...",
    Environment: "production",
})

logger := logging.ConfigureLogging("my-service")
```

## Migration Guide

### Migrating Python Services

1. Add import at the top of your main file:
```python
import sys
sys.path.append('../shared-logging')  # Adjust path as needed
from python_logging_config import configure_logging
import logging
```

2. Replace existing logging setup with:
```python
configure_logging(logging.INFO, "service-name", include_uvicorn=True)
```

3. Remove any custom logging formatters or handlers

4. Use `logging.getLogger(__name__)` to get loggers in modules

### Migrating Go Services

1. Add import:
```go
import "github.com/SurrealityAI/voice-messaging/shared-logging"
```

2. Replace existing logger initialization with:
```go
logger := logging.ConfigureLogging("service-name")
```

3. Update log calls to use new logger methods:
   - `log.Printf()` → `logger.Infof()`
   - `log.Println()` → `logger.Info()`
   - `fmt.Printf()` → `logger.Infof()` (for logging purposes)

4. Remove custom logging configuration

## Log Levels

Use appropriate log levels:

- **DEBUG**: Detailed diagnostic information (disabled in production)
- **INFO**: General informational messages (startup, shutdown, state changes)
- **WARNING**: Warning messages (rate limits, retries, deprecated usage)
- **ERROR**: Error messages (failed operations, exceptions)
- **CRITICAL**: Critical errors (data corruption, security issues)
- **FATAL**: Fatal errors that require immediate exit

## Testing

### Python

```python
import logging
from python_logging_config import configure_logging, get_logger

configure_logging(logging.DEBUG)  # Enable DEBUG for testing
logger = get_logger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
```

### Go

```go
import "github.com/SurrealityAI/voice-messaging/shared-logging"

func TestLogging() {
    logger := logging.ConfigureLogging("test-service")

    logger.Debug("Debug message")
    logger.Info("Info message")
    logger.Warning("Warning message")
    logger.Error("Error message")
}
```

## Best Practices

1. **Always include context**: Add relevant information to log messages
   ```python
   logger.error(f"Failed to connect to database: {error}")
   ```

2. **Use appropriate levels**: Don't log everything as INFO or ERROR

3. **Avoid sensitive data**: Never log passwords, tokens, or PII

4. **Use structured logging for complex data**:
   ```python
   logger.info(f"User {user_id} completed action {action_type} in {duration}ms")
   ```

5. **Keep messages concise**: Log messages should be clear and actionable

6. **Include error context**: Always include the actual error when logging exceptions
   ```python
   logger.error(f"Connection failed: {str(e)}")
   ```

## Troubleshooting

### Colors not showing in terminal

- Ensure you're running in a terminal (not redirected output)
- Check that `stdout.isatty()` returns `True` (Python) or `os.Stdout.Stat()` shows `ModeCharDevice` (Go)

### Module names showing as `root`

- Use `logging.getLogger(__name__)` instead of `logging.getLogger()`

### Line numbers incorrect

- This usually means the logger is being called from a wrapper function
- Adjust the `skip` parameter in `runtime.Caller()` (Go) or use the logger directly

### Uvicorn logs not showing standardized format

- Ensure `configure_logging(include_uvicorn=True)` is called before `uvicorn.run()`
- Or pass `log_config=UVICORN_LOG_CONFIG` to `uvicorn.run()`

### Sentry not receiving logs

- Ensure Sentry SDK is initialized before configuring logging
- Check that DSN is correctly set
- Only ERROR/CRITICAL/FATAL logs are sent to Sentry (by design)
