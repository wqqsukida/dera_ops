from django.db import models

# Create your models here.
from rbac import models  as rbac_model


class BusinessUnit(models.Model):
    """
    主机组(部门)
    """
    name = models.CharField(verbose_name='主机组名称', max_length=64, unique=True) # 销售，1,2
    roles = models.ManyToManyField(verbose_name="对应用户组",to=rbac_model.Role,blank=True) # 运维管理人员：2

    class Meta:
        verbose_name_plural = "主机组表"

    def __str__(self):
        return self.name

class Tag(models.Model):
    """
    资产标签
    """
    name = models.CharField('标签', max_length=32, unique=True)

    class Meta:
        verbose_name_plural = "标签表"

    def __str__(self):
        return self.name

class IDC(models.Model):
    """
    机房信息
    """
    name = models.CharField('机房', max_length=32)
    floor = models.IntegerField('楼层', default=1)

    class Meta:
        verbose_name_plural = "机房表"

    def __str__(self):
        return self.name



class Server(models.Model):
    """
    服务器信息
    """
    # asset = models.OneToOneField('Asset')


    idc = models.ForeignKey(IDC,null=True, blank=True)
    cabinet_num = models.CharField('机柜号', max_length=30, null=True, blank=True)
    cabinet_order = models.CharField('机柜中序号', max_length=30, null=True, blank=True)

    business_unit = models.ManyToManyField(to=BusinessUnit,null=True, blank=True)

    tags = models.ManyToManyField(Tag)


    server_status_choices = (
        (1, '上架'),
        (2, '在线'),
        (3, '离线'),
        (4, '下架'),
    )

    server_status_id = models.IntegerField(choices=server_status_choices, default=1)

    hostname = models.CharField(max_length=128, unique=True)
    sn = models.CharField('SN号', max_length=128, db_index=True)
    manufacturer = models.CharField(verbose_name='制造商', max_length=64, null=True, blank=True)
    model = models.CharField('型号', max_length=64, null=True, blank=True)

    manage_ip = models.GenericIPAddressField('管理IP', null=True, blank=True)

    os_platform = models.CharField('系统', max_length=16, null=True, blank=True)
    os_version = models.CharField('系统版本', max_length=128, null=True, blank=True)

    cpu_count = models.IntegerField('CPU个数', null=True, blank=True)
    cpu_physical_count = models.IntegerField('CPU物理个数', null=True, blank=True)
    cpu_model = models.CharField('CPU型号', max_length=128, null=True, blank=True)

    create_at = models.DateTimeField(auto_now_add=True, blank=True)

    latest_date = models.DateTimeField(null=True,blank=True)

    def run_task_count(self):
        return self.server_task.filter(status=5).count()

    class Meta:
        verbose_name_plural = "服务器表"

    def __str__(self):
        return self.hostname




class Disk(models.Model):
    """
    硬盘信息
    """
    slot = models.CharField('插槽位', max_length=8)
    model = models.CharField('磁盘型号', max_length=256)
    capacity = models.FloatField('磁盘容量GB')
    pd_type = models.CharField('磁盘类型', max_length=256)
    server_obj = models.ForeignKey('Server',related_name='disk')

    class Meta:
        verbose_name_plural = "硬盘表"

    def __str__(self):
        return self.slot

class Nvme_ssd(models.Model):
    """
    Nvme_ssd
    """
    node = models.CharField('',max_length=64)
    sn = models.CharField('SN号', max_length=128, db_index=True)
    model = models.CharField('SSD型号', max_length=256)
    namespace = models.CharField('', max_length=32)
    usage = models.CharField('使用情况', max_length=128)
    format = models.CharField('', max_length=128)
    fw_rev = models.CharField('', max_length=64)
    server_obj = models.ForeignKey('Server', related_name='nvme_ssd')

    class Meta:
        verbose_name_plural = "SSD表"

    def __str__(self):
        return self.node

