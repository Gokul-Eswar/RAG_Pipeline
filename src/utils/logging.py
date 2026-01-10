"""Logging configuration."""

import logging
import sys
import os
from pythonjsonlogger import jsonlogger
from contextvars import ContextVar

# Context variable for request correlation ID
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

class CorrelationIdFilter(logging.Filter):
    """Injects the correlation ID into log records."""
    
    def filter(self, record):
        cid = correlation_id.get()
        record.correlation_id = cid if cid else "N/A"
        return True

def setup_logging(level: str = None):
    """Setup application logging with JSON formatting and correlation IDs.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level = level or os.getenv("LOG_LEVEL", "INFO")
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    
    logger = logging.getLogger()
    logger.setLevel(numeric_level)
    
    # clear existing handlers to avoid duplicates during reload
    if logger.handlers:
        logger.handlers.clear()
        
    handler = logging.StreamHandler(sys.stdout)
    
    # Custom format with added fields
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(correlation_id)s %(filename)s %(lineno)d"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Apply filter to root logger
    logger.addFilter(CorrelationIdFilter())
    
    # Set levels for noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("kafka").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
