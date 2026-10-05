import logging
import os


# ==================================================
# LOG DIRECTORY
# ==================================================

LOG_DIR = "logs"

os.makedirs(
    LOG_DIR,
    exist_ok=True
)


# ==================================================
# LOG FILE
# ==================================================

LOG_FILE = os.path.join(
    LOG_DIR,
    "lead_generator.log"
)


# ==================================================
# LOGGER SETUP
# ==================================================

logger = logging.getLogger(
    "TECHUWEB_LEAD_GENERATOR"
)

logger.setLevel(
    logging.INFO
)


# ==================================================
# AVOID DUPLICATE HANDLERS
# ==================================================

if not logger.handlers:

    # File Handler
    file_handler = logging.FileHandler(
        LOG_FILE,
        encoding="utf-8"
    )

    # Console Handler
    console_handler = logging.StreamHandler()

    # ==================================================
    # LOG FORMAT
    # ==================================================

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    file_handler.setFormatter(
        formatter
    )

    console_handler.setFormatter(
        formatter
    )

    # ==================================================
    # ADD HANDLERS
    # ==================================================

    logger.addHandler(
        file_handler
    )

    logger.addHandler(
        console_handler
    )