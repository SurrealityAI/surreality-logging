# Surreality Logging

Standardized logging configuration for all Surreality AI services in both Python and Go.

## Log Format

All services use the following standardized format with colors:

```
YYYY-MM-DD HH:MM:SS.mmm | LEVEL    | module:function:line - message
```

**Example:**
```
2025-11-09 01:38:06.072 | DEBUG    | pipecat.services.mcp_service:_convert_mcp_schema_to_pipecat:140 - Converting schema for tool 'get_unread_count'
2025-11-09 01:38:06.072 | INFO     | gmail.auth:authenticate_user:45 - User authenticated successfully
2025-11-09 01:38:06.072 | WARNING  | rate_limit:check_limit:23 - Rate limit exceeded
2025-11-09 01:38:06.072 | ERROR    | connection:connect:89 - Connection failed
```

## Features

- ✨ **Unified Format**: Same format across Python and Go services
- 🎨 **Colored Output**: Automatic color coding in terminals
- 📁 **File Rotation**: Size-based log rotation with configurable limits
- 🔄 **Standard Library Interception**: Python captures all `logging` calls
- 🚀 **Zero Configuration**: Works out of the box with sensible defaults
- 🎯 **Function Tracking**: Automatic capture of module:function:line information

## Quick Start

### Python

```bash
pip install git+https://github.com/SurrealityAI/surreality-logging.git#subdirectory=python
```

```python
from surreality_logging import configure_logging, logger

configure_logging("INFO")

logger.info("Hello from Python!")
logger.debug("Debug information")
logger.warning("Warning message")
logger.error("Error message")
```

[→ Full Python Documentation](./python/README.md)

### Go

```bash
go get github.com/SurrealityAI/surreality-logging/go
```

```go
import logging "github.com/SurrealityAI/surreality-logging/go"

func main() {
    logger := logging.ConfigureLogging("my-service")
    defer logger.Close()

    logger.Info("Hello from Go!")
    logger.Debug("Debug information")
    logger.Warning("Warning message")
    logger.Error("Error message")
}
```

[→ Full Go Documentation](./go/README.md)

## Repository Structure

```
surreality-logging/
├── python/                  # Python package (uses Loguru)
│   ├── surreality_logging/
│   ├── tests/
│   ├── setup.py
│   ├── pyproject.toml
│   └── README.md
├── go/                      # Go package
│   ├── logging.go
│   ├── logging_test.go
│   ├── go.mod
│   └── README.md
├── README.md                # This file
└── LICENSE
```

## Technology

- **Python**: Built on [Loguru](https://github.com/Delgan/loguru) - a modern logging library with powerful features
- **Go**: Custom implementation using Go's standard library with automatic function tracking

## Log Levels

Both implementations support the same log levels:

| Level | Description | Color |
|-------|-------------|-------|
| DEBUG | Detailed diagnostic information | Blue |
| INFO | General informational messages | White/Gray |
| WARNING | Warning messages | Yellow |
| ERROR | Error messages | Red |
| CRITICAL/FATAL | Critical errors | Red Bold |

## File Rotation

Both Python and Go support automatic log rotation:

- **Size-based rotation**: Rotate when file reaches max size (default: 100MB)
- **Backup retention**: Keep N backup files (default: 5)
- **Automatic cleanup**: Delete oldest backup when limit reached
- **Dual output**: Write to both console and file simultaneously

**Disk space calculation:**
```
Total disk space = max_bytes × (backup_count + 1)
```

## Python-Specific Features

- **Loguru-based**: Leverages loguru's powerful features
- **Standard Library Interception**: Automatically captures `logging` calls
- **Uvicorn Integration**: Seamless integration with FastAPI/Uvicorn
- **Dynamic Logger Addition**: Add loggers at runtime

```python
# Intercept standard library logging
configure_logging(
    "INFO",
    additional_loggers=["requests", "httpx", ("boto3", "WARNING")]
)
```

## Go-Specific Features

- **Zero Dependencies**: No external dependencies
- **Thread-Safe**: Safe for concurrent use
- **Function Tracking**: Automatic capture of function names
- **Package-Level Functions**: Convenience functions for quick logging

```go
// Package-level convenience functions
logging.Info("Quick log message")
logging.Errorf("Error: %v", err)
```

## Installation

### Python

```bash
# Via pip
pip install git+https://github.com/SurrealityAI/surreality-logging.git#subdirectory=python

# In requirements.txt
surreality-logging @ git+https://github.com/SurrealityAI/surreality-logging.git#subdirectory=python
```

### Go

```bash
# Via go get
go get github.com/SurrealityAI/surreality-logging/go

# In go.mod
require github.com/SurrealityAI/surreality-logging/go v0.2.0
```

## Examples

### Python with File Rotation

```python
from surreality_logging import configure_logging, logger

configure_logging(
    level="INFO",
    log_file="/var/log/myapp/app.log",
    max_bytes=50 * 1024 * 1024,  # 50MB
    backup_count=10
)

logger.info("Application started with file rotation")
```

### Go with File Rotation

```go
logger := logging.ConfigureLoggingWithConfig(logging.LogConfig{
    ServiceName: "my-service",
    LogFile:     "/var/log/myapp/app.log",
    MaxBytes:    50 * 1024 * 1024, // 50MB
    BackupCount: 10,
})
defer logger.Close()

logger.Info("Application started with file rotation")
```

## Best Practices

1. **Call configuration early**: Configure logging at application startup
2. **Use appropriate log levels**: Don't log everything as INFO or ERROR
3. **Include context**: Add relevant information to log messages
4. **Avoid sensitive data**: Never log passwords, tokens, or PII
5. **Close loggers**: Always close file-based loggers on shutdown (Go: `defer logger.Close()`)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Links

- [Python Documentation](./python/README.md)
- [Go Documentation](./go/README.md)
- [GitHub Repository](https://github.com/SurrealityAI/surreality-logging)
