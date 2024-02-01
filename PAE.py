'''
Created on Dec 14, 2015

@author: zhouchao
'''
from tkinter import *
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
import traceback
from main import ReadCSV, EditPattern, InList, main4, main11
import multiprocessing
from multiprocessing import Pool, Manager
multiprocessing.freeze_support()

version = 'V1.12.0'

class DemoClass(tk.Tk):

    def __init__(self):
        super().__init__()  # 有点相当于tk.Tk()
        self.ATPfilename = []
        self.CSVfilename = []
        self.createWidgets()

    def createWidgets(self):
        self.title('Pattern Auto Edit Tool ' + version)
        # used to set each widget to resize together
        self.rowconfigure(0, weight=0, minsize=30)
        self.rowconfigure(1, weight=1, minsize=50)
        self.columnconfigure(0, weight=1, minsize=50)
        self.columnconfigure(1, weight=0)

        # create a notebook
        notebook = ttk.Notebook(self)
        notebook.grid(row=0, column=0, sticky="nsew")

        topframe = ttk.Frame(notebook, height=80, borderwidth=1)
        topframe_simple = ttk.Frame(notebook, height=80, borderwidth=1)
        contentframe = ttk.Frame(self, height=80, borderwidth=1)
        contentframe.rowconfigure(0, weight=1)
        contentframe.columnconfigure(0, weight=1)
        topframe.grid(row=0, column=0, sticky=tk.W + tk.S + tk.E + tk.N)
        topframe_simple.grid(row=0, column=0, sticky=tk.W + tk.S + tk.E + tk.N)
        contentframe.grid(row=1, column=0, sticky=tk.W + tk.S + tk.E + tk.N)

        notebook.add(topframe, text='Classical')
        notebook.add(topframe_simple, text='Simplified')

        # Step 1. Please enter ATP file path and name:
        self.ety2 = tk.Entry(topframe, width=40)
        # self.ety2.pack()
        self.ety2.grid(row=0, column=0)

        self.btn2 = tk.Button(
            topframe,
            text='Select ATP Files',
            command=lambda: self.CallATPFile(self.contents2), width=30)
        # self.btn2.pack()
        self.btn2.grid(row=0, column=1)

        self.contents2 = StringVar()
        self.contents2.set("Please Select ATP Files")
        self.ety2.config(textvariable=self.contents2)
        # ATPFile = self.contents2.get()

        # Step 2. Please enter CSV file path and name:
        self.ety3 = tk.Entry(topframe, width=40)
        # self.ety3.pack()
        self.ety3.grid(row=1, column=0)

        self.btn3 = tk.Button(
            topframe,
            text='Select CSV Files',
            command=lambda: self.CallCSVFile(self.contents3), width=30)
        # self.btn2.pack()
        self.btn3.grid(row=1, column=1)

        self.contents3 = StringVar()
        self.contents3.set("Please Select CSV File")
        self.ety3.config(textvariable=self.contents3)
        # CSVFile = self.contents3.get()

        # Step 3. Pin Name Entry
        self.ety = tk.Entry(topframe, width=40)
        # self.ety.pack()
        self.ety.grid(row=2, column=0)

        self.contents4 = StringVar()
        self.contents4.set("Please Enter the Pin Name")
        self.ety.config(textvariable=self.contents4)

        # Step 4. Please choose function
        CmbList = ['DSSC Capture', 'DSSC Source', 'CMEM/HRAM Capture', 'Expand Pattern', 'Compress Pattern', 'WFLAG',
                   'Add opcode', 'Remove Opcode']
        self.cmb = ttk.Combobox(topframe, values=CmbList, width=37)
        # self.cmb.pack()
        self.cmb.grid(row=3, column=0)

        self.contents5 = StringVar()
        self.contents5.set("[Please Select Capture Mode]")
        self.cmb.config(textvariable=self.contents5)

        # Step 5. Please choose time mode
        # CmbList = ['Single', 'Dual']
        # self.cmb2 = ttk.Combobox(topframe, values=CmbList, width=27)
        # # self.cmb.pack()
        # self.cmb2.grid(row=3, column=1)
        #
        # self.contents6 = StringVar()
        # self.contents6.set("[Please Select Time Mode]")
        # self.cmb2.config(textvariable=self.contents6)

        self.check_box_Label2 = ttk.Label(topframe, text='Time Mode:\t\t')
        self.check_box_var2 = StringVar()  # tk.IntVar()
        self.check_box3 = ttk.Radiobutton(topframe,
                                          text=u'Single',
                                          variable=self.check_box_var2,
                                          value='Single',
                                          command=self.on_radiobox_changed)
        self.check_box4 = ttk.Radiobutton(topframe,
                                          text=u'Dual',
                                          variable=self.check_box_var2,
                                          value='Dual',
                                          command=self.on_radiobox_changed)
        self.check_box_var2.set('Single')
        self.check_box_Label2.grid(row=4, column=0, sticky='E')
        self.check_box3.grid(row=4, column=1, sticky='W')
        self.check_box4.grid(row=4, column=1, sticky='E')

        # Step 6, button
        self.btn = tk.Button(topframe, text='Generate', command=self.SayHello_MultProcess)  # self.SayHello)
        # self.btn.pack()
        self.btn.grid(row=6, column=0, columnspan=2)

        # Step 7. Label Name Entry
        self.ety2 = tk.Entry(topframe, width=40)
        # self.ety.pack()
        self.ety2.grid(row=3, column=1)

        self.contents7 = StringVar()
        self.contents7.set("Please Enter the User String")
        self.ety2.config(textvariable=self.contents7)
        # self.tk.mainloop()

        # Step 8. Please choose index mode
        self.check_box_Label = ttk.Label(topframe, text='Index Mode:\t\t')
        self.check_box_var1 = StringVar()  # tk.IntVar()
        self.check_box1 = ttk.Radiobutton(topframe,
                                          text=u'Cycle',
                                          variable=self.check_box_var1,
                                          value='Cycle',
                                          command=self.on_radiobox_changed)
        self.check_box2 = ttk.Radiobutton(topframe,
                                          text=u'Vector',
                                          variable=self.check_box_var1,
                                          value='Vector',
                                          command=self.on_radiobox_changed)
        self.check_box_var1.set('Cycle')
        self.check_box_Label.grid(row=5, column=0, sticky='E')
        self.check_box1.grid(row=5, column=1, sticky='W')
        self.check_box2.grid(row=5, column=1, sticky='E')


        # Simplified Tab
        # Step 1. Please enter ATP file path and name:
        self.ety2_simple = tk.Entry(topframe_simple, width=40)
        self.ety2_simple.grid(row=0, column=0)

        self.btn2_simple = tk.Button(
            topframe_simple,
            text='Select ATP Files',
            command=lambda: self.CallATPFile(self.contents2_simple), width=30)
        # self.btn2.pack()
        self.btn2_simple.grid(row=0, column=1)

        self.contents2_simple = StringVar()
        self.contents2_simple.set("Please Select ATP Files")
        self.ety2_simple.config(textvariable=self.contents2_simple)
        # ATPFile = self.contents2.get()

        # Step 2. Please enter CSV file path and name:
        self.ety3_simple = tk.Entry(topframe_simple, width=40)
        # self.ety3.pack()
        self.ety3_simple.grid(row=1, column=0)

        self.btn3_simple = tk.Button(
            topframe_simple,
            text='Select CSV Files',
            command=lambda: self.CallCSVFile(self.contents3_simple), width=30)
        # self.btn2.pack()
        self.btn3_simple.grid(row=1, column=1)
        self.contents3_simple = StringVar()
        self.contents3_simple.set("Please Select CSV File")
        self.ety3_simple.config(textvariable=self.contents3_simple)
        # CSVFile = self.contents3.get()

        # Step 6, button
        self.btn_simple = tk.Button(topframe_simple, text='Generate', command=self.SayHello_simple)  # self.SayHello)
        # self.btn.pack()
        self.btn_simple.grid(row=6, column=0, columnspan=2)



        # output log part
        right_bar = tk.Scrollbar(contentframe, orient=tk.VERTICAL)
        bottom_bar = tk.Scrollbar(contentframe, orient=tk.HORIZONTAL)
        self.textbox = tk.Text(contentframe, yscrollcommand=right_bar.set, xscrollcommand=bottom_bar.set)
        self.textbox.config()
        self.textbox.grid(row=0, column=0, sticky=tk.W + tk.S + tk.E + tk.N)
        right_bar.grid(row=0, column=1, sticky=tk.S + tk.N)
        bottom_bar.grid(row=1, column=0, sticky=tk.W + tk.E)
        right_bar.config(command=self.textbox.yview)
        bottom_bar.config(command=self.textbox.xview)

    def put_data_log(self, data_log):
        self.textbox.insert(tk.END, data_log + '\n')
        self.textbox.see(tk.END)
        self.textbox.update()

    def on_radiobox_changed(self):
        print(self.check_box_var1.get())

    def SayHello(self):  # (, ATPFile, CSVFile, PinName, Mode):
        ATPFile = self.ATPfilename
        # sss =  self.contents2.get()
        CSVFile = self.CSVfilename
        # Dir = FolderPath
        PinName = self.ety.get()
        Mode = self.cmb.get()
        TimeMode = self.check_box_var2.get()  # self.cmb2.get()
        UserString = self.ety2.get()
        IndexMode = self.check_box_var1.get()
        textout = self.put_data_log
        main4(ATPFile, CSVFile, PinName, Mode, TimeMode, UserString, IndexMode, textout)

    def SayHello_simple(self):  # (, ATPFile, CSVFile, PinName, Mode):
        ATPFile = self.ATPfilename
        CSVFile = self.CSVfilename

        # PinName = self.ety.get()
        # Mode = self.cmb.get()
        # TimeMode = self.check_box_var2.get()  # self.cmb2.get()
        # UserString = self.ety2.get()
        # IndexMode = self.check_box_var1.get()
        textout = self.put_data_log
        main11(ATPFile, CSVFile[0], textout)

    def SayHello_MultProcess(self):
        # disable button
        self.switchButtonState(self.btn)

        # initial variables
        ATPFiles = self.ATPfilename
        # sss =  self.contents2.get()
        CSVFiles = self.CSVfilename
        # Dir = FolderPath
        PinName = self.ety.get()
        Mode = self.cmb.get()
        TimeMode = self.check_box_var2.get()  # self.cmb2.get()
        UserString = self.ety2.get()
        IndexMode = self.check_box_var1.get()
        textoutwin = self.put_data_log

        self.queue = Manager().Queue()
        self.counter = Manager().Value('i', 0)
        self.pool = Pool(processes=4)  # max 4 processes

        # main4 part
        try:
            CmbList = ['DSSC Capture', 'DSSC Source', 'CMEM/HRAM Capture', 'Expand Pattern', 'Compress Pattern', 'WFLAG',
                       'Add opcode', 'Remove Opcode']
            if TimeMode == 'Single':
                timemode = '1'
            elif TimeMode == 'Dual':
                timemode = '2'
            CycleRanges = []
            if len(CSVFiles) > 1:
                textoutwin("Error: Only ONE CSV file supported !!!")
                print("Error: Only ONE CSV file supported !!!")
                return
            CycleRanges = ReadCSV(CSVFiles[0])

            self.total_tasks = 0
            for key in CycleRanges.keys():
                tmpFileName = key  # CycleRanges[i]#CSVFiles[i].replace('.csv', '.atp')
                j = InList(tmpFileName, ATPFiles)
                if j >= 0:
                    textoutwin("Info: Start convert file: " + ATPFiles[j])
                    print("Info: start convert file: +" + ATPFiles[j])
                    if Mode in CmbList:
                        self.total_tasks += 1
                        self.pool.apply_async(EditPattern, args=(
                            self.queue.put, PinName, ATPFiles[j], CycleRanges[key], Mode, timemode, IndexMode,
                            UserString), callback=self.my_callback)
                    else:
                        textoutwin("Error: Wrong Choice !!!")
                        print("Error: Wrong Choice !!!")
                    # textoutwin("Info: Done conversion: " + ATPFiles[j])
                    # print("Info: Done conversion: " + ATPFiles[j])
                else:
                    textoutwin("Warning: Cannot find atp file: " + tmpFileName)
                    print("Warning: Cannot find atp file: " + tmpFileName)
            self.after(500, self.update_progress)
        except Exception:
            error_msg = traceback.format_exc()
            self.put_data_log(error_msg)
            # enable button
            self.switchButtonState(self.btn)

    def my_callback(self, result):
        self.counter.value += 1
        if self.counter.value == self.total_tasks:
            self.put_data_log("All tasks completed!!!")
            # enable button
            self.switchButtonState(self.btn)

    def update_progress(self):
        if self.queue.empty() == False:
            message = self.queue.get()
            self.put_data_log(message)
        self.after(500, self.update_progress)

    def switchButtonState(self, button):
        if (button['state'] == tk.NORMAL):
            button['state'] = tk.DISABLED
        else:
            button['state'] = tk.NORMAL

    def CallATPFile(self, contents2):
        # global ATPfilename
        self.ATPfilename = tk.filedialog.askopenfilenames(
            filetypes=[('ATP File', '*.atp;*.atp.gz'), ("all", "*.*")])  #
        contents2.set(self.ATPfilename)
        # print(filename)

    def CallCSVFile(self, contents3):
        # global CSVfilename
        self.CSVfilename = tk.filedialog.askopenfilenames(
            filetypes=[('CSV File', '*.csv'), ("all", "*.*")])
        contents3.set(self.CSVfilename)
        # print(filename)

    def GetFolderPath(self, contents2):
        global FolderPath
        FolderPath = tk.filedialog.askdirectory()
        contents2.set(FolderPath)

    def addmenu(self, Menu):
        Menu(self)


class MyMenu():
    '''class for menu'''

    def __init__(self, root):
        '''initial menu class'''
        self.menubar = tk.Menu(root)  # Create Menu Bar

        # create "File"
        filemenu = tk.Menu(self.menubar, tearoff=0)
        filemenu.add_command(label="Exit", command=root.quit)

        # create "Help"
        helpmenu = tk.Menu(self.menubar, tearoff=0)
        helpmenu.add_command(label="About", command=self.help_about)

        # add menu to menu bar
        self.menubar.add_cascade(label="File", menu=filemenu)
        self.menubar.add_cascade(label="Help", menu=helpmenu)

        # add menu bar to win "root"
        root.config(menu=self.menubar)

    def help_about(self):
        messagebox.showinfo(
            'About',
            'Author：Chao Zhou \n verion ' + version + '\n 感谢您的使用！ \n chao.zhou@teradyne.com ')  # message box


if __name__ == '__main__':
    win = DemoClass()
    win.addmenu(MyMenu)
    win.mainloop()
