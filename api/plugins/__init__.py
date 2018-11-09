from django.conf import settings
from cmdb import models
import importlib
from .server import Server
import traceback

class PluginManger(object):

    def __init__(self):
        self.plugin_items = settings.PLUGIN_ITEMS
        self.basic_key = "basic"
        self.board_key = "board"

    def exec(self,server_dict):
        """

        :param server_dict:
        :return: 1,执行完全成功； 2, 局部失败；3，执行失败;4. 服务器不存在
        """
        ret = {'code': 1,'msg':{}}
        asset_type = server_dict.get('type')
        # hostname = server_dict[self.basic_key]['data']['hostname']
        # server_obj = models.Server.objects.filter(hostname=hostname).first()
        if asset_type == "create":
            # 不存在则添加主机
            tmp = {}
            tmp.update(server_dict[self.basic_key]['data'])
            tmp.update(server_dict[self.board_key]['data'])
            server_obj = models.Server.objects.create(**tmp)
        elif asset_type == 'update':
            hostname = server_dict['basic']['data']['hostname']
            server_obj = models.Server.objects.get(hostname=hostname)
            obj = Server(server_obj, server_dict[self.basic_key], server_dict[self.board_key])
            obj.process()
        elif asset_type == 'host_update':
            hostname = server_dict['cert']
            server_obj = models.Server.objects.get(hostname=hostname)
            obj = Server(server_obj, server_dict[self.basic_key], server_dict[self.board_key])
            obj.process()

        # 对比更新[硬盘，网卡，内存，可插拔的插件]
        for k,v in self.plugin_items.items():
            try:
                if server_dict[k]['status']:
                    module_path,cls_name = v.rsplit('.',maxsplit=1)

                    md = importlib.import_module(module_path)
                    cls = getattr(md,cls_name)
                    obj = cls(server_obj,server_dict[k])
                    obj.process()
                    # ret['msg'] = '执行完全成功!'
                else:
                    ret['code'] = 2
                    ret['msg'][k] = server_dict[k]['msg']
            except Exception as e:
                msg = traceback.format_exc()
                ret['code'] = 2
                ret['msg'] = msg
        return ret

