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
import datetime

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s  %(threadName)s  %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    stream=sys.stdout)

Rthandler = RotatingFileHandler('logs/ftp_monitor_log.log', maxBytes=10 * 1024 * 1024, backupCount=10)
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
update_time = float(cf.get('ftp_mod', 'update_time'))

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


class File(object):

    def __init__(self, _file_path):

        if not os.path.exists(_file_path):
            raise OSError('{} not exist'.format(_file_path))
        self.file_path = os.path.abspath(_file_path)

    def status(self):

        open_fd_list = self.__get_all_fd()
        open_count = len(open_fd_list)
        is_opened = False
        if open_count > 0:
            is_opened = True

        return {'is_opened': is_opened, 'open_count': open_count}

    def __get_all_pid(self):
        '''get all thread'''

        return [_i for _i in os.listdir('/proc') if _i.isdigit()]

    def __get_all_fd(self):
        '''get all fd open the file'''

        all_fd = []
        for pid in self.__get_all_pid():
            _fd_dir = '/proc/{pid}/fd'.format(pid=pid)
            if os.access(_fd_dir, os.R_OK) is False:
                continue

            for fd in os.listdir(_fd_dir):
                fd_path = os.path.join(_fd_dir, fd)
                if os.path.exists(fd_path) and os.readlink(fd_path) == self.file_path:
                    all_fd.append(fd_path)

        return all_fd


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
                    os.remove(filepath)
                    logger.info('不是jpg格式文件删除{}'.format(file))
                elif os.path.getsize(filepath) > (file_size * 1024):
                    os.remove(filepath)
                    logger.info('图片大于{}KB，删除{}'.format(file_size, file))
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
            time.sleep(update_time)
            with open(face_path, 'rb') as f:
                data = f.read()
            msg = sendfile_pb2.sendpic()
            msg.face_filename = face_format_result
            msg.face = data
            producer.produce(topic=storagerecvtopic, value=msg.SerializeToString())
            producer.poll(1)
            logger.info('图片{}发送完成,===>{}'.format(face_path, face_format_result))
        except Exception as e:
            logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(traceback.format_exc())


def start():
    try:
        privilegedTime = datetime.datetime(2019, 7, 1)
        d = datetime.datetime.now()
        if d > privilegedTime:
            logger.error("授权已过期！")
            return
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
    except Exception as e:
        logger.error(traceback.format_exc())


if __name__ == '__main__':
    logger.info('Start at {}'.format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))))
    start()
