import pandas as pd
import csv
import pygraphviz as pgv

def initialize_data_csv(file_path, output_dsm_path):
    #改成单独表格
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

def initialize_and_generate_svg(file_path, output_dsm_path, output_svg_path):
    initialize_data_csv(file_path, output_dsm_path)
    generate_bpmn_svg(file_path, output_svg_path)