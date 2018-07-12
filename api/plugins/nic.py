from cmdb import models
from django.db import transaction

class Nic(object):
    def __init__(self,server_obj,info,u_obj=None):
        self.server_obj = server_obj
        self.nic_dict = info
        self.u_obj = u_obj
    def process(self):
        new_nic_info_dict = self.nic_dict['data']
        """
        {
            'enp3s0': 
                {'up': True, 'netmask': '255.255.254.0', 'ipaddrs': '10.0.2.17', 'hwaddr': '40:8d:5c:64:6c:3e'},
            'enp3s1':    
                {'up': True, 'netmask': '255.255.254.0', 'ipaddrs': '10.0.2.18', 'hwaddr': '40:8d:5c:64:6c:3e'},
        
        }"""
        new_nic_info_list = self.server_obj.nic.all()
        """
        [
            obj,
            obj,
            obj,
        ]
        """
        new_nic_set = set(new_nic_info_dict.keys())
        old_nic_set = {obj.name for obj in new_nic_info_list}
        # add_slot_list = new_disk_slot_set - old_disk_slot_set
        add_nic_list = new_nic_set.difference(old_nic_set)
        del_nic_list = old_nic_set.difference(new_nic_set)
        update_nic_list = old_nic_set.intersection(new_nic_set)

        # add_record_list = []
        # 增加 [2,5]
        if add_nic_list:
            for name in add_nic_list:
                value = new_nic_info_dict[name]
                value['name'] = name
                self.add_nic(value)
        # for slot in add_slot_list:
        #     value = new_disk_info_dict[slot]
        #     tmp = "添加硬盘slot{0}至{1}".format(slot,self.server_obj.hostname)
        #     add_record_list.append(tmp)
        #     value['server_obj'] = self.server_obj
        #     models.Disk.objects.create(**value)
        # 删除 [4,6]
        if del_nic_list:
            self.del_nic(del_nic_list)
        # models.Disk.objects.filter(server_obj=self.server_obj, slot__in=del_slot_list).delete()

        # 更新 [7,8]
        if update_nic_list:
            for name in update_nic_list:
                value = new_nic_info_dict[name]
                value['name'] = name
                self.update_nic(value)
        # for slot in update_slot_list:
        #     value = new_disk_info_dict[
        #         slot]  # {'slot': '0', 'pd_type': 'SAS', 'capacity': '279.396', 'model': 'SEAGATE ST300MM0006     LS08S0K2B5NV'}
        #     obj = models.Disk.objects.filter(server_obj=self.server_obj, slot=slot).first()
        #     for k, new_val in value.items():
        #         old_val = getattr(obj, k)
        #         if old_val != new_val:
        #             setattr(obj, k, new_val)
        #     obj.save()

    def add_nic(self,val_dict):
        try:
            with transaction.atomic():
                record = "添加网卡:{0}至{1}".format(val_dict['name'],self.server_obj.hostname)
                val_dict['server_obj'] = self.server_obj
                models.NIC.objects.create(**val_dict)
                models.ServerRecord.objects.create(server_obj=self.server_obj,
                                                   content=record,
                                                   creator=self.u_obj)
        except Exception as e:
            print(e)

    def del_nic(self,del_nic_list):
        try:
            with transaction.atomic():
                record = "删除网卡:{0}从{1}".format(del_nic_list,self.server_obj.hostname)
                models.NIC.objects.filter(server_obj=self.server_obj,
                                           name__in=del_nic_list).delete()

                models.ServerRecord.objects.create(server_obj=self.server_obj,
                                                   content=record,
                                                   creator=self.u_obj)
        except Exception as e:
            print(e)

    def update_nic(self,val_dict):
        # {'slot': '0', 'pd_type': 'SAS', 'capacity': '279.396', 'model': 'SEAGATE ST300MM0006     LS08S0K2B5NV'}
        obj = models.NIC.objects.filter(server_obj=self.server_obj,
                                         name=val_dict['name']).first()
        record_list = []
        try:
            with transaction.atomic():
                for k, new_val in val_dict.items():
                    old_val = getattr(obj, k)
                    if type(old_val) == float or type(old_val) == int :
                        old_val = str(old_val)

                    if old_val != new_val:
                        record = "[%s]:[%s]的[%s]由[%s]变更为[%s]" % (self.server_obj.hostname,
                                                                 val_dict['name'],k, old_val,
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