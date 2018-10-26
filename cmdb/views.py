from django.shortcuts import render,redirect,HttpResponseRedirect
from django.shortcuts import HttpResponse
from django.http import FileResponse
from rbac.models import *
from rbac.service.init_permission import init_permission
import copy
import json
import random
import datetime
import os
from utils.md5 import encrypt
from django.forms import Form,fields,widgets
from .models import *
from django.db.models import Q
from django.urls import reverse
from utils.pagination import Pagination
from django.http.request import QueryDict
from django.conf import settings
from utils.remote_client import Remote
from utils.ansible_api import Runner

#========================================================================#
def init_paginaion(request,queryset):
    # 初始化分页器
    query_params = copy.deepcopy(request.GET)  # QueryDict
    current_page = request.GET.get('page', 1)
    # per_page = config.per_page
    # pager_page_count = config.pager_page_count
    all_count = queryset.count()
    base_url = request.path_info
    page_obj = Pagination(current_page, all_count, base_url, query_params)
    query_set = queryset[page_obj.start:page_obj.end]
    page_html = page_obj.page_html()

    return query_set,page_html
#========================================================================#
class LoginForm(Form):
    username = fields.CharField(
        required=True,
        error_messages={'required':'*用户名不能为空'},
        widget=widgets.TextInput(attrs={'class':'form-control uname',
                                        'type':'text',
                                        'id':'inputUsername3',
                                        'placeholder':'Username',
                                        'name':'username'
                                        })
    )
    password = fields.CharField(
        required=True,
        error_messages={'required': '*密码不能为空'},
        widget = widgets.PasswordInput(attrs={'class':'form-control pword m-b',
                                        'id':'inputPassword3',
                                        'placeholder':'Password',
                                        'name':'password'
                                        })
    )
#========================================================================#
def login(request):
    '''
    login登录验证函数
    '''
    if request.method == "GET":
        form = LoginForm()
        return render(request,'login_v2.html',{'form':form})
    else:
        response = {'status': True, 'data': None, 'msg': None}
        form = LoginForm(request.POST)
        if form.is_valid():
            user = request.POST.get('username',None)  #获取input标签里的username的值 None：获取不到不会报错
            pwd = request.POST.get('password',None)
            pwd = encrypt(pwd) #md5加密密码字符串
            user_obj = AdminInfo.objects.filter(username=user, password=pwd).first()

            if user_obj:
                role = user_obj.user.roles.values('title')
                # print(role)
                if role:
                    role = role.first().get('title')
                else:
                    role = '访客'
                request.session['is_login'] = {'user': user_obj.user.name, 'role': role}  # 仅作为登录后用户名和身份显示session
                init_permission(user_obj, request)
                response['data'] = {}
            else:
                response['status'] = False
                response['msg'] = {'password': ['*用户名或者密码错误']}
        else:
            response['status'] = False
            response['msg'] = form.errors
        # print(response)
        return HttpResponse(json.dumps(response))

def logout(request):
    '''
    logout删除session函数
    '''
    request.session.clear() #删除session
    return HttpResponseRedirect('/login/')

def forbidden(request):
    return render(request,'403.html')

def index(request):
    '''
    index页面函数
    '''
    user_dict = request.session.get('is_login', None)
    username = user_dict['user']
    user_role = user_dict['role']
    # print('---当前登录用户/角色--->',username,user_role)
    return render(request,'index.html',locals())


def index_v3(request):
    current_date = datetime.date.today()
    # 获取今日未采集的主机列表
    query_list = Server.objects.filter(
        Q(Q(latest_date=None) | Q(latest_date__lt=current_date)) & Q(server_status_id=2)
    )
    host_list = list(query_list.values('hostname'))
    query_list.update(server_status_id=3)
    print(host_list)

    server_up = Server.objects.filter(server_status_id=1).count()
    server_online = Server.objects.filter(server_status_id=2).count()
    server_offline = Server.objects.filter(server_status_id=3).count()
    server_down = Server.objects.filter(server_status_id=4).count()

    task_new = SSDTask.objects.filter(status=1).count()
    task_finished = SSDTask.objects.filter(status=2).count()
    task_error = SSDTask.objects.filter(status=3).count()
    task_deleted = SSDTask.objects.filter(status=4).count()
    task_pushing = SSDTask.objects.filter(status=5).count()

    stask_new = ServerTask.objects.filter(status=1).count()
    stask_finished = ServerTask.objects.filter(status=2).count()
    stask_error = ServerTask.objects.filter(status=3).count()
    stask_deleted = ServerTask.objects.filter(status=4).count()
    stask_pushing = ServerTask.objects.filter(status=5).count()

    return render(request,'index_v1.html',locals())
