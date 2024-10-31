'''
Created on Dec 8, 2015

@author: zhouchao
'''
import csv, os, re, gzip, shutil, glob
import zipfile
from pathlib import Path
from typing import List


def EditPattern(textoutwin, PinName, something, CycleRange, Mode, timemode, IndexMode, UserString='', PinNameOri=""):
    result = False
    OutputPath = os.getcwd() + '/Output'
    if not os.path.exists(OutputPath):  # check the directory is existed or not
        os.mkdir(OutputPath)

    # CycleRange = ReadCSV(CSVFile)
    otherthing = os.path.join(OutputPath, os.path.basename(something))

    if Mode == 'Expand Pattern':
        RemoveRepeatFile = RemoveRepeat(something, timemode)
        # RemoveRepeatFile = os.path.realpath('new_RemoveRepeat.atp')
        copy_and_rename(RemoveRepeatFile, otherthing)
        if os.path.exists(RemoveRepeatFile):
            os.remove(RemoveRepeatFile)
        return otherthing
    if Mode == 'Compress Pattern':
        AddRepeatFile = AddReapt(something, timemode)
        copy_and_rename(AddRepeatFile, otherthing)
        if os.path.exists(AddRepeatFile):
            os.remove(AddRepeatFile)
        return otherthing

    if Mode == 'Remove Opcode':
        RemoveOpcodeFile = RemoveOpcode(something, UserString)
        copy_and_rename(RemoveOpcodeFile, otherthing)
        if os.path.exists(RemoveOpcodeFile):
            os.remove(RemoveOpcodeFile)
        return otherthing

    LineIndex = 0
    CycleNum = 0
    RepeatCnt = 0
    # remove all "repeat" opcode first
    if IndexMode == 'Cycle':
        RemoveRepeatFile = RemoveRepeat(something, timemode)
        # RemoveRepeatFile = something.replace(r'.atp', r'_RemoveRepeat.atp')  # os.path.realpath('temp_RemoveRepeat.atp')
    else:
        RemoveRepeatFile = something
    with openfile(otherthing, mode='w') as NewATPfile:
        with openfile(RemoveRepeatFile) as ATPfile:
            # with open(something) as ATPfile:
            while True:
                line = ATPfile.readline()
                LineIndex += 1
                # trim line, replace multiple-space to single space
                # line = line.replace(r" +", " ")
                # strinfo = re.compile(' +')
                # line = strinfo.sub(' ', line)

                # modify the head part of atp file
                if line.find(r">") == -1:
                    # check the timeset name
                    if line[0:12] == "import tset " or line[0:22] == 'import_all_undefineds ':
                        NewATPfile.write(line)

                        if Mode == 'DSSC Capture':
                            PinNameList = PinName.split(',')
                            NewATPfile.write("\n")
                            NewATPfile.write("instruments = {\n")
                            NewATPfile.write(
                                "({0}):DigCap {1}:auto_trig_enable;\n".format(PinNameOri, len(PinNameList)))
                            NewATPfile.write("}\n")
                        elif Mode == 'DSSC Source':
                            PinNameList = PinName.split(',')
                            NewATPfile.write("\n")
                            NewATPfile.write("instruments = {\n")
                            NewATPfile.write(
                                "({0}):DigSrc {1};\n".format(PinNameOri, len(PinNameList)))
                            NewATPfile.write("}\n")
                        elif Mode == 'CMEM/HRAM Capture':
                            # do nothing here
                            pass
                        elif Mode == 'WFLAG':
                            # do nothing here
                            pass
                        elif Mode == 'Add Opcode':
                            NewATPfile.write("\n")
                            # NewATPfile.write("import subr " + UserString + ";\n")  # import label

                            if PinName != '':  # if PinName is not empty, then add them as DCVS
                                PinNameList = PinName.split(',')
                                NewATPfile.write("instruments = {\n")
                                for pin in PinNameList:
                                    NewATPfile.write(
                                        "{0}:DCVS 1;\n".format(pin))
                                NewATPfile.write("}\n")

                    # check the index of pin in pin head
                    elif line.find("$tset") != -1:
                        Index = FindPinIndex(PinName, line, textoutwin)
                        if 0 in Index:
                            textoutwin('Error: Cannot find pinname')
                            print('Error: Cannot find pinname')
                        NewATPfile.write(line)

                    else:
                        NewATPfile.write(line)
                else:
                    # tset_index = Check_tset_line(tset_list, line)
                    RepeatCnt = GetRepeatCnt(line)
                    if CycleNum == 0:
                        # find the modify pin position
                        ModifyIndex = 0

                        pattern = re.compile(r"> *\S+")
                        StartSearchPos = re.search(pattern, line).end()

                        ModifyIndexList = []
                        for i in range(len(Index)):
                            ModifyIndex = StartSearchPos
                            CountNum = 0
                            for x in line[StartSearchPos:]:
                                a = re.findall("(?<=\s)([01HLXMVD\-\.])(?=[\s;])", line)
                                if not x.isspace():
                                    CountNum += 1
                                if Index[i] + 1 == CountNum:
                                    ModifyIndexList.append(ModifyIndex)
                                    break
                                ModifyIndex += 1

                    # add DigSrc Signaal
                    if (CycleNum == 1) and (Mode == 'DSSC Source'):
                        line = "(({0}):DigSrc = Start DSSCSrcSig)".format(
                            PinNameOri) + line

                    # add wflag setup
                    if Mode == 'WFLAG':
                        if CycleNum == 0:
                            line = 'branch_expr = (!cpuA_cond)\t' + line
                        if CycleNum == 1:
                            line = 'set_msb_infinite\t' + line
                        if CycleNum == 2:
                            line = 'set_infinite c0\t' + line
                        if CycleNum == 3:
                            line = 'push_loop c0\t' + line
                        if (CycleNum + 1 >= CycleRange[0][0]) and (
                                CycleNum + 1 <= CycleRange[-1][1]):
                            if CheckInRange(CycleNum + 1, CycleRange):
                                line = 'set_cpu_cond (cpuA_cond)\t' + line

                    if (CycleNum >= CycleRange[0][0]) and (
                            CycleNum <= CycleRange[-1][1]):
                        if Mode == 'DSSC Capture':
                            if RepeatCnt == 1:
                                if CheckInRange(CycleNum, CycleRange):
                                    # line[ModifyIndex] = "V"
                                    line_list = line.split()
                                    for k in Index:
                                        try:
                                            start_index = line_list.index(">")
                                        except Exception as e:
                                            print(e)
                                        if line_list[start_index + 1 + k + 1] == '0' or line_list[
                                            start_index + 1 + k + 1] == '1':
                                            textoutwin("Warning: Drive data found in DigCap, line " + str(
                                                LineIndex) + ", and pin data index " + str(k))
                                            print("Warning: Drive data found in DigCap, line " + str(
                                                LineIndex) + ", and pin data index " + str(k))
                                        else:
                                            line_list[start_index + 1 + k + 1] = "V"
                                    line = "(({0}):DigCap = Store)".format(PinNameOri) + " ".join(line_list) + "\n"
                                    # for ModifyIndex in ModifyIndexList:
                                    #     line = line[0:ModifyIndex] + "V" + line[ModifyIndex + 1:]
                                    #     if line[ModifyIndex] == '0' or line[ModifyIndex] == '1':
                                    #         textoutwin("Warning: Drive data found in DigCap, line " + LineIndex + ", and pin data index" + ModifyIndex)
                                    #         print("Warning: Drive data found in DigCap, line " + LineIndex + ", and pin data index" + ModifyIndex)
                                    # line = "(({0}):DigCap = Store)".format(PinName) + line
                            else:
                                CycleNumList = [CycleNum, CycleNum + RepeatCnt - 1]
                                if CheckInSameRange(CycleNumList, CycleRange):
                                    line_list = line.split()
                                    for k in Index:
                                        start_index = line_list.index(">")
                                        if line_list[start_index + 1 + k + 1] == '0' or line_list[
                                            start_index + 1 + k + 1] == '1':
                                            textoutwin("Warning: Drive data found in DigCap, line " + str(
                                                LineIndex) + ", and pin data index " + str(k))
                                            print("Warning: Drive data found in DigCap, line " + str(
                                                LineIndex) + ", and pin data index " + str(k))
                                        else:
                                            line_list[start_index + 1 + k + 1] = "V"
                                    line = "(({0}):DigCap = Store)".format(PinNameOri) + " ".join(line_list) + "\n"
                                    # for ModifyIndex in ModifyIndexList:
                                    #     line = line[0:ModifyIndex] + "V" + line[ModifyIndex + 1:]
                                    #     if line[ModifyIndex] == '0' or line[ModifyIndex] == '1':
                                    #         textoutwin("Warning: Drive data found in DigCap, line " + LineIndex + ", and pin data index" + ModifyIndex)
                                    #         print("Warning: Drive data found in DigCap, line " + LineIndex + ", and pin data index" + ModifyIndex)
                                    # line = "(({0}):DigCap = Store)".format(PinName) + " " + line

                        elif Mode == 'DSSC Source':
                            if RepeatCnt == 1:
                                if CheckInRange(CycleNum, CycleRange):
                                    # line[ModifyIndex] = "D"
                                    line_list = line.split()
                                    for k in Index:
                                        start_index = line_list.index(">")
                                        if line_list[start_index + 1 + k + 1] == 'H' or line_list[
                                            start_index + 1 + k + 1] == 'L':
                                            textoutwin("Warning: Compare data found in DigSrc, line " + str(
                                                LineIndex) + ", and pin data index " + str(k))
                                            print("Warning: Compare data found in DigSrc, line " + str(
                                                LineIndex) + ", and pin data index " + str(k))
                                        else:
                                            line_list[start_index + 1 + k + 1] = "D"
                                    line = "(({0}):DigSrc = Send)".format(PinNameOri) + " ".join(line_list) + "\n"
                                    # for ModifyIndex in ModifyIndexList:
                                    #     line = line[0:ModifyIndex] + "D" + line[ModifyIndex + 1:]
                                    #     if line[ModifyIndex] == 'H' or line[ModifyIndex] == 'L':
                                    #         textoutwin("Warning: Compare data found in DigSrc, line " + LineIndex + ", and pin data index" + ModifyIndex)
                                    #         print("Warning: Compare data found in DigSrc, line " + LineIndex + ", and pin data index" + ModifyIndex)
                                    # line = "(({0}):DigSrc = Send)".format(PinName) + line
                            else:
                                CycleNumList = [CycleNum, CycleNum + RepeatCnt - 1]
                                if CheckInSameRange(CycleNumList, CycleRange):
                                    line_list = line.split()
                                    for k in Index:
                                        start_index = line_list.index(">")
                                        if line_list[start_index + 1 + k + 1] == 'H' or line_list[
                                            start_index + 1 + k + 1] == 'L':
                                            textoutwin("Warning: Compare data found in DigSrc, line " + str(
                                                LineIndex) + ", and pin data index " + str(k))
                                            print("Warning: Compare data found in DigSrc, line " + str(
                                                LineIndex) + ", and pin data index " + str(k))
                                        else:
                                            line_list[start_index + 1 + k + 1] = "D"
                                    line = "(({0}):DigSrc = Send)".format(PinNameOri) + " ".join(line_list) + "\n"
                                    # for ModifyIndex in ModifyIndexList:
                                    #     line = line[0:ModifyIndex] + "D" + line[ModifyIndex + 1:]
                                    #     if line[ModifyIndex] == 'H' or line[ModifyIndex] == 'L':
                                    #         textoutwin("Warning: Compare data found in DigSrc, line " + LineIndex + ", and pin data index" + ModifyIndex)
                                    #         print("Warning: Compare data found in DigSrc, line " + LineIndex + ", and pin data index" + ModifyIndex)
                                    # line = "(({0}):DigSrc = Send)".format(PinName) + " " + line

                        elif Mode == 'CMEM/HRAM Capture':
                            if RepeatCnt == 1:
                                if CheckInRange(CycleNum, CycleRange):
                                    # line[ModifyIndex] = "V"
                                    line_list = line.split()
                                    for k in Index:
                                        start_index = line_list.index(">")
                                        if line_list[start_index + 1 + k + 1] == '0' or line_list[
                                            start_index + 1 + k + 1] == '1':
                                            textoutwin("Warning: Drive data found in Cap, line " + str(
                                                LineIndex) + ", and pin data index " + str(k))
                                            print("Warning: Drive data found in Cap, line " + str(
                                                LineIndex) + ", and pin data index " + str(k))
                                        else:
                                            line_list[start_index + 1 + k + 1] = "V"
                                    line = "stv\t" + " ".join(line_list) + "\n"
                                    # for ModifyIndex in ModifyIndexList:
                                    #     line = line[0:ModifyIndex] + "V" + line[ModifyIndex + 1:]
                                    #     if line[ModifyIndex] == '0' or line[ModifyIndex] == '1':
                                    #         textoutwin("Warning: Drive data found in DigCap, line " + LineIndex + ", and pin data index" + ModifyIndex)
                                    #         print("Warning: Drive data found in DigCap, line " + LineIndex + ", and pin data index" + ModifyIndex)
                                    # line = "stv\t" + line
                            else:
                                CycleNumList = [CycleNum, CycleNum + RepeatCnt - 1]
                                if CheckInSameRange(CycleNumList, CycleRange):
                                    line_list = line.split()
                                    for k in Index:
                                        start_index = line_list.index(">")
                                        if line_list[start_index + 1 + k + 1] == '0' or line_list[
                                            start_index + 1 + k + 1] == '1':
                                            textoutwin("Warning: Drive data found in Cap, line " + str(
                                                LineIndex) + ", and pin data index " + str(k))
                                            print("Warning: Drive data found in Cap, line " + str(
                                                LineIndex) + ", and pin data index " + str(k))
                                        else:
                                            line_list[start_index + 1 + k + 1] = "V"
                                    line = " ".join(line_list).replace('repeat', 'stv,repeat') + "\n"
                                    # for ModifyIndex in ModifyIndexList:
                                    #     line = line[0:ModifyIndex] + "V" + line[ModifyIndex + 1:]
                                    #     if line[ModifyIndex] == '0' or line[ModifyIndex] == '1':
                                    #         textoutwin("Warning: Drive data found in DigCap, line " + LineIndex + ", and pin data index" + ModifyIndex)
                                    #         print("Warning: Drive data found in DigCap, line " + LineIndex + ", and pin data index" + ModifyIndex)
                                    # line = line.replace('repeat', 'stv,repeat')

                        elif Mode == 'WFLAG':
                            if RepeatCnt == 1:
                                if CheckInRange(CycleNum, CycleRange):
                                    line = 'wflag\t' + line
                                else:
                                    # WFLAG does not support on repeat line
                                    pass
                        elif Mode == 'Add Opcode':
                            if RepeatCnt == 1:
                                if CheckInRange(CycleNum, CycleRange):
                                    # line = 'call ' + UserString + '\t' + line  # Add opcode name
                                    line = UserString + '\t' + line
                                else:
                                    # Add opcode does not support on repeat line
                                    pass

                    NewATPfile.write(line)

                    if IndexMode == 'Cycle':
                        CycleNum += RepeatCnt
                    else:
                        CycleNum += 1

                if len(line) == 0:
                    if CycleNum < CycleRange[-1][1]:
                        textoutwin('Error: The cycle you specified exceeds the total number of cycles in the pattern: ' + something)
                        print('Error: The cycle you specified exceeds the total number of cycles in the pattern: ' + something)
                    break
        if os.path.exists(RemoveRepeatFile):
            if IndexMode == 'Cycle':
                os.remove(RemoveRepeatFile)
        else:
            textoutwin("The file " + RemoveRepeatFile + " does not exist")
            print("The file " + RemoveRepeatFile + " does not exist")
    textoutwin("Info: Done conversion: " + something)
    print("Info: Done conversion: " + something)
    return otherthing

