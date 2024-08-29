import pandas as pd
import numpy as np
import os

def correlation_analysis(dmm_process_file, dmm_change_file, dmm_methode_file, dmm_dt_file, dmm_pa_ca_file, dmm_change_mdt_file, dmm_process_mdt_file, selected_M_DT_file):
    df1 = pd.read_csv(dmm_process_file)
    df1_names = df1['Name']
    df1 = df1.drop(columns=['Name'])
    df2 = pd.read_csv(dmm_change_file)
    df3 = pd.read_csv(dmm_methode_file)
    df4 = pd.read_csv(dmm_dt_file)
    df5 = pd.read_csv(dmm_change_mdt_file)
    df6 = pd.read_csv(dmm_process_mdt_file)
    df7 = pd.read_csv(dmm_pa_ca_file)
    df7 = df7.drop(columns=['PA'])
    df8 = pd.read_csv(selected_M_DT_file, header=None)
    dt_names = df8[0]
    df8 = df8.drop(columns=[0])

    n = 5 #Zahl der MA
    m = 5 #Zahl der Methode
    dmm_process = df1.values
    dmm_change = df2.values
    change_vector = dmm_change.T
    methode = df8.iloc[:m].values
    digital_tools = df8.iloc[m:].values
    dmm_methode = df3.iloc[:, 1:].values
    dmm_dt = df4.iloc[:, 1:].values
    dmm_PA_CA = df7.values
    dmm_CA_MA = df5.iloc[:, 1:n+1].values
    dmm_CA_DT = df5.iloc[:, n+1:].values
    dmm_PA_MA= df6.iloc[:, 1:n+1].values
    dmm_PA_DT = df6.iloc[:, n+1:].values

    dmm_methode = dmm_methode*methode
    dmm_dt = dmm_dt*digital_tools

    print("Correlation result:")
    R_change = dmm_PA_CA @ change_vector
    R_CA_process = dmm_process @ dmm_PA_CA
    flex_process = R_CA_process @ change_vector
    print("changeable process:", flex_process)
    R_change_MA = dmm_CA_MA.T @ change_vector
    R_change_DT = dmm_CA_DT.T @ change_vector
    R_process_MA = dmm_process @ dmm_PA_MA
    R_process_DT = dmm_process @ dmm_PA_DT
    R_change_process = dmm_process @ R_change
    print("Change related process:", R_change_process)
    vector_change_methode = dmm_methode @ R_change_MA
    print("vector_change_methode:", vector_change_methode)
    vector_change_DT = dmm_dt @ R_change_DT
    print("vector_change_DT", vector_change_DT)

    correlation_process_methode = R_process_MA @ dmm_methode.T
    print("correlation_process_methode", correlation_process_methode)
    correlation_process_DT = R_process_DT @ dmm_dt.T
    print("correlation_process_DT", correlation_process_DT)

    combined = pd.DataFrame({
        'Name': df1_names,
        'R_change_process': R_change_process.flatten()
    })

    # Filter and print values greater than 30000
    related_process = combined[combined['R_change_process'] > 30000]
    print(related_process)

    methode_names = dt_names[:m]
    dt_names = dt_names[m:]


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
    print(max_vector_change)

    df_correlation_process_methode = pd.DataFrame(correlation_process_methode, index=df1_names, columns=methode_names)
    df_correlation_process_DT = pd.DataFrame(correlation_process_DT, index=df1_names, columns=dt_names)

    max_values_info = []

    for name in related_process['Name']:
        max_methode_value = df_correlation_process_methode.loc[name].max()
        max_methode_column = df_correlation_process_methode.loc[name].idxmax()
        max_dt_value = df_correlation_process_DT.loc[name].max()
        max_dt_column = df_correlation_process_DT.loc[name].idxmax()

        max_values_info.append({
            'Name': name,
            'Methode': max_methode_column,
            'methode_value': max_methode_value,
            'DT': max_dt_column,
            'DT_value': max_dt_value
        })

    print(max_values_info)
    max_values_df = pd.DataFrame(max_values_info)
    combined_result = related_process.merge(max_values_df, on='Name')
    print(combined_result)
    return(max_vector_change, combined_result)

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


correlation_analysis(dmm_process_file, dmm_change_file, dmm_methode_file, dmm_dt_file,dmm_pa_ca_file, dmm_change_mdt_file, dmm_process_mdt_file, selected_M_DT_file)