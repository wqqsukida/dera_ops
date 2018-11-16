import functools
import time
import copy
from types import FunctionType
from django.conf.urls import url
from django.utils.safestring import mark_safe
from django.shortcuts import HttpResponse, render, redirect
from django.urls import reverse
from django import forms
from django.db.models import Q
from django.http import QueryDict
from django.db.models.fields.related import ForeignKey, ManyToManyField, OneToOneField
from django.forms import modelformset_factory

from stark.forms.forms import StarkModelForm


class ModelConfigMapping(object):

    def __init__(self, model, config, prev):
        self.model = model
        self.config = config
        self.prev = prev


def get_choice_text(field, head):
    """
    获取choice对应的内容
    :param field:  字段名称
    :param head: 表头名称
    :return:
    """

    def inner(self, row=None, header=False):
        if header:
            return head
        func_name = "get_%s_display" % field
        return getattr(row, func_name)()

    return inner


def get_date_text(field, head):
    """
    获取choice对应的内容
    :param field:  字段名称
    :param head: 表头名称
    :return:
    """

    def inner(self, row=None, header=False):
        if header:
            return head
        return getattr(row, field).strftime('%Y-%m-%d')

    return inner


class Row(object):
    def __init__(self, data_list, option, query_dict):
        """
        元组
        :param data_list:元组或queryset
        """
        self.data_list = data_list
        self.option = option
        self.query_dict = query_dict
        # print(self.data_list)
        # print(self.option)
        # print(self.query_dict)
    def __iter__(self):
        yield '<div class="whole">'

        total_query_dict = self.query_dict.copy()
        total_query_dict._mutable = True
        # print(self.query_dict)
        # print(total_query_dict) # <QueryDict: {'page': ['7']}>
        origin_value_list = self.query_dict.getlist(self.option.field)  # [2,]
        # print(self.option.field) # business_unit
        if origin_value_list:
            total_query_dict.pop(self.option.field)
            yield '<a href="?%s">全部</a>' % (total_query_dict.urlencode(),)

        else:
            yield '<a class="active btn-warning" href="?%s">全部</a>' % (total_query_dict.urlencode(),)

        yield '</div>'
        yield '<div class="others">'

        for item in self.data_list:  # item=(),queryset中的一个对象
            val = self.option.get_value(item)
            # print(val) # 1
            text = self.option.get_text(item)
            # print(text) # ops测试环境

            query_dict = self.query_dict.copy()
            query_dict._mutable = True

            if not self.option.is_multi:  # 单选
                if str(val) in origin_value_list:
                    query_dict.pop(self.option.field)
                    yield '<a class="active btn-warning" href="?%s">%s</a>' % (query_dict.urlencode(), text)
                else:
                    query_dict[self.option.field] = val
                    yield '<a href="?%s">%s</a>' % (query_dict.urlencode(), text)
            else:  # 多选
                multi_val_list = query_dict.getlist(self.option.field)
                if str(val) in origin_value_list:
                    # 已经选，把自己去掉
                    multi_val_list.remove(str(val))
                    query_dict.setlist(self.option.field, multi_val_list)
                    yield '<a class="active btn-warning" href="?%s">%s</a>' % (query_dict.urlencode(), text)
                else:
                    multi_val_list.append(val)
                    query_dict.setlist(self.option.field, multi_val_list)
                    yield '<a href="?%s">%s</a>' % (query_dict.urlencode(), text)

        yield '</div>'


class Option(object):

    def __init__(self, field, condition=None, is_choice=False, text_func=None, value_func=None, is_multi=False):
        self.field = field
        self.is_choice = is_choice
        if not condition:
            condition = {}
        self.condition = condition
        self.text_func = text_func
        self.value_func = value_func
        self.is_multi = is_multi

    def get_queryset(self, _field, model_class, config):
        if isinstance(_field, ForeignKey) or isinstance(_field, ManyToManyField):
            row = Row(_field.rel.model.objects.filter(**self.condition), self, config.request.GET)
        else:
            if self.is_choice:
                row = Row(_field.choices, self, config.request.GET)
            else:
                row = Row(model_class.objects.filter(**self.condition), self, config.request.GET)
        return row

    def get_text(self, item):
        if self.text_func:
            return self.text_func(item)
        return str(item)

    def get_value(self, item):
        if self.value_func:
            return self.value_func(item)
        if self.is_choice:
            return item[0]
        return item.pk


