import streamlit as st
import pandas as pd
import xlsxwriter

def compare_headers(df_a,df_b):
    headers_df1 = set(df_a.columns)
    headers_df2 = set(df_b.columns)
    
    missing_in_df2 = headers_df1 - headers_df2
    missing_in_df1 = headers_df2 - headers_df1
    
    if not missing_in_df2 and not missing_in_df1:
        return True, ""
    
    differences = []
    if missing_in_df2:
        differences.append(f"Columns in CSV 1 but not in CSV 2: {', '.join(missing_in_df2)}")
    if missing_in_df1:
        differences.append(f"Columns in CSV 2 but not in CSV 1: {', '.join(missing_in_df1)}")
    
    return False, "; ".join(differences)


def validate_csvs(csv_a, csv_b):
    if csv_a is None or csv_b is None:
        return False, "One or both CSV files are empty."

    df_a = pd.read_csv(csv_a)
    df_b = pd.read_csv(csv_b)

    st.subheader("Preview of CSV 1:")
    st.write(df_a.head(4))

    st.subheader("Preview of CSV 2:")
    st.write(df_b.head(4))

    if df_a.shape != df_b.shape:
        return False, "Number of rows or columns in CSVs are not the same."
    
    compr_headers, messages = compare_headers(df_a,df_b)
    if not compr_headers:
        return False, messages


    return True, None

def compare_csvs(csv_a, csv_b):
    csv_a.seek(0)
    csv_b.seek(0)
    df1 = pd.read_csv(csv_a)
    df2 = pd.read_csv(csv_b)

    df1['Row']  = df1.index + 1
    df2['Row']  = df2.index + 1

    matched_uids = []
    non_matched_uids = []
    non_matched_uid_fields = {}

    for index, row in df1.iterrows():
        print(f"Row index: {index}")

        uuid = row['Row']
        df2_row = df2[df2['Row'] == uuid]

        matched = True
        for col in df1.columns:
            df2_val = df2_row[col].values
            df1_val = row[col]

            if df2_val == df1_val:
                pass
            else:
                matched = False
                if uuid not in non_matched_uid_fields:
                    non_matched_uid_fields[uuid] = {col:[df1_val,df2_val.item()]}
                else:
                    non_matched_uid_fields[uuid][col] = [df1_val,df2_val.item()]
                
        if not matched:
            non_matched_uids.append(uuid)
        else:
            matched_uids.append(uuid)
    
    return non_matched_uid_fields, non_matched_uids, matched_uids, df1, df2

def nonmatching(non_matched_uids,non_matched_uid_fields,df1,df2,csv_b_source,csv_a_source,text_input1,text_input2):
    filtered_df1 = df1[df1['Row'].isin(non_matched_uids)]
    filtered_df2 = df2[df2['Row'].isin(non_matched_uids)]

    filtered_df1.insert(0,'Source',csv_a_source)
    filtered_df2.insert(0,'Source',csv_b_source)
    filtered_df1.insert(0,'Initial',text_input1)
    filtered_df2.insert(0,'Initial',text_input2)

    concatenated_df = pd.concat([filtered_df1, filtered_df2], ignore_index=True)
    ordered_df = concatenated_df.sort_values(by='Row')
    ordered_df = ordered_df.reset_index(drop=True)

    move_uid = ordered_df.pop("Row")
    ordered_df.insert(0,"Row",move_uid)

    #print(ordered_df)

    #conparedf = (df1.compare(df2))
    #conparedf.to_csv('mycsv.csv')
                        
    
    writer = pd.ExcelWriter('errors.xlsx', engine='xlsxwriter',engine_kwargs={'options': {'nan_inf_to_errors': True}})
    # Convert the DataFrame to an Excel object
    ordered_df.to_excel(writer, sheet_name='Sheet1', index=False)

    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    highlight_format = workbook.add_format({'bg_color': '#FFC7CE'})

    for index, row in ordered_df.iterrows():
        if index % 2 == 0:
            continue
        uid = row['Row']
        column_dict = non_matched_uid_fields[uid]
        for col, v in column_dict.items():
            column_index = ordered_df.columns.get_loc(col)
            tmp_index = index
            for value in v:
                worksheet.write(tmp_index, column_index, value, highlight_format)
                tmp_index += 1
    writer._save()


def download_csv(data):
    st.download_button(
        label='Success Report',
        data=data,
        file_name='sucess.csv',
        mime='text/csv'
    )

def download_excel_file(file_path, file_label):
    with open(file_path, "rb") as file:
        file_content = file.read()
    st.download_button(
        label=file_label,
        data=file_content,
        file_name=file_path.split("/")[-1],  # Extracting file name from file path
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )



def main():
    st.title("CSV Compare Tool")

    st.sidebar.title("Upload CSV Files")
    csv_a = st.sidebar.file_uploader("Upload CSV 1", type=["csv"])
    text_input1 = st.sidebar.text_input("Transcriber 1 Initials (i.e. AC)", value="AC")

    csv_b = st.sidebar.file_uploader("Upload CSV 2", type=["csv"])
    text_input2 = st.sidebar.text_input("Transcriber 2 Initials (i.e. KL)", value="KL")

    if csv_a is not None and csv_b is not None:
        validation_result, validation_message = validate_csvs(csv_a, csv_b)
        csv_a_source = csv_a.name
        csv_b_source = csv_b.name

        if validation_result:
            st.success("CSVs validated successfully!")


            # Button to initiate comparison
            non_matched_uid_fields, non_matched_uids, matched_uids, df1, df2  = compare_csvs(csv_a, csv_b) 
            matched_df = df1[df1['Row'].isin(matched_uids)]
            matched_df.drop('Row',axis=1,inplace=True)
            #matched_output = matched_df.to_csv('success.csv', index=False)
            matched_output = matched_df.to_csv(index=False).encode()
            nonmatching(non_matched_uids,non_matched_uid_fields,df1,df2,csv_b_source,csv_a_source,text_input1,text_input2)
            st.success(f"Comparison complete. Files generated.")
            download_csv(matched_output)
            download_excel_file('errors.xlsx', 'Error Report')

        else:
            st.error(f"Validation failed: {validation_message}")

if __name__ == "__main__":
    main()
