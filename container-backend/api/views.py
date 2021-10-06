from rest_framework.decorators import api_view
from rest_framework.response import Response
import docker
from django.conf import settings
import os
import time
import requests
import json


@api_view(['POST'])
def launch_blender_container(request):
    scene = request.POST.get('scene_file')
    scene_name = request.POST.get('scene_name')
    print(scene_name)
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
    time.sleep(30)
    a.reload()
    ip_add = a.attrs['NetworkSettings']['Networks']['golemgrid-backend_swarm-example']['IPAMConfig']['IPv4Address']
    scene_upload_url = f"http://{ip_add}/files/"
    params_upload_url = f"http://{ip_add}/params/"
    files = {'scene_file': open(
        settings.MEDIA_ROOT + scene, 'rb')}
    params = {'params': open('data.json', 'rb')}
    r = requests.post(scene_upload_url, files=files)
    r_params = requests.post(params_upload_url, files=params)
    print(args)
    if r.status_code == 200:
        cmd = "/bin/bash export YAGNA_APPKEY=$(yagna app-key list --json | jq -r .values[0][1]) && python3 /requestor/blender.py -j /requestor/data.json <&- &"
        a.exec_run(cmd, detach=True)
        a.reload()
        print(a.logs())
