from flask import Flask, render_template, request, redirect, url_for, flash, jsonify,session
import pandas as pd
import os
import time
import service
from werkzeug.utils import secure_filename
import csv

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # 用于闪现消息

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
SETTING_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['SETTING_FOLDER'] = SETTING_FOLDER
CSV_FILE_PATH = os.path.join(UPLOAD_FOLDER, 'change_attribute.csv')
PA_PI_CSV_PATH = os.path.join(UPLOAD_FOLDER, 'pa_pi.csv')
DMT_CSV_PATH = os.path.join(UPLOAD_FOLDER, 'digital_tools.csv')
SELECTED_CA_FILE_PATH = os.path.join(UPLOAD_FOLDER, 'selected_CA.csv')
previous_CA_columns = []
selected_MDT = []


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
    if os.path.exists(DMT_CSV_PATH):
        df = pd.read_csv(DMT_CSV_PATH, header=None, names=['label', 'value'])
        selected_MDT = df[df['value'] == 1]['label'].tolist()
    else:
        selected_MDT = []


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/start_page')
def start_page():
    return render_template('index.html')




@app.route('/input_pa_pis')
def step2_input_pa_pis():
    return render_template('input_papi.html')

@app.route('/select_CA')
def select_CA():
    initialize_previous_columns()
    print(previous_CA_columns)
    return render_template('select_CA.html', previous_CA_columns=previous_CA_columns)

@app.route('/DMT')
def DMT():
    load_selected_MDT()
    return render_template('DMT.html', selected_MDT=selected_MDT)

@app.route('/input_CA')
def input_CA():
    initialize_previous_columns()
    return render_template('input_CA.html', previous_CA_columns=previous_CA_columns)

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
        session['uploaded_file'] = filename  # 保存上传的文件名到 session
        return jsonify({'message': 'File successfully uploaded'}), 200
    return jsonify({'message': 'File upload failed'}), 400

@app.route('/generate_bpmn', methods=['POST'])
def generate_bpmn():
    try:
        if 'uploaded_file' not in session:
            return jsonify({'message': 'No file uploaded'}), 400
        filename = session['uploaded_file']
        input_file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # 这里需要根据实际情况修改
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
            # 将空值替换为0
            node_data = {k: (0 if pd.isna(v) else v) for k, v in node_data.items()}
            return jsonify(node_data)
    return jsonify({"message": "Node data not found"}), 404

@app.route('/update_data', methods=['POST'])
def update_data():
    # 读取 JSON 数据
    data = request.get_json()
    print("Received data:", data)
    selectedOption = data['selectedOption']
    updates = data['data']

    # 指定 CSV 文件路径
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pa_pi.csv')
    print(f"CSV file path: {file_path}")
    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return jsonify({'status': 'error', 'message': 'Data file does not exist.'})

    try:
        # 读取 CSV 文件
        df = pd.read_csv(file_path)
        print("DataFrame before update:", df.head())
        # 检查 'Name' 列中是否包含 selectedOption
        if selectedOption in df['Name'].values:
            row_index = df[df['Name'] == selectedOption].index
            print("Row index to update:", row_index)
            if not row_index.empty:
                for item in updates:
                    if item['id'] in df.columns:
                        df.at[row_index[0], item['id']] = int(item['value'])
                print("DataFrame after update:", df.head())
                # 写回 CSV 文件并刷新文件系统缓冲区
                with open(file_path, 'w') as f:
                    df.to_csv(f, index=False)
                    f.flush()
                    os.fsync(f.fileno())
                # 添加短暂的延迟
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

    # 指定 pa_pi.csv 文件路径
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'pa_pi.csv')
    print(f"CSV file path: {file_path}")

    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return jsonify({'status': 'error', 'message': 'Data file does not exist.'})

    try:
        # 读取 CSV 文件
        df = pd.read_csv(file_path)
        print("DataFrame before delete:", df.head())

        # 清空指定行的除 'Name' 列以外的数据
        row_index = df[df['Name'] == selectedOption].index
        if not row_index.empty:
            for col in df.columns:
                if col != 'Name':
                    df.at[row_index[0], col] = ''

        print("DataFrame after delete:", df.head())

        # 写回 CSV 文件
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            df.to_csv(f, index=False)
            f.flush()
            os.fsync(f.fileno())

        # 添加短暂的延迟
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

        # 更新 previous_CA_columns
        previous_CA_columns = ids
        print(previous_CA_columns)

        # 现在将传入的数据保存到selected_CA.csv文件，覆盖之前的内容
        selected_data_df = pd.DataFrame(columns=ids)
        selected_data_df.to_csv(SELECTED_CA_FILE_PATH, index=False, mode='w')

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

