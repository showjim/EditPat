'''
Created on Dec 8, 2015

@author: zhouchao
'''
import csv
import os
import re


def EditPattern(PinName, something, CycleRange, Mode, timemode, IndexMode, UserString = ''):
    OutputPath = os.getcwd() + '/Output'
    if not os.path.exists(OutputPath):  # check the directory is existed or not
        os.mkdir(OutputPath)
    if Mode == 'Expand Pattern':
        RemoveRepeat(something, timemode)
        RemoveRepeatFile = os.path.realpath('new_RemoveRepeat.atp')
        return
    if Mode == 'Compress Pattern':
        AddReapt(something, timemode)
        return

    # CycleRange = ReadCSV(CSVFile)
    otherthing = os.path.join(OutputPath, os.path.basename(something))

    LineIndex = 0
    CycleNum = 0
    RepeatCnt = 0
    # remove all "repeat" opcode first
    if IndexMode == 'Cycle':
        RemoveRepeat(something, timemode)
        RemoveRepeatFile = something.replace(r'.atp', r'_RemoveRepeat.atp') # os.path.realpath('temp_RemoveRepeat.atp')
    else:
        RemoveRepeatFile = something
    with open(otherthing, mode='w') as NewATPfile:
        with open(RemoveRepeatFile) as ATPfile:
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
                            NewATPfile.write("\n")
                            NewATPfile.write("instruments = {\n")
                            NewATPfile.write(
                                "({0}):DigCap 1:auto_trig_enable;\n".format(PinName))
                            NewATPfile.write("}\n")
                        elif Mode == 'DSSC Source':
                            NewATPfile.write("\n")
                            NewATPfile.write("instruments = {\n")
                            NewATPfile.write(
                                "({0}):DigSrc 1;\n".format(PinName))
                            NewATPfile.write("}\n")
                        elif Mode == 'CMEM/HRAM Capture':
                            # do nothing here
                            pass
                        elif Mode == 'WFLAG':
                            # do nothing here
                            pass
                        elif Mode == 'Call Label':
                            NewATPfile.write("\n")
                            NewATPfile.write("import subr " + UserString + ";\n") #import label

                            if PinName != '': # if PinName is not empty, then add them as DCVS
                                PinNameList = PinName.split(',')
                                NewATPfile.write("instruments = {\n")
                                for pin in PinNameList:
                                    NewATPfile.write(
                                        "{0}:DCVS 1:;\n".format(pin))
                                NewATPfile.write("}\n")

                    # check the index of pin in pin head
                    elif line.find("$tset") != -1:
                        Index = FindPinIndex(PinName, line)
                        if Index == 0 or Index == -1:
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
                        CountNum = 0

                        pattern = re.compile(r"> *\S+")
                        StartSearchPos = re.search(pattern, line).end()

                        ModifyIndex = StartSearchPos
                        for x in line[StartSearchPos:]:

                            if not x.isspace():
                                CountNum += 1
                            if Index + 1 == CountNum:
                                break
                            ModifyIndex += 1

                    # add DigSrc Signaal
                    if (CycleNum == 1) and (Mode == 'DSSC Source'):
                        line = "(({0}):DigSrc = Start DSSCSrcSig)".format(
                            PinName) + line

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
                                    line = line[0:ModifyIndex] + \
                                           "V" + line[ModifyIndex + 1:]
                                    line = "(({0}):DigCap = Store)".format(
                                        PinName) + line
                            else:
                                CycleNumList = [CycleNum, CycleNum + RepeatCnt - 1]
                                if CheckInSameRange(CycleNumList, CycleRange):
                                    line = line[0:ModifyIndex] + \
                                           "V" + line[ModifyIndex + 1:]
                                    line = "(({0}):DigCap = Store)".format(
                                        PinName) + " " + line

                        elif Mode == 'DSSC Source':
                            if RepeatCnt == 1:
                                if CheckInRange(CycleNum, CycleRange):
                                    # line[ModifyIndex] = "V"
                                    line = line[0:ModifyIndex] + \
                                           "D" + line[ModifyIndex + 1:]
                                    line = "(({0}):DigSrc = Send)".format(
                                        PinName) + line
                            else:
                                CycleNumList = [CycleNum, CycleNum + RepeatCnt - 1]
                                if CheckInSameRange(CycleNumList, CycleRange):
                                    line = line[0:ModifyIndex] + \
                                           "D" + line[ModifyIndex + 1:]
                                    line = "(({0}):DigSrc = Send)".format(
                                        PinName) + " " + line

                        elif Mode == 'CMEM/HRAM Capture':
                            if RepeatCnt == 1:
                                if CheckInRange(CycleNum, CycleRange):
                                    # line[ModifyIndex] = "V"
                                    line = line[0:ModifyIndex] + \
                                        "V" + line[ModifyIndex + 1:]
                                    line = "stv\t" + line
                            else:
                                CycleNumList = [CycleNum, CycleNum + RepeatCnt - 1]
                                if CheckInSameRange(CycleNumList, CycleRange):
                                    line = line[0:ModifyIndex] + \
                                           "V" + line[ModifyIndex + 1:]
                                    line = line.replace('repeat', 'stv,repeat')

                        elif Mode == 'WFLAG':
                            if RepeatCnt == 1:
                                if CheckInRange(CycleNum, CycleRange):
                                    line = 'wflag\t' + line
                                else:
                                    # WFLAG does not support on repeat line
                                    pass
                        elif Mode == 'Call Label':
                            if RepeatCnt == 1:
                                if CheckInRange(CycleNum, CycleRange):
                                    line = 'call ' + UserString + '\t' + line # Call Label name
                                else:
                                    # Call Label does not support on repeat line
                                    pass

                    NewATPfile.write(line)

                    if IndexMode == 'Cycle':
                        CycleNum += RepeatCnt
                    else:
                        CycleNum += 1

                if len(line) == 0:
                    break
        if os.path.exists(RemoveRepeatFile):
            if IndexMode == 'Cycle':
                os.remove(RemoveRepeatFile)
        else:
            print("The file " + RemoveRepeatFile + " does not exist")


