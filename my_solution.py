import os.path
import sys
import time

from EDADataSet.EDADataset import EDADataset
from EDAModel.NetlistModel import NetlistModel

def run_main(data_dir: str = './image.png'):
    tmp_dir = './tmp/'
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    dataset = EDADataset(data_dir, need_read_json=False)

    for file_index in range(len(dataset)):
        graph, info, file_path = dataset[file_index]
        print(f"开始转换{os.path.basename(file_path)}")
        netlist = NetlistModel()
        output_netlist = netlist.run(file_path, os.path.basename(file_path), graph, info, tmp_dir, is_draw=False)
        with open("generate/" + os.path.basename(file_path).replace("png","txt"), "w") as file:
            file.write(str(output_netlist))
        print(f"完成转换{os.path.basename(file_path)}")

def transform(data_dir: str = './image.png', tag: str = '.'):
    tmp_dir = './tmp/'
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    dataset = EDADataset(data_dir, need_read_json=False)
    if tag is not None:
        print(f"开始转换`{tag}`: ", end="")
        start_time = time.time()
    for file_index in range(len(dataset)):
        t1 = time.time() if tag is not None else 0
        graph, info, file_path = dataset[file_index]
        netlist = NetlistModel()
        output_netlist = netlist.run(file_path, os.path.basename(file_path), graph, info, tmp_dir, is_draw=False)
        with open(os.path.basename(file_path).replace("png","txt"), "w") as file:
            file.write(str(output_netlist))
        t2 = time.time() if tag is not None else 0
        if tag is not None:
            average_time = (t2 - start_time) / (file_index + 1)
            pass_time = t2 - start_time
            pred_time = (len(dataset) - file_index - 1) * average_time
            # 转换成时分秒
            pass_time_str = time.strftime("%H:%M:%S", time.gmtime(pass_time))
            pred_time_str = time.strftime("%H:%M:%S", time.gmtime(pred_time))
            print(f"\r转换`{tag}` 中: {file_index:4d}/{len(dataset):4d}[{file_index/ len(dataset) * 100 :.2f}%] [{int((t2-t1)*1000):3d}ms/it] {pass_time_str} < {pred_time_str}", end="")
    if tag is not None:
        end_time = time.time()
        all_time_str = time.strftime("%H:%M:%S", time.gmtime(end_time - start_time))
        print(f"\r转换`{tag}`完成: [{all_time_str}]")
    

if __name__ == "__main__":
    if sys.argv.__len__() == 2:
        transform(sys.argv[1])
    else:
        transform()