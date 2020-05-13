#!usr/bin/env python3
#coding=utf-8

import re
import random
import threading
from collections import defaultdict
from confs.Setting import *
from MYSQL.MysqlHelper import MysqlPool
import time,wx
from wx.grid import Grid
LAYOUT_WidTH = 1200
LAYOUT_HEIGHT = 600
LAYOUT_GAP = 2

ID_ADD_SERIES = 200
ID_DEL_SERIES = 201
ID_ADD_TYPE = 202
ID_MODIFY_TYPE = 203
ID_DEL_TYPE = 204
ID_EXIT_TYPE = 205
ID_LISTBOX = 206

class PackResultShowDialog(wx.Dialog):
    def __init__(self, parent, id,package_id, solution):
        self.solution = solution[0]
        self.total_layers, self.box_length, self.box_width, self.height, self.part_num = solution[1:]

        super(PackResultShowDialog, self).__init__(parent, id, title=package_id+'布局',
                                                   size=(LAYOUT_WidTH + (self.total_layers-1) * LAYOUT_GAP, LAYOUT_HEIGHT+30)
                                                   )

        self.packPanel = wx.Panel(parent=self, id=-1)
        self.layoutResultShow()

    def preHandle(self):
        if '#' in self.solution:
            solution_lists=self.solution.split('#')
        else:
            solution_lists = [self.solution]
        return solution_lists

    def layoutResultShow(self):
        solution_lists = self.preHandle()
        for perPart in solution_lists:
            prePart_lists = perPart.split('&')
            self._layout(float(prePart_lists[0]), float(prePart_lists[1]), int(prePart_lists[2]),
                         float(prePart_lists[3]), float(prePart_lists[4]), float(prePart_lists[5]),
                         int(prePart_lists[6]), prePart_lists[7])

    def getInitDot(self, z_layer):
        """
        :param z_layer: 当前层数
        :return: 每层的初始点位置
        """
        for i in range(1, self.total_layers+1):
            if i == z_layer:
                initDotX = int((i - 1) * LAYOUT_WidTH / self.total_layers)
                initDotY = 0
                return initDotX, 0
            else:
                continue

    def _layout(self, x_start, y_start, z_layer, part_length, part_width, part_thick, axis, part_id):
        #######################画分割线#####################
        self.packPanel.Bind(wx.EVT_PAINT, self.onPanit)

        if self.total_layers > 8:
            tempSplit = part_id.split('S')
            part_id = tempSplit[0] + '\nS'+tempSplit[1]
            value = '%s\n%s' % (part_id, str(int(part_length)) + '\n*' + str(int(part_width)) + '\n*' + str(int(part_thick)))
            fontsize = 8
        else:
            value = '%s\n%s' % (part_id, str(int(part_length)) + '*' + str(int(part_width)) + '*' + str(int(part_thick)))
            fontsize = 12
        #######################计算比例#####################
        if self.total_layers == 1 or self.total_layers == 2:  # 当层数为1或2时，定义纸箱画板长度方向为屏幕宽度方向
            boxPaintLength = LAYOUT_WidTH
            boxPaintwidth = LAYOUT_HEIGHT/self.total_layers
            reverse = False
        else:# 当层数大于2时，定义纸箱画板长度方向为屏幕高度方向
            boxPaintLength = LAYOUT_HEIGHT
            boxPaintwidth = LAYOUT_WidTH/self.total_layers
            reverse = True
        # if self.box_width > self.box_length:  # 纸箱的实际长度方向与纸箱画板长度方向对齐
        #     self.box_length, self.box_width = self.box_width, self.box_length
        proportionL = boxPaintLength / self.box_length
        proportionW = boxPaintwidth / self.box_width

        ######################绘制布局######################
        if axis == 0 and reverse: # 不旋转：实际纸箱长度方向与部件长度方向对齐
            part_length, part_width = part_width, part_length
            x_start,y_start=y_start,x_start
            # 板件的长边平行于纸箱的长边
            for i in range(1, self.total_layers+1):
                if i == z_layer:
                    initDotX = x_start * proportionW + (i - 1) * LAYOUT_WidTH / self.total_layers
                    initDotY = y_start * proportionL
                    break
                continue
            pos = (initDotX, initDotY)
            size = (proportionW * part_length, proportionL * part_width)
        elif axis == 0 and not reverse:
            for i in range(1, self.total_layers+1):
                if i == z_layer:
                    initDotX = x_start*proportionL + (i - 1) * LAYOUT_WidTH / self.total_layers
                    initDotY = y_start * proportionW
                    break
                continue
            pos = (initDotX, initDotY)
            size = (proportionL * part_length, proportionW * part_width)
        elif axis == 1 and not reverse:
            part_length, part_width = part_width, part_length
            for i in range(1, self.total_layers+1):
                if i == z_layer:
                    initDotX = x_start*proportionL + (i - 1) * LAYOUT_WidTH / self.total_layers
                    initDotY = y_start * proportionW
                    break
                continue
            pos = (initDotX, initDotY)
            size = (proportionL * part_length, proportionW * part_width)
            print(pos, size)
        elif axis == 1 and reverse:
            x_start,y_start = y_start,x_start
            for i in range(1, self.total_layers+1):
                if i == z_layer:
                    initDotX = x_start * proportionW + (i - 1) * LAYOUT_WidTH / self.total_layers
                    initDotY = y_start * proportionL
                    break
                continue
            pos = (initDotX, initDotY)
            size = (proportionW * part_length, proportionL * part_width)


        partBtn = wx.Button(parent=self.packPanel, id=-1, label=value, pos=pos, size=size, style=wx.BU_EXACTFIT)
        partBtn.SetBackgroundColour('green')
        font = wx.Font(pointSize=fontsize, family=wx.FONTFAMILY_ROMAN, style=wx.FONTSTYLE_NORMAL,
                               weight=wx.FONTWEIGHT_BOLD, underline=False)
        partBtn.SetFont(font)

    def onPanit(self, event):  # 层分割线
        dc = wx.PaintDC(window=self.packPanel)
        pen=wx.Pen(colour='Black', width=1, style=wx.PENSTYLE_DOT)
        dc.SetPen(pen)
        for i in range(self.total_layers-1):
            line_x1 = int((i + 1) * LAYOUT_WidTH / self.total_layers)
            line_x2 = int((i+1) * LAYOUT_WidTH/self.total_layers + LAYOUT_GAP)

            dc.DrawLine(line_x1, 0, line_x1,LAYOUT_HEIGHT)
            dc.DrawLine(line_x2, 0, line_x2, LAYOUT_HEIGHT)
        event.Skip()

