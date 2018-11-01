from cmdb import models
from django.db import transaction

class Disk(object):
    def __init__(self,server_obj,info,u_obj=None):
        self.server_obj = server_obj
        self.disk_dict = info
        self.u_obj = u_obj
    def process(self):
        # 硬盘、网卡和内存
        new_disk_info_dict = self.disk_dict['data']
        """ 
        {
            '0': {'slot': '0', 'pd_type': 'SAS', 'capacity': '279.396', 'model': 'SEAGATE ST300MM0006     LS08S0K2B5NV'},
            '1': {'slot': '1', 'pd_type': 'SAS', 'capacity': '279.396', 'model': 'SEAGATE ST300MM0006     LS08S0K2B5AH'},
            '2': {'slot': '2', 'pd_type': 'SATA', 'capacity': '476.939', 'model': 'S1SZNSAFA01085L     Samsung SSD 850 PRO 512GB               EXM01B6Q'},
            '3': {'slot': '3', 'pd_type': 'SATA', 'capacity': '476.939', 'model': 'S1AXNSAF912433K     Samsung SSD 840 PRO Series              DXM06B0Q'},
            '4': {'slot': '4', 'pd_type': 'SATA', 'capacity': '476.939', 'model': 'S1AXNSAF303909M     Samsung SSD 840 PRO Series              DXM05B0Q'},
            '5': {'slot': '5', 'pd_type': 'SATA', 'capacity': '476.939', 'model': 'S1AXNSAFB00549A     Samsung SSD 840 PRO Series
        }"""
        new_disk_info_list = self.server_obj.disk.all()
        """
        [
            obj,
            obj,
            obj,
        ]
        """
        new_disk_slot_set = set(new_disk_info_dict.keys())
        old_disk_slot_set = {obj.slot for obj in new_disk_info_list}
        # add_slot_list = new_disk_slot_set - old_disk_slot_set
        add_slot_list = new_disk_slot_set.difference(old_disk_slot_set)
        del_slot_list = old_disk_slot_set.difference(new_disk_slot_set)
        update_slot_list = old_disk_slot_set.intersection(new_disk_slot_set)

        # add_record_list = []
        # 增加 [2,5]
        if add_slot_list:
            for slot in add_slot_list:
                value = new_disk_info_dict[slot]
                self.add_disk(value)
        # for slot in add_slot_list:
        #     value = new_disk_info_dict[slot]
        #     tmp = "添加硬盘slot{0}至{1}".format(slot,self.server_obj.hostname)
        #     add_record_list.append(tmp)
        #     value['server_obj'] = self.server_obj
        #     models.Disk.objects.create(**value)
        # 删除 [4,6]
        if del_slot_list:
            self.del_disk(del_slot_list)
        # models.Disk.objects.filter(server_obj=self.server_obj, slot__in=del_slot_list).delete()

        # 更新 [7,8]
        if update_slot_list:
            for slot in update_slot_list:
                value = new_disk_info_dict[slot]
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
                record = "添加硬盘slot{0}至{1}".format(val_dict['slot'],self.server_obj.hostname)
                val_dict['server_obj'] = self.server_obj
                models.Disk.objects.create(**val_dict)
                models.ServerRecord.objects.create(server_obj=self.server_obj,
                                                   content=record,
                                                   creator=self.u_obj)
        except Exception as e:
            print(e)

    def del_disk(self,del_slot_list):
        try:
            with transaction.atomic():
                record = "删除硬盘slot{0}从{1}".format(del_slot_list,self.server_obj.hostname)
                models.Disk.objects.filter(server_obj=self.server_obj,
                                           slot__in=del_slot_list).delete()

                models.ServerRecord.objects.create(server_obj=self.server_obj,
                                                   content=record,
                                                   creator=self.u_obj)
        except Exception as e:
            print(e)

    def update_disk(self,val_dict):
        # {'slot': '0', 'pd_type': 'SAS', 'capacity': '279.396', 'model': 'SEAGATE ST300MM0006     LS08S0K2B5NV'}
        obj = models.Disk.objects.filter(server_obj=self.server_obj,
                                         slot=val_dict['slot']).first()
        record_list = []
        try:
            with transaction.atomic():
                for k, new_val in val_dict.items():
                    old_val = getattr(obj, k)
                    # if type(old_val) == float or type(old_val) == int :
                    #     old_val = str(old_val)

                    if old_val != new_val:
                        record = "[%s]:[%s]的[%s]由[%s]变更为[%s]" % (self.server_obj.hostname,
                                                                 val_dict['slot'],k, old_val,
                                                                 new_val)
                        record_list.append(record)
                        setattr(obj, k, new_val)
                obj.save()
                if record_list:
                    models.ServerRecord.objects.create(server_obj=self.server_obj,
                                                       content=';\n'.join(record_list),
                                                       creator=self.u_obj)
        except Exception as e:
            print(e)