class ChangeList(object):
    """
    封装列表页面需要的所有功能
    """

    def __init__(self, config, queryset, q, search_list, page, model_formset):
        self.q = q
        self.search_list = search_list
        self.page = page

        self.config = config
        self.action_list = [{'name': func.__name__, 'text': func.text} for func in config.get_action_list()]

        self.add_btn = config.get_add_btn()

        self.queryset = queryset

        self.list_display = config.get_list_display()
        self.list_edit = config.get_list_edit()
        self.list_filter = config.get_list_filter()
        self.model_formset = model_formset

    def gen_list_filter_rows(self):
        for option in self.list_filter:
            _field = self.config.model_class._meta.get_field(option.field)
            yield option.get_queryset(_field, self.config.model_class, self.config)

    def header_list(self):
        """
        数据表表头
        :param cl:
        :return:
        """
        if self.list_display:
            for name_or_func in self.list_display:
                if isinstance(name_or_func, FunctionType):
                    verbose_name = name_or_func(self.config, header=True)
                else:
                    verbose_name = self.config.model_class._meta.get_field(name_or_func).verbose_name
                yield verbose_name
        else:
            yield self.config.model_class._meta.model_name

    def body_list(self):
        """
        数据表内容
        :return:
        """
        if self.list_edit:
            return self.edit_body()
        return self.origin_body()

    def origin_body(self):
        for row in self.queryset:
            row_list = []
            if not self.list_display:
                row_list.append([row, ])
                yield row_list
                continue
            for name_or_func in self.list_display:
                if isinstance(name_or_func, FunctionType):
                    val = name_or_func(self.config, row=row)
                else:
                    val = getattr(row, name_or_func)
                row_list.append([val, ])
            yield row_list

    def edit_body(self):
        for form in self.model_formset:
            row_list = []
            if not self.list_display:
                row_list.append(form.instance)
                yield row_list
                continue

            for name_or_func in self.list_display:
                pack = []
                if not row_list:
                    pack.append(form['id'])

                if name_or_func in self.list_edit:
                    field = form[name_or_func]
                    pack.append(field)
                    if field.errors:
                        pack.append(field.errors[0])
                else:
                    if isinstance(name_or_func, FunctionType):
                        pack.append(name_or_func(self.config, row=form.instance))
                    else:
                        pack.append(getattr(form.instance, name_or_func))
                row_list.append(pack)
            yield row_list


