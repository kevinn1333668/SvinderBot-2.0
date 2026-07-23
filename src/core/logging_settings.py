import logging
import sys
from logging.handlers import RotatingFileHandler


def setup_logging(level: str = "INFO") -> None:
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    data_format = "%Y-%m-%d %H:%M:%S"

    handlers = [
        logging.StreamHandler(sys.stdout),
        RotatingFileHandler(
            "logs/bot.log",
            maxBytes=10 * 1024 * 1024, # 10 MB
            backupCount=5,
            encoding="utf-8",
        ),
    ]

    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=data_format,
        handlers=handlers,
    )

    logging.getLogger("aiogram.event").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)