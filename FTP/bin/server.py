#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __Author__: Zhaohongfei


import  os,sys
import socketserver
BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(BASE_PATH,'core'))

import ftpserver
import base


def start():
    CONFIGINFO = base.init()
    ip_port = (CONFIGINFO['ip'],int(CONFIGINFO['port']))
    server = socketserver.ThreadingTCPServer(ip_port, ftpserver.FtpServer)
    server.serve_forever()


help_msg = '''
支持选项:
                %s start    运行ftpserver
                %s adduser   创建用户

'''  % (sys.argv[0],sys.argv[0])

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'start':
            start()
        elif sys.argv[1] == 'adduser':
            ftpserver.FtpServer.add_user()
        else:
            print("没有此选项:%s" % sys.argv[1])
            print(help_msg)
    else:
        print(help_msg)