class PartGeneratorDialog(wx.Dialog):
    def __init__(self, parent,id,log):
        super(PartGeneratorDialog, self).__init__(parent, id, title='板件数据生成器',size=(450, 400))
        self.log=log
        self.mysql = MysqlPool()
        self.createButton()
        self.createText()
        self.order_input_flag = True
        self.section_input_flag = True
        self.part_input_flag = True
        self.range_input_flag = True
    def createButton(self):
        self.OkButton = wx.Button(parent=self, label="确定", pos=(20, 250))
        self.ClearButton = wx.Button(parent=self, label="清空", pos=(170, 250))
        self.CancelButton = wx.Button(parent=self, label="取消", pos=(320, 250))
        self.OkButton.Bind(wx.EVT_BUTTON, self.onOk)
        self.ClearButton.Bind(wx.EVT_BUTTON, self.onClear)
        self.CancelButton.Bind(wx.EVT_BUTTON, self.onCancel)
    def createText(self):
        wx.StaticText(parent=self, label="订单数:", pos=(5, 50))
        wx.StaticText(parent=self, label="组件数:", pos=(5, 100))
        wx.StaticText(parent=self, label="部件数:", pos=(5, 150))

        self.OrderAmountText = wx.TextCtrl(parent=self, pos=(50, 50))
        self.SectionAmountText = wx.TextCtrl(parent=self, pos=(50, 100))
        self.PartAmountText = wx.TextCtrl(parent=self, pos=(50, 150))

        wx.StaticText(parent=self,label="高度范围:", pos=(180, 50))
        self.HeightMinText = wx.TextCtrl(parent=self, pos=(240, 50), size=(50, 22))
        wx.StaticText(parent=self,label="~", pos=(300, 50))
        self.HeightMaxText = wx.TextCtrl(parent=self, pos=(320, 50), size=(50, 22))
        wx.StaticText(parent=self,label="宽度范围:", pos=(180, 100))
        self.WidthMinText = wx.TextCtrl(parent=self,pos=(240, 100), size=(50, 22))
        wx.StaticText(parent=self,label="~", pos=(300, 100))
        self.WidthMaxText = wx.TextCtrl(parent=self, pos=(320, 100), size=(50, 22))
        thick_list = ['18mm', '20mm', '22mm', '25mm']
        wx.StaticText(parent=self,label="基材厚度:", pos=(180, 150))
        self.ThickCombobox = wx.ComboBox(parent=self,value=thick_list[0], pos=(240, 150), size=(130, 50),
                                         choices=thick_list)
    def get_order_amount(self):
        """
        获取需要生成的订单数
        :return: 生成的订单数
        """
        order_num_min = 1
        order_num_max = 110
        if self.OrderAmountText.GetValue().replace(' ', '') == '':  # 没有输入处理
            self.order_input_flag = False
            self.log.write_textctrl_txt('请输入订单数！')
        else:
            if '.' in str(self.OrderAmountText.GetValue().replace(' ', '')):  # 输入小数处理
                self.order_input_flag = False
                self.log.write_textctrl_txt('输入的订单数不合理！')
            else:
                if str(self.OrderAmountText.GetValue().replace(' ', '')).isdigit():  # 判断输入的字符串是否全为数字
                    order_num = int(self.OrderAmountText.GetValue().replace(' ', ''))  # 去除空格并转换成整数
                    if order_num >= order_num_min and order_num <= order_num_max:  # 最大最小值限制，也把输入负数，0的情况进行了处理
                        self.order_input_flag = True
                        return order_num
                    else:
                        self.order_input_flag = False
                        self.log.write_textctrl_txt('输入的订单数不合理！')
                else:
                    self.log.write_textctrl_txt('输入的订单数不合理！')

    def get_section_amount(self):
        """
        获取需要生成一个订单下的组件数
        :return: 生成一个订单下的组件数
        """
        section_num_min = 1
        section_num_max = 10
        if self.SectionAmountText.GetValue().replace(' ', '') == '':  # 没有输入处理
            self.section_input_flag = False
            self.log.write_textctrl_txt('请输入组件数！')
        else:
            if '.' in str(self.SectionAmountText.GetValue().replace(' ', '')):  # 输入小数处理
                self.section_input_flag = False
                self.log.write_textctrl_txt('输入的组件数不合理！')
            else:
                if str(self.SectionAmountText.GetValue().replace(' ', '')).isdigit():
                    section_num = int(self.SectionAmountText.GetValue().replace(' ', ''))  # 去除空格并转换成整数
                    if section_num >= section_num_min and section_num <= section_num_max:  # 最大最小值限制，也把输入负数，0的情况进行了处理
                        self.section_input_flag = True
                        return section_num
                    else:
                        self.section_input_flag = False
                        self.log.write_textctrl_txt('输入的组件数不合理！')
                else:
                    self.log.write_textctrl_txt('输入的组件数不合理！')

    def get_part_amount(self):
        """
        获取需要生成一个组件下的部件数
        :return:获取需要生成一个组件下的部件数
        """
        part_num_min = 1
        part_num_max = 120  # 设置部件数能够输入的最大值为50
        if self.PartAmountText.GetValue().replace(' ', '') == '':  # 没有输入处理
            self.part_input_flag = False
            self.log.write_textctrl_txt('请输入部件数！')
        else:
            if '.' in str(self.PartAmountText.GetValue().replace(' ', '')):  # 输入小数处理
                self.part_input_flag = False
                self.log.write_textctrl_txt('输入的部件数不合理！')
            else:
                if str(self.PartAmountText.GetValue().replace(' ', '')).isdigit():
                    part_num = int(self.PartAmountText.GetValue().replace(' ', ''))  # 去除空格并转换成整数
                    if part_num >= part_num_min and part_num <= part_num_max:  # 最大最小值限制，也把输入负数，0的情况进行了处理
                        self.part_input_flag = True
                        return part_num
                    else:
                        self.part_input_flag = False
                        self.log.write_textctrl_txt('输入的部件数不合理！')
                else:
                    self.log.write_textctrl_txt('输入的部件数不合理！')

    def get_thick(self):
        """
        获取基材厚度
        :return: 基材厚度
        """
        return int(self.ThickCombobox.GetValue().split('mm')[0])

    def get_height_width_range(self):
        """
        从文本框得到高宽的最大值与最小值范围，将min H，max H, min W, max W依次存储到列表height_width_range中
        对输入框的数据合理性进行判断
        :return: 列表height_width_range
        """
        # regInt = '^\d+$'  # 只能匹配1、12、123等只包含数字的字符串
        # regFloat = '^\d+\.\d+$'  # 能匹配2.36、0.36、00069.63、0.0、263.25等
        regIntOrFloat = '^\d+$' + '|' + '^\d+\.\d+$'  # 整数或小数
        height_width_range = []
        height_min = self.HeightMinText.GetValue().replace(' ', '')  # 得到的数据类型为unicode
        height_max = self.HeightMaxText.GetValue().replace(' ', '')
        width_min = self.WidthMinText.GetValue().replace(' ', '')
        width_max = self.WidthMaxText.GetValue().replace(' ', '')
        if height_min == "" or height_max == "" or width_min == "" or width_max == "":
            self.range_input_flag = False
            self.log.write_textctrl_txt('请正确输入生成门板高宽数据的范围！')
        else:
            # 用正则表达式判断输入的范围是否合理，即为整数或者小数
            if re.search(regIntOrFloat, height_min) and re.search(regIntOrFloat, height_max) and re.search(
                    regIntOrFloat, width_min) and re.search(regIntOrFloat, width_max):
                height_min_float = float(height_min)
                height_max_float = float(height_max)
                width_min_float = float(width_min)
                width_max_float = float(width_max)
                if height_min_float <= height_max_float and width_min_float <= width_max_float and height_min_float >= HeightOrWidthMin and height_min_float < HeightOrWidthMax and height_max_float > HeightOrWidthMin and height_max_float <= HeightOrWidthMax and width_min_float >= HeightOrWidthMin and width_min_float < HeightAndWidthLimit and width_max_float > HeightOrWidthMin and width_max_float <= HeightAndWidthLimit:
                    self.range_input_flag = True
                    height_width_range = [height_min_float, height_max_float, width_min_float, width_max_float]
                    return height_width_range
                else:
                    self.range_input_flag = False
                    self.log.write_textctrl_txt('输入的门板的高宽范围数据不合理，请重新输入！')
            else:
                self.range_input_flag = False
                self.log.write_textctrl_txt('输入的门板的高宽范围数据不合理，请重新输入！')

    def onOk(self, event):
        order_num = self.get_order_amount()
        section_num = self.get_section_amount()
        part_num = self.get_part_amount()
        thick = self.get_thick()
        height_width_range = self.get_height_width_range()
        if order_num == "" or section_num == "" or part_num == "" or height_width_range == [] or thick == "":
            self.log.write_textctrl_txt('您未输入或选择好数据')
        else:
            if self.order_input_flag and self.section_input_flag and self.part_input_flag and self.range_input_flag:
                # 实例化ID类
                id = ID(order_num, section_num, part_num)
                part_id = id.get_part_id()
                # 实例化CreateData类
                create_data = CreateData(order_num, section_num, part_num, height_width_range, thick)
                Door_Size = create_data.create_door_data()

                # IO数据操作密集型，使用线程操作
                myThread1=threading.Thread(target=self.writeInfo,args=(Door_Size, part_id, order_num, section_num, part_num, thick,))
                myThread1.start()
                myThread2 = threading.Thread(target=self.showInfo, args=(Door_Size, part_id,))
                myThread2.start()
        event.Skip()
    def onClear(self, event):
        self.OrderAmountText.Clear()
        self.SectionAmountText.Clear()
        self.PartAmountText.Clear()
        self.HeightMaxText.Clear()
        self.HeightMinText.Clear()
        self.WidthMaxText.Clear()
        self.WidthMinText.Clear()
        event.Skip()
    def onCancel(self, event):
        self.Close()
        event.Skip()
    def writeInfo(self,door_info, part_id, order_num, section_num, part_num, thick):
        order_id = []
        section_id = []
        sql="SELECT `Index` FROM `order_contract_internal` WHERE 1  ORDER BY `Index` DESC  LIMIT 1"
        res=self.mysql.do_sql_one(sql)
        if res is None:
            contract_id = 0
        else:
            contract_id = res[0]
        contract_id += 1

        # 存数据到合同表单
        sql = "INSERT INTO `order_contract_internal`(`Contract_id`, `Contract_C_Time`, `Order_num`, `Sec_num`, `Part_num`, `State`) VALUES ('%s', '%s', '%s', '%s', '%s', '%s')" % (
                    str(contract_id), time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time())), order_num,
                    section_num * order_num, part_num * section_num * order_num, 0)
        self.mysql.insert(sql)

        # 存数据到部件表单
        for i in range(len(part_id)):
            section_id.append(part_id[i].split('P')[0])
            section_id = sorted(set(section_id), key=section_id.index)
            order_id.append(part_id[i].split('P')[0].split('S')[0])
            order_id = sorted(set(order_id), key=order_id.index)
            sql = "INSERT INTO `order_part_online`(`Contract_id`, `Order_id`, `Sec_id`, `Part_id`, `Door_type`, `Door_height`, `Door_width`, `Door_thick`, `Package_state`) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
                  (contract_id, part_id[i].split('P')[0].split('S')[0], part_id[i].split('P')[0], part_id[i],
                   door_info[0][i], door_info[1][i], door_info[2][i], door_info[3][i], 0)
            self.mysql.insert(sql)
        # 存数据到零件表单
        for i in range(len(part_id)):
            section_id.append(part_id[i].split('P')[0])
            section_id = sorted(set(section_id), key=section_id.index)
            order_id.append(part_id[i].split('P')[0].split('S')[0])
            order_id = sorted(set(order_id), key=order_id.index)
            sql = "INSERT INTO `order_element_online`(`Contract_id`, `Order_id`, `Sec_id`, `Part_id`, `Board_type`, `Board_height`, `Board_width`, `Board_thick`) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % \
                  (contract_id, part_id[i].split('P')[0].split('S')[0], part_id[i].split('P')[0], part_id[i],
                   door_info[0][i], door_info[1][i], door_info[2][i], door_info[3][i])
            self.mysql.insert(sql)
        # 存数据到订单表单
        for i in range(order_num):
            sql="INSERT INTO `order_order_online`(`Order_id`, `Sec_num`, `Part_num`) VALUES ('%s', '%s', '%s')" % \
                (order_id[i], section_num, part_num * section_num)
            self.mysql.insert(sql)
        # 存数据到组件表单
        for i in range(section_num * order_num):
            sql = "INSERT INTO `order_section_online`(`Order_id`, `Sec_id`, `Part_num`, `Package_state`) VALUES ('%s', '%s', '%s', '%s')" % \
                  (section_id[i].split('S')[0], section_id[i], part_num, 0)
            self.mysql.insert(sql)
    def showInfo(self, door_info, part_id):
        for i in range(len(door_info[1])):
            output_str1 = str(
                "门型：" + str(door_info[0][i]) + " , " + "门板长度：" + str(door_info[1][i]) + " , " +
                "门板宽度：" + str(door_info[2][i]) + " , " + "门板厚度：" + str(door_info[3][i]))
            output_str2 = " , " + "部件号：" + part_id[i] + " , " + "所属组件号：" + part_id[i].split('P')[0] + " , " \
                          + "所属订单号：" + part_id[i].split('P')[0].split('S')[0]
            self.log.write_textctrl_txt(output_str1 + output_str2)
        self.log.write_textctrl_txt(str("订单部件数：" + str(len(door_info[0]))))

