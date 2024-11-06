import numpy as np

CV_UP = "up"
CV_DOWN = "down"
CV_LEFT = "left"
CV_RIGHT = "right"
CV_CENTER = "center"

# 右为x轴正方向，下为y轴正方向

class EDAPoint:
    DIRECTIONS_POINT = [[0, 1], [1, 0], [0, -1], [-1, 0]]
    def __init__(self, x, y):
        self.x = int(x)
        self.y = int(y)
    def to_numpy(self):
        return np.array([self.x, self.y])

    def __str__(self):
        return f'({self.x}, {self.y})'

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __add__(self, other):
        return EDAPoint(self.x + other.x, self.y + other.y)

    def __sub__(self, other):
        return EDAPoint(self.x - other.x, self.y - other.y)

    def __mul__(self, other):
        return EDAPoint(self.x * other, self.y * other)

    def __truediv__(self, other):
        return EDAPoint(self.x / other, self.y / other)

    def manhattan_distance(self, other):
        return abs(self.x - other.x) + abs(self.y - other.y)

    def euclidean_distance(self, other):
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def get_horizontal_points(self, ax: int):  # 获取(mx, my)到(ax, my)的所有点
        results = []
        for x in range(min(self.x, ax), max(self.x, ax) + 1):
            results.append(EDAPoint(x, self.y))
        return results

    def get_vertical_points(self, ay: int):  # 获取(mx, my)到(mx, ay)的所有点
        results = []
        for y in range(min(self.y, ay), max(self.y, ay) + 1):
            results.append(EDAPoint(self.x, y))
        return results

    def is_invalid(self, rgb: np.ndarray):
        return self.x < 0 or self.y < 0 or self.x >= rgb.shape[1] or self.y >= rgb.shape[0]

    def __hash__(self):
        return hash((self.x, self.y))


class EDARectangle:
    def __init__(self, left_up, right_down):
        self.left_up = left_up
        self.right_down = right_down

    def __str__(self):
        return f'[{self.left_up}, {self.right_down}]'

    def __eq__(self, other):
        return self.left_up == other.left_up and self.right_down == other.right_down

    # 获取四个角的点
    def get_corners(self):
        return [
            self.left_up,  # 左上
            EDAPoint(self.right_down.x, self.left_up.y), # 右上
            self.right_down, # 右下
            EDAPoint(self.left_up.x, self.right_down.y), # 左下
        ]

    # 获取四个边
    def get_edge(self, direction):
        if direction == CV_LEFT:
            return self.left_up.get_vertical_points(self.right_down.y)
        elif direction == CV_RIGHT:
            return EDAPoint(self.right_down.x, self.left_up.y).get_vertical_points(self.right_down.y)
        elif direction == CV_UP:
            return self.left_up.get_horizontal_points(self.right_down.x)
        elif direction == CV_DOWN:
            return EDAPoint(self.left_up.x, self.right_down.y).get_horizontal_points(self.right_down.x)
        else:
            raise ValueError('方向错误')

    def area(self):
        return (self.right_down.x - self.left_up.x) * (self.right_down.y - self.left_up.y)

    def center(self):
        return (self.left_up + self.right_down) / 2

    def in_me(self, a_point):
        return self.left_up.x <= a_point.x <= self.right_down.x and self.left_up.y <= a_point.y <= self.right_down.y

    def point_to_left(self, a_point):
        return a_point.x - self.left_up.x

    def point_to_right(self, a_point):
        return self.right_down.x - a_point.x

    def point_to_up(self, a_point):
        return a_point.y - self.left_up.y

    def point_to_down(self, a_point):
        return self.right_down.y - a_point.y

    def direct(self, a_point):
        to_left = self.point_to_left(a_point)
        to_right = self.point_to_right(a_point)
        to_up = self.point_to_up(a_point)
        to_down = self.point_to_down(a_point)

        # 哪个最小就是哪个方向，如果有多个最小，优先级为左右上下，如果都一样，那么为中间
        min_value = min(to_left, to_right, to_up, to_down)
        if min_value == to_left == to_right == to_up == to_down:
            return CV_CENTER
        if min_value == to_left:
            return CV_LEFT
        elif min_value == to_right:
            return CV_RIGHT
        elif min_value == to_up:
            return CV_UP
        else:
            return CV_DOWN





