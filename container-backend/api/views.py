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
from .tasks import start_task
from django.http import HttpResponse


@api_view(['POST'])
def launch_blender_container(request):
    scene = request.POST.get('scene_file')
    scene_name = request.POST.get('scene_name')
    compositing = request.POST.get('use_compositing')
    crops = request.POST.get('crops')
    samples = request.POST.get('samples')
    frames = request.POST.get('frames')
    output_format = request.POST.get('output_format')
    resource_dir = request.POST.get('RESOURCES_DIR')
    work_dir = request.POST.get('WORK_DIR')
    output_dir = request.POST.get('OUTPUT_DIR')
    task_id = request.POST.get('task_id')
    client = docker.from_env()
    args = '{{"scene_file": "/requestor/scene/{0}", "scene_name": "{0}", "resolution1": {1},"resolution2" : {2},"use_compositing": "False","samples": 100,"output_format": "PNG","RESOURCES_DIR": "/golem/resources","WORK_DIR": "/golem/work","OUTPUT_DIR": "/golem/output","outfilebasename" : "out","borderx1" : 0.0,"borderx2" : 1.0,"bordery1" : 0.0,"bordery2" : 1.0}}'.format(
        scene_name, request.POST.get('resolution1'), request.POST.get('resolution2'))
    with open('data.json', 'w') as f:
        f.write(args)
    a = client.containers.run(
        f"phillipjensen/requestor:latest", network="golemgrid-backend_swarm-example", detach=True, environment=[f"TASKID={task_id}"])
    a.reload()
    ip_add = a.attrs['NetworkSettings']['Networks']['golemgrid-backend_swarm-example']['IPAMConfig']['IPv4Address']
    TaskContainer.objects.create(
        ip=ip_add, task_id=task_id, task_args=args, container_id=a.id, scene=scene)
    return HttpResponse(status=200)


def container_ready(request, task_id):
    start_task.delay(task_id)
    return HttpResponse(status=200)


def task_finished_shutdown_container(request, task_id):
    obj = TaskContainer.objects.get(task_id=task_id)
    client = docker.from_env()
    a = client.containers.get(obj.container_id)
    a.stop()
    return HttpResponse(status=200)
