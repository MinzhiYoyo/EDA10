import json
import os
from typing import Tuple, Any

import cv2
import numpy as np
from cv2 import Mat
from numpy import ndarray, dtype

from EDAPublic.EDACV import EDAPoint, EDARectangle
from predict import predict


class EDADataset:
    def __init__(self, input_path:str, need_read_json = True):
        # 判断 input_path 是否是目录
        assert os.path.exists(input_path), f'{input_path} not exists'
        self.input_images = []  # 读入文件夹下的所有图片
        if os.path.isdir(input_path):  # 是目录
            self.input_images = [os.path.join(input_path, file_name) for file_name in os.listdir(input_path) if file_name.endswith('.png')]
        elif os.path.isfile(input_path): # 是单个文件
            self.input_images.append(input_path)
        # 对这个list进行排序
        # if len(self.input_images) > 0:
        #     self.input_images.sort(key=lambda x: int(os.path.basename(x).split('.')[0]))

        # 读取配置文件
        with open('./config.json', 'r', encoding='utf-8') as f:
            # print(f'loading config from {f.name}')
            self.config = json.load(f)

        self.length = len(self.input_images)
        self.info_list = []  # 读入所有的yolo图片识别的信息
        if not need_read_json:  # 不需要读取json文件
            self.info_list = [self.read_a_info_list(predict(i_path)) for i_path in self.input_images]  # 读入所有的yolo图片识别的信息
        else:
            self.info_list = [
                self.read_json_file(json.load(open(i_path.replace('.png', '.json'), 'r', encoding='utf-8')))
                for i_path in self.input_images
            ]
        self.need_read_json = need_read_json

        self._index = 0

    def read_a_info_list(self, info_list):
        info = []  # 返回 [{"label": label, "points": rec}]
        for shape in info_list:
            label = self.label_trans(shape['label'])
            points = shape['points']
            left_up = EDAPoint(*points[0])
            right_down = EDAPoint(*points[1])
            rec = EDARectangle(left_up, right_down)
            info.append({
                'label': label,
                'points': rec,
            })
        return info

    def read_json_file(self, json_data: dict) -> list:  # 读取json文件
        return self.read_a_info_list(json_data['shapes'])

    def label_trans(self, label: str):
        label_hash = self.config['label_trans']
        for dst_label, src_label in label_hash.items():
            if label in src_label:
                return dst_label
        return label

    def get_item_path(self, index):  # 获取第index数据的路径
        return self.input_images[index]

    def __getitem__(self, index):  # return path
        graph = cv2.imread(self.input_images[index])
        return graph, self.info_list[index], self.input_images[index]

    # 实现 for i in dataset
    def __iter__(self):
        if self._index >= self.length:
            self._index = 0
            raise StopIteration
        self._index += 1
        return self.__getitem__(self._index - 1)
        # return iter(self.input_images)

    def __len__(self):
        return self.length


