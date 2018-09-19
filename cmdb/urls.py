"""auto_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from . import views
urlpatterns = [

    url(r'^asset_list', views.asset_list),
    url(r'^asset_detail', views.asset_detail), #主机详情
    url(r'^asset_add', views.asset_add),
    url(r'^asset_del', views.asset_del),
    url(r'^asset_update', views.asset_update),
    url(r'^asset_change_log', views.asset_change_log), #主机变更记录
    url(r'^asset_run_tasks', views.asset_run_tasks), #批量修改主机

    url(r'^ssd_list', views.ssd_list), #SSD列表
    url(r'^ssd_smartlog', views.ssd_smartlog), #SSD查看smart_log
    url(r'^ssd_push_task', views.ssd_push_task), #SSD创建任务
    url(r'^ssd_task_list', views.ssd_task_list), #SSD任务列表

    url(r'^server_task_status/(?P<sid>\d*)/(?P<fsid>\d*)/(?P<ssid>\d*)/(?P<sts_id>\d*)/$', views.server_task_status),  # 主机任务状态列表
    url(r'^server_task_reload', views.server_task_reload),  # 恢复执行暂停任务
    url(r'^server_task_download', views.server_task_download),  # 下载任务文件
    url(r'^server_task_session', views.server_task_session),  # 任务计划列表
    url(r'^server_create_session', views.server_create_session),  # 创建任务计划
    url(r'^server_copy_session', views.server_copy_session),  # 复制任务计划
    url(r'^server_edit_session', views.server_edit_session),  # 修改任务计划
    url(r'^server_del_session', views.server_del_session),  # 删除任务计划
    url(r'^server_run_session', views.server_run_session),  # 执行任务计划
    url(r'^server_random_runsecs', views.server_random_runsecs),  # 随机执行任务会话
    url(r'^server_random_runs', views.server_random_runs),  # 随机执行任务计划

    url(r'^server_task_secsession', views.server_task_secsession),  # 主机任务会话列表
    url(r'^server_create_secsession', views.server_create_secsession),  # 创建主机任务会话
    url(r'^server_copy_secsession', views.server_copy_secsession),  # 复制主机任务会话
    url(r'^server_edit_secsession', views.server_edit_secsession),  # 修改主机任务会话
    url(r'^server_del_secsession', views.server_del_secsession),  # 删除主机任务会话
    url(r'^server_run_secsession', views.server_run_secsession),  # 执行主机任务会话

    url(r'^server_taskmethod_list', views.server_taskmethod_list),  # 主机任务项
    url(r'^server_taskmethod_add', views.server_taskmethod_add),  # 添加主机任务项
    url(r'^server_taskmethod_edit', views.server_taskmethod_edit),  # 修改主机任务项
    url(r'^server_taskmethod_del', views.server_taskmethod_del),  # 删除主机任务项
    url(r'^server_taskmethod_upload', views.server_taskmethod_upload),  # 上传任务脚本

    url(r'^t1', views.t1),
]