#========================================================================#
def asset_list(request):
    if request.method == "GET":
        page = request.GET.get("page")
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}

        search_q = request.GET.get('q','')
        user_dict = request.session.get('is_login', None)
        # print(user_dict)
        if UserProfile.objects.get(name=user_dict['user']).is_admin :
            queryset = Server.objects.filter(Q(Q(hostname__contains=search_q) |
                                               Q(sn__contains=search_q) |
                                               Q(manage_ip__contains=search_q) |
                                               Q(os_platform__contains=search_q) |
                                               Q(idc__name__contains=search_q) |
                                               Q(business_unit__name__contains=search_q) |
                                               Q(tags__name__contains=search_q))).distinct()
        else:
            queryset = Server.objects.filter(Q(Q(hostname__contains=search_q) |
                                               Q(sn__contains=search_q) |
                                               Q(manage_ip__contains=search_q) |
                                               Q(os_platform__contains=search_q) |
                                               Q(idc__name__contains=search_q) |
                                               Q(business_unit__name__contains=search_q) |
                                               Q(tags__name__contains=search_q)),
                       business_unit__roles__userprofile__name=user_dict['user']).distinct()

        idc_list = IDC.objects.all()
        tag_list = Tag.objects.all()
        business_list = BusinessUnit.objects.all()
        taskmethod_list = TaskMethod.objects.all()
        taskscript_list = TaskScript.objects.all()
        # 加载分页器
        queryset, page_html = init_paginaion(request, queryset)

        return render(request,'asset.html',locals())

def asset_run_tasks(request):
    if request.method == "POST":
        page = request.POST.get("page")
        id_list = request.POST.getlist("input_chk",None)
        # print('run_actions id :%s'%id_list)
        server_objs = Server.objects.filter(id__in=id_list)
        server_status_id = request.POST.get("status_ids",None)
        tags = request.POST.getlist("tags",None)
        business_unit = request.POST.getlist("business_units",None)
        taskmethods = request.POST.getlist("taskmethods",None)
        task_script_id = request.POST.get("task_script_id",None)
        if server_objs:
            try:
                if server_status_id:
                    server_objs.update(server_status_id=server_status_id)
                    code = 0
                    msg="成功修改主机状态！"
                elif tags:
                    for s in server_objs:
                        setattr(s,'tags',tags)
                        s.save()
                    code = 0
                    msg="成功修改主机标签！"
                elif business_unit:
                    for s in server_objs:
                        setattr(s,'business_unit',business_unit)
                        s.save()
                    code = 0
                    msg="成功修改主机组！"
                # elif taskmethods:
                #     # 创建任务子会话
                #     # if request.POST.get("save_session"):
                #     title = 'auto_create_secsession'
                #     content = ''
                #     new_ts = Task_SecSession.objects.create(title=title,content=content)
                #     t_objs = TaskMethod.objects.filter(id__in=taskmethods)
                #     new_ts.server_obj.add(*server_objs)
                #     new_ts.task_obj.add(*t_objs)
                #     # 执行刚创建的子会话
                #     # for t in new_ts.task_obj.all():
                #     #     for s in new_ts.server_obj.all():
                #     #         ServerTask.objects.create(server_obj=s, task=t)
                #
                #     code = 0
                #     msg="成功执行主机任务！"
                # elif task_script_id:
                #     ts_obj = TaskScript.objects.get(id=task_script_id)
                #     local_file = ts_obj.script_path
                #     remote_file = '/usr/local/src/auto_client/task_handler/script/%s'%ts_obj.name
                #     error_server_list = []
                #     for server in server_objs.values('manage_ip','hostname'):
                #         try:
                #             print(" send {1} to {0}:{2} ".format(server.get("manage_ip"), local_file, remote_file))
                #             rc = Remote(server.get('manage_ip'),username="root",password="test")
                #             rc.scp(local_file,remote_file)
                #         except Exception as e:
                #             error_server_list.append(server.get("hostname"))
                #
                #     if error_server_list:
                #         code = 1
                #         msg = "%s下发脚本失败！"%str(error_server_list)
                #     else:
                #         code = 0
                #         msg = "成功下发任务脚本！"
                else:
                    code = 1
                    msg = "没有可执行的任务！"
                result = {"code": code, "message": msg}
            except Exception as e:
                result = {"code": 1, "message": str(e)}
        else:
            result = {"code": 1, "message": "请至少选择一个主机!!"}
        return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}&page={2}'.
                                    format(result.get("code", ""),
                                           result.get("message", ""),
                                           page))

def asset_detail(request):
    result = {}
    if request.method == "GET":
        server_id = request.GET.get("id",None)
        print(server_id)
        server_obj = Server.objects.filter(id=server_id).first()
        if server_obj:
            memory_query_list = Memory.objects.filter(server_obj=server_obj)
            nic_query_list = NIC.objects.filter(server_obj=server_obj)
            disk_query_list = Disk.objects.filter(server_obj=server_obj)
            ssd_query_list = Nvme_ssd.objects.filter(server_obj=server_obj)
            result = {"code": 0, "message": "找到资产"}
        else:
            result = {"code": 1, "message": "未找到指定资产"}

        return render(request,'asset_detail.html',locals())
    else:
        pass

def asset_add(request):
    result = {}
    if request.method == "POST":
        page = request.POST.get('page')
        hostname = request.POST.get('hostname',None)
        sn = request.POST.get('sn',None)
        server_status_id = request.POST.get('server_status_id',None)
        if hostname:
            try:
                Server.objects.create(hostname=hostname,sn=sn,
                                      server_status_id=server_status_id)
                result = {"code": 0, "message": "创建主机成功！"}
            except Exception as e:
                result = {"code": 1, "message":e }
        else:
            result = {"code": 1, "message": "主机名不能为空！"}
        return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}&page={2}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page))

