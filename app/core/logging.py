import logging
import sys

from pythonjsonlogger.json import JsonFormatter

from app.core.config import settings


def configure_logging() -> None:
    # 1. Decide where log messages are sent
    # if you omit "sys.stdout", StreamHandler() defaults to "sys.stderr"
    handler = logging.StreamHandler(sys.stdout)

    # uncomment if want to save messages into a file (too):
    # file_handler = logging.FileHandler("service.log")

    # 2. Decide how each log message is formatted
    handler.setFormatter(
        JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )

    # uncomment if using "file_handler":
    # file_handler.setFormatter(
    #     JsonFormatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    # )

    # 3. Configure the root logger
    logger = logging.getLogger()

    # Remove existing handlers to avoid duplicate output
    logger.handlers.clear()

    # Attach our handler to the root logger
    logger.addHandler(handler)

    # uncomment if using "file_handler":
    # logger.addHandler(file_handler)

    # Accept INFO and higher-level messages
    logger.setLevel(settings.log_level.upper())
