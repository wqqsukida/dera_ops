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
        # 加载分页器
        query_params = copy.deepcopy(request.GET) # QueryDict
        current_page = request.GET.get('page',1)
        # per_page = config.per_page
        # pager_page_count = config.pager_page_count
        all_count = queryset.count()
        base_url = request.path_info
        page_obj = Pagination(current_page,all_count,base_url,query_params)
        queryset = queryset[page_obj.start:page_obj.end]
        page_html = page_obj.page_html()

        return render(request,'asset.html',locals())

def asset_run_tasks(request):
    if request.method == "POST":
        id_list = request.POST.getlist("input_chk",None)
        print('run_actions id :%s'%id_list)
        server_objs = Server.objects.filter(id__in=id_list)
        server_status_id = request.POST.get("status_ids",None)
        tags = request.POST.getlist("tags",None)
        business_unit = request.POST.getlist("business_units",None)
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
            else:
                code = 1
                msg = "没有可执行的任务！"
            result = {"code": code, "message": msg}
        except Exception as e:
            result = {"code": 1, "message": str(e)}

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
        query_params = copy.deepcopy(request.GET) # QueryDict
        current_page = request.GET.get('page',1)
        # per_page = config.per_page
        # pager_page_count = config.pager_page_count
        all_count = queryset.count()
        base_url = request.path_info
        page_obj = Pagination(current_page,all_count,base_url,query_params)
        queryset = queryset[page_obj.start:page_obj.end]
        page_html = page_obj.page_html()

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

        return render(request,'ssd_task.html',locals())
    elif request.method == "POST":
        task_id = request.POST.get("task_id")
        task_obj = Task.objects.get(id=task_id)
        t_res = task_obj.task_res
        res = {'res':'task running......'}
        if t_res:
            import ast
            res = ast.literal_eval(t_res)


        return HttpResponse(json.dumps(res))

def t1(request):
    return render(request,'t1.html')