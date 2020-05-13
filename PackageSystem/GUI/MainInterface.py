#!usr/bin/env python3
#encoding:utf8

import wx
import time
import os, sys
import threading
import wx.aui
from confs.Setting import *
from GUI.panel.NotoBookRef import MyNoteBook
from GUI.RichTextCtrl import RichText
from GUI.panel.DialogRef import BoxGeneratorDialog,BoxGeneratorDialog2,BoxGeneratorDialog3,PartGeneratorDialog

class MainFrame(wx.Frame):
    def __init__(self, parent, id, title, pos, size, style):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        #######################创建状态栏#######################
        self.setupStatusBar()
        #######################创建菜单栏#######################
        self.setupMenuBar()
        #######################创建工具栏#######################
        self.setupToolBar()
        #######################创建面板########################
        self.initUI()
        #######################标题栏图标#######################
        self.setupIcon()

    def initUI(self):
        ################Notebook的调用##########################
        vboxsizer = wx.BoxSizer(orient=wx.VERTICAL)  # 对NoteBook和日志TextCtrl进行流式布局
        self.logTextCtrl = RichText(parent=self, id=-1)
        self.myNoteBook = MyNoteBook(parent=self, id=-1,log=self.logTextCtrl)

        vboxsizer.Add(window=self.myNoteBook, proportion=1, flag=wx.TOP | wx.EXPAND, border=0)  # proportion=0表示不能伸缩改变,proportion>0表示能伸缩改变
        vboxsizer.Add(window=self.logTextCtrl, proportion=0, flag=wx.BOTTOM | wx.EXPAND, border=0)
        self.SetSizer(vboxsizer)

    def setupStatusBar(self):
        self.statusBar = self.CreateStatusBar(number=3)  # 将状态栏分2栏
        self.SetStatusWidths([-1, -4, -1])  # 以2:1的长度比例分栏
        self.SetStatusText("Ready", 0)  # 在栏1里显示文本

        self.timer = wx.PyTimer(self.notify)  # derived from wx.Timer
        self.timer.Start(1000, wx.TIMER_CONTINUOUS)  # 以1秒钟的时间，不停在跑
        self.notify()  # 加上运行frame可以立即显示，否则需要等待1秒钟时间

    def setupIcon(self):
        self.icon_path = './IMAGE/title_icon.jpg'
        icon = wx.Icon(self.icon_path, wx.BITMAP_TYPE_JPEG)  # 将png转换成bitmap位图
        self.SetIcon(icon)

    def setupMenuBar(self):
        ######################创建菜单栏########################
        menubar = wx.MenuBar()

        ############################################创建开始菜单###################################################
        start_menu = wx.Menu()
        ######################创建菜单项：登入####################
        login_menu_item = wx.MenuItem(parentMenu=start_menu, id=ID_LOGIN, text='登入(&I)')
        start_menu.Append(menuItem=login_menu_item)
        self.Bind(wx.EVT_MENU, self.onLogin, id=ID_LOGIN)
        ######################创建菜单项：登出####################
        logout_menu_item = wx.MenuItem(parentMenu=start_menu, id=ID_LOGOUT, text='登出(&O)')
        start_menu.Append(menuItem=logout_menu_item)
        self.Bind(wx.EVT_MENU, self.onLogout, id=ID_LOGOUT)

        start_menu.AppendSeparator()

        ######################创建菜单项：退出####################
        exit_menu_item = wx.MenuItem(parentMenu=start_menu, id=ID_EXIT, text='退出(&E)')
        start_menu.Append(menuItem=exit_menu_item)
        self.Bind(wx.EVT_MENU, self.onExit, id=ID_EXIT)

        menubar.Append(menu=start_menu, title='开始(&S)')  # 将菜单开始添加到菜单栏

        ############################################创建设置菜单###################################################
        set_menu = wx.Menu()

        menubar.Append(menu=set_menu, title='设置(&T)')  # 将菜单开始添加到菜单栏

        ############################################创建生成菜单###################################################
        produce_menu = wx.Menu()
        ######################创建菜单项：随机生成板件数据####################
        random_part_menu_item = wx.MenuItem(parentMenu=produce_menu, id=ID_RANDOM_PART, text='板件数据(&P)')
        produce_menu.Append(menuItem=random_part_menu_item)
        self.Bind(wx.EVT_MENU, self.onRandomPart, id=ID_RANDOM_PART)
        ######################创建菜单项：纸箱数据生成####################
        box_menu_item = wx.MenuItem(parentMenu=produce_menu, id=ID_GENERATE_BOX, text='纸箱数据(&B)')
        produce_menu.Append(menuItem=box_menu_item)
        self.Bind(wx.EVT_MENU, self.onGenerateBox, id=ID_GENERATE_BOX)

        menubar.Append(menu=produce_menu, title='生成(&P)')  # 将菜单开始添加到菜单栏

        ############################################创建帮助菜单###################################################
        help_menu = wx.Menu()

        menubar.Append(menu=help_menu, title='帮助(&H)')  # 将菜单开始添加到菜单栏

        self.SetMenuBar(menubar)  # 将菜单栏显示到frame上

    def setupToolBar(self):
        #################创建工具栏#######################
        toolbar = self.CreateToolBar()

        toolbar.AddSeparator()
        quit_tool_item = toolbar.AddTool(toolId=ID_EXIT, label='',bitmap=wx.Bitmap('./IMAGE/quit.jpg'),shortHelp='退出')
        self.Bind(wx.EVT_TOOL, self.onExit, quit_tool_item)

        # box_tool_item = toolbar.AddTool(toolId=ID_GENERATE_BOX, label='', bitmap=wx.Bitmap('./IMAGE/box.png'),
        #                                  shortHelp='纸箱生成')
        # self.Bind(wx.EVT_TOOL, self.onGenerateBox, box_tool_item)
        toolbar.Realize()  # 准备显示工具栏

    def onLogin(self, event):
        pass

    def onLogout(self, event):
        pass

    def onExit(self, event):
        self.Close()
        event.Skip()

    def notify(self):
        try:
            st = time.strftime('%Y{y}%m{m}%d{d}  %H{h}%M{f}%S{s}').format(y='-', m='-', d='', h=':', f=':', s='')
            self.SetStatusText(st, 2)
        except:
            pass

    def onRandomPart(self, event):
        dlg = PartGeneratorDialog(None, -1, self.logTextCtrl)
        dlg.ShowModal()
        dlg.Destroy()
        event.Skip()

    def onGenerateBox(self, event):
        dlg = BoxGeneratorDialog2(None, -1, self.logTextCtrl)
        dlg.ShowModal()
        dlg.Destroy()
        event.Skip()

class MyApp(wx.App):
    def __init__(self):
        wx.App.__init__(self)

    def OnInit(self):
        self.frame = MainFrame(parent=None, id=-1, title='Package System', pos=wx.DefaultPosition,
                               size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE | wx.MAXIMIZE)
        self.SetTopWindow(frame=self.frame)
        self.frame.Center()
        print('当前线程是：', threading.current_thread().name)
        self.frame.Show(show=True)
        return True

def mainUI():
    app = MyApp()
    app.MainLoop()

if __name__ == '__main__':
    mainUI()