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
import os

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
        ####################################添加推送ssd任务请求######################################
        hostname = server_dict['basic']['data']['hostname']
        server_obj = models.Server.objects.filter(hostname=hostname).first()
        task_query_list = models.SSDTask.objects.filter(ssd_obj__server_obj=server_obj,status=1)
        task_list = []
        if task_query_list:
            for task in task_query_list:
                task_list.append({'ssd_node':task.ssd_obj.node,
                                  'task_content':task.content,
                                  'task_id':task.id})

        response.update({'task':task_list})
        # 改变任务的状态：新建任务->推送执行中
        #              创建时间->推送时间
        task_query_list.update(status=5,create_date=datetime.datetime.now())
        ####################################添加推送主机任务请求######################################
        # server_task_query_list = models.ServerTask.objects.filter(server_obj=server_obj,status=1).\
        #     order_by('create_date')
        # st = server_task_query_list.first()    # 只推送一个任务
        # if st:
        #     response.update({'stask':{'stask_id':st.id,
        #                                'script_name':st.task.task_script.name,
        #                                'args_str':''},
        #                               })
        #     models.ServerTask.objects.filter(id=st.id).update(status=5,create_date=datetime.datetime.now())
        # server_task_list = []
        # if server_task_query_list:
        #     for st in server_task_query_list:
        #         server_task_list.append({'stask_id':st.id,
        #                                  'script_name':st.task.task_script.name,
        #                                  'args_str': '',
        #                                  # 'stask_title':st.task.title,
        #                                  # 'stask_content':st.task.content,
        #                                  # 'stask_hasfile':st.task.has_file,
        #                                  # 'stask_file_url':st.task.file_url,
        #                                  })
        # response.update({'stask':server_task_list})
        # # 改变任务的状态：新建任务->推送执行中
        # #              创建时间->推送时间
        # server_task_query_list.update(status=5,create_date=datetime.datetime.now())
        ###########################################################################################
        print('Response to[{0}]:{1}'.format(clien_ip,response))
        return HttpResponse(json.dumps(response))

@csrf_exempt
@api_auth
def task(request):
    if request.method == "POST":
        fd = datetime.datetime.now()
        res = json.loads(request.body.decode('utf-8'))    #结果必须为字典形式
        print(res)
        t_obj = models.SSDTask.objects.filter(id=res.get('task_id'))
        cd = t_obj.first().create_date
        rt = fd - cd  # 计算出实际运行时间
        # for res in res_list:
        if res.get('task_res'):
            t_obj.update(status = 2 , finished_date = fd,
                          run_time = rt ,
                          task_res=res.get('task_res'))
        else:
            t_obj.update(status = 3 , finished_date = fd,
                          run_time = rt)

        return HttpResponse('finish task')
    elif request.method == "GET":
        return HttpResponse('Error api method!')

@csrf_exempt
@api_auth
def stask(request):
    if request.method == "POST":
        # fd = datetime.datetime.now()
        # 获取客户端ip
        if request.META.get('HTTP_X_FORWARDED_FOR'):
            clien_ip = request.META['HTTP_X_FORWARDED_FOR']
        else:
            clien_ip = request.META['REMOTE_ADDR']

        rep = json.loads(request.body.decode('utf-8'))    #结果必须为字典形式
        res = rep.get("res")
        if res:
            for st_res in res:
                st_obj = models.ServerTask.objects.filter(id=st_res.get('stask_id'))
                if st_res.get('status_code') == 2 :
                    st_obj.update(status = 2 , run_time = st_res['run_time']
                                  ,task_res = st_res['data'])
                elif st_res.get('status_code') == 3:
                    st_obj.update(status = 3 , run_time = st_res['run_time']
                                  ,task_res = st_res['data'])

        ####################################添加推送主机任务请求######################################
        hostname = rep.get("hostname")
        response = {}
        server_obj = models.Server.objects.filter(hostname=hostname).first()
        server_task_query_list = models.ServerTask.objects.filter(server_obj=server_obj,status=1).\
            order_by('create_date')
        server_runing_task = models.ServerTask.objects.filter(server_obj=server_obj,status=5)
        st = server_task_query_list.first()    # 只推送一个任务
        if st and not server_runing_task:
            '''
            存在可推送任务且当前主机没有执行中的任务
            '''
            response.update({'stask':{'stask_id':st.id,
                                       'script_name':st.task.task_script.name,
                                       'args_str':''},
                                      })
            models.ServerTask.objects.filter(id=st.id).update(status=5,create_date=datetime.datetime.now())
        print('Response to[{0}]:{1}'.format(clien_ip, response))
        return HttpResponse(json.dumps(response))
    elif request.method == "GET":
        return HttpResponse('Error api method!')

@csrf_exempt
@api_auth
def task_file_headler(request):
    if request.method == "POST":
        file_obj = request.FILES.get('task_file')
        stask_id = request.POST.get('stask_id')
        hostname = request.POST.get('hostname')
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        file_path = os.path.join(settings.BASE_DIR,'tmp',hostname,date)
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        file_name = os.path.join(file_path,file_obj.name)
        f = open(file_name,'wb')
        for c in file_obj.chunks():
            f.write(c)
        f.close()

        models.ServerTask.objects.filter(id=stask_id).update(server_file_url=file_name)

        print('Upload--->', file_name)
    return HttpResponse('Upload file success!')