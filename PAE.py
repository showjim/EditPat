'''
Created on Dec 14, 2015

@author: zhouchao
'''
from tkinter import *
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
from tkinter import messagebox
from argparse import FileType
from main import *

version = 'V1.9.6'

class DemoClass(tk.Tk):

    def __init__(self):
        super().__init__()  # 有点相当于tk.Tk()
        self.createWidgets()

    def createWidgets(self):
        self.title('Pattern Auto Edit Tool ' + version)
        self.columnconfigure(0, minsize=50)

        topframe = tk.Frame(self, height=80)
        contentframe = tk.Frame(self)
        topframe.pack(side=tk.TOP)
        contentframe.pack(side=tk.TOP)

        # Step 1. Please enter ATP file path and name:
        self.ety2 = tk.Entry(topframe, width=30)
        # self.ety2.pack()
        self.ety2.grid(row=0, column=0)

        self.btn2 = tk.Button(
            topframe,
            text='Select ATP Files',
            command=self.CallATPFile)
        # self.btn2.pack()
        self.btn2.grid(row=0, column=1)

        self.contents2 = StringVar()
        self.contents2.set("Please Select ATP Files")
        self.ety2.config(textvariable=self.contents2)
        # ATPFile = self.contents2.get()

        # Step 2. Please enter CSV file path and name:
        self.ety3 = tk.Entry(topframe, width=30)
        # self.ety3.pack()
        self.ety3.grid(row=1, column=0)

        self.btn3 = tk.Button(
            topframe,
            text='Select CSV Files',
            command=self.CallCSVFile)
        # self.btn2.pack()
        self.btn3.grid(row=1, column=1)

        self.contents3 = StringVar()
        self.contents3.set("Please Select CSV File")
        self.ety3.config(textvariable=self.contents3)
        # CSVFile = self.contents3.get()

        # Step 3. Pin Name Entry
        self.ety = tk.Entry(topframe, width=30)
        # self.ety.pack()
        self.ety.grid(row=2, column=0)

        self.contents4 = StringVar()
        self.contents4.set("Please Enter the Pin Name")
        self.ety.config(textvariable=self.contents4)

        # Step 4. Please choose function
        CmbList = ['DSSC Capture', 'DSSC Source', 'CMEM/HRAM Capture','Expand Pattern', 'Compress Pattern', 'WFLAG', 'Call Label']
        self.cmb = ttk.Combobox(topframe, values=CmbList, width=27)
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

        self.check_box_Label2 = ttk.Label(topframe, text='Time Mode:')
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
        self.check_box_Label2.grid(row=4, column=0, sticky='W')
        self.check_box3.grid(row=4, column=1, sticky='W')
        self.check_box4.grid(row=4, column=1, sticky='E')

        # Step 6, button
        self.btn = tk.Button(topframe, text='Generate', command=self.SayHello)
        # self.btn.pack()
        self.btn.grid(row=6, column=0, columnspan=2)

        # Step 7. Label Name Entry
        self.ety2 = tk.Entry(topframe, width=30)
        # self.ety.pack()
        self.ety2.grid(row=3, column=1)

        self.contents7 = StringVar()
        self.contents7.set("Please Enter the User String")
        self.ety2.config(textvariable=self.contents7)
        # self.tk.mainloop()

        # Step 8. Please choose index mode
        self.check_box_Label = ttk.Label(topframe, text='Index Mode:')
        self.check_box_var1 = StringVar() #tk.IntVar()
        self.check_box1 = ttk.Radiobutton(topframe,
                                         text=u'Cycle',
                                         variable = self.check_box_var1,
                                         value = 'Cycle',
                                         command=self.on_radiobox_changed)
        self.check_box2 = ttk.Radiobutton(topframe,
                                          text=u'Vector',
                                          variable=self.check_box_var1,
                                          value='Vector',
                                          command=self.on_radiobox_changed)
        self.check_box_var1.set('Cycle')
        self.check_box_Label.grid(row=5, column=0, sticky='W')
        self.check_box1.grid(row=5, column=1, sticky='W')
        self.check_box2.grid(row=5, column=1, sticky='E')


    def on_radiobox_changed(self):
        print(self.check_box_var1.get())

    def SayHello(self):  # (, ATPFile, CSVFile, PinName, Mode):
        ATPFile = ATPfilename
        # sss =  self.contents2.get()
        CSVFile = CSVfilename
        # Dir = FolderPath
        PinName = self.ety.get()
        Mode = self.cmb.get()
        TimeMode = self.check_box_var2.get() #self.cmb2.get()
        UserString = self.ety2.get()
        IndexMode = self.check_box_var1.get()
        main4(ATPFile, CSVFile, PinName, Mode, TimeMode, UserString, IndexMode)

    def CallATPFile(self):
        global ATPfilename
        ATPfilename = tk.filedialog.askopenfilenames(
            filetypes=[('ATP File', '*.atp'), ("all", "*.*")])  #
        self.contents2.set(ATPfilename)
        # print(filename)

    def CallCSVFile(self):
        global CSVfilename
        CSVfilename = tk.filedialog.askopenfilenames(
            filetypes=[('CSV File', '*.csv'), ("all", "*.*")])
        self.contents3.set(CSVfilename)
        # print(filename)

    def GetFolderPath(self):
        global FolderPath
        FolderPath = tk.filedialog.askdirectory()
        self.contents2.set(FolderPath)

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
