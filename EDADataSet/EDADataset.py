import json
import os
from typing import Tuple, Any

import cv2
import numpy as np
from cv2 import Mat
from numpy import ndarray, dtype

from Public.EDACV import EDAPoint, EDARectangle


class EDADataset:
    def __init__(self, input_dir:str):
        self.input_images = []
        self.length = 0
        for file_name in os.listdir(input_dir):
            if not file_name.endswith('.png'):
                continue
            self.input_images.append(os.path.join(input_dir, file_name))
            self.length += 1
        with open('./config.json', 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        self._index = 0

    def read_json(self, json_data: dict) -> list:  # 读取json文件
        info = []
        for shape in json_data['shapes']:
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

    def label_trans(self, label: str):
        label_hash = self.config['label_trans']
        for dst_label, src_label in label_hash.items():
            if label in src_label:
                return dst_label
        return label

    def get_item_path(self, index):  # 获取第index数据的路径
        return self.input_images[index]

    def __getitem__(self, index) -> tuple[ndarray | Any, list, str]:  # return path
        graph = cv2.imread(self.input_images[index])
        with open(self.input_images[index].replace('.png', '.json'), 'r') as f:
            json_data = json.load(f)
            info = self.read_json(json_data)
        return graph, info, self.input_images[index]

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


