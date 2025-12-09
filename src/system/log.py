import logging
import os
from datetime import datetime


LOG_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOG_DIR, exist_ok=True)


def _make_log_path():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    return os.path.join(LOG_DIR, f"run_{timestamp}.log")


def configure_root_logger(level=logging.INFO):
    """Configure root logger to write to a timestamped file only.

    This is idempotent: calling multiple times won't add duplicate handlers.
    It removes any existing StreamHandler to avoid stdout/stderr logging.
    Ensures idempotence.
    """
    root = logging.getLogger() # all loggers will propagate to root
    if getattr(root, '_beruto_configured', False):
        return

    root.setLevel(level)

    # remove existing console handlers so we don't log to stdout/stderr
    for h in list(root.handlers):
        if isinstance(h, logging.StreamHandler):
            root.removeHandler(h)

    # file handler (only)
    fh = logging.FileHandler(_make_log_path(), encoding='utf-8')
    fh.setLevel(level)
    fh_formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] %(message)s')
    fh.setFormatter(fh_formatter)
    root.addHandler(fh)

    root._beruto_configured = True


def get_logger(name: str = None):
    """
    Pass different __name__ to get loggers for different modules.
    Ensures root logger is configured on first call.
    """ 
    configure_root_logger()

    # there is a registry of loggers, every call to getLogger with the same name
    # returns the same logger instance.
    return logging.getLogger(name)