class CreateData:
    def __init__(self, Order_amount, OneOrder_Section_amount, OneSection_Part_amount, height_width_range, thick):
        self.Order_amount = Order_amount
        self.OneOrder_Section_amount = OneOrder_Section_amount
        self.OneSection_Part_amount = OneSection_Part_amount
        self.height_width_range = height_width_range
        # self.Data_Type = Data_Type
        self.thick = thick

    def create_door_type(self):  # 随机生成MY_1701-MY_1794的94款门型
        door_type_amount = 94
        i = random.randint(1, door_type_amount)
        if i < 10:
            door_type = "MY_170" + str(i) + "_橱柜门"
        else:
            door_type = "MY_17" + str(i) + "_橱柜门"
        return door_type

    def create_door_data(self):
        """
        随机生成门板数据函数
        :return: Door_Part_Size[0]存门型，Door_Part_Size[1]存高度，Door_Part_Size[2]存宽度，Door_Part_Size[3]存厚度
        """
        Part_amount = self.OneSection_Part_amount*self.OneOrder_Section_amount*self.Order_amount  # 需要生成的总部件数
        Door_Part_Height = []
        Door_Part_Width = []
        Door_Part_Thick = []
        Door_Type = []
        Door_Type_Value = self.create_door_type()
        same_size_list = self.create_same_size_part(Part_amount)

        for i in range(same_size_list[1]):
            same_int = random.randint(0, 1)  # 加了随机生成相同尺寸的和不同尺寸的
            if same_int == 0:
                RandomHeight = round(random.uniform(self.height_width_range[0], self.height_width_range[1]))
                RandomWidth = round(random.uniform(self.height_width_range[2], self.height_width_range[3]))
            # RandomHeight = round(random.uniform(self.height_width_range[0], self.height_width_range[1]))
            # RandomWidth = round(random.uniform(self.height_width_range[2], self.height_width_range[3]))
            for j in range(same_size_list[0]):
                Door_Type.append(Door_Type_Value)
                if same_int == 1:
                    RandomHeight = round(random.uniform(self.height_width_range[0], self.height_width_range[1]))
                    RandomWidth = round(random.uniform(self.height_width_range[2], self.height_width_range[3]))
                HorW= random.randint(0, 1)  # 随机分配高宽
                if HorW == 0:
                    H = RandomHeight
                    W = RandomWidth
                else:
                    H = RandomWidth
                    W = RandomHeight
                Door_Part_Height.append(H)
                Door_Part_Width.append(W)
                Door_Part_Thick.append(self.thick)
        Door_Part_Size = [Door_Type, Door_Part_Height, Door_Part_Width, Door_Part_Thick]
        return Door_Part_Size

    def create_same_size_part(self, part_num):
        """
        随机生成尺寸相同的门板数据
        得到的prime_list为质数因子，并添加了一个1，如12=[1,2,2,3]
        :param part_num: 部件总数
        :return: part_num = same_size_num * remain_num，其中same_size_num是随机的，算法：将一个整数分解成多个质数相乘
        """
        part_num_store = part_num
        prime_list = [1]
        if not isinstance(part_num, int) or part_num <= 0:
            exit(0)
        elif part_num in [1]:
            prime_list = [1]
        while part_num not in [1]:  # 循环保证递归
            for index in range(2, part_num + 1):
                if part_num % index == 0:
                    part_num //= index  # let n equal to it n/index
                    if part_num == 1:  # This is the point
                        prime_list.append(index)
                    else:  # index 一定是素数
                        prime_list.append(index)
                    break
        # 优化生成相同尺寸算法，使其相同尺寸的门板块数可以达到1-12任意整数值
        same_size_num = 1
        for i in range(len(prime_list)):
            if random.randint(1, 12) > 6:
                continue
            else:
                same_size_num = same_size_num * prime_list[i]
        if same_size_num > 12:
            range_index = random.randint(1, len(prime_list))  # 随机生成1-len(prime_list)的整数，包括0与len(prime_list)
            same_size_num = prime_list[range_index - 1]
        remain_num = part_num_store // same_size_num
        return [same_size_num, remain_num]

