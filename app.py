from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import pandas as pd
import os
import time
from dsm2bpmn import initialize_and_generate_svg

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # 用于闪现消息

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
@app.route('/')
def home():
    return render_template('start_page.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file:
            input_file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            output_csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'data.csv')
            output_svg_path = os.path.join(app.config['OUTPUT_FOLDER'], 'bpmn.svg')
            file.save(input_file_path)
            flash('File successfully uploaded')
            initialize_and_generate_svg(input_file_path, output_csv_path, output_svg_path)
            return redirect(url_for('upload'))
    return render_template('upload.html')

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
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'data.csv')
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


if __name__ == '__main__':
    app.run(debug=True)
