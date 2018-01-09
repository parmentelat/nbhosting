from pathlib import Path

import logging
import logging.config
from logging.handlers import TimedRotatingFileHandler

def init_loggers(dir):

    # accept a path or a string
    path = Path(dir)
    # create if needed
    dir.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig({
        'version' : 1,
        'disable_existing_loggers' : False,
        'formatters': { 
            'standard': { 
                'format': '%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s',
                'datefmt': '%m-%d %H:%M:%S'
            },
            'shorter': { 
                'format': '%(asctime)s %(levelname)s %(message)s',
                'datefmt': '%d %H:%M:%S'
            },
        },
        'handlers': {
            'nbhosting': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'when': 'midnight',
                'backupCount': 7,
                'formatter': 'standard',
                'filename' : str(path / 'nbhosting.log'),
            },
            'monitor': {
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'when': 'midnight',
                'backupCount': 7,
                'formatter': 'standard',
                'filename' : str(path / 'monitor.log'),
            },
        },
        'loggers': {
            'nbhosting': {
                'level': 'INFO',
                'handlers': ['nbhosting'],
                'propagate': False,
            },
            'monitor': {
                'level': 'INFO',
                'handlers': ['monitor'],
                'propagate': False,
            },
        },
    })
