import pandas as pd

# 定义矩阵
DMM_PA_CA = [
    [2, 0, 1, 3],
    [1, 3, 2, 0],
    [4, 1, 0, 2],
    [3, 2, 1, 1],
    [0, 1, 4, 3]
]

DMM_Change_CA = [
    [1, 0, 1, 0],
    [0, 1, 0, 1],
    [1, 1, 0, 0]
]

DMM_Process_PA = [
    [1, 0, 1, 0, 1],
    [0, 1, 0, 1, 0],
    [1, 1, 0, 0, 1],
    [0, 0, 1, 1, 1]
]

# 转换为DataFrame
df_DMM_PA_CA = pd.DataFrame(DMM_PA_CA, columns=["CA1", "CA2", "CA3", "CA4"])
df_DMM_Change_CA = pd.DataFrame(DMM_Change_CA, columns=["CA1", "CA2", "CA3", "CA4"])
df_DMM_Process_PA = pd.DataFrame(DMM_Process_PA, columns=["PA1", "PA2", "PA3", "PA4", "PA5"])

# 保存为CSV文件
df_DMM_PA_CA.to_csv('D:/MA/example/DMM_PA_CA.csv', index=False)
df_DMM_Change_CA.to_csv('D:/MA/example/DMM_Change_CA.csv', index=False)
df_DMM_Process_PA.to_csv('D:/MA/example/DMM_Process_PA.csv', index=False)
