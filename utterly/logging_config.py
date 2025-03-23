import logging
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(log_dir: str = "logs", log_level: str = "INFO") -> None:
    """
    Configure logging for the application.

    Args:
        log_dir: Directory to store log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Create year-month subdirectory for logs
    date_subdir = datetime.now().strftime("%Y-%m")
    log_path = log_path / date_subdir
    log_path.mkdir(parents=True, exist_ok=True)

    # Configure logging format
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Set up file handler
    log_file = log_path / f"utterly_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(log_format)

    # Set up console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Create loggers for each component
    loggers = ["recorder", "transcriber", "summarizer", "config"]
    for logger_name in loggers:
        logger = logging.getLogger(f"utterly.{logger_name}")
        logger.setLevel(getattr(logging, log_level.upper()))


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance for a specific component.

    Args:
        name: Component name (e.g., 'recorder', 'transcriber')

    Returns:
        logging.Logger: Configured logger instance
    """
    if name:
        return logging.getLogger(f"utterly.{name}")
    return logging.getLogger("utterly")
