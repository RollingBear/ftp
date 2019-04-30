# -*- coding: utf-8 -*-

# 2019/3/18 0018 下午 4:56

__author__ = 'RollingBear'

'''
This file provides a simple way to read the ini configuration file

usage mode:
    same as a common class
        name = config('ini configuration file address')
        message = name.get('section').key

FINAL EDIT TIME: 2019/03/19 12:41
FINAL EDITOR: RollingBear
'''

import configparser
import os
import logging
import traceback


class OperationalError(Exception):
    '''
    operation error
    '''


class Dictionary(dict):
    '''
    from "config.ini" add parameter into the dict
    '''

    def __getattr__(self, item):
        '''
        item == key
        if the value of the key not existed
        return the default: not find config keyname
        :param item: the key
        :return: the value of the key
        '''
        return self.get(item, 'not find config key name in "config.ini"')

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


class config(object):
    '''
    the secondary encapsulation of the config parse, get value with key from the dictionary
    when the class init, need a parameter: the address of ini configuration file
    '''

    def __init__(self, config_file_address):
        '''
        get the path of config.ini
        current_dir = absolute address
        top_one_dir = the superior address of the absolute address
        if ini configuration file locate the same address with this python file, use
            file_name = current_dir + config_file_address
                ps: need modification the "config_file_address", remove relative address from variable value,
                    only need a file name of the ini configuration file
        if ini configuration file locate the superior address of this python file, use
            file_name = top_one_dir + config_file_address
                ps: need modification the "config_file_address", add relative address into variable value
        '''

        self.config_file_address = config_file_address

        try:
            self.current_dir = os.path.dirname(__file__)
            self.file_name = self.current_dir + self.config_file_address
            # self.top_one_dir = os.path.dirname(self.current_dir)
            # self.file_name = self.top_one_dir + self.config_file_address
        except Exception:
            logging.info(traceback.format_exc())

        '''instantiation the config parse object'''
        try:
            self.config = configparser.ConfigParser()
            self.config.read(self.file_name, encoding="utf-8-sig")
        except Exception:
            logging.info(traceback.format_exc())

        '''with section write the key and value into dictionary'''
        for section in self.config.sections():
            try:
                setattr(self, section, Dictionary())
                for keyname, value in self.config.items(section):
                    try:
                        setattr(getattr(self, section), keyname, value)
                    except Exception:
                        logging.info(traceback.format_exc())
            except Exception:
                logging.info(traceback.format_exc())

    def get(self, section):
        '''
        get option
        @:param section: section to fetch
        @:return: option value
        '''

        try:
            return getattr(self, section)
        except AttributeError as e:
            logging.info(traceback.format_exc())
            raise OperationalError('Option %s is not found in configuration, error: %s' % (section, e))

    def outer_element_count(self):
        '''
        dictionary outer element statistics
        :return: the count of ini label
        '''
        conf = configparser.ConfigParser()
        conf.read(self.config_file_address[1:], encoding='utf-8')
        dic = dict(conf._sections)
        for i in dic:
            dic[i] = dict(dic[i])

        return len(dic)
