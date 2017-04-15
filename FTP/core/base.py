#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __Author__: Zhaohongfei

import os
import configparser

BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def init():
    '''
    获取服务器配置
    :return:
    '''
    config_file = os.path.join(BASE_PATH,'conf','ftp.conf')
    config = configparser.ConfigParser()
    config.read(config_file)
    configinfo = dict(config.items(section='global'))     #获取global信息
    sections = config.sections()    #获取所有section
    userdb = os.path.join(BASE_PATH, configinfo['userdb'])
    userinfo = {}
    with open(userdb,'r') as fp:
        for i in fp:
            i = i.strip().split(':')
            username = i[0]
            password = i[1]
            userinfo[username] = {'password':password}
            if username in sections:
                userconfig = dict(config.items(section=username))
                userinfo[username].update(userconfig)
    configinfo['userinfo'] = userinfo
    return configinfo
