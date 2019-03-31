from django.contrib import admin
from django.urls import include, path
from django.urls import path, re_path
from . import views

app_name = 'api'

urlpatterns = [
    re_path(r'^$', views.TaskView.as_view({'get': 'list'}), name='task_list'),
    re_path(r'^(?P<task_ident>\w{32})/$', views.TaskView.as_view({'get': 'retrieve'}), name='task_detail')
]