import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import csv

def initialize_data_csv(file_path, output_dsm_path):
    input_file = file_path
    output_file = output_dsm_path
    # 生成 gpa01-gpa22, spa01-spa35, pi01-pi28
    additional_columns = [f'gpa{i:02d}' for i in range(1, 23)] + \
                         [f'spa{i:02d}' for i in range(1, 36)] + \
                         [f'pi{i:02d}' for i in range(1, 29)]

    try:
        with open(input_file, mode='r', newline='') as infile, \
             open(output_file, mode='w', newline='') as outfile:
            reader = csv.DictReader(infile)
            # 获取除前两列外的其余所有列的字段名
            original_fieldnames = reader.fieldnames[2:]  # 排除前两个字段名
            fieldnames = original_fieldnames + additional_columns  # 添加新列到字段名列表中
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)

            writer.writeheader()
            for row in reader:
                # 创建新行，只包括原始数据中除前两列外的数据，并为新增的列初始化为空字符串
                new_row = {field: row[field] for field in original_fieldnames}
                new_row.update({col: '' for col in additional_columns})
                writer.writerow(new_row)
        print("CSV initialization completed successfully.")
    except FileNotFoundError:
        print(f"File {input_file} not found. Ensure it's in the correct directory.")
    except Exception as e:
        print(f"An error occurred: {e}")

def generate_bpmn_svg(file_path, output_svg_path):
    # 读取数据
    df = pd.read_csv(file_path)
    dsm_df = pd.read_csv(file_path, index_col=2)

    #read all elements and sorted with swimlane
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

    #calculate start y_position of each swimlane
    start_y_positions = {}
    vertical_spacing = 5
    for index, swimlane in enumerate(swimlanes):
        start_y_positions[swimlane] = index * vertical_spacing

    #初始化position字典
    positions = {}
    for swimlane, elements in swimlanes.items():
        # 获取这个 swimlane 的起始 y 坐标，并加上2.5的偏移
        start_y = start_y_positions[swimlane] + 2.5

        for element in elements:
            # 设置每个元素的初始位置，x坐标设为1，y坐标为计算后的起始位置
            positions[element] = (1, start_y)

    sequence_flows = {}
    #给每一个element计算坐标，以sequence flow为依据，间隔为2，这里并行任务将使用同一坐标并在下一步重新计算。
    for index, row in dsm_df.iterrows():
        outgoing_element = index
        target_elements = row[row == 'S'].index.tolist()
        sequence_flows[outgoing_element] = target_elements

        if len(target_elements) == 1:
            # 只有一个目标，直接设置位置
            if outgoing_element in positions:
                old_x, old_y = positions[outgoing_element]
                positions[target_elements[0]] = (old_x + 2, old_y)
        elif len(target_elements) > 1:
            # 多个目标元素，需要处理 y 坐标的分配
            old_x, old_y = positions[outgoing_element]  # 获取出发元素的旧坐标
            delta = 1.5  # 设置y坐标的偏移量
            mid_index = len(target_elements) // 2
            for i, target_element in enumerate(target_elements):
                positions[target_element] = (old_x + 2, old_y + (i - mid_index) * delta)

    #获取messageflow
    message_flows = {}
    for index, row in dsm_df.iterrows():
        outgoing_element = index
        target_elements = row[row == 'M'].index.tolist()
        message_flows[outgoing_element] = target_elements

    #获取Association
    associations = {}
    for index, row in dsm_df.iterrows():
        outgoing_element = index
        target_elements = row[row == 'A'].index.tolist()
        associations[outgoing_element] = target_elements


    G = nx.DiGraph()
    # 添加节点，使用positions字典中的坐标作为节点的位置
    for node, pos in positions.items():
        G.add_node(node)
        G.nodes[node]['pos'] = pos
    # 添加边
    # 根据 sequence_flows 添加边
    for src, targets in sequence_flows.items():
        for target in targets:
            if src in G.nodes and target in G.nodes:
                G.add_edge(src, target)  # 添加边从源节点到目标节点

    #根据messageflow添加虚线边
    for src, targets in message_flows.items():
        for target in targets:
            if src in G.nodes and target in G.nodes:
                G.add_edge(src, target, style='dashed')

    # 获取节点的位置
    pos = nx.get_node_attributes(G, 'pos')

    # 设置图形大小
    plt.figure(figsize=(12, 6))

    fig, ax = plt.subplots()
    for node, (x, y) in positions.items():
        node_type = elementnames[node]  # 从elementnames获取类型信息

        if node_type == 'Task':
            # 圆角矩形
            box = mpatches.FancyBboxPatch((x - 0.3, y - 0.15), 0.6, 0.3, boxstyle="round,pad=0.02", edgecolor='black',
                                          facecolor='white')
            ax.add_patch(box)

        elif node_type == 'ExklusiveGate':
            # 菱形
            diamond = mpatches.RegularPolygon((x, y), numVertices=4, radius=0.3, orientation=np.pi, edgecolor='black',
                                              facecolor='white')
            ax.add_patch(diamond)
        else:
            circle = plt.Circle((x, y), 0.3, edgecolor='black', facecolor='white', fill=True)  # 创建一个圆形
            ax.add_patch(circle)


    # 绘制实线边
    nx.draw_networkx_edges(G, pos, edgelist=[(u, v) for u, v in G.edges() if G[u][v].get('style') != 'dashed'],
                           arrowstyle='-|>')

    # 绘制虚线边
    nx.draw_networkx_edges(G, pos, edgelist=[(u, v) for u, v in G.edges() if G[u][v].get('style') == 'dashed'],
                           arrowstyle='-|>',
                           style='dashed')
    # 绘制标签
    label_pos = {node: (x, y + 0.5) for node, (x, y) in positions.items()}
    nx.draw_networkx_labels(G, label_pos, font_size=8, font_color='black', font_family='sans-serif')

    # 显示图形
    plt.savefig(output_svg_path)
    plt.close()

def initialize_and_generate_svg(file_path, output_dsm_path, output_svg_path):
    initialize_data_csv(file_path, output_dsm_path)
    generate_bpmn_svg(file_path, output_svg_path)