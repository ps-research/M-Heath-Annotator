"""
Structured logging configuration for the annotation system.

Replaces print statements with proper logging for better debugging and monitoring.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from datetime import datetime


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output.

    Makes logs more readable with color coding by level.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'

    # Emoji prefixes
    EMOJI = {
        'DEBUG': '🔍',
        'INFO': '✅',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥',
    }

    def format(self, record):
        # Add color
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.EMOJI.get(levelname, '')} {self.COLORS[levelname]}{levelname}{self.RESET}"

        # Format the message
        result = super().format(record)

        # Reset levelname for other handlers
        record.levelname = levelname

        return result


def setup_logging(
    name: str = "annotation_system",
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_dir: Path = None
) -> logging.Logger:
    """
    Setup structured logging for the application.

    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to log to file
        log_dir: Directory for log files

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_formatter = ColoredFormatter(
        '%(levelname)s [%(name)s] %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_to_file:
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "data" / "logs"

        log_dir.mkdir(parents=True, exist_ok=True)

        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_dir / f"{name}_{timestamp}.log"

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.

    If not configured, will use default configuration.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)

    # Configure if not already configured
    if not logger.handlers:
        logger = setup_logging(name)

    return logger


# Create default logger instances for different modules
def get_worker_logger(annotator_id: int, domain: str) -> logging.Logger:
    """Get logger for a specific worker."""
    return get_logger(f"worker.{annotator_id}.{domain}")


def get_manager_logger() -> logging.Logger:
    """Get logger for worker manager."""
    return get_logger("worker_manager")


def get_watchdog_logger() -> logging.Logger:
    """Get logger for watchdog."""
    return get_logger("watchdog")


def get_api_logger() -> logging.Logger:
    """Get logger for API."""
    return get_logger("api")