class ID:
    """
    生成合同、订单、组件、部件的ID类
    协议：例如4O2S1P3表示部件号，其中O前面的4为合同id，O后面的2为订单id,S后面的1为组件id,P后面的3为部件id
    """
    def __init__(self, order_num, section_num, part_num):
        self.order_num = order_num
        self.section_num = section_num
        self.part_num = part_num
        self.mysql=MysqlPool()

    def get_contract_id(self):
        sql="SELECT `Index` FROM `order_contract_internal` WHERE 1  ORDER BY `Index` DESC  LIMIT 1"
        contract_id_tuple=self.mysql.do_sql_one(sql)
        if contract_id_tuple is None:
            contract_id = 0
        else:
            contract_id = contract_id_tuple[0]
        contract_id += 1
        return contract_id

    def get_order_id(self):
        global order_id_num  # 存储当前的订单数
        order_id_num = self.order_num
        order_id = []
        c_id = self.get_contract_id()
        for i in range(order_id_num):
            order_id.append(str(c_id) + "O" + str(i + 1))
        return order_id

    def get_section_id(self):
        global section_id_num
        section_id_num = self.section_num
        section_id = []
        o_id = self.get_order_id()
        for i in range(len(o_id)):
            for j in range(section_id_num):
                section_id.append(o_id[i] + "S" + str(j + 1))
        return section_id

    def get_part_id(self):
        global part_id_num
        part_id_num = self.part_num
        part_id = []
        s_id = self.get_section_id()
        for i in range(len(s_id)):
            for j in range(part_id_num):
                part_id.append(s_id[i] + "P" + str(j + 1))
        return part_id

