##########################################################
# 输入：图片路径
# 输出：字典，包含三个键值对
#       EC：发射极和集电极是垂直方向（Vertical）或水平方向（Horizontal）
#       Emitter：发射极的位置（Left/Right/Up/Down）
#       Collector：集电极的位置（Left/Right/Up/Down）
#       Base：基极的位置（Left/Right/Up/Down）
# 调用方法：python bjt_detect.py <image_path>
##########################################################
import queue

from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import matplotlib.pyplot as plt
import sys

from EDAPublic.EDACV import CV_UP, CV_DOWN, CV_LEFT, CV_RIGHT
result = {'EC': None, 'Emitter': None, 'Collector': None, 'Base': None}
image_path = ''
binary_threshold = 175
def bfs_remove_zi(image):
    # 传入的是 image，其中，0表示前景，255表示背景，我们需要移除部分前景
    point_set = set()
    h, w = image.shape
    for i in range(h):
        for j in range(w):
            if image[i][j] == 0:
                point_set.add((i, j))
    # 随机选择一个点
    while len(point_set) > 0:
        start = point_set.pop()
        # 新建队列
        q = queue.Queue()
        q.put(start)
        record_to_edge = 0
        record_remove_point = set()
        record_remove_point.add(start)
        while not q.empty():
            cur = q.get()
            nex = [(cur[0] - 1, cur[1]), (cur[0] + 1, cur[1]), (cur[0], cur[1] - 1), (cur[0], cur[1] + 1)]
            for n in nex:
                if n in point_set:
                    q.put(n)
                    point_set.remove(n)
                    record_remove_point.add(n)
                elif n[0] < 0 or n[0] >= h or n[1] < 0 or n[1] >= w:
                    record_to_edge += 1
        if record_to_edge < 2:
            for p in record_remove_point:
                image[p[0]][p[1]] = 255
    return image



# 降维
def convert_row(row):
    count_greater_equal = np.sum(row >= 128)
    # 返回 0 或 1
    return 1 if count_greater_equal >= 2 else 0

def binarize_image(image_path):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE) if isinstance(image_path, str) else cv2.cvtColor(image_path, cv2.COLOR_BGR2GRAY)
    _, binary_image = cv2.threshold(image, binary_threshold, 255, cv2.THRESH_BINARY)
    # cv2.imshow('binary_image_bjt_mos', binary_image)
    # 统计黑色占比，如果占比过小，就腐蚀
    if np.sum(binary_image == 0) / binary_image.size < 0.25:
        kernel = np.ones((5, 5), np.uint8)
        binary_image = cv2.erode(binary_image, kernel, iterations=1)
    # cv2.imshow('binary_image_bjt_mos', binary_image)
        binary_image = bfs_remove_zi(binary_image)
    # cv2.imshow('binary_image_bjt_mos', binary_image)
    # cv2.waitKey(0)
    return binary_image

def calculate_symmetry(binary_image):
    h, w = binary_image.shape
    mid_w = w // 2
    mid_h = h // 2

    # 左右对称性
    left_half = binary_image[:, :mid_w]
    right_half = cv2.flip(binary_image[:, mid_w:], 1)
    if left_half.shape[1] != right_half.shape[1]:
        right_half = right_half[:, :left_half.shape[1]]

    lr_symmetry = np.sum(left_half == right_half) / left_half.size

    # 上下对称性
    top_half = binary_image[:mid_h, :]
    bottom_half = cv2.flip(binary_image[mid_h:, :], 0)
    if top_half.shape[0] != bottom_half.shape[0]:
        bottom_half = bottom_half[:top_half.shape[0], :]

    ud_symmetry = np.sum(top_half == bottom_half) / top_half.size

    return lr_symmetry, ud_symmetry

def calculate_centroid(binary_image):
    h, w = binary_image.shape
    # 黑色像素为1，白色像素为0
    black_pixels = 255 - binary_image
    M = cv2.moments(black_pixels, binaryImage=True)
    if M["m00"] != 0:
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
    else:
        cx, cy = w // 2, h // 2

    # 判断重心方向
    horizontal_bias = CV_LEFT if cx < w / 2 else CV_RIGHT
    vertical_bias = CV_UP if cy < h / 2 else CV_DOWN

    return horizontal_bias, vertical_bias

def calculate_column_ratios(binary_array):
    # 计算每列黑白像素的比例
    height, width = binary_array.shape
    black_ratios = np.sum(binary_array == 0, axis=0) / height
    white_ratios = np.sum(binary_array == 1, axis=0) / height
    return black_ratios, white_ratios

