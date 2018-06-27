#!/usr/bin/env python
# -*- coding:utf-8 -*-
#----------------------------------------------
#@version:    ??                               
#@author:   Dylan_wu                                                        
#@software:    PyCharm                  
#@file:    md5.py
#@time:    2017/9/4 9:39
#----------------------------------------------
import hashlib

def encrypt(pwd):
    obj = hashlib.md5()
    obj.update(pwd.encode('utf-8'))
    res = obj.hexdigest()
    return res