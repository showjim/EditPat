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
    if "ZipFilesFlag" not in st.session_state:
        st.session_state["ZipFilesFlag"] = True
    if "ZipFilesName" not in st.session_state:
        st.session_state["ZipFilesName"] = ""
    if "PAE_logprint" not in st.session_state:
        st.session_state["PAE_logprint"] = ""
    if "PinmapFile" not in st.session_state:
        st.session_state["PinmapFile"] = ""

    # Sidebar for menu options
    with st.sidebar:
        st.header("Other Tools")
        st.page_link("http://taishanstone:8501", label="Check INFO Tool", icon="1️⃣")
        st.page_link("http://taishanstone:8503", label="Shmoo Detect Tool", icon="2️⃣")
        st.header("Help")
        if st.button("About"):
            st.info(
                "Thank you for using!\nCreated by Chao Zhou.\nAny suggestions please mail zhouchao486@gmail.com]")

    work_path = os.path.abspath('.')
    OutputPath = os.path.join(work_path, "workDir")
    if not os.path.exists(OutputPath):  # check the directory is existed or not
        os.mkdir(OutputPath)

    with st.expander("Run Logs"):
        log_text_area = st.empty()  # text_area("", key="logs", height=300)

    def send_log(data_log):
        st.session_state["PAE_logprint"] += f'{datetime.now()} - {data_log}\n'
        log_text_area.code(st.session_state["PAE_logprint"])


    # Step 1. Upload atp/atp.gz files
    st.subheader('Step 1. Upload atp/atp.gz files')
    file_paths = st.file_uploader("`1.1. Upload a document file`",
                                  type=["atp", "atp.gz"],
                                  accept_multiple_files=True)

    if st.button("Upload"):
        if file_paths is not None or len(file_paths) > 0:
            my_bar = st.progress(0, text="Saving file...")
            # save file
            with st.spinner('Saving file'):
                uploaded_paths = []
                for i, file_path in enumerate(file_paths):
                    uploaded_paths.append(os.path.join(OutputPath, file_path.name))
                    uploaded_path = uploaded_paths[-1]
                    with open(uploaded_path, mode="wb") as f:
                        f.write(file_path.getbuffer())
                    my_bar.progress(int(100 * (i + 1) / len(file_paths)), text="Saving file...")

            with st.spinner('Checking file'):
                for uploaded_path in uploaded_paths:
                    if os.path.exists(uploaded_path) == True:
                        st.session_state["FileList"].append(uploaded_path)
                        st.write(f"✅ {Path(uploaded_path).name} uploaed")
    # select the specified index base(s)
    index_file_list = get_all_files_list(OutputPath, ["atp", "atp.gz"])
    options = st.multiselect('`1.2. Select files you want to process`',
                             index_file_list)
    if len(options) > 0:
        st.session_state["FileList"] = [os.path.join(OutputPath, x) for x in options]

    # Step 2. Upload or create CSV config file
    st.subheader('Step 2. Upload or create CSV config file')
    ## 2.1
    st.write('`2.1. Config table`')
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

    # def df_on_change(df):
    #     state = st.session_state["df_editor"]
    #     for index, updates in state["edited_rows"].items():
    #         # st.session_state["CSVFileTab"].loc[st.session_state["CSVFileTab"].index == index, "edited"] = True
    #         for key, value in updates.items():
    #             st.session_state["CSVFileTab"].loc[st.session_state["CSVFileTab"].index == index, key] = value
    #
    # CmbList = ['DSSC Capture', 'DSSC Source', 'CMEM/HRAM Capture', 'Expand Pattern', 'Compress Pattern', 'WFLAG']
    # df = st.session_state["CSVFileTab"]
    # edited_df = edited_placeholder.data_editor(
    #     st.session_state["CSVFileTab"],
    #     key = "df_editor",
    #     num_rows="dynamic",
    #     column_config={
    #         "Process Type": st.column_config.SelectboxColumn(
    #             "Process Type",
    #             help="How would you like to process ATP file",
    #             width="medium",
    #             options=CmbList,
    #             required=True,
    #         ),
    #         "Process Type 2": st.column_config.SelectboxColumn(
    #             "Process Type 2",
    #             help="How would you like to process ATP file",
    #             width="medium",
    #             options=CmbList,
    #             required=False,
    #         ),
    #     },
    #     on_change = df_on_change, args = [df]
    # )
    # st.session_state["CSVFileTab"] = edited_df

    ## 2.2 CSV config
    file_path = st.file_uploader("`2.2. Or Upload a CSV config file`",
                                 type=["csv"])
    if st.button("Upload CSV"):
        csv_config = pd.read_csv(file_path)
        csv_config.fillna("",inplace=True)
        st.session_state["CSVFileTab"] = csv_config
        # edited_df = edited_placeholder.data_editor(csv_config, num_rows="dynamic")

    def df_on_change(df):
        state = st.session_state["df_editor"]
        for index, updates in state["edited_rows"].items():
            # st.session_state["CSVFileTab"].loc[st.session_state["CSVFileTab"].index == index, "edited"] = True
            for key, value in updates.items():
                st.session_state["CSVFileTab"].loc[st.session_state["CSVFileTab"].index == index, key] = value

    CmbList = ['DSSC Capture', 'DSSC Source', 'CMEM/HRAM Capture', 'Expand Pattern', 'Compress Pattern', 'WFLAG']
    df = st.session_state["CSVFileTab"]
    edited_df = edited_placeholder.data_editor(
        st.session_state["CSVFileTab"],
        key = "df_editor",
        num_rows="dynamic",
        column_config={
            "Process Type": st.column_config.SelectboxColumn(
                "Process Type",
                help="How would you like to process ATP file",
                width="medium",
                options=CmbList,
                required=True,
            ),
            "Process Type 2": st.column_config.SelectboxColumn(
                "Process Type 2",
                help="How would you like to process ATP file",
                width="medium",
                options=CmbList,
                required=False,
            ),
        },
        on_change = df_on_change, args = [df],
        use_container_width=True,
        height=200,
    )
    # st.session_state["CSVFileTab"] = edited_df

    ##2.3 (optional) select pinmap
    pinmap_path = st.file_uploader("`2.3. (Optional) Upload a pin map file`",
                                 type=["txt"])
    if st.button("(Optional) Upload Pinmap"):
        if pinmap_path is not None:
            # save file
            with st.spinner('Saving file'):
                uploaded_path = os.path.join(OutputPath, pinmap_path.name)
                with open(uploaded_path, mode="wb") as f:
                    f.write(pinmap_path.getbuffer())

                st.session_state["PinmapFile"] = uploaded_path
                st.write(f"✅ {Path(uploaded_path).name} uploaed")


    # Step 3. Run post-process
    st.subheader('Step 3. Run post-process')
    if st.button("Run Post-Process"):
        merge_config_file = os.path.join(OutputPath, "sample.csv")
        merge_config_file_content = st.session_state["CSVFileTab"].to_csv(merge_config_file, index=False)
        result_fils = main11(st.session_state["FileList"], merge_config_file, send_log, st.session_state["PinmapFile"]) #print_info)
        st.session_state["ResultFiles"] = result_fils
        st.session_state["ZipFilesFlag"] = True

    if len(st.session_state["ResultFiles"]) > 0:
        st.subheader('Step 4. Download Zipped Result')
        if st.session_state["ZipFilesFlag"] == True:
            st.session_state["ZipFilesFlag"] = False
            cur_time = datetime.now()
            zip_file_name = "ZipFile_" + cur_time.strftime("%Y%m%d%H%M%S") + ".zip"
            cur_path = os.path.dirname(st.session_state["ResultFiles"][0])
            compress_file = os.path.join(cur_path, zip_file_name)
            make_zip(st.session_state["ResultFiles"], compress_file)
            st.session_state["ZipFilesName"] = compress_file

        compress_file = st.session_state["ZipFilesName"]
        zip_file_name = os.path.basename(compress_file)
        with open(compress_file, "rb") as file:
            btn = st.download_button(
                label="Download Result Zip File",
                data=file,
                file_name=zip_file_name,
                mime="application/octet-stream"
            )


if __name__ == '__main__':
    main()
