#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __Author__: Zhaohongfei

import socket
import json
import shutil
import os
import common
import re


class FtpClient:
    '''
    ftp 客户端类
    '''
    isLogin = None
    current_path = ""     #当前用户在服务端的目录
    def __init__(self):
        self.conn = socket.socket()
    def connect(self,arg):
        '''
        连接ftp
        :param args:
        :return:
        '''
        try:
            ip = arg[1]
            port = int(arg[2])
            self.conn.connect((ip,port))
            self.__login()
        except IndexError :
            print("请输入完整的ip和端口")
        except Exception as e:
            print(e)

    def __login(self):
        '''
        登录
        :return:
        '''
        while True:
            res = self.conn.recv(1024).decode()
            print(res)
            user = input(">>user: ")
            passwd = input(">>password: ")
            userinfo = json.dumps([user,passwd])
            self.conn.send(userinfo.encode())
            server_ack = self.conn.recv(1024).decode()
            if server_ack == "400":
                self.isLogin = user
                self.conn.send('300'.encode())
                common.code_parsing(server_ack)
                break
            else:
                common.code_parsing(server_ack)
                self.conn.send('403'.encode())

    def session_judge(func):
        '''
        判断用户登录的装饰器
        :return:
        '''
        def inner(self,arg):
            if not self.isLogin:
                print("连接ftp服务器")
            else:
                return func(self,arg)
        return inner

    def check_file(func):
        def inner(self,arg):
            if len(arg) == 2:
                if arg[0] == 'put':
                    arg.append(self.current_path)    #将当前用户在服务器切换的目录加到路径中
                elif arg[0] == 'get':
                    arg[1] = os.path.join(self.current_path, arg[1])   #服务端的相对路径
                    arg.append('./')            #下载到本地的目的路径
                elif arg[0] == 'rm':
                    arg[1] = os.path.join(self.current_path,arg[1])
            elif len(arg) == 3:
                if arg[0] == 'put':
                    arg.append(os.path.join(self.current_path,arg[2]))    #拼接当前路径和用户输入要上传的路径
                elif arg[0] == 'get':
                    arg[1]=os.path.join(self.current_path, arg[1])
            elif len(arg) < 2:
                print("请输入正确的文件路径")
            return func(self, arg)
        return inner

    @session_judge
    @check_file
    def put(self,arg):
        '''
        上传文件
        :param arg: 要上传的文件
        :return:
        '''

        local_file = arg[1]        #要上传的文件(绝对路径)
        file_target_path = arg[2]       #上传到服务端的路径,默认为当前目录
        if os.path.exists(local_file):          #判断文件是否存在
            filename = os.path.basename(local_file)
            filesize = os.stat(local_file).st_size
            md5 = common.md5sum(local_file)
            point = {
                'action':arg[0],
                'filename':filename,
                'filesize':filesize,
                'md5':md5,
                'target_path':file_target_path,
                'user':self.isLogin,
            }

            self.conn.send(bytes(json.dumps(point), encoding="utf-8"))   #发送文件指针信息,包括动作,文件名,目标路径,文件大小,md5等
            server_ack = self.conn.recv(1024).decode()      #接收服务器状态
            code = server_ack.split('|')[0]
            if code == '211':    #选择是否断点续传
                common.code_parsing(server_ack)
                while True:
                    res = input('请选择：')
                    if res in ('y','n'):
                        self.conn.send(res.encode())
                        server_ack = self.conn.recv(1024).decode()  # 接收服务器状态
                        if server_ack.split('|')[0] == "200":  # 服务器已经准备好接收数据
                            start_send_size = int(server_ack.split('|')[1])
                            break
                        else:
                            common.code_parsing(server_ack)
                            return None  #服务端异常,中断上传
                    else:
                        print("输入错误，请输入y和n")
            elif code == "200": #直接上传
                start_send_size = 0
            else:
                common.code_parsing(server_ack)
                return None  # 服务端异常,中断上传
        else:
            print("%s 不存在!!" % local_file)
            return None  # 客户端异常,中断上传

        #开始上传
        fp = open(local_file, 'rb')
        fp.seek(start_send_size)
        while start_send_size < filesize:
            data = fp.read(4096)
            self.conn.send(data)
            start_send_size += len(data)
            common.view_bar(start_send_size, filesize)
        fp.close()
        result = self.conn.recv(1024).decode()
        common.code_parsing(result)

    @session_judge
    @check_file
    def get(self,arg):
        '''
        下载文件
        :param arg: 下载的文件和本地路径
        :return:
        '''
        point = {
            'action':arg[0],
            'file':arg[1],
            'user':self.isLogin,
        }
        self.conn.send(json.dumps(point).encode())     #发送文件指针,包含动作和下载的文件名
        server_ack = self.conn.recv(1024).decode()
        if not server_ack == '404':
            server_ack = json.loads(server_ack)
            filename = server_ack['filename']
            filesize = server_ack['filesize']
            filemd5 = server_ack['md5']
            #判断本地路径
            if os.path.exists(arg[2]):          #存在,说明不需要重命名
                if os.path.isfile(arg[2]):           #判断目标文件是否存在
                    print("%s本地文件已存在"%arg[2])
                    self.conn.send('error'.encode())  # 发送客户端状态
                    return None  # 中断下载
                else:
                    tmp_filename = "%s_%s.tmp" % (filename, filemd5)  # 临时文件名
                    tmp_file = os.path.join(arg[2],tmp_filename)        #临时文件
                    file = os.path.join(arg[2], filename)       #真实文件
            else:       #不存在,说明可能需要重命名
                upper_file_path = os.path.dirname(arg[2])       #本地目标路径的上一级目录
                if os.path.exists(upper_file_path): #上一级目录存在,说明需要重命名
                    filename = os.path.basename(arg[2])
                    tmp_filename = "%s_%s.tmp" % (filename, filemd5)  # 临时文件名
                    tmp_file = os.path.join(upper_file_path,tmp_filename)
                    file = arg[2]           #真实文件为目标目录,最后一个为文件名
                else:       #上一级目录不存在,说明输入的路径的确不存在
                    print(print("本地路径不存在:%s" % arg[2]))
                    self.conn.send('error'.encode())  # 发送客户端状态
                    return None  #中断下载

            #判断断点续传
            if os.path.exists(tmp_file):     #临时文件存在
                while True:
                    res = input("本地文件%s已存在,是否断点续传?[y/n]" % file)
                    if res == 'y':
                        start_size = os.stat(tmp_file).st_size
                        open_file_type = 'ab'
                        break
                    elif res == 'n':
                        start_size = 0
                        open_file_type = 'wb'
                        break
                    else:
                        print("请输入y和n")
            else:
                start_size = 0
                open_file_type = 'wb'
                #发送结果
            self.conn.send(bytes("ok|%s" % start_size,encoding='utf-8'))

            fw = open(tmp_file,open_file_type)
            fw.seek(start_size)
            recv_size = start_size
            while recv_size < filesize:
                data = self.conn.recv(4096)
                fw.write(data)
                recv_size += len(data)
                common.view_bar(recv_size,filesize)
            fw.close()
            newmd5 = common.md5sum(tmp_file)  # md5校验
            if newmd5 == filemd5:
                shutil.move(tmp_file,file)
                print("文件下载成功")
            else:
                print("文件下载失败,md5不一致,服务端md5:%s" %filemd5)
                res = input("是否删除临时文件? [y/n] ")
                if res == 'y':
                    os.remove(tmp_file)
        else:
            common.code_parsing(server_ack)

    @session_judge
    def ls(self,arg):
        '''
        列出当前目录或者前目录子目录的方法
        :param arg: 目录路径
        :return:
        '''
        if len(arg) < 2:
            path = self.current_path
        else:
            path = self.__cover_path(arg[1])
        point = {
            'action':arg[0],
            'path':path,
            'user':self.isLogin,

        }
        self.conn.send(json.dumps(point).encode())
        server_ack = self.conn.recv(4096).decode()
        for k,v in json.loads(server_ack).items():
            print(k+v)

    @session_judge
    @check_file
    def rm(self,arg):
        '''
        删除文件或目录
        :param arg:
        :return:
        '''
        point = {
            'action':arg[0],
            'file':arg[1],
            'user':self.isLogin,
        }
        self.conn.send(json.dumps(point).encode())     #发送指针到服务端
        server_ack = self.conn.recv(1024).decode()
        common.code_parsing(server_ack)

    @session_judge
    def pwd(self,arg):
        '''
        查看当前所在路径
        :return:
        '''
        if self.current_path:
            print(os.path.join("/",self.current_path))
        else:
            print("/")

    def __back_path(self,arg, num):
        '''
        用于目录切换,消除../
        :param num:
        :return:
        '''
        if num == 0:
            return arg
        else:
            tmp = os.path.dirname(arg)
            num -= 1
            return self.__back_path(tmp, num)
    def __cover_path(self,arg):
        '''
        处理切换目录中返回的输入 ../../
        :param arg: 路径
        :return: 处理后的路径
        '''

        arg = re.search(r'((\.\./?)*(\w*/?\w*)*)', arg).group()  # 取出正确的路径
        path_back = re.findall(r'(\.\./?)', arg)                #取出 ../,形成一个列表,用于计算../个数
        dir_path = re.search(r'(\w+/?)+',arg)             #取出../后面的内容
        back_num = len(path_back)
        if not back_num == 0:      #如果../存在
            res = self.__back_path(self.current_path,back_num)
        else:       #../不存在
            res = self.current_path
        if not dir_path:  # 如果../后面没有内容，则path就是处理后的结果
            path = res
        else:  # 否则需要将处理后的路径和./后面内容拼接
            dir_path = dir_path.group()
            path = os.path.join(res,dir_path)
        return path

    @session_judge
    def cd(self,arg):
        '''
        切换目录方法
        :param arg: 切换的路径
        :return:
        '''
        path = self.__cover_path(arg[1])
        point = {
            'action':arg[0],
            'target_path':path,
            'user':self.isLogin,
        }
        self.conn.send(json.dumps(point).encode())
        server_ack = self.conn.recv(1024).decode()
        if server_ack == '203':
            self.current_path = path
        else:
            common.code_parsing(server_ack)

    @session_judge
    def mkdir(self,arg):
        '''
        创建目录的方法
        :param arg: 目录路径
        :return:
        '''
        path = self.__cover_path(arg[1])
        point = {
            'action':arg[0],
            'path':path,
            'user':self.isLogin,
        }
        self.conn.send(json.dumps(point).encode())     #发送文件指针
        server_ack = self.conn.recv(1024).decode()
        common.code_parsing(server_ack)

    @session_judge
    def mv(self,arg):
        '''
        客户端移动文件或者修改文件名的方法
        :param arg:
        :return:
        '''
        if len(arg) == 3:
            source = self.__cover_path(arg[1])         #源地址
            target = self.__cover_path(arg[2])        #目标地址
            point = {
                'action':arg[0],
                'source':source,
                'target':target,
                'user':self.isLogin,
            }

            self.conn.send(json.dumps(point).encode())  # 发送文件指针
            server_ack = self.conn.recv(1024).decode()
            common.code_parsing(server_ack)
        else:
            print("缺少必须参数")

    def exit(self,arg):
        '''
        客户端断开链接
        :param arg:
        :return:
        '''
        point = {
            'action':arg[0],
        }
        self.conn.send(json.dumps(point).encode())  # 发送文件指针
        exit()

    def help(self,arg):
        msg = '''
支持命令:
        connect     连接服务器  [ip  port]
        put         上传
        get         下载
        ls          列出文件
        rm          删除目录或文件
        pwd         查看当前路径
        mkdir       创建目录
        mv          移动或更名
        help        帮助
        '''
        print(msg)