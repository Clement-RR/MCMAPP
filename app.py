from flask import Flask, render_template, request, redirect, url_for, flash, jsonify,session
import pandas as pd
import os
import time
import datetime
import service
import csv
import webview
import numpy as np
from werkzeug.utils import secure_filename



app = Flask(__name__)
app.secret_key = 'supersecretkey' 

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
SETTING_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings')
CHANGE_RECORD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Change_Record')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['SETTING_FOLDER'] = SETTING_FOLDER
app.config['CHANGE_RECORD_FOLDER'] = CHANGE_RECORD_FOLDER
CSV_FILE_PATH = os.path.join(UPLOAD_FOLDER, 'change_attribute.csv')
PA_PI_CSV_PATH = os.path.join(UPLOAD_FOLDER, 'pa_pi.csv')
DMT_CSV_PATH = os.path.join(UPLOAD_FOLDER, 'digital_tools.csv')
SELECTED_CA_FILE_PATH = os.path.join(UPLOAD_FOLDER, 'selected_CA.csv')
previous_CA_columns = []
selected_MDT = []
MDT = []
ImgPath = []


def initialize_previous_columns():
    global previous_CA_columns
    if os.path.exists(SELECTED_CA_FILE_PATH):
        if os.path.getsize(SELECTED_CA_FILE_PATH) > 0:
            existing_df = pd.read_csv(SELECTED_CA_FILE_PATH)
            previous_CA_columns = list(existing_df.columns)
        else:
            previous_CA_columns = []
    else:
        previous_CA_columns = []

def load_selected_MDT():
    global selected_MDT
    global MDT
    global ImgPath
    if os.path.exists(DMT_CSV_PATH):
        df = pd.read_csv(DMT_CSV_PATH, header=None, names=['label', 'value','path'])
        MDT = df['label'].tolist()
        selected_MDT = df[df['value'] == 1]['label'].tolist()
        ImgPath = df['path'].tolist()
    else:
        selected_MDT = []
        MDT = []
        ImgPath = []


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/input_pa_pis')
def step2_input_pa_pis():
    return render_template('input-papi.html')

@app.route('/select_CA')
def select_CA():
    initialize_previous_columns()
    print(previous_CA_columns)
    return render_template('select-ca.html', previous_CA_columns=previous_CA_columns)

@app.route('/DMT')
def DMT():
    load_selected_MDT()
    return render_template('select-mdt.html', selected_MDT=selected_MDT, MDT=MDT, ImgPath=ImgPath)

@app.route('/addnew')
def addnew():
    return render_template('addnew.html')

@app.route('/input_change')
def input_CA():
    file_path = CSV_FILE_PATH

    # Check if the CSV file exists and has data
    try:
        df = pd.read_csv(file_path)
        if not df.empty:
            # Get the last row of the CSV file (latest entry)
            last_entry = df.iloc[-1].to_dict()
        else:
            last_entry = {}
    except FileNotFoundError:
        last_entry = {}  # If file not found, send an empty dictionary

    initialize_previous_columns()
    print(previous_CA_columns)
    return render_template('input-change.html', previous_CA_columns=previous_CA_columns, last_entry=last_entry)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        session['uploaded_file'] = filename  
        return jsonify({'message': 'File successfully uploaded'}), 200
    return jsonify({'message': 'File upload failed'}), 400

@app.route('/uploadSetting', methods=['GET', 'POST'])
def uploadSetting():
    if 'file' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['SETTING_FOLDER'], filename)
        file.save(file_path)
        session['uploadedSetting_file'] = filename 
        return jsonify({'message': 'File successfully uploaded'}), 200
    return jsonify({'message': 'File upload failed'}), 400

@app.route('/generate_bpmn', methods=['POST'])
def generate_bpmn():
    try:
        if 'uploaded_file' not in session:
            return jsonify({'message': 'No file uploaded'}), 400
        filename = session['uploaded_file']
        input_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)  
        output_folder = app.config['UPLOAD_FOLDER']
        output_svg_path = os.path.join(app.config['OUTPUT_FOLDER'], 'bpmn.svg')
        service.initialize_data_csv(input_file_path, output_folder)
        service.generate_bpmn_svg(input_file_path, output_svg_path)
        return jsonify({'message': 'BPMN successfully generated'}), 200
    except Exception as e:
        return jsonify({'message': f'Error generating BPMN: {e}'}), 500