class StarkConfig(object):

    def display_checkbox(self, row=None, header=False):
        if header:
            return "选择"
        return mark_safe("<input type='checkbox' name='pk' value='%s' />" % row.pk)

    @staticmethod
    def display_edit_del(protocol):
        """
        显示：删除、修改
        :param protocol:
        :return:
        """
        if protocol not in ['edit', 'delete', 'both']:
            raise Exception('protocol must be edit/delete/both')

        def display_edit_del(self, row=None, header=False):
            if header:
                return "操作"
            if protocol == 'edit':
                tpl = '<a href="%s"><i class="fa fa-edit" aria-hidden="true"></i></a></a>' % self.reverse_edit_url(row)
            elif protocol == 'delete':
                tpl = '<a href="%s"><i class="fa fa-trash-o" aria-hidden="true"></i></a></a>' % self.reverse_del_url(
                    row)
            else:
                tpl = """<a href="%s"><i class="fa fa-edit" aria-hidden="true"></i></a></a> |
                <a href="%s"><i class="fa fa-trash-o" aria-hidden="true"></i></a>
                """ % (self.reverse_edit_url(row), self.reverse_del_url(row),)
            return mark_safe(tpl)

        return display_edit_del

    def multi_delete(self, request):
        """
        批量删除的action
        :param request:
        :return:
        """
        pk_list = request.POST.getlist('pk')
        self.model_class.objects.filter(pk__in=pk_list).delete()

    multi_delete.text = "批量删除"

    order_by = ['id']
    list_display = []
    list_edit = []
    model_form_class = None
    action_list = []
    search_list = []
    list_filter = []

    def __init__(self, model_class, site, prev):
        self.model_class = model_class
        self.site = site
        self.prev = prev
        self.request = None
        self.args = None
        self.kwargs = None

        self.back_condition_key = "_filter"

    def get_order_by(self):
        return self.order_by

    def get_list_display(self):
        val = []
        val.extend(self.list_display)
        val.append(StarkConfig.display_edit_del('both'))

        return val

    def get_list_edit(self):
        val = []
        val.extend(self.list_edit)
        return val

    def get_add_btn(self):
        return mark_safe('<a href="%s" class="btn btn-success">添加</a>' % self.reverse_add_url())

    def get_model_form_class(self):
        """
        获取ModelForm类
        :return:
        """
        if self.model_form_class:
            return self.model_form_class

        class AddModelForm(StarkModelForm):
            class Meta:
                model = self.model_class
                fields = "__all__"

        return AddModelForm

    def get_model_form_set_class(self):
        model_formset_cls = modelformset_factory(self.model_class, self.get_model_form_class(),
                                                 fields=self.get_list_edit(),
                                                 extra=0)
        return model_formset_cls

    def get_action_list(self):
        val = []
        val.extend(self.action_list)
        return val

    def get_action_dict(self):
        val = {}
        for item in self.action_list:
            val[item.__name__] = item
        return val

    def get_search_list(self):
        val = []
        val.extend(self.search_list)
        return val

    def get_search_condition(self, request):
        search_list = self.get_search_list()
        q = request.GET.get('q', "")
        con = Q()
        con.connector = "OR"
        if q:
            for field in search_list:
                con.children.append(('%s__contains' % field, q))

        return search_list, q, con

    def get_list_filter(self):
        val = []
        val.extend(self.list_filter)
        return val

    def get_list_filter_condition(self):
        comb_condition = {}
        for option in self.get_list_filter():
            element = self.request.GET.getlist(option.field)
            if element:
                comb_condition['%s__in' % option.field] = element

        return comb_condition

    def get_queryset(self, request, *args, **kwargs):
        return self.model_class.objects

    def changelist_view(self, request, *args, **kwargs):
        """
        所有URL的查看列表页面
        :param request:
        :return:
        """

        if request.method == 'POST' and request.POST.get('_action'):
            action_name = request.POST.get('action')
            action_dict = self.get_action_dict()
            if action_name not in action_dict:
                return HttpResponse('非法请求')
            response = getattr(self, action_name)(request)
            if response:
                return response

        # ##### 处理搜索 #####
        search_list, q, con = self.get_search_condition(request)

        # ##### 处理分页 #####
        from stark.utils.pagination import Pagination

        total_count = self.model_class.objects.filter(con).count()

        query_params = request.GET.copy()
        query_params._mutable = True
        page = Pagination(request.GET.get('page'), total_count, request.path_info, query_params, per_page=7)

        # ##### 获取组合搜索筛选 #####
        origin_queryset = self.get_queryset(request, *args, **kwargs)
        queryset = origin_queryset.filter(con).filter(**self.get_list_filter_condition()).order_by(
            *self.get_order_by()).distinct()[page.start:page.end]

        # ##### model formset #####
        model_form_set_class = self.get_model_form_set_class()
        model_formset = model_form_set_class(queryset=queryset,form_kwargs={'request':request})
        if request.method == "POST" and request.POST.get('_multi_save'):
            model_formset = model_form_set_class(data=request.POST, queryset=queryset,form_kwargs={'request':request})
            if model_formset.is_valid():
                model_formset.save()
                return redirect(self.reverse_list_origin_url())
        cl = ChangeList(self, queryset, q, search_list, page, model_formset)

        context = {
            'cl': cl
        }
        return render(request, 'stark/changelist.html', context)

    def save(self, form, modify=False):
        """
        :param form:
        :param modify: True,表示要修改；False新增
        :return:
        """
        return form.save()

    def add_view(self, request, *args, **kwargs):
        """
        所有添加页面，都在此函数处理
        使用ModelForm实现
        :param request:
        :return:
        """
        ModelFormClass = self.get_model_form_class()
        if request.method == "GET":
            form = ModelFormClass(request=request)
            return render(request, 'stark/change.html', {'form': form})

        form = ModelFormClass(request,request.POST)
        if form.is_valid():
            self.save(form, modify=False)
            return redirect(self.reverse_list_url())
        return render(request, 'stark/change.html', {'form': form})

    def change_view(self, request, pk, *args, **kwargs):
        """
        所有编辑页面
        :param request:
        :param pk:
        :return:
        """
        obj = self.model_class.objects.filter(pk=pk).first()
        if not obj:
            return HttpResponse('数据不存在')

        ModelFormClass = self.get_model_form_class()
        if request.method == 'GET':
            form = ModelFormClass(request,instance=obj)
            return render(request, 'stark/change.html', {'form': form})
        form = ModelFormClass(request,data=request.POST, instance=obj)
        if form.is_valid():
            self.save(form, modify=True)
            return redirect(self.reverse_list_url())
        return render(request, 'stark/change.html', {'form': form})

    def delete_view(self, request, pk, *args, **kwargs):
        """
        所有删除页面
        :param request:
        :param pk:
        :return:
        """

        if request.method == "GET":
            return render(request, 'stark/delete.html', {'cancel_url': self.reverse_list_url()})

        self.model_class.objects.filter(pk=pk).delete()
        return redirect(self.reverse_list_url())

    def wrapper(self, func):
        @functools.wraps(func)
        def inner(request, *args, **kwargs):
            self.request = request
            self.args = args
            self.kwargs = kwargs
            return func(request, *args, **kwargs)

        return inner

    def get_urls(self):
        urlpatterns = [
            url(r'^list/$', self.wrapper(self.changelist_view), name=self.get_list_url_name),
            url(r'^add/$', self.wrapper(self.add_view), name=self.get_add_url_name),
            url(r'^(?P<pk>\d+)/change/', self.wrapper(self.change_view), name=self.get_change_url_name),
            url(r'^(?P<pk>\d+)/del/', self.wrapper(self.delete_view), name=self.get_del_url_name),
        ]

        extra = self.extra_url()
        if extra:
            urlpatterns.extend(extra)

        return urlpatterns

    def extra_url(self):
        pass

    @property
    def get_list_url_name(self):
        app_label = self.model_class._meta.app_label
        model_name = self.model_class._meta.model_name
        if self.prev:
            name = '%s_%s_%s_changelist' % (app_label, model_name, self.prev)
        else:
            name = '%s_%s_changelist' % (app_label, model_name)
        return name

    @property
    def get_add_url_name(self):
        app_label = self.model_class._meta.app_label
        model_name = self.model_class._meta.model_name
        if self.prev:
            name = '%s_%s_%s_add' % (app_label, model_name, self.prev)
        else:
            name = '%s_%s_add' % (app_label, model_name)
        return name

    @property
    def get_change_url_name(self):
        app_label = self.model_class._meta.app_label
        model_name = self.model_class._meta.model_name
        if self.prev:
            name = '%s_%s_%s_change' % (app_label, model_name, self.prev)
        else:
            name = '%s_%s_change' % (app_label, model_name)
        return name

    @property
    def get_del_url_name(self):
        app_label = self.model_class._meta.app_label
        model_name = self.model_class._meta.model_name
        if self.prev:
            name = '%s_%s_%s_del' % (app_label, model_name, self.prev)
        else:
            name = '%s_%s_del' % (app_label, model_name)
        return name

    def reverse_list_origin_url(self):
        namespace = self.site.namespace
        name = '%s:%s' % (namespace, self.get_list_url_name)
        list_url = reverse(name, args=self.args, kwargs=self.kwargs)

        if not self.request.GET:
            return list_url

        list_url = "%s?%s" % (list_url, self.request.GET.urlencode(),)
        return list_url

    def reverse_list_url(self):
        namespace = self.site.namespace
        name = '%s:%s' % (namespace, self.get_list_url_name)
        kwargs = copy.deepcopy(self.kwargs)
        if 'pk' in kwargs:
            kwargs.pop('pk')
        list_url = reverse(name, args=self.args, kwargs=kwargs)

        origin_condition = self.request.GET.get(self.back_condition_key)
        if not origin_condition:
            return list_url

        list_url = "%s?%s" % (list_url, origin_condition,)
        return list_url

    def reverse_add_url(self):
        namespace = self.site.namespace
        name = '%s:%s' % (namespace, self.get_add_url_name)
        kwargs = copy.deepcopy(self.kwargs)
        if 'pk' in kwargs:
            kwargs.pop('pk')
        add_url = reverse(name, args=self.args, kwargs=kwargs)

        if not self.request.GET:
            return add_url
        param_str = self.request.GET.urlencode()  # q=嘉瑞&page=2
        new_query_dict = QueryDict(mutable=True)
        new_query_dict[self.back_condition_key] = param_str
        add_url = "%s?%s" % (add_url, new_query_dict.urlencode(),)

        return add_url

    def reverse_edit_url(self, row):
        namespace = self.site.namespace
        name = '%s:%s' % (namespace, self.get_change_url_name)
        kwargs = {'pk': row.pk}
        kwargs.update(self.kwargs)
        edit_url = reverse(name, args=self.args, kwargs=kwargs)

        if not self.request.GET:
            return edit_url
        param_str = self.request.GET.urlencode()  # q=嘉瑞&page=2
        new_query_dict = QueryDict(mutable=True)
        new_query_dict[self.back_condition_key] = param_str
        edit_url = "%s?%s" % (edit_url, new_query_dict.urlencode(),)

        return edit_url

    def reverse_del_url(self, row):
        namespace = self.site.namespace
        name = '%s:%s' % (namespace, self.get_del_url_name)
        kwargs = {'pk': row.pk}
        kwargs.update(self.kwargs)
        del_url = reverse(name, args=self.args, kwargs=kwargs)

        if not self.request.GET:
            return del_url
        param_str = self.request.GET.urlencode()  # q=嘉瑞&page=2
        new_query_dict = QueryDict(mutable=True)
        new_query_dict[self.back_condition_key] = param_str
        del_url = "%s?%s" % (del_url, new_query_dict.urlencode(),)

        return del_url

    @property
    def urls(self):
        return self.get_urls()


class AdminSite(object):
    def __init__(self):
        self._registry = []
        self.app_name = 'stark'
        self.namespace = 'stark'

    def register(self, model_class, stark_config=None, prev=None):
        if not stark_config:
            stark_config = StarkConfig
        obj = ModelConfigMapping(model_class, stark_config(model_class, self, prev), prev)
        self._registry.append(obj)

    def get_urls(self):

        urlpatterns = []
        for item in self._registry:
            app_label = item.model._meta.app_label
            model_name = item.model._meta.model_name
            if item.prev:
                temp = url(r'^%s/%s/%s/' % (app_label, model_name, item.prev), (item.config.urls, None, None))
            else:
                temp = url(r'^%s/%s/' % (app_label, model_name,), (item.config.urls, None, None))
            urlpatterns.append(temp)
        return urlpatterns

    @property
    def urls(self):
        return self.get_urls(), self.app_name, self.namespace


site = AdminSite()