class BoxGeneratorDialog(wx.Dialog):
    def __init__(self, parent,id,log):
        super(BoxGeneratorDialog, self).__init__(parent, id, title='纸箱数据生成器',size=(500, 400))
        self.log = log
        self.mysql=MysqlPool()
        wx.StaticText(parent=self,label='长  度：',pos=(50, 50))
        wx.StaticText(parent=self,label='宽  度：',pos=(50, 100))
        wx.StaticText(parent=self, label='高  度：', pos=(50, 150))

        self.lengthList = ['650', '800', '950', '1100', '1200', '1400', '1600', '1800', '2050', '2300', '2436']
        self.widthList = ['450', '600', '750', '900', '1050', '1200']
        self.lengthCombo=wx.ComboBox(parent=self,value=self.lengthList[0],pos=(100, 50),size=(110,30),choices=self.lengthList)
        self.widthCombo = wx.ComboBox(parent=self, value=self.widthList[0], pos=(100, 100), size=(110,30), choices=self.widthList)
        self.heightText=wx.TextCtrl(parent=self,pos=(100,150))
        self.heightCheck=wx.CheckBox(parent=self,label='高度是否手动产生？',pos=(250,150))
        self.heightText.Enable(False)
        self.heightCheck.Bind(wx.EVT_CHECKBOX,self.isAutoHeight)
        okBtn=wx.Button(parent=self, label='确定', pos=(25, 250))
        cancelBtn = wx.Button(parent=self, label='取消', pos=(190, 250))
        autoBtn = wx.Button(parent=self, label='自动', pos=(355, 250))
        okBtn.Bind(wx.EVT_BUTTON, self.onOk)
        cancelBtn.Bind(wx.EVT_BUTTON, self.onCancel)
        autoBtn.Bind(wx.EVT_BUTTON, self.onAuto)
    def isAutoHeight(self, event):
        if self.heightCheck.GetValue():
            self.heightText.Enable(True)
        else:
            self.heightText.Enable(False)
            self.heightText.Clear() # 清零
        event.Skip()
    def onOk(self,event):
        length=int(self.lengthCombo.GetValue())
        width = int(self.widthCombo.GetValue())
        if self.heightCheck.IsChecked():#复选框选中
            if self.heightText.GetValue() != '':
                height = int(self.heightText.GetValue())
            else:
                height = None
                self.log.write_textctrl_txt('please input the box height correctly.')
        else:#复选框没有选中
            height = int(round(60 * (10 ** 9) / (length * width * BaseMaterialDensity)))
        if height is not None:
            volume = round(length * width * height * 10 ** (-3), 6)#体积单位：立方厘米
            weight = OnePackageMaxWeight
            sql = "INSERT INTO `equipment_package_box` (`Box_type`, `Box_long`, `Box_short`, `Box_height`, `Box_volume`,`Box_weight`,`Box_num`,`State`) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (
                'BT' + str(length) + 'X' + str(width), length, width, height, volume,weight,1,5)
            self.mysql.insert(sql)
            self.log.write_textctrl_txt('the box size is ({},{},{}).'.format(length, width, height))
        event.Skip()
    def onCancel(self,event):
        self.Close()
        event.Skip()
    def onAuto(self,event):
        lenList=[int(l) for l in self.lengthList]
        widList = [int(w) for w in self.widthList]

        # 此处操作的IO数据较多，使用线程的方式，保证IO操作时，界面不卡顿
        myThread = threading.Thread(target=self.writeInfo,args=(lenList,widList,))
        myThread.start()
        event.Skip()
    def writeInfo(self, lenList, widList):
        for i in range(len(widList)):
            series = '系列' + str(i + 1)
            for j in range(len(lenList)):
                height = int(round(60 * (10 ** 9) / (lenList[j] * widList[i] * BaseMaterialDensity)))
                volume= round(lenList[j]*widList[i]*height*10**(-3),6)#体积单位：立方厘米
                weight = OnePackageMaxWeight
                sql = "INSERT INTO `equipment_package_box` (`Box_type`, `Box_long`, `Box_short`, `Box_height`, `Box_volume`,`Box_weight`,`Box_num`,`Box_series`,`State`) VALUES ('%s', '%s', '%s', '%s', '%s','%s', '%s', '%s', '%s')" % (
                    'BT' + str(lenList[j]) + 'X' + str(widList[i]), lenList[j], widList[i], height, volume,weight,1,series,5)
                self.mysql.insert(sql)
                self.log.write_textctrl_txt('the box size is ({},{},{}).'.format(lenList[j], widList[i], height))

