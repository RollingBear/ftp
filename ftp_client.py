# -*- coding: utf-8 -*-

#   2019/5/28 0028 下午 4:26     

__author__ = 'RollingBear'

import os
import sys
import time
import json
import socket
import hashlib
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s  %(threadName)s  %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
                    stream=sys.stdout)

Rthandler = RotatingFileHandler('logs/ftp_monitor_log.log', maxBytes=10 * 1024 * 1024, backupCount=10)
Rthandler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s  %(threadName)s  %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
Rthandler.setFormatter(formatter)
logger = logging.getLogger('PicCaptureFace')
logger.addHandler(Rthandler)


class ftp_client(object):

    def init(self):
        self.client = socket.socket()

    def help(self):
        msg = '''useage:
                    ls
                    pwd
                    cd dir(example:/ .. . /var
                    put filename
                    rm filename
                    get filename
                    mkdir directory name
                    '''
        print(msg)

    def connect(self, addr, port):
        self.client.connect((addr, port))

    def auth(self):
        m = hashlib.md5()

        username = input('Input username:').strip()
        m.update(input('Input password:').strip().encode())
        password = m.hexdigest()

        user_info = {
            'action': 'auth',
            'username': username,
            'password': password
        }

        self.client.send(json.dumps(user_info).encode('utf-8'))
        server_response = self.client.recv(1024).decode()

        return server_response

    def interactive(self):
        while True:
            msg = input('>>>').strip()
            if not msg:
                logger.warning('Can not send Null')
                continue

            cmd = msg.split()[0]
            if hasattr(self, cmd):
                func = getattr(self, cmd)
                func(msg)
            else:
                self.help()
                continue

    def put(self, *args):
        cmd_split = args[0].split()
        if len(cmd_split) > 1:
            filename = cmd_split[1]
            if os.path.isfile(filename):
                filesize = os.stat(filename).st_size
                file_info = {
                    'action': 'put',
                    'filename': filename,
                    'size': filesize,
                    'overriding': 'True'
                }
                self.client.send(json.dumps(file_info).encode('utf-8'))
                request_code = {
                    '200': 'Ready to receive data!',
                    '210': 'Not ready to receive data!'
                }
                server_response = self.client.recv(1024).decode()
                if server_response is '200':
                    with open(filename, 'rb') as f:
                        send_size = 0
                        start_time = time.time()
                        for line in f:
                            self.client.send(line)
                            send_size += len(line)
                            while True:
                                send_percentage = int((send_size / filesize) * 100)
                                progress = ('\r Update finish: %sMB(%s%%)' % (
                                    round(send_size / 102400, 2), send_percentage)).encode('utf-8')
                                os.write(1, progress)
                                sys.stdout.flush()
                                time.sleep(0.0001)
                                break
                        else:
                            end_time = time.time()
                            time_use = int(end_time - start_time)
                            logger.info('\n File {} has been sent successfully!'.format(filename))
                            logger.info('\n Average download speed: {}Mb/s'.format(
                                round(round(send_size / 102400, 2) / time_use, 2)))
                else:
                    logger.warning('Server is not ready to receive data')
                    time.sleep(10)
                    with open(filename, 'rb') as f:
                        send_size = 0
                        start_time = time.time()
                        for line in f:
                            self.client.send(line)
                            send_size += len(line)
                            while True:
                                send_percentage = int((send_size / filesize) * 100)
                                progress = ('\r Update finish: %sMB(%s%%)' % (
                                    round(send_size / 102400, 2), send_percentage)).encode('utf-8')
                                os.write(1, progress)
                                sys.stdout.flush()
                                break
                        else:
                            end_time = time.time()
                            time_use = int(end_time - start_time)
                            logger.info('\n File {} has been sent successfully!'.format(filename))
                            logger.info('\n Average download speed: {}Mb/s'.format(
                                round(round(send_size / 102400, 2) / time_use, 2)))
            else:
                logger.warning('File {} not exist'.format(filename))
        else:
            self.help()

    def ls(self, *args):
        cmd_split = args[0].split()
        if len(cmd_split) > 1:
            path = cmd_split[1]
        elif len(cmd_split) == 1:
            path = '.'

        request_info = {
            'action': 'ls',
            'path': path
        }

        self.client.send(json.dumps(request_info).encode('utf-8'))
        server_response = self.client.recv(1024).decode()

        logger.info(server_response)

    def pwd(self, *args):
        cmd_split = args[0].split()
        if len(cmd_split) == 1:
            request_info = {
                'action': 'pwd'
            }
            self.client.send(json.dumps(request_info).encode('utf-8'))
            server_response = self.client.recv(1024).decode()
            logger.info(server_response)
        else:
            self.help()

    def get(self, *args):
        cmd_split = args[0].split()
        if len(cmd_split) > 1:
            filename = cmd_split[1]
            file_info = {
                'action': 'get',
                'filename': filename,
                'overriding': 'True'
            }
            self.client.send(json.dumps(file_info).encode('utf-8'))
            server_response = self.client.recv(1024).decode()
            self.client.send('0'.encode('utf-8'))
            if server_response is '0':
                file_size = int(self.client.recv(1024).decode())
                self.client.send('0'.encode('utf-8'))
                if os.path.isfile(filename):
                    filename = filename + '.new'
                with open(filename, 'wb') as f:
                    receive_size = 0
                    m = hashlib.md5()
                    start_time = time.time()
                    while receive_size < file_size:
                        if file_size - receive_size > 1024:
                            size = 1024
                        else:
                            size = file_size - receive_size
                        data = self.client.recv(size)
                        m.update(data)
                        receive_size += len(data)
                        data_percent = int((receive_size / file_size) * 100)
                        f.write(data)
                        progress = ('\r Download Finish: %sMB(%s%%)' % (
                            round(receive_size / 102400, 2), data_percent)).encode('utf-8')
                        os.write(1, progress)
                        sys.stdout.flush()
                        time.sleep(0.0001)
                    else:
                        end_time = time.time()
                        time_use = int(end_time - start_time)
                        logger.info('\n Average Download speed: {}MB/s'.format(
                            round(round(receive_size / 102400, 2) / time_use, 2)))
                        Md5_server = self.client.recv(1024).decode()
                        Md5_client = m.hexdigest()
                        print('File Checking, please wait')
                        time.sleep(0.3)
                        if Md5_server == Md5_client:
                            logger.info('Normal file: {}'.format(filename))
                        else:
                            logger.info('Md5 not match: {}'.format(filename))
            else:
                logger.warning('File not find')
                self.interactive()
        else:
            self.help()

    def rm(self, *args):
        cmd_split = args[0].split()
        if len(cmd_split) > 1:
            filename = cmd_split[1]
            request_info = {
                'action': 'rm',
                'filename': filename,
                'prompt': 'Y'
            }
            self.client.send(json.dumps(request_info).encode('utf-8'))
            server_response = self.client.recv(1024).decode()

            request_code = {
                '0': 'confirm to delete',
                '1': 'cancel to delete'
            }

            if server_response is '0':
                confirm = input('Are you sure to delete this file?')
                if confirm is 'Y' or confirm is 'y':
                    self.client.send('0'.encode('utf-8'))
                    logger.info(self.client.recv(1024).decode())
                else:
                    self.client.send('1'.encode('utf-8'))
                    logger.info(self.client.recv(1024).decode())
            else:
                logger.warning('File not find')
                self.interactive()
        else:
            self.help()

    def cd(self, *args):
        cmd_split = args[0].split()
        if len(cmd_split) > 1:
            path = cmd_split[1]
        elif len(cmd_split) == 1:
            path = '.'

        request_info = {
            'action': 'cd',
            'path': path
        }

        self.client.send(json.dumps(request_info).encode('utf-8'))
        server_response = self.client.recv(1024).decode()
        logger.info(server_response)

    def mkdir(self, *args):
        request_code = {
            '0': 'Directory has been made!',
            '1': 'Directory is aleady exist!'
        }
        cmd_split = args[0].split()
        if len(cmd_split) > 1:
            dir_name = cmd_split[1]
            request_info = {
                'action': 'mkdir',
                'dir_name': dir_name
            }
            self.client.send(json.dumps(request_info).encode("utf-8"))
            server_response = self.client.recv(1024).decode()
            if server_response == '0':
                print('Directory has been made!')
            else:
                print('Directory is already exist!')
        else:
            self.help()


def run():
    client = ftp_client()
    # client.connect('10.1.2.3',6969)
    Addr = input("请输入服务器IP：").strip()
    Port = int(input("请输入端口号：").strip())
    client.connect(Addr, Port)
    while True:
        if client.auth() == '0':
            print("Welcome.....")
            client.interactive()
            break
        else:
            print("用户名或密码错误！")
            continue
