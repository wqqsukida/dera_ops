#!/usr/bin/env python
# -*- coding:utf-8 -*-
import itertools


def model_to_dict(instance, fields=None, exclude=None):
    from django.db import models
    opts = instance._meta
    data = {}
    for f in itertools.chain(opts.concrete_fields, opts.private_fields, opts.many_to_many):
        if not getattr(f, 'editable', False):
            continue
        if fields and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        data[f.name] = getattr(instance, f.name)
        if isinstance(f, models.ManyToManyField):
            data[f.name] = list(data[f.name])
    return data
