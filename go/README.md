# Surreality Logging - Go

Standardized logging configuration for Surreality AI Go services.

## Format

```
YYYY-MM-DD HH:MM:SS.mmm | LEVEL    | module:function:line - message
```

Example:
```
2025-11-09 01:45:34.278 | INFO     | logging:ConfigureLogging:249 - Standardized logging configured
2025-11-09 01:45:34.279 | DEBUG    | main:processRequest:45 - Processing request ID: abc123
2025-11-09 01:45:34.279 | WARNING  | handler:checkRate:89 - Rate limit exceeded
2025-11-09 01:45:34.279 | ERROR    | database:connect:123 - Connection failed
```

## Installation

```bash
go get github.com/SurrealityAI/surreality-logging/go
```

Or in `go.mod`:
```go
require github.com/SurrealityAI/surreality-logging/go v0.2.0
```

## Usage

### Basic Setup

```go
package main

import (
    logging "github.com/SurrealityAI/surreality-logging/go"
)

func main() {
    // Console only
    logger := logging.ConfigureLogging("my-service")
    defer logger.Close() // Always close to flush file writes

    logger.Info("Application started")
    logger.Debug("Debug information")
    logger.Warning("Rate limit exceeded")
    logger.Error("Connection failed")
}
```

### With File Rotation

```go
package main

import (
    logging "github.com/SurrealityAI/surreality-logging/go"
)

func main() {
    logger := logging.ConfigureLoggingWithConfig(logging.LogConfig{
        ServiceName: "my-service",
        LogFile:     "/var/log/myapp/app.log",
        MaxBytes:    50 * 1024 * 1024, // 50MB
        BackupCount: 10,                // Keep 10 backups
    })
    defer logger.Close()

    logger.Info("Application started with file rotation")
}
```

### Package-Level Functions

For convenience, you can use package-level logging functions:

```go
package main

import (
    logging "github.com/SurrealityAI/surreality-logging/go"
)

func processRequest() {
    // Uses the default logger
    logging.Info("Processing request")
    logging.Debugf("Request ID: %s", requestID)
    logging.Warning("High memory usage")
    logging.Errorf("Failed to process: %v", err)
}

func main() {
    // Configure the default logger
    logging.ConfigureLogging("my-service")

    processRequest()
}
```

## API Reference

### Configuration

#### `ConfigureLogging(serviceName string) *StandardLogger`

Basic configuration with console output only.

```go
logger := logging.ConfigureLogging("my-service")
defer logger.Close()
```

#### `ConfigureLoggingWithConfig(config LogConfig) *StandardLogger`

Advanced configuration with file rotation.

```go
logger := logging.ConfigureLoggingWithConfig(logging.LogConfig{
    ServiceName: "my-service",
    LogFile:     "/var/log/app/app.log",
    MaxBytes:    100 * 1024 * 1024, // 100MB (default)
    BackupCount: 5,                  // 5 backups (default)
})
defer logger.Close()
```

**LogConfig Fields:**
- `ServiceName`: Service name (optional, for future use)
- `LogFile`: Path to log file (optional, enables file rotation if set)
- `MaxBytes`: Maximum file size before rotation (default: 100MB)
- `BackupCount`: Number of backup files to keep (default: 5)

### Logger Methods

#### Instance Methods

```go
logger := logging.ConfigureLogging("my-service")

logger.Debug(v ...interface{})
logger.Debugf(format string, v ...interface{})

logger.Info(v ...interface{})
logger.Infof(format string, v ...interface{})

logger.Warning(v ...interface{})
logger.Warningf(format string, v ...interface{})

logger.Error(v ...interface{})
logger.Errorf(format string, v ...interface{})

logger.Fatal(v ...interface{})  // Logs and exits
logger.Fatalf(format string, v ...interface{})
```

#### Package-Level Functions