def asset_del(request):
    if request.method == "GET":
        id = request.GET.get("server_id",None)
        page = request.GET.get("page")
        try:
            Server.objects.get(id=id).delete()
            result = {"code": 0, "message": "删除主机成功！"}
        except Exception as e:
            result = {"code": 1, "message":e }

        return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}&page={2}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page))

def asset_update(request):
    if request.method == "GET":
        res = {}
        id = request.GET.get("server_id",None)

        server_obj = Server.objects.filter(id=id)


        server_dict = server_obj.values().first()
        if server_dict:
            business_unit = server_obj.first().business_unit.all()
            bid_list = [b.id for b in business_unit]
            tags = server_obj.first().tags.all()
            tid_list = [t.id for t in tags]

            server_dict['business_unit'] = bid_list
            server_dict['tags'] = tid_list

            server_dict['latest_date'] = str(server_dict['latest_date'])
            server_dict['create_at'] = str(server_dict['create_at'])
            res = dict(server_dict)
        return HttpResponse(json.dumps(res))

    elif request.method == "POST":

        result = {}
        page = request.POST.get('page')
        id = request.POST.get("id",None)
        # 不允许用户更改唯一标识:主机名
        # hostname = request.POST.get("hostname",None)
        sn = request.POST.get("sn",None)
        manufacturer = request.POST.get("manufacturer",None)
        model = request.POST.get("model",None)
        manage_ip = request.POST.get("manage_ip",None)
        os_platform = request.POST.get("os_platform",None)
        os_version = request.POST.get("os_version",None)

        server_status_id = request.POST.get("server_status_id",None)
        tags = request.POST.getlist("tags",None)
        business_unit = request.POST.getlist("business_unit",None)
        idc = request.POST.get("idc",None)

        val_dic = {'data':{'sn':sn,'manufacturer':manufacturer,
                   'model':model,'manage_ip':manage_ip,'os_platform':os_platform,
                   'os_version':os_version,'server_status_id':server_status_id,
                   'tags':tags,'business_unit':business_unit,'idc_id':idc}}

        try:
            from api.plugins import server
            obj = server.Server(server_obj=Server.objects.get(id=id),basic_dict=val_dic,
                          board_dict={'data':{}})
            obj.user_obj = UserProfile.objects.get(name=request.session['is_login']['user'])
            obj.process()
            result = {"code": 0, "message": "更新主机成功！"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}&page={2}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page))

def asset_change_log(request):
    if request.method == "GET":
        res = []
        id = request.GET.get("server_id",None)
        record_list = ServerRecord.objects.filter(server_obj_id=id).order_by('-create_at')
        if record_list:
            for record in record_list:
                res_dic = {}
                res_dic['content'] = record.content
                if record.creator:
                    res_dic['creator'] = record.creator.name
                else:
                    res_dic['creator'] = '自动上报'

                res_dic['create_at'] = str(record.create_at)
                res.append(res_dic)

        return HttpResponse(json.dumps(res))
