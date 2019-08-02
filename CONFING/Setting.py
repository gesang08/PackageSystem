#!/usr/bin/env python3
# _*_ coding: UTF-8 _*_

import wx
from win32api import GetSystemMetrics  # 用于获取电脑屏幕大小

SCREEN_WIDTH = GetSystemMetrics(0)
SCREEN_HEIGHT = GetSystemMetrics(1)

# 菜单栏中的item项目ID定义
ID_BASE = wx.ID_HIGHEST + 1
ID_LOGIN = ID_BASE + 1
ID_LOGOUT = ID_BASE + 2
ID_EXIT = ID_BASE + 3
ID_SET = ID_BASE + 4

MAX_THICKNESS = 300  # 定义一包的最大的厚度为300mm
HeightOrWidthMax = 2436  # 门板高宽上限
HeightOrWidthMin = 30  # 门板高宽下限
HeightAndWidthLimit = 1200  # 门板高宽不能同时大于1200限制
OnePackageMaxWeight = 50  # 打包的重量最大值设置为50kg，最小值设置为20kg
OnePackageMinWeight = 20
BaseMaterialDensity = 765.18  # 基材密度设置为765.18kg/m^3
OneLayerMaxPlates = 10  # 一层的最大块数设置为10
OnePackageMaxLayers = 10  # 一包的最大层数设置为10

# 数据库相关设置
SERVER_IP = '127.0.0.1'
USER = 'root'
PASSWORD = '12345678'
DB = 'gs_package'
PORT = 3306
CHARSET = 'utf8'
