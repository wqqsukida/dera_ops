from django.shortcuts import render,redirect,HttpResponseRedirect
from django.shortcuts import HttpResponse
from rbac.models import *
from rbac.service.init_permission import init_permission
import copy
import json
import paramiko
import datetime
from utils.md5 import encrypt
from django.forms import Form,fields,widgets
from .models import *
from django.db.models import Q
from django.urls import reverse
from utils.pagination import Pagination

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

    task_new = Task.objects.filter(status=1).count()
    task_finished = Task.objects.filter(status=2).count()
    task_error = Task.objects.filter(status=3).count()
    task_deleted = Task.objects.filter(status=4).count()
    task_pushing = Task.objects.filter(status=5).count()

    return render(request,'index_v1.html',locals())
#========================================================================#
def asset_list(request):
    if request.method == "GET":
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}

        search_q = request.GET.get('q','')
        user_dict = request.session.get('is_login', None)
        print(user_dict)
        if UserProfile.objects.get(name=user_dict['user']).is_admin :
            queryset = Server.objects.filter(hostname__contains=search_q)
        else:
            queryset = Server.objects.filter(hostname__contains=search_q,
                                             business_unit__roles__userprofile__name=user_dict['user'])

        idc_list = IDC.objects.all()
        tag_list = Tag.objects.all()
        business_list = BusinessUnit.objects.all()
        taskmethod_list = TaskMethod.objects.all()
        # 加载分页器
        queryset, page_html = init_paginaion(request, queryset)

        return render(request,'asset.html',locals())

def asset_run_tasks(request):
    if request.method == "POST":
        id_list = request.POST.getlist("input_chk",None)
        print('run_actions id :%s'%id_list)
        server_objs = Server.objects.filter(id__in=id_list)
        server_status_id = request.POST.get("status_ids",None)
        tags = request.POST.getlist("tags",None)
        business_unit = request.POST.getlist("business_units",None)
        taskmethods = request.POST.getlist("taskmethods",None)
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
                elif taskmethods:
                    # 创建任务模板
                    # if request.POST.get("save_model"):
                    title = 'auto_create_taskmodel'
                    content = ''
                    new_tm = TaskModel.objects.create(title=title,content=content)
                    t_objs = TaskMethod.objects.filter(id__in=taskmethods)
                    new_tm.server_obj.add(*server_objs)
                    new_tm.task_obj.add(*t_objs)
                    # 执行刚创建的任务模板
                    for t in new_tm.task_obj.all():
                        for s in new_tm.server_obj.all():
                            ServerTask.objects.create(server_obj=s, task=t)

                    code = 0
                    msg="成功执行主机任务！"
                else:
                    code = 1
                    msg = "没有可执行的任务！"
                result = {"code": code, "message": msg}
            except Exception as e:
                result = {"code": 1, "message": str(e)}
        else:
            result = {"code": 1, "message": "请至少选择一个主机!!"}
        return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}'.
                                    format(result.get("code", ""),
                                           result.get("message", "")))

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
        return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))

