from __future__ import absolute_import

from celery import Celery

celery = Celery('grondview.celery',
                broker='redis://localhost',
                backend='redis://localhost',
                include=['grondview.tasks'])

# Optional configuration, see the application user guide.
celery.conf.update(
    CELERY_TASK_RESULT_EXPIRES=3600,
)

if __name__ == '__main__':
    celery.start()
