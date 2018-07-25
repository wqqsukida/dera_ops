"""auto_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from . import views
urlpatterns = [
    url(r'^users_list', views.users_list),
    url(r'^users_add', views.users_add),
    url(r'^users_del', views.users_del),
    url(r'^users_edit', views.users_edit),
    url(r'^users_pwd', views.users_pwd),
    url(r'^roles_list', views.roles_list),
    url(r'^roles_add', views.roles_add),
    url(r'^roles_del', views.roles_del),
    url(r'^roles_edit', views.roles_edit),
    url(r'^permissions_list', views.permissions_list),
    url(r'^permissions_add', views.permissions_add),
    url(r'^permissions_del', views.permissions_del),
    url(r'^permissions_edit', views.permissions_edit),
    url(r'^business_list', views.business_list),
    url(r'^business_add', views.business_add),
    url(r'^business_del', views.business_del),
    url(r'^business_edit', views.business_edit),
]