class BoxGeneratorDialog2(wx.Dialog):
    def __init__(self, parent,id,log):
        super(BoxGeneratorDialog2, self).__init__(parent, id, title='纸箱数据生成器',size=(480, 450))
        self.log = log
        self.mysql=MysqlPool()
        self.panel = wx.Panel(parent=self)

        self.boxSeries=self.getSeries()
        wx.StaticText(parent=self.panel, label='系   列：', pos=(20, 12)).SetFont(self.setFont(9))
        self.seriesCombo = wx.ComboBox(parent=self.panel, value=self.boxSeries[0], pos=(90, 15), size=(110, 30),
                                      choices=self.boxSeries)
        newSeriesBtn = wx.Button(parent=self.panel, label='添加系列', pos=(260, 15))
        delSeriesBtn = wx.Button(parent=self.panel, label='删除系列', pos=(360, 15))

        if len(self.boxSeries[0]) == 0:
            self.typeList = []
        else:
            self.typeList = self.getType(self.seriesCombo.GetValue())
        wx.StaticText(parent=self.panel, label='纸箱类型：', pos=(20, 50)).SetFont(self.setFont(9))

        self.listBox=wx.ListBox(parent=self.panel,id=ID_LISTBOX,pos=(20,70),size=(320,300),choices=self.typeList,style=wx.LB_EXTENDED)
        self.Bind(wx.EVT_LISTBOX, self.EvtMultiListBox, self.listBox)

        newTypeBtn=wx.Button(parent=self.panel, id=ID_ADD_TYPE, label='添加类型', pos=(360, 170))
        modifyTypeBtn = wx.Button(parent=self.panel, id=ID_MODIFY_TYPE, label='修改类型', pos=(360, 220))
        delTypeBtn=wx.Button(parent=self.panel, id=ID_DEL_TYPE, label='删除类型', pos=(360, 270))
        exitBtn =wx.Button(parent=self.panel, id=ID_EXIT_TYPE, label='退出', pos=(360, 320))

        self.seriesCombo.Bind(wx.EVT_TEXT,self.onSeries)

        newSeriesBtn.Bind(wx.EVT_BUTTON, self.onNewSeries)
        delSeriesBtn.Bind(wx.EVT_BUTTON, self.onDelSeries)
        newTypeBtn.Bind(wx.EVT_BUTTON, self.onNewType)
        modifyTypeBtn.Bind(wx.EVT_BUTTON, self.onModify)
        delTypeBtn.Bind(wx.EVT_BUTTON, self.onDelType)
        exitBtn.Bind(wx.EVT_BUTTON, self.onExit)

    def onSeries(self, event):
        self.typeList = self.getType(self.seriesCombo.GetValue())
        self.listBox.Set(self.typeList)  # 更新显示内容
        event.Skip()


    def getType(self, curSeries):
        boxList = []
        sql = "SELECT `Box_type`,`Box_long`,`Box_short`,`Box_series` FROM `equipment_package_box` WHERE " \
              "`Box_series`='%s'" % curSeries
        box_info = self.mysql.do_sql(sql)
        if box_info is None:  # 一个系列没有返回[]显示
            return []
        else:
            for i in range(len(box_info)):
                item = box_info[i][0]
                if item is None:
                    boxList.append('')
                else:
                    boxList.append(item)
            return boxList

    def getSeries(self):
        sql = "SELECT DISTINCT `Box_series` FROM `equipment_package_box` WHERE " \
              "`State`=5"  # DISTINCT用于字段重复数据去重
        box_info = self.mysql.do_sql(sql)
        if box_info is None:  # 一个系列没有返回['']显示,''用于显示初始下拉框
            return []
        else:
            return [box_info[i][0] for i in range(len(box_info))]

    # def onOk(self,event):
    #     curSelect = self.checkListBox.GetCheckedStrings()
    #     curSelect = list(curSelect)
    #     if len(curSelect) == 0:
    #         self.log.write_textctrl_txt('没有需要产生的纸箱，否则请选中.')
    #     else:
    #         for i, v in enumerate(curSelect):
    #             boxType= v
    #             length=int(v.split('X')[0].split('BT')[-1])
    #             width = int(v.split('X')[1])
    #             sql="INSERT INTO `equipment_package_box` (`Box_type`,`Box_long`,`Box_short`) VALUES ('%s','%s','%s')" % \
    #               (boxType, length, width)
    #             self.mysql.insert(sql)
    #             self.log.write_textctrl_txt('the box size is ({},{}).'.format(length, width))
    #     event.Skip()

    def onNewSeries(self ,event):
        newSeriesDialog = NewSeriesDialog(parent=None, id=-1, log=self.log)
        newSeriesDialog.ShowModal()
        if (newSeriesDialog.newSeries != "" or newSeriesDialog.newSeries is not None) and newSeriesDialog.newSeries not in newSeriesDialog.oldSeries:
            self.boxSeries = self.getSeries()
            self.seriesCombo.Set(self.boxSeries)  # 更新显示
            self.seriesCombo.SetStringSelection(self.boxSeries[0])
        newSeriesDialog.Destroy()
        event.Skip()

    def onDelSeries(self ,event):
        curSeries = self.seriesCombo.GetValue()  # 获取移除的系列
        if len(curSeries) !=0:
            self.boxSeries.remove(curSeries)  # 内存移除
            self.seriesCombo.Set(self.boxSeries)  # 更新系列显示
            self.log.write_textctrl_txt('成功删除%s及所属的纸箱信息.' % curSeries)
            self.seriesCombo.SetStringSelection(self.boxSeries[0])  # 设置选中系列

            self.typeList = self.getType(self.seriesCombo.GetValue())  # 更新选中系列表格显示
            self.listBox.Set(self.typeList)  # 更新显示内容
            sql = "DELETE FROM `equipment_package_box` WHERE  `Box_series`='%s'" % curSeries
            self.mysql.upda_sql(sql)  # 从数据库移除系列

        event.Skip()

    def onNewType(self,event):
        curSeries = self.seriesCombo.GetValue()
        newTypeDialog = NewTypeDialog(parent=None, id=-1, log=self.log, curSeries=curSeries)
        newTypeDialog.ShowModal()
        if newTypeDialog.boxType is not None:
            newType = newTypeDialog.boxType
            newLen, newWidth = newTypeDialog.boxSize[0], newTypeDialog.boxSize[1]
            self.typeList = self.getType(self.seriesCombo.GetValue())  # 更新选中系列表格显示
            if len(self.typeList) == 1 and self.typeList[0] == '':
                self.typeList.remove('')
                sql = "UPDATE `equipment_package_box` SET `Box_type`='%s',`Box_long`='%s',`Box_short`='%s',`State`='%s' WHERE  `Box_series`='%s';" % \
                      (newType, newLen, newWidth, 5, curSeries)
            else:
                sql = "INSERT INTO `equipment_package_box` (`Box_type`,`Box_long`,`Box_short`,`Box_series`,`State`) VALUES ('%s','%s','%s','%s','%s')" % \
                  (newType, newLen, newWidth, curSeries, 5)
            self.mysql.upda_sql(sql)
            self.typeList.append(newType)


            self.listBox.Set(self.typeList)  # 更新显示内容
        else:
            self.log.write_textctrl_txt('没有正确输入长度和宽度.')
        newTypeDialog.Destroy()
        event.Skip()

    def onDelType(self,event):
        selections = list(self.listBox.GetSelections())  # 获取选中删除列表
        if len(selections) >= 1:
            selections.reverse()
            for index in selections:
                self.listBox.Delete(index)

            selElement = []
            curSeries=self.seriesCombo.GetValue()
            for v in selections:
                selElement.append(self.typeList[v])
            for value in selElement:
                self.typeList.remove(value)
                self.log.write_textctrl_txt('成功删除%s下的%s类型纸箱.' % (curSeries, value))
                sql = "DELETE FROM `equipment_package_box` WHERE  `Box_series`='%s' and `Box_type` = '%s'" % (
                    curSeries, value)
                self.mysql.upda_sql(sql)
            if len(self.typeList) == 0:  # 当系列下面纸箱删除没有时，将系列删除
                self.boxSeries.remove(curSeries)
                self.seriesCombo.Set(self.boxSeries)
                self.seriesCombo.SetStringSelection(self.boxSeries[0])  # 设置选中系列

                self.typeList = self.getType(self.seriesCombo.GetValue())  # 更新选中系列表格显示
                self.listBox.Set(self.typeList)  # 更新显示内容
        else:
            self.log.write_textctrl_txt('请选中需删除的纸箱.')
        event.Skip()

    def onModify(self, event):
        selections = list(self.listBox.GetSelections())  # 获取需修改的列表
        if len(selections) == 1:
            modifyElement = self.typeList[selections[0]]
            curSeries = self.seriesCombo.GetValue()
            modifyTypeDialog = NewTypeDialog(parent=None, id=-1, log=self.log, curSeries=curSeries,mode=True,boxInfo=modifyElement)
            modifyTypeDialog.ShowModal()
            if modifyTypeDialog.boxType is not None:
                newType = modifyTypeDialog.boxType
                newLen, newWidth = modifyTypeDialog.boxSize[0], modifyTypeDialog.boxSize[1]


                sql = "UPDATE `equipment_package_box` SET `Box_type`='%s',`Box_long`='%s',`Box_short`='%s',`State`='%s' WHERE  `Box_type`='%s';" % \
                      (newType,newLen, newWidth, 5, modifyElement)
                self.mysql.upda_sql(sql)

                self.typeList = self.getType(self.seriesCombo.GetValue())  # 更新选中系列表格显示
                self.listBox.Set(self.typeList)  # 更新显示内容
            else:
                self.log.write_textctrl_txt('没有正确输入长度和宽度.')
            modifyTypeDialog.Destroy()
        elif len(selections) == 0:
            self.log.write_textctrl_txt('请选中一种纸箱修改.')
        else:
            self.log.write_textctrl_txt('只能选中一种纸箱修改.')
        event.Skip()

    def onExit(self,event):
        self.Close()
        event.Skip()

    def EvtMultiListBox(self, event):
        self.listBox.GetSelections()
        event.Skip()

    def setFont(self,size):
        font = wx.Font(size, wx.ROMAN, wx.NORMAL, wx.BOLD, underline=False)
        return font

