#!usr/bin/env python3
#encoding:utf8

import wx
import datetime
import os
from MYSQL.MysqlHelper import Mysql
from PublicRef.PublicRef import current_time

class RichText(wx.TextCtrl):
    """
    三种记录日志的方法：1.记录日志到界面的日志TextCtrl;2.记录日志到数据库info_log表；3.记录日志到项目文件下的log.txt
    """
    def __init__(self, parent, id=-1, value="", pos=wx.Point(0, 0), size=wx.Size(150, 90),
                 style=wx.NO_BORDER | wx.TE_MULTILINE | wx.TE_READONLY):  # value即是TextCtrl中的Text的值
        wx.TextCtrl.__init__(self, parent, id, value, pos, size, style)
        self.log_file = 'log.txt'
        self.log_table_name = 'info_log'

    def write_textctrl_db(self, text, enable=True, font=wx.NORMAL_FONT, colour=wx.BLACK):
        """
        写日志到TextCtrl和数据库中
        :param text:
        :param enable:
        :param font:
        :param colour:
        :return:
        """
        if enable:
            sql = "INSERT INTO `%s`(`error_occurance_time`,`event`) VALUES ('%s','%s')" % \
                  (self.log_table_name, datetime.datetime.now(), text)
            try:
                mydb = Mysql()
                mydb.modify_sql(sql)
            except Exception as e:
                wx.TextCtrl.WriteText(self, current_time() + str(e))
            text = current_time() + text
            wx.TextCtrl.SetFont(self, font)
            wx.TextCtrl.SetForegroundColour(self, colour)
            try:
                wx.TextCtrl.WriteText(self, text)
            except Exception as e:
                wx.TextCtrl.WriteText(self, current_time() + str(e))

    def write_textctrl_txt(self, text, enable=True, font=wx.NORMAL_FONT, colour=wx.BLACK):
        if enable:
            text = current_time() + ' ' + text + '\n'
            all_files = os.listdir(os.getcwd())  # 获取当前工程项目文件夹下所有文件名
            if self.log_file not in all_files:  # 若该文件不存在，在当前目录创建一个日志文件
                self.log_file = open(self.log_file, 'w+')
                self.log_file.close()
                self.log_file = self.log_file.name
            with open(self.log_file, 'a+') as file_obj:  # 向日志文件加log
                file_obj.write(text)
            wx.TextCtrl.SetFont(self, font)
            wx.TextCtrl.SetForegroundColour(self, colour)
            try:
                wx.TextCtrl.WriteText(self, text)
            except Exception as e:
                wx.TextCtrl.WriteText(self, current_time() + str(e))

