from cmdb import models
import datetime
import traceback

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
        '''
        tmp = {
            'hostname': 'SUZWYS5133', 
            'cpu_physical_count': None, 
            'cpu_model': '', 
            'os_platform': 'Windows-7-6.1.7601-SP1', 
            'os_version': '6.1.7601', 
            'cpu_count': None, 
            'manage_ip': '10.0.6.85', 
            'client_version': 'v1.1.6'
        }
        '''
        # 服务器数据更新
        # tmp.pop('hostname')
        record_list = []
        # 导入模块
        from django.db import transaction

        try:
            # 可回滚
            with transaction.atomic():
                for k, new_val in tmp.items():
                    old_val = getattr(self.server_obj, k)

                    if type(old_val) == float or type(old_val) == int :
                        old_val = str(old_val)

                    if old_val != new_val:
                        record = "[%s]的[%s]由[%s]变更为[%s]" % (self.server_obj.hostname, k, old_val, new_val)
                        record_list.append(record)
                        setattr(self.server_obj, k, new_val)
                    if not self.user_obj:   #如果不是用户主动修改,则更新主机状态和日期
                        self.server_obj.server_status_id = 2
                        self.server_obj.latest_date = datetime.datetime.now()
                self.server_obj.save()
                if record_list:
                    models.ServerRecord.objects.create(server_obj=self.server_obj,creator=self.user_obj,
                                                       content=';\n'.join(record_list))
        except Exception as e:
            print(traceback.format_exc())



