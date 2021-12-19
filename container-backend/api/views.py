from django.db.models.fields import IPAddressField
from rest_framework.decorators import api_view
from rest_framework.response import Response
import docker
from django.conf import settings
import os
import time
import requests
import json
from .models import TaskContainer
from .tasks import start_task, zip_output_ended_task
from django.http import HttpResponse


@api_view(['POST'])
def launch_blender_container(request):
    scene = request.POST.get('scene_file')
    scene_name = request.POST.get('scene_name')
    task_id = request.POST.get('task_id')
    client = docker.from_env()
    a = client.containers.run(
        f"phillipjensen/requestor:latest", network="golemgrid-backend_swarm-example", detach=True, environment=[f"TASKID={task_id}"])
    a.reload()
    ip_add = a.attrs['NetworkSettings']['Networks']['golemgrid-backend_swarm-example']['IPAMConfig']['IPv4Address']
    TaskContainer.objects.create(
        ip=ip_add, task_id=task_id, container_id=a.id, scene=scene, scene_name=scene_name, scene_file=f"/requestor/scene/{scene_name}")
    return HttpResponse(status=200)


def container_ready(request, task_id):
    start_task.delay(task_id)
    return HttpResponse(status=200)


def task_finished_shutdown_container(request, task_id):
    obj = TaskContainer.objects.get(task_id=task_id)
    client = docker.from_env()
    a = client.containers.get(obj.container_id)
    a.stop()
    zip_output_ended_task.delay(task_id)
    return HttpResponse(status=200)
