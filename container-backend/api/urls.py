from django.urls import path
from django.shortcuts import render
from . import views

app_name = 'api'

urlpatterns = [
    path('start/blender', views.launch_blender_container),
    path('container/ping/ready/<task_id>', views.container_ready),
    path('container/ping/shutdown/<task_id>',
         views.task_finished_shutdown_container),
]
