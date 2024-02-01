from datetime import datetime

import streamlit as st
import pandas as pd
import os
from pathlib import Path
from main import main11, get_all_files_list, make_zip
from PAE import version


def print_info(msg: str):
    st.info(msg, icon="ℹ️")


def main():
    st.title("Pattern Auto-Edit Tool Web App Beta" + version)
    st.caption('Powered by Streamlit, written by Chao Zhou')
    st.subheader("", divider='rainbow')
    if "FileList" not in st.session_state:
        st.session_state["FileList"] = []
    if "CSVFileTab" not in st.session_state:
        st.session_state["CSVFileTab"] = None
    if "InitCSVFileFlag" not in st.session_state:
        st.session_state["InitCSVFileFlag"] = False
    if "ResultFiles" not in st.session_state:
        st.session_state["ResultFiles"] = []

    # Step 1. Upload atp/atp.gz files
    st.subheader('Step 1. Upload atp/atp.gz files')
    file_paths = st.file_uploader("`1.1. Upload a document file`",
                                  type=["atp", "atp.gz"],
                                  accept_multiple_files=True)
    work_path = os.path.abspath('.')
    if st.button("Upload"):
        if file_paths is not None or len(file_paths) > 0:
            my_bar = st.progress(0, text="Saving file...")
            # save file
            with st.spinner('Saving file'):
                uploaded_paths = []
                for i, file_path in enumerate(file_paths):
                    uploaded_paths.append(os.path.join(work_path + "/tempDir/output", file_path.name))
                    uploaded_path = uploaded_paths[-1]
                    with open(uploaded_path, mode="wb") as f:
                        f.write(file_path.getbuffer())
                    my_bar.progress(int(100 * i / len(file_paths)), text="Saving file...")

            with st.spinner('Checking file'):
                for uploaded_path in uploaded_paths:
                    if os.path.exists(uploaded_path) == True:
                        st.session_state["FileList"].append(uploaded_path)
                        st.write(f"✅ {Path(uploaded_path).name} uploaed")
    # select the specified index base(s)
    index_file_list = get_all_files_list(work_path + "/tempDir/output", ["atp", "atp.gz"])
    options = st.multiselect('`1.2. Select files you want to process`',
                             index_file_list)
    if len(options) > 0:
        st.session_state["FileList"] = [os.path.join(work_path + "/tempDir/output", x) for x in options]

    # Step 2. Upload or create CSV config file
    st.subheader('Step 2. Upload or create CSV config file')
    ## 2.1
    st.write('`2.1. Uconfig table`')
    edited_placeholder = st.empty()
    if st.session_state["InitCSVFileFlag"] == False:
        df = pd.DataFrame(
            [
                {"Instance(Optional)": "sample", "Pattern": "sample.atp", "Status": "NotStart",
                 "Process Type": "DSSC Capture", "Pin or Method": "TDO", "Cycle": "[0-1];[3-3]",
                 "Process Type 2": "", "Pin or Method 2": "", "Cycle 2": ""},
            ]
        )
        st.session_state["CSVFileTab"] = df
        st.session_state["InitCSVFileFlag"] = True
    edited_df = edited_placeholder.data_editor(st.session_state["CSVFileTab"], num_rows="dynamic")

    ## 2.2
    file_path = st.file_uploader("`2.2. Or Upload a CSV config file`",
                                 type=["csv"])
    if st.button("Upload CSV"):
        csv_config = pd.read_csv(file_path)
        edited_df = edited_placeholder.data_editor(csv_config, num_rows="dynamic")

    st.session_state["CSVFileTab"] = edited_df

    # Step 3. Run post-process
    st.subheader('Step 3. Run post-process')
    merge_config_file = os.path.join(work_path + "/tempDir/output", "sample.csv")
    merge_config_file_content = st.session_state["CSVFileTab"].to_csv(merge_config_file, index=False)
    if st.button("Run Post-Process"):
        result_fils = main11(st.session_state["FileList"], merge_config_file, print_info)
        st.session_state["ResultFiles"] = result_fils

    if len(st.session_state["ResultFiles"]) > 0:
        st.subheader('Step 4. Download Zipped Result')
        cur_time = datetime.now()
        zip_file_name = "ZipFile_" + cur_time.strftime("%Y%m%d%H%M%S") + ".zip"
        cur_path = os.path.dirname(st.session_state["ResultFiles"][0])
        compress_file = os.path.join(cur_path, zip_file_name)
        make_zip(st.session_state["ResultFiles"], compress_file)
        with open(compress_file, "rb") as file:
            btn = st.download_button(
                label="Download Result Zip File",
                data=file,
                file_name=zip_file_name,
                mime="application/octet-stream"
            )


if __name__ == '__main__':
    main()