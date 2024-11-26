'''
Main module for ATP file processing
Created on Dec 8, 2015
@author: zhouchao
'''
import os
from typing import List, Any
from src.utils import in_list
from src.atp_handler import read_csv, read_pinmap, analyse_merge_config
from src.pattern_processor import edit_pattern
from src.file_ops import copy_and_rename

def main4(atp_files: List[str], csv_files: List[str], pin_name: str, mode: str, 
          time_mode: str, user_string: str, index_mode: str, textoutwin: Any, pin_map: str) -> None:
    """Process ATP files according to CSV configuration"""
    pin_name_ori = pin_name
    if pin_map != "":
        pinrounp_dict = read_pinmap(pin_map[0])
        if ("," not in pin_name) and (pin_name in pinrounp_dict.keys()):
            pin_name = ",".join(pinrounp_dict[pin_name])

    cmb_list = ['DSSC Capture', 'DSSC Source', 'CMEM/HRAM Capture', 'Expand Pattern', 
                'Compress Pattern', 'WFLAG', 'Add Opcode', 'Remove Opcode']

    if time_mode == 'Single':
        timemode = '1'
    elif time_mode == 'Dual':
        timemode = '2'

    if len(csv_files) > 1:
        textoutwin("Error: Only ONE CSV file supported !!!")
        print("Error: Only ONE CSV file supported !!!")
        return

    cycle_ranges = read_csv(csv_files[0])

    for key in cycle_ranges.keys():
        tmp_file_name = key
        j = in_list(tmp_file_name, atp_files)
        if j >= 0:
            textoutwin("Info: Start convert file: " + atp_files[j])
            print("Info: start convert file: +" + atp_files[j])
            if mode in cmb_list:
                edit_pattern(textoutwin, pin_name, atp_files[j], cycle_ranges[key], 
                           mode, timemode, index_mode, user_string, pin_name_ori)
            else:
                textoutwin("Error: Wrong Choice !!!")
                print("Error: Wrong Choice !!!")
            textoutwin("Info: Done conversion")
            print("Info: Done conversion")
        else:
            textoutwin("Warning: Cannot find atp file: " + tmp_file_name)
            print("Warning: Cannot find atp file: " + tmp_file_name)

def main11(atp_files: List[str], merge_config_file: str, textoutwin: Any, pin_map: str) -> List[str]:
    """Process ATP files according to merge configuration file"""
    # check pin group
    if pin_map != "":
        pinrounp_dict = read_pinmap(pin_map)

    # use to process merge-setup format input
    config_list = analyse_merge_config(merge_config_file, textoutwin)

    cmb_list = ['DSSC Capture', 'DSSC Source', 'CMEM/HRAM Capture', 'Expand Pattern', 
                'Compress Pattern', 'WFLAG', 'Add Opcode', 'Remove Opcode']

    pre_file_name = ""
    result = []
    for config_item in config_list:
        # initial parameters
        tmp_file_name = config_item["ATPFile"]
        mode = config_item["Mode"]
        pin_name = config_item["PinName"]
        cycle_range = config_item["CycleRange"]
        time_mode = config_item["TimeMode"]

        # check pin group
        pin_name_ori = pin_name
        if pin_map != "":
            if ("," not in pin_name) and (pin_name in pinrounp_dict.keys()):
                pin_name = ",".join(pinrounp_dict[pin_name])

        if time_mode == 'Single':
            time_mode = '1'
        elif time_mode == 'Dual':
            time_mode = '2'
        index_mode = config_item["IndexMode"]
        user_string = ""
        j = in_list(tmp_file_name, atp_files)

        prcs_file_name = atp_files[j]
        # if some  name as previous, then copy output of previous to src path
        if pre_file_name == tmp_file_name:
            OutputPath = os.path.join(os.getcwd(), 'Output')
            otherthing = os.path.join(OutputPath, os.path.basename(atp_files[j]))
            # shutil.copy(otherthing, ATPFiles[j])
            prcs_file_name = atp_files[j].replace(r'.atp', r'_1stpostprcs.atp')
            copy_and_rename(otherthing, prcs_file_name)

        # go~ and run process function
        if j >= 0:
            textoutwin("Info: Start convert file: " + prcs_file_name)
            print("Info: start convert file: +" + prcs_file_name)
            if mode in cmb_list:
                result_file = edit_pattern(textoutwin, pin_name, prcs_file_name, cycle_range,
                                        mode, time_mode, index_mode, user_string, pin_name_ori)

                # Check is it the temp file from dual post process
                if result_file.endswith(r"_1stpostprcs.atp"):
                    if os.path.exists(prcs_file_name):
                        os.remove(prcs_file_name)
                    dual_post_prcs_file = result_file.replace(r'_1stpostprcs.atp', r'.atp')
                    copy_and_rename(result_file, dual_post_prcs_file)
                    result_file = dual_post_prcs_file

                pre_file_name = tmp_file_name
                if result_file not in result:
                    result.append(result_file)
            else:
                textoutwin("Error: Wrong Choice !!!")
                print("Error: Wrong Choice !!!")
            textoutwin("Info: Done conversion")
            print("Info: Done conversion")
        else:
            textoutwin("Warning: Cannot find atp file: " + tmp_file_name)
            print("Warning: Cannot find atp file: " + tmp_file_name)
    return result

if __name__ == '__main__':
    main11(r"C:\Users\zhouchao\PycharmProjects\EditPat\S5\Post_process_pattern_list_S5.csv")
