# -*- coding: utf-8 -*-

#   2019/5/5 0005 下午 2:58     

__author__ = 'RollingBear'

import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler
import traceback
import configparser
from confluent_kafka import Producer
from protobuf import sendfile_pb2

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s  %(threadName)s  %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    stream=sys.stdout)

Rthandler = RotatingFileHandler('ftp_monitor_log.log', maxBytes=10 * 1024 * 1024, backupCount=10)
Rthandler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s  %(threadName)s  %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
Rthandler.setFormatter(formatter)
logger = logging.getLogger('PicCaptureFace')
logger.addHandler(Rthandler)

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


# name = []


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
                if '.jpg' not in file:
                    print(file, 'has been removed')
                    os.remove(filepath)
                elif os.path.getsize(filepath) > (file_size * 1024):
                    print(file, 'has been removed')
                    os.remove(filepath)
                else:
                    path.append(filepath)
                    # name.append(file)

    except Exception as e:
        logger.error(traceback.format_exc())

    return path


def get(file_path):
    '''empty list'''
    del path[:]
    # del name[:]
    return get_file_list(file_path)


def format_name_face(face_path):
    '''rename hk face file'''
    try:
        creat_time = os.path.getctime(face_path)
        data_secs = (creat_time - int(creat_time)) * 10000
        data_head = time.strftime("%Y%m%d%H%M%S", time.localtime(creat_time))
        time_stamp = "%s%04d" % (data_head, data_secs)

        dirname = face_path.lstrip(file_path).split('/')[0].replace('-', '.')

        face_format_result = dirname + '_' + time_stamp + '_face.jpg'
        # face_path_format = face_path.replace(str(face), str(face_format_result))

        try:
            with open(face_path, 'rb') as f:
                data = f.read()

            msg = sendfile_pb2.sendpic()
            msg.face_filename = face_format_result
            msg.face = data
            producer.produce(topic=storagerecvtopic, value=msg.SerializeToString())
            producer.poll(1)
        except Exception as e:
            logger.error(traceback.format_exc())

    except Exception as e:
        logger.error(traceback.format_exc())


def start():
    '''Traversing the file directory, rename all file'''
    while True:
        get(file_path)
        for i in range(len(path)):
            format_name_face(path[i])
            try:
                os.remove(path[i])
            except Exception as e:
                logger.error(traceback.format_exc())

        time.sleep(scan_time)


if __name__ == '__main__':
    logger.info('Start at {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))
    start()
