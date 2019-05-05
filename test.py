# -*- coding: utf-8 -*-

#   2019/4/30 0030 下午 4:01     

__author__ = 'RollingBear'

str_face = '192.168.81.13_01_20190505160221929_FACE_SNAP.jpg'
str_face_path = 'E:\\ftp\\admin\\192.168.81.13\\192.168.81.13_01_20190505160221929_FACE_SNAP.jpg'
str_back = '192.168.81.13_01_20190505160221327_FACE_BACKGROUND.jpg'
str_back_path = 'E:\\ftp\\admin\\192.168.81.13\\192.168.81.13_01_20190505160221327_FACE_BACKGROUND.jpg'

str_face_format_1 = str_face.split('_')
str_back_format_1 = str_back.split('_')
str_face_format_2 = str_face_format_1[0] + '_' + str_face_format_1[2][:14] + str_face_format_1[2][15:17] + '0_face.jpg'
str_back_format_2 = str_back_format_1[0] + '_' + str_back_format_1[2][:14] + str_face_format_1[2][15:17] + '0_back.jpg'

print(str_face)
print(str_face_format_2)
print(str_back)
print(str_back_format_2)

# print(len('192.168.81.13_01_20190505170759875_FACE_SNAP.jpg'))
# print(len('192.168.81.13_01_20190505170821281_FACE_BACKGROUND.jpg'))

str_face_path_format = str_face_path.replace(str_face, str_face_format_2)
str_back_path_format = str_back_path.replace(str_back, str_back_format_2)

print(str_face_path)
print(str_face_path_format)
print(str_back_path)
print(str_back_path_format)
