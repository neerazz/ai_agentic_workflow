import logging


def setup_logging(
        level: int = logging.INFO,
        fmt: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
):
    """
    Configure root logger formatting and level.
    Call this once at application startup.
    """
    logging.basicConfig(format=fmt, level=level)
