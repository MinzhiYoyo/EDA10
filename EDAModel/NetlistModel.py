import json
import pickle

from PIL import Image
from logging import warning
from queue import Queue

import cv2
import numpy as np
from numpy import ndarray

# from Graph.EDADrawGraph import draw_graph
from Graph.EDANode import *
from EDAPublic.EDACV import EDARectangle, EDAPoint
from mos_detect import detect_mos
from bjt_detect import detect_bjt, binary_threshold
from cur_detect import detect_cur
from diode_detect import detect_diode

classify_er_model = pickle.load(open('./predict_function.pkl', 'rb'))

class NetlistModel:
    def __init__(self):
        self.mp4_out = None
        with open('config.json', 'r', encoding='utf8') as f:
            self.config = json.load(f)

        self.colors = self.config['colors']
        for k in self.colors.keys():
            self.colors[k] = np.array(self.colors[k])
        self.nodes: list[EDANode] = []
        self.nets: list[NetNode] = []
        self.netlist_components = self.config['netlist_components']

    def draw(self, title, graph, is_draw: bool = False, timeout: int = 1):
        if is_draw:
            cv2.imshow(title, graph)
            self.mp4_write(graph)
            cv2.waitKey(timeout)

    def save_tmp(self, title, graph, tmp_dir, is_draw):
        if is_draw:
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

        # # 将所有元器件上色
        # for index, item in enumerate(info):
        #     item_label = item['label']
        #
        #
        #     item_rectangle = item['points']
        #     component_color = self.colors['component_add'] + index
        #     component_color[1] = 0
        #     corners = item_rectangle.get_corners()
        #     corners = np.array([corner.to_numpy() for corner in corners])
        #     cv2.fillConvexPoly(rgb, corners, component_color.tolist())
        return rgb

    def crop_image_from_source(self, input_image, top_left_x, top_left_y, bottom_right_x, bottom_right_y):
        # 使用 opencv 裁剪图片 input_image
        # top_left_x, top_left_y, bottom_right_x, bottom_right_y 是裁剪区域的左上角和右下角坐标
        return input_image[top_left_y:bottom_right_y, top_left_x:bottom_right_x].copy()



    def crop_image(self, input_path, output_path, top_left_x, top_left_y, bottom_right_x, bottom_right_y):
        # if isinstance(input_path, str):
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
        self.save_tmp(f'origin_{png_file_name}', graph, tmp_dir, is_draw)
        gray = cv2.cvtColor(graph, cv2.COLOR_BGR2GRAY)
        self.draw(f'gray_{png_file_name}', gray, is_draw)
        self.save_tmp(f'gray_{png_file_name}', gray, tmp_dir, is_draw)
        _, binary = cv2.threshold(gray, binary_threshold, 255, cv2.THRESH_BINARY)
        self.draw(f'binary_{png_file_name}', binary, is_draw)
        self.save_tmp(f'binary_{png_file_name}', binary, tmp_dir, is_draw)
        # 腐蚀
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.erode(binary, kernel, iterations=1)
        self.draw(f'erode_{png_file_name}', binary, is_draw)
        self.save_tmp(f'erode_{png_file_name}', binary, tmp_dir, is_draw)
        rgb = cv2.cvtColor(binary, cv2.COLOR_GRAY2RGB)

        # 图像操作结束，开始填色
        # 将所有黑色的地方变成wire

        self.draw(f'rgb_{png_file_name}', rgb, is_draw)
        self.save_tmp(f'rgb_{png_file_name}', rgb, tmp_dir, is_draw)
        self.reset_rgb(binary, rgb, info)  # 画线

        self.draw(f'draw_component_{png_file_name}', rgb, is_draw)
        self.save_tmp(f'draw_component_{png_file_name}', rgb, tmp_dir, is_draw)

        return rgb, binary

    def draw_component(self,index, rgb, rect, is_draw):
        component_color = self.colors['component_add'] + index
        component_color[1] = 0
        corners = rect.get_corners()
        corners = np.array([corner.to_numpy() for corner in corners])
        cv2.fillConvexPoly(rgb, corners, component_color.tolist())
        self.draw(f'draw_component', rgb, is_draw)
        return rgb

    def label_to_type(self, label: str):
        for k, v in self.config['label_trans'].items():
            if label in v:
                return k
        return label

    # 执行一张图
    def run(self, png_file_path, png_file_name, graph: ndarray, info: list[dict], tmp_dir: str = None, is_draw: bool = False, animal_interval = 20):
        if graph is None:
            warning('图像为空')
            return
        if is_draw:
            self.mp4_init(tmp_dir, size=(graph.shape[1], graph.shape[0]), file_name = png_file_name.split('.')[0] + '.mp4')

        source_graph = graph.copy()

        graph, binary = self.image_preprocess(png_file_name, graph, info, tmp_dir, is_draw)

        # animal_interval = 20 # 每寻多少个点就画一次
        graph_poly = None
        graph_netlist = None
        if is_draw:
            graph_poly = source_graph.copy()
            graph_netlist = source_graph.copy()

        for i, item in enumerate(info):
            item_rectangle: EDARectangle = item['points']
            item_label = item['label']
            if item_label == 'bridge':
                self.draw_component(i, graph, item_rectangle, is_draw)  # 填充元器件颜色

        for i, item in enumerate(info):
            item_rectangle: EDARectangle = item['points']
            item_label = item['label']
            corners = item_rectangle.get_corners()
            corners = np.array([corner.to_numpy() for corner in corners])
            new_node = EDANode(node_type=self.label_to_type(item_label), id=len(self.nodes), rect = item_rectangle)

            if item_label != 'bridge':
                self.draw_component(i, graph, item_rectangle, is_draw)  # 填充元器件颜色
            try:
                if 'MOS' in item_label:
                    # 调用MOS端口识别
                    # self.crop_image(png_file_path, f'{tmp_dir}/tmp_mos.png', corners[0][0], corners[0][1], corners[2][0], corners[2][1])
                    crop_image = self.crop_image_from_source(source_graph, corners[0][0], corners[0][1], corners[2][0], corners[2][1])
                    mos_ports = detect_mos(crop_image)
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
                    # self.crop_image(png_file_path, f'{tmp_dir}/tmp_bjt.png', corners[0][0], corners[0][1], corners[2][0], corners[2][1])
                    crop_image = self.crop_image_from_source(source_graph, corners[0][0], corners[0][1], corners[2][0], corners[2][1])
                    bjt_ports = detect_bjt(crop_image)
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
                elif 'Cur' in item_label:
                    # 调用电流源端口识别
                    crop_image = self.crop_image_from_source(source_graph, corners[0][0], corners[0][1], corners[2][0], corners[2][1])
                    cur_ports = detect_cur(crop_image)
                    if cur_ports['In'] is not None: # 识别成功
                        new_node.set_direct_to_poly(cur_ports['In'], 'In')
                        new_node.set_direct_to_poly(cur_ports['Out'], 'Out')
                    elif cur_ports['IO'] == 'Horizontal':
                        new_node.set_direct_to_poly(EDANode.LEFT, 'In')
                        new_node.set_direct_to_poly(EDANode.RIGHT, 'Out')
                    else:
                        new_node.set_direct_to_poly(EDANode.UP, 'In')
                        new_node.set_direct_to_poly(EDANode.DOWN, 'Out')
                elif 'Diode' in item_label:
                    # 调用二极管端口识别
                    crop_image = self.crop_image_from_source(source_graph, corners[0][0], corners[0][1], corners[2][0], corners[2][1])
                    diode_ports = detect_diode(crop_image)
                    if diode_ports['In'] is not None: # 识别成功
                        new_node.set_direct_to_poly(diode_ports['In'], 'In')
                        new_node.set_direct_to_poly(diode_ports['Out'], 'Out')
                    elif diode_ports['IO'] == 'Horizontal':
                        new_node.set_direct_to_poly(EDANode.LEFT, 'In')
                        new_node.set_direct_to_poly(EDANode.RIGHT, 'Out')
                    else:
                        new_node.set_direct_to_poly(EDANode.UP, 'In')
                        new_node.set_direct_to_poly(EDANode.DOWN, 'Out')
                if is_draw:
                    for direction, poly in new_node.direct_to_poly.items():
                        if poly is not None:
                            point = item_rectangle.center()
                            if direction == EDANode.UP:
                                point.y = item_rectangle.left_up.y
                            elif direction == EDANode.DOWN:
                                point.y = item_rectangle.right_down.y
                            elif direction == EDANode.LEFT:
                                point.x = item_rectangle.left_up.x
                            elif direction == EDANode.RIGHT:
                                point.x = item_rectangle.right_down.x
                            cv2.putText(graph_poly, poly, (point.x, point.y), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 0, 255), 1)
                            # 用红色线框出来
                            cv2.polylines(graph_poly, [corners], True, (0, 0, 255), 1)
                            self.draw("draw_poly", graph_poly, is_draw=is_draw)
            except Exception as e:
                pass
            self.nodes.append(new_node)

        # 遍历所有图像，识别wire
        wire_set = set()
        color_wire = self.colors['wire'] # np.array
        for i in range(graph.shape[0]):
            for j in range(graph.shape[1]):
                if (graph[i][j] == color_wire).all():
                    wire_set.add(EDAPoint(j, i))

        # 将所有节点连成网络
        self.bfs(wire_set, graph, info, animal_interval, is_draw=is_draw)  # 将 self.nodes 连接起来了

        # 删除bridge节点
        self.remove_bridge() # 去除桥

        # 将节点间的关系创建成net
        self.create_net(info, graph, is_draw) # 创建网络

        # 生成网表
        netlist = self.to_netlist(graph_netlist, is_draw) # 生成 netlist
        netlist = self.predict_function(netlist) # 预测功能
        # 以人能够阅读的方式写入 json 文件，路径为 {tmp_dir}/test.json
        # with open(f'{tmp_dir}/{png_file_name.split(".")[0]}.json', 'w', encoding='utf8') as f:
        #     json.dump(netlist, f, ensure_ascii=False, indent=4)

        # if is_draw:
        #     draw_graph(netlist, png_file_name)

        if is_draw:
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            self.mp4_release()

        return netlist

    def bfs(self, wire_set: set, rbg: np.ndarray, info: list[dict], animal_interval = 20, is_draw = False):
        if isinstance(animal_interval, int):
            pass
        elif isinstance(animal_interval, float):
            assert 0 < animal_interval < 1, f"Invalid animal_interval {animal_interval}, must be in (0, 1)"
            animal_interval = int(animal_interval * len(wire_set))

        frame_counter = 0
        while len(wire_set) > 0:
            record_component_id_direction = [] # (id, direction, point)
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
                for next_point in next_points:  # 遍历当前点的上下左右四个点
                    if next_point.is_invalid(rbg):
                        continue

                    if next_point in wire_set:  # 如果下一个点是未遍历的点（线点）
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
                            next_direct = EDAPoint.get_direction(next_point, current_point)
                            if (next_id, next_direct) not in record_component_id_direction:
                                record_component_id_direction.append((next_id, next_direct, next_point))
                            # record_component_id_direction.append((next_id, next_direct))

            for i in range(len(record_component_id_direction)):
                for j in range(i + 1, len(record_component_id_direction)):
                    id_i = record_component_id_direction[i][0]
                    id_j = record_component_id_direction[j][0]
                    direct_i = record_component_id_direction[i][1]
                    direct_j = record_component_id_direction[j][1]
                    point_i = record_component_id_direction[i][2]
                    point_j = record_component_id_direction[j][2]

                    # 做一点过滤
                    if id_j == id_i:
                        continue
                        # distance_threshold = self.nodes[id_i].rect.get_width() + self.nodes[id_i].rect.get_height() + 1
                        # if point_i.euclidean_distance(point_j) <= distance_threshold:
                        #     continue

                    if record_component_id_direction[i] != record_component_id_direction[j]:
                        self.nodes[id_i].add_next(direct_i, (direct_j, id_j))
                        self.nodes[id_j].add_next(direct_j, (direct_i, id_i))

    # 将 dir2 的所有连接到 dir1 上
    def _connect_nodes(self,node_id: int, dir1: str, dir2:str):
        node = self.nodes[node_id]
        for next_direction, next_id in node.next_node[dir1]:
            # 删除self.nodes[next_id].next_node[next_direction]中的(node_id, dir1)
            # self.nodes[next_id].next_node[next_direction].remove((dir1, node_id))
            self.nodes[next_id].delete_next(next_direction, (dir1, node_id))
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

    def create_net(self, info: list[dict] = None, graph: np.ndarray = None, is_draw = False):
        node_length = len(self.nodes)
        self.nets.append(NetNode(0))
        def draw(id, direction = None, net_id = None, id_or_net_id = False):
            if is_draw:
                rec: EDARectangle = info[id]['points']
                # 在direction的中间写上 net_id
                center = rec.center()
                # 写上绿色的id，字体小一点
                if id_or_net_id:
                    cv2.putText(graph, str(id), (center.x, center.y), cv2.FONT_HERSHEY_SIMPLEX, 0.3, (0, 255, 255), 1)
                else:
                    text = str(net_id)
                    if direction == EDANode.UP:
                        center.y = rec.left_up.y
                    elif direction == EDANode.DOWN:
                        center.y = rec.right_down.y
                    elif direction == EDANode.LEFT:
                        center.x = rec.left_up.x
                    elif direction == EDANode.RIGHT:
                        center.x = rec.right_down.x
                    # 写上红色的字
                    cv2.putText(graph, text, (center.x, center.y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
                    pass
            self.draw("create_net", graph, is_draw=is_draw)

        for my_id in range(node_length):
            draw(my_id, id_or_net_id=True)
            if self.nodes[my_id].node_type == 'bridge':
                continue

            my_directions = [EDANode.UP, EDANode.DOWN, EDANode.LEFT, EDANode.RIGHT]


            for my_direction in my_directions:
                if len(self.nodes[my_id].next_node[my_direction]) == 0: # 如果这个方向没有连任何节点，则跳过
                    continue

                net_node = NetNode(len(self.nets))

                id_direction_set = set()
                # 新建一个队列
                q = Queue()
                q.put((my_id, my_direction))
                is_gnd = self.nodes[my_id].node_type == 'Gnd'
                while not q.empty():
                    cur_id, cur_direction = q.get()
                    for next_direction, next_id in self.nodes[cur_id].next_node[cur_direction]:
                        is_gnd = is_gnd or self.nodes[next_id].node_type == 'Gnd'
                        if (next_id, next_direction) not in id_direction_set:
                            id_direction_set.add((next_id, next_direction))
                            q.put((next_id, next_direction))

                set_net_id = 0 if is_gnd else net_node.id
                # 把 id_direction_set 中的所有元素的网络都设置成 net_node
                for the_id, the_direction in id_direction_set:
                    self.nodes[the_id].next_net[the_direction].append(set_net_id)
                    draw(the_id, the_direction, set_net_id, False)
                    self.nodes[the_id].next_node[the_direction] = []
                self.nets.append(net_node)

    def to_netlist(self, graph: np.ndarray, is_draw):
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
        random_poly = self.config['label_random_poly']
        random_poly_name = self.config['random_poly_name']
        for node_id in range(len(self.nodes)):
            if self.nodes[node_id].node_type not in self.netlist_components:
                continue
            component = {
                "component_type": self.nodes[node_id].node_type,
                "port_connection": {}
            }

            # 提取当前节点的连接信息
            # 分为两种，1. 需要随机生成极的，2. 需要确定极的
            # 1. 随机生成极的，那么就需要随机生成一个极
            # 2. 确定极的，如果有极，那么就正常输出，没有极，就不输出极，只输出节点即可
            if self.nodes[node_id].node_type in random_poly:
                self.nodes[node_id].random_poly(*random_poly_name)

            # 获取节点的连接信息
            connection_info_list = self.nodes[node_id].get_connection_info()
            for direction, poly, net_id in connection_info_list:
                component["port_connection"][poly] = str(self.nets[net_id])
                if is_draw:
                    info_text = f"{poly[:2]} {net_id:2d}"
                    center = self.nodes[node_id].rect.center()
                    if direction == EDANode.UP:
                        center.y = self.nodes[node_id].rect.left_up.y + 5
                    elif direction == EDANode.DOWN:
                        center.y = self.nodes[node_id].rect.right_down.y - 5
                    elif direction == EDANode.LEFT:
                        center.x = self.nodes[node_id].rect.left_up.x + 5
                    elif direction == EDANode.RIGHT:
                        center.x = self.nodes[node_id].rect.right_down.x - 5
                    # 画框
                    corners = self.nodes[node_id].rect.get_corners()
                    corners = np.array([corner.to_numpy() for corner in corners])
                    cv2.polylines(graph, [corners], True, (255, 0, 0), 1)
                    cv2.putText(graph, info_text, (center.x, center.y), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
                    self.draw("to_netlist", graph, is_draw=is_draw)

            result["ckt_netlist"].append(component)
        return result

    def predict_function(self, netlist):
        ckt_type_numer: list = self.config['ckt_type']
        components_number: list = self.config['netlist_components']
        a_x = [0] * len(components_number)
        for component in netlist['ckt_netlist']:
            component_index = components_number.index(component['component_type'])
            a_x[component_index] += 1
        x = np.array(a_x)
        y = classify_er_model.predict([x])
        netlist['ckt_type'] = ckt_type_numer[y[0]]
        return netlist



