import logging
from logging.handlers import RotatingFileHandler
from .config import settings

def configure_logging():
    # file_handler = RotatingFileHandler("logs/logs.log", encoding='utf-8', maxBytes=5 * 1024 * 1024, backupCount=3)
    console_handler = logging.StreamHandler()

    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    console_handler.setFormatter(formatter)
    # file_handler.setFormatter(formatter)

    logger = logging.getLogger('logger')
    logger.setLevel(logging.DEBUG if settings.DEBUG_MOD else logging.INFO)
    # logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.info('logger initialized to console and file')
    return logger


log = configure_logging()

if __name__ == "__main__":
    log.info("Logger configured successfully")
    log.info("This message should appear in console, file and Seq")