class Smart_log(models.Model):
    """
    ssd smart_log
    """
    critical_warning = models.CharField(max_length=128, null=True)
    temperature = models.CharField(max_length=128, null=True)
    available_spare = models.CharField(max_length=128, null=True)
    available_spare_threshold = models.CharField(max_length=128, null=True)
    percentage_used = models.CharField(max_length=128, null=True)
    data_units_read = models.CharField(max_length=128, null=True)
    data_units_written = models.CharField(max_length=128, null=True)
    host_read_commands = models.CharField(max_length=128, null=True)
    host_write_commands = models.CharField(max_length=128, null=True)
    controller_busy_time = models.CharField(max_length=128, null=True)
    power_cycles = models.CharField(max_length=128, null=True)
    power_on_hours = models.CharField(max_length=128, null=True)
    unsafe_shutdowns = models.CharField(max_length=128, null=True)
    media_errors = models.CharField(max_length=128, null=True)
    num_err_log_entries = models.CharField(max_length=128, null=True)

    warning_temperature_time = models.CharField(max_length=128, null=True)
    critical_composite_temperature_time = models.CharField(max_length=128, null=True)

    temperature_sensor_1 = models.CharField(max_length=128, null=True)
    temperature_sensor_2 = models.CharField(max_length=128, null=True)
    temperature_sensor_3 = models.CharField(max_length=128, null=True)
    temperature_sensor_4 = models.CharField(max_length=128, null=True)

    thermal_management_t1_trans_count = models.CharField(max_length=128, null=True)
    thermal_management_t2_trans_count = models.CharField(max_length=128, null=True)

    thermal_management_t1_total_time = models.CharField(max_length=128, null=True)
    thermal_management_t2_total_time = models.CharField(max_length=128, null=True)

    ssd_obj = models.ForeignKey(to='Nvme_ssd',related_name='smart_log')
    log_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "SmartLog表"


class NIC(models.Model):
    """
    网卡信息
    """
    name = models.CharField('网卡名称', max_length=128)
    hwaddr = models.CharField('网卡mac地址', max_length=64)
    netmask = models.CharField(max_length=64)
    ipaddrs = models.CharField('ip地址', max_length=256)
    up = models.BooleanField(default=False)
    server_obj = models.ForeignKey('Server',related_name='nic')


    class Meta:
        verbose_name_plural = "网卡表"

    def __str__(self):
        return self.name


class Memory(models.Model):
    """
    内存信息
    """
    slot = models.CharField('插槽位', max_length=32)
    manufacturer = models.CharField('制造商', max_length=32, null=True, blank=True)
    model = models.CharField('型号', max_length=64)
    capacity = models.FloatField('容量', null=True, blank=True)
    sn = models.CharField('内存SN号', max_length=64, null=True, blank=True)
    speed = models.CharField('速度', max_length=16, null=True, blank=True)

    server_obj = models.ForeignKey('Server',related_name='memory')


    class Meta:
        verbose_name_plural = "内存表"

    def __str__(self):
        return self.slot


