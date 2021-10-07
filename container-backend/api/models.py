from django.db import models
from django.utils import timezone
from django.contrib.postgres.fields import ArrayField
import uuid

# Create your models here.


class TaskContainer(models.Model):
    scene = models.CharField(max_length=128, blank=True, null=True)
    task_args = models.JSONField(null=True)
    task_id = models.UUIDField(unique=True)
    ip = models.GenericIPAddressField(protocol='IPv4')
    container_id = models.CharField(max_length=64, blank=True, null=True)
