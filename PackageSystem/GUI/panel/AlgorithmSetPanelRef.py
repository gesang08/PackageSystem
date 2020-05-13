#!usr/bin/env python3
#encoding:utf8

import wx
from ThreadHelper import LoopTimer
from CartonPackAlgorithm import CartonPackAlgorithmMain
import threading
class AlgorithmSetPanel(wx.Panel):
    def __init__(self, parent, id, log):
        super(AlgorithmSetPanel, self).__init__(parent, id)
        self.log=log
        self.button=wx.Button(parent=self,label='确定',pos=(50, 50))
        self.button.Bind(wx.EVT_BUTTON, self.do)

    def do(self, event):
        # CartonPackAlgorithmMain()
        # loop = LoopTimer(interval=2, target=CartonPackAlgorithmMain)
        # loop.start()
        # loop.join()
        self.thread = threading.Thread(target=CartonPackAlgorithmMain, args=(self.log,))
        self.thread.start()
        # self.win = TestFrame(self, self.log)
        # self.win.Show(True)
        event.Skip()
