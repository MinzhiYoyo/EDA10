from PIL import Image, ImageDraw, ImageFont
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
import sys

result = {}
image_path = 'test4.png'  # 替换为你的图片路径

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

def binarize_image(image_path, threshold=128):
    # 打开图像并转换为灰度
    image = Image.open(image_path).convert('L')
    # 将灰度图像转换为NumPy数组
    image_array = np.array(image)
    # 二值化处理
    binary_array = (image_array > threshold).astype(int)
    return binary_array

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

def find_peaks_and_second_peak(ratios, imgWidth):
    peaks, properties = find_peaks(
        ratios, 
        distance = imgWidth / 10,          # 最小距离
        prominence = 0.1,      # 显著性
        width = 0.1              # 最小宽度
    )
    
    if len(peaks) > 3:
        # 获取峰值高度
        peak_values = ratios[peaks]
        
        # 找到最高的三个峰值索引
        top_three_indices = np.argsort(peak_values)[-3:]
        peaks = peaks[top_three_indices]
        
    # 打印峰值位置
    print("Peaks:", peaks)
    
    if len(peaks) > 1:
        second_peak_index = peaks[1]
        return peaks, second_peak_index
    else:
        return peaks, None

def find_second_peak(peaks, column_black_ratios):
    if len(peaks) > 1:
        second_peak_index = peaks[1]
        relative_position = second_peak_index / len(column_black_ratios)
        return second_peak_index, relative_position
    else:
        return None, None

def calculate_ratios(binary_array):
    height, width = binary_array.shape
    column_black_ratios = np.sum(binary_array == 0, axis=0) / height
    row_black_ratios = np.sum(binary_array == 0, axis=1) / width
    return column_black_ratios, row_black_ratios

def calculate_symmetry_score(ratios):
    half = len(ratios) // 2
    left = ratios[:half]
    right = ratios[-half:][::-1]
    symmetry_score = np.sum(np.abs(left - right))
    return symmetry_score

def analyze_orientation(column_black_ratios, row_black_ratios):
    column_symmetry = calculate_symmetry_score(column_black_ratios)
    row_symmetry = calculate_symmetry_score(row_black_ratios)
    
    print(f'Column Symmetry: {column_symmetry}')
    print(f'Row Symmetry: {row_symmetry}')
    
    if column_symmetry < row_symmetry:
        print("DS Vertical")
    else:
        print("DS Horizontal")

def analyze_peaks(peaks, center):
    if peaks is None or len(peaks) < 3:
        return None

    # 计算每对峰值之间的距离
    distances = np.diff(peaks)
    min_distance_index = np.argmin(distances)

    # 判断最近的两个峰值的位置
    left_peak = peaks[min_distance_index]
    right_peak = peaks[min_distance_index + 1]

    if (left_peak + right_peak) / 2 < center:
        position = "left"
    else:
        position = "right"

    return position

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

def detect_mos(argv):
    try:
        global image_path
        try:
            image_path = argv[1]
        except IndexError:
            print("Usage: python mos_detect.py <image_path>")
            sys.exit(1)
        binary_array = binarize_image(image_path)
        column_black_ratios, column_white_ratios = calculate_column_ratios(binary_array)
        row_black_ratios, row_white_ratios = calculate_row_ratios(binary_array)
        # plot_ratios(column_black_ratios, column_white_ratios, row_black_ratios, row_white_ratios)
        # analyze_orientation(column_black_ratios, row_black_ratios)
        column_peaks, column_second_peak = find_peaks_and_second_peak(column_black_ratios, binary_array.shape[1])
        row_peaks, row_second_peak = find_peaks_and_second_peak(row_black_ratios, binary_array.shape[0])
        # sort the peaks
        column_peaks = np.sort(column_peaks)
        row_peaks = np.sort(row_peaks)
        second_peak_index_column, relative_position_column = find_second_peak(column_peaks, column_black_ratios)
        second_peak_index_row, relative_position_row = find_second_peak(row_peaks, row_black_ratios)

        plot_ratios(column_black_ratios, column_white_ratios, row_black_ratios, row_white_ratios)
        
        if second_peak_index_column is not None:
            print(f'Second peak index (column): {second_peak_index_column}')
            print(f'Second peak relative position (column): {relative_position_column}')
        else:
            print("Less than two peaks found.")

        if second_peak_index_row is not None:
            print(f'Second peak index (row): {second_peak_index_row}')
            print(f'Second peak relative position (row): {relative_position_row}')
        else:
            print("Less than two peaks found.")

        # 计算second_peak_index到中心的距离，若column大于row则为竖直，否则为水平
        height, width = binary_array.shape
        center_column = width // 2
        center_row = height // 2
        distance_column = abs(second_peak_index_column - center_column)
        distance_row = abs(second_peak_index_row - center_row)
        print(f'Distance to center (column): {distance_column}')
        print(f'Distance to center (row): {distance_row}')
        if distance_column > distance_row:
            print("DS Vertical")
            result['Source'] = 'Up'
            result['Drain'] = 'Down'
            position = analyze_peaks(column_peaks, center_column)
            print("Column histogram: Closest peaks are on the", position)
            if position == 'left':
                result['Gate'] = 'Left'
            else:
                result['Gate'] = 'Right'
        else:
            print("DS Horizontal")
            result['Source'] = 'Left'
            result['Drain'] = 'Right'
            position = analyze_peaks(row_peaks, center_row)
            print("Row histogram: Closest peaks are on the", position)
            if position == 'left':
                result['Gate'] = 'Up'
            else:
                result['Gate'] = 'Down'

        # result['Body'] = result['Source']
        print(result)

        save_path = image_path.replace('.png', '_annotated.png')  # 保存图片的路径
        annotate_image(image_path, save_path, result)

        return result
    except Exception as e:
        print(e)
        print("Unknown component")
        return 'Unknown component'

if __name__ == "__main__":
    detect_mos(sys.argv)