#========================================================================#
def ssd_list(request):
    if request.method == "GET":
        page = request.GET.get("page")
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}

        search_q = request.GET.get('q','')
        user_dict = request.session.get('is_login', None)
        if UserProfile.objects.get(name=user_dict['user']).is_admin :
            queryset = Nvme_ssd.objects.filter(node__contains=search_q)
        else:
            queryset = Nvme_ssd.objects.filter(node__contains=search_q,
                                               server_obj__business_unit__roles__userprofile__name=user_dict['user'])

        # 加载分页器
        queryset, page_html = init_paginaion(request, queryset)

        return render(request,'ssd.html',locals())

    elif request.method == "POST":
        '''批量推送任务'''
        page = request.POST.get("page")
        ssd_id_list = request.POST.getlist("input_chk",None)
        print(ssd_id_list)
        task = request.POST.get("tasks",None)
        try:
            objs=[SSDTask(ssd_obj_id=id,content=task) for id in ssd_id_list]
            SSDTask.objects.bulk_create(objs)
            result = {"code": 0, "message": "批量创建任务成功！"}
        except Exception as e :
            print(e)
            result = {"code": 1, "message": "批量创建任务失败！"}

        return HttpResponseRedirect('/cmdb/ssd_list?status={0}&message={1}&page={2}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page))

def ssd_smartlog(request):
    if request.method == "GET":
        step_time = request.GET.get("step_time","1800")  # 默认取30分钟内的smart_log
        if step_time.isdigit():
            step_time = int(step_time)
        ssd_id = request.GET.get("ssd_id",None)
        ssd_obj = Nvme_ssd.objects.get(id=ssd_id)

        limit_time = datetime.datetime.now() - datetime.timedelta(seconds=step_time)
        print(limit_time)
        query = Smart_log.objects.filter(ssd_obj=ssd_obj,log_date__gt=limit_time)
        if not query:
            result = {"code": 1, "message": "获取信息失败！"}
        else:
            result = {"code": 0, "message": "获取信息成功！"}

        return render(request,"ssd_smartlog.html",locals())

def ssd_push_task(request):
    if request.method == "POST":
        page = request.POST.get("page")
        ssd_id = request.POST.get("ssd_id",None)
        task = request.POST.get("task",None)
        try:
            SSDTask.objects.create(ssd_obj_id=ssd_id,content=task)
            result = {"code": 0, "message": "创建任务成功！"}
        except Exception as e :
            print(e)
            result = {"code": 1, "message": "创建任务失败！"}

        return HttpResponseRedirect('/cmdb/ssd_list?status={0}&message={1}&page={2}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page))

def ssd_task_list(request):
    if request.method == "GET":
        ssd_id = request.GET.get("ssd_id")
        ssd_obj = Nvme_ssd.objects.get(id=ssd_id)
        task_list = SSDTask.objects.filter(ssd_obj=ssd_obj).order_by('-create_date')
        task_list, page_html = init_paginaion(request, task_list)
        return render(request,'ssd_task.html',locals())
    elif request.method == "POST":
        task_id = request.POST.get("task_id")
        task_obj = SSDTask.objects.get(id=task_id)
        t_res = task_obj.task_res
        res = {'res':'task running......'}
        if t_res:
            import ast
            res = ast.literal_eval(t_res)  # 字符串转换字典

        return HttpResponse(json.dumps(res))

def t1(request):
    return render(request,'t1.html')
#========================================================================#
#==========主机任务状态视图===========
def server_task_status(request,sid="",ssid="",sts_id="",fsid=""):
    '''
    任务执行列表
    :param request:
    :return:
    '''
    if request.method == "GET":
        # 通知栏
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}

        # server_id = request.GET.get("sid")
        # secsession_id = request.GET.get("ssid")
        # st_status_id = request.GET.get("sts_id")
        # fsid = request.GET.get("fsid")
        server_id=sid
        secsession_id=ssid
        st_status_id=sts_id

        search_q = request.GET.get("q","").strip()
        page = request.GET.get('page')
        q_query = Q(Q(task__title__contains=search_q)|
                    Q(task__content__contains=search_q)|
                    Q(server_obj__hostname__contains=search_q)|
                    Q(secsession_obj__title__contains=search_q)|
                    Q(secsession_obj__father_session__title__contains=search_q)
                    )

        if server_id: #从主机列表访问
            server_obj = Server.objects.get(id=server_id)
            queryset = ServerTask.objects.filter(server_obj=server_obj).order_by('-create_date')
        elif secsession_id: #从任务会话列表访问
            ss_obj = Task_SecSession.objects.get(id=secsession_id)
            if st_status_id == '1':
                queryset = ServerTask.objects.filter(q_query,status=1,secsession_obj=ss_obj).order_by('-create_date')
            elif st_status_id == '2':
                queryset = ServerTask.objects.filter(q_query,status=2,secsession_obj=ss_obj).order_by('-create_date')
            elif st_status_id == '3':
                queryset = ServerTask.objects.filter(q_query,status=3,secsession_obj=ss_obj).order_by('-create_date')
            elif st_status_id == '4':
                queryset = ServerTask.objects.filter(q_query,status=4,secsession_obj=ss_obj).order_by('-create_date')
            elif st_status_id == '5':
                queryset = ServerTask.objects.filter(q_query,status=5,secsession_obj=ss_obj).order_by('-create_date')
            else:
                queryset = ServerTask.objects.filter(q_query,secsession_obj=ss_obj).order_by('-create_date')
        elif fsid:
            fs_obj =  TaskSession.objects.filter(id=fsid)
            ss_objs = fs_obj.values('task_secsession__id')
            ssid_list = [t['task_secsession__id'] for t in ss_objs]
            if st_status_id == '1':
                queryset = ServerTask.objects.filter(q_query,status=1,secsession_obj_id__in=ssid_list).order_by('-create_date')
            elif st_status_id == '2':
                queryset = ServerTask.objects.filter(q_query,status=2,secsession_obj_id__in=ssid_list).order_by('-create_date')
            elif st_status_id == '3':
                queryset = ServerTask.objects.filter(q_query,status=3,secsession_obj_id__in=ssid_list).order_by('-create_date')
            elif st_status_id == '4':
                queryset = ServerTask.objects.filter(q_query,status=4,secsession_obj_id__in=ssid_list).order_by('-create_date')
            elif st_status_id == '5':
                queryset = ServerTask.objects.filter(q_query,status=5,secsession_obj_id__in=ssid_list).order_by('-create_date')
            else:
                queryset = ServerTask.objects.filter(q_query,secsession_obj_id__in=ssid_list).order_by('-create_date')
        else:
            queryset = ServerTask.objects.filter(q_query).order_by('-create_date')
        # 权限处理
        user_dict = request.session.get('is_login', None)
        if not UserProfile.objects.get(name=user_dict['user']).is_admin:
            queryset = queryset.filter(server_obj__business_unit__roles__userprofile__name=user_dict['user'])
        # 加载分页器
        task_list, page_html = init_paginaion(request, queryset)

        return render(request,'server_task.html',locals())
    elif request.method == "POST":
        task_id = request.POST.get("task_id")
        task_obj = ServerTask.objects.get(id=task_id)
        t_res = task_obj.task_res
        res = {'res':'task running......'}
        if t_res:
            import ast
            res = ast.literal_eval(t_res)  # 字符串转换字典

        return HttpResponse(json.dumps(res))

def server_task_reload(request):
    if request.method == "GET":
        tid = request.GET.get("tid")

        fsid = request.GET.get("fsid","")
        ssid = request.GET.get("ssid","")
        sts_id = request.GET.get("sts_id","")
        page = request.GET.get("page","")
        server_id = request.GET.get("sid","")

        try:
            ServerTask.objects.filter(id=tid).update(status=1,finished_date=None)
            result = {"code":0, "message":"任务恢复成功!"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}
        return HttpResponseRedirect('/cmdb/server_task_status/{0}/{1}/{2}/{3}/'
                                    '?status={4}&message={5}&page={6}'.
                                    format(server_id,fsid,ssid,sts_id,
                                           result.get("code", ""),
                                           result.get("message", ""),
                                           page,
                                           ))

def server_task_download(request):
    if request.method == "GET":
        tid = request.GET.get("tid")

        try:
            t_obj = ServerTask.objects.get(id=tid)
            server_file_url = t_obj.server_file_url
            file_name = server_file_url.rsplit('/',1)[-1]
            file = open(server_file_url,'rb')
            rep = FileResponse(file)
            rep['Content-type'] = 'application/octet-stream'
            rep['Content-Disposition'] = 'attachment;filename=%s'%file_name
            return rep
        except Exception as e:
            print(str(e))
            return HttpResponse('DownLoad Error!(%s)'%str(e))
#==========任务会话视图=============
def server_task_secsession(request):
    '''
    服务器任务会话列表
    :param request:
    :return:
    '''
    if request.method == "GET":
        fs_id = request.GET.get("sid","")
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}
        if fs_id:
            queryset = Task_SecSession.objects.filter(father_session_id=fs_id)
            current_session = TaskSession.objects.filter(id=fs_id)
        else:
            queryset = Task_SecSession.objects.all()
        # 加载分页器
        model_list, page_html = init_paginaion(request, queryset)

        server_queryset = Server.objects.all()
        # 权限处理:添加任务会话时只能指定当前用户属组下的主机
        user_dict = request.session.get('is_login', None)
        if not UserProfile.objects.get(name=user_dict['user']).is_admin:
            server_queryset = Server.objects.filter(business_unit__roles__userprofile__name=user_dict['user'])

        task_queryset = TaskMethod.objects.all()

        page = request.GET.get('page')

        return render(request,'server_task_secsession.html',locals())