class ServerRecord(models.Model):
    """
    服务器变更记录,creator为空时，表示是资产汇报的数据。
    """
    server_obj = models.ForeignKey('Server', related_name='ar')
    content = models.TextField(null=True)
    creator = models.ForeignKey(to=rbac_model.UserProfile, null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "资产记录表"

    def __str__(self):
        return self.server_obj.hostname


class ErrorLog(models.Model):
    """
    错误日志,如：agent采集数据错误 或 运行错误
    """
    server_obj = models.ForeignKey('Server', null=True, blank=True)
    title = models.CharField(max_length=16)
    content = models.TextField()
    create_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "错误日志表"

    def __str__(self):
        return self.title

class SSDTask(models.Model):
    '''
    ssd任务状态表
    '''
    ssd_obj = models.ForeignKey(to='Nvme_ssd',related_name='task')
    content = models.TextField('任务内容')
    task_status_choices = (
        (1, '新建任务'),
        (2, '执行完成'),
        (3, '执行错误'),
        (4, '已删除'),
        (5, '推送执行中')
    )
    status = models.IntegerField('任务状态',choices=task_status_choices,default='1')
    create_date = models.DateTimeField('任务创建时间',auto_now_add=True)
    finished_date = models.DateTimeField('任务完成时间',null=True,blank=True)
    run_time = models.CharField('执行总计时间',max_length=32,null=True,blank=True)
    task_res = models.TextField('任务结果',null=True,blank=True)

class TaskMethod(models.Model):
    '''
    主机任务模板
    '''
    title = models.CharField('任务名称', max_length=32)
    content = models.TextField('任务内容')
    create_date = models.DateTimeField('任务创建时间', auto_now_add=True)

class ServerTask(models.Model):
    '''
    主机任务状态表
    '''
    server_obj = models.ForeignKey(to='Server',related_name='server_task')
    task = models.ForeignKey(to='TaskMethod')
    task_status_choices = (
        (1, '新任务'),
        (2, '执行完成'),
        (3, '执行失败'),
        (4, '执行暂停'),
        (5, '执行中')
    )
    status = models.IntegerField('任务状态',choices=task_status_choices,default='1')
    create_date = models.DateTimeField('任务创建时间',auto_now_add=True)
    finished_date = models.DateTimeField('任务完成时间',null=True,blank=True)
    run_time = models.CharField('执行总计时间',max_length=32,null=True,blank=True)
    task_res = models.TextField('任务结果',null=True,blank=True)
    secsession_obj = models.ForeignKey(to='Task_SecSession',null=True, blank=True)

class TaskSession(models.Model):
    '''
    主机任务会话表
    '''
    title = models.CharField('会话名称', max_length=32,null=False,blank=False)
    content = models.TextField('会话描述',null=True,blank=True)
    create_date = models.DateTimeField('会话创建时间', auto_now_add=True)
    role = models.ForeignKey(verbose_name='所属用户组',to=rbac_model.Role,null=True, blank=True)

    def ast(self):
        return self.nst() + self.fst() + self.est() + self.dst() + self.pst()

    def nst(self):
        count = 0
        server_tasks = self.task_secsession_set.values('servertask__id','servertask__status')
        for st in server_tasks:
            if st.get('servertask__status') == 1:
                count += 1
        return count

    def fst(self):
        count = 0
        server_tasks = self.task_secsession_set.values('servertask__id','servertask__status')
        for st in server_tasks:
            if st.get('servertask__status') == 2:
                count += 1
        return count

    def est(self):
        count = 0
        server_tasks = self.task_secsession_set.values('servertask__id','servertask__status')
        for st in server_tasks:
            if st.get('servertask__status') == 3:
                count += 1
        return count

    def dst(self):
        count = 0
        server_tasks = self.task_secsession_set.values('servertask__id','servertask__status')
        for st in server_tasks:
            if st.get('servertask__status') == 4:
                count += 1
        return count

    def pst(self):
        count = 0
        server_tasks = self.task_secsession_set.values('servertask__id','servertask__status')
        for st in server_tasks:
            if st.get('servertask__status') == 5:
                count += 1
        return count

class Task_SecSession(models.Model):
    '''
    主机子任务会话表
    '''
    title = models.CharField('子会话名称', max_length=32,null=False,blank=False)
    server_obj = models.ManyToManyField(to='Server')
    task_obj = models.ManyToManyField(to='TaskMethod')
    content = models.TextField('子会话描述',null=True,blank=True)
    create_date = models.DateTimeField('子会话创建时间', auto_now_add=True)
    father_session = models.ForeignKey(to='TaskSession',null=True, blank=True)
    is_random = models.BooleanField('是否随机执行',default=False)

    def ast(self):
        return self.servertask_set.count()

    def nst(self):
        return self.servertask_set.filter(status=1).count()

    def fst(self):
        return self.servertask_set.filter(status=2).count()

    def est(self):
        return self.servertask_set.filter(status=3).count()

    def dst(self):
        return self.servertask_set.filter(status=4).count()

    def pst(self):
        return self.servertask_set.filter(status=5).count()