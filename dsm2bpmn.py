import pandas as pd
import csv
import pygraphviz as pgv
import os

def initialize_data_csv(file_path, output_folder):
    # 确保输出文件夹存在
    os.makedirs(output_folder, exist_ok=True)

    # 定义输出文件路径
    dsm_output_file = os.path.join(output_folder, 'dsm.csv')
    pa_pi_output_file = os.path.join(output_folder, 'pa_pi.csv')
    change_attribute_output_file = os.path.join(output_folder, 'change_attribute.csv')
    digital_tools_output_file = os.path.join(output_folder, 'digital_tools.csv')

    # 生成 gpa01-gpa22, spa01-spa35, pi01-pi28
    additional_columns = [f'gpa{i:02d}' for i in range(1, 23)] + \
                         [f'spa{i:02d}' for i in range(1, 36)] + \
                         [f'pi{i:02d}' for i in range(1, 29)]

    change_attribute_columns = [
        'changeName', 'changeId', 'changeDescription', 'responsibility', 'timeframe', 'changeCause',
        'localization', 'departments', 'changeStatus', 'timeOfOccurrence', 'lessonsLearned',
    ]

    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            original_fieldnames = reader.fieldnames

            # 获取除前两列外的其余所有列的字段名
            dsm_fieldnames = original_fieldnames[2:]
            pa_pi_fieldnames = ['Name'] + additional_columns

            # 打开输出文件并写入数据
            with open(dsm_output_file, mode='w', newline='', encoding='utf-8') as dsm_outfile, \
                    open(pa_pi_output_file, mode='w', newline='', encoding='utf-8') as pa_pi_outfile, \
                    open(change_attribute_output_file, mode='w', newline='', encoding='utf-8') as change_attribute_outfile, \
                    open(digital_tools_output_file, mode='w', newline='', encoding='utf-8') as digital_tools_outfile:
                dsm_writer = csv.DictWriter(dsm_outfile, fieldnames=dsm_fieldnames)
                pa_pi_writer = csv.DictWriter(pa_pi_outfile, fieldnames=pa_pi_fieldnames)
                change_attribute_writer = csv.DictWriter(change_attribute_outfile, fieldnames=change_attribute_columns)
                digital_tools_writer = csv.writer(digital_tools_outfile)

                dsm_writer.writeheader()
                pa_pi_writer.writeheader()
                change_attribute_writer.writeheader()

                for row in reader:
                    # 写入 dsm.csv
                    dsm_row = {field: row[field] for field in dsm_fieldnames}
                    dsm_writer.writerow(dsm_row)

                    # 写入 pa_pi.csv
                    pa_pi_row = {'Name': row['Name']}
                    pa_pi_row.update({col: '' for col in additional_columns})
                    pa_pi_writer.writerow(pa_pi_row)

        print("CSV initialization completed successfully.")
    except FileNotFoundError:
        print(f"File {file_path} not found. Ensure it's in the correct directory.")
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
    horizontal_spacing = 2
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
                positions[target_elements[0]] = (old_x + horizontal_spacing, old_y)
        elif len(target_elements) > 1:
            old_x, old_y = positions[outgoing_element]
            delta = 1.5
            mid_index = len(target_elements) // 2
            for i, target_element in enumerate(target_elements):
                positions[target_element] = (old_x + horizontal_spacing, old_y + (i - mid_index) * delta)

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

