# /usr/bin/env python
# -*- coding:utf-8 -*-
# Author  : wuyifei
# Data    : 9/20/18 3:53 PM
# FileName: remote_client.py

# import paramiko
#
# t = paramiko.Transport(('172.17.0.5',22))
# t.connect(username='root',
#           password='test')
# sftp = paramiko.SFTPClient.from_transport(t)
# sftp.put('/home/wuyifei/pro06/dera_ops/utils/bs64.py','/tmp/bs64.py')
#
# t.close()

import os
from paramiko import SSHClient,AutoAddPolicy,AuthenticationException

class ConnectError(Exception):
    """
    连接错误
    """
    pass

class RemoteExecError(Exception):
    """
    远程执行命令失败
    """
    pass

class SCPError(Exception):
    """
    远程下发文件错误
    """
    pass

class Remote(object):
    def __init__(self,host,username,password=None,port=22,key_filename=None):
        self.host = host
        self.username = username
        self.password = password
        self.port =port
        self.key_filename = key_filename
        self._ssh = None

    def _connect(self):
        self._ssh = SSHClient()
        self._ssh.set_missing_host_key_policy(AutoAddPolicy())
        try:
            if self.key_filename:
                pass
            else:
                self._ssh.connect(self.host,username=self.username,
                                  password=self.password,port=self.port)

        except AuthenticationException:
            self._ssh = None
            raise ConnectionError('连接失败,请确认用户名、密码、端口是否正确')
        except Exception as e:
            self._ssh = None
            raise ConnectionError('连接时出现意外错误：%s'%e)

    def get_ssh(self):
        if not self._ssh:
            self._connect()
        return self._ssh

    def ssh(self,cmd,root_password=None,get_pty=False,super=False):
        cmd = self._prepare_cmd(cmd,root_password,super)
        stdout = self._exec(cmd,get_pty)
        return stdout

    def _prepare_cmd(self,cmd,root_password=None,super=False):
        if self.username != "root" :
            if root_password:   # 非root且无sudo权限用户
                cmd = "echo '{}'|su - root -c '{}'".format(root_password,cmd)
            elif super:   # 非root有sudo权限用户
                cmd = "echo '{}'|sudo -p '' -S su - root -c '{}'".format(self.password,cmd)
        return cmd

    def _exec(self,cmd,get_pty=False):
        channel = self.get_ssh().get_transport().open_session()
        if get_pty:
            channel.get_pty()
        channel.exec_command(cmd)
        stdout = channel.makefile('r',-1).readlines()
        stderr = channel.makefile_stderr('r',-1).readlines()
        ret_code = channel.recv_exit_status()
        if ret_code:
            msg = ''.join(stderr) if stderr else ''.join(stdout)
            raise RemoteExecError(msg)
        return stdout

    def scp(self,local_file,remote_path):
        if not os.path.exists(local_file):
            raise SCPError("Local %s isn`t exists!"%local_file)
        if not os.path.isfile(local_file):
            raise SCPError("%s is not a file!"%local_file)
        sftp = self.get_ssh().open_sftp()
        try:
            sftp.put(local_file,remote_path)
        except Exception as e:
            raise SCPError(e)


# if __name__ == "__main__":
    # rc = Remote("10.0.2.17","dera","Dera1234")
    # rc.scp('/home/wuyifei/pro06/dera_ops/utils/kaisa_jiemi.py','/tmp/kaisa_jiemi.py')
    # print(rc.ssh('systemctl restart nginx',root_password="P@44w.rD",get_pty=True))
