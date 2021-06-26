from rest_framework.decorators import api_view
from rest_framework.response import Response
import docker


@api_view(['POST'])
def launch_container(request):
    scene = request.POST.get('scene_file')
    compositing = request.POST.get('use_compositing')
    crops = request.POST.get('crops')
    samples = request.POST.get('samples')
    frames = request.POST.get('frames')
    output_format = request.POST.get('output_format')
    resource_dir = request.POST.get('RESOURCES_DIR')
    work_dir = request.POST.get('WORK_DIR')
    output_dir = request.POST.get('OUTPUT_DIR')
    file = request.FILES['file']
    client = docker.from_env()
    args = '{{"scene_file": "{0}","resolution1": "{1}","resolution2" : "{2}","use_compositing": "False","samples": "100","output_format": "PNG","RESOURCES_DIR": "/golem/resources","WORK_DIR": "/golem/work","OUTPUT_DIR": "/golem/output","outfilebasename" : "out","borderx1" : "0.0","borderx2" : "1.0","bordery1" : "0.0","bordery2" : "1.0"}}'.format(
        request.POST.get('scene_file'), request.POST.get('resolution1'), request.POST.get('resolution2'))
    client.containers.run(f"phillipjensen/requestor:latest",
                          "python3 blender.py --name {args}")
    return Response({"message": "Hello, world!"})
