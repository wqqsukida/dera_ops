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

    url(r'^asset_list', views.asset_list),
    url(r'^asset_detail', views.asset_detail),
    url(r'^asset_add', views.asset_add),
    url(r'^asset_del', views.asset_del),
    url(r'^asset_update', views.asset_update),
    url(r'^asset_change_log', views.asset_change_log),
    url(r'^ssd_list', views.ssd_list),
    url(r'^ssd_smartlog', views.ssd_smartlog),
    # url(r'^tran.html$', views.tran),
]