def calculate_row_ratios(binary_array):
    # 计算每行黑白像素的比例
    height, width = binary_array.shape
    black_ratios = np.sum(binary_array == 0, axis=1) / width
    white_ratios = np.sum(binary_array == 1, axis=1) / width
    return black_ratios, white_ratios

def plot_ratios(column_black_ratios, column_white_ratios, row_black_ratios, row_white_ratios):
    global image_path
    # 绘制列直方图
    indices = np.arange(len(column_black_ratios))
    plt.figure(figsize=(12, 6))
    
    plt.subplot(1, 2, 1)
    plt.bar(indices, column_black_ratios, color='black', label='Black Ratio')
    plt.bar(indices, column_white_ratios, bottom=column_black_ratios, color='white', label='White Ratio')
    plt.xlabel('Column Index')
    plt.ylabel('Ratio')
    plt.title('Column Black and White Ratios')
    plt.legend()

    # 绘制行直方图
    indices = np.arange(len(row_black_ratios))
    
    plt.subplot(1, 2, 2)
    plt.bar(indices, row_black_ratios, color='black', label='Black Ratio')
    plt.bar(indices, row_white_ratios, bottom=row_black_ratios, color='white', label='White Ratio')
    plt.xlabel('Row Index')
    plt.ylabel('Ratio')
    plt.title('Row Black and White Ratios')
    plt.legend()

    plt.tight_layout()
    # plt.show()
    plt.savefig(image_path.replace('.png', '_histogram.png'))

def annotate_image(image_path, save_path, annotations):
    # 打开图像
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    
    # 使用truetype字体
    font_path = "DejaVuSansMono.ttf"  # 确保该路径下有合适的字体文件
    font = ImageFont.truetype(font_path, size=20)
    
    # 获取图像尺寸
    width, height = image.size
    
    # 根据字典在对应的边上写入文字
    if CV_LEFT in annotations.values():
        text = [k for k, v in annotations.items() if v == CV_LEFT][0]
        draw.text((10, height / 2), text, font=font, fill="red")

    if CV_RIGHT in annotations.values():
        text = [k for k, v in annotations.items() if v == CV_RIGHT][0]
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text((width - text_width - 10, height / 2), text, font=font, fill="red")

    if CV_UP in annotations.values():
        text = [k for k, v in annotations.items() if v == CV_UP][0]
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text(((width - text_width) / 2, 10), text, font=font, fill="red")
        
    if CV_DOWN in annotations.values():
        text = [k for k, v in annotations.items() if v == CV_DOWN][0]
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.text(((width - text_width) / 2, height - text_height - 10), text, font=font, fill="red")

    # 保存修改后的图像
    image.save(save_path)

def detect_bjt(image_path):
    binary_image = binarize_image(image_path)
    lr_symmetry, ud_symmetry = calculate_symmetry(binary_image)
    column_black_ratios, column_white_ratios = calculate_column_ratios(binary_image)
    row_black_ratios, row_white_ratios = calculate_row_ratios(binary_image)

    horizontal_bias, vertical_bias = calculate_centroid(binary_image)
    # print(f"Centroid is biased to the {horizontal_bias} and {vertical_bias}.")

    # 比较对称性
    if lr_symmetry > ud_symmetry:
        # print("EC horizontal")
        result['EC'] = 'Horizontal'
        if horizontal_bias == CV_LEFT:
            result['Emitter'] = CV_LEFT
            result['Collector'] = CV_RIGHT
        else:
            result['Emitter'] = CV_RIGHT
            result['Collector'] = CV_LEFT
        if vertical_bias == CV_UP:
            result['Base'] = CV_UP
        else:
            result['Base'] = CV_DOWN
    else:
        # print("EC vertical")
        result['EC'] = 'Vertical'
        if vertical_bias == CV_UP:
            result['Emitter'] = CV_UP
            result['Collector'] = CV_DOWN
        else:
            result['Emitter'] = CV_DOWN
            result['Collector'] = CV_UP
        if horizontal_bias == CV_LEFT:
            result['Base'] = CV_LEFT
        else:
            result['Base'] = CV_RIGHT
    
    # print(result)
    # save_path = image_path.replace('.png', '_annotated.png')  # 保存图片的路径
    # annotate_image(image_path, save_path, result)
    # plot_ratios(column_black_ratios, column_white_ratios, row_black_ratios, row_white_ratios)

    return result

if __name__ == "__main__":
    try:
        image_path = sys.argv[1]
    except IndexError:
        print("Usage: python bjt_detect.py <image_path>")
        sys.exit(1)
    detect_bjt(image_path)