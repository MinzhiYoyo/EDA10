import json
import queue
from logging import warning
from queue import Queue

import cv2
import numpy as np
from numpy import ndarray
from sympy.integrals.heurisch import components

from Graph.EDANode import *
from Public.EDACV import EDARectangle, EDAPoint


class NetlistModel:
    def __init__(self):
        self.mp4_out = None
        with open('config.json', 'r', encoding='utf8') as f:
            self.config = json.load(f)

        self.colors = self.config['colors']
        for k in self.colors.keys():
            self.colors[k] = np.array(self.colors[k])
        self.label_class = self.config['label_class']
        self.nodes = []

    def draw(self, title, graph, is_draw: bool = False, timeout: int = 1):
        if is_draw:
            cv2.imshow(title, graph)
            self.mp4_write(graph)
            cv2.waitKey(timeout)

    def save_tmp(self, title, graph, tmp_dir):
        cv2.imwrite(f'{tmp_dir}/{title}.png', graph)

    def mp4_init(self, tmp_dir, fps: int = 60, size: tuple[int, int] = (640, 480), file_name: str = 'output.mp4'):
        # 使用MPEG-4编码
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(f'{tmp_dir}/output.mp4', fourcc, fps, size)
        self.mp4_out = out

    def mp4_write(self, graph):
        if self.mp4_out is not None:
            self.mp4_out.write(graph)

    def mp4_release(self):
        # 保存视频
        if self.mp4_out is not None:
            self.mp4_out.release()

    def reset_rgb(self, binary, rgb, info):
        # 重置线
        for i in range(rgb.shape[0]):
            for j in range(rgb.shape[1]):
                if binary[i][j] == 0:
                    rgb[i][j] = self.colors['wire']

        # 将所有元器件上色
        for index, item in enumerate(info):
            item_rectangle = item['points']
            component_color = self.colors['component_add'] + index
            component_color[1] = 0
            corners = item_rectangle.get_corners()
            corners = np.array([corner.to_numpy() for corner in corners])
            cv2.fillConvexPoly(rgb, corners, component_color.tolist())
        return rgb

    def image_preprocess(self,png_file_name, graph: ndarray, info: list[dict], tmp_dir: str, is_draw: bool = False):
        """
        对一张图进行处理
        :param graph:
        :param info: [
            {
                "label": label,
                "points": EDARectangle
            }, ...
        ]
        :param tmp_dir:
        :return:
        """
        # 1. 对图进行灰度处理
        # 2. 对图进行二值化处理
        self.draw(f'origin_{png_file_name}', graph, is_draw)
        self.save_tmp(f'origin_{png_file_name}', graph, tmp_dir)
        gray = cv2.cvtColor(graph, cv2.COLOR_BGR2GRAY)
        self.draw(f'gray_{png_file_name}', gray, is_draw)
        self.save_tmp(f'gray_{png_file_name}', gray, tmp_dir)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        self.draw(f'binary_{png_file_name}', binary, is_draw)
        self.save_tmp(f'binary_{png_file_name}', binary, tmp_dir)
        # 腐蚀
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.erode(binary, kernel, iterations=1)
        self.draw(f'erode_{png_file_name}', binary, is_draw)
        self.save_tmp(f'erode_{png_file_name}', binary, tmp_dir)
        rgb = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)

        # 图像操作结束，开始填色
        # 将所有黑色的地方变成wire

        self.draw(f'rgb_{png_file_name}', rgb, is_draw)
        self.save_tmp(f'rgb_{png_file_name}', rgb, tmp_dir)
        self.reset_rgb(binary, rgb, info)

        self.draw(f'draw_wire_{png_file_name}', rgb, is_draw)
        self.save_tmp(f'draw_wire_{png_file_name}', rgb, tmp_dir)

        self.draw(f'draw_component_{png_file_name}', rgb, is_draw)
        self.save_tmp(f'draw_component_{png_file_name}', rgb, tmp_dir)

        return rgb, binary

    # 执行一张图
    def run(self, png_file_name, graph: ndarray, info: list[dict], tmp_dir: str, is_draw: bool = False, animal_interval: int = 20):
        if graph is None:
            warning('图像为空')
            return
        self.mp4_init(tmp_dir, size=(graph.shape[1], graph.shape[0]), file_name = png_file_name.split('.')[0] + '.mp4')
        graph, binary = self.image_preprocess(png_file_name, graph, info, tmp_dir, is_draw)

        # animal_interval = 20 # 每寻多少个点就画一次
        for i, item in enumerate(info):
            item_rectangle = item['points']
            corners = item_rectangle.get_corners()
            corners = np.array([corner.to_numpy() for corner in corners])
            item_label = item['label']
            self.nodes.append(
                eval(f"{self.label_class[item_label]}(i)")  # 只会返回None
            )

        for node in self.nodes:
            graph = self.bfs(node.id, graph, binary, info)
            self.draw(f'graph', graph, is_draw)


        if is_draw:
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            self.mp4_release()

    def bfs(self, start_node_id: int, rbg: np.ndarray, binary: np.ndarray, info: list[dict], animal_interval: int = 20):
        rect: EDARectangle = info[start_node_id]['points']

        start_nodes = {
            EDANode.UP: rect.get_edge(EDANode.UP),
            EDANode.DOWN: rect.get_edge(EDANode.DOWN),
            EDANode.LEFT: rect.get_edge(EDANode.LEFT),
            EDANode.RIGHT: rect.get_edge(EDANode.RIGHT),
        }
        corners = rect.get_corners()
        corners = np.array([corner.to_numpy() for corner in corners])
        component_close_color = self.colors['component_close']
        cv2.fillConvexPoly(rbg, corners, component_close_color.tolist())
        frame_counter = 0
        for direction, direction_start_points in start_nodes.items():
            q = Queue()
            for start_point in direction_start_points:
                q.put(start_point)
            while not q.empty():
                if frame_counter >= animal_interval:
                    self.draw("graph", rbg, is_draw=True)
                    frame_counter = 0
                frame_counter += 1
                current_point = q.get()
                # 删除这个点
                if current_point.is_invalid(rbg):  # 这个点无效
                    continue
                next_points = [current_point + EDAPoint(*direct_point) for direct_point in EDAPoint.DIRECTIONS_POINT]
                for next_point in next_points:
                    if next_point.is_invalid(rbg):
                        continue
                    next_point_color = rbg[next_point.y][next_point.x]
                    component_color_start = self.colors['component_add']
                    if (next_point_color == self.colors['wire']).all():
                        q.put(next_point)
                        rbg[next_point.y][next_point.x] = self.colors['wire_close'].tolist()
                    elif next_point_color[0] == next_point_color[2] and next_point_color[1] == 0 and next_point_color[0] >= component_color_start[0]:
                        # 遇到下一个元器件了
                        next_id = int(next_point_color[0] - component_color_start[0])
                        if next_id != start_node_id: # 不等于当前 id
                            next_rect: EDARectangle = info[next_id]['points']
                            next_direct = next_rect.direct(next_point)
                            self.nodes[start_node_id].add_next(direction, (next_direct, next_id))
                            self.nodes[next_id].add_next(next_direct, (direction, start_node_id))
        # 需要重置所有线路的颜色
        rbg = self.reset_rgb(binary, rbg, info)
        return rbg
