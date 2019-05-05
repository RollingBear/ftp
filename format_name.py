# -*- coding: utf-8 -*-

#   2019/5/5 0005 下午 2:58     

__author__ = 'RollingBear'

import os
import time

path = []
name = []


def getallfile(file_path):
    file_list = os.listdir(file_path)
    # 遍历该文件夹下的所有目录或者文件
    for file in file_list:
        filepath = os.path.join(file_path, file)
        # 如果是文件夹，递归调用函数
        if os.path.isdir(filepath):
            getallfile(filepath)
        # 如果不是文件夹，保存文件路径及文件名
        elif os.path.isfile(filepath):
            path.append(filepath)
            name.append(file)
    return path, name


def get(file_path):
    del path[:]
    del name[:]
    return getallfile(file_path)


if __name__ == '__main__':
    file_path = 'E:\\ftp\\admin'
    get(file_path)
    for num in range(len(path)):
        print(path[num])
        print(name[num])
        print("created: %s" % time.ctime(os.path.getctime(path[num])))
        print()

    print(path)
    print(name)
