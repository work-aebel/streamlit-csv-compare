import streamlit as st
import pandas as pd
import xlsxwriter


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

    if 'UID' not in df_a.columns or 'UID' not in df_b.columns:
        return False, "UID column not found in one or both CSVs."

    return True, None

def compare_csvs(csv_a, csv_b):
    csv_a.seek(0)
    csv_b.seek(0)
    df1 = pd.read_csv(csv_a)
    df2 = pd.read_csv(csv_b)

    matched_uids = []
    non_matched_uids = []
    non_matched_uid_fields = {}

    for index, row in df1.iterrows():
        print(f"Row index: {index}")

        uuid = row['UID']
        df2_row = df2[df2['UID'] == uuid]

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
    filtered_df1 = df1[df1['UID'].isin(non_matched_uids)]
    filtered_df2 = df2[df2['UID'].isin(non_matched_uids)]

    filtered_df1.insert(0,'Source',csv_a_source)
    filtered_df2.insert(0,'Source',csv_b_source)
    filtered_df1.insert(0,'Inital',text_input1)
    filtered_df2.insert(0,'Inital',text_input2)

    concatenated_df = pd.concat([filtered_df1, filtered_df2], ignore_index=True)
    ordered_df = concatenated_df.sort_values(by='UID')
    ordered_df = ordered_df.reset_index(drop=True)

    move_uid = ordered_df.pop("UID")
    ordered_df.insert(0,"UID",move_uid)

    #print(ordered_df)

    #conparedf = (df1.compare(df2))
    #conparedf.to_csv('mycsv.csv')

    writer = pd.ExcelWriter('errors.xlsx', engine='xlsxwriter')
    # Convert the DataFrame to an Excel object
    ordered_df.to_excel(writer, sheet_name='Sheet1', index=False)

    # Get the xlsxwriter workbook and worksheet objects
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    # Add a format for highlighted cells
    highlight_format = workbook.add_format({'bg_color': '#FFC7CE'})

    for index, row in ordered_df.iterrows():
        if index % 2 == 0:
            continue
        uid = row['UID']
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

# Function to generate and download an Excel file
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
            matched_df = df1[df1['UID'].isin(matched_uids)]
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
