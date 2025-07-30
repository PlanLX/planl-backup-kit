"""Logging utilities for the backup toolkit."""

import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional

try:
    from rich.logging import RichHandler
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    RichHandler = None
    Console = None
    Panel = None
    Table = None
    box = None


class StructuredFormatter(logging.Formatter):
    """Structured JSON formatter for better log collection."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_entry, ensure_ascii=False)


class LoggingLogger(logging.Logger):
    """Enhanced logger that supports structured logging and rich console output."""
    
    def __init__(self, name: str, level: int = logging.NOTSET):
        super().__init__(name, level)
        self.console = None
        if RICH_AVAILABLE:
            self.console = Console()
    
    def info(self, msg: str, **kwargs: Any) -> None:
        """Log info message with optional structured fields."""
        if kwargs:
            record = self.makeRecord(self.name, logging.INFO, "", 0, msg, (), None)
            record.extra_fields = kwargs
            self.handle(record)
        else:
            super().info(msg)
    
    def error(self, msg: str, **kwargs: Any) -> None:
        """Log error message with optional structured fields."""
        if kwargs:
            record = self.makeRecord(self.name, logging.ERROR, "", 0, msg, (), None)
            record.extra_fields = kwargs
            self.handle(record)
        else:
            super().error(msg)
    
    def warning(self, msg: str, **kwargs: Any) -> None:
        """Log warning message with optional structured fields."""
        if kwargs:
            record = self.makeRecord(self.name, logging.WARNING, "", 0, msg, (), None)
            record.extra_fields = kwargs
            self.handle(record)
        else:
            super().warning(msg)
    
    def debug(self, msg: str, **kwargs: Any) -> None:
        """Log debug message with optional structured fields."""
        if kwargs:
            record = self.makeRecord(self.name, logging.DEBUG, "", 0, msg, (), None)
            record.extra_fields = kwargs
            self.handle(record)
        else:
            super().debug(msg)
    
    def print_table(self, title: str, data: list, columns: list) -> None:
        """Print data as a rich table.
        
        Args:
            title: Table title
            data: List of dictionaries containing row data
            columns: List of column definitions [(name, key, style), ...]
        """
        if not RICH_AVAILABLE or not self.console:
            # Fallback to plain text
            self.info(f"Table: {title}")
            for row in data:
                row_str = " | ".join([f"{col[0]}: {row.get(col[1], '')}" for col in columns])
                self.info(f"  {row_str}")
            return
        
        table = Table(title=title, box=box.ROUNDED)
        
        # Add columns
        for name, key, style in columns:
            table.add_column(name, style=style)
        
        # Add rows
        for row in data:
            table.add_row(*[str(row.get(key, '')) for name, key, style in columns])
        
        self.console.print(table)
    
    def print_panel(self, content: str, title: str = None, style: str = "blue") -> None:
        """Print content in a rich panel.
        
        Args:
            content: Panel content
            title: Panel title
            style: Panel style
        """
        if not RICH_AVAILABLE or not self.console:
            # Fallback to plain text
            if title:
                self.info(f"=== {title} ===")
            self.info(content)
            return
        
        panel = Panel(content, title=title, style=style)
        self.console.print(panel)
    
    def print_success(self, message: str) -> None:
        """Print success message with green color."""
        if not RICH_AVAILABLE or not self.console:
            self.info(f"SUCCESS: {message}")
            return
        
        self.console.print(f"✓ {message}", style="green")
    
    def print_error(self, message: str) -> None:
        """Print error message with red color."""
        if not RICH_AVAILABLE or not self.console:
            self.error(message)
            return
        
        self.console.print(f"✗ {message}", style="red")
    
    def print_warning(self, message: str) -> None:
        """Print warning message with yellow color."""
        if not RICH_AVAILABLE or not self.console:
            self.warning(message)
            return
        
        self.console.print(f"⚠ {message}", style="yellow")


class PlainFormatter(logging.Formatter):
    """Plain text formatter with optional timestamp and extra formatting."""
    
    def __init__(self, fmt: str = '%(asctime)s %(levelname)s %(message)s', datefmt: str = '%Y-%m-%d %H:%M:%S') -> None:
        """
        Initialize the PlainFormatter.
        
        :param fmt: Format for the log message.
        :param datefmt: Format for the timestamp.
        """
        super().__init__(fmt=fmt, datefmt=datefmt)
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as plain text."""
        # Apply standard formatting (timestamp, level, message)
        formatted = super().format(record)
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields') and record.extra_fields:
            extra_str = " | ".join([f"{k}={v}" for k, v in record.extra_fields.items()])
            formatted += f" | {extra_str}"
        
        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


