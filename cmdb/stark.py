# /usr/bin/env python
# -*- coding:utf-8 -*-
# Author  : wuyifei
# Data    : 11/13/18 3:56 PM
# FileName: stark.py
from django.shortcuts import HttpResponse, render
from django.conf.urls import url
from stark.service.stark import site, StarkConfig, get_choice_text, Option, StarkModelForm
from stark.forms.widgets import DatePickerInput
from cmdb import models
from django.utils.safestring import mark_safe

# IDC管理
class IDCConfig(StarkConfig):
    list_display = ['name', 'floor', ]
    search_list = ['name', 'floor']


site.register(models.IDC, IDCConfig)

class ServerModelForm(StarkModelForm):
    class Meta:
        model = models.Server
        # fields = "__all__"
        exclude = ['sn','manufacturer','model']
        widgets = {
            'latest_date': DatePickerInput(attrs={'class': 'date-picker'})
        }


class ServerConfig(StarkConfig):
    def display_status(self, row=None, header=False):
        if header:
            return '状态'
        from django.utils.safestring import mark_safe
        data = row.get_server_status_id_display()
        tpl = "<span style='color:green'>%s</span>" % data
        return mark_safe(tpl)

    def display_detail(self, row=None, header=False):
        """
        查看详细
        :param row:
        :param header:
        :return:
        """
        if header:
            return '查看详细'
        return mark_safe("<a href='/stark/cmdb/server/%s/detail/'>查看详细</a>" % row.id)

    def display_business(self, row=None, header=False):
        if header:
            return '主机组'
        data = row.business_unit.values()
        tpl = ""
        for b in data:
            tpl += "<a class='btn btn-success btn-outline btn-xs'>%s</a>"%b['name']

        return mark_safe(tpl)

    list_display = [

        'hostname',
        'os_platform',
        'os_version',
        display_status,
        display_business,
        # 'business_unit',
        get_choice_text('server_status_id', '状态'),
        display_detail,
    ]
    search_list = ['hostname', 'os_platform', 'business_unit__name']


    list_filter = [
        # Option('business_unit',condition={'id__gt':0},is_choice=False,text_func=lambda x:x.name,value_func=lambda x:x.id,is_multi=True),
        Option('business_unit', condition={'id__gt': 0}, is_choice=False, text_func=lambda x: x.name,
               value_func=lambda x: x.id),
        Option('server_status_id', is_choice=True, text_func=lambda x: x[1], value_func=lambda x: x[0]),
    ]
    # 自定义ModelForm
    model_form_class = ServerModelForm


    def extra_url(self):
        """
        扩展URL
        :return:
        """
        patterns = [
            url(r'^(?P<nid>\d+)/detail/$', self.detail_view),
        ]
        return patterns

    def detail_view(self, request, nid):
        """
        详细页面的视图函数
        :param request:
        :param nid:
        :return:
        """
        server_id = nid
        server_obj = models.Server.objects.filter(id=server_id).first()
        if server_obj:
            memory_query_list = models.Memory.objects.filter(server_obj=server_obj)
            nic_query_list = models.NIC.objects.filter(server_obj=server_obj)
            disk_query_list = models.Disk.objects.filter(server_obj=server_obj)
            ssd_query_list = models.Nvme_ssd.objects.filter(server_obj=server_obj)
            result = {"code": 0, "message": "找到资产"}
        else:
            result = {"code": 1, "message": "未找到指定资产"}

        return render(request, 'asset_detail.html', locals())

site.register(models.Server, ServerConfig)