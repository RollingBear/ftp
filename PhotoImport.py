#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/10/26 14:48
import platform
import time
import datetime
import os
import sys
from logging.handlers import RotatingFileHandler
from queue import Queue
import re
import threading
from PIL import Image, ImageDraw
import logging
import traceback
import time
import io
from confluent_kafka import Producer
from confluent_kafka import Consumer
from protobuf import sendfile_pb2
import face_function
import configparser

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s  %(threadName)s  %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    stream=sys.stdout)

Rthandler = RotatingFileHandler('logs/Face_PhotoImport.log', maxBytes=10 * 1024 * 1024, backupCount=10)
Rthandler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s  %(threadName)s  %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
Rthandler.setFormatter(formatter)
logger = logging.getLogger('PicCaptureFace')
logger.addHandler(Rthandler)

cf = configparser.ConfigParser()
cf.read("config.conf", encoding="utf-8")

data_model_dir = cf.get("general", "data_model_dir")  # 数据模型目录
face_maxnum = cf.getint("general", "face_maxnum")  # ;最大人脸数
face_feature_length = cf.getint("general", "face_feature_length")  # ;人脸特征长度

threadNum = cf.getint("photoimport", "feature_thread_num")  # 提取特征的线程数
threadNum_back = threadNum  # 提取特征的线程数

pic_Quality = cf.getint("photoimport", "pic_Quality")  # ;图片品质
angle_confidence = cf.getfloat("photoimport", "angle_confidence")  # ;人脸姿态可信度
yaw_threshold = cf.getint("photoimport", "yaw_threshold")  # ;人脸姿态角度
pitch_threshold = cf.getint("photoimport", "pitch_threshold")  #
roll_threshold = cf.getint("photoimport", "roll_threshold")  #

# kafka
servers = cf.get('kafka', 'bootstrap_servers')
group = cf.get('kafka', 'photoimportgroup')
msg_max_bytes = cf.getint("kafka", "msg_max_bytes")
receive_message_max_bytes = cf.getint("kafka", "receive_message_max_bytes")
storagerecvtopic = cf.get("kafka", "storagerecvtopic")
photoimportrecvtopic = cf.get("photoimport", "photoimportrecvtopic")

platm = sys.platform
if platm == "linux":
    data_model_dir = data_model_dir.replace("\\", '/')

# 定义生产者
producer = Producer({'bootstrap.servers': servers,
                     # 'security.protocol': 'sasl_plaintext',
                     # 'sasl.mechanism': 'PLAIN',
                     # 'sasl.username': 'admin',
                     # 'sasl.password': 'admin123',
                     "message.max.bytes": msg_max_bytes,
                     'default.topic.config': {'acks': 'all'}})
# 定义消费者
consumer = Consumer({
    'bootstrap.servers': servers,
    # 'security.protocol': 'sasl_plaintext',
    # 'sasl.mechanism': 'PLAIN',
    # 'sasl.username': 'admin',
    # 'sasl.password': 'admin123',
    'group.id': group,
    'enable.auto.commit': False,
    "receive.message.max.bytes": receive_message_max_bytes,
    'fetch.message.max.bytes': msg_max_bytes
})
consumer.subscribe([photoimportrecvtopic])

failnum = 0
oknum = 0

picQueue = Queue()
fileContextQueue = Queue()
procQueue = Queue()
lasttime = time.time()

lock = threading.Lock()
lock_shooting_time = threading.Lock()

# 文件名格式 192.168.1.1_01_20180820153001001_*.jpg
pattern = re.compile(
    r'((?:(?:25[0-5]|2[0-4]\d|(?:1\d{2}|[1-9]?\d))\.){3}(?:25[0-5]|2[0-4]\d|(?:1\d{2}|[1-9]?\d)))_(\d){2}_(\d)+_(.)+\.jpg')


# 取特征线程
class featureThread(threading.Thread):
    def __init__(self, threadId):
        threading.Thread.__init__(self)
        self.threadId = threadId

    def run(self):
        while True:
            try:
                cameraid, importbatch, date, fname, fpath, file, feedbacktopic, total, currentid = picQueue.get()
                if not fpath and not fname:
                    continue

                FeatureTest(fname, file, cameraid, date, importbatch, len(file), self.threadId)
                procQueue.put((feedbacktopic, fname, fpath, currentid, total))
            except Exception as e:
                time.sleep(1)
                logger.error(traceback.format_exc())


"""
提取特征
"""