def copy_and_rename(src_path, dest_path):
    shutil.copy(src_path, dest_path)
    shutil.move(src_path, dest_path)

def Check_tset_line(tset_list, line):
    ii = -1
    for i, val in enumerate(tset_list):
        # last space need here to ensure the end
        val = r"> {0} ".format(val)
        if val in line:
            ii = i
            return ii
    return ii


def ReadCSV(something):
    CycleRange = {}
    # x=[]
    with openfile(something) as f:
        f_csv = csv.reader(f)
        for row in f_csv:
            if len(row) > 0:
                if len(row[0]) or len(row[1]) > 0:
                    # tmparray = row[1].replace('[', '').replace(']', '')
                    # tmparray = tmparray.split(';')
                    # tmparray = [x.split('-') for x in tmparray]
                    # tmparray = [sorted([int(y) for y in x]) for x in tmparray]
                    CycleRange[row[0]] = process_input_cycles(row[1])  # tmparray
                else:
                    break
            else:
                break
    return CycleRange

def ReadPinMap(pinmap_dir: str):
    pin_dict = {}
    line_cnt = 0
    with open(pinmap_dir, mode='r') as f:  # , encoding='UTF-8'
        f_csv = csv.reader(f, delimiter="\t")
        for row in f_csv:
            if len(row) >= 2 and line_cnt >= 3:
                if row[1] != "":
                    key = row[1]
                    if key in pin_dict.keys():
                        pin_dict[key].append(row[2])
                    else:
                        pin_dict[key] = [row[2]]
                # pin_dict[row[0]] = process_input_cycles(row[1])  # tmparray
                # if
            # else:
            #     break
            line_cnt += 1
    return pin_dict

