import pandas as pd
import pygraphviz as pgv

def generate_bpmn_svg(file_path, output_svg_path):
    # 读取数据
    df = pd.read_csv(file_path)
    dsm_df = pd.read_csv(file_path, index_col=2)

    # 读取所有元素并按泳道排序
    swimlanes = {}
    for index, row in df.iterrows():
        swimlane = row['Swimlane']
        element = row['Name']
        if swimlane not in swimlanes:
            swimlanes[swimlane] = []
        swimlanes[swimlane].append(element)

    elementnames = {}
    for index, row in df.iterrows():
        elementname = row['Name']
        elementtype = row['Type']
        elementnames[elementname] = elementtype

    # 计算每个泳道的起始 y 坐标
    start_y_positions = {}
    vertical_spacing = 5
    for index, swimlane in enumerate(swimlanes):
        start_y_positions[swimlane] = index * vertical_spacing

    # 初始化位置字典
    positions = {}
    for swimlane, elements in swimlanes.items():
        start_y = start_y_positions[swimlane] + 2.5
        for element in elements:
            positions[element] = (1, start_y)

    sequence_flows = {}
    for index, row in dsm_df.iterrows():
        outgoing_element = index
        target_elements = row[row == 'S'].index.tolist()
        sequence_flows[outgoing_element] = target_elements

        if len(target_elements) == 1:
            if outgoing_element in positions:
                old_x, old_y = positions[outgoing_element]
                positions[target_elements[0]] = (old_x + 2, old_y)
        elif len(target_elements) > 1:
            old_x, old_y = positions[outgoing_element]
            delta = 1.5
            mid_index = len(target_elements) // 2
            for i, target_element in enumerate(target_elements):
                positions[target_element] = (old_x + 2, old_y + (i - mid_index) * delta)

    message_flows = {}
    for index, row in dsm_df.iterrows():
        outgoing_element = index
        target_elements = row[row == 'M'].index.tolist()
        message_flows[outgoing_element] = target_elements

    associations = {}
    for index, row in dsm_df.iterrows():
        outgoing_element = index
        target_elements = row[row == 'A'].index.tolist()
        associations[outgoing_element] = target_elements

    G = pgv.AGraph(directed=True)

    for node, pos in positions.items():
        node_type = elementnames[node]
        shape = 'box'
        if node_type == 'ExklusiveGate':
            shape = 'diamond'
        elif node_type == 'StartEvent' or node_type == 'EndEvent':
            shape = 'ellipse'
        G.add_node(node, pos=f"{pos[0]},{pos[1]}!", shape=shape, width=0.6, height=0.3)

    for src, targets in sequence_flows.items():
        for target in targets:
            if src in G.nodes() and target in G.nodes():
                G.add_edge(src, target)

    for src, targets in message_flows.items():
        for target in targets:
            if src in G.nodes() and target in G.nodes():
                G.add_edge(src, target, style='dashed')

    G.graph_attr['splines'] = 'ortho'  # Orthogonal edges
    G.layout(prog='neato')
    G.draw(output_svg_path)

# 示例调用
file_path = 'uploads/bpmn.csv'
output_svg_path = 'output_graph.svg'
generate_bpmn_svg(file_path, output_svg_path)