def server_run_secsession(request):
    '''
    单独执行任务会话
    :param request:
    :return:
    '''
    if request.method == "GET":
        sid = request.GET.get("mid","")
        s_obj = Task_SecSession.objects.get(id=sid)
        status = request.GET.get("status")

        fs_id = request.GET.get("fs_id","")
        page = request.GET.get("page")

        if status == "pause" :
            ServerTask.objects.filter(secsession_obj=s_obj,status=1).update(
                status=4,finished_date=datetime.datetime.now())
            result = {"code": 2, "message": "子任务会话已被暂停执行 !"}
        elif status == "redo" :
            ServerTask.objects.filter(secsession_obj=s_obj,status=4).update(
                status=1,finished_date=None
            )
            result = {"code": 0, "message": "子任务会话已恢复执行 !"}
        else:
            # 权限处理
            user_dict = request.session.get('is_login', None)
            if UserProfile.objects.get(name=user_dict['user']).is_admin:
                server_objs = s_obj.server_obj.all()
            else:
                server_objs = s_obj.server_obj.filter(
                    business_unit__roles__userprofile__name=user_dict['user'])
            # 创建任务
            if server_objs:
                try:
                    for t in s_obj.task_obj.all():
                        for s in server_objs:
                            ServerTask.objects.create(server_obj=s,task=t,
                                                      secsession_obj=s_obj)
                    result = {"code": 0, "message": "任务会话执行成功 !"}
                except Exception as e:
                    result = {"code": 1, "message": str(e)}
            else:
                result = {"code": 1, "message": "你没有权限执行该会话下的任务!"}

        return HttpResponseRedirect('/cmdb/server_task_secsession?status={0}&message={1}&page={2}&sid={3}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page,fs_id))

def server_random_runsecs(request):
    '''
    随机执行任务会话里的任务
    :param request:
    :return:
    '''
    if request.method == "GET":
        sid = request.GET.get("sid","")
        s_obj = Task_SecSession.objects.get(id=sid)

        fs_id = request.GET.get("fs_id","")
        page = request.GET.get("page")

        # 权限处理
        user_dict = request.session.get('is_login', None)
        if UserProfile.objects.get(name=user_dict['user']).is_admin:
            server_objs = s_obj.server_obj.all()
        else:
            server_objs = s_obj.server_obj.filter(business_unit__roles__userprofile__name=user_dict['user'])

        # 创建任务
        if server_objs:
            try:
                for t in s_obj.task_obj.all():
                    s = random.choice(server_objs)
                    # print(s.hostname,t.title)
                    ServerTask.objects.create(server_obj=s,task=t,secsession_obj=s_obj)
                result = {"code": 0, "message": "随机执行成功 !"}
            except Exception as e:
                result = {"code": 1, "message": str(e)}
        else:
            result = {"code": 1, "message": "你没有权限执行该会话下的任务!"}

        return HttpResponseRedirect('/cmdb/server_task_secsession?status={0}&message={1}&page={2}&sid={3}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page,fs_id))

def server_create_secsession(request):
    '''
    创建任务会话
    :param request:
    :return:
    '''
    result = {}
    if request.method == "POST":
        title = request.POST.get("title")
        sid_list = request.POST.getlist("sids")
        tid_list = request.POST.getlist("tids")
        content = request.POST.get("content")
        is_random = request.POST.get("is_random")
        is_random = True if is_random == 'on' else False

        father_session_id = request.POST.get("fs") #要修改的fs_id

        fs_id = request.POST.get("fs_id") #当前页面的fs_id
        page = request.POST.get("page")
        if title:
            try:
                new_ts = Task_SecSession.objects.create(title=title,content=content,
                                                        father_session_id=father_session_id,
                                                        is_random=is_random)
                s_objs = Server.objects.filter(id__in=sid_list)
                t_objs = TaskMethod.objects.filter(id__in=tid_list)
                new_ts.server_obj.add(*s_objs)
                new_ts.task_obj.add(*t_objs)
                result = {"code": 0, "message": "任务会话创建成功!"}
            except Exception as e:
                result = {"code": 1, "message": str(e)}
        else:
            result = {"code": 1, "message": "必须指定会话名称!"}
        return HttpResponseRedirect('/cmdb/server_task_secsession?status={0}&message={1}&page={2}&sid={3}'.
                                    format(result.get("code", ""),
                                           result.get("message", ""),
                                           page, fs_id))

def server_copy_secsession(request):
    '''
    复制当前任务会话
    :param request:
    :return:
    '''
    if request.method == "GET":
        ssid = request.GET.get('ssid',None)
        fs_id = request.GET.get("fs_id")
        page = request.GET.get("page")
        try:
            old_ss = Task_SecSession.objects.filter(id=ssid)
            task_objs = old_ss.first().task_obj.all()
            server_objs = old_ss.first().server_obj.all()
            old_val = old_ss.values('is_random', 'title', 'father_session_id', 'content').first()
            new_ss = Task_SecSession.objects.create(**old_val)
            new_ss.task_obj.add(*task_objs)
            new_ss.server_obj.add(*server_objs)
            result = {"code": 0, "message": "任务会话复制成功!"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}
        return HttpResponseRedirect('/cmdb/server_task_secsession?status={0}&message={1}&page={2}&sid={3}'.
                                    format(result.get("code", ""),
                                           result.get("message", ""),
                                           page, fs_id))


def server_edit_secsession(request):
    '''
    修改任务会话
    :param request:
    :return:
    '''
    if request.method == "GET":
        mid = request.GET.get('mid',None)

        m_obj = Task_SecSession.objects.filter(id=mid)
        m_dict = m_obj.values().first()
        m_dict.pop('create_date')

        as_list = Server.objects.all()
        # 权限处理
        user_dict = request.session.get('is_login', None)
        if not UserProfile.objects.get(name=user_dict['user']).is_admin:
            as_list = Server.objects.filter(business_unit__roles__userprofile__name=user_dict['user'])
        ms_list = m_obj.first().server_obj.all()

        as_id = {(s.id,s.hostname) for s in as_list}
        ms_id = {(s.id,s.hostname) for s in ms_list}

        sfrom_list = list(as_id.difference(ms_id))
        sto_list = list(ms_id)

        m_dict['sfrom_list'] = sorted(sfrom_list)
        m_dict['sto_list'] = sto_list
        #===========================================#

        at_list = TaskMethod.objects.all()
        mt_list = m_obj.first().task_obj.all()

        at_id = {(t.id,t.title) for t in at_list}
        mt_id = {(t.id,t.title) for t in mt_list}

        tfrom_list = list(at_id.difference(mt_id))
        tto_list = list(mt_id)

        m_dict['tfrom_list'] = sorted(tfrom_list)
        m_dict['tto_list'] = tto_list

        return HttpResponse(json.dumps(dict(m_dict)))

    elif request.method == "POST":

        mid = request.POST.get("id")
        title = request.POST.get("title",None)
        content = request.POST.get("content",None)
        is_random = request.POST.get("is_random",None)
        is_random = True if is_random == 'on' else False
        server_obj = request.POST.getlist("sids",None)
        task_obj = request.POST.getlist("tids",None)
        fs = request.POST.get("fs")

        fs_id = request.POST.get("fs_id")
        page = request.POST.get("page")

        form_data = {
            'title':title,
            'server_obj':server_obj,
            'task_obj':task_obj,
            'content':content,
            'is_random':is_random,
            'father_session_id':fs
        }

        m_obj = Task_SecSession.objects.get(id=mid)
        try:
            for k ,v in form_data.items():
                setattr(m_obj,k,v)
                m_obj.save()
            result = {"code": 0, "message": "任务会话更新成功！"}
        except Exception as e:
            print(e)
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/cmdb/server_task_secsession?status={0}&message={1}&page={2}&sid={3}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page,fs_id))