def process_input_cycles(row: str):
    tmparray = row.replace('[', '').replace(']', '')
    if tmparray.endswith(";"):
        tmparray = tmparray[:-1]
    tmparray = tmparray.split(';')
    tmparray = [x.split('-') for x in tmparray]
    tmparray = [sorted([int(y) for y in x]) for x in tmparray]
    tmparray.sort(key=lambda x: x[0]) # sort list according to the first element of sub-list
    return tmparray


def CheckInRange(CycleNum, CycleRange):
    for x in range(len(CycleRange)):
        if CycleNum in range(CycleRange[x][0], CycleRange[x][1] + 1):
            return True
    return False


def CheckInSameRange(CycleNumList, CycleRange):
    for x in range(len(CycleRange)):
        if (CycleNumList[0] in range(CycleRange[x][0], CycleRange[x][1] + 1)) and (
                CycleNumList[1] in range(CycleRange[x][0], CycleRange[x][1] + 1)):
            return True
    return False


def FindPinIndex(PinNames, STRLine, textoutwin):
    # pattern = re.compile(r"\,\s*(.+)\)")
    # (?<=\b\,)\s*([^\,^\s]+)(?=[\,\)\s*])
    PinName = PinNames.split(",")
    STRLine = STRLine.replace(' ', '')
    pattern = re.compile(r'(?<=\,)\s*([^\,^\s]+)(?=[\,\)])')
    tmparray = re.findall(pattern, STRLine)
    Index = []  # -1
    for i in range(len(PinName)):
        for x in range(len(tmparray)):
            if tmparray[x] == PinName[i]:
                Index.append(x)
    if len(Index) != len(PinName):
        Index = []
        textoutwin("Error: Cannot find all given pins")
        print("Error: Cannot find all given pins")
    return Index


