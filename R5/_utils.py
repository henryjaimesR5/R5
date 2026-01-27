import logging

class R5LoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return f'[R5] {msg}', kwargs


def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return R5LoggerAdapter(logger, {})