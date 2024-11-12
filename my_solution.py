import os.path
import sys
import time

from EDADataSet.EDADataset import EDADataset
from EDAModel.NetlistModel import NetlistModel


def solution(img_path: str) -> str:
    """
    赛题队伍实现这段代码提供自己的解决方案

    参数:
        img_path:
            图片地址

    返回:
        转换为赛题格式的python字典字符串
        案例：
            你的代码...
            ans = {"ckt_ckt_netlist": ...}  # type(ans) == dict
            return str(ans)
    """
    dataset = EDADataset(img_path, need_read_json=False)
    graph, info, file_path = dataset[0]
    netlist = NetlistModel()
    output_netlist = netlist.run(file_path, os.path.basename(file_path), graph, info, is_draw=False)
    return str(output_netlist)

if __name__ == '__main__':
    print(solution('./images/022.png'))