```go
logging.Debug(v ...interface{})
logging.Debugf(format string, v ...interface{})

logging.Info(v ...interface{})
logging.Infof(format string, v ...interface{})

logging.Warning(v ...interface{})
logging.Warningf(format string, v ...interface{})

logging.Error(v ...interface{})
logging.Errorf(format string, v ...interface{})

logging.Fatal(v ...interface{})
logging.Fatalf(format string, v ...interface{})
```

### `GetLogger() *StandardLogger`

Returns the default logger instance.

```go
logger := logging.GetLogger()
logger.Info("Using default logger")
```

### `Close() error`

Closes the logger and flushes any pending file writes. **Always call this before exiting!**

```go
logger := logging.ConfigureLogging("my-service")
defer logger.Close()
```

## Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **FATAL**: Fatal errors (logs and exits)

## Features

- **Colored Output**: Automatic color coding in terminals
  - DEBUG/INFO: Gray
  - WARNING: Yellow
  - ERROR/FATAL: Red
- **File Rotation**: Size-based log rotation with configurable limits
- **Automatic Function Tracking**: Captures module:function:line information
- **Zero Dependencies**: No external dependencies required
- **Thread-Safe**: Safe for concurrent use

## File Rotation

When `LogFile` is specified, logs are rotated automatically:

1. **Size-based rotation**: When file reaches `MaxBytes`, it's rotated
2. **Backup naming**: Rotated files are renamed (`app.log` → `app.log.1` → `app.log.2`, etc.)
3. **Automatic cleanup**: After `BackupCount` files, oldest is deleted
4. **Dual output**: Logs written to both console and file

### Disk Space Calculation

```
Total disk space = MaxBytes × (BackupCount + 1)
```

**Examples:**
- `MaxBytes=100MB, BackupCount=5`: **600MB total**
- `MaxBytes=50MB, BackupCount=10`: **550MB total**

## Examples

### HTTP Server

```go
package main

import (
    "net/http"
    logging "github.com/SurrealityAI/surreality-logging/go"
)

func handler(w http.ResponseWriter, r *http.Request) {
    logging.Infof("Request: %s %s", r.Method, r.URL.Path)
    w.Write([]byte("Hello World"))
}

func main() {
    logger := logging.ConfigureLoggingWithConfig(logging.LogConfig{
        ServiceName: "http-server",
        LogFile:     "/var/log/http-server/app.log",
        MaxBytes:    50 * 1024 * 1024,
        BackupCount: 10,
    })
    defer logger.Close()

    logger.Info("Starting HTTP server on :8080")

    http.HandleFunc("/", handler)
    if err := http.ListenAndServe(":8080", nil); err != nil {
        logger.Fatalf("Server failed: %v", err)
    }
}
```

### Error Handling

```go
func connectDatabase() error {
    logger := logging.GetLogger()

    conn, err := db.Connect()
    if err != nil {
        logger.Errorf("Database connection failed: %v", err)
        return err
    }

    logger.Info("Database connected successfully")
    return nil
}
```

### Conditional Logging

```go
if cfg.Debug {
    logging.Debugf("Configuration: %+v", cfg)
}

logging.Infof("Service started on port %d", cfg.Port)
```

## Best Practices

1. **Always close the logger**: Use `defer logger.Close()` to flush file writes
2. **Use formatted functions**: Prefer `Infof()` over `Info()` for structured data
3. **Include context**: Add relevant information to log messages
4. **Use appropriate levels**: Don't log everything as INFO or ERROR
5. **Avoid sensitive data**: Never log passwords, tokens, or PII
6. **Pass logger to components**: Don't rely solely on package-level functions for large apps

## Troubleshooting

### Colors not showing
- Check that you're running in a terminal
- Verify `os.Stdout` is a terminal device

### Function names showing as "unknown"
- Ensure you're not using wrapper functions
- The `skip` parameter in `runtime.Caller()` may need adjustment

### File rotation not working
- Check file permissions
- Ensure parent directory exists
- Call `logger.Close()` on shutdown

## License

MIT
