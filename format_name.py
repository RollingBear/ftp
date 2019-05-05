# -*- coding: utf-8 -*-

#   2019/5/5 0005 下午 2:58     

__author__ = 'RollingBear'

import os
import logging
import traceback

path = []
name = []


def get_file_list(file_path):
    '''Traversing the file directory'''
    file_list = os.listdir(file_path)
    # Traversing the file directory
    for file in file_list:
        filepath = os.path.join(file_path, file)
        # if file folder, recursive
        if os.path.isdir(filepath):
            get_file_list(filepath)
        # if not file folder, save file name and path
        elif os.path.isfile(filepath):
            path.append(filepath)
            name.append(file)
    return path, name


def get(file_path):
    '''empty list'''
    del path[:]
    del name[:]
    return get_file_list(file_path)


def format_name_face(face, face_path):
    '''rename face file'''
    print(face)
    face_format = face.split('_')
    face_format_result = face_format[0] + '_' + face_format[2] + '0_face.jpg'
    face_path_format = face_path.replace(str(face), str(face_format_result))
    try:
        os.rename(face_path, face_path_format)
    except Exception as e:
        logging.info(traceback.format_exc())


def format_name_back(back, back_path):
    '''rename back file'''
    print(back)
    back_format = back.split('_')
    back_format_result = back_format[0] + '_' + back_format[2] + '0_back.jpg'
    back_path_format = back_path.replace(back, back_format_result)
    try:
        os.rename(back_path, back_path_format)
    except Exception as e:
        logging.info(traceback.format_exc())


def update_file(file_path):
    '''Traversing the file directory, rename all file'''
    get(file_path)
    count = 0
    for i in range(len(name)):
        if 'FACE' in name[i]:
            count += 1
            format_name_face(name[i], path[i])
        elif 'BACK' in name[i]:
            count += 1
            format_name_back(name[i], path[i])
        else:
            continue
    print(count, 'picture formatted')


if __name__ == '__main__':
    file_path = 'E:\\ftp\\admin'

    # get(file_path)
    # print(path)
    # print(name)

    update_file(file_path)

    # get(file_path)
    # print(path)
    # print(name)

    # for num in range(len(path)):
    #     print(path[num])
    #     print(name[num])
    #     print("created: %s" % time.ctime(os.path.getctime(path[num])))
    #     print()