def RemoveOpcode(something, UserString):
    otherthing = something.replace(r'.atp', r'_RemoveOpcode.atp')
    with openfile(otherthing, mode='w') as NewATPfile:
        with openfile(something) as ATPfile:
            while True:
                tmpLine = ATPfile.readline()
                if len(tmpLine) == 0:
                    break
                if tmpLine.strip().startswith(UserString):
                    tmpLine = tmpLine.replace(UserString, '')
                NewATPfile.write(tmpLine)
    return otherthing


def openfile(filename, mode='r'):
    if filename.endswith('.gz'):
        return gzip.open(filename, mode + 't')  # "t" means open gz as string
    else:
        return open(filename, mode)


def RemoveRepeat(something, timemode):
    otherthing = something.replace(r'.atp', r'_RemoveRepeat.atp')  # os.path.realpath('new_RemoveRepeat.atp')

    LineIndex = 0
    RepeatCnt = 1
    # PrevLine = []  # ""
    # line = []
    linenum = 0
    Boby_Flag = False

    if timemode == '1':
        linenum = 1
    elif timemode == '2':
        linenum = 2

    # /Users/Jerry/OneDrive/Python/EditRepeatTool/test1.txt
    with openfile(otherthing, mode='w') as NewATPfile:
        with openfile(something) as ATPfile:
            while True:
                line = []  # initial line for dual mode
                if not Boby_Flag:
                    headerline = ATPfile.readline()
                    if headerline.strip().startswith(r"{"):  # (r"start_label"):  # check the header part
                        Boby_Flag = True

                    if len(headerline) == 0:
                        break

                    NewATPfile.write(headerline)
                else:
                    for i in range(linenum):

                        while True:
                            tmpLine = ATPfile.readline()
                            LineIndex += 1
                            if tmpLine.strip().startswith(r'//'):
                                continue
                            else:
                                break
                        line.append(tmpLine)
                    RepeatCnt = 1
                    p = re.compile(r'(?<=repeat)\s+\d+')
                    m = re.search(p, line[-1])

                    if m:
                        RepeatCnt = int(m.group())

                    if RepeatCnt > 1:
                        # i = 0
                        # j = len('repeat ' + str(RepeatCnt))
                        # line = line.replace('repeat ' + str(RepeatCnt), ' ' * j)
                        line[-1] = line[-1].replace('repeat', ' ' * len('repeat'), 1)
                        line[-1] = line[-1].replace(str(RepeatCnt), ' ' * len(str(RepeatCnt)), 1)
                        for j in range(RepeatCnt):
                            for i in range(len(line)):
                                NewATPfile.write(line[i])
                    else:
                        for i in range(len(line)):
                            NewATPfile.write(line[i])

                        if (line[-1].find(r'}') != -1) or line[-1] == '':
                            Boby_Flag = False
    return otherthing


