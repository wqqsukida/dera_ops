from django.shortcuts import render,redirect,HttpResponse,HttpResponseRedirect
from rbac.models import *
from cmdb.models import BusinessUnit
from django.db import transaction
from utils import md5
import json

# Create your views here.

def users_list(request):
    if request.method == "GET":
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}
        search_q = request.GET.get('q', '')


        query = UserProfile.objects.filter(name__contains=search_q)
        role_list = Role.objects.all()

        return render(request,'users.html',locals())

def users_add(request):
    result = {}
    if request.method == "POST":
        username = request.POST.get("username",None)
        password = request.POST.get("password",None)
        name = request.POST.get("name",None)
        email = request.POST.get("email",None)
        phone = request.POST.get("phone",None)
        mobile = request.POST.get("mobile",None)

        print(username,password,name,email,phone,mobile)

        try:
            with transaction.atomic():
                password = md5.encrypt(password)
                user_obj = UserProfile.objects.create(name=name,email=email,
                                                      phone=phone,mobile=mobile,)
                AdminInfo.objects.create(username=username,password=password,
                                         user=user_obj)
            result = {"code": 0, "message": "创建用户成功！"}
        except Exception as e:
            result = {"code": 1, "message": e}
            print(e)

        return HttpResponseRedirect('/rbac/users_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))

def users_del(request):
    if request.method == "GET":
        user_id =request.GET.get("user_id",None)

        try:
            with transaction.atomic():
                UserProfile.objects.get(id=user_id).delete()
                result = {"code": 0, "message": "删除用户成功！"}
        except Exception as e:
            result = {"code": 1, "message":e }

        return HttpResponseRedirect('/rbac/users_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))

def users_edit(request):
    if request.method == "GET":
        res = {}
        id = request.GET.get("user_id",None)

        user_obj = UserProfile.objects.filter(id=id)


        user_dict = user_obj.values().first()
        if user_dict:
            roles = user_obj.first().roles.all()
            rid_list = [r.id for r in roles]

            user_dict['roles'] = rid_list

            res = dict(user_dict)
        return HttpResponse(json.dumps(res))

    elif request.method == "POST":

        result = {}
        user_id = request.POST.get("id")
        email = request.POST.get("email",None)
        mobile = request.POST.get("mobile",None)
        phone = request.POST.get("phone",None)
        roles = request.POST.getlist("roles",None)

        form_data = {
            'email':email,
            'mobile':mobile,
            'phone':phone,
            'roles':roles
        }
        user_obj = UserProfile.objects.get(id=user_id)
        try:
            for k ,v in form_data.items():
                setattr(user_obj,k,v)
            user_obj.save()
            result = {"code": 0, "message": "更新用户成功！"}
        except Exception as e:
            print(e)
            result = {"code": 1, "message": e}

        return HttpResponseRedirect('/rbac/users_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))

def users_pwd(request):
    if request.method == "GET":
        user_id = request.GET.get("user_id",None)

        login_id = AdminInfo.objects.get(user_id=user_id).id

        return HttpResponse(json.dumps(login_id))

    elif request.method == "POST":
        id = request.POST.get("id")
        old_password = request.POST.get("old_password")
        new_password = request.POST.get("new_password")
        new_confirm_password = request.POST.get("new_confirm_password")

        if  new_password and new_confirm_password:
            # old_password = md5.encrypt(old_password)
                obj=AdminInfo.objects.get(id=id)
            # db_password = obj.password
            # if db_password == old_password:
                if new_password == new_confirm_password:
                    new_pwd = md5.encrypt(new_confirm_password)
                    setattr(obj,'password',new_pwd)
                    obj.save()
                    result = {"code": 0, "message":"密码修改成功!"}
                else:
                    result = {"code": 1, "message":"两次输入的密码不一致!"}
            # else:
            #     result = {"code": 1, "message": "旧密码输入错误!"}
        else:
            result = {"code": 1, "message": "字段不能为空!"}

        return HttpResponseRedirect('/rbac/users_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))

def roles_list(request):
    if request.method == "GET":
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code": int(status), "message": message}
        search_q = request.GET.get('q', '')

        query = Role.objects.filter(title__contains=search_q)
        permission_list = Permission.objects.all()

        return render(request, 'roles.html', locals())


def roles_add(request):
    if request.method == "POST":
        title = request.POST.get("title", None)
        permissions = request.POST.getlist("permissions",None)
        try:
            r_obj = Role.objects.create(title=title)
            p_objs = Permission.objects.filter(id__in=permissions)
            r_obj.permissions.add(*p_objs)
            result = {"code": 0, "message": "创建用户组成功！"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/rbac/roles_list?status={0}&message={1}'.
                                    format(result.get("code", ""),
                                           result.get("message", "")))


def roles_del(request):
    if request.method == "GET":
        role_id =request.GET.get("role_id",None)

        try:
            Role.objects.get(id=role_id).delete()
            result = {"code": 0, "message": "删除用户组成功！"}
        except Exception as e:
            result = {"code": 1, "message":str(e) }

        return HttpResponseRedirect('/rbac/roles_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))


def roles_edit(request):
    if request.method == "GET":
        role_id = request.GET.get('role_id',None)

        r_obj = Role.objects.filter(id=role_id)
        r_dict = r_obj.values().first()

        ap_list = Permission.objects.all()
        rp_list = r_obj.first().permissions.all()

        ap_id = {(p.id,p.title) for p in ap_list}
        rp_id = {(p.id,p.title) for p in rp_list}

        from_list = list(ap_id.difference(rp_id))
        to_list = list(rp_id)

        r_dict['from_list'] = from_list
        r_dict['to_list'] = to_list


        return HttpResponse(json.dumps(dict(r_dict)))
    elif request.method == "POST":

        role_id = request.POST.get("id")
        title = request.POST.get("title",None)

        permissions = request.POST.getlist("permissions",None)

        form_data = {
            'title':title,
            'permissions':permissions
        }

        role_obj = Role.objects.get(id=role_id)
        try:
            for k ,v in form_data.items():
                setattr(role_obj,k,v)
            role_obj.save()
            result = {"code": 0, "message": "修改用户组成功！"}
        except Exception as e:
            print(e)
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/rbac/roles_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))


def permissions_list(request):
    if request.method == "GET":
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code": int(status), "message": message}
        search_q = request.GET.get('q', '')

        query = Permission.objects.filter(title__contains=search_q)

        return render(request, 'permissions.html', locals())


def permissions_add(request):
    if request.method == "POST":
        title = request.POST.get('title',None)
        url = request.POST.get('url',None)
        try:
            Permission.objects.create(title=title,url=url)

            result = {"code": 0, "message": "添加新权限成功！"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/rbac/permissions_list?status={0}&message={1}'.
                                    format(result.get("code", ""),
                                           result.get("message", "")))
def permissions_del(request):
    if request.method == "GET":
        permission_id = request.GET.get("permission_id", None)

        try:
            Permission.objects.get(id=permission_id).delete()
            result = {"code": 0, "message": "删除权限成功！"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/rbac/permissions_list?status={0}&message={1}'.
                                    format(result.get("code", ""),
                                           result.get("message", "")))


def permissions_edit(request):
    if request.method == "GET":
        p_id = request.GET.get("p_id",None)
        val_dic = dict(Permission.objects.filter(id=p_id).values().first())

        return HttpResponse(json.dumps(val_dic))
    elif request.method == "POST":
        id = request.POST.get("id",None)
        title = request.POST.get("title",None)
        url = request.POST.get("url",None)
        if id :
            try:
                p_obj =  Permission.objects.filter(id=id)
                p_obj.update(title=title,url=url)
                result = {"code": 0, "message": "修改权限成功！"}
            except Exception as e:
                result = {"code": 1, "message": str(e)}
        else:
            result = {"code": 1, "message": "操作异常！"}

        return HttpResponseRedirect('/rbac/permissions_list?status={0}&message={1}'.
                                    format(result.get("code", ""),
                                           result.get("message", "")))

def business_list(request):
    if request.method == "GET":
        status = request.GET.get("status", "")
        message = request.GET.get("message", "")
        if status.isdigit():
            result = {"code":int(status),"message":message}
        search_q = request.GET.get('q', '')


        query = BusinessUnit.objects.filter(name__contains=search_q)
        role_list = Role.objects.all()

        return render(request,'business.html',locals())


def business_add(request):
    if request.method == "POST":
        name = request.POST.get("name", None)
        roles = request.POST.getlist("roles",None)
        try:
            b_obj = BusinessUnit.objects.create(name=name)
            r_objs = Role.objects.filter(id__in=roles)
            b_obj.roles.add(*r_objs)
            result = {"code": 0, "message": "创建主机组成功！"}
        except Exception as e:
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/rbac/business_list?status={0}&message={1}'.
                                    format(result.get("code", ""),
                                           result.get("message", "")))


def business_del(request):
    if request.method == "GET":
        b_id =request.GET.get("b_id",None)

        try:
            BusinessUnit.objects.get(id=b_id).delete()
            result = {"code": 0, "message": "删除主机组成功！"}
        except Exception as e:
            result = {"code": 1, "message":str(e) }

        return HttpResponseRedirect('/rbac/business_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))


def business_edit(request):
    if request.method == "GET":
        b_id = request.GET.get('b_id',None)

        b_obj = BusinessUnit.objects.filter(id=b_id)
        b_dict = b_obj.values().first()

        ar_list = Role.objects.all()
        br_list = b_obj.first().roles.all()

        ar_id = {(p.id,p.title) for p in ar_list}
        br_id = {(p.id,p.title) for p in br_list}

        from_list = list(ar_id.difference(br_id))
        to_list = list(br_id)

        b_dict['from_list'] = from_list
        b_dict['to_list'] = to_list


        return HttpResponse(json.dumps(dict(b_dict)))
    elif request.method == "POST":

        b_id = request.POST.get("id")
        name = request.POST.get("name",None)

        roles = request.POST.getlist("roles",None)

        form_data = {
            'name':name,
            'roles':roles
        }

        b_obj = BusinessUnit.objects.get(id=b_id)
        try:
            for k ,v in form_data.items():
                setattr(b_obj,k,v)
            b_obj.save()
            result = {"code": 0, "message": "修改主机组成功！"}
        except Exception as e:
            print(e)
            result = {"code": 1, "message": str(e)}

        return HttpResponseRedirect('/rbac/business_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))