import sys

from pathlib import Path

import logging
import logging.config
from logging.handlers import TimedRotatingFileHandler

def init_loggers(debug):

    level = 'INFO' if not debug else 'DEBUG'

    logging.config.dictConfig({
        'version' : 1,
        'disable_existing_loggers' : False,
        'formatters': {
            'standard': {
                'format': '%(asctime)s.%(msecs)03d %(levelname)s %(filename)s:%(lineno)d %(message)s',
                'datefmt': '%m-%d %H:%M:%S'
            },
            'shorter': {
                'format': '%(asctime)s.%(msecs)03d %(levelname)s %(message)s',
                'datefmt': '%d %H:%M:%S'
            },
        },
        'handlers': {
#            'nbhosting': {
#                'class': 'logging.handlers.TimedRotatingFileHandler',
#                'when': 'midnight',
#                'backupCount': 7,
#                'formatter': 'standard',
#                'filename' : str(path / 'nbhosting.log'),
#            },
#            'monitor': {
#                'class': 'logging.handlers.TimedRotatingFileHandler',
#                'when': 'midnight',
#                'backupCount': 7,
#                'formatter': 'standard',
#                'filename' : str(path / 'monitor.log'),
#            },
            'stdout': {
                'level': level,
                'class': 'logging.StreamHandler',
                'formatter': 'standard',
                'stream': sys.stdout,
            }
        },
        'loggers': {
            'nbhosting': {
                'level': level,
                'handlers': ['stdout'],  # no longer on 'nbhosting'
                'propagate': False,
            },
            'monitor': {
                'level': level,
                'handlers': ['stdout'],  # ditto, logs go to systemd/journal
                'propagate': False,
            },
        },
    })
