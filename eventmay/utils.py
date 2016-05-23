from django.conf import settings
import logging
import random


def get_score():
    return random.randint(50, 100)


def get_logger(logger_name='django'):
    try:
        if logger_name not in settings.LOGGING['loggers'].keys():
            logger_name = 'django'
    except:
        logger_name = 'django'
    logger = logging.getLogger(logger_name)
    return logger