"""
Structured logger — writes to console and rotating log file.
"""

import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logger(name: str = "root", log_dir: str = "logs") -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    # File handler (5 MB per file, keep 5 backups)
    fh = RotatingFileHandler(
        os.path.join(log_dir, "tor_router.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=5
    )
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger
