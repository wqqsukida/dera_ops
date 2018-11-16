#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.forms.widgets import TextInput


class DatePickerInput(TextInput):
    template_name = 'stark/form/date_picker_input.html'
