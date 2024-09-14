import logging
from logging.handlers import TimedRotatingFileHandler

from app.core.config import settings


def setup_logging():
    logger = logging.getLogger("storm_app_logger")
    logger.setLevel(settings.LOG_LEVEL)
    logger.propagate = False
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    if not logger.hasHandlers():
        if settings.ENVIRONMENT == "local":
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        else:
            debug_handler = TimedRotatingFileHandler(settings.LOG_PATH + '/app_debug.log', when='midnight', interval=1, backupCount=30)
            debug_handler.setLevel(logging.DEBUG)
            debug_handler.setFormatter(formatter)

            info_handler = TimedRotatingFileHandler(settings.LOG_PATH + '/app_info.log', when='midnight', interval=1, backupCount=30)
            info_handler.setLevel(logging.INFO)
            info_handler.setFormatter(formatter)

            error_handler = TimedRotatingFileHandler(settings.LOG_PATH + '/app_error.log', when='midnight', interval=1, backupCount=30)
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)

            class DebugFilter(logging.Filter):
                def filter(self, record):
                    return record.levelno == logging.DEBUG

            class InfoFilter(logging.Filter):
                def filter(self, record):
                    return record.levelno == logging.INFO

            class ErrorFilter(logging.Filter):
                def filter(self, record):
                    return record.levelno == logging.ERROR

            debug_handler.addFilter(DebugFilter())
            info_handler.addFilter(InfoFilter())
            error_handler.addFilter(ErrorFilter())

            logger.addHandler(debug_handler)
            logger.addHandler(info_handler)
            logger.addHandler(error_handler)

    return logger
