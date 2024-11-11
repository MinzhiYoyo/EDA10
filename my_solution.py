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

    for file_index in range(len(dataset)):
        graph, info, file_path = dataset[file_index]
        print(f"开始转换{os.path.basename(file_path)}")
        netlist = NetlistModel()
        output_netlist = netlist.run(file_path, os.path.basename(file_path), graph, info, tmp_dir, is_draw=False)
        with open(os.path.basename(file_path).replace("png","txt"), "w") as file:
            file.write(str(output_netlist))
        print(f"完成转换{os.path.basename(file_path)}")


if __name__ == "__main__":
    if sys.argv.__len__() == 2:
        run_main(sys.argv[1])
    else:
        run_main()