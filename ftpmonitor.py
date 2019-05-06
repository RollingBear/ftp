# -*- coding: utf-8 -*-

#   2019/5/5 0005 下午 2:58     

__author__ = 'RollingBear'

import os
import time
import logging
import traceback
import configparser
from confluent_kafka import Producer
from protobuf import sendfile_pb2

cf = configparser.ConfigParser()
cf.read("config.conf", encoding="utf-8")

# kafka
servers = cf.get('kafka', 'bootstrap_servers')
group = cf.get('kafka', 'photoimportgroup')
msg_max_bytes = cf.getint("kafka", "msg_max_bytes")
receive_message_max_bytes = cf.getint("kafka", "receive_message_max_bytes")
storagerecvtopic = cf.get("kafka", "storagerecvtopic")
file_path = os.path.abspath(cf.get('ftp_mod', 'file_path'))
file_size = int(cf.get('ftp_mod', 'file_size'))
scan_time = int(cf.get('ftp_mod', 'scan_time'))

# 定义生产者
producer = Producer({'bootstrap.servers': servers,
                     # 'security.protocol': 'sasl_plaintext',
                     # 'sasl.mechanism': 'PLAIN',
                     # 'sasl.username': 'admin',
                     # 'sasl.password': 'admin123',
                     "message.max.bytes": msg_max_bytes,
                     'default.topic.config': {'acks': 'all'}})

path = []
name = []
count_remove = 0

def get_file_list(file_path):
    '''Traversing the file directory, remove file size > 50Kb'''

    global count_remove

    try:
        file_list = os.listdir(file_path)
        # Traversing the file directory
        for file in file_list:
            filepath = os.path.join(file_path, file)
            # if file folder, recursive
            if os.path.isdir(filepath):
                get_file_list(filepath)
            # if not file folder, save file name and path
            elif os.path.isfile(filepath):
                if '.jpg' in file:
                    print(file, 'has been removed')
                    os.remove(filepath)
                    count_remove += 1
                elif os.path.getsize(filepath) > (file_size * 1024):
                    print(file, 'has been removed')
                    os.remove(filepath)
                    count_remove += 1
                else:
                    path.append(filepath)
                    name.append(file)

    except Exception as e:
        logging.info(traceback.format_exc())

    return path, name


def get(file_path):
    '''empty list'''
    del path[:]
    del name[:]
    return get_file_list(file_path)


def format_name_face(face, face_path):
    '''rename hk face file'''
    try:
        creat_time = os.path.getctime(face_path)
        data_secs = (creat_time - int(creat_time)) * 10000
        data_head = time.strftime("%Y%m%d%H%M%S", time.localtime(creat_time))
        time_stamp = "%s%04d" % (data_head, data_secs)

        dirname = face_path.lstrip(file_path).split('/')[0]

        face_format_result = dirname + '_' + time_stamp + '_face.jpg'
        face_path_format = face_path.replace(str(face), str(face_format_result))

        with open(face_path_format, 'rb') as f:
            data = f.read()

        msg = sendfile_pb2.sendpic()
        msg.face_filename = face_format_result
        msg.face = data
        producer.produce(topic=storagerecvtopic, value=msg.SerializeToString())
        producer.poll(1)

    except Exception as e:
        logging.info(traceback.format_exc())



# def kafka_send(face, face_path):
#     try:
#         msg = sendfile_pb2.sendpic()
#         msg.face_filename = face
#         msg.face = face_path
#         producer.produce(topic=storagerecvtopic, value=msg.SerializeToString())
#         producer.poll(1)
#
#         return True
#
#     except Exception as e:
#         logging.info(traceback.format_exc())
#         return False


def update_file():
    '''Traversing the file directory, rename all file'''
    while True:
        get(file_path)
        global count_remove
        print(count_remove, 'picture removed')
        count_remove = 0
        for i in range(len(name)):
            format_name_face(name[i], path[i])
            os.remove(path[i])

        # get(file_path)
        #
        # for i in range(len(name)):
        #     result = kafka_send(name[i], path[i])
        #     if result:
        #         try:
        #             os.remove(path[i])
        #         except Exception as e:
        #             logging.info(traceback.format_exc())
        #     else:
        #         logging.info('send to kafka failed')

        time.sleep(scan_time)


if __name__ == '__main__':
    update_file()