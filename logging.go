/*
Standardized logging configuration for all Surreality AI Go services.

Format: [YYYY-MM-DD HH:MM:SS,mmm] [LEVEL] [module:line] message

This module provides:
- Unified log format across all services
- Automatic file:line tracking
- Colored console output
- Automatic Sentry integration for errors
- Log rotation with size limits
*/
package logging

import (
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"runtime"
	"sync"
	"time"

	"github.com/getsentry/sentry-go"
)

// ANSI color codes
const (
	ColorReset   = "\033[0m"
	ColorGray    = "\033[90m"  // DEBUG/INFO
	ColorYellow  = "\033[93m"  // WARNING
	ColorRed     = "\033[91m"  // ERROR
	ColorRedBold = "\033[91;1m" // CRITICAL/FATAL
)

// LogLevel represents log severity levels
type LogLevel string

const (
	LevelDebug    LogLevel = "DEBUG"
	LevelInfo     LogLevel = "INFO"
	LevelWarning  LogLevel = "WARNING"
	LevelError    LogLevel = "ERROR"
	LevelCritical LogLevel = "CRITICAL"
	LevelFatal    LogLevel = "FATAL"
)

// getColor returns the ANSI color code for a log level
func getColor(level LogLevel) string {
	if !isTerminal() {
		return ""
	}
	switch level {
	case LevelDebug, LevelInfo:
		return ColorGray
	case LevelWarning:
		return ColorYellow
	case LevelError, LevelCritical, LevelFatal:
		return ColorRed
	default:
		return ""
	}
}

// isTerminal checks if stdout is a terminal
func isTerminal() bool {
	fileInfo, _ := os.Stdout.Stat()
	return (fileInfo.Mode() & os.ModeCharDevice) != 0
}

// formatLogMessage formats a log message in standardized format
// Format: [YYYY-MM-DD HH:MM:SS,mmm] [LEVEL] [module:line] message
func formatLogMessage(level LogLevel, message string, skip int) string {
	now := time.Now()

	// Get caller information (file:line)
	_, file, line, ok := runtime.Caller(skip)
	var location string
	if ok {
		// Get just the filename without path
		location = fmt.Sprintf("%s:%d", filepath.Base(file), line)
	} else {
		location = "unknown:0"
	}

	// Format timestamp: [2025-10-20 21:30:45,123]
	timestamp := fmt.Sprintf("[%04d-%02d-%02d %02d:%02d:%02d,%03d]",
		now.Year(), now.Month(), now.Day(),
		now.Hour(), now.Minute(), now.Second(),
		now.Nanosecond()/1000000)

	// Apply color to level name if terminal
	levelStr := string(level)
	color := getColor(level)
	if color != "" {
		levelStr = color + levelStr + ColorReset
	}

	return fmt.Sprintf("%s [%s] [%s] %s", timestamp, levelStr, location, message)
}

// RotatingFileWriter implements log rotation based on file size
type RotatingFileWriter struct {
	filename    string
	maxBytes    int64
	backupCount int
	file        *os.File
	currentSize int64
	mu          sync.Mutex
}

// NewRotatingFileWriter creates a new rotating file writer
func NewRotatingFileWriter(filename string, maxBytes int64, backupCount int) (*RotatingFileWriter, error) {
	// Create log directory if it doesn't exist
	dir := filepath.Dir(filename)
	if dir != "" && dir != "." {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return nil, fmt.Errorf("failed to create log directory: %w", err)
		}
	}

	w := &RotatingFileWriter{
		filename:    filename,
		maxBytes:    maxBytes,
		backupCount: backupCount,
	}

	// Open the file
	if err := w.openFile(); err != nil {
		return nil, err
	}

	return w, nil
}

func (w *RotatingFileWriter) openFile() error {
	file, err := os.OpenFile(w.filename, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return fmt.Errorf("failed to open log file: %w", err)
	}

	// Get current file size
	info, err := file.Stat()
	if err != nil {
		file.Close()
		return fmt.Errorf("failed to stat log file: %w", err)
	}

	w.file = file
	w.currentSize = info.Size()
	return nil
}

func (w *RotatingFileWriter) Write(p []byte) (n int, err error) {
	w.mu.Lock()
	defer w.mu.Unlock()

	// Check if we need to rotate
	if w.currentSize+int64(len(p)) > w.maxBytes {
		if err := w.rotate(); err != nil {
			return 0, err
		}
	}

	n, err = w.file.Write(p)
	w.currentSize += int64(n)
	return n, err
}

