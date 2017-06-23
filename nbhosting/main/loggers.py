import logging
import logging.config

from pathlib import Path

def init_loggers(dir):

    # accept a path or a string
    path = Path(dir)
    # create if needed
    dir.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig({
        'version' : 1,
        'disable_existing_loggers' : True,
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
                'level': 'INFO',
                'class': 'logging.FileHandler',
                'formatter': 'standard',
                'filename' : str(path / 'nbhosting.log'),
            },
            'monitor': {
                'level': 'INFO',
                'class': 'logging.FileHandler',
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
