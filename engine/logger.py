import logging
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load for standalone usage if needed
load_dotenv()

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE = os.getenv("LOG_FILE", "logs/audit.log")

# Ensure log directory exists
log_path = Path(LOG_FILE)
log_path.parent.mkdir(parents=True, exist_ok=True)

class AuditLogger:
    _logger = None

    @classmethod
    def get_logger(cls):
        if cls._logger is None:
            logger = logging.getLogger("audit")
            logger.setLevel(LOG_LEVEL)

            # Prevent double logging
            logger.propagate = False

            # Formatter: [TIMESTAMP] [LEVEL] [MODULE] Message
            formatter = logging.Formatter(
                '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )

            # Console Handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

            # File Handler
            file_handler = logging.FileHandler(LOG_FILE)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

            cls._logger = logger
        
        return cls._logger

# Export a ready-to-use instance
logger = AuditLogger.get_logger()
