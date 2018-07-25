import re

from django.shortcuts import redirect,HttpResponse
from django.conf import settings
from rbac.models import *

class MiddlewareMixin(object):
    def __init__(self, get_response=None):
        self.get_response = get_response
        super(MiddlewareMixin, self).__init__()

    def __call__(self, request):
        response = None
        if hasattr(self, 'process_request'):
            response = self.process_request(request)
        if not response:
            response = self.get_response(request)
        if hasattr(self, 'process_response'):
            response = self.process_response(request, response)
        return response


class RbacMiddleware(MiddlewareMixin):

    def process_request(self,request):
        # 1. 获取当前请求的URL
        # request.path_info
        # 2. 获取Session中保存当前用户的权限
        # request.session.get("permission_url_list')
        current_url = request.path_info

        # 当前请求不需要执行权限验证
        for url in settings.VALID_URL:
            if re.match(url,current_url):
                return None
        # 用户是否登陆
        user_session = request.session.get("is_login")
        if not user_session:
            return redirect('/login/')
        # 用户是否是管理员
        is_superuser = UserProfile.objects.get(name=user_session['user']).is_admin
        if is_superuser:
            return None

        # 检索用户url权限
        permission_list = request.session.get(settings.PERMISSION_MENU_KEY)
        # if not permission_list:
        #     return redirect('/login/')

        flag = False
        for db_url in permission_list:
            regax = "^{0}$".format(db_url)
            if re.match(regax, current_url):
                # print(regax)
                # print(current_url)
                flag = True
                break

        if not flag:
            return redirect('/403/')

        # flag = False
        # for group_id,code_url in permission_dict.items():
        #     for db_url in code_url['urls']:
        #         regax = "^{0}$".format(db_url)
        #         # 用当前访问url匹配permission_dict中对应url的,，获取code list
        #         if re.match(regax, current_url):
        #             # 获取当前用户对当前组内的所有code，并赋值给request
        #             request.permission_code_list = code_url['codes']
        #             flag = True
        #             break
        #     if flag:
        #         break
        #
        # if not flag:
        #     return redirect('/403/')
