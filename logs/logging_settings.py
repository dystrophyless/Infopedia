import sys

logging_config = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '[{asctime}] #{levelname:8} {filename}:{lineno} - {message}',
            'style': '{'
        }
    },
    'handlers': {
        'default': {
            'class': 'logging.StreamHandler',
            'formatter': 'default',
            'stream': sys.stdout
        },
    },
    'loggers': {
        '__main__': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'filters.filters': {
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
        'handlers.menu_handlers': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'handlers.subscription_handlers': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'database.connection': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'database.create_tables': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'database.db_users': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'database.db_terms': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'database.db_statistics': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'database.db_search': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'database.db_counters': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'database.db_feedback': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'database.db_feature_usage': {
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
        'middlewares.feature_usage': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'services.terms': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'services.search': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'services.signature': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'services.membership': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'services.definition_service': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'services.notification_service': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'services.term_service': {
            'level': 'DEBUG',
            'handlers': ['default'],
            'propagate': False
        },
        'services.feature_usage': {
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