def asset_del(request):
    if request.method == "GET":
        id = request.GET.get("server_id",None)

        try:
            Server.objects.get(id=id).delete()
            result = {"code": 0, "message": "删除主机成功！"}
        except Exception as e:
            result = {"code": 1, "message":e }

        return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))

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
        id = request.POST.get("id",None)
        hostname = request.POST.get("hostname",None)
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

        val_dic = {'data':{'hostname':hostname,'sn':sn,'manufacturer':manufacturer,
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

        return HttpResponseRedirect('/cmdb/asset_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))

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
        ssd_id_list = request.POST.getlist("input_chk",None)
        print(ssd_id_list)
        task = request.POST.get("tasks",None)
        try:
            objs=[Task(ssd_obj_id=id,content=task) for id in ssd_id_list]
            Task.objects.bulk_create(objs)
            result = {"code": 0, "message": "批量创建任务成功！"}
        except Exception as e :
            print(e)
            result = {"code": 1, "message": "批量创建任务失败！"}

        return HttpResponseRedirect('/cmdb/ssd_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))

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
        ssd_id = request.POST.get("ssd_id",None)
        task = request.POST.get("task",None)
        try:
            Task.objects.create(ssd_obj_id=ssd_id,content=task)
            result = {"code": 0, "message": "创建任务成功！"}
        except Exception as e :
            print(e)
            result = {"code": 1, "message": "创建任务失败！"}


        return HttpResponseRedirect('/cmdb/ssd_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))

def ssd_task_list(request):
    if request.method == "GET":
        ssd_id = request.GET.get("ssd_id")
        ssd_obj = Nvme_ssd.objects.get(id=ssd_id)
        task_list = Task.objects.filter(ssd_obj=ssd_obj).order_by('-create_date')
        task_list, page_html = init_paginaion(request, task_list)
        return render(request,'ssd_task.html',locals())
    elif request.method == "POST":
        task_id = request.POST.get("task_id")
        task_obj = Task.objects.get(id=task_id)
        t_res = task_obj.task_res
        res = {'res':'task running......'}
        if t_res:
            import ast
            res = ast.literal_eval(t_res)  # 字符串转换字典

        return HttpResponse(json.dumps(res))

def t1(request):
    return render(request,'t1.html')
#========================================================================#
def server_task_status(request):
    '''
    任务执行列表
    :param request:
    :return:
    '''
    if request.method == "GET":
        server_id = request.GET.get("sid")
        server_obj = Server.objects.get(id=server_id)
        queryset = ServerTask.objects.filter(server_obj=server_obj).order_by('-create_date')
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

def server_task_model(request):
    '''
    服务器任务模板列表
    :param request:
    :return:
    '''
    if request.method == "GET":
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}

        queryset = TaskModel.objects.all()
        # 加载分页器
        model_list, page_html = init_paginaion(request, queryset)

        server_queryset = Server.objects.all()
        task_queryset = TaskMethod.objects.all()

        return render(request,'server_task_model.html',locals())

def server_run_model(request):
    '''
    执行任务模板
    :param request:
    :return:
    '''
    if request.method == "GET":
        mid = request.GET.get("mid")
        m_obj = TaskModel.objects.get(id=mid)

        try:
            for t in m_obj.task_obj.all():
                for s in m_obj.server_obj.all():
                    ServerTask.objects.create(server_obj=s,task=t)
            result = {"code": 0, "message": "任务模板执行成功!"}

        except Exception as e:
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/cmdb/server_task_model?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))

def server_create_model(request):
    '''
    创建任务模板
    :param request:
    :return:
    '''
    result = {}
    if request.method == "POST":
        title = request.POST.get("title")
        sid_list = request.POST.getlist("sids")
        tid_list = request.POST.getlist("tids")
        content = request.POST.get("content")
        if title:
            try:
                new_tm = TaskModel.objects.create(title=title,content=content)
                s_objs = Server.objects.filter(id__in=sid_list)
                t_objs = TaskMethod.objects.filter(id__in=tid_list)
                new_tm.server_obj.add(*s_objs)
                new_tm.task_obj.add(*t_objs)
                result = {"code": 0, "message": "任务模板创建成功!"}
            except Exception as e:
                result = {"code": 1, "message": str(e)}
        else:
            result = {"code": 1, "message": "必须指定模板名称!"}
    return HttpResponseRedirect('/cmdb/server_task_model?status={0}&message={1}'.
                                format(result.get("code", ""),
                                       result.get("message", "")))

def server_edit_model(request):
    '''
    修改任务模板
    :param request:
    :return:
    '''
    if request.method == "GET":
        mid = request.GET.get('mid',None)

        m_obj = TaskModel.objects.filter(id=mid)
        m_dict = m_obj.values().first()
        m_dict.pop('create_date')

        as_list = Server.objects.all()
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
        server_obj = request.POST.getlist("sids",None)
        task_obj = request.POST.getlist("tids",None)

        form_data = {
            'title':title,
            'server_obj':server_obj,
            'task_obj':task_obj,
            'content':content
        }

        m_obj = TaskModel.objects.get(id=mid)
        try:
            for k ,v in form_data.items():
                setattr(m_obj,k,v)
                m_obj.save()
            result = {"code": 0, "message": "任务模板修改成功！"}
        except Exception as e:
            print(e)
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/cmdb/server_task_model?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))

def server_del_model(request):
    '''
    删除任务模板
    :param request:
    :return:
    '''
    if request.method == "GET":
        mid = request.GET.get("mid")
        try:
            TaskModel.objects.get(id=mid).delete()
            result = {"code": 0, "message": "任务模板删除成功!"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}
        return HttpResponseRedirect('/cmdb/server_task_model?status={0}&message={1}'.
                                    format(result.get("code", ""),
                                           result.get("message", "")))

def server_taskmethod_list(request):
    '''
    任务项列表
    :param request:
    :return:
    '''
    if request.method == "GET":
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}

        queryset = TaskMethod.objects.all()
        # 加载分页器
        task_list, page_html = init_paginaion(request, queryset)


        return render(request,'server_taskmethod.html',locals())


def server_taskmethod_add(request):
    result = {}
    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        if title:
            try:
                TaskMethod.objects.create(title=title,content=content)
                result = {"code": 0, "message": "任务项创建成功!"}
            except Exception as e:
                result = {"code": 1, "message": str(e)}
        else:
            result = {"code": 1, "message": "必须指定任务名称!"}
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
        form_data = {
            'title':title,
            'content':content
        }
        t_obj = TaskMethod.objects.get(id=tid)
        try:
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