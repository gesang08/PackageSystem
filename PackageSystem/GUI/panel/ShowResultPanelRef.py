#!usr/bin/env python3
#encoding:utf8

import wx
import wx.grid
from MYSQL.MysqlHelper import MysqlPool
from GUI.panel.DialogRef import PackResultShowDialog
import threading

class ShowResultPanel(wx.Panel):
    def __init__(self, parent, id):
        super(ShowResultPanel, self).__init__(parent, id)

        self.grid=ShowByGrid(parent=self, id=-1)
        vboxsizer = wx.BoxSizer(wx.VERTICAL)  # 对Grid进行流式布局
        vboxsizer.Add(window=self.grid, proportion=1, flag=wx.TOP | wx.EXPAND, border=0)
        self.SetSizer(vboxsizer)
        # wx.CallAfter(callableObj=self.grid.showGrid)
        wx.CallLater(millis=500, callableObj=self.grid.showGrid)


class ShowByGrid(wx.grid.Grid):

    def __init__(self, parent, id=-1, pos=wx.DefaultPosition, size=wx.DefaultSize, style=wx.WANTS_CHARS, name='结果显示'):
        wx.grid.Grid.__init__(self, parent, id, pos, size, style, name)
        self.app = wx.GetApp()
        self.mysql = MysqlPool()
        # self.showGrid()

        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.onCellLeftClick)

    def getRows(self):
        """获取数据库状态为0的打包数据"""
        sql = "SELECT `package_id`, `total_layers`, `total_area`, `total_weight`, `total_volume`, `section_id`, " \
              "`order_id`, `create_time`, `box_type`, `box_length`, `box_width`, `box_height`, `part_num`, " \
              "`volume_rate`, `state` FROM `package_result` WHERE `state` = '0'"
        self.package = self.mysql.do_sql(sql)
        if self.package:
            return len(self.package)

    def showGrid(self):
        print('当前线程是：', threading.current_thread().name)
        rows_num = self.getRows()
        if rows_num:
            self.CreateGrid(rows_num, 15)  # 创建Grid
            #######################设置Column的Header####################
            colHeaders = ['包编号', '层数', '面积', '重量', '体积', '组件号', '订单号',
                          '创建时间', '纸箱类型', '纸箱长', '纸箱宽', '纸箱高', '部件数', '体积利用率', '状态']
            for i, colHeader in enumerate(colHeaders):
                self.SetColLabelValue(col=i, value=colHeader)
            #######################显示每个单元Cell的值####################
            for j, row in enumerate(self.package):
                for k, col in enumerate(row):
                    self.SetCellValue(j, k, str(col))
                    self.SetReadOnly(j, k)
            self.SetFont(
                wx.Font(pointSize=12, family=wx.FONTFAMILY_ROMAN, style=wx.FONTSTYLE_NORMAL, weight=wx.FONTWEIGHT_BOLD))
            # self.AutoSize()
            self.SetColSize(col=0, width=90)
            self.SetColSize(col=7, width=130)
            self.SetColSize(col=8, width=90)

    def onCellLeftClick(self, event):
        self.app.frame.logTextCtrl.write_textctrl_txt('第{}行，第{}列，单元格左上角坐标{} \r\n'.format(str(event.GetRow()), str(event.GetCol()), str(event.GetPosition())))
        # total_rows = self.GetNumberRows()
        # total_cols = self.GetNumberCols()
        # gridRowAttr = wx.grid.GridCellAttr()
        # gridRowAttr.SetBackgroundColour('yellow')
        # self.SetRowAttr(event.GetRow(), gridRowAttr)

        # attr = wx.grid.GridCellAttr()
        # attr.SetBackgroundColour('yellow')
        # self.SetRowAttr(event.GetRow(), attr)

        evtRow = event.GetRow()  # 获取cell点击事件所在的行
        package_id = self.GetCellValue(evtRow, 0)
        create_time = self.GetCellValue(evtRow, 7)

        sql = "SELECT `solution`,`total_layers`,`box_length`,`box_width`,`box_height`, `part_num` FROM `package_result` WHERE `package_id` = '%s' and `create_time`='%s'" % (package_id, create_time)
        solution = self.mysql.do_sql_one(sql)
        if solution:

            packResultShowDialog = PackResultShowDialog(parent=None, id=-1, package_id=package_id,solution=solution)
            packResultShowDialog.ShowModal()
            packResultShowDialog.Destroy()
        self.app.frame.logTextCtrl.write_textctrl_txt(package_id)
        event.Skip()


