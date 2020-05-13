#!usr/bin/env python3
#encoding:utf8

import wx
from GUI.panel.ProduceDataPanelRef import ProduceDataPanel
from GUI.panel.ShowResultPanelRef import ShowResultPanel
from GUI.panel.AlgorithmSetPanelRef import AlgorithmSetPanel

class MyNoteBook(wx.Notebook):
    def __init__(self, parent, id, log):
        super(MyNoteBook, self).__init__(parent, id)
        self.panels = []

        ###############为界面设置Notebook#################
        # self.producepanel = ProduceDataPanel(parent=self, id=-1)
        # self.panels.append(self.producepanel)
        # self.AddPage(page=self.panels[0], text='生成数据')

        self.resultpanel = ShowResultPanel(parent=self, id=-1)
        self.panels.append(self.resultpanel)
        self.AddPage(page=self.panels[0], text='显示结果')

        self.setpanel = AlgorithmSetPanel(parent=self, id=-1, log=log)
        self.panels.append(self.setpanel)
        self.AddPage(page=self.panels[1], text='算法设置')

