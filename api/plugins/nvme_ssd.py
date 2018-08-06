from cmdb import models
from django.db import transaction
import datetime
from django.conf import settings

class Nvme_ssd(object):
    def __init__(self,server_obj,info,u_obj=None):
        self.server_obj = server_obj
        self.disk_dict = info
        self.u_obj = u_obj
    def process(self):
        new_ssd_info_dict = self.disk_dict['data']
        """
        {
            '/dev/nvme0n1': 
                {'model': 'P34MMM-03T2H-ST', 'format': '512   B +  0 B', 'usage': '3.20  TB /   3.20  TB', 'namespace': '1', 'node': '/dev/nvme0n1', 'fw_rev': 'OATMA106', 'sn': '600032A310NN0037'},
            '/dev/nvme0n2': 
                {'model': 'P34MMM-03T2H-ST', 'format': '512   B +  0 B', 'usage': '3.20  TB /   3.20  TB', 'namespace': '1', 'node': '/dev/nvme0n1', 'fw_rev': 'OATMA106', 'sn': '600032A310NN0037'},
        },"""
        new_ssd_info_list = self.server_obj.nvme_ssd.all()
        """
        [
            obj,
            obj,
            obj,
        ]
        """
        new_ssd_set = set(new_ssd_info_dict.keys())
        old_ssd_set = {obj.node for obj in new_ssd_info_list}
        # add_slot_list = new_disk_slot_set - old_disk_slot_set
        add_ssd_list = new_ssd_set.difference(old_ssd_set)
        del_ssd_list = old_ssd_set.difference(new_ssd_set)
        update_ssd_list = old_ssd_set.intersection(new_ssd_set)

        # add_record_list = []
        # 增加 [2,5]
        if add_ssd_list:
            for node in add_ssd_list:
                value = new_ssd_info_dict[node]
                self.add_disk(value)
        # for slot in add_slot_list:
        #     value = new_disk_info_dict[slot]
        #     tmp = "添加硬盘slot{0}至{1}".format(slot,self.server_obj.hostname)
        #     add_record_list.append(tmp)
        #     value['server_obj'] = self.server_obj
        #     models.Disk.objects.create(**value)
        # 删除 [4,6]
        if del_ssd_list:
            self.del_disk(del_ssd_list)
        # models.Disk.objects.filter(server_obj=self.server_obj, slot__in=del_slot_list).delete()

        # 更新 [7,8]
        if update_ssd_list:
            for node in update_ssd_list:
                value = new_ssd_info_dict[node]
                self.update_disk(value)
        # for slot in update_slot_list:
        #     value = new_disk_info_dict[
        #         slot]  # {'slot': '0', 'pd_type': 'SAS', 'capacity': '279.396', 'model': 'SEAGATE ST300MM0006     LS08S0K2B5NV'}
        #     obj = models.Disk.objects.filter(server_obj=self.server_obj, slot=slot).first()
        #     for k, new_val in value.items():
        #         old_val = getattr(obj, k)
        #         if old_val != new_val:
        #             setattr(obj, k, new_val)
        #     obj.save()
    def add_smart_log(self,smart_log,ssd_obj):
        smart_log['ssd_obj'] = ssd_obj
        # 删除数据库中此SSD 1天前的smart_log
        limit_time = datetime.datetime.now() - datetime.timedelta(days=settings.SMART_LOG_LIMIT_TIME)
        models.Smart_log.objects.filter(ssd_obj=ssd_obj,log_date__lt=limit_time).delete()
        '''
        添加本次提交的smart_log至数据库，因为smart_log上报时字段不固定，
        要去掉数据库中没有的字段，这里list(smart_log.keys)是因为字典类型
        在迭代时做del或者pop等操作会报错，转换为list则不会
        '''
        for k in list(smart_log.keys()):
            if not getattr(models.Smart_log,k,None):
                smart_log.pop(k)
        models.Smart_log.objects.create(**smart_log)

    def add_disk(self,val_dict):
        try:
            with transaction.atomic():
                record = "添加SSD:{0}至{1}".format(val_dict['node'],self.server_obj.hostname)
                val_dict['server_obj'] = self.server_obj
                smart_log = val_dict.pop('smart_log')
                ssd_obj = models.Nvme_ssd.objects.create(**val_dict)
                models.ServerRecord.objects.create(server_obj=self.server_obj,
                                                   content=record,
                                                   creator=self.u_obj)
                # 添加一条smart_log
                if smart_log:
                    self.add_smart_log(smart_log, ssd_obj)

        except Exception as e:
            print(e)

    def del_disk(self,del_ssd_list):
        try:
            with transaction.atomic():
                record = "删除SSD:{0}从{1}".format(del_ssd_list,self.server_obj.hostname)
                models.Nvme_ssd.objects.filter(server_obj=self.server_obj,
                                           node__in=del_ssd_list).delete()

                models.ServerRecord.objects.create(server_obj=self.server_obj,
                                                   content=record,
                                                   creator=self.u_obj)
        except Exception as e:
            print(e)

    def update_disk(self,val_dict):
        # {'slot': '0', 'pd_type': 'SAS', 'capacity': '279.396', 'model': 'SEAGATE ST300MM0006     LS08S0K2B5NV'}
        obj = models.Nvme_ssd.objects.filter(server_obj=self.server_obj,
                                         node=val_dict['node']).first()
        smart_log = val_dict.pop('smart_log')
        # 添加smart_log
        if smart_log:
            self.add_smart_log(smart_log, obj)

        record_list = []
        try:
            with transaction.atomic():
                for k, new_val in val_dict.items():
                    old_val = getattr(obj, k)
                    if type(old_val) == float or type(old_val) == int :
                        old_val = str(old_val)

                    if old_val != new_val:
                        record = "[%s]:[%s]的[%s]由[%s]变更为[%s]" % (self.server_obj.hostname,
                                                                 val_dict['node'],k, old_val,
                                                                 new_val)
                        record_list.append(record)
                        setattr(obj, k, new_val)
                obj.save()
                if record_list:
                    models.ServerRecord.objects.create(server_obj=self.server_obj,
                                                       content=';'.join(record_list),
                                                       creator=self.u_obj)
        except Exception as e:
            print(e)