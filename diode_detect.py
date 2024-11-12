from PIL import Image, ImageDraw, ImageFont
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import sys
import cv2
from EDAPublic.EDACV import CV_UP, CV_DOWN, CV_LEFT, CV_RIGHT

result = {'IO': None, 'In': None, 'Out': None}
image_path = ''
from bjt_detect import binarize_image
def annotate_image(image_path, save_path, annotations):
    # 打开图像
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    
    # 使用truetype字体
    font_path = "DejaVuSansMono.ttf"  # 确保该路径下有合适的字体文件
    # font_path = "Arial.ttf"
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

# 降维
def convert_row(row):
    count_greater_equal = np.sum(row >= 128)
    # 返回 0 或 1
    return 1 if count_greater_equal >= 2 else 0

# def binarize_image(image_path, threshold=128):
#     image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE) if isinstance(image_path, str) else cv2.cvtColor(image_path, cv2.COLOR_BGR2GRAY)
#     _, binary_image = cv2.threshold(image, 200, 255, cv2.THRESH_BINARY)
#     return binary_image

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

def plot_ratios(image_path, save_path, column_black_ratios, column_white_ratios, row_black_ratios, row_white_ratios, column_peaks, row_peaks):
    # 绘制列直方图
    indices = np.arange(len(column_black_ratios))
    plt.figure(figsize=(12, 6))
    
    plt.subplot(1, 2, 1)
    plt.bar(indices, column_black_ratios, color='black', label='Black Ratio')
    plt.bar(indices, column_white_ratios, bottom=column_black_ratios, color='white', label='White Ratio')
    plt.scatter(column_peaks, column_black_ratios[column_peaks], color='red', label='Peaks')
    plt.xlabel('Column Index')
    plt.ylabel('Ratio')
    plt.title('Column Black and White Ratios')
    plt.legend()

    # 绘制行直方图
    indices = np.arange(len(row_black_ratios))
    
    plt.subplot(1, 2, 2)
    plt.bar(indices, row_black_ratios, color='black', label='Black Ratio')
    plt.bar(indices, row_white_ratios, bottom=row_black_ratios, color='white', label='White Ratio')
    plt.scatter(row_peaks, row_black_ratios[row_peaks], color='red', label='Peaks')
    plt.xlabel('Row Index')
    plt.ylabel('Ratio')
    plt.title('Row Black and White Ratios')
    plt.legend()

    plt.tight_layout()
    # plt.show()
    # plt.savefig(save_path)

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
    horizontal_bias = "left" if cx < w / 2 else "right"
    vertical_bias = "up" if cy < h / 2 else "down"

    # print("Centroid is biased towards", horizontal_bias, vertical_bias)
    return horizontal_bias, vertical_bias

def detect_diode(image_path):
    binary_array = binarize_image(image_path)
    column_black_ratios, column_white_ratios = calculate_column_ratios(binary_array)
    row_black_ratios, row_white_ratios = calculate_row_ratios(binary_array)
    # plot_ratios(column_black_ratios, column_white_ratios, row_black_ratios, row_white_ratios)

    # 从行列直方图中找最大值
    row_max = row_black_ratios.argmax()
    column_max = column_black_ratios.argmax()
    # 判断 row_max 和 column_max 哪个更接近中间位置
    height, width = binary_array.shape
    center_column = width // 2
    center_row = height // 2
    distance_column = abs(column_max - center_column)
    distance_row = abs(row_max - center_row)
    if distance_column < distance_row:
        result['IO'] = 'Vertical' # 上下
        row_peaks, _ = find_peaks(row_black_ratios, distance=width / 10, prominence=0.05, width=0.1)
        if len(row_peaks) > 3:
            # 获取峰值高度
            peak_values = row_black_ratios[row_peaks]
            # 找到最高的三个峰值索引
            top_three_indices = np.argsort(peak_values)[-3:]
            row_peaks = row_peaks[top_three_indices]
        # print(row_peaks)
        i = row_peaks[0]
        while i < row_peaks[1]:
            brush = column_max
            # 从中间向两边搜索，白色变黑色，直到遇到黑色像素
            while binary_array[i][brush] == 255:
                binary_array[i][brush] = 0
                brush += 1
            brush = column_max - 1
            while binary_array[i][brush] == 255:
                binary_array[i][brush] = 0
                brush -= 1
            i += 1
        if calculate_centroid(binary_array[row_peaks[0]:row_peaks[1]])[1] == 'up':
            result['In'] = CV_UP
            result['Out'] = CV_DOWN
        else:
            result['In'] = CV_DOWN
            result['Out'] = CV_UP
    else:
        result['IO'] = 'Horizontal' # 左右
        column_peaks, _ = find_peaks(column_black_ratios, distance=width / 10, prominence=0.05, width=0.1)
        if len(column_peaks) > 3:
            # 获取峰值高度
            peak_values = column_black_ratios[column_peaks]
            # 找到最高的三个峰值索引
            top_three_indices = np.argsort(peak_values)[-3:]
            column_peaks = column_peaks[top_three_indices]
        # print(column_peaks)
        i = column_peaks[0]
        while i < column_peaks[1]:
            brush = row_max
            # 从中间向两边搜索，白色变黑色，直到遇到黑色像素
            while binary_array[brush][i] == 255:
                binary_array[brush][i] = 0
                brush += 1
            brush = row_max - 1
            while binary_array[brush][i] == 255:
                binary_array[brush][i] = 0
                brush -= 1
            i += 1
        if calculate_centroid(binary_array[:, column_peaks[0]:column_peaks[1]+1])[0] == 'left':
            result['In'] = CV_LEFT
            result['Out'] = CV_RIGHT
        else:
            result['In'] = CV_RIGHT
            result['Out'] = CV_LEFT

    # save_path = image_path.replace('.png', '_histogram.png')  # 保存图片的路径
    # plot_ratios(image_path, save_path, column_black_ratios, column_white_ratios, row_black_ratios, row_white_ratios, column_peaks, row_peaks)

    # 将 binary_array 转换为 PIL 图像并保存
    # image = Image.fromarray(binary_array)
    # image.save(image_path.replace('.png', '_binary.png'))
    # print(result)

    # save_path = image_path.replace('.png', '_annotated.png')  # 保存图片的路径
    # annotate_image(image_path, save_path, result)

    return result

if __name__ == "__main__":
    try:
        image_path = sys.argv[1]
    except IndexError:
        print("Usage: python diode_detect.py <image_path>")
        sys.exit(1)
    detect_diode(image_path)