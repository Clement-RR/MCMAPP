import csv

def initialize_data_csv():
    input_file = 'uploads/bpmn.csv'
    output_file = 'data.csv'
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

if __name__ == "__main__":
    initialize_data_csv()