def Check_tset_line(tset_list, line):
    ii = -1
    for i,val in enumerate(tset_list):
        # last space need here to ensure the end
        val = r"> {0} ".format(val)
        if val in line:
            ii = i
            return ii
    return ii

def ReadCSV(something):
    CycleRange = {}
    # x=[]
    with open(something) as f:
        f_csv = csv.reader(f)
        for row in f_csv:
            if len(row) > 0:
                tmparray = row[1].replace('[', '').replace(']', '')
                tmparray = tmparray.split(';')
                tmparray = [x.split('-') for x in tmparray]
                tmparray = [sorted([int(y) for y in x]) for x in tmparray]
                CycleRange[row[0]] = tmparray
            else:
                break
    return CycleRange


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


def FindPinIndex(PinName, STRLine):
    # pattern = re.compile(r"\,\s*(.+)\)")
    # (?<=\b\,)\s*([^\,^\s]+)(?=[\,\)\s*])
    pattern = re.compile(r'(?<=\,)\s*([^\,^\s]+)(?=[\,\)])')
    tmparray = re.findall(pattern, STRLine)
    Index = -1
    for x in range(len(tmparray)):
        if tmparray[x] == PinName:
            Index = x
    return Index


# def RemoveRepeat(something):
#     otherthing = os.path.realpath('new_RemoveRepeat.atp')
#
#     with open(otherthing, mode='w') as NewATPfile:
#         with open(something) as ATPfile:
#
#             for line in ATPfile:
#                 RepeatCnt = 1
#                 p = re.compile(r'(?<=repeat)\s+\d+')
#                 m = re.search(p, line)
#
#                 if m:
#                     RepeatCnt = int(m.group())
#
#                 if RepeatCnt > 1:
#                     # j = line.find('>')
#                     # j = len('repeat ' + str(RepeatCnt))
#                     line = line.replace('repeat', ' ' * len('repeat'))
#                     line = line.replace(str(RepeatCnt), ' ' * len(str(RepeatCnt)))
#                     for i in range(0, RepeatCnt):
#                         NewATPfile.write(line)
#                 else:
#                     NewATPfile.write(line)
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
    with open(otherthing, mode='w') as NewATPfile:
        with open(something) as ATPfile:

            while True:
                line = []  # initial line for dual mode
                if not Boby_Flag:
                    headerline = ATPfile.readline()
                    if headerline.strip().startswith(r"{"): #(r"start_label"):  # check the header part
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
                        line[-1] = line[-1].replace('repeat',
                                                    ' ' * len('repeat'))
                        line[-1] = line[-1].replace(str(RepeatCnt),
                                                    ' ' * len(str(RepeatCnt)))
                        for j in range(RepeatCnt):
                            for i in range(len(line)):
                                NewATPfile.write(line[i])
                    else:
                        for i in range(len(line)):
                            NewATPfile.write(line[i])

                        if (line[-1].find(r'}') != -1) or line[-1] == '':
                            Boby_Flag = False


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

    with open(otherthing, mode='w') as NewATPfile:
        with open(something) as ATPfile:
            while True:
                line = []  # initial line for dual mode
                if not Boby_Flag:
                    headerline = ATPfile.readline()
                    if headerline.find(r"start_label") != -1:  # check the header part
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


