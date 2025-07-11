import pandas as pd
import pygraphviz as pgv
import os
import csv
import numpy as np



def initialize_data_csv(file_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    dsm_output_file = os.path.join(output_folder, 'dsm.csv')
    pa_pi_output_file = os.path.join(output_folder, 'pa_pi.csv')
    change_attribute_output_file = os.path.join(output_folder, 'change_attribute.csv')
    digital_tools_output_file = os.path.join(output_folder, 'digital_tools.csv')
    selected_CA_output_file = os.path.join(output_folder, 'selected_CA.csv')

    additional_columns = [f'gpa{i:02d}' for i in range(1, 23)] + \
                         [f'spa{i:02d}' for i in range(1, 36)] + \
                         [f'pi{i:02d}' for i in range(1, 29)]

    change_attribute_columns = [
        'changeName', 'changeId', 'changeDescription', 'responsibility', 'timeframe', 'changeCause',
        'localization', 'departments', 'changeStatus', 'timeOfOccurrence', 'lessonsLearned',
        'impactOnInternal', 'impactOnExternal', 'efforts', 'costs', 'availableDataInformation',
        'dependencyLevel', 'changePropagation', 'changeReoccurrence', 'complexity', 'challenges',
        'duration', 'relevance', 'urgency'
    ]

    try:
        with open(file_path, mode='r', newline='', encoding='utf-8') as infile:
            reader = csv.DictReader(infile)
            original_fieldnames = reader.fieldnames

            dsm_fieldnames = original_fieldnames[2:]
            pa_pi_fieldnames = ['Name'] + additional_columns

            with open(dsm_output_file, mode='w', newline='', encoding='utf-8') as dsm_outfile, \
                    open(pa_pi_output_file, mode='w', newline='', encoding='utf-8') as pa_pi_outfile, \
                    open(change_attribute_output_file, mode='w', newline='', encoding='utf-8') as change_attribute_outfile, \
                    open(digital_tools_output_file, mode='w', newline='', encoding='utf-8') as digital_tools_outfile, \
                    open(selected_CA_output_file, mode='w', newline='', encoding='utf-8') as selected_CA_outfile:
                dsm_writer = csv.DictWriter(dsm_outfile, fieldnames=dsm_fieldnames)
                pa_pi_writer = csv.DictWriter(pa_pi_outfile, fieldnames=pa_pi_fieldnames)
                change_attribute_writer = csv.DictWriter(change_attribute_outfile, fieldnames=change_attribute_columns)
                digital_tools_writer = csv.writer(digital_tools_outfile)
                selected_CA_writer = csv.writer(selected_CA_outfile)

                dsm_writer.writeheader()
                pa_pi_writer.writeheader()
                change_attribute_writer.writeheader()

                for row in reader:
                    dsm_row = {field: row[field] for field in dsm_fieldnames}
                    dsm_writer.writerow(dsm_row)

                    pa_pi_row = {'Name': row['Name']}
                    pa_pi_row.update({col: '' for col in additional_columns})
                    pa_pi_writer.writerow(pa_pi_row)

        print("CSV initialization completed successfully.")
    except FileNotFoundError:
        print(f"File {file_path} not found. Ensure it's in the correct directory.")
    except Exception as e:
        print(f"An error occurred: {e}")

def calculate_positions(positions, sequence_flows, start_element, horizontal_spacing, vertical_spacing, visited=None):
    if visited is None:
        visited = set()

    if start_element in visited:
        return
    visited.add(start_element)

    old_x, old_y = positions[start_element]
    targets = sequence_flows.get(start_element, [])

    if len(targets) == 1:
        positions[targets[0]] = (old_x + horizontal_spacing, old_y)
        calculate_positions(positions, sequence_flows, targets[0], horizontal_spacing, vertical_spacing, visited)
    elif len(targets) > 1:
        num_targets = len(targets)
        delta = vertical_spacing / num_targets
        mid_index = num_targets // 2

        for i, target in enumerate(targets):
            if num_targets % 2 == 0:
                offset = (i - mid_index + 0.5) * delta
            else:
                offset = (i - mid_index) * delta
            positions[target] = (old_x + horizontal_spacing, old_y + offset)
            calculate_positions(positions, sequence_flows, target, horizontal_spacing, vertical_spacing, visited)
            
def generate_bpmn_svg(file_path, output_svg_path):
    # Read dsm file
    df = pd.read_csv(file_path)
    dsm_df = pd.read_csv(file_path, index_col=2, header=0)
    print(dsm_df)
    # Create Data frame with only process steps present in the result bpmn
    i = 1
    s = 0
    dsm_df_cols= dsm_df.columns.tolist()
    for element in dsm_df_cols[2:]:
        i = i+1
        if not element in df.Name.tolist():    
            s = i
            while not dsm_df_cols[i] in df.Name.tolist():
                if s >= len(dsm_df_cols)-1:
                    while not dsm_df_cols[i] in df.Name.tolist():
                        s = s-1
                        dsm_df_cols[i] = dsm_df_cols[s+1]
                    break
                dsm_df_cols[i] = dsm_df_cols[s+1]
                s = s + 1         
              
        
                
    dsm_df.columns = tuple(dsm_df_cols)
    def same_merge(x): return ';'.join(x[x.notnull()].astype(str))

# Define new DataFrame that merges columns with same names together
    dsm_df = dsm_df.groupby(level=0, axis=1).apply(lambda x: x.apply(same_merge, axis=1))
    for element in dsm_df.columns.tolist():
        dsm_df.loc[element, element] = ''
    dsm_df=dsm_df[:len(dsm_df.index)-2]

   


    print(dsm_df)
    # Initialize swimlanes and elements
    swimlanes = {}
    elements = {}
    for index, row in df.iterrows():
        swimlane = row['Swimlane']
        element = row['Name']
        elementtype = row['Type']
        elements[element] = elementtype
        if swimlane not in swimlanes:
            swimlanes[swimlane] = []
        swimlanes[swimlane].append(element)

    # Process sequence flows and message flows
    sequence_flows = {}
    message_flows = {}
    associations = {}
    for index, row in dsm_df.iterrows():
        outgoing_element = index
        # Remove columns that do not need to be checked
        relevant_columns = row.drop(labels=['Swimlane', 'Type'])

        sequence_targets = relevant_columns[relevant_columns.astype(str).str.contains('S', na=False)].index.tolist()
        message_targets = relevant_columns[relevant_columns.astype(str).str.contains('M', na=False)].index.tolist()
        association_targets = relevant_columns[relevant_columns == 'A'].index.tolist()

        sequence_flows[outgoing_element] = sequence_targets
        message_flows[outgoing_element] = message_targets
        associations[outgoing_element] = association_targets

    # Check for elements needing startevent and endevent
    start_events = []
    end_events = []
    start_swimlanes = {}
    end_swimlanes = {}

    for element in dsm_df.index:
        # Check if the element has no target elements (no 'S' or 'M' in its column)
        if not any(dsm_df[element].astype(str).str.contains('S|M', na=False)):
            start_events.append(element)
            if not df[df['Name'] == element].empty:
                start_swimlanes[element] = df[df['Name'] == element]['Swimlane'].values[0]
        # Check if the element has no outgoing elements (no 'S' or 'M' in its row)
        if not any(dsm_df.drop(columns=['Swimlane', 'Type']).loc[element].astype(str).str.contains('S|M', na=False)):
            end_events.append(element)
            if not df[df['Name'] == element].empty:
                end_swimlanes[element] = df[df['Name'] == element]['Swimlane'].values[0]
    print("Start events:", start_events)
    print("End events:", end_events)
    # Add startevent to swimlanes
    if start_events:
        unique_start_event = 'Start'
        elements[unique_start_event] = 'StartEvent'
        for element in start_events:
            if element in start_swimlanes:
                swimlane = start_swimlanes[element]
                if unique_start_event not in swimlanes.get(swimlane, []):
                    swimlanes.setdefault(swimlane, []).insert(0, unique_start_event)
                sequence_flows.setdefault(unique_start_event, []).append(element)

    # Add endevent to swimlanes
    if end_events:
        unique_end_event = 'End'
        elements[unique_end_event] = 'EndEvent'
        for element in end_events:
            if element in end_swimlanes:
                swimlane = end_swimlanes[element]
                if unique_end_event not in swimlanes.get(swimlane, []):
                    swimlanes.setdefault(swimlane, []).append(unique_end_event)
                if element in sequence_flows:
                    sequence_flows[element].append(unique_end_event)
                else:
                    sequence_flows[element] = [unique_end_event]
    print("Sequence flows after adding start and end events:", sequence_flows)
    # Process gates and outgoing elements
    gate_counter = 1
    final_sequence_flows = {}
    for element, targets in sequence_flows.items():
        if len(targets) > 1:
                if not element == 'Start':
                    row = dsm_df.loc[element]
                    gate_type = None
                    if any('AS' in str(val) for val in row):
                        gate_type = 'AND'
                    elif any('XS' in str(val) for val in row):
                        gate_type = 'XOR'
                else:
                    row = dsm_df.loc[targets[0]]
                    gate_type = None
                    if any('AS' in str(val) for val in row):
                        gate_type = 'AND'
                    elif any ('XS' in str(val) for val in row):
                        gate_type = 'XOR'
                if gate_type:
                    gate_name = f'{gate_type}_gate_{gate_counter}'
                    elements[gate_name] = gate_type
                    gate_counter += 1
                    print("past1")
                    if element in start_swimlanes:
                        print("past2")
                        swimlane = start_swimlanes[element]
                    elif not df[df['Name'] == element].empty:
                        print("past3")
                        swimlane = df[df['Name'] == element]['Swimlane'].values[0]
                    else:
                        print("past4")
                        swimlane = start_swimlanes[targets[0]]
                    swimlanes[swimlane].insert(swimlanes[swimlane].index(element) + 1, gate_name)
                    final_sequence_flows[element] = [gate_name]
                    final_sequence_flows[gate_name] = targets
                    print(f"Added {elements[gate_name]} '{gate_name}' after '{element}' with targets {targets}")
                else:
                    print("past6")
                    final_sequence_flows[element] = targets
            #else:
                #final_sequence_flows[element] = targets
        else:
            final_sequence_flows[element] = targets
    print("done")
    # Process XOR gates for elements with the same target
    inverted_flows = {}
    for element, targets in final_sequence_flows.items():
        for target in targets:
            if target not in inverted_flows:
                inverted_flows[target] = []
            inverted_flows[target].append(element)
    print("Inverted flows:", inverted_flows)

    updated_sequence_flows = final_sequence_flows.copy()
    for target, elements_with_same_target in inverted_flows.items():
        if len(elements_with_same_target) > 1:
            if not any(not set(elements_with_same_target).isdisjoint(set(inverted_flows[target])) for target in elements_with_same_target):
                xor_gate_name = f'XOR_gate_{gate_counter}'
                elements[xor_gate_name] = 'XOR'
                gate_counter += 1
                for element in elements_with_same_target:
                    updated_sequence_flows[element] = [xor_gate_name]
                    print(f"Updated target of '{element}' to '{xor_gate_name}'")
                updated_sequence_flows[xor_gate_name] = [target]
                print(f"Set target of '{xor_gate_name}' to '{target}'")
                if target in start_swimlanes:
                    swimlane = start_swimlanes[target]
                elif not df[df['Name'] == target].empty:
                    swimlane = df[df['Name'] == target]['Swimlane'].values[0]
                else:
                    swimlane = 'default_swimlane'
                if xor_gate_name not in swimlanes.get(swimlane, []):
                    swimlanes.setdefault(swimlane, []).insert(0, xor_gate_name)
                print(f"Added XOR gate '{xor_gate_name}' before '{target}' with sources {elements_with_same_target}")

    sequence_flows = updated_sequence_flows
    print("Final sequence flows:", sequence_flows)

    # Calculate start y positions for each swimlane
    start_y_positions = {}
    vertical_spacing = 5
    for index, swimlane in enumerate(swimlanes):
        start_y_positions[swimlane] = index * vertical_spacing

    # Initialize positions dictionary
    positions = {}
    horizontal_spacing = 3  # Setting the X-axis spacing
    for swimlane, elements_list in swimlanes.items():
        for index, element in enumerate(elements_list):
            positions[element] = (index * horizontal_spacing, start_y_positions[swimlane])

    # caculate initial position
    visited = set()
    for element in list(positions.keys()):
        calculate_positions(positions, sequence_flows, element, horizontal_spacing, vertical_spacing, visited)

    # one target more outgoings
    target_incoming = {}
    for src, targets in sequence_flows.items():
        for target in targets:
            if target not in target_incoming:
                target_incoming[target] = []
            target_incoming[target].append(src)

    # Ensure that the target element is positioned to the right and in the centre of all source element positions.
    for target, sources in target_incoming.items():
        if len(sources) > 1:
            max_x = max(positions[src][0] for src in sources)
            avg_y = sum(positions[src][1] for src in sources) / len(sources)
            positions[target] = (max_x + horizontal_spacing, avg_y)
            # Reposition the element and press sequence flow again to recalculate.
            visited = set()
            calculate_positions(positions, sequence_flows, target, horizontal_spacing, vertical_spacing, visited)



    # Initialize message_flows
    message_flows = {}
    for index, row in dsm_df.iterrows():
        outgoing_element = index
        target_elements = row[row == 'M'].index.tolist()
        message_flows[outgoing_element] = target_elements



    print(swimlanes)
    print(elements)
    print("Final positions:", positions)

    # Create graph
    G = pgv.AGraph(directed=True)

    for node, pos in positions.items():
        node_type = elements[node]
        shape = 'box'
        style = 'rounded'
        width = '2'
        height = '1'
        if node_type == 'XOR' or node_type == 'AND' or node_type == '?':
            shape = 'diamond'
            style = ''
            width = '0.5'
            height = '1'
            G.add_node(node, pos=f"{pos[0]},{pos[1]}!", shape=shape, style=style, width=width, height=height, label=node_type)
        elif node_type == 'StartEvent' or node_type == 'EndEvent':
            shape = 'circle'
            width = '1'
            height = '1'
            G.add_node(node, pos=f"{pos[0]},{pos[1]}!", shape=shape, style=style, width=width, height=height)
        else:
            G.add_node(node, pos=f"{pos[0]},{pos[1]}!", shape=shape, style=style, width=width, height=height)

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

def correlation_analysis(dmm_process_file, dmm_change_file,dmm_mdt_file, dmm_pa_ca_file, dmm_change_mdt_file, dmm_process_mdt_file, selected_M_DT_file, n, m):
    df1 = pd.read_csv(dmm_process_file)
    df1_names = df1['Name']
    df1 = df1.drop(columns=['Name'])
    df1 = df1.iloc[:, :57]
    df2 = pd.read_csv(dmm_change_file)
    df3 = pd.read_csv(dmm_mdt_file)
    df5 = pd.read_csv(dmm_change_mdt_file)
    df6 = pd.read_csv(dmm_process_mdt_file)
    df7 = pd.read_csv(dmm_pa_ca_file)
    df7 = df7.drop(columns=['PA'])
    df8 = pd.read_csv(selected_M_DT_file, header=None)
    dt_names = df8[0]
    df8 = df8.drop(columns=[0,2])

    dmm_process = df1.values
    dmm_change = df2.values
    change_vector = dmm_change.T
    methode = df8.iloc[:n].values
    digital_tools = df8.iloc[n:].values
    dmm_methode = df3.iloc[:n,1:11].join(df3.iloc[:n,16:])
    dmm_dt = df3.iloc[n:,1:20]
    dmm_PA_CA = df7.values
    dmm_CA_MA = df5.iloc[:, 6:].values
    dmm_CA_DT = df5.iloc[:, 1:6].join(df5.iloc[: , 11:]).values
    dmm_PA_MA= df6.iloc[:, 1:].values
    dmm_PA_DT = df6.iloc[:, 1:].values

    dmm_methode = dmm_methode*methode    
    dmm_dt = dmm_dt*digital_tools

    dmm_method_PA = dmm_methode.iloc[:,:10]
    dmm_method_CA = dmm_methode.iloc[:,10:]
    dmm_dt_PA = dmm_dt.iloc[:,:10]
    dmm_dt_CA = dmm_dt.iloc[:,10:]
    
    #Change related process
    print("Correlation result:")
    R_change = dmm_PA_CA @ change_vector

    R_change_MA = dmm_CA_MA.T @ change_vector
    R_change_DT = dmm_CA_DT.T @ change_vector

    dmm_PA_MA = dmm_PA_MA @ dmm_method_PA.T
    R_process_MA = dmm_process[:,:22] @ dmm_PA_MA
    dmm_PA_DT = dmm_PA_DT @ dmm_dt_PA.T
    R_process_DT = dmm_process[:,:22] @ dmm_PA_DT

    R_change_process = dmm_process @ R_change
    print("Change related process:", R_change_process)

    vector_change_methode = dmm_method_CA @ R_change_MA

    correlation_process_methode = (R_process_MA*np.tile(vector_change_methode,(1,len(df1_names))).T).to_numpy()

    vector_change_methode = vector_change_methode.to_numpy()
    print("vector_change_methode:", vector_change_methode)
    vector_change_DT = dmm_dt_CA @ R_change_DT

    correlation_process_DT = (R_process_DT*np.tile(vector_change_DT,(1,len(df1_names))).T).to_numpy()

    vector_change_DT = vector_change_DT.to_numpy()
    print("vector_change_DT", vector_change_DT)

    
    print("correlation_process_methode", correlation_process_methode)
    
    print("correlation_process_DT", correlation_process_DT)

    combined = pd.DataFrame({
        'Name': df1_names,
        'R_change_process': R_change_process.flatten()
    })

    max_value = np.max(R_change_process) 
    threshold = max_value * 0.85 
    related_process = combined[combined['R_change_process'] > threshold]
    print(related_process)

    methode_names = dt_names[:n]
    dt_names = dt_names[n:]


    df_vector_change_methode = pd.DataFrame({
        'Name': methode_names,
        'vector_change_methode': vector_change_methode.flatten()
    })
    df_vector_change_DT = pd.DataFrame({
        'Name': dt_names,
        'vector_change_DT': vector_change_DT.flatten()
    })

    max_vector_change = {
        'max_vector_change_methode': df_vector_change_methode.loc[
            df_vector_change_methode['vector_change_methode'].idxmax()].to_dict(),
        'max_vector_change_DT': df_vector_change_DT.loc[df_vector_change_DT['vector_change_DT'].idxmax()].to_dict()
    }
  

    df_correlation_process_methode = pd.DataFrame(correlation_process_methode, index=df1_names, columns=methode_names)
    df_correlation_process_DT = pd.DataFrame(correlation_process_DT, index=df1_names, columns=dt_names)
    max_values_info = []

    for name in related_process['Name']:
        max_methode_values = df_correlation_process_methode.loc[name].nlargest(4)
        max_dt_values = df_correlation_process_DT.loc[name].nlargest(4)
        for i in range(0,4):
            max_values_info.append({
                'Name': name,
                'Methods': max_methode_values.index[i],
                'Digital Tools': max_dt_values.index[i],
                'Ranking': i+1,            
            })
        
    max_values_df = pd.DataFrame(max_values_info)
    combined_result = max_values_df.set_index(['Name','Ranking'])
    print(max_values_df)
    
    return max_vector_change, combined_result, max_values_df, related_process

# Usage example
input_path = 'D:/MA/example/bpmn.csv'
svg_path = 'D:/MA/example/bpmnsvg.svg'
#generate_bpmn_svg(input_path, svg_path)

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
SETTING_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings')

dmm_process_file = os.path.join(UPLOAD_FOLDER, 'pa_pi.csv')
dmm_change_file = os.path.join(UPLOAD_FOLDER, 'change_vector.csv')
selected_M_DT_file = os.path.join(UPLOAD_FOLDER, 'digital_tools.csv')
dmm_pa_ca_file = os.path.join(SETTING_FOLDER, 'DMM_PA_CA.csv')
dmm_methode_file = os.path.join(SETTING_FOLDER, 'DMM_Methode.csv')
dmm_dt_file = os.path.join(SETTING_FOLDER, 'DMM_DT.csv')
dmm_change_mdt_file = os.path.join(SETTING_FOLDER, 'DMM_CA_MDT.csv')
dmm_process_mdt_file = os.path.join(SETTING_FOLDER, 'DMM_PA_MDT.csv')

def result_initialization(input_file_path,csv_file_path, Result_Tasks):
    with open(input_file_path, mode='r', newline='', encoding='utf-8') as input, open(csv_file_path, mode='w', newline='', encoding='utf-8') as out:
            inp = csv.DictReader(input) 
            dsm_fieldnames = inp.fieldnames
            writer = csv.DictWriter(out, fieldnames=dsm_fieldnames)
            
            writer.writeheader()

            for row in inp:
                dsm_row = {field: row[field] for field in dsm_fieldnames}
                
                for Task in Result_Tasks:      
                                 
                    if dsm_row['Name'] == Task:
                        
                        writer.writerow(dsm_row)
            input.close
            out.close
    