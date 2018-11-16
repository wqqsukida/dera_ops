from django.template import Library
from types import FunctionType

register = Library()


@register.inclusion_tag('stark/table.html')
def table(cl):
    return {'header_list': cl.header_list(), 'body_list': cl.body_list()}
