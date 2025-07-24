# project_name/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrms_project.settings')

app = Celery('hrms_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