def server_del_secsession(request):
    '''
    删除任务会话
    :param request:
    :return:
    '''
    if request.method == "GET":
        mid = request.GET.get("mid")

        fs_id = request.GET.get("fs_id")
        page = request.GET.get("page")
        try:
            Task_SecSession.objects.get(id=mid).delete()
            result = {"code": 0, "message": "任务会话删除成功!"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}
        return HttpResponseRedirect('/cmdb/server_task_secsession?status={0}&message={1}&page={2}&sid={3}'.
                                    format(result.get("code", ""),
                                           result.get("message", ""),
                                           page,fs_id))
#==========任务模板视图===============
def server_taskmethod_list(request):
    '''
    任务模板列表
    :param request:
    :return:
    '''
    if request.method == "GET":
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}

        queryset = TaskMethod.objects.all()
        script_query = TaskScript.objects.all()
        # 加载分页器
        task_list, page_html = init_paginaion(request, queryset)


        return render(request,'server_taskmethod.html',locals())

    elif request.method == "POST":
        tm_id = request.POST.get("tm_id")
        script_id = TaskMethod.objects.get(id=tm_id).task_script_id
        script_path = TaskScript.objects.get(id=script_id).script_path
        with open(script_path,'r') as f:
            script_content = f.read()
        return HttpResponse(json.dumps(script_content))


