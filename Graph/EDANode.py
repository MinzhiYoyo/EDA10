
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
            EDANode.TOTAL: [],
        }

        self.direct_to_poly = {
            EDANode.UP: None,
            EDANode.DOWN: None,
            EDANode.LEFT: None,
            EDANode.RIGHT: None,
        }


    def set_direct_to_poly(self, direction: str | list, poly_id: tuple[str, int] | list[tuple[str, int]]):
        if isinstance(direction, list):
            for d, p in zip(direction, poly_id):
                self.direct_to_poly[d] = p
        elif isinstance(poly_id, tuple):
            self.direct_to_poly[direction] = poly_id

    # 会自动去除重复
    def add_next(self, d: str , p: tuple[str, int]):
        assert d in self.direct_to_poly.keys() and d != EDANode.TOTAL, f"Invalid direction `{d}`, must be in [{EDANode.UP}, {EDANode.DOWN}, {EDANode.LEFT}, {EDANode.RIGHT}]"
        assert isinstance(p, tuple) and len(p) == 2 and isinstance(p[0], str) and isinstance(p[1], int), f"Invalid poly_id `{p}`, must be tuple[str, int], but is {type(p)}[{type(p[0])}, {type(p[1])}], len(p) = {len(p)}, (direction of next node, id of next node)"

        if not self.next_exist(d, p):
            self.next_node[d].append(p)

    def next_exist(self,d, p):
         return p in self.next_node[d]

    def __str__(self):
        return f"{self.node_type}_{self.id}"

# 定义MOS节点，包括PMOS和NMOS
class MOSNode(EDANode):
    Gate = "Gate"
    Drain = "Drain"
    Source = "Source"
    def __init__(self, node_type: str, id: int):
        super().__init__(node_type, id)

# 定义源节点，电压源/电流源
class SourceNode(EDANode):
    Positive = "Positive"
    Negative = "Negative"
    def __init__(self,node_type: str, id: int):
        super().__init__(node_type, id)

# 定义三极管，包括PNP和NPN
class BJTNode(EDANode):
    Base = "Base"
    Collector = "Collector"
    Emitter = "Emitter"
    def __init__(self, node_type: str, id: int):
        super().__init__(node_type, id)

class PMOSNode(MOSNode):
    def __init__(self, id: int):
        super().__init__("PMOS", id)

class NMOSNode(MOSNode):
    def __init__(self, id: int):
        super().__init__("NMOS", id)

class VoltageSourceNode(SourceNode):
    def __init__(self, id: int):
        super().__init__("VoltageSource", id)

class CurrentSourceNode(SourceNode):
    def __init__(self, id: int):
        super().__init__("CurrentSource", id)

class PNPNode(BJTNode):
    def __init__(self, id: int):
        super().__init__("PNP", id)

class NPNNode(BJTNode):
    def __init__(self, id: int):
        super().__init__("NPN", id)

class DiodeNode(EDANode):
    In = "In"
    Out = "Out"
    def __init__(self, id: int):
        super().__init__("Diode", id)

class DisoAmpNode(EDANode):
    InN = "InN"
    InP = "InP"
    Out = "Out"
    def __init__(self, id: int):
        super().__init__("DisoAmp", id)

class SisoAmpNode(EDANode):
    In = "In"
    Out = "Out"
    def __init__(self, id: int):
        super().__init__("SisoAmp", id)

class CapacitorNode(EDANode):
    Pos = "Pos"
    Neg = "Neg"
    def __init__(self, id: int):
        super().__init__("Cap", id)

class GndNode(EDANode):
    port = "port"
    def __init__(self, id: int):
        super().__init__("Gnd", id)

class InductorNode(EDANode):
    Pos = "Pos"
    Neg = "Neg"
    def __init__(self, id: int):
        super().__init__("Ind", id)

class ResistorNode(EDANode):
    Pos = "Pos"
    Neg = "Neg"
    def __init__(self, id: int):
        super().__init__("Res", id)

# 新建一个Net节点，用于替换掉 Port 节点
class NetNode(EDANode):
    def __init__(self, id: int):
        super().__init__("net", id)

class BridgeNode(EDANode):
    def __init__(self, id: int):
        super().__init__("Bridge", id)

