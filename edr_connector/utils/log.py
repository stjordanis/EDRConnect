import logging
import logging.handlers


def get_logger() -> logging.Logger:
    _logger = logging.getLogger(__name__)
    _logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    _logger.addHandler(handler)
    return _logger
