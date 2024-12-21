# from __future__ import absolute_import, unicode_literals
# import os
# from celery import Celery

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zeuz_backend.settings')

# app = Celery('zeuz_backend')

# # Using a string here means the worker doesn't have to serialize
# # the configuration object to child processes.
# # Namespace 'CELERY' means all celery-related configs start with 'CELERY_'.
# app.config_from_object('django.conf:settings', namespace='CELERY')

# # Autodiscover tasks from installed apps
# app.autodiscover_tasks()


from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'zeuz_backend.settings')

app = Celery('zeuz_backend')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related config keys should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


from celery import shared_task