def AddReapt(something, timemode):
    '''tmpstr = open('','r')'''
    # print(os.getcwd())
    # print(something)

    otherthing = something.replace(r'.atp', r'_AddRepeat.atp')

    LineIndex = 0
    RepeatCnt = 1
    PrevLine = []  # ""
    # line = []
    linenum = 0
    Boby_Flag = False

    if timemode == '1':
        linenum = 1
    elif timemode == '2':
        linenum = 2

    with openfile(otherthing, mode='w') as NewATPfile:
        with openfile(something) as ATPfile:
            while True:
                line = []  # initial line for dual mode
                if not Boby_Flag:
                    headerline = ATPfile.readline()
                    if headerline.strip().startswith(
                            r"{"):  # headerline.find(r"start_label") != -1:  # check the header part
                        Boby_Flag = True

                    if len(headerline) == 0:
                        break

                    NewATPfile.write(headerline)
                else:
                    for i in range(linenum):

                        while True:
                            tmpLine = ATPfile.readline()
                            # LineIndex += 1
                            if tmpLine.strip().startswith(r'//'):
                                continue
                            else:
                                LineIndex += 1
                                break
                        line.append(tmpLine)
                        # LineIndex += 1
                    # print(line)
                    # pass

                    if cmp(line, PrevLine) == 0 and RepeatCnt < 65535:
                        RepeatCnt += 1
                    elif LineIndex != linenum:
                        # if cmp(line, PrevLine) != 0 and LineIndex != linenum:

                        for i in range(len(PrevLine) - 1):
                            NewATPfile.write('{0}'.format(PrevLine[i]))  # write lines but last line in block

                        if RepeatCnt != 1:  # write last line
                            NewATPfile.write('repeat {0}    {1}'.format(RepeatCnt, PrevLine[-1]))
                        else:
                            NewATPfile.write('{0}'.format(PrevLine[-1]))
                        RepeatCnt = 1

                    # if len(line[-1]) == 0:
                    #     break
                    if (line[-1].find(r'}') != -1) or line[-1] == '':
                        Boby_Flag = False
                        for i in range(len(line)):
                            NewATPfile.write('{0}'.format(line[i]))

                    PrevLine = line
    return otherthing

