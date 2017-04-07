import logging
import logging.config

import os

def init_logger(filename):

    # in case we receive a Path
    filename = str(filename)
    # creating a dir in python is such a pain
    bash = 'f="{}"; d=$(dirname $f); [ -d $d ] || mkdir -p $d'.format(filename)
    os.system(bash)

    logging_config = {
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
                'filename' : filename,
            },
        },
        'loggers': {
            'nbhosting': {
                'handlers': ['nbhosting'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }

    logging.config.dictConfig(logging_config)

    return logging.getLogger('nbhosting')