class BoxGeneratorDialog3(wx.Dialog):
    def __init__(self, parent,id, log):
        super(BoxGeneratorDialog3, self).__init__(parent, id, title='纸箱数据生成器',size=(480, 450),
                                                  style=wx.DEFAULT_DIALOG_STYLE & (~wx.RESIZE_BORDER))
        self.log = log
        self.mysql=MysqlPool()
        self.panel = wx.Panel(parent=self)

        self.boxSeries=self.getSeries()
        wx.StaticText(parent=self.panel, label='系   列：', pos=(20, 12)).SetFont(self.setFont(9))
        self.seriesCombo = wx.ComboBox(parent=self.panel, value=self.boxSeries[0], pos=(90, 15), size=(110, 30),
                                      choices=self.boxSeries)
        wx.Button(parent=self.panel, id=ID_ADD_SERIES, label='添加系列', pos=(260, 15))
        wx.Button(parent=self.panel, id=ID_DEL_SERIES, label='删除系列', pos=(360, 15))

        if len(self.boxSeries[0]) == 0:
            self.typeList = []
        else:
            self.typeList = self.getType(self.seriesCombo.GetValue())
        wx.StaticText(parent=self.panel, label='纸箱信息：', pos=(20, 50)).SetFont(self.setFont(9))

        # 创建表，并设置表头
        self.boxGrid = Grid(parent=self.panel, pos=(20, 70), size=(320, 300))
        self.boxGrid.CreateGrid(numRows=len(self.typeList), numCols=4, selmode=Grid.SelectRows)
        colHeaders = ['类型', '长度(mm)', '宽度(mm)', '系列']
        for i, colHeader in enumerate(colHeaders):
            self.boxGrid.SetColLabelValue(col=i, value=colHeader)
        # rowHeaders = [str(i+1) for i in range(len(self.typeList))]
        # for j, rowHeader in enumerate(rowHeaders):
        #     self.boxGrid.SetRowLabelValue(row=j, value=rowHeader)
        self.boxGrid.SetRowLabelSize(0)  # 行头不需要
        self.update()

        wx.Button(parent=self.panel, id=ID_ADD_TYPE,label='添加类型', pos=(360, 170))
        wx.Button(parent=self.panel, id=ID_MODIFY_TYPE,label='修改类型', pos=(360, 220))
        wx.Button(parent=self.panel, id=ID_DEL_TYPE,label='删除类型', pos=(360, 270))
        wx.Button(parent=self.panel, id=ID_EXIT_TYPE,label='退出', pos=(360, 320))

        self.seriesCombo.Bind(wx.EVT_TEXT,self.onSeries)
        # self.boxGrid.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.onCellLeftClick)

        # 使用一个处理器，多个事件ID处理响应事件
        self.Bind(wx.EVT_BUTTON, self.onClick, id=ID_ADD_SERIES)
        self.Bind(wx.EVT_BUTTON, self.onClick, id=ID_DEL_SERIES)
        self.Bind(wx.EVT_BUTTON, self.onClick, id=ID_ADD_TYPE)
        self.Bind(wx.EVT_BUTTON, self.onClick, id=ID_MODIFY_TYPE)
        self.Bind(wx.EVT_BUTTON, self.onClick, id=ID_DEL_TYPE)
        self.Bind(wx.EVT_BUTTON, self.onClick, id=ID_EXIT_TYPE)

    def onCellLeftClick(self, event):
        self.log.write_textctrl_txt(event.GetRow(), event.GetCol(), event.GetPosition())
        event.Skip()

    def update(self):

        for j, row in enumerate(self.typeList):
            for k, col in enumerate(row):
                if col is None or col == 0:
                    col = ""
                self.boxGrid.SetCellValue(j, k, str(col))
                self.boxGrid.SetCellAlignment(wx.ALIGN_CENTER,j,k)
                self.boxGrid.SetReadOnly(j, k)

    def onSeries(self, event):  # 系列选择改变事件
        self.typeList = self.getType(self.seriesCombo.GetValue())
        self.boxGrid.ClearGrid()
        # self.boxGrid.ForceRefresh()
        self.update()  # 更新显示内容
        event.Skip()

    def getType(self, curSeries):
        boxList = []
        sql = "SELECT `Box_type`,`Box_long`,`Box_short`,`Box_series` FROM `equipment_package_box` WHERE " \
              "`Box_series`='%s'" % curSeries
        box_info = self.mysql.do_sql(sql)
        if box_info is None:  # 一个系列没有返回[]显示
            return []
        else:
            for i in range(len(box_info)):
                boxList.append([box_info[i][0],box_info[i][1],box_info[i][2],box_info[i][3]])
            return boxList

    def getSeries(self):
        sql = "SELECT DISTINCT `Box_series` FROM `equipment_package_box` WHERE " \
              "`State`=5"  # DISTINCT用于字段重复数据去重
        box_info = self.mysql.do_sql(sql)
        if box_info is None:  # 一个系列没有返回['']显示,''用于显示初始下拉框
            return ['']
        else:
            return [box_info[i][0] for i in range(len(box_info))]

    def onClick(self, event):
        if event.GetEventObject().GetId() == ID_ADD_SERIES:
            newSeriesDialog = NewSeriesDialog(parent=None, id=-1, log=self.log)
            newSeriesDialog.ShowModal()
            if (newSeriesDialog.newSeries != "" or newSeriesDialog.newSeries is not None) and newSeriesDialog.newSeries not in newSeriesDialog.oldSeries:
                self.boxSeries = self.getSeries()
                self.seriesCombo.Set(self.boxSeries)  # 更新显示
                self.seriesCombo.SetStringSelection(self.boxSeries[0])
            newSeriesDialog.Destroy()
        elif event.GetEventObject().GetId() == ID_DEL_SERIES:
            curSeries = self.seriesCombo.GetValue()  # 获取移除的系列
            self.boxSeries.remove(curSeries)  # 内存移除
            self.boxGrid.ClearGrid()  # 清空该系列下的纸箱显示
            self.seriesCombo.Set(self.boxSeries)  # 更新系列显示
            self.seriesCombo.SetStringSelection(self.boxSeries[0])  # 设置选中系列
            self.typeList = self.getType(self.seriesCombo.GetValue())  # 更新选中系列表格显示
            self.update()  # 更新显示内容
            sql = "DELETE FROM `equipment_package_box` WHERE  `Box_series`='%s'" % curSeries
            self.mysql.upda_sql(sql)  # 从数据库移除系列
        elif event.GetEventObject().GetId() == ID_ADD_TYPE:
            curSeries=self.seriesCombo.GetValue()
            newTypeDialog = NewTypeDialog(parent=None, id=-1, log=self.log, curSeries=curSeries)
            newTypeDialog.ShowModal()
            if newTypeDialog.boxType is not None:
                newType = newTypeDialog.boxType
                newLen,newWidth=newTypeDialog.boxSize[0],newTypeDialog.boxSize[1]

                sql = "INSERT INTO `equipment_package_box` (`Box_type`,`Box_long`,`Box_short`,`Box_series`,`State`) VALUES ('%s','%s','%s','%s','%s')" % \
                      (newType, newLen, newWidth, curSeries, 5)
                self.mysql.upda_sql(sql)
                self.typeList.append(newType)

                self.typeList = self.getType(self.seriesCombo.GetValue())  # 更新选中系列表格显示
                self.update()  # 更新显示内容
            else:
                self.log.write_textctrl_txt('没有正确输入长度和宽度.')
            newTypeDialog.Destroy()

        elif event.GetEventObject().GetId() == ID_MODIFY_TYPE:
            pass
        elif event.GetEventObject().GetId() == ID_DEL_TYPE:
            if self.boxGrid.GetNumberRows() < 1:
                self.log.write_textctrl_txt('没有纸箱需要删除.')
            else:
                self.selRows = self.boxGrid.GetSelectedRows()
                if len(self.selRows) < 1:
                    self.log.write_textctrl_txt('请选中需删除的纸箱.')
                else:
                    self.selElement=[]
                    for v in self.selRows:
                        self.selElement.append(self.typeList[v])
                    for value in self.selElement:
                        sql = "DELETE FROM `equipment_package_box` WHERE  `Box_series`='%s' and `Box_type` = '%s'" % (value[-1],value[0])
                        self.mysql.upda_sql(sql)
                        self.typeList.remove(value)

                    self.typeList = self.getType(self.seriesCombo.GetValue())
                    self.update()
        elif event.GetEventObject().GetId() == ID_EXIT_TYPE:
            self.Close()
        else:
            self.log.write_textctrl_txt('没有需要响应的事件.')
        event.Skip()

    def setFont(self,size):
        font = wx.Font(size, wx.ROMAN, wx.NORMAL, wx.BOLD, underline=False)
        return font

