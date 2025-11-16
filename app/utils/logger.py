import logging
from app.constants import LoggingConstants


def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LoggingConstants.LOG_LEVEL_DEBUG))
    return logger
