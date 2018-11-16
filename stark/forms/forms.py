#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.forms import ModelForm


class StarkModelForm(ModelForm):

    def __init__(self, request, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            cls = field.widget.attrs.get('class')
            if cls:
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'


class BootStrapModelForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            cls = field.widget.attrs.get('class')
            if cls:
                field.widget.attrs['class'] += ' form-control'
            else:
                field.widget.attrs['class'] = 'form-control'