class NewSeriesDialog(wx.Dialog):
    def __init__(self, parent,id, log):
        super(NewSeriesDialog, self).__init__(parent, id, title='添加新系列',size=(300, 170))
        self.log = log
        self.mysql=MysqlPool()
        self.newSeries = None
        self.oldSeries = []

        wx.StaticText(parent=self, label='系列名称：', pos=(20, 15))
        self.seriesText = wx.TextCtrl(parent=self, pos=(100, 15))
        okBtn = wx.Button(parent=self, label='确定', pos=(30, 75))
        cancelBtn = wx.Button(parent=self, label='退出', pos=(150, 75))
        okBtn.Bind(wx.EVT_BUTTON, self.onOk)
        cancelBtn.Bind(wx.EVT_BUTTON, self.onCancel)

    def onOk(self,event):
        self.newSeries = self.seriesText.GetValue()
        self.oldSeries = self.getSeries()
        if (self.newSeries != "" or self.newSeries is not None) and self.newSeries not in self.oldSeries:
            sql = "INSERT INTO `equipment_package_box` (`Box_series`,`State`) VALUES ('%s','%s');" % (self.newSeries,5)
            self.mysql.upda_sql(sql)
            self.log.write_textctrl_txt('成功添加新纸箱系列：%s.' % self.newSeries)
        elif self.newSeries in self.oldSeries:
            self.log.write_textctrl_txt('纸箱系列：%s已存在，不是新系列.' % self.newSeries)
        else:
            pass
        # self.Close()#按确定之后退出
        event.Skip()
    def onCancel(self,event):
        self.Close()
        event.Skip()

    def getSeries(self):
        sql = "SELECT DISTINCT `Box_series` FROM `equipment_package_box` WHERE " \
              "`State`=5"  # DISTINCT用于字段重复数据去重
        box_info = self.mysql.do_sql(sql)
        if box_info is None:  # 一个系列没有返回['']显示,''用于显示初始下拉框
            return ['']
        else:
            return [box_info[i][0] for i in range(len(box_info))]

class NewTypeDialog(wx.Dialog):
    def __init__(self, parent,id,log,curSeries, mode=False,boxInfo=None):
        if mode and boxInfo is not None:
            super(NewTypeDialog, self).__init__(parent, id, title='修改%s类型纸箱尺寸' % boxInfo, size=(430, 140))
            self.boxSize = [str(boxInfo.split('X')[0].split('T')[-1]), str(boxInfo.split('X')[1])]
            self.boxType = boxInfo
        else:
            super(NewTypeDialog, self).__init__(parent, id, title='%s添加新类型纸箱尺寸'% curSeries,size=(430, 140))
            self.boxSize = [0, 0]
            self.boxType = None
        self.log = log
        self.mode=mode
        self.boxInfo=boxInfo

        self.curSeries=curSeries

        wx.StaticText(parent=self, label='长度(mm)：', pos=(10, 15))
        wx.StaticText(parent=self, label='宽度(mm)：', pos=(210, 15))
        self.lenText=wx.TextCtrl(parent=self,pos=(80,15))
        self.widthText = wx.TextCtrl(parent=self, pos=(280, 15))

        if mode and boxInfo is not None:
            self.lenText.SetValue(self.boxSize[0])
            self.widthText.SetValue(self.boxSize[1])
        okBtn = wx.Button(parent=self, label='确定', pos=(40, 60))
        cancelBtn = wx.Button(parent=self, label='退出', pos=(250, 60))
        okBtn.Bind(wx.EVT_BUTTON, self.onOk)
        cancelBtn.Bind(wx.EVT_BUTTON, self.onCancel)
    def onOk(self,event):
        boxLen,boxWidth = self.lenText.GetValue(),self.widthText.GetValue()
        # 1-9999的范围
        if re.match(pattern=r'^[1-9]\d{0,3}$',string=boxLen) and re.match(pattern=r'^[1-9]\d{0,3}$',string=boxWidth):
            self.boxSize[0]=int(self.lenText.GetValue())
            self.boxSize[1] = int(self.widthText.GetValue())
            self.boxType='BT'+str(self.boxSize[0])+'X' + str(self.boxSize[1])
            self.Close()#按确定之后退出
            if self.mode and self.boxInfo is not None:
                self.log.write_textctrl_txt(
                    '%s纸箱修改后的信息为：长度为%smm，宽度为%smm.' % (self.boxInfo, self.boxSize[0], self.boxSize[1]))
            else:
                self.log.write_textctrl_txt('%s添加的新纸箱类型为%s，长度为%smm，宽度为%smm.' % (self.curSeries, self.boxType, self.boxSize[0], self.boxSize[1]))
        else:
            self.log.write_textctrl_txt('纸箱尺寸输入不符合规范，请重新输入.')
        event.Skip()
    def onCancel(self,event):
        self.Close()
        event.Skip()

