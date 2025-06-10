import os
import logging
from logging.handlers import RotatingFileHandler

def get_logger(name: str, filename: str, level=logging.INFO) -> logging.Logger:
    log_dir = "log_dirs"
    os.makedirs(log_dir, exist_ok=True)

    file_path = os.path.join(log_dir, filename)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Tránh lặp log nếu logger đã có handler
    if not logger.handlers:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        file_handler = RotatingFileHandler(file_path, maxBytes=5_000_000, backupCount=3)
        file_handler.setFormatter(formatter)

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(stream_handler)

    return logger
