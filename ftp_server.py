# -*- coding: utf-8 -*-

#   2019/4/30 0030 下午 2:03     

__author__ = 'RollingBear'

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler, ThrottledDTPHandler
from pyftpdlib.servers import FTPServer

import mysql
import config

import logging

conf = config.config('\\config\\config.ini')
sql = mysql.mysql()


def get_user():
    # 定义一个用户列表

    user_list = sql.format_query_dict(_list_name='*', _table_name='user', _condition='user_id>0')
    return user_list


def ftp_server():
    # 实例化虚拟用户，这是FTP验证首要条件
    authorizer = DummyAuthorizer()

    # 添加用户权限和路径，括号内的参数是(用户名， 密码， 用户目录， 权限)
    # authorizer.add_user('user', '12345', '/home/', perm='elradfmw')
    user_list = get_user()
    for user in user_list:
        id, username, password, auth, address = user
        try:
            authorizer.add_user(username=username, password=password, homedir=address, perm=auth)
        except Exception as e:
            print(e)

    # 添加匿名用户 只需要路径
    if conf.get('ftp').enable_anonymous == 'on':
        authorizer.add_anonymous(conf.get('ftp').anonymous_path)

    # 下载上传速度设置
    dtp_handler = ThrottledDTPHandler
    dtp_handler.read_limit = int(conf.get('ftp').max_download) * 1024
    dtp_handler.write_limit = int(conf.get('ftp').max_upload) * 1024

    # 初始化ftp句柄
    handler = FTPHandler
    handler.authorizer = authorizer

    # 日志记录
    if conf.get('ftp').enable_logging == 'on':
        logging.basicConfig(filename=conf.get('ftp').logging_name, level=logging.INFO)

    # 欢迎信息
    handler.banner = conf.get('ftp').welcome_msg

    # 添加被动端口范围
    handler.passive_ports = range(int(conf.get('ftp').port_start), int(conf.get('ftp').port_end))

    # 监听ip 和 端口
    server = FTPServer((conf.get('ftp').ip, int(conf.get('ftp').port)), handler)

    # 最大连接数
    server.max_cons = int(conf.get('ftp').max_connect)
    server.max_cons_per_ip = int(conf.get('ftp').max_per_id)

    # 开始服务
    print(conf.get('ftp').welcome_msg)
    server.serve_forever()


if __name__ == "__main__":
    ftp_server()
