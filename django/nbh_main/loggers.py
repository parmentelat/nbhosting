"""
initialize loggers for nbhosting
"""

import sys

import logging
import logging.config


def init_loggers(debug):
    """
    initialize loggers for nbhosting
    """

    level = 'DEBUG' if debug else 'INFO'

    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'standard': {
                'format': (
                    '%(asctime)s.%(msecs)03d %(levelname)s'
                    ' %(filename)s:%(lineno)d %(message)s'
                ),
                'datefmt': '%m-%d %H:%M:%S'
            },
            'shorter': {
                'format': '%(asctime)s.%(msecs)03d %(levelname)s %(message)s',
                'datefmt': '%d %H:%M:%S'
            },
        },
        'handlers': {
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
                'handlers': ['stdout'],   # logs go to systemd/journal
                'propagate': False,
            },
            'monitor': {
                'level': level,
                'handlers': ['stdout'],   # logs go to systemd/journal
                'propagate': False,
            },
        },
    })
