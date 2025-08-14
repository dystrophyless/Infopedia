import sys

from logs.log_filters import ErrorLogFilter, CriticalLogFilter

logging_config = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '[{asctime}] #{levelname:8} {filename}:{lineno} - {message}',
            'style': '{'
        }
    },
    'filters': {
        'error_filter': {
            '()': ErrorLogFilter
        },
        'critical_filter': {
            '()': CriticalLogFilter
        }
    },
    'handlers': {
        'default': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': sys.stdout
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'filename': 'error.log',
            'mode': 'w',
            'formatter': 'default',
            'filters': ['error_filter']
        },
        'critical_file': {
            'class': 'logging.FileHandler',
            'filename': 'critical.log',
            'mode': 'w',
            'formatter': 'default',
            'filters': ['critical_filter']
        },
    },
    'loggers': {
        '__main__': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'handlers.register_handlers': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'handlers.language_handlers': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'handlers.unfollowed_handlers': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'handlers.user_handlers': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'handlers.client_handlers': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'handlers.admin_handlers': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'database.connection': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'database.db': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'middlewares.throttler': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'middlewares.database': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'middlewares.registration': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'middlewares.membership': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'middlewares.shadow_ban': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'middlewares.statistics': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'middlewares.language_settings': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'middlewares.i18n': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
    },
    'root': {
        'formatter': 'default',
        'handlers': ['default']
    }
}