'''
Created on Dec 8, 2015

@author: zhouchao
'''
import csv
import os
import re


def EditPattern(PinName, something, CSVFile, Mode, timemode):
    OutputPath = os.getcwd() + '/Output'
    if not os.path.exists(OutputPath):  # check the directory is existed or not
        os.mkdir(OutputPath)
    if Mode=='Expand Pattern':
        RemoveRepeat(something, timemode)
        RemoveRepeatFile = os.path.realpath('new_RemoveRepeat.atp')
        return
    
    CycleRange = ReadCSV(CSVFile)
    otherthing = os.path.join(OutputPath, os.path.basename(something))
    
    LineIndex = 0
    CycleNum = 0
    RepeatCnt = 0

    with open(otherthing, mode='w') as NewATPfile:
        # with open(RemoveRepeatFile) as ATPfile:
        with open(something) as ATPfile:
            while True:
                line = ATPfile.readline()
                LineIndex += 1

                # modify the body part of atp file
                if line.find(r">") == -1:
                    # check the timeset name
                    if line[0:6] == "import":
                        tset = line[12:-2]
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

                    # check the index of pin
                    elif line.find("$tset") != -1:
                        Index = FindPinIndex(PinName, line)
                        NewATPfile.write(line)

                    else:
                        NewATPfile.write(line)
                elif line.find(r"> {0}".format(tset)) != -1:
                    RepeatCnt = GetRepeatCnt(line)
                    if CycleNum == 0:

                        # find the modify position
                        ModifyIndex = 0
                        CountNum = 0

                        pattern = re.compile(r"> {0}".format(tset))
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
                                CycleNumList = [CycleNum, CycleNum+RepeatCnt-1]
                                if CheckInSameRange(CycleNumList, CycleRange):
                                    line = line[0:ModifyIndex] + \
                                        "V" + line[ModifyIndex + 1:]
                                    line = "(({0}):DigCap = Store)".format(
                                        PinName) + line

                        elif Mode == 'DSSC Source':
                            if RepeatCnt == 1:
                                if CheckInRange(CycleNum, CycleRange):
                                    # line[ModifyIndex] = "V"
                                    line = line[0:ModifyIndex] + \
                                        "D" + line[ModifyIndex + 1:]
                                    line = "(({0}):DigSrc = Send)".format(
                                        PinName) + line
                            else:
                                CycleNumList = [CycleNum, CycleNum+RepeatCnt-1]
                                if CheckInSameRange(CycleNumList, CycleRange):
                                    line = line[0:ModifyIndex] + \
                                        "D" + line[ModifyIndex + 1:]
                                    line = "(({0}):DigSrc = Send)".format(
                                        PinName) + line

                        elif Mode == 'CMEM/HRAM Capture':
                            if RepeatCnt == 1:
                                if CheckInRange(CycleNum, CycleRange):
                                    # line[ModifyIndex] = "V"
                                    line = line[0:ModifyIndex] + \
                                        "V" + line[ModifyIndex + 1:]
                                    line = "stv    " + line
                            else:
                                CycleNumList = [CycleNum, CycleNum+RepeatCnt-1]
                                if CheckInSameRange(CycleNumList, CycleRange):
                                    line = line[0:ModifyIndex] + \
                                        "V" + line[ModifyIndex + 1:]
                                    line = line.replace('repeat', 'stv,repeat')

                    NewATPfile.write(line)
                    #CycleNum += 1
                    CycleNum += RepeatCnt

                if len(line) == 0:
                    break


def ReadCSV(something):
    CycleRange = []
    with open(something) as f:
        f_csv = csv.reader(f)
        for row in f_csv:
            if f_csv.line_num == 1:
                continue
            tmparray = re.findall(r"\d+", row[0])
            tmparray = sorted([int(x) for x in tmparray])
            CycleRange.append(tmparray)
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
    pattern = re.compile(r'(?<=\,)\s*([^\,^\s]+)(?=[\,\)\s*])')
    tmparray = re.findall(pattern, STRLine)
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
    otherthing = os.path.realpath('new_RemoveRepeat.atp')

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
                    if headerline.find(r"start_label") != - \
                            1:  # check the header part
                        Boby_Flag = True

                    if len(headerline) == 0:
                        break

                    NewATPfile.write(headerline)
                else:
                    for i in range(linenum):
                        line.append(ATPfile.readline())
                        LineIndex += 1
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

                        if line[-1].find(r'halt') != -1:
                            Boby_Flag = False


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


def main11():
    something = input('Step 1. Please enter ATP file path and name:\n')
    CSVFile = input("Step 2. Please enter CSV file path and name:\n")
    PinName = input('Step 3. Please enter the name of the pin need to edit:\n')
    print('Step 4. Please choose function, input the NO.')
    choosefunction = input(
        '1.DSSC Capture;\n2.DSSC Source;\n3.CMEM/HRAM Capture.\n')
    timemode = input('1. Single\n2. Dual')

    # DSSCCap(PinName, r"C:\Users\zhouchao\workspace\EditPat\src\DIEID_READ_R01_SD6183V100.atp", r"C:\Users\zhouchao\workspace\EditPat\src\Book1.csv")
    # DSSCSrc(PinName, r"C:\Users\zhouchao\workspace\EditPat\src\DIEID_WRITE_R01_SD6183V100.atp", r"C:\Users\zhouchao\workspace\EditPat\src\Write.csv")
    # CMEMCap(PinName, r"C:\Users\zhouchao\workspace\EditPat\src\DIEID_READ_R01_SD6183V100.atp", r"C:\Users\zhouchao\workspace\EditPat\src\Book1.csv")
    # os.system('pause')
    input('Press Enter key to exit!')


def main4(ATPFiles, CSVFiles, PinName, Mode, TimeMode):
    # ATPFiles = []
    # CSVFiles = []
    # GetFiles(ATPFiles, Dir, ".atp")
    # GetFiles(CSVFiles, Dir, ".csv")

    if TimeMode == 'Single':
        timemode = '1'
    elif TimeMode == 'Dual':
        timemode = '2'

    for i in range(len(CSVFiles)):
        tmpFileName = CSVFiles[i].replace('.csv', '.atp')
        j = InList(tmpFileName, ATPFiles)
        if j >= 0:

            if Mode == 'DSSC Capture':
                EditPattern(PinName, ATPFiles[j], CSVFiles[i], Mode, timemode)
            elif Mode == 'DSSC Source':
                EditPattern(PinName, ATPFiles[j], CSVFiles[i], Mode, timemode)
            elif Mode == 'CMEM/HRAM Capture':
                EditPattern(PinName, ATPFiles[j], CSVFiles[i], Mode, timemode)
            elif Mode == 'Expand Pattern':
                EditPattern(PinName, ATPFiles[j], CSVFiles[i], Mode, timemode)
            else:
                print("Wrong Choice !!!")


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
        if str == tmplist[i]:
            return i
    return -1


if __name__ == '__main__':
    main11()
    '''
    csv_array = []
    GetFiles(csv_array, r"/Users/Jerry/OneDrive/Python/EditPat", ".csv")  # main2()
    print("Hello World")

    '''
