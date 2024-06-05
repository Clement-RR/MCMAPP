from flask import Flask, render_template, request, redirect, url_for, flash, jsonify,session
import pandas as pd
import os
import time
from dsm2bpmn import initialize_data_csv, generate_bpmn_svg
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # 用于闪现消息

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
@app.route('/')
def home():
    return render_template('start_page.html')

@app.route('/initialization')
def initialization():
    return render_template('initialization.html')

@app.route('/input_with_dsm')
def input_with_dsm():
    return render_template('input_with_dsm.html')

@app.route('/step2_input_pa_pis')
def step2_input_pa_pis():
    return render_template('step2_input_pa_pis.html')

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

@app.route('/next_step')
def next_step():
    return render_template('index.html')


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


if __name__ == '__main__':
    app.run(debug=True)
