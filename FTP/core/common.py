#!/usr/bin/env python
# -*- coding: utf-8 -*-
# __Author__: Zhaohongfei


import hashlib
import os,sys
import time
import logging



def encrypt(string):
    """
    字符串加密函数
    :param string: 待加密的字符串
    :return:  返回加密过的字符串
    """
    ha = hashlib.md5(b'beyond')
    ha.update(string.encode('utf-8'))
    result = ha.hexdigest()
    return result


def md5sum(fname):
    '''
    校验文件md5
    :param fname:
    :return:
    '''
    def read_chunks(fh):
        fh.seek(0)
        chunk = fh.read(8096)
        while chunk:
            yield chunk
            chunk = fh.read(8096)
        else:
            fh.seek(0)
    m = hashlib.md5()
    if os.path.exists(fname):
        with open(fname, "rb") as fh:
            for chunk in read_chunks(fh):
                m.update(chunk)
    return m.hexdigest()


def code_parsing(server_ack):
    code_information = {
        '200':"服务端准备就绪",
        '201':'文件上传成功',
        '202':'文件上传失败',
        '203':'目录切换成功',
        '204':'目录不存在',
        '205':'目标是文件,无法切换进去',
        '206':'文件删除成功',
        '207':'文件无法删除',
        '208':'目录或文件已存在',
        '209':'可用空间不足',
        '210':'目录创建成功',
        '211':'是否断点续传？[y/n]',
        '300':'客户端准备就绪',
        '301':'客户端有问题',
        '400':'验证通过',
        '401':'用户密码错误',
        '402':'用户不存在',
        '403':'请求重新验证',
        '404':'文件或目录不存在',
        '405':'移动成功',
    }
    server_ack = server_ack.split('|')
    code = server_ack[0]
    if len(server_ack) == 2:
        msg = server_ack[1]
        print(code_information[code],msg)
    else:
        print(code_information[code])



def view_bar(num,total):
    time.sleep(0.001)
    rate = num / total
    rate_num =  int(rate * 100)
    r = '\r%s>%d%%' % ('=' * rate_num, rate_num,)
    sys.stdout.write(r)
    sys.stdout.flush

def credit_logger(log_path):
    '''
    记录ftp日志
    :param user: 用户名
    :return:
    '''

    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    fmt = logging.Formatter(fmt="%(levelname)s-%(asctime)s-%(message)s",datefmt="%Y/%m/%d %H:%M:%S")
    file_handler.setFormatter(fmt)
    logger1 = logging.Logger('credit_logger', level=logging.INFO)
    logger1.addHandler(file_handler)
    return logger1