class SyslogFormatter(logging.Formatter):
    """Syslog-compatible formatter."""
    
    # Syslog facility codes
    FACILITY_USER = 1
    FACILITY_LOCAL0 = 16
    FACILITY_LOCAL1 = 17
    FACILITY_LOCAL2 = 18
    FACILITY_LOCAL3 = 19
    FACILITY_LOCAL4 = 20
    FACILITY_LOCAL5 = 21
    FACILITY_LOCAL6 = 22
    FACILITY_LOCAL7 = 23
    
    # Syslog severity levels
    SEVERITY_EMERG = 0
    SEVERITY_ALERT = 1
    SEVERITY_CRIT = 2
    SEVERITY_ERR = 3
    SEVERITY_WARNING = 4
    SEVERITY_NOTICE = 5
    SEVERITY_INFO = 6
    SEVERITY_DEBUG = 7
    
    def __init__(self, facility=FACILITY_LOCAL0):
        """Initialize syslog formatter.
        
        Args:
            facility: Syslog facility code
        """
        super().__init__()
        self.facility = facility
    
    def _get_syslog_level(self, level: int) -> int:
        """Convert logging level to syslog severity."""
        if level >= logging.CRITICAL:
            return self.SEVERITY_CRIT
        elif level >= logging.ERROR:
            return self.SEVERITY_ERR
        elif level >= logging.WARNING:
            return self.SEVERITY_WARNING
        elif level >= logging.INFO:
            return self.SEVERITY_INFO
        else:
            return self.SEVERITY_DEBUG
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as syslog message."""
        # Calculate priority
        priority = self.facility * 8 + self._get_syslog_level(record.levelno)
        
        # Format timestamp
        timestamp = datetime.utcnow().strftime("%b %d %H:%M:%S")
        
        # Base syslog format: <priority>timestamp hostname program[pid]: message
        formatted = f"<{priority}>{timestamp} {record.name}: {record.getMessage()}"
        
        # Add extra fields if present
        if hasattr(record, 'extra_fields') and record.extra_fields:
            extra_str = " | ".join([f"{k}={v}" for k, v in record.extra_fields.items()])
            formatted += f" | {extra_str}"
        
        # Add exception info if present
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


def setup_logging(
    level: str = "INFO", log_format: str = "json", format_string: str | None = None
) -> None:
    """Setup logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Log format (json, plain, syslog, console)
        format_string: Custom format string for logging (deprecated, use log_format instead)
    """
    # Convert string level to logging constant
    log_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Choose formatter based on log_format
    log_format_lower = log_format.lower()
    if log_format_lower == "json":
        formatter = StructuredFormatter()
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    elif log_format_lower == "plain":
        formatter = PlainFormatter()
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    elif log_format_lower == "syslog":
        formatter = SyslogFormatter()
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    elif log_format_lower == "console":
        if RICH_AVAILABLE:
            # Use rich handler for better console output
            console = Console()
            rich_handler = RichHandler(
                console=console,
                show_time=True,
                show_path=False,
                markup=False,
                rich_tracebacks=True
            )
            rich_handler.setLevel(log_level)
            root_logger.addHandler(rich_handler)
        else:
            # Fallback to plain if rich is not available
            formatter = PlainFormatter()
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
    else:
        # Default to JSON format
        formatter = StructuredFormatter()
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # Set specific logger levels
    logging.getLogger("elasticsearch").setLevel(logging.WARNING)
    # logging.getLogger("urllib3").setLevel(logging.WARNING)
    # logging.getLogger("boto3").setLevel(logging.WARNING)
    # logging.getLogger("botocore").setLevel(logging.WARNING)


def get_logger(name: str) -> LoggingLogger:
    """Get a logger instance with the specified name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance with structured logging and rich console support
    """
    # Register our custom logger class
    logging.setLoggerClass(LoggingLogger)
    return logging.getLogger(name)
