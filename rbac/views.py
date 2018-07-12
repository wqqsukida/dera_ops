from django.shortcuts import render,redirect,HttpResponse,HttpResponseRedirect
from rbac.models import *
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
            result = {"code": 0, "message": "更新用户成功！"}
        except Exception as e:
            print(e)
            result = {"code": 1, "message": e}

        return HttpResponseRedirect('/rbac/users_list?status={0}&message={1}'.
                            format(result.get("code", ""),
                                   result.get("message", "")))


def roles(request):
    if request.method == "GET":
        pass


def roles_add(request):
    if request.method == "POST":
        pass


def roles_del(request):
    if request.method == "GET":
        pass


def roles_edit(request):
    if request.method == "GET":
        pass
    else:
        pass


def permissions(request):
    if request.method == "GET":
        pass


def permissions_add(request):
    if request.method == "POST":
        pass


def permissions_del(request):
    if request.method == "GET":
        pass


def permissions_edit(request):
    if request.method == "GET":
        pass
    else:
        pass


def business(request):
    if request.method == "GET":
        pass


def business_add(request):
    if request.method == "POST":
        pass


def business_del(request):
    if request.method == "GET":
        pass


def business_edit(request):
    if request.method == "GET":
        pass
    else:
        pass