func (w *RotatingFileWriter) rotate() error {
	// Close current file
	if w.file != nil {
		w.file.Close()
	}

	// Rotate existing backup files
	// app.log -> app.log.1, app.log.1 -> app.log.2, etc.
	for i := w.backupCount - 1; i >= 1; i-- {
		oldName := fmt.Sprintf("%s.%d", w.filename, i)
		newName := fmt.Sprintf("%s.%d", w.filename, i+1)

		if _, err := os.Stat(oldName); err == nil {
			// File exists, rename it
			if i == w.backupCount-1 {
				// Delete the oldest file
				os.Remove(newName)
			}
			os.Rename(oldName, newName)
		}
	}

	// Rename current file to .1
	if _, err := os.Stat(w.filename); err == nil {
		os.Rename(w.filename, fmt.Sprintf("%s.1", w.filename))
	}

	// Open new file
	w.currentSize = 0
	return w.openFile()
}

func (w *RotatingFileWriter) Close() error {
	w.mu.Lock()
	defer w.mu.Unlock()

	if w.file != nil {
		return w.file.Close()
	}
	return nil
}

// StandardLogger wraps Go's standard logger with standardized format
type StandardLogger struct {
	serviceName string
	logger      *log.Logger
	fileWriter  *RotatingFileWriter
}

var defaultLogger *StandardLogger

// LogConfig contains configuration for logging
type LogConfig struct {
	ServiceName string
	LogFile     string // Optional: path to log file for file logging with rotation
	MaxBytes    int64  // Maximum size per log file in bytes (default: 100MB)
	BackupCount int    // Number of backup files to keep (default: 5)
}

// ConfigureLogging sets up standardized logging for the service
// serviceName: optional service name to include in logs
func ConfigureLogging(serviceName string) *StandardLogger {
	return ConfigureLoggingWithConfig(LogConfig{
		ServiceName: serviceName,
	})
}

// ConfigureLoggingWithConfig sets up standardized logging with full configuration
func ConfigureLoggingWithConfig(config LogConfig) *StandardLogger {
	// Set defaults
	if config.MaxBytes == 0 {
		config.MaxBytes = 100 * 1024 * 1024 // 100MB
	}
	if config.BackupCount == 0 {
		config.BackupCount = 5
	}

	var writer io.Writer = os.Stdout

	// Setup file logging with rotation if log file is specified
	var fileWriter *RotatingFileWriter
	if config.LogFile != "" {
		var err error
		fileWriter, err = NewRotatingFileWriter(config.LogFile, config.MaxBytes, config.BackupCount)
		if err != nil {
			log.Printf("Failed to setup file logging: %v", err)
		} else {
			// Write to both console and file
			writer = io.MultiWriter(os.Stdout, fileWriter)
			log.Printf("File logging enabled: %s (max %.0fMB, %d backups)",
				config.LogFile,
				float64(config.MaxBytes)/(1024*1024),
				config.BackupCount)
		}
	}

	defaultLogger = &StandardLogger{
		serviceName: config.ServiceName,
		logger:      log.New(writer, "", 0), // No flags, we format manually
		fileWriter:  fileWriter,
	}

	defaultLogger.Info("Standardized logging configured")
	return defaultLogger
}

// Close closes the logger and any open file handles
func (l *StandardLogger) Close() error {
	if l.fileWriter != nil {
		return l.fileWriter.Close()
	}
	return nil
}

// GetLogger returns the configured logger instance
func GetLogger() *StandardLogger {
	if defaultLogger == nil {
		defaultLogger = ConfigureLogging("")
	}
	return defaultLogger
}

// Debug logs a debug message
func (l *StandardLogger) Debug(v ...interface{}) {
	message := fmt.Sprintln(v...)
	message = message[:len(message)-1] // Remove trailing newline
	formatted := formatLogMessage(LevelDebug, message, 3)
	l.logger.Print(formatted)
}

// Debugf logs a formatted debug message
func (l *StandardLogger) Debugf(format string, v ...interface{}) {
	message := fmt.Sprintf(format, v...)
	formatted := formatLogMessage(LevelDebug, message, 3)
	l.logger.Print(formatted)
}