def GetRepeatCnt(line):
    RepeatCnt = 0
    p = re.compile(r'(?<=repeat)\s+\d+')
    m = re.search(p, line)
    if m:
        RepeatCnt = int(m.group())

    if RepeatCnt > 1:
        return RepeatCnt
    else:
        return 1


def cmp(a, b):  # compare two lists
    listlena = len(a)
    listlenb = len(b)
    result = -1
    if listlena == listlenb:
        # tempa = ''
        for i in range(listlena):
            tempa = str(a[i])
            commtindexa = tempa.find('//')
            tempb = str(b[i])
            commtindexb = tempa.find('//')
            if commtindexa > 0:
                tempa = tempa[:commtindexa].strip()
            if commtindexb > 0:
                tempb = tempb[:commtindexb].strip()
            result = (tempa > tempb) - (tempa < tempb)
            if result != 0:
                break
    return result


def GetFiles(files_array, dirname, extname):
    for path in os.listdir(dirname):
        absolutely_path = os.path.join(dirname, path)
        if os.path.isdir(absolutely_path):
            GetFiles(files_array, absolutely_path, extname)
        elif os.path.splitext(absolutely_path)[1] == extname:
            files_array.append(absolutely_path)
        else:
            pass
            # print(path)
            # print("OK")


def InList(str, tmplist):
    for i in range(len(tmplist)):
        if tmplist[i].find(str) > -1:
            return i
    return -1