@app.route('/get_change_attribute_data', methods=['GET'])
def get_change_attribute_data():
    if os.path.exists(CSV_FILE_PATH) and os.path.getsize(CSV_FILE_PATH) > 0:
        df = pd.read_csv(CSV_FILE_PATH).replace({np.nan: None})
        data = df.to_dict(orient='records')
        print("Data sent to frontend:", data)
        return jsonify(data)
    else:
        return jsonify([])

@app.route('/delete_change_attribute', methods=['POST'])
def delete_change_attribute():
    file_path = CSV_FILE_PATH
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        df = pd.read_csv(file_path)
        if not df.empty:
            # 删除第一行
            df = df.iloc[1:]
            df.to_csv(file_path, index=False, encoding='utf-8')
            return jsonify({'status': 'success', 'message': 'Data deleted successfully.'})
        else:
            return jsonify({'status': 'error', 'message': 'File is already empty.'})
    else:
        return jsonify({'status': 'error', 'message': 'File not found.'})


@app.route('/save_DMT', methods=['POST'])
def save_DMT():
    global selected_MDT
    data = request.get_json()
    labels = data.get('labels', [])

    selected_MDT = labels

    # 创建 DataFrame 并保存到 CSV 文件
    df = pd.DataFrame(labels)
    df.to_csv(DMT_CSV_PATH, index=False, mode='w', header=not os.path.exists(DMT_CSV_PATH))

    return jsonify({"status": "success", "message": "Attributes saved successfully."})

@app.route('/result')
def result():
    dmm_process_file = os.path.join(UPLOAD_FOLDER, 'pa_pi.csv')
    dmm_change_file = os.path.join(UPLOAD_FOLDER, 'change_vector.csv')
    selected_M_DT_file = os.path.join(UPLOAD_FOLDER, 'digital_tools.csv')
    dmm_pa_ca_file = os.path.join(SETTING_FOLDER, 'DMM_PA_CA.csv')
    dmm_methode_file = os.path.join(SETTING_FOLDER, 'DMM_Methode.csv')
    dmm_dt_file = os.path.join(SETTING_FOLDER, 'DMM_DT.csv')
    dmm_change_mdt_file = os.path.join(SETTING_FOLDER, 'DMM_CA_MDT.csv')
    dmm_process_mdt_file = os.path.join(SETTING_FOLDER, 'DMM_PA_MDT.csv')

    max_vector_change, combined_result, name_color_dict = service.correlation_analysis(
        dmm_process_file, dmm_change_file, dmm_methode_file, dmm_dt_file,
        dmm_pa_ca_file, dmm_change_mdt_file, dmm_process_mdt_file, selected_M_DT_file
    )
    combined_result_filtered = combined_result[
        ['Name', 'Methode_1', 'methode_value_1', 'Methode_2', 'methode_value_2', 'DT_1', 'DT_value_1', 'DT_2',
         'DT_value_2']]
    return render_template('result.html', max_vector_change=max_vector_change,
                           combined_result=combined_result_filtered.to_html(index=False), name_color_dict=name_color_dict)

if __name__ == '__main__':
    app.run(debug=True)

