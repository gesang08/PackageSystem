#!/usr/bin/env python3
# _*_ coding: UTF-8 _*_

# import wx
import math,time
from win32api import GetSystemMetrics  # 用于获取电脑屏幕大小
from matplotlib.font_manager import FontProperties  # 通过字体管理器下面的FontProperties类来控制plt图的字体属性
import matplotlib # 注意这个也要import一次

SCREEN_WIDTH = GetSystemMetrics(0)
SCREEN_HEIGHT = GetSystemMetrics(1)

# 菜单栏中的item项目ID定义
# ID_BASE = wx.ID_HIGHEST + 1
ID_BASE = 200
ID_LOGIN = ID_BASE + 1
ID_LOGOUT = ID_BASE + 2
ID_EXIT = ID_BASE + 3
ID_SET = ID_BASE + 4
ID_RANDOM_PART = ID_BASE + 5
ID_GENERATE_BOX = ID_BASE + 6
ID_INPUT_ORDER = ID_BASE + 7

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
area_index = 10
volume_index =11
weight_index = 12
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
box_volume_index = 4
box_weight_index = 5
box_num_index = 6

# 读取电脑自带的字体文件，simsun为黑体-->解决plt上中文乱码问题
simsun = FontProperties(fname=r'C:\Windows\Fonts\simsun.ttc', size=12)
# msyh.ttf字体为下载的微软雅黑字体-->解决plt上中文乱码问题
msyh = matplotlib.font_manager.FontProperties(fname=r'C:\Windows\Fonts\msyh.ttf')
# 极小数，解决分母为0的问题
eps = math.exp(-6)

# C21和N13数据子集名称
C21 = ('C11', 'C12', 'C13', 'C21', 'C22', 'C23', 'C31', 'C32', 'C33',
       'C41', 'C42', 'C43', 'C51', 'C52', 'C53', 'C61', 'C62', 'C63', 'C71', 'C72', 'C73')
N13 = ('N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'N9', 'N10', 'N11', 'N12', 'N13')
