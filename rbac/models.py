from django.db import models

# Create your models here.
class UserProfile(models.Model):
    """
    用户信息，运维管理员和业务负责人 50人
    """
    name = models.CharField('姓名', max_length=32)
    email = models.EmailField('邮箱')
    phone = models.CharField('座机', max_length=32)
    mobile = models.CharField('手机', max_length=32)
    roles = models.ManyToManyField(verbose_name='具有的所有角色', to="Role", blank=True)
    is_admin = models.BooleanField(default=False)
    class Meta:
        verbose_name_plural = "用户表"

    def __str__(self):
        return self.name

class AdminInfo(models.Model):
    """
    用户登录： 10
    """
    user = models.OneToOneField("UserProfile")
    username = models.CharField('用户名', max_length=32)
    password = models.CharField('密码', max_length=32)

class Role(models.Model):

    """
    role
    ID   名称
     1   组A
     2   组B
     3   组C
    role to user
    roleID    userID
     1       1
     1       2
     2       2
     2       3
     3       4
    """
    title = models.CharField(verbose_name='角色名',max_length=32, unique=True)
    permissions = models.ManyToManyField(verbose_name='具有的所有权限', to='Permission', blank=True)

    class Meta:
        verbose_name_plural = "用户组表"

    def __str__(self):
        return self.title


class Permission(models.Model):
    """
    权限表
    """
    title = models.CharField(verbose_name='标题',max_length=32)
    url = models.CharField(verbose_name="含正则URL",max_length=64)

    # menu_gp = models.ForeignKey(verbose_name='默认选中的组内权限ID',to='Permission',null=True,blank=True,related_name='x1')
    #
    # code = models.CharField(verbose_name="代码",max_length=16)
    # group = models.ForeignKey(verbose_name='所属组',to="Group")

    class Meta:
        verbose_name_plural = "权限表"

    def __str__(self):
        return self.title