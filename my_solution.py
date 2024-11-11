import os.path
import sys

from EDADataSet.EDADataset import EDADataset
from EDAModel.NetlistModel import NetlistModel

run_index = 0

def run_main(data_dir: str = './image.png'):
    tmp_dir = './tmp/'
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    dataset = EDADataset(data_dir, need_read_json=False)
    netlist = NetlistModel()

    graph, info, file_path = dataset[run_index]

    return netlist.run(file_path, os.path.basename(file_path), graph, info, tmp_dir, is_draw=False)

# 示例solution函数（仅用于说明）
def solution(case_image):
    # 读入一张电路图
    image = case_image 

    # case_image是二进制图像编码，可通过下面的方式转存为png格式
    # 假设输出图像文件路径为case_image_path
    case_image_path = 'case_image.png'
    with open(case_image_path, 'wb') as img_file:
        img_file.write(image)
    # 当不需要输出图像文件时，可以注释掉这段的代码

    netlist_result = run_main(case_image_path)
    
    # 经过一系列算法处理，得到电路功能和网表

    # ......
    # ......
    # ......

    # 假设得到的结果为：(这里用的是case_4的例子)
    '''
    ckt_type = 'DIDO-Amplifier'
    ckt_netlist = [{'component_type': 'NMOS',
                  'port_connection': {'Drain': 'voutp',
                                      'Gate': 'vin',
                                      'Source': 'net1'}},
                 {'component_type': 'NMOS',
                  'port_connection': {'Drain': 'voutn',
                                      'Gate': 'vip',
                                      'Source': 'net1'}},
                 {'component_type': 'PMOS',
                  'port_connection': {'Drain': 'voutp',
                                      'Gate': 'vcmfb',
                                      'Source': 'vdd!'}},
                 {'component_type': 'PMOS',
                  'port_connection': {'Drain': 'voutn',
                                      'Gate': 'vcmfb',
                                      'Source': 'vdd!'}},
                 {'component_type': 'Current',
                  'port_connection': {'In': 'net1', 'Out': '0'}}]
    '''
    return netlist_result