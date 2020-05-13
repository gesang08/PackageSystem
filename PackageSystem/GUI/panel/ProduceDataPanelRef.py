#!usr/bin/env python3
#encoding:utf8

import wx
import wx.aui as aui
from MYSQL.MysqlHelper import MysqlPool

class ProduceDataPanel(wx.Panel):
    def __init__(self, parent, id):
        super(ProduceDataPanel, self).__init__(parent, id)

        hboxsizer = wx.BoxSizer(wx.HORIZONTAL)
        # create several text controls
        text1 = wx.TextCtrl(parent=self,value='',
                            style=wx.NO_BORDER | wx.TE_MULTILINE|wx.TE_READONLY)
        text2 = wx.TextCtrl(parent=self,value='',
                            style=wx.NO_BORDER | wx.TE_MULTILINE|wx.TE_NO_VSCROLL|wx.TE_READONLY)
        hboxsizer.Add(window=text1, proportion=1, flag=wx.LEFT|wx.EXPAND, border=0)
        hboxsizer.Add(window=text2, proportion=2, flag=wx.RIGHT|wx.EXPAND, border=0)
        hboxsizer1 = wx.BoxSizer(wx.HORIZONTAL)

        self.contractLabel = wx.StaticText(parent=text1, id=-1, label='合同：')
        self.contractText = wx.TextCtrl(parent=text1, id=-1, value=str(12))
        self.contractBtn = wx.Button(parent=text1, id=-1, label='添加合同')
        hboxsizer1.Add(window=self.contractLabel, proportion=0, flag=wx.TOP | wx.LEFT, border=20)
        hboxsizer1.Add(window=self.contractText, proportion=0, flag=wx.TOP | wx.LEFT, border=20)
        hboxsizer1.Add(window=self.contractBtn, proportion=0, flag=wx.TOP | wx.LEFT, border=20)
        text1.SetSizer(hboxsizer1)
        self.SetSizer(hboxsizer)

class GetIndex:
    def __init__(self):
        self.mysql = MysqlPool()
    def getContractIndex(self):
        contractIndex = 1
        sql = "SELECT `Index` FROM `order_contract_internal` WHERE 1  ORDER BY `Index` DESC  LIMIT 1"
        rev = self.mysql.do_sql_one(sql)
        if rev:
            contractIndex = rev[0] + 1
        return contractIndex
    def getOrderIndex(self):
        orderIndex = 1
        sql = "SELECT `Index` FROM `order_order_online` WHERE 1  ORDER BY `Index` DESC  LIMIT 1"
        rev = self.mysql.do_sql_one(sql)
        if rev:
            orderIndex = rev[0] + 1
        return orderIndex
    def getSectionIndex(self):
        sectionIndex = 1
        sql = "SELECT `Index` FROM `order_section_online` WHERE 1  ORDER BY `Index` DESC  LIMIT 1"
        rev = self.mysql.do_sql_one(sql)
        if rev:
            sectionIndex = rev[0] + 1
        return sectionIndex





