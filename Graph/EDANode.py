
# 颜色标志：导线是绿色的，走过的导线是浅绿色
# 元器件是黑色的，走过的元器件是灰色
#

class EDANode:
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    TOTAL = "total"
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
        if self.next_net[direction] is None:
            return None, None
        return direction if self.direct_to_poly[direction] is None else self.direct_to_poly[direction], self.next_net[direction]

    # 设置上下左右分别是什么
    def set_direct_to_poly(self, direction: str | list, poly_id: tuple[str, int] | list[tuple[str, int]]):
        if isinstance(direction, list):
            for d, p in zip(direction, poly_id):
                self.direct_to_poly[d] = p
        elif isinstance(poly_id, tuple):
            self.direct_to_poly[direction] = poly_id

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