def get_all_files_list(source_dir, exts):
    all_files = []
    result = []
    for ext in exts:
        all_files.extend(
            glob.glob(os.path.join(source_dir, f"*.{ext}"), recursive=False)
        )
    for filepath in all_files:
        file_name = Path(filepath).name
        result.append(file_name)
    return result


def make_zip(filenames: List, output_filename):
    with zipfile.ZipFile(output_filename, 'w') as zipf:
        for filename in filenames:
            print(filename)
            zipf.write(filename)
        print()

def analyse_merge_config(merge_config_file:str, textoutwin):
    config_list = []
    with openfile(merge_config_file) as f:
        f_csv = csv.reader(f)
        for index, row in enumerate(f_csv):
            if index == 0:
                head_list = row
            elif len(row) > 0:
                cur_config_dict = {"ATPFile": "", "CycleRange": None, "Mode": "", "PinName": "", "TimeMode": "Single",
                                   "IndexMode": "Cycle"}
                for i, item in enumerate(row):
                    item = item.strip()
                    if item != "" and item is not None:
                        if i == 1 and item.lower().endswith(".atp"):
                            cur_config_dict["ATPFile"] = item
                        elif i == 3 or i == 6:
                            cur_config_dict["Mode"] = item
                            if "Pattern" in item: #'Expand Pattern'  'Compress Pattern':
                                tmp_dict = cur_config_dict.copy()
                                config_list.append(tmp_dict)
                                # reset possible conflict info
                                cur_config_dict["CycleRange"] = None
                                cur_config_dict["Mode"] = ""
                                cur_config_dict["PinName"] = ""
                        elif i == 4 or i == 7:
                            cur_config_dict["PinName"] = item
                        elif i == 5 or i == 8:
                            cur_config_dict["CycleRange"] = process_input_cycles(item)
                            if "Pattern" not in item: #'Expand Pattern'  'Compress Pattern':
                                tmp_dict = cur_config_dict.copy()
                                config_list.append(tmp_dict)
                                # reset possible conflict info
                                cur_config_dict["CycleRange"] = None
                                cur_config_dict["Mode"] = ""
                                cur_config_dict["PinName"] = ""

            else:
                textoutwin("Warning: NO CONFIG FOUND!!!")
                break
    return config_list