def FeatureTest(filename, file, camera_id, shooting_time, importbatch, imageLen, threadId):
    global lock_shooting_time, lasttime
    res = face_function.RLTZ(threadId, file, imageLen)
    if res[0] == 0:
        Faceinfos = res[2]
        feature_num = res[3]
        if feature_num > 0:
            buff = io.BytesIO(file)
            im = Image.open(buff)
            fx, fy = im.size
            for num in range(0, feature_num):
                facePos = Faceinfos[num]
                this_pic_Quality = facePos.blur_score
                this_angle_confidence = facePos.confidence_headpose
                this_yaw_threshold = facePos.yaw
                this_pitch_threshold = facePos.pitch
                this_roll_threshold = facePos.roll

                if this_pic_Quality < pic_Quality:
                    continue
                # if this_angle_confidence < angle_confidence:
                #     continue
                if (abs(this_yaw_threshold) > yaw_threshold) or (abs(this_pitch_threshold) > pitch_threshold) or (
                        abs(this_roll_threshold) > roll_threshold) or (
                        (abs(this_yaw_threshold) + abs(this_pitch_threshold)) > (
                        abs(yaw_threshold) + abs(pitch_threshold) - 10)) or (
                        (abs(this_yaw_threshold) + abs(this_pitch_threshold) + abs(this_roll_threshold)) > (
                        abs(yaw_threshold) + abs(pitch_threshold) + abs(roll_threshold) - 20)):
                    continue

                left = facePos.left - 50
                if left < 0:
                    left = 0
                top = facePos.top - 50
                if top < 0:
                    top = 0
                right = facePos.right + 50
                if right > fx:
                    right = fx
                bottom = facePos.bottom + 50
                if bottom > fy:
                    bottom = fy
                w = right - left
                h = bottom - top
                with lock_shooting_time:
                    face_filename = "{}_{}_face_{}.jpg".format(camera_id, str(int(shooting_time) + num + 1),
                                                               importbatch)
                    back_filename = "{}_{}_back_{}.jpg".format(camera_id, str(int(shooting_time) + num + 1),
                                                               importbatch)
                if w / fx > 0.6 and h / fy > 0.6 and feature_num == 1:
                    facebuff = io.BytesIO()
                    # 不压缩，不裁剪，无背景
                    im.save(facebuff, format='JPEG', quality=90)
                    face_file = facebuff.getvalue()
                    backbuff = io.BytesIO()
                    back_file = backbuff.getvalue()
                else:
                    buff = io.BytesIO(file)
                    ix = Image.open(buff)
                    facebuff = io.BytesIO()
                    backbuff = io.BytesIO()
                    region = ix.crop((left, top, right, bottom))
                    region.save(facebuff, format='JPEG', quality=90)
                    face_file = facebuff.getvalue()
                    draw = ImageDraw.Draw(ix)
                    line = 3
                    for i in range(1, line + 1):
                        draw.rectangle((left + (line - i), top + (line - i), right + i, bottom + i), outline='red')
                    ix.save(backbuff, format='JPEG', quality=90)
                    back_file = backbuff.getvalue()
                msg = sendfile_pb2.sendpic()
                msg.face_filename = face_filename
                msg.face = face_file
                msg.back_filename = back_filename
                msg.back = back_file
                producer.produce(topic=storagerecvtopic, value=msg.SerializeToString())
                producer.poll(1)
                lasttime = time.time()
    else:
        logger.error("返回错误结果：------文件名：{}，res：{}".format(filename, res[0]))


# 反馈结果线程
def feedBackThread(procQueue, Producer):
    global failnum, oknum
    while True:
        try:
            time.sleep(0.05)
            feedbacktopic, filename, path, currentid, total = procQueue.get()
            msg = sendfile_pb2.ptfeedback()
            msg.fname = filename
            msg.fpath = path
            msg.currentid = currentid
            msg.total = total
            oknum += 1
            msg.oknum = oknum
            msg.failnum = 0
            if oknum == total:
                failnum = 0
                oknum = 0
            producer.produce(topic=feedbacktopic, value=msg.SerializeToString())
            producer.poll(1)
        except Exception as e:
            logger.info(traceback.format_exc())


def main():
    try:
        d = datetime.datetime.now()
        if d.year > 2019:
            logger.error("授权已过期！")
            return
        threadNum = threadNum_back
        face_function.CSH(data_model_dir, threadNum)
        logger.info("运行库初始化完成，....")
        # 启动提取特征线程
        threads = []

        for ti in range(0, threadNum):
            t = featureThread(ti)
            threads.append(t)
        for t in threads:
            t.start()

        feedback = threading.Thread(target=feedBackThread, args=(procQueue, producer))
        feedback.start()
        logger.info('结果反馈线程启动')
        logger.info('开始数据接收')
        while True:
            try:
                msg = consumer.poll(1)
                consumer.commit()
                # print(msg)
                if msg is None:
                    continue
                if msg.error():
                    # print("Consumer error: {}".format(msg.error()))
                    continue
                mmsg = sendfile_pb2.ptsendfile()
                # print('Received message: {}'.format(msg.value().decode('utf-8')))
                mmsg.ParseFromString(msg.value())
                cameraid = mmsg.cameraid
                importbatch = int(mmsg.importbatch)
                date = mmsg.date
                fname = mmsg.fname
                fpath = mmsg.fpath
                file = mmsg.file
                feedbacktopic = mmsg.feedbacktopic
                total = mmsg.total
                currentid = mmsg.currentid
                picQueue.put((cameraid, importbatch, date, fname, fpath, file, feedbacktopic, total, currentid))
            except Exception as e:
                logger.error(traceback.format_exc())
    except Exception as e:
        logger.error(traceback.format_exc())
    consumer.close()


if __name__ == '__main__':
    main()