def Trim(mystr):
    x = ""
    for tmpstr in mystr:
        if tmpstr == "":
            continue
        else:
            x = x + tmpstr
    return x


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
                tempa = tempa[:commtindexa].strip( )
            if commtindexb > 0:
                tempb = tempb[:commtindexb].strip( )
            result = (tempa > tempb) - (tempa < tempb)
            if result != 0:
                break
    return result


def main11():
    something = input('Step 1. Please enter ATP file path and name:\n')
    CSVFile = input("Step 2. Please enter CSV file path and name:\n")
    PinName = input('Step 3. Please enter the name of the pin need to edit:\n')
    print('Step 4. Please choose function, input the NO.')
    choosefunction = input(
        '1.DSSC Capture;\n2.DSSC Source;\n3.CMEM/HRAM Capture.\n')
    timemode = input('1. Single\n2. Dual')

    input('Press Enter key to exit!')


def main4(ATPFiles, CSVFiles, PinName, Mode, TimeMode, UserString, IndexMode):
    # ATPFiles = []
    # CSVFiles = []
    # GetFiles(ATPFiles, Dir, ".atp")
    # GetFiles(CSVFiles, Dir, ".csv")

    if TimeMode == 'Single':
        timemode = '1'
    elif TimeMode == 'Dual':
        timemode = '2'
    CycleRanges = []
    if len(CSVFiles) > 1:
        print("Error: Only ONE CSV file supported !!!")
        return
    CycleRanges = ReadCSV(CSVFiles[0])

    for key in CycleRanges.keys():
        tmpFileName = key  # CycleRanges[i]#CSVFiles[i].replace('.csv', '.atp')
        j = InList(tmpFileName, ATPFiles)
        if j >= 0:
            if Mode == 'DSSC Capture':
                EditPattern(PinName, ATPFiles[j], CycleRanges[key], Mode, timemode, IndexMode)
            elif Mode == 'DSSC Source':
                EditPattern(PinName, ATPFiles[j], CycleRanges[key], Mode, timemode, IndexMode)
            elif Mode == 'CMEM/HRAM Capture':
                EditPattern(PinName, ATPFiles[j], CycleRanges[key], Mode, timemode, IndexMode)
            elif Mode == 'Expand Pattern':
                EditPattern(PinName, ATPFiles[j], CycleRanges[key], Mode, timemode, IndexMode)
            elif Mode == 'Compress Pattern':
                EditPattern(PinName, ATPFiles[j], CycleRanges[key], Mode, timemode, IndexMode)
            elif Mode == 'WFLAG':
                EditPattern(PinName, ATPFiles[j], CycleRanges[key], Mode, timemode, IndexMode)
            elif Mode == 'Call Label':
                EditPattern(PinName, ATPFiles[j], CycleRanges[key], Mode, timemode, IndexMode, UserString)
            else:
                print("Error: Wrong Choice !!!")
        else:
            print("Error: Cannot find atp file: " + tmpFileName)


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


if __name__ == '__main__':
    main11()
    '''
    csv_array = []
    GetFiles(csv_array, r"/Users/Jerry/OneDrive/Python/EditPat", ".csv")  # main2()
    print("Hello World")

    '''
