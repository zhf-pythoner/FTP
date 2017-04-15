#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __Author__: Zhaohongfei


import socketserver
import json
import os
import common
import shutil
import time
import base

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

class FtpServer(socketserver.BaseRequestHandler):
    '''
    ftp 服务端类
    '''

    def setup(self):
        self.log_template = "user:%s-action:%s-filename:%s-resualt:%s-msg:%s"
        self.configinfo = base.init()
        self.data_path = os.path.join(BASE_PATH,self.configinfo['data'])
        self.log_path = os.path.join(BASE_PATH,self.configinfo['logs'])
        self.quota_size = int(self.configinfo['quota_size'])

    def handle(self):
        self.auth()
        while True:
            try:
                point = self.request.recv(1024)     #接收客户端发送的操作指针 action,filename,filesize,md5
                if not point:break
                point = json.loads(point.decode())       #将json转换为字典
                if point['action'] == 'exit':       #客户端断开主动链接
                    break
                if hasattr(self,point['action']):
                    func = getattr(self,point['action'])
                    func(point)
                else:
                    print('没有此action:%s' % point['action'])
            except Exception as e:
                self.__write_log(self.client_address[0],"客户端异常断开",'error')
    def auth(self):
        while True:
            msg = '请输入用户密码: '
            self.request.send(msg.encode())
            logininfo = self.request.recv(1024)
            logininfo = json.loads(logininfo.decode())
            userinfo = self.configinfo['userinfo']
            if not userinfo: break
            if logininfo[0] in userinfo:     #如果用户存在
                if common.encrypt(logininfo[1]) == userinfo[logininfo[0]]['password']:   #比较用户的密码和配置中用户的密码
                    msg = "400"     #验证通过
                    log_msg = self.log_template % (logininfo[0], 'login', ' ', "success", "登录成功")
                    self.__write_log(log_msg, 'info')

                else:
                    msg = "401"         #密码错误
                    log_msg = self.log_template % (logininfo[0], 'login', '', "faild", "登录失败,密码错误")
                    self.__write_log(log_msg, 'warning')
            else:
                msg = "402"         #用户不存在
                log_msg = self.log_template % (logininfo[0], 'login', '', "faild", "登录失败,未知用户")
                self.__write_log(log_msg, 'error')

            self.request.send(msg.encode())
            client_ack = self.request.recv(1024).decode()
            if client_ack == "300":
                break
            else:
                continue

    def __get_total_size(self,user):
        size = 0
        data_dir = os.path.join(self.data_path,user)
        for root, dirs, files in os.walk(data_dir):
            size += sum([os.path.getsize(os.path.join(root, name)) for name in files])
        return size

    def __write_log(self,message,level):
        """
        记录用户日志
        :param message:
        :return:
        """
        logger_obj = common.credit_logger(self.log_path)
        func = getattr(logger_obj,level)
        func(message)


    @staticmethod
    def add_user():
        configinfo = base.init()
        userdb =  os.path.join(BASE_PATH,configinfo['userdb'])
        data_path = os.path.join(BASE_PATH,configinfo['data'])
        username = input('请输入用户名: ')
        passwd = input('请输入密码: ')
        fp = open(userdb, 'a+')
        fp.write("%s:%s"  %(username,common.encrypt(passwd)) + '\n')      #写入密码文件
        fp.close()
        user_file = os.path.join(data_path,username)    #用户数据目录
        os.mkdir(user_file)   #创建目录

        print('用户%s添加成功' % username)

    def put(self,arg):
        '''
        用户上传方法
        :param arg: 客户端post的文件指针
        :return:
        '''
        filename = arg['filename']
        filesize = arg['filesize']
        filemd5 = arg['md5']
        file_target_path = arg['target_path']      #要上传的目标路径
        user = arg['user']

        #用户空间配额判断
        if 'quota_size' in self.configinfo['userinfo'][user]:    #如果用户有自定义quota,自定义生效
            quota_size = self.configinfo['userinfo'][user]['quota_size']
        else:                                     #否则使用默认配置
            quota_size = self.quota_size

        available_space = int(quota_size) * 1024 * 1024 - self.__get_total_size(user)    #可用空间
        if available_space > filesize:

            # 开始判断客户端是否要求重命名
            abs_file_target_path = os.path.join(self.data_path,user,file_target_path)   #目标地址的绝对路径
            if os.path.exists(abs_file_target_path):    #绝对路径存在,说明客户端提供的是目标路径,不需要对文件重命名
                if os.path.isfile(abs_file_target_path): #目标路径是一个文件,这个文件存在,说明上传的文件冲突
                    self.request.send(bytes("208|:%s" % file_target_path, encoding='utf-8'))  # 文件存在,并发送传送指针
                    return None  # 中断运行
                else:
                    tmp_filename = "%s_%s.tmp" %(filename,filemd5)
                    tmp_file = os.path.join(abs_file_target_path,tmp_filename)    #拼接临时文件的绝对路径
                    file = os.path.join(abs_file_target_path,filename)          #实际的文件绝对路径

            else:       #目标地址不存在,客户端可能需要重命名

                #判断目标路径的上一级目录的绝对路径是否存在
                upper_abs_target_path = os.path.dirname(abs_file_target_path)   #上一级目录的绝对路径
                if os.path.exists(upper_abs_target_path):    #存在,说明最后一个目录名为新文件名
                    tmp_filename = "%s_%s.tmp" %(os.path.basename(abs_file_target_path),filemd5)   #拼接临时文件名
                    tmp_file = os.path.join(upper_abs_target_path,tmp_filename)  #拼接临时文件的绝对路径
                    file = os.path.join(upper_abs_target_path,os.path.basename(abs_file_target_path))  #实际文件绝对路径
                else:   #不存在,说明,客户端提供的路径不存在
                    msg = self.log_template % (arg['user'], arg['action'], file, "faild","路径不存在:%s" %os.path.dirname(file_target_path))
                    self.__write_log(msg, "warning")
                    self.request.send(bytes("204|:%s" % os.path.dirname(file_target_path),encoding='utf-8'))
                    return None    #中断put方法

            #判断目标文件是否存在
            if os.path.exists(file):      #存在
                msg = self.log_template % (arg['user'], arg['action'], file, "faild","文件已存在:%s" % os.path.basename(file))
                self.__write_log(msg, "warning")
                self.request.send(bytes("208|:%s" % os.path.basename(file), encoding='utf-8'))  # 文件存在,并发送传送指针
                return None  # 中断运行
            else:       #不存在
                #是否断点续传判断
                if os.path.exists(tmp_file):            #临时文件存在,让客户端判断是否断点续传
                    self.request.send(bytes('211|%s文件已存在' % filename,encoding='utf-8'))
                    client_ack = self.request.recv(1024).decode()
                    if client_ack == 'y':       #客户端要求断点续传
                        file_open_type = 'ab'  # 文件打开方式改为追加a
                        seek = int(os.stat(tmp_file).st_size)  #取出了临时文件大小
                        self.request.send(bytes("200|%s" % seek, encoding='utf-8'))  # 服务端ok,并发送存在的文件大小
                    elif client_ack == 'n':    #客户端要求重新上传
                        seek = 0
                        file_open_type = 'wb'  # 文件打开方式
                        self.request.send(bytes("200|%s" % seek, encoding='utf-8'))  # 服务端ok,并发送传送指针
                else:   #临时文件不存在
                    seek = 0
                    file_open_type = 'wb'  # 文件打开方式
                    self.request.send(bytes("200|%s" % seek, encoding='utf-8'))  # 服务端ok,并发送传送指针

            #开始接收数据
            recv_size = seek
            t_start = time.time()
            fw = open(tmp_file,file_open_type)
            while int(recv_size) < filesize:
                data = self.request.recv(4096)
                if not data:break               #最后收到空消息,表示客户端断开连接
                fw.write(data)
                recv_size += len(data)
            fw.close()
            t_cost = time.time() - t_start
            newmd5 = common.md5sum(tmp_file)       #md5校验
            if newmd5 == filemd5:
                msg = self.log_template % (arg['user'],arg['action'],file,"success",'上传成功')
                self.__write_log(msg, "info")
                shutil.move(tmp_file,file)    #将临时文件重命名为实际文件
                self.request.send(bytes("201|耗时:%s" % t_cost,encoding='utf-8'))       #201表示上传成功
            else:
                msg = self.log_template % (arg['user'],arg['action'],file,'faild','md5校验不一致')
                self.__write_log(msg, "error")
                self.request.send(bytes("202|md5不一致!服务端md5:%s" %newmd5,encoding='utf-8'))       #202表示上传失败

        else:
            msg = self.log_template  % (arg['user'], arg['action'], file,'faild',"超过空间配额")
            self.__write_log(msg, "error")
            self.request.send(bytes("209|可用空间:%sM" % str(available_space/1024/1024),encoding='utf-8'))  # 用户空间不足

    def get(self,arg):
        '''
        用户下载的方法
        :param arg: 客户端post的文件指针
        :return:
        '''
        file = os.path.join(self.data_path,arg['user'],arg['file'])   #拼接文件的绝对路径
        if os.path.exists(file):
            filename = os.path.basename(file)
            filesize = os.stat(file).st_size
            md5 = common.md5sum(file)
            server_response = {                  #服务端回应的文件指针内容
                'filename': filename,
                'filesize': filesize,
                'md5': md5,
            }
            self.request.send(json.dumps(server_response).encode())
            client_ack = self.request.recv(1024).decode().split('|')  # 接收客户端的状态
            if client_ack[0] == 'ok':  # 客户端准备就绪
                send_size = int(client_ack[1])
                fp = open(file, 'rb')
                fp.seek(send_size)
                while send_size < filesize:
                    data = fp.read(4096)
                    self.request.send(data)
                    send_size += len(data)
                fp.close()
                msg = self.log_template % (arg['user'], arg['action'], file,'success','文件发送至客户端')
                self.__write_log(msg, "info")
            else:
                msg = self.log_template % (arg['user'], arg['action'], file,'faild', "客户端问题")
                self.__write_log(msg, "warning")
                return None  #客户端有问题,中断方法
        else:
            msg = self.log_template % (arg['user'], arg['action'], file, 'faild',"文件不存在:%s" %file )
            self.__write_log(msg, "error")
            self.request.send('404'.encode())    #服务端没有该文件

    def ls(self,arg):
        res = {}        #字典用于存放文件名或目录名 以及类别
        path = os.path.join(self.data_path,arg['user'],arg['path'])
        if os.path.isfile(path):
            res = {arg:"文件"}
        else:
            file_list = os.listdir(path)
            for i in file_list:
                if os.path.isdir(os.path.join(path,i)):  #判断是否是目录
                    res[i] = '(目录)'
                elif os.path.isfile(os.path.join(path,i)):     #判断是否是文件
                    res[i] = '(文件)'
        self.request.send(json.dumps(res).encode())    #将结果发送至客户端

    def cd(self,arg):
        '''
        切换目录方法
        :param arg: 切换的路径
        :return:
        '''
        target_path = arg['target_path']
        user = arg['user']
        path = os.path.join(self.data_path,user,target_path)
        if os.path.exists(path):  #路径存在
            if os.path.isdir(path):      #切换的路径是目录
                self.request.send('203'.encode())    #切换成功
            else:
                self.request.send('205'.encode())    #目标是文件,无法切换进去
        else:
            self.request.send('404'.encode())    #切换失败,目录不存在

    def rm(self,arg):
        '''
        客户端删除文件方法
        :param arg: 删除的文件
        :return:
        '''
        file = os.path.join(self.data_path,arg['user'],arg['file'])
        if os.path.exists(file):        #如果删除的对象存在
            try:
                if os.path.isfile(file):   #如果删除的对象是文件,则直接删除
                    os.remove(file)
                elif os.path.isdir(file):       #如果删除的对象是目录,则先删除目录里的文件,再删除目录
                    filelist = os.listdir(file)
                    for i in filelist:
                        os.remove(os.path.join(file,i))
                    os.rmdir(file)
            except Exception as e:
                pass
            finally:
                if not os.path.exists(file):  #上述处理完之后,如果对象不存在,则表示删除成功
                    msg = self.log_template % (arg['user'], arg['action'], file, "success", "删除成功")
                    self.__write_log(msg, "info")
                    self.request.send('206'.encode())
                else:
                    msg = self.log_template % (arg['user'], arg['action'], file, "faild", "删除失败")
                    self.__write_log(msg, "warning")
                    self.request.send('207'.encode())
        else:
            msg = self.log_template % (arg['user'], arg['action'], file, "faild", "目标不存在")
            self.__write_log(msg, "warning")
            self.request.send('404'.encode())

    def mkdir(self,arg):
        '''
        客户端创建目录的方法
        :param arg: 目录路径
        :return:
        '''
        path = os.path.join(self.data_path,arg['user'],arg['path'])
        if os.path.exists(path):
            msg = self.log_template % (arg['user'], arg['action'], path, "faild", "目录已存在")
            self.__write_log( msg, "warning")
            self.request.send('208'.encode())   #要创建的目录已存在

        else:
            os.makedirs(path)             #创建目录
            msg = self.log_template % (arg['user'], arg['action'], path, "success", "创建成功")
            self.__write_log( msg, "info")
            self.request.send('210'.encode())  #目录创建成功


    def mv(self,arg):
        '''
        客户端移动文件或更名的方法
        :param arg: 文件指针
        :return:
        '''
        source = os.path.join(self.data_path,arg['user'],arg['source'])
        target = os.path.join(self.data_path,arg['user'],arg['target'])
        if os.path.exists(source):          #源文件存在
            if os.path.exists(target):
                shutil.move(source,target)
                msg = self.log_template % (arg['user'], arg['action'], source, "success", "移动成功")
                self.__write_log(msg, "info")
                self.request.send('406'.encode())   #移动成功
            elif os.path.dirname(source) == os.path.dirname(target):   #如果原文件和目标在同一个目录下
                shutil.move(source, target)
                msg = self.log_template % (arg['user'], arg['action'], source, "success", "重命名成功")
                self.__write_log(msg, "info")
                self.request.send('406'.encode())  # 重命名成功

            else:
                msg = self.log_template % (arg['user'], arg['action'], source, "faild", "目标目录不存在")
                self.__write_log(msg, "warning")
                self.request.send('404'.encode())  # 目标不存在

        else:
            msg = self.log_template % (arg['user'], arg['action'], source, "success", "源文件不存在")
            self.__write_log(msg, "warning")
            self.request.send('404'.encode())   #源文件不存在