def server_taskmethod_add(request):
    result = {}
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        # has_file = request.POST.get("has_file")
        # file_url = request.POST.get("file_url")
        ts_id = request.POST.get("ts_id")
        if title:
            try:
                TaskMethod.objects.create(title=title,content=content,task_script_id=ts_id)
                result = {"code": 0, "message": "任务模板创建成功!"}
            except Exception as e:
                result = {"code": 1, "message": str(e)}
        else:
            result = {"code": 1, "message": "必须指定任务模板名称!"}
    return HttpResponseRedirect('/cmdb/server_taskmethod_list?status={0}&message={1}'.
                                format(result.get("code", ""),
                                       result.get("message", "")))

def server_taskmethod_edit(request):
    if request.method == "GET":
        tid = request.GET.get('tid',None)
        t_obj = TaskMethod.objects.filter(id=tid)
        t_dict = t_obj.values().first()
        t_dict.pop('create_date')

        return HttpResponse(json.dumps(dict(t_dict)))

    elif request.method == "POST":
        tid = request.POST.get("id")
        title = request.POST.get("title",None)
        content = request.POST.get("content",None)
        # has_file = request.POST.get("has_file")
        # file_url = request.POST.get("file_url")
        ts_id = request.POST.get("ts_id",None)
        try:
            ts_obj = TaskScript.objects.get(id=ts_id)
            t_obj = TaskMethod.objects.get(id=tid)
            form_data = {
                'title':title,
                'content':content,
                'task_script':ts_obj,
                # 'has_file':True if has_file == 'on' else False,
                # 'file_url':file_url
            }

            for k ,v in form_data.items():
                setattr(t_obj,k,v)
                t_obj.save()
            result = {"code": 0, "message": "任务项更新成功！"}
        except Exception as e:
            print(e)
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/cmdb/server_taskmethod_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))

def server_taskmethod_del(request):
    if request.method == "GET":
        tid = request.GET.get("tid")
        try:
            TaskMethod.objects.get(id=tid).delete()
            result = {"code": 0, "message": "任务项删除成功!"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}
        return HttpResponseRedirect('/cmdb/server_taskmethod_list?status={0}&message={1}'.
                                    format(result.get("code", ""),
                                           result.get("message", "")))

def server_taskmethod_upload(request):
    if request.method == "POST" :
        file_obj = request.FILES.get('task_script')

        file_path = os.path.join(settings.BASE_DIR,'task_script',file_obj.name)
        f = open(file_path,'wb')
        for c in file_obj.chunks():
            f.write(c)
        f.close()
        try :
            TaskScript.objects.create(name=file_obj.name,script_path=file_path)
            result = {"code": 0, "message": "任务脚本上传成功!"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}
        return HttpResponseRedirect('/cmdb/server_taskmethod_list?status={0}&message={1}'.
                                    format(result.get("code", ""),
                                           result.get("message", "")))

#==========任务计划视图===============
def server_task_session(request):
    '''
    服务器任务会话列表
    :param request:
    :return:
    '''
    if request.method == "GET":
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code": int(status), "message": message}

        queryset = TaskSession.objects.all()
        role_queryset = Role.objects.all()
        # 权限处理
        user_dict = request.session.get('is_login', None)
        if not UserProfile.objects.get(name=user_dict['user']).is_admin:
            queryset = TaskSession.objects.filter(role__userprofile__name=user_dict['user'])
            role_queryset = Role.objects.filter(userprofile__name=user_dict['user'])
        #加载分页器
        session_list, page_html = init_paginaion(request, queryset)

        page = request.GET.get('page')

        return render(request, 'server_task_session.html', locals())

def server_run_session(request):
    if request.method == "GET":
        sid = request.GET.get("sid")
        s_obj = TaskSession.objects.get(id=sid)
        status = request.GET.get("status")

        page = request.GET.get("page")

        ss_list = s_obj.task_secsession_set.all()
        if status == "pause":
            result = {"code": 2, "message": "任务计划已被暂停执行!"}
            for ss in ss_list:
                ServerTask.objects.filter(secsession_obj=ss,status=1).update(
                    status=4,finished_date=datetime.datetime.now())
        elif status == "redo":
            result = {"code": 0, "message": "任务计划已恢复执行!"}
            for ss in ss_list:
                ServerTask.objects.filter(secsession_obj=ss,status=4).update(
                    status=1,finished_date=None)
        else:
            try:
                for ss in ss_list:
                    if ss.is_random:    #随机执行会话
                        for t in ss.task_obj.all():
                            s = random.choice(ss.server_obj.all())
                            print(ss.title, t.title, s.hostname)
                            ServerTask.objects.create(server_obj=s, task=t, secsession_obj=ss)
                    else:   #正常执行会话
                        for t in ss.task_obj.all():
                            for s in ss.server_obj.all():
                                print(ss.title,t.title,s.hostname)
                                ServerTask.objects.create(server_obj=s,task=t,secsession_obj=ss)

                result = {"code": 0, "message": "执行任务计划成功!"}
            except Exception as e:
                result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/cmdb/server_task_session?status={0}&message={1}&page={2}'.
                                    format(result.get("code", ""),
                                           result.get("message", ""),
                                           page))

