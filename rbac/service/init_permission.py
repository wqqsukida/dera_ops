from django.conf import settings


def init_permission(user_obj,request):
    """
    初始化权限信息，获取权限信息并放置到session中。
    :param user: Rbac
    :param request:
    :return:
    """
    permission_list = user_obj.user.roles.filter(permissions__id__isnull=False).values('permissions__id',
                                        'permissions__title',              # 用户列表
                                        'permissions__url',
                                        ).distinct()

    menu_permission_list = ['/index_v3/','/index/']
    for item in permission_list:
        # tpl = {
        #     'id':item['permissions__id'],
        #     'title':item['permissions__title'],
        #     'url':item['permissions__url'],
        # }
        menu_permission_list.append(item['permissions__url'])
    print('User menu permission list:%s'%menu_permission_list)
    request.session[settings.PERMISSION_MENU_KEY] = menu_permission_list
