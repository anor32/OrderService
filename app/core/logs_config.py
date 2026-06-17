import logging


def setup_logger():
    logger = logging.getLogger("api_logger")
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        fmt="%(levelname)s:     %(message)s - %(asctime)s"
    )
    console_handler = logging.StreamHandler()
    logger.propagate = False
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


api_logger = setup_logger()
