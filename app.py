from flask import Flask, render_template, request, redirect, url_for, flash, jsonify,session
import pandas as pd
import os
import time
from dsm2bpmn import initialize_data_csv, generate_bpmn_svg
from werkzeug.utils import secure_filename
import csv

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # 用于闪现消息

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
CSV_FILE_PATH = os.path.join(UPLOAD_FOLDER, 'change_attribute.csv')
previous_CA_columns = []


change_attribute_columns = [
    'changeName', 'changeId', 'changeDescription', 'responsibility', 'timeframe', 'changeCause',
    'localization', 'departments', 'changeStatus', 'timeOfOccurrence', 'lessonsLearned',
]

def initialize_previous_columns():
    global previous_CA_columns
    if os.path.exists(CSV_FILE_PATH):
        existing_df = pd.read_csv(CSV_FILE_PATH)
        # 过滤出非预定义的列标签
        previous_CA_columns = [col for col in existing_df.columns if col not in change_attribute_columns]


@app.route('/')
def home():
    return render_template('start_page.html')


@app.route('/initialization')
def initialization():
    return render_template('initialization.html')

@app.route('/input_with_dsm')
def input_with_dsm():
    return render_template('input_with_dsm.html')

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
    return render_template('DMT.html')

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
        initialize_data_csv(input_file_path, output_folder)
        generate_bpmn_svg(input_file_path, output_svg_path)
        return jsonify({'message': 'BPMN successfully generated'}), 200
    except Exception as e:
        return jsonify({'message': f'Error generating BPMN: {e}'}), 500


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
    if data and 'labels' in data:
        labels = data['labels']

        if os.path.exists(CSV_FILE_PATH):
            # 如果CSV文件存在，则读取现有的列标签
            existing_df = pd.read_csv(CSV_FILE_PATH)
            existing_CA_columns = list(existing_df.columns)
        else:
            # 如果CSV文件不存在，则初始化为空列表
            existing_CA_columns = []

        # 移除上一次写入的列标题
        for col in previous_CA_columns:
            if col in existing_CA_columns:
                existing_CA_columns.remove(col)

        previous_CA_columns = labels
        print(previous_CA_columns)
        # 合并现有列标签和新标签，去重
        new_columns = existing_CA_columns + labels

        # 创建一个新的DataFrame，只包含合并后的列标签
        df = pd.DataFrame(columns=new_columns)

        # 保存到CSV文件
        df.to_csv(CSV_FILE_PATH, index=False)

        return jsonify({"message": "Attributes saved successfully."})
    return jsonify({"message": "No labels received."})

@app.route('/save_change_attribute', methods=['POST'])
def save_change_attribute():
    data = request.get_json()
    data = {key: str(value) for key, value in data.items()}
    change_id = data['changeId']
    file_path = os.path.join(UPLOAD_FOLDER, 'change_attribute.csv')
    new_entry = pd.DataFrame([data])

    # 如果文件存在，则读取现有数据并追加新的数据
    if os.path.isfile(file_path):
        existing_data = pd.read_csv(file_path, dtype=str)
        if change_id in existing_data['changeId'].values:
            return jsonify({'status': 'error', 'message': 'Change ID already exists.'})
        combined_data = pd.concat([existing_data, new_entry], ignore_index=True)
    else:
        combined_data = new_entry

    # 写回 CSV 文件
    combined_data.to_csv(file_path, index=False, encoding='utf-8')

    return jsonify({'status': 'success'})

@app.route('/get_change_attribute', methods=['GET'])
def get_change_attribute():
    file_path = os.path.join(UPLOAD_FOLDER, 'change_attribute.csv')
    print(f"File path: {file_path}")  # 输出文件路径
    if os.path.exists(file_path):
        df = pd.read_csv(file_path, dtype=str)
        print(df.head())  # 打印前几行数据进行调试
        data = df[['changeName', 'changeId']].to_dict(orient='records')
        print(data)  # 打印数据进行调试
        return jsonify(data)
    else:
        print("File not found")
        return jsonify([])

@app.route('/delete_change_attribute', methods=['POST'])
def delete_change_attribute():
    data = request.get_json()
    change_id = str(data.get('changeId'))

    file_path = os.path.join(UPLOAD_FOLDER, 'change_attribute.csv')
    if not os.path.isfile(file_path):
        return jsonify({'status': 'error', 'message': 'File not found.'})

    df = pd.read_csv(file_path, dtype=str)

    print(f"DataFrame:\n{df}")
    print(f"Change ID to delete: {change_id}")

    # 检查 changeId 是否在 DataFrame 中
    if change_id not in df['changeId'].astype(str).values:
        return jsonify({'status': 'error', 'message': 'Change ID not found.'})

    # 删除匹配的行
    df = df[df['changeId'].astype(str) != change_id]

    # 写回 CSV 文件
    df.to_csv(file_path, index=False, encoding='utf-8')

    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(debug=True)
