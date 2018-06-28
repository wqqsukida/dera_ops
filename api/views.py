from django.shortcuts import render

# Create your views here.
from django.shortcuts import render,HttpResponse
from django.views.decorators.csrf import csrf_exempt
from datetime import date
import json
from cmdb import models
from django.db.models import Q
from .plugins import PluginManger

@csrf_exempt
def server(request):
    if request.method == "GET":
        current_date = date.today()
        # 获取今日未采集的主机列表
        host_list = models.Server.objects.filter(
            Q(Q(latest_date=None)|Q(latest_date__date__lt=current_date)) & Q(server_status_id=2)
        ).values('hostname')
        host_list = list(host_list)
        return HttpResponse(json.dumps(host_list))

    elif request.method == "POST":
        # 客户端提交的最新资产数据
        server_dict = json.loads(request.body.decode('utf-8'))

        # 检查server表中是否有当前资产信息【主机名是唯一标识】
        if not server_dict['basic']['status']:
            return HttpResponse('Server Post Status Error!')

        manager = PluginManger()
        response = manager.exec(server_dict)
        print(response)
        return HttpResponse(json.dumps(response))