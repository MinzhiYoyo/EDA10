from Public.EDACV import CV_UP, CV_DOWN, CV_LEFT, CV_RIGHT


# 颜色标志：导线是绿色的，走过的导线是浅绿色
# 元器件是黑色的，走过的元器件是灰色
#

class EDANode:
    UP = CV_UP # "Up"
    DOWN = CV_DOWN # "Down"
    LEFT = CV_LEFT # "Left"
    RIGHT = CV_RIGHT # "Right"
    # TOTAL = "Total"
    def __init__(self, node_type: str, id: int):
        self.name = node_type + str(id)
        self.id = id
        self.node_type = node_type

        self.next_node = {
            EDANode.UP: [],
            EDANode.DOWN: [],
            EDANode.LEFT: [],
            EDANode.RIGHT: [],
        }

        self.next_net = {
            EDANode.UP: None,
            EDANode.DOWN: None,
            EDANode.LEFT: None,
            EDANode.RIGHT: None,
        }

        self.direct_to_poly = {
            EDANode.UP: None,
            EDANode.DOWN: None,
            EDANode.LEFT: None,
            EDANode.RIGHT: None,
        }

    def get_port_name(self, direction: str):
        assert direction in [EDANode.UP, EDANode.DOWN, EDANode.LEFT, EDANode.RIGHT], f"Invalid direction `{direction}`, must be in [{EDANode.UP}, {EDANode.DOWN}, {EDANode.LEFT}, {EDANode.RIGHT}]"
        if self.next_net[direction] is None: # 这个方向上没有连接
            return None, None
        return direction if self.direct_to_poly[direction] is None else self.direct_to_poly[direction], self.next_net[direction]

    # 设置上下左右分别是什么
    def set_direct_to_poly(self, direction: str | list, poly: str | list):
        if isinstance(direction, list):
            for d, p in zip(direction, poly):
                assert d in [EDANode.UP, EDANode.DOWN, EDANode.LEFT, EDANode.RIGHT], f"Invalid direction `{direction}`, must be in [{EDANode.UP}, {EDANode.DOWN}, {EDANode.LEFT}, {EDANode.RIGHT}]"
                self.direct_to_poly[d] = p
        elif isinstance(poly, str):
            self.direct_to_poly[direction] = poly
        else:
            raise ValueError(f"Invalid input {direction}, {poly}")
        
    def process_directions(self):
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

    def next_exist(self,d, p):
         return p in self.next_node[d]

    def __str__(self):
        return f"{self.node_type}_{self.id}"

class NetNode:
    def __init__(self, id):
        self.id = id
        self.next_node = []
    def __str__(self):
        return f"net{self.id}"
