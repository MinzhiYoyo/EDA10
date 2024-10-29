import os.path

from EDADataSet.EDADataset import EDADataset
from EDAModel.NetlistModel import NetlistModel


def main():
    data_dir = './data/'
    tmp_dir = 'D:\\codes\\EDA10\\EDA10\\tmp'
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    dataset = EDADataset(data_dir)
    netlist = NetlistModel()

    graph, info, file_path = dataset[683]

    netlist.run(os.path.basename(file_path), graph, info, tmp_dir, is_draw=True)


if __name__ == "__main__":
    main()

