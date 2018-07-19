from django.shortcuts import render

# Create your views here.
from django.shortcuts import render,HttpResponse
from django.views.decorators.csrf import csrf_exempt
import datetime
import json
from cmdb import models
from django.db.models import Q
from .plugins import PluginManger

@csrf_exempt
def server(request):
    if request.method == "GET":
        current_date = datetime.date.today()
        # 获取今日未采集的主机列表
        host_list = models.Server.objects.filter(
            Q(Q(latest_date=None)|Q(latest_date__lt=current_date))  # & Q(server_status_id=2)
        ).values('hostname')
        host_list = list(host_list)
        return HttpResponse(json.dumps(host_list))

    elif request.method == "POST":
        # 客户端提交的最新资产数据
        server_dict = json.loads(request.body.decode('utf-8'))
        # print(server_dict)
        # 检查server表中是否有当前资产信息【主机名是唯一标识】
        if not server_dict['basic']['status']:
            return HttpResponse('Server Post Status Error!')

        manager = PluginManger()
        response = manager.exec(server_dict)
        ####################################推送任务请求########################################
        hostname = server_dict['basic']['data']['hostname']
        server_obj = models.Server.objects.filter(hostname=hostname).first()
        task_query_list = models.Task.objects.filter(ssd_obj__server_obj=server_obj,status=1)
        task_list = []
        if task_query_list:
            for task in task_query_list:
                task_list.append({'ssd_node':task.ssd_obj.node,
                                  'task_content':task.content,
                                  'task_id':task.id})

        response.update({'task':task_list})
        task_query_list.update(status=5) # 改变任务的状态：新建任务->推送执行中
        ######################################################################################
        print(response)
        return HttpResponse(json.dumps(response))

@csrf_exempt
def task(request):
    if request.method == "POST":
        res = json.loads(request.body.decode('utf-8'))
        print(res)
        # for res in res_list:
        if res.get('task_res'):
            models.Task.objects.filter(id=res.get('task_id')).\
                update(status=2,finished_date=datetime.datetime.now(),
                       task_res=res.get('task_res'))
        else:
            models.Task.objects.filter(id=res.get('task_id')).\
                update(status=3,finished_date=datetime.datetime.now())


        return HttpResponse('finish task')
    elif request.method == "GET":
        return HttpResponse('Error api method!')
