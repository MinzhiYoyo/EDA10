import os.path
import sys

from EDADataSet.EDADataset import EDADataset
from EDAModel.NetlistModel import NetlistModel


def run_main(data_dir: str = './image.png'):
    tmp_dir = './tmp/'
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    dataset = EDADataset(data_dir)
    netlist = NetlistModel()

    graph, info, file_path = dataset[0]

    netlist.run(os.path.basename(file_path), graph, info, tmp_dir, is_draw=False)


if __name__ == "__main__":
    if sys.argv.__len__() == 2:
        run_main(sys.argv[1])
    else:
        run_main()

