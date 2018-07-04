from cmdb import models
import datetime

class Server(object):

    def __init__(self,server_obj,basic_dict,board_dict):
        self.server_obj = server_obj
        self.basic_dict = basic_dict
        self.board_dict = board_dict
        self.user_obj = None

    def process(self,):
        # 更新server表
        tmp = {}
        tmp.update(self.basic_dict['data'])
        tmp.update(self.board_dict['data'])

        # 服务器数据更新
        tmp.pop('hostname')
        record_list = []
        # 导入模块
        from django.db import transaction

        try:
            # 可回滚
            with transaction.atomic():
                for k, new_val in tmp.items():
                    old_val = getattr(self.server_obj, k)
                    if old_val != new_val:
                        record = "[%s]的[%s]由[%s]变更为[%s]" % (self.server_obj.hostname, k, old_val, new_val)
                        record_list.append(record)
                        setattr(self.server_obj, k, new_val)

                self.server_obj.latest_date = datetime.datetime.now()
                self.server_obj.save()
                if record_list:
                    models.ServerRecord.objects.create(server_obj=self.server_obj,creator=self.user_obj,
                                                       content=';\n'.join(record_list))
        except Exception as e:
            print(e)