def main11(ATPFiles, merge_config_file, textoutwin, PinMap):
    # check pin group
    if PinMap != "":
        pinrounp_dict = ReadPinMap(PinMap[0])

    # use to process merge-setup format input
    config_list = analyse_merge_config(merge_config_file, textoutwin)

    # process atp files
    CmbList = ['DSSC Capture', 'DSSC Source', 'CMEM/HRAM Capture', 'Expand Pattern', 'Compress Pattern', 'WFLAG',
               'Add Opcode', 'Remove Opcode']

    preFileName = ""
    result = []
    for config_item in config_list:
        # initial parameters
        tmpFileName = config_item["ATPFile"]
        Mode = config_item["Mode"]
        PinName = config_item["PinName"]
        CycleRange = config_item["CycleRange"]
        TimeMode = config_item["TimeMode"]

        # check pin group
        PinNameOri = PinName
        if PinMap != "":
            if ("," not in PinName) and (PinName in pinrounp_dict.keys()):
                PinName = ",".join(pinrounp_dict[PinName])

        if TimeMode == 'Single':
            time_mode = '1'
        elif TimeMode == 'Dual':
            time_mode = '2'
        IndexMode = config_item["IndexMode"]
        UserString = ""
        j = InList(tmpFileName, ATPFiles)

        PrcsFileName = ATPFiles[j]
        # if some  name as previous, then copy output of previous to src path
        if preFileName == tmpFileName:
            OutputPath = os.path.join(os.getcwd(), 'Output')
            otherthing = os.path.join(OutputPath, os.path.basename(ATPFiles[j]))
            # shutil.copy(otherthing, ATPFiles[j])
            PrcsFileName = ATPFiles[j].replace(r'.atp', r'_1stpostprcs.atp')
            copy_and_rename(otherthing, PrcsFileName)

        # go~ and run process function
        if j >= 0:
            textoutwin("Info: Start convert file: " + PrcsFileName)
            print("Info: start convert file: +" + PrcsFileName)
            if Mode in CmbList:
                result_file = EditPattern(textoutwin, PinName, PrcsFileName, CycleRange, Mode, time_mode, IndexMode,
                                          UserString, PinNameOri)
                # Check is it the temp file from dual post process
                if result_file.endswith(r"_1stpostprcs.atp"):
                    if os.path.exists(PrcsFileName):
                        os.remove(PrcsFileName)
                    DualPostPrcsFile = result_file.replace(r'_1stpostprcs.atp',r'.atp')
                    copy_and_rename(result_file, DualPostPrcsFile)
                    result_file = DualPostPrcsFile

                preFileName = tmpFileName
                if result_file not in result:
                    result.append(result_file)
            else:
                textoutwin("Error: Wrong Choice !!!")
                print("Error: Wrong Choice !!!")
            textoutwin("Info: Done conversion")
            print("Info: Done conversion")
        else:
            textoutwin("Warning: Cannot find atp file: " + tmpFileName)
            print("Warning: Cannot find atp file: " + tmpFileName)
    return result


def main4(ATPFiles, CSVFiles, PinName:str, Mode, TimeMode, UserString, IndexMode, textoutwin, PinMap):
    # ATPFiles = []
    # CSVFiles = []
    # GetFiles(ATPFiles, Dir, ".atp")
    # GetFiles(CSVFiles, Dir, ".csv")
    PinNameOri = PinName # pin group name possible
    if PinMap != "":
        pinrounp_dict = ReadPinMap(PinMap[0])
        if ("," not in PinName) and (PinName in pinrounp_dict.keys()):
            PinName = ",".join(pinrounp_dict[PinName])
    CmbList = ['DSSC Capture', 'DSSC Source', 'CMEM/HRAM Capture', 'Expand Pattern', 'Compress Pattern', 'WFLAG',
               'Add Opcode', 'Remove Opcode']
    if TimeMode == 'Single':
        time_mode = '1'
    elif TimeMode == 'Dual':
        time_mode = '2'
    CycleRanges = []
    if len(CSVFiles) > 1:
        textoutwin("Error: Only ONE CSV file supported !!!")
        print("Error: Only ONE CSV file supported !!!")
        return
    CycleRanges = ReadCSV(CSVFiles[0])

    for key in CycleRanges.keys():
        tmpFileName = key  # CycleRanges[i]#CSVFiles[i].replace('.csv', '.atp')
        j = InList(tmpFileName, ATPFiles)
        if j >= 0:
            textoutwin("Info: Start convert file: " + ATPFiles[j])
            print("Info: start convert file: +" + ATPFiles[j])
            if Mode in CmbList:
                EditPattern(textoutwin, PinName, ATPFiles[j], CycleRanges[key], Mode, time_mode, IndexMode, UserString, PinNameOri)
            else:
                textoutwin("Error: Wrong Choice !!!")
                print("Error: Wrong Choice !!!")
            textoutwin("Info: Done conversion")
            print("Info: Done conversion")
        else:
            textoutwin("Warning: Cannot find atp file: " + tmpFileName)
            print("Warning: Cannot find atp file: " + tmpFileName)


if __name__ == '__main__':
    main11(r"C:\Users\zhouchao\PycharmProjects\EditPat\S5\Post_process_pattern_list_S5.csv")
    '''
    csv_array = []
    GetFiles(csv_array, r"/Users/Jerry/OneDrive/Python/EditPat", ".csv")  # main2()
    print("Hello World")

    '''
