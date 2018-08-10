from django.shortcuts import render

# Create your views here.
from django.shortcuts import render,HttpResponse
from django.views.decorators.csrf import csrf_exempt
import datetime
import json
from cmdb import models
from django.db.models import Q
from .plugins import PluginManger
from utils.md5 import encrypt
from django.conf import settings
import time

key = settings.API_TOKEN
# redis,Memcache
visited_keys = {
    # "841770f74ef3b7867d90be37c5b4adfc":时间,  10
}

def api_auth(func):
    def inner(request,*args,**kwargs):
        server_float_ctime = time.time()
        auth_header_val = request.META.get('HTTP_AUTH_TOKEN')
        # 841770f74ef3b7867d90be37c5b4adfc|1506571253.9937866
        if request.META.get('HTTP_X_FORWARDED_FOR'):
            clien_ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            clien_ip = request.META['REMOTE_ADDR']

        if auth_header_val:
            client_md5_str, client_ctime = auth_header_val.split('|', maxsplit=1)
            client_float_ctime = float(client_ctime)

            # 第一关
            if (client_float_ctime + 20) < server_float_ctime:
                res = { 'code': 5, 'msg': '时间不同步!'}
                print('[{0}]:{1}'.format(clien_ip, res))
                return HttpResponse(json.dumps(res))

            # 第二关：
            server_md5_str = encrypt("%s|%s" % (key, client_ctime,))
            if server_md5_str != client_md5_str:
                res = {'code': 6, 'msg': 'token验证失败!'}
                print('[{0}]:{1}'.format(clien_ip, res))
                return HttpResponse(json.dumps(res))

            return func(request,*args,**kwargs)
        else:
            res = {'code': 7, 'msg': '找不到token,请求失败!'}
            print('[{0}]:{1}'.format(clien_ip, res))
            return HttpResponse(json.dumps(res))

    return inner


@csrf_exempt
@api_auth
def server(request):
    if request.method == "GET":
        current_date = datetime.date.today()
        # 获取今日未采集的主机列表
        query_list = models.Server.objects.filter(
            Q(Q(latest_date=None)|Q(latest_date__lt=current_date))   & Q(server_status_id=2)
        )
        host_list = list(query_list.values('hostname'))
        query_list.update(server_status_id=3)

        return HttpResponse(json.dumps(host_list))

    elif request.method == "POST":
        # 客户端提交的最新资产数据
        server_dict = json.loads(request.body.decode('utf-8'))
        # 获取客户端ip
        if request.META.get('HTTP_X_FORWARDED_FOR'):
            clien_ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            clien_ip = request.META['REMOTE_ADDR']

        # print(server_dict)
        # 检查server表中是否有当前资产信息【主机名是唯一标识】
        if not server_dict['basic']['status']:
            return HttpResponse('Server Post Status Error!')
        if clien_ip:
            server_dict['basic']['data']['manage_ip'] = clien_ip
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
        print('[{0}]:{1}'.format(clien_ip,response))
        return HttpResponse(json.dumps(response))

@csrf_exempt
@api_auth
def task(request):
    if request.method == "POST":
        res = json.loads(request.body.decode('utf-8'))    #结果必须为字典形式
        print(res)
        # for res in res_list:
        if res.get('task_res'):
            models.Task.objects.filter(id=res.get('task_id')).\
                update(status = 2 , finished_date = datetime.datetime.now(),
                       task_res=res.get('task_res'))
        else:
            models.Task.objects.filter(id=res.get('task_id')).\
                update(status = 3 , finished_date = datetime.datetime.now())

        return HttpResponse('finish task')
    elif request.method == "GET":
        return HttpResponse('Error api method!')