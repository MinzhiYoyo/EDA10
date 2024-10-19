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

    graph, info, file_path = dataset[46]

    netlist.run(os.path.basename(file_path), graph, info, tmp_dir, is_draw=True)


if __name__ == "__main__":
    main()

# import cv2
# import json
#
# import numpy as np
#
# img = cv2.imread('./data/0.png')
# json_data = json.load(open('./data/0.json', 'r'))
# cv2.imshow('img', img)
# cv2.waitKey(0)
# # 二值化
# gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
# cv2.imshow('binary', binary)
# cv2.waitKey(0)
# img = binary
# # 遍历 json_data['shapes']，绘制多边形
# for shape in json_data['shapes']:
#     point_1 = [int(shape['points'][0][0]), int(shape['points'][0][1])]
#     point_2 = [int(shape['points'][1][0]), int(shape['points'][1][1])]
#     label = shape['label']
#     cv2.rectangle(img, (int(point_1[0]), int(point_1[1])), (int(point_2[0]), int(point_2[1])), (0, 255, 0), 2)
#     # 填充这个矩形，用多边形填充法
#     cv2.fillConvexPoly(img, np.array([point_1, [point_2[0], point_1[1]], point_2, [point_1[0], point_2[1]]]), (0, 255, 0))
#
# cv2.imshow('img', img)
# cv2.waitKey(0)
#
# # 对img做霍夫变换
# # gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# edges = cv2.Canny(gray, 50, 150, apertureSize=3)
# lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
# for line in lines:
#     rho, theta = line[0]
#     a = np.cos(theta)
#     b = np.sin(theta)
#     x0 = a * rho
#     y0 = b * rho
#     x1 = int(x0 + 1000 * (-b))
#     y1 = int(y0 + 1000 * a)
#     x2 = int(x0 - 1000 * (-b))
#     y2 = int(y0 - 1000 * a)
#     cv2.line(img, (x1, y1), (x2, y2), (0, 0, 255), 2)
#
# cv2.imshow('line', img)
# cv2.waitKey(0)
#
# cv2.destroyWindow('img')
# cv2.destroyWindow('binary')



# import json
# import os
#
# files_name = os.listdir('./data/')
# for file_name in files_name:
#     if not file_name.endswith('.json'):
#         continue
#     json_data = json.load(open(f'./data/{file_name}', 'r'))
#     for shape in json_data['shapes']:
#         points = shape['points']
#         for point in points:
#             print(point[0], point[1])

