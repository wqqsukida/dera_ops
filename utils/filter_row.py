# /usr/bin/env python
# -*- coding:utf-8 -*-
# Author  : wuyifei
# Data    : 11/16/18 2:39 PM
# FileName: filter_row.py

class Row(object):
    def __init__(self,data_list,query_dict,option):
        self.data_list = data_list
        self.query_dict = query_dict
        self.option = option
        self.is_multi = False
    def __iter__(self):
        yield '<div>'
        total_query_dict = self.query_dict.copy()
        total_query_dict._mutable = True
        origin_value_list = self.query_dict.getlist(self.option)  # [2,]
        if origin_value_list:
            total_query_dict.pop(self.option)
            yield '<a class="btn btn-xs btn-warning btn-outline" href="?%s">全部</a>' % (total_query_dict.urlencode(),)
        else:
            yield '<a class="btn btn-xs btn-warning" href="?%s">全部</a>' % (total_query_dict.urlencode(),)

        # yield '</div>'
        # yield '<div class="others">'


        for item in self.data_list:
            val = item['id']
            text = item['name']
            query_dict = self.query_dict.copy()
            query_dict._mutable = True
            if not self.is_multi:

                if str(val) in origin_value_list:
                    query_dict.pop(self.option)
                    yield '<a class="btn btn-xs btn-warning" href="?%s">%s</a> ' % (query_dict.urlencode(), text)
                else:
                    query_dict[self.option] = val
                    yield '<a class="btn btn-xs btn-warning btn-outline" href="?%s">%s</a> ' % (query_dict.urlencode(), text)
            else:
                multi_val_list = query_dict.getlist(self.option)
                # < QueryDict: {'server_status_id': ['3']} >
                # server_status_id
                # multi_val_list = ['3']
                if str(val) in origin_value_list:
                    # 已经选，把自己去掉
                    multi_val_list.remove(str(val))
                    query_dict.setlist(self.option, multi_val_list)
                    yield '<a class="btn btn-xs btn-warning" href="?%s">%s</a>' % (query_dict.urlencode(), text)
                else:
                    multi_val_list.append(val)
                    query_dict.setlist(self.option, multi_val_list)
                    yield '<a class="btn btn-xs btn-warning btn-outline" href="?%s">%s</a>' % (query_dict.urlencode(), text)

        yield '</div>'


