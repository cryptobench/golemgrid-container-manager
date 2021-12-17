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


@app.task
def start_task(task_id):
    obj = TaskContainer.objects.get(task_id=task_id)
    with open('data.json', 'w') as f:
        f.write(obj.task_args)
    client = docker.from_env()
    a = client.containers.get(obj.container_id)
    scene_upload_url = f"http://{obj.ip}/files/"
    params_upload_url = f"http://{obj.ip}/params/"
    files = {'scene_file': open(
        settings.MEDIA_ROOT + obj.scene, 'rb')}
    if os.environ.get("ARM"):
        with open('data.json', 'r+') as f:
            data = json.load(f)
            print(data)
            data['startframe'] = 1
            data['endframe'] = 5
            f.seek(0)
            json.dump(data, f)
    else:
        process = subprocess.check_output(
            ['blender', '-b', settings.MEDIA_ROOT + obj.scene, '-P', '/get_frames.py'])
        start_frame = re.search(r"\|(.*?)\|", process.decode('UTF-8').rstrip())
        end_frame = re.search(r"\[([A-Za-z0-9_]+)\]",
                              process.decode('UTF-8').rstrip())
        with open('data.json', 'r+') as f:
            data = json.load(f)
            data['startframe'] = start_frame.group(1)
            data['endframe'] = end_frame.group(1)
            f.seek(0)
            json.dump(data, f)
    params = {'params': open('data.json', 'rb')}
    r = requests.post(scene_upload_url, files=files)
    r_params = requests.post(params_upload_url, files=params)
    if r.status_code == 200:
        cmd = "/bin/bash export YAGNA_APPKEY=$(yagna app-key list --json | jq -r .values[0][1]) && python3 /requestor/blender.py -j /requestor/data.json <&- &"
        a.exec_run(cmd, detach=True)
        a.reload()
        print(a.logs())