def server_random_runs(request):
    if request.method == "GET":
        sid = request.GET.get("sid")
        s_obj = TaskSession.objects.get(id=sid)

        page = request.GET.get("page")

        ss_list = s_obj.task_secsession_set.all()
        try:
            for ss in ss_list:
                for t in ss.task_obj.all():
                    s = random.choice(ss.server_obj.all())
                    print(ss.title, t.title, s.hostname)
                    ServerTask.objects.create(server_obj=s,task=t,secsession_obj=ss)

            result = {"code": 0, "message": "随机执行任务计划成功!"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/cmdb/server_task_session?status={0}&message={1}&page={2}'.
                                    format(result.get("code", ""),
                                           result.get("message", ""),
                                           page))

def server_create_session(request):
    '''
    创建任务会话
    :param request:
    :return:
    '''
    result = {}
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        rid = request.POST.get("rid")

        page = request.POST.get("page")
        if title:
            try:
                new_ts = TaskSession.objects.create(title=title, content=content, role_id=rid)
                result = {"code": 0, "message": "任务计划创建成功!"}
            except Exception as e:
                result = {"code": 1, "message": str(e)}
        else:
            result = {"code": 1, "message": "必须指定计划名称!"}
        return HttpResponseRedirect('/cmdb/server_task_session?status={0}&message={1}&page={2}'.
                                    format(result.get("code", ""),
                                           result.get("message", ""),
                                           page))

def server_copy_session(request):
    if request.method == "GET":
        sid = request.GET.get('sid', None)
        page = request.GET.get("page")
        try:
            old_obj = TaskSession.objects.filter(id=sid)
            old_val = old_obj.values('title','content','role_id').first()
            old_ss_objs_query_list = old_obj.first().task_secsession_set.all()
            old_ss_vals_list = old_obj.first().task_secsession_set.values('is_random', 'title', 'content')
            new_obj = TaskSession.objects.create(**old_val) # 新计划
            for ss_obj,ss_val in zip(old_ss_objs_query_list,old_ss_vals_list):
                task_objs = ss_obj.task_obj.all()
                server_objs = ss_obj.server_obj.all()

                new_ss = Task_SecSession.objects.create(**ss_val,father_session_id=new_obj.id)
                new_ss.task_obj.add(*task_objs)
                new_ss.server_obj.add(*server_objs)

            result = {"code": 0, "message": "任务计划复制成功!"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}
        return HttpResponseRedirect('/cmdb/server_task_session?status={0}&message={1}&page={2}'.
                                    format(result.get("code", ""),
                                           result.get("message", ""),
                                           page))

def server_edit_session(request):
    '''
    修改任务会话
    :param request:
    :return:
    '''
    if request.method == "GET":
        sid = request.GET.get('sid',None)

        s_obj = TaskSession.objects.filter(id=sid)
        s_dict = s_obj.values().first()
        s_dict.pop('create_date')

        return HttpResponse(json.dumps(dict(s_dict)))

    elif request.method == "POST":

        sid = request.POST.get("id")
        title = request.POST.get("title",None)
        content = request.POST.get("content",None)
        rid = request.POST.get("rid",None)

        page = request.POST.get("page")

        form_data = {
            'title':title,
            'content':content,
            'role_id':rid,
        }
        s_obj = TaskSession.objects.get(id=sid)
        try:
            for k ,v in form_data.items():
                setattr(s_obj,k,v)
                s_obj.save()
            result = {"code": 0, "message": "任务计划更新成功！"}
        except Exception as e:
            print(e)
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/cmdb/server_task_session?status={0}&message={1}&page={2}'.
                            format(result.get("code", ""),
                                   result.get("message", ""),
                                   page))

def server_del_session(request):
    '''
    删除任务会话
    :param request:
    :return:
    '''
    if request.method == "GET":
        sid = request.GET.get("sid")

        page = request.GET.get("page")
        try:
            TaskSession.objects.get(id=sid).delete()
            result = {"code": 0, "message": "任务计划删除成功!"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}
        return HttpResponseRedirect('/cmdb/server_task_session?status={0}&message={1}&page={2}'.
                                    format(result.get("code", ""),
                                           result.get("message", ""),
                                           page))

def version_info(request):
    '''
    版本信息
    :param request:
    :return:
    '''
    return render(request,'version_info.html')

def firmware_update(request):
    '''
    固件升级
    :param request:
    :return:
    '''
    return render(request,'firmware_update.html')

def client_update(request):
    '''
    客户端升级
    :param request:
    :return:
    '''
    if request.method == "POST" :
        result = {"code":0,"message":"test"}
        hosts = request.POST.getlist("hosts")
        if hosts:
            hosts = ','.join(hosts)+','
        ansible_client = Runner(hosts)
        ansible_client.run_playbook()
        msg = ansible_client.get_playbook_result()

        return HttpResponse(json.dumps(msg))


    elif request.method == "GET" :
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}

        host_query = Server.objects.filter(server_status_id=2)

        return render(request,'client_update.html',locals())