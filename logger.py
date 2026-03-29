import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOGS_FILE = Path('logs/app.log')
logs_file = LOGS_FILE.resolve()
print(f"{logs_file=}")


def create_logger(logger_name: str = __name__):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    console_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s" )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)


    # File handler
    file_handler = RotatingFileHandler(logs_file, maxBytes=1000000, backupCount=3)
    file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger
