import json
import random
from PIL import Image
from logging import warning
from queue import Queue

import cv2
import numpy as np
from numpy import ndarray
from sympy.integrals.heurisch import components

from Graph.EDADrawGraph import draw_graph
from Graph.EDANode import *
from EDAPublic.EDACV import EDARectangle, EDAPoint
from mos_detect import detect_mos
from bjt_detect import detect_bjt


class NetlistModel:
    def __init__(self):
        self.mp4_out = None
        with open('config.json', 'r', encoding='utf8') as f:
            self.config = json.load(f)

        self.colors = self.config['colors']
        for k in self.colors.keys():
            self.colors[k] = np.array(self.colors[k])
        self.label_class = self.config['label_class']
        self.nodes: list[EDANode] = []
        self.nets: list[NetNode] = []
        self.netlist_components = self.config['netlist_components']

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
    
    def crop_image(self, input_path, output_path, top_left_x, top_left_y, bottom_right_x, bottom_right_y):
        # 打开输入图片
        with Image.open(input_path) as img:
            # 定义裁剪区域
            crop_area = (top_left_x, top_left_y, bottom_right_x, bottom_right_y)
            
            # 裁剪图片
            cropped_img = img.crop(crop_area)
            
            # 保存裁剪后的图片
            cropped_img.save(output_path)

    def image_preprocess(self, png_file_name, graph: ndarray, info: list[dict], tmp_dir: str, is_draw: bool = False):
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
    def run(self, png_file_path, png_file_name, graph: ndarray, info: list[dict], tmp_dir: str, is_draw: bool = False, animal_interval: int = 20):
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
            new_node = EDANode(node_type=item_label, id=i)
            if 'MOS' in item_label:
                # 调用MOS端口识别
                self.crop_image(png_file_path, f'{tmp_dir}/tmp_mos.png', corners[0][0], corners[0][1], corners[2][0], corners[2][1])
                mos_ports = detect_mos(f'{tmp_dir}/tmp_mos.png')
                if mos_ports['Gate'] is not None: # 识别成功
                    new_node.set_direct_to_poly(mos_ports['Source'], 'Source')
                    new_node.set_direct_to_poly(mos_ports['Gate'], 'Gate')
                    new_node.set_direct_to_poly(mos_ports['Drain'], 'Drain')
                elif mos_ports['DS'] == 'Vertical': # Drain 和 Source 是上下方向，但 Gate 没识别出来
                    new_node.set_direct_to_poly(EDANode.UP, 'Source')
                    new_node.set_direct_to_poly(EDANode.LEFT, 'Gate') # 随便猜一个方向
                    new_node.set_direct_to_poly(EDANode.DOWN, 'Drain')
                else: # Drain 和 Source 是左右方向，但 Gate 没识别出来，或者全部识别失败
                    new_node.set_direct_to_poly(EDANode.LEFT, 'Source')
                    new_node.set_direct_to_poly(EDANode.UP, 'Gate') # 随便猜一个方向
                    new_node.set_direct_to_poly(EDANode.RIGHT, 'Drain')
            elif 'NPN' in item_label or 'PNP' in item_label:
                # 调用BJT端口识别
                self.crop_image(png_file_path, f'{tmp_dir}/tmp_bjt.png', corners[0][0], corners[0][1], corners[2][0], corners[2][1])
                bjt_ports = detect_bjt(f'{tmp_dir}/tmp_bjt.png')
                if bjt_ports['Base'] is not None: # 识别成功
                    new_node.set_direct_to_poly(bjt_ports['Base'], 'Base')
                    new_node.set_direct_to_poly(bjt_ports['Emitter'], 'Emitter')
                    new_node.set_direct_to_poly(bjt_ports['Collector'], 'Collector')
                elif bjt_ports['EC'] == 'Vertical': # Emitter 和 Collector 是上下方向，但 Base 没识别出来
                    new_node.set_direct_to_poly(EDANode.UP, 'Base')
                    new_node.set_direct_to_poly(EDANode.LEFT, 'Emitter') # 随便猜一个方向
                    new_node.set_direct_to_poly(EDANode.DOWN, 'Collector')
                else: # Emitter 和 Collector 是左右方向，但 Base 没识别出来，或者全部识别失败
                    new_node.set_direct_to_poly(EDANode.LEFT, 'Base')
                    new_node.set_direct_to_poly(EDANode.UP, 'Emitter') # 随便猜一个方向
                    new_node.set_direct_to_poly(EDANode.RIGHT, 'Collector')

            self.nodes.append(new_node)

        # 遍历所有图像，识别wire
        wire_set = set()
        color_wire = self.colors['wire'] # np.array
        for i in range(graph.shape[0]):
            for j in range(graph.shape[1]):
                if (graph[i][j] == color_wire).all():
                    wire_set.add(EDAPoint(j, i))

        self.bfs(wire_set, graph, info, animal_interval, is_draw=is_draw)  # 将 self.nodes 连接起来了
        self.remove_bridge() # 去除桥

        self.create_net() # 创建网络
        netlist = self.to_netlist() # 生成 netlist
        # 以人能够阅读的方式写入 json 文件，路径为 {tmp_dir}/test.json
        with open(f'{tmp_dir}/{png_file_name.split(".")[0]}.json', 'w', encoding='utf8') as f:
            json.dump(netlist, f, ensure_ascii=False, indent=4)

        if is_draw:
            draw_graph(netlist, int(png_file_name.split(".")[0]))

        if is_draw:
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            self.mp4_release()

        return netlist

    def bfs(self, wire_set: set, rbg: np.ndarray, info: list[dict], animal_interval: int = 20, is_draw = False):
        frame_counter = 0
        while len(wire_set) > 0:
            record_component_id_direction = [] # (id, direction)
            start_point = wire_set.pop()
            q = Queue()
            q.put(start_point)
            rbg[start_point.y][start_point.x] = self.colors['wire_close'].tolist()
            while not q.empty():
                if frame_counter >= animal_interval:
                    self.draw("graph", rbg, is_draw=is_draw)
                    frame_counter = 0
                frame_counter += 1
                current_point = q.get()
                next_points = [current_point + EDAPoint(*direct_point) for direct_point in EDAPoint.DIRECTIONS_POINT]
                for next_point in next_points:
                    if next_point.is_invalid(rbg):
                        continue
                    if next_point in wire_set:
                        wire_set.remove(next_point)
                        q.put(next_point)
                        rbg[next_point.y][next_point.x] = self.colors['wire_close'].tolist()
                    else:
                        next_point_color = rbg[next_point.y][next_point.x]
                        component_color_start = self.colors['component_add']
                        if next_point_color[0] == next_point_color[2] and next_point_color[1] == 0 and next_point_color[0] >= component_color_start[0]:
                            # 遇到下一个元器件了
                            next_id = int(next_point_color[0] - component_color_start[0])
                            next_rect: EDARectangle = info[next_id]['points']
                            next_direct = next_rect.direct(next_point)
                            record_component_id_direction.append((next_id, next_direct))
            # 开始连接
            for i in range(len(record_component_id_direction)):
                for j in range(i + 1, len(record_component_id_direction)):
                    id_i = record_component_id_direction[i][0]
                    id_j = record_component_id_direction[j][0]
                    direct_i = record_component_id_direction[i][1]
                    direct_j = record_component_id_direction[j][1]
                    if record_component_id_direction[i] != record_component_id_direction[j]:
                        self.nodes[id_i].add_next(direct_i, (direct_j, id_j))
                        self.nodes[id_j].add_next(direct_j, (direct_i, id_i))

    # 将 dir2 的所有连接到 dir1 上
    def _connect_nodes(self,node_id: int, dir1: str, dir2:str):
        node = self.nodes[node_id]
        for next_direction, next_id in node.next_node[dir1]:
            # 删除self.nodes[next_id].next_node[next_direction]中的(node_id, dir1)
            self.nodes[next_id].next_node[next_direction].remove((dir1, node_id))
            # 添加 node.next_node[dir2]中的所有元素到 self.nodes[next_id].next_node[next_direction]中
            for next_next_direction, next_next_id in node.next_node[dir2]:
                self.nodes[next_id].add_next(next_direction, (next_next_direction, next_next_id))


    def remove_bridge(self): # 移除桥
        for i in range(len(self.nodes)):
            if self.nodes[i].node_type == 'bridge':
                self._connect_nodes(i, EDANode.UP, EDANode.DOWN)
                self._connect_nodes(i, EDANode.DOWN, EDANode.UP)
                self._connect_nodes(i, EDANode.LEFT, EDANode.RIGHT)
                self._connect_nodes(i, EDANode.RIGHT, EDANode.LEFT)

    def create_net(self):
        node_length = len(self.nodes)

        for i in range(node_length):
            if self.nodes[i].node_type == 'bridge':
                continue
            my_directions = [EDANode.UP, EDANode.DOWN, EDANode.LEFT, EDANode.RIGHT]
            for my_direction in my_directions:
                if len(self.nodes[i].next_node[my_direction]) == 0: # 如果这个方向没有连任何节点，则跳过
                    continue
                self.nets.append(NetNode(len(self.nets)))
                self.nodes[i].next_net[my_direction] = len(self.nets) - 1
                for next_direction, next_id in self.nodes[i].next_node[my_direction]:
                    self.nodes[next_id].next_net[next_direction] = len(self.nets) - 1
                    self.nodes[next_id].next_node[next_direction] = []
                self.nodes[i].next_node[my_direction] = []

    def to_netlist(self):
        """
        {
            "ckt_type": "Unkown", # 电路类型预测
            "ckt_netlist": [
                {
                    "component_type": "R1", # 元件类型
                    "port_connection" {
                        "positive": 1, # 正极
                        "negative": 2, # 负极
                    }
                },
                ...
        }
        :return: dict
        """
        result = {
            "ckt_type": random.choice(self.config['ckt_type']),
            "ckt_netlist": []
        }
        for node_id in range(len(self.nodes)):
            if self.nodes[node_id].node_type not in self.netlist_components:
                continue
            component = {
                "component_type": self.nodes[node_id].node_type,
                "port_connection": {}
            }
            if(self.nodes[node_id].node_type in self.config['label_dual_port']): # 处理双端口元件被识别错端口数量的潜在问题
                self.nodes[node_id].process_directions()
            ports = []
            for direction in [EDANode.UP, EDANode.DOWN, EDANode.LEFT, EDANode.RIGHT]:
                dir_to_ports = [p for p, n in self.nodes[node_id].next_net.items() if n is not None]
                self.nodes[node_id].set_direct_to_poly(dir_to_ports, self.config['label_netlist_port'][self.nodes[node_id].node_type])
                port_name, next_net_id = self.nodes[node_id].get_port_name(direction)
                if port_name is None or next_net_id is None or port_name in [EDANode.UP, EDANode.DOWN, EDANode.LEFT, EDANode.RIGHT]:
                    continue
                component["port_connection"][port_name] = str(self.nets[next_net_id])
                if port_name == 'Source':
                    component["port_connection"]["Body"] = str(self.nets[next_net_id])
            result["ckt_netlist"].append(component)
        return result

