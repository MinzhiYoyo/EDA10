from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import matplotlib.pyplot as plt
import sys

result = {}
image_path = 'test6.png'  # 替换为你的图片路径

def binarize_image(image_path):
    # 读取图像
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # 二值化
    _, binary_image = cv2.threshold(image, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
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
    horizontal_bias = "left" if cx < w / 2 else "right"
    vertical_bias = "up" if cy < h / 2 else "down"

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
    if 'Left' in annotations.values():
        text = [k for k, v in annotations.items() if v == 'Left'][0]
        draw.text((10, height / 2), text, font=font, fill="red")

    if 'Right' in annotations.values():
        text = [k for k, v in annotations.items() if v == 'Right'][0]
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text((width - text_width - 10, height / 2), text, font=font, fill="red")

    if 'Up' in annotations.values():
        text = [k for k, v in annotations.items() if v == 'Up'][0]
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        draw.text(((width - text_width) / 2, 10), text, font=font, fill="red")
        
    if 'Down' in annotations.values():
        text = [k for k, v in annotations.items() if v == 'Down'][0]
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.text(((width - text_width) / 2, height - text_height - 10), text, font=font, fill="red")

    # 保存修改后的图像
    image.save(save_path)

def detect_bjt(argv):
    try:
        global image_path
        try:
            image_path = argv[1]
        except IndexError:
            print("Usage: python bjt_detect.py <image_path>")
            sys.exit(1)
        binary_image = binarize_image(image_path)
        lr_symmetry, ud_symmetry = calculate_symmetry(binary_image)
        column_black_ratios, column_white_ratios = calculate_column_ratios(binary_image)
        row_black_ratios, row_white_ratios = calculate_row_ratios(binary_image)

        horizontal_bias, vertical_bias = calculate_centroid(binary_image)
        print(f"Centroid is biased to the {horizontal_bias} and {vertical_bias}.")

        # 比较对称性
        if lr_symmetry > ud_symmetry:
            print("EC horizontal")
            if horizontal_bias == "left":
                result['Emitter'] = 'Left'
                result['Collector'] = 'Right'
            else:
                result['Emitter'] = 'Right'
                result['Collector'] = 'Left'
            if vertical_bias == "up":
                result['Base'] = 'Up'
            else:
                result['Base'] = 'Down'
        else:
            print("EC vertical")
            if vertical_bias == "up":
                result['Emitter'] = 'Up'
                result['Collector'] = 'Down'
            else:
                result['Emitter'] = 'Down'
                result['Collector'] = 'Up'
            if horizontal_bias == "left":
                result['Base'] = 'Left'
            else:
                result['Base'] = 'Right'
        
        print(result)
        save_path = image_path.replace('.png', '_annotated.png')  # 保存图片的路径
        annotate_image(image_path, save_path, result)
        plot_ratios(column_black_ratios, column_white_ratios, row_black_ratios, row_white_ratios)

        return result
    except Exception as e:
        print(e)
        print("Unknown component")
        return 'Unknown component'

if __name__ == "__main__":
    detect_bjt(sys.argv)