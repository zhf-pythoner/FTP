#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __Author__: Zhaohongfei


import os,sys
import re
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_PATH)
sys.path.append(os.path.join(BASE_PATH,'core'))
import ftpclient


obj = ftpclient.FtpClient()


logo = """
++++++++++++++++++++++++++++++++++++++++++++++
+               超级FTP                       +
+ 用户:%s                                     +
++++++++++++++++++++++++++++++++++++++++++++++
当前路径:%s
"""
while True:
    print(logo % (obj.isLogin,obj.current_path))
    res = input('ftp>>')
    if not res:
        continue
    res = re.sub(r"^\s*", '',res)    #去掉action前面的空格
    res = re.split(r'\s+',res)           #将action 和文件分割为列表
    action = res[0]
    if hasattr(obj,action):
        func = getattr(obj,action)
        func(res)
    else:
        print("没有此命令,请使用 help 查看支持的命令")
