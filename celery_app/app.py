import logging
import logging.config
from environs import Env
from celery import Celery
from celery.signals import setup_logging

from logs.logging_settings import logging_config

env: Env = Env()
env.read_env("./.env", override=True)

logging.config.dictConfig(logging_config)

app = Celery(
    'app',
    broker=env("CELERY_BROKER_URL"),
    backend=env("CELERY_RESULT_BACKEND"),
    include=[
        'celery_app.search_task',
    ]
)

app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Almaty",
    enable_utc=False,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=10,
    worker_max_memory_per_child=2_000_000,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_hijack_root_logger=False,
    worker_redirect_stdouts=False,
)

@setup_logging.connect
def _disable_celery_noise(*args, **kwargs):
    for name in (
        "celery",
        "celery.app.trace",
        "celery.worker",
        "celery.redirected",
        "kombu",
        "amqp",
        "billiard",
    ):
        logging.getLogger(name).setLevel(logging.INFO)