@app.route('/get_pa_pi_data', methods=['POST'])
def get_pa_pi_data():
    node_id = request.json.get('node_id')
    if os.path.exists(PA_PI_CSV_PATH):
        pa_pi_df = pd.read_csv(PA_PI_CSV_PATH)
        if node_id in pa_pi_df['Name'].values:
            node_data = pa_pi_df.loc[pa_pi_df['Name'] == node_id].to_dict(orient='records')[0]
            
            node_data = {k: (0 if pd.isna(v) else v) for k, v in node_data.items()}
            return jsonify(node_data)
    return jsonify({"message": "Node data not found"}), 404

@app.route('/update_data', methods=['POST'])
def update_data():
    data = request.get_json()
    print("Received data:", data)
    selectedOption = data['selectedOption']
    updates = data['data']

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pa_pi.csv')
    print(f"CSV file path: {file_path}")
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return jsonify({'status': 'error', 'message': 'Data file does not exist.'})

    try:
        df = pd.read_csv(file_path)
        print("DataFrame before update:", df.head())
        if selectedOption in df['Name'].values:
            row_index = df[df['Name'] == selectedOption].index
            print("Row index to update:", row_index)
            if not row_index.empty:
                for item in updates:
                    if item['id'] in df.columns:
                        df.at[row_index[0], item['id']] = int(item['value'])
                print("DataFrame after update:", df.head())
                with open(file_path, 'w') as f:
                    df.to_csv(f, index=False)
                    f.flush()
                    os.fsync(f.fileno())
                time.sleep(0.1)

                df.to_csv(file_path, index=False)  # Ensure writing inside the condition
                return jsonify({'status': 'success', 'message': 'Data updated successfully.'})
            else:
                return jsonify({'status': 'error', 'message': 'Selected option not found.'})
        else:
            return jsonify({'status': 'error', 'message': 'Selected option not found in the data.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})


@app.route('/delete_data', methods=['POST'])
def delete_data():
    data = request.get_json()
    selectedOption = data['selectedOption']

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pa_pi.csv')
    print(f"CSV file path: {file_path}")

    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return jsonify({'status': 'error', 'message': 'Data file does not exist.'})

    try:
        df = pd.read_csv(file_path)
        print("DataFrame before delete:", df.head())

        row_index = df[df['Name'] == selectedOption].index
        if not row_index.empty:
            for col in df.columns:
                if col != 'Name':
                    df.at[row_index[0], col] = ''

        print("DataFrame after delete:", df.head())

        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            df.to_csv(f, index=False)
            f.flush()
            os.fsync(f.fileno())

        time.sleep(0.1)

        return jsonify({'status': 'success', 'message': 'Data deleted successfully.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/select_change_attribute', methods=['POST'])
def select_change_attribute():
    global previous_CA_columns
    data = request.get_json()
    if data and 'ids' in data:
        ids = data['ids']

        previous_CA_columns = ids
        print(previous_CA_columns)

        selected_data_df = pd.DataFrame(columns=ids)
        selected_data_df.to_csv(SELECTED_CA_FILE_PATH, index=False, mode='w')
        try:
            df = pd.read_csv(CSV_FILE_PATH)
            header = df.columns  # Get the column names
        except FileNotFoundError:
            return jsonify({'status': 'error', 'message': 'CSV file not found'})

        # Write the header back to the file, clearing all data but keeping the header
        with open(CSV_FILE_PATH, 'w', encoding='utf-8') as file:
            file.write(','.join(header) + '\n')
        return jsonify({"message": "Attributes saved successfully."})

    return jsonify({"message": "No labels received."})

CHANGE_FILE_PATH = os.path.join(UPLOAD_FOLDER, 'change_vector.csv')
@app.route('/save_change_attribute', methods=['POST'])
def save_change_attribute():
    data = request.get_json()
    data = {key: str(value) for key, value in data.items()}
    file_path = CSV_FILE_PATH

    new_data_df = pd.DataFrame([data])
    new_data_df.to_csv(file_path, index=False, encoding='utf-8')
    filtered_data = {key: value for i, (key, value) in enumerate(data.items()) if i >= 11}
    filtered_data_df = pd.DataFrame([filtered_data])
    filtered_data_df.to_csv(CHANGE_FILE_PATH, index=False, encoding='utf-8')
    return jsonify({'status': 'success'})

@app.route('/save_method_attribute', methods=['POST'])
def save_method_attribute():
    data = request.get_json()
    MDT_data = data[1]
    MDTType = data[0]
    MDTName = data[2]
    tools_file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'digital_tools.csv')
    DMM_MDT_file_path = os.path.join(app.config['SETTING_FOLDER'], 'DMM_MDT.csv')

    load_selected_MDT()
    n=len(MDT[:MDT.index("3D Modeling and Animation")])
    m=len(MDT[MDT.index("3D Modeling and Animation"):])

    if MDTType['MDTType'] == 0:
        df_tools = pd.read_csv(tools_file_path, header=None)
        df_DMM = pd.read_csv(DMM_MDT_file_path, header=None)

        
        print(df_tools)
        df_tools = pd.DataFrame(np.insert(df_tools.values, n, values=[MDTName['MDTName'], '1', ''], axis=0))
        df_DMM = pd.DataFrame(np.insert(df_DMM.values, n+1, values=[MDTName['MDTName'],MDT_data['I1'],MDT_data['I2'],MDT_data['I3'],MDT_data['I4'],MDT_data['I5'],MDT_data['I6'],MDT_data['I7'],MDT_data['I8'],MDT_data['I9'],MDT_data['I10'],MDT_data['DT1'],MDT_data['DT2'],MDT_data['DT3'],MDT_data['DT4'],MDT_data['DT5'],MDT_data['MDT1'],MDT_data['MDT2'],MDT_data['MDT3'],MDT_data['MDT4'],MDT_data['M1'],MDT_data['M2'],MDT_data['M3'],MDT_data['M4'],MDT_data['M5']], axis=0))
        print(df_tools)
        with open(tools_file_path, 'w') as f:
            df_tools.to_csv(f, header=False, index=False, lineterminator='\n')
            f.flush()
            os.fsync(f.fileno())
        time.sleep(0.1)
        with open(DMM_MDT_file_path, 'w') as f:
            df_DMM.to_csv(f, header = False,index=False, lineterminator='\n')
            f.flush()
            os.fsync(f.fileno())
        time.sleep(0.1)
        return jsonify({'status': 'success', 'message': 'Change registered succesfully.'})
    else:
        with open(tools_file_path, mode='a', newline='', encoding='utf-8') as out:
            writer = csv.DictWriter(out, fieldnames=['360-Degree Feedback','1','../static/images/360.png'])
            writer.writerow({'360-Degree Feedback':MDTName['MDTName'],'1':'1','../static/images/360.png':''})
            out.close
        with open(DMM_MDT_file_path, mode='a', newline='', encoding='utf-8') as out:
            writer = csv.DictWriter(out, fieldnames=['','I1','I2','I3','I4','I5','I6','I7','I8','I9','I10','DT1','DT2','DT3','DT4','DT5','MDT1','MDT2','MDT3','MDT4','M1','M2','M3','M4','M5'])
            writer.writerow({'':MDTName['MDTName'],'I1':MDT_data['I1'],'I2':MDT_data['I2'],'I3':MDT_data['I3'],'I4':MDT_data['I4'],'I5':MDT_data['I5'],'I6':MDT_data['I6'],'I7':MDT_data['I7'],'I8':MDT_data['I8'],'I9':MDT_data['I9'],'I10':MDT_data['I10'],'DT1':MDT_data['DT1'],'DT2':MDT_data['DT2'],'DT3':MDT_data['DT3'],'DT4':MDT_data['DT4'],'DT5':MDT_data['DT5'],'MDT1':MDT_data['MDT1'],'MDT2':MDT_data['MDT2'],'MDT3':MDT_data['MDT3'],'MDT4':MDT_data['MDT4'],'M1':MDT_data['M1'],'M2':MDT_data['M2'],'M3':MDT_data['M3'],'M4':MDT_data['M4'],'M5':MDT_data['M5']})
            out.close
        return jsonify({'status': 'success', 'message': 'Change registered succesfully.'})
    
    

@app.route('/save_DMT', methods=['POST'])
def save_DMT():
    global selected_MDT
    data = request.get_json()
    labels = data.get('labels', [])
    selected_MDT = labels

    df = pd.DataFrame(labels)
    df.to_csv(DMT_CSV_PATH, index=False, mode='w', header=not os.path.exists(DMT_CSV_PATH))

    return jsonify({"status": "success", "message": "Attributes saved successfully."})

@app.route('/result')
def result():
    dmm_process_file = os.path.join(UPLOAD_FOLDER, 'pa_pi.csv')
    dmm_change_file = os.path.join(UPLOAD_FOLDER, 'change_vector.csv')
    dmm_mdt_file = os.path.join(SETTING_FOLDER, 'DMM_MDT.csv')
    selected_M_DT_file = os.path.join(UPLOAD_FOLDER, 'digital_tools.csv')
    dmm_pa_ca_file = os.path.join(SETTING_FOLDER, 'DMM_PA_CA.csv')
    dmm_change_mdt_file = os.path.join(SETTING_FOLDER, 'DMM_CA_MDT_New.csv')
    dmm_process_mdt_file = os.path.join(SETTING_FOLDER, 'DMM_PA_MDT_New.csv')
    load_selected_MDT()
    n=len(MDT[:MDT.index("3D Modeling and Animation")])
    m=len(MDT[MDT.index("3D Modeling and Animation"):])

    max_vector_change, combined_result, ResultList, related_process = service.correlation_analysis(
        dmm_process_file, dmm_change_file, dmm_mdt_file, dmm_pa_ca_file, dmm_change_mdt_file, dmm_process_mdt_file, selected_M_DT_file,
        n, m
    )
    try:
        #if 'inputdsm.csv' not in app.config['UPLOAD_FOLDER']:
            #return jsonify({'message': 'No file uploaded'}), 400
        filename = 'inputdsm.csv'
        input_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        csv_file_path =   os.path.join(app.config['UPLOAD_FOLDER'], 'result_bpmn.csv')
        Result_Tasks = related_process['Name']
        output_svg_path = os.path.join(app.config['OUTPUT_FOLDER'], 'result_bpmn.svg')
        service.result_initialization(input_file_path,csv_file_path , Result_Tasks)
        service.generate_bpmn_svg(csv_file_path, output_svg_path)
    except Exception as e:
        return jsonify({'message': f'Error generating BPMN: {e}'}), 500
   

    global DoneNodes
    if os.path.exists(os.path.join(app.config['OUTPUT_FOLDER'], 'Change_record.csv')):
        change_attribute_file = os.path.join(UPLOAD_FOLDER, 'change_attribute.csv')
        changeID = pd.read_csv(change_attribute_file)['changeId'][0]
        df = pd.read_csv(os.path.join(app.config['OUTPUT_FOLDER'], 'Change_record.csv'))        
        print(df.loc[df['Change ID'] == changeID])
        DoneNodes = df.loc[df['Change ID'] == changeID]['Process step'].tolist()
        
        print(DoneNodes)
    else:
        DoneNodes = []

    comb= ResultList.to_numpy().tolist()
    load_selected_MDT()
    return render_template('result.html', max_vector_change=max_vector_change,
                           combined_result=combined_result.to_html(index=True, header=True, justify='left', classes='combined_result_table'), comb_res=comb, MDT=MDT, ImgPath=ImgPath, DoneNodes=DoneNodes)

@app.route('/save_lessons_learned', methods=['POST'])
def save_lessons_learned():
    data = request.get_json()['data']
    change_attribute_file = os.path.join(UPLOAD_FOLDER, 'change_attribute.csv')
    changeID = pd.read_csv(change_attribute_file)['changeId'][0]
    print("Received data:", data)
    file_path = os.path.join(app.config['CHANGE_RECORD_FOLDER'], 'Change_record.csv')
    print(f"CSV file path: {file_path}")
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='', encoding='utf-8') as out:
            writer = csv.DictWriter(out, fieldnames=['Change ID','Process step','Date','Time','Responsible','Method or digital tool','Lessons learned'])
            writer.writeheader()
            writer.writerow({'Change ID':changeID,'Process step':data['Name'],'Date':datetime.datetime.now().strftime("%x"),'Time':datetime.datetime.now().strftime("%X"),'Responsible':data['responsible'],'Method or digital tool':data['MDT'],'Lessons learned':data['lessonsLearned']})
            out.close
        return jsonify({'status': 'success', 'message': 'Change record created and change registered succesfully.'})

    try:
        df = pd.read_csv(file_path)
        print("DataFrame before update:", df.head())
        if changeID in df['Change ID'].values:       
            if not df[(df['Process step'] == data['Name']) & (df['Change ID'] == changeID)].empty:
                row_index = df[(df['Process step'] == data['Name']) & (df['Change ID'] == changeID)].index
                print("Row index to update:", row_index)
                if not row_index.empty:
                    df.at[row_index[0], 'Date'] = datetime.datetime.now().strftime("%x")
                    df.at[row_index[0], 'Time'] = datetime.datetime.now().strftime("%X")
                    df.at[row_index[0], 'Responsible'] = data['responsible']
                    df.at[row_index[0], 'Method or digital tool'] = data['MDT']
                    df.at[row_index[0], 'Lessons learned'] = data['lessonsLearned']
                    print("DataFrame after update:", df.head())
                    with open(file_path, 'w') as f:
                        df.to_csv(f, index=False)
                        f.flush()
                        os.fsync(f.fileno())
                    time.sleep(0.1)

                    df.to_csv(file_path, index=False)  # Ensure writing inside the condition
                    return jsonify({'status': 'success', 'message': 'Lessons learned updated successfully.'})
                else:
                    return jsonify({'status': 'error', 'message': 'Selected option not found in the data.'})
            else:
                with open(file_path, mode='a', newline='', encoding='utf-8') as out:
                    writer = csv.DictWriter(out, fieldnames=['Change ID','Process step','Date','Time', 'Responsible', 'Method or digital tool', 'Lessons learned'])
                    writer.writerow({'Change ID':changeID,'Process step':data['Name'],'Date':datetime.datetime.now().strftime("%x"),'Time':datetime.datetime.now().strftime("%X"),'Responsible':data['responsible'],'Method or digital tool':data['MDT'], 'Lessons learned':data['lessonsLearned']})
                    out.close
                return jsonify({'status': 'success', 'message': 'Change completion registered succesfully.'})
        else:
            with open(file_path, mode='a', newline='', encoding='utf-8') as out:
                writer = csv.DictWriter(out, fieldnames=['Change ID','Process step','Date','Time', 'Responsible', 'Method or digital tool', 'Lessons learned'])
                writer.writerow({'Change ID':changeID,'Process step':data['Name'],'Date':datetime.datetime.now().strftime("%x"),'Time':datetime.datetime.now().strftime("%X"),'Responsible':data['responsible'],'Method or digital tool':data['MDT'], 'Lessons learned':data['lessonsLearned']})
                out.close
            return jsonify({'status': 'success', 'message': 'Change registered succesfully.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/delete_process_step', methods=['POST'])
def delete_process_step():
    change_record_file = os.path.join(app.config['OUTPUT_FOLDER'], 'Change_record.csv')
    df = pd.read_csv(change_record_file)
    df = df.drop(df.index[-1])
    df.to_csv(change_record_file, index=False)
    return jsonify({'status': 'success', 'message': 'Change deleted succesfully.'})
    


if __name__ == '__main__':
    webview.settings['ALLOW_DOWNLOADS'] = True
    webview.create_window('MCMAPP', app)
    webview.start()

