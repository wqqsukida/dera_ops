from cmdb import models
from django.db import transaction

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

    def add_disk(self,val_dict):
        try:
            with transaction.atomic():
                record = "添加SSD:{0}至{1}".format(val_dict['node'],self.server_obj.hostname)
                val_dict['server_obj'] = self.server_obj
                models.Nvme_ssd.objects.create(**val_dict)
                models.ServerRecord.objects.create(server_obj=self.server_obj,
                                                   content=record,
                                                   creator=self.u_obj)
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
        record_list = []
        try:
            with transaction.atomic():
                for k, new_val in val_dict.items():
                    old_val = getattr(obj, k)
                    if type(old_val) != str :
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