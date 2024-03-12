import logging

LOG_FORMAT = "%(asctime)s - %(name)s [%(levelname)s]: %(message)s"
DATE_FORMAT = "%Y/%m/%d %H:%M:%S"


def setup_file_logger(
    name: str,
    path: str,
):
    """Build a logger that writes to the specified file."""

    # Setup basic logger configuration
    logger = logging.getLogger(name)
    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # Setup the correct handler
    file_logger = logging.FileHandler(path)

    # Apply formatter to the handler
    file_logger.setFormatter(formatter)

    # Apply the handler to the logger
    logger.addHandler(file_logger)

    return logger


def setup_console_logger(
    name: str,
):
    """Build a logger that streams the log to the console."""

    # Setup basic logger configuration
    logger = logging.getLogger(name)
    formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)

    # Setup the correct handler
    console_logger = logging.StreamHandler()

    # Apply formatter to the handler
    console_logger.setFormatter(formatter)

    # Apply the handler to the logger
    logger.addHandler(console_logger)

    return logger
