from cmdb import models
from django.db import transaction


class Memory(object):
    def __init__(self, server_obj, info, u_obj=None):
        self.server_obj = server_obj
        self.mem_dict = info
        self.u_obj = u_obj

    def process(self):
        new_mem_info_dict = self.mem_dict['data']
        """
           {'data': 
                 'ChannelA-DIMM0': 
                     {'speed': 'Unknown', 'capacity': 0, 'sn': '[Empty]', 'slot': 'ChannelA-DIMM0', 'model': 'Unknown', 'manufacturer': '[Empty]'}, 
                 'ChannelA-DIMM1': 
                     {'speed': 'Unknown', 'capacity': 0, 'sn': '[Empty]', 'slot': 'ChannelA-DIMM1', 'model': 'Unknown', 'manufacturer': '[Empty]'}, 
                 'ChannelB-DIMM1': 
                     {'speed': '1600 MHz', 'capacity': 8192, 'sn': '78166EEA', 'slot': 'ChannelB-DIMM1', 'model': 'DDR3', 'manufacturer': 'Kingston'}}, 
            'status': True, 
            'msg': None},
        """
        db_mem_obj_list = self.server_obj.memory.all()
        """
        [
            obj,
            obj,
            obj,
        ]
        """
        new_mem_set = set(new_mem_info_dict.keys())
        old_mem_set = {obj.slot for obj in db_mem_obj_list}
        # add_slot_list = new_disk_slot_set - old_disk_slot_set
        add_mem_list = new_mem_set.difference(old_mem_set)
        del_mem_list = old_mem_set.difference(new_mem_set)
        update_mem_list = old_mem_set.intersection(new_mem_set)

        # add_record_list = []
        # 增加 [2,5]
        if add_mem_list:
            for slot in add_mem_list:
                value = new_mem_info_dict[slot]
                self.add_mem(value)
        # for slot in add_slot_list:
        #     value = new_disk_info_dict[slot]
        #     tmp = "添加硬盘slot{0}至{1}".format(slot,self.server_obj.hostname)
        #     add_record_list.append(tmp)
        #     value['server_obj'] = self.server_obj
        #     models.Disk.objects.create(**value)
        # 删除 [4,6]
        if del_mem_list:
            self.del_mem(del_mem_list)
        # models.Disk.objects.filter(server_obj=self.server_obj, slot__in=del_slot_list).delete()

        # 更新 [7,8]
        if update_mem_list:
            for slot in update_mem_list:
                value = new_mem_info_dict[slot]
                self.update_mem(value)
        # for slot in update_slot_list:
        #     value = new_disk_info_dict[
        #         slot]  # {'slot': '0', 'pd_type': 'SAS', 'capacity': '279.396', 'model': 'SEAGATE ST300MM0006     LS08S0K2B5NV'}
        #     obj = models.Disk.objects.filter(server_obj=self.server_obj, slot=slot).first()
        #     for k, new_val in value.items():
        #         old_val = getattr(obj, k)
        #         if old_val != new_val:
        #             setattr(obj, k, new_val)
        #     obj.save()

    def add_mem(self, val_dict):
        try:
            with transaction.atomic():
                record = "添加内存{0}至{1}".format(val_dict['slot'], self.server_obj.hostname)
                val_dict['server_obj'] = self.server_obj
                models.Memory.objects.create(**val_dict)
                models.ServerRecord.objects.create(server_obj=self.server_obj,
                                                   content=record,
                                                   creator=self.u_obj)
        except Exception as e:
            print(e)

    def del_mem(self, del_mem_list):
        try:
            with transaction.atomic():
                record = "删除内存:{0}从{1}".format(del_mem_list, self.server_obj.hostname)
                models.Memory.objects.filter(server_obj=self.server_obj,
                                          slot__in=del_mem_list).delete()

                models.ServerRecord.objects.create(server_obj=self.server_obj,
                                                   content=record,
                                                   creator=self.u_obj)
        except Exception as e:
            print(e)

    def update_mem(self, val_dict):
        # {'slot': '0', 'pd_type': 'SAS', 'capacity': '279.396', 'model': 'SEAGATE ST300MM0006     LS08S0K2B5NV'}
        obj = models.Memory.objects.filter(server_obj=self.server_obj,
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
                                                                 val_dict['slot'], k, old_val,
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