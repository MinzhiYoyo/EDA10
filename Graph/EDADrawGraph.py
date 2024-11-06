# 使用 graphviz 画图
from graphviz import Graph

"""
 "ckt_type": "Unkown",
    "ckt_netlist": [
        {
            "component_type": "Diode",
            "port_connection": {
                "left": "net0",
                "right": "net1"
            }
        },
        ...
    ]
"""

# 画无向图
def draw_graph(netlist: dict, file_name):
    netlist = netlist['ckt_netlist']
    dot = Graph(comment='The Round Table')
    counter = 0
    nets = set()
    for component in netlist:
        component_type = component['component_type'] + str(counter)
        counter += 1
        dot.node(component_type, component_type)
        for port, net in component['port_connection'].items():
            if net not in nets:
                dot.node(net, net)
                nets.add(net)
            dot.edge(component_type, net)

    dot.render(f'tmp/route_{file_name}.gv', view=True)

    return dot
