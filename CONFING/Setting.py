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

"""
从数据库获得part信息列表的各index
part信息列表格式：
[Contract_id, Order_id, Sec_id, Part_id, Door_type, Door_height, Door_width, Door_thick, Package_state, Element_type_id]
例如：
['48', '48O43', '48O43S55', '48O43S55P694', 'MY_1777_橱柜门', 797.0, 458.0, 18, 0, 1]
"""
contract_id_index = 0
order_id_index = 1
sec_id_index = 2
part_id_index = 3
door_type_index = 4
part_length_index = 5  # 部件高是为长length
part_width_index = 6
part_thickness_index = 7
package_state_index = 8
element_type_id_index = 9
"""
从数据库获得纸箱box信息列表的各index
part信息列表格式：
[Box_type, Box_long, Box_short, Box_height]
例如：
['BT650', 650, 450, 268]
"""
box_type_index = 0
box_length_index = 1
box_width_index = 2
box_height_index = 3
