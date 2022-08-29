from core.celery import app
from celery import Celery
import json
from .models import TaskContainer
import docker
from django.conf import settings
import requests
import subprocess
import re
import os
import shutil


@app.task
def get_task_args(task_id):
    obj = TaskContainer.objects.get(task_id=task_id)
    subprocess.check_output(
        ['blender', '-b', settings.MEDIA_ROOT + obj.scene, '-P', '/get_frames.py', '--', task_id])


@app.task
def start_task(task_id):
    obj = TaskContainer.objects.get(task_id=task_id)
    client = docker.from_env()
    a = client.containers.get(obj.container_id)
    scene_upload_url = f"http://{obj.ip}/files/"
    params_upload_url = f"http://{obj.ip}/params/"
    files = {'scene_file': open(
        settings.MEDIA_ROOT + obj.scene, 'rb')}
    if os.environ.get("ARM"):
        process = subprocess.check_output(
            ['blender', '-b', settings.MEDIA_ROOT + obj.scene, '-P', '/get_frames.py', '--', task_id])
        print(process)
        data = {'startframe': 1, 'endframe': 5,
                "scene_file": obj.scene_file, 'scene_name': obj.scene_name, 'output_format': "PNG", 'output_extension': ".PNG"}
        with open('data.json', 'w') as f:
            json.dump(data, f)
    else:
        process = subprocess.check_output(
            ['blender', '-b', settings.MEDIA_ROOT + obj.scene, '-P', '/get_frames.py'])
        print(process)
        start_frame = re.search(r"\|(.*?)\|", process.decode('UTF-8').rstrip())
        output_extension = re.search(
            r"\%(.*?)\%", process.decode('UTF-8').rstrip())
        output_format = re.search(
            r"\#(.*?)\#", process.decode('UTF-8').rstrip())
        end_frame = re.search(r"\[([A-Za-z0-9_]+)\]",
                              process.decode('UTF-8').rstrip())
        data = {'startframe': int(start_frame.group(
            1)), 'endframe': int(end_frame.group(1)), "scene_file": obj.scene_file, 'scene_name': obj.scene_name, 'output_format': str(output_extension.group(1)), 'output_extension': str(output_format.group(1))}
        with open('data.json', 'w') as f:
            json.dump(data, f)
    params = {'params': open('data.json', 'rb')}
    r = requests.post(scene_upload_url, files=files)
    r_params = requests.post(params_upload_url, files=params)
    if r.status_code == 200:
        cmd = "/bin/bash export YAGNA_APPKEY=$(yagna app-key list --json | jq -r .values[0][1]) && python3 /requestor/blender.py -j /requestor/data.json <&- &"
        a.exec_run(cmd, detach=True)
        a.reload()
        print(a.logs())


@app.task
def zip_output_ended_task(task_id):
    dir = settings.MEDIA_ROOT + task_id
    shutil.make_archive(settings.MEDIA_ROOT + task_id, 'zip', dir)
    shutil.move(settings.MEDIA_ROOT + task_id +
                ".zip", dir + f"/{task_id}.zip")
