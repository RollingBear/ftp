# -*- coding: utf-8 -*-

#   2019/4/30 0030 下午 4:01     

__author__ = 'RollingBear'


def get_user(userfile):
    # 定义一个用户列表
    user_list = []

    with open(userfile, encoding="utf-8") as f:
        for line in f:
            if not line.startswith('#') and line:
                if len(line.split()) == 4:
                    user_list.append(line.split())
                else:
                    print("user.conf配置错误")
    return user_list


print(get_user('t2.py'))

import mysql

sql = mysql.mysql()

listre = (sql.format_query_dict(_list_name='*', _table_name='user', _condition='user_id>0'))
print(listre)
print(listre[0][2])