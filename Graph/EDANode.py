import random
from EDAPublic.EDACV import CV_UP, CV_DOWN, CV_LEFT, CV_RIGHT, EDARectangle


# 颜色标志：导线是绿色的，走过的导线是浅绿色
# 元器件是黑色的，走过的元器件是灰色
#

class EDANode:
    UP = CV_UP # "Up"
    DOWN = CV_DOWN # "Down"
    LEFT = CV_LEFT # "Left"
    RIGHT = CV_RIGHT # "Right"
    # TOTAL = "Total"

    # 获取相对方向
    @staticmethod
    def opposite_direction(direction):
        if direction == EDANode.UP:
            return EDANode.DOWN
        elif direction == EDANode.DOWN:
            return EDANode.UP
        elif direction == EDANode.LEFT:
            return EDANode.RIGHT
        elif direction == EDANode.RIGHT:
            return EDANode.LEFT
        else:
            raise ValueError(f"Invalid direction `{direction}`")

    def __init__(self, node_type: str, id: int, rect):
        self.name = node_type + str(id)
        self.id = id
        self.node_type = node_type
        self.rect: EDARectangle = rect

        self.next_node = {
            EDANode.UP: [],
            EDANode.DOWN: [],
            EDANode.LEFT: [],
            EDANode.RIGHT: [],
        }

        self.next_net = {
            EDANode.UP: [],
            EDANode.DOWN: [],
            EDANode.LEFT: [],
            EDANode.RIGHT: [],
        }

        self.direct_to_poly = {
            EDANode.UP: None,
            EDANode.DOWN: None,
            EDANode.LEFT: None,
            EDANode.RIGHT: None,
        }

    def get_net_of_direction(self, direction: str):
        assert direction in [EDANode.UP, EDANode.DOWN, EDANode.LEFT, EDANode.RIGHT], f"Invalid direction `{direction}`, must be in [{EDANode.UP}, {EDANode.DOWN}, {EDANode.LEFT}, {EDANode.RIGHT}]"

        if self.next_net[direction] is None or len(self.next_net[direction]) == 0 or self.direct_to_poly[direction] is None:
            return None, None

        random_next_net = self.next_net[direction][random.randint(0, len(self.next_net[direction]) - 1)]
        return self.direct_to_poly[direction], random_next_net

    # 设置上下左右分别是什么
    def set_direct_to_poly(self, direction, poly):
        assert direction in [EDANode.UP, EDANode.DOWN, EDANode.LEFT, EDANode.RIGHT], f"Invalid direction `{direction}`, must be in [{EDANode.UP}, {EDANode.DOWN}, {EDANode.LEFT}, {EDANode.RIGHT}]"
        assert isinstance(poly, str), f"Invalid poly `{poly}`, must be str, but is {type(poly)}"
        self.direct_to_poly[direction] = poly
        
    def process_directions(self):
        '''
        上下相对，左右相对
        若只有1个键被赋值，则将这个值也赋给与之相对的那个键；
        若有2个键被赋值，且这两个键恰好是相对的，则不做任何操作；
        若有2个键被赋值，但这两个键不是相对的，则对于"Up""Down"这两个键，保留其中非None的值，并把另一个None值改为"Left""Right"两个键中非None的那个值，其他的键重置为None；
        若有3个键被赋值，则保留其中相对的两个键的值，其他重置为None；
        若4个键都被赋值，则保留其中"Up""Down"这两个键的值，其他重置为None。
        '''
        D = self.next_net
        OPPOSITES = {EDANode.UP: EDANode.DOWN, EDANode.DOWN: EDANode.UP, EDANode.LEFT: EDANode.RIGHT, EDANode.RIGHT: EDANode.LEFT}
        keys = [EDANode.UP, EDANode.DOWN, EDANode.LEFT, EDANode.RIGHT]
        non_none_keys = [k for k in keys if D.get(k) is not None]
        n = len(non_none_keys)
        D_out = {EDANode.UP: None, EDANode.DOWN: None, EDANode.LEFT: None, EDANode.RIGHT: None}

        if n == 1:
            # Only one key is assigned
            assigned_key = non_none_keys[0]
            assigned_value = D[assigned_key]
            opposite_key = OPPOSITES[assigned_key]
            D_out[assigned_key] = assigned_value
            D_out[opposite_key] = assigned_value
            # All other keys already set to None
        elif n == 2:
            k1, k2 = non_none_keys
            is_opposite = OPPOSITES[k1] == k2
            if is_opposite:
                # Do nothing, keep the two keys as is
                D_out[k1] = D[k1]
                D_out[k2] = D[k2]
                # Other keys are None
            else:
                # The keys are not opposites
                # Keep non-None value among EDANode.UP and EDANode.DOWN; assign the other to non-None value among EDANode.LEFT and EDANode.RIGHT
                # Set EDANode.LEFT and EDANode.RIGHT to None

                # Determine which of EDANode.UP and EDANode.DOWN is non-None
                up_down_non_none = [k for k in [EDANode.UP, EDANode.DOWN] if D.get(k) is not None]
                left_right_non_none = [k for k in [EDANode.LEFT, EDANode.RIGHT] if D.get(k) is not None]
                if len(up_down_non_none) == 1 and len(left_right_non_none) == 1:
                    up_down_key = up_down_non_none[0]
                    left_right_key = left_right_non_none[0]
                    up_down_value = D[up_down_key]
                    left_right_value = D[left_right_key]
                    # Assign values
                    D_out[up_down_key] = up_down_value
                    opposite_up_down_key = OPPOSITES[up_down_key]
                    D_out[opposite_up_down_key] = left_right_value
                    # EDANode.LEFT and EDANode.RIGHT are None
                else:
                    # Should not happen if inputs are correct
                    pass
        elif n == 3:
            # Keep values of the two opposite keys, set others to None
            assigned_keys = non_none_keys
            opposites_found = False
            for k1 in assigned_keys:
                k2 = OPPOSITES[k1]
                if k2 in assigned_keys:
                    # Found the two opposite keys
                    D_out[k1] = D[k1]
                    D_out[k2] = D[k2]
                    opposites_found = True
                    break
            if not opposites_found:
                # Should not happen if inputs are correct
                pass
        elif n == 4:
            # All four keys assigned values
            # Keep EDANode.UP and EDANode.DOWN, set others to None
            D_out[EDANode.UP] = D[EDANode.UP]
            D_out[EDANode.DOWN] = D[EDANode.DOWN]
            # EDANode.LEFT and EDANode.RIGHT are already None in D_out
        else:
            # n == 0
            # All values are None, return as is
            pass

        self.next_net = D_out
        print(self.next_net)

    # 会自动去除重复
    def add_next(self, d: str , p: tuple[str, int]):
        assert d in self.direct_to_poly.keys(), f"Invalid direction `{d}`, must be in [{EDANode.UP}, {EDANode.DOWN}, {EDANode.LEFT}, {EDANode.RIGHT}]"
        assert isinstance(p, tuple) and len(p) == 2 and isinstance(p[0], str) and isinstance(p[1], int), \
            (f"Invalid poly_id `{p}`, must be tuple[str, int], but is {type(p)}[{type(p[0])}, {type(p[1])}], len(p) = {len(p)},"
             f" direction of next node, id of next node")
        if not self.next_exist(d, p):
            self.next_node[d].append(p)

    def delete_next(self, d: str, p: tuple[str, int]):
        assert d in self.direct_to_poly.keys(), f"Invalid direction `{d}`, must be in [{EDANode.UP}, {EDANode.DOWN}, {EDANode.LEFT}, {EDANode.RIGHT}]"
        assert isinstance(p, tuple) and len(p) == 2 and isinstance(p[0], str) and isinstance(p[1], int), \
            (f"Invalid poly_id `{p}`, must be tuple[str, int], but is {type(p)}[{type(p[0])}, {type(p[1])}], len(p) = {len(p)},"
             f" direction of next node, id of next node")
        if self.next_exist(d, p):
            self.next_node[d].remove(p)


    def next_exist(self,d, p):
         return p in self.next_node[d]

    def __str__(self):
        return f"{self.node_type}_{self.id}"

    def random_poly(self, *poly_names):
        assert len(poly_names) == 2, f"Invalid number of poly names, must be 2, but is {len(poly_names)}"
        # 确定摆放方向
        connect_directions = [k for k, v in self.next_net.items() if len(v) > 0]
        net_s = len(connect_directions)
        if net_s == 0:
            return
        elif net_s == 1:
            # 获取哪个方向有连接
            self.set_direct_to_poly(connect_directions[0], poly_names[0])
            self.set_direct_to_poly(EDANode.opposite_direction(connect_directions[0]), poly_names[1])
            return
        elif net_s == 2:
            # 两个方向都有连接
            self.set_direct_to_poly(connect_directions[0], poly_names[0])
            self.set_direct_to_poly(connect_directions[1], poly_names[1])
            return
        elif net_s == 3:
            # 获取相对的两个方向
            opposite_directions = [EDANode.opposite_direction(d) for d in connect_directions]
            set_directions = [d for d in connect_directions if d in opposite_directions]
            assert len(set_directions) == 2, f"Invalid number of set directions, must be 2, it is {set_directions}, opposite_directions = {opposite_directions}, connect_directions = {connect_directions}"
            self.set_direct_to_poly(set_directions[0], poly_names[0])
            self.set_direct_to_poly(set_directions[1], poly_names[1])
            return
        elif net_s == 4:
            # 随机选择一个方向以及其相对方向
            random_direction = connect_directions[random.randint(0, 3)]
            random_direction = [random_direction, EDANode.opposite_direction(random_direction)]
            self.set_direct_to_poly(random_direction[0], poly_names[0])
            self.set_direct_to_poly(random_direction[1], poly_names[1])

    def get_connection_info(self):
        rst = []
        for direction in self.next_net.keys():
            poly, net = self.get_net_of_direction(direction)
            if poly is None:
                continue
            if poly == "Source":
                rst.append((direction, "Body", net))
            rst.append((direction, poly, net))

        return rst



class NetNode:
    def __init__(self, id):
        self.id = id
        self.next_node = []
    def __str__(self):
        return f"net{self.id}"