// Info logs an info message
func (l *StandardLogger) Info(v ...interface{}) {
	message := fmt.Sprintln(v...)
	message = message[:len(message)-1] // Remove trailing newline
	formatted := formatLogMessage(LevelInfo, message, 3)
	l.logger.Print(formatted)
}

// Infof logs a formatted info message
func (l *StandardLogger) Infof(format string, v ...interface{}) {
	message := fmt.Sprintf(format, v...)
	formatted := formatLogMessage(LevelInfo, message, 3)
	l.logger.Print(formatted)
}

// Warning logs a warning message
func (l *StandardLogger) Warning(v ...interface{}) {
	message := fmt.Sprintln(v...)
	message = message[:len(message)-1] // Remove trailing newline
	formatted := formatLogMessage(LevelWarning, message, 3)
	l.logger.Print(formatted)

	// Add to Sentry as breadcrumb
	sentry.AddBreadcrumb(&sentry.Breadcrumb{
		Message:  message,
		Level:    sentry.LevelWarning,
		Category: "log",
	})
}

// Warningf logs a formatted warning message
func (l *StandardLogger) Warningf(format string, v ...interface{}) {
	message := fmt.Sprintf(format, v...)
	formatted := formatLogMessage(LevelWarning, message, 3)
	l.logger.Print(formatted)

	// Add to Sentry as breadcrumb
	sentry.AddBreadcrumb(&sentry.Breadcrumb{
		Message:  message,
		Level:    sentry.LevelWarning,
		Category: "log",
	})
}

// Error logs an error message and sends to Sentry
func (l *StandardLogger) Error(v ...interface{}) {
	message := fmt.Sprintln(v...)
	message = message[:len(message)-1] // Remove trailing newline
	formatted := formatLogMessage(LevelError, message, 3)
	l.logger.Print(formatted)

	// Send to Sentry as error
	sentry.CaptureMessage(message)
}

// Errorf logs a formatted error message and sends to Sentry
func (l *StandardLogger) Errorf(format string, v ...interface{}) {
	message := fmt.Sprintf(format, v...)
	formatted := formatLogMessage(LevelError, message, 3)
	l.logger.Print(formatted)

	// Send to Sentry as error
	sentry.CaptureMessage(message)
}

// Fatal logs a fatal message, sends to Sentry, and exits
func (l *StandardLogger) Fatal(v ...interface{}) {
	message := fmt.Sprintln(v...)
	message = message[:len(message)-1] // Remove trailing newline
	formatted := formatLogMessage(LevelFatal, message, 3)

	// Send to Sentry as fatal error
	sentry.CaptureMessage(message)
	sentry.Flush(2 * time.Second)

	// Log and exit
	l.logger.Fatal(formatted)
}

// Fatalf logs a formatted fatal message, sends to Sentry, and exits
func (l *StandardLogger) Fatalf(format string, v ...interface{}) {
	message := fmt.Sprintf(format, v...)
	formatted := formatLogMessage(LevelFatal, message, 3)

	// Send to Sentry as fatal error
	sentry.CaptureMessage(message)
	sentry.Flush(2 * time.Second)

	// Log and exit
	l.logger.Fatal(formatted)
}

// Convenience functions for package-level logging

// Debug logs a debug message using the default logger
func Debug(v ...interface{}) {
	GetLogger().Debug(v...)
}

// Debugf logs a formatted debug message using the default logger
func Debugf(format string, v ...interface{}) {
	GetLogger().Debugf(format, v...)
}

// Info logs an info message using the default logger
func Info(v ...interface{}) {
	GetLogger().Info(v...)
}

// Infof logs a formatted info message using the default logger
func Infof(format string, v ...interface{}) {
	GetLogger().Infof(format, v...)
}

// Warning logs a warning message using the default logger
func Warning(v ...interface{}) {
	GetLogger().Warning(v...)
}

// Warningf logs a formatted warning message using the default logger
func Warningf(format string, v ...interface{}) {
	GetLogger().Warningf(format, v...)
}

// Error logs an error message using the default logger
func Error(v ...interface{}) {
	GetLogger().Error(v...)
}

// Errorf logs a formatted error message using the default logger
func Errorf(format string, v ...interface{}) {
	GetLogger().Errorf(format, v...)
}

// Fatal logs a fatal message using the default logger
func Fatal(v ...interface{}) {
	GetLogger().Fatal(v...)
}

// Fatalf logs a formatted fatal message using the default logger
func Fatalf(format string, v ...interface{}) {
	GetLogger().Fatalf(format, v...)
}
