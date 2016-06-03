from django.conf import settings
import logging
import random
import string


def get_score():
    return random.randint(30, 65)


def get_logger(logger_name='django'):
    try:
        if logger_name not in settings.LOGGING['loggers'].keys():
            logger_name = 'django'
    except:
        logger_name = 'django'
    logger = logging.getLogger(logger_name)
    return logger


def get_new_code():
    size = 16
    code = ''.join(random.choice(string.letters + string.digits) for _ in range(size))
    return code