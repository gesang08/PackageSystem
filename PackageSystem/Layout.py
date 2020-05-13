#!/usr/bin/env python3
# encoding:utf-8


"""
板件的布局、放置算法
"""
from confs.Setting import *
import copy
from collections import Counter

class LowestHoriztonalAlgorithm:
    """
    通过最低水平线算法将包中每一层部件的放置情况给出来
    """
    def __init__(self, key, value, box_long, box_short, log=None):
        """
        value协议：
        [part_id,width,height,thick,is_change_state,Index,short_range_low, short_range_up, long_range_low, long_range_up,
        box_block_low,box_block_up]
        """
        self._key = key
        self._value = value[:]  # 使用切片复制一份列表数据副本，使形参在改变的同时不改变实参
        self._box_long = box_long
        self._box_short = box_short
        self._log = log
        self._each_package_part_num = len(self._value)  # 每包需要放置的部件总数量
        self.lowest_level_line = 0  # 设置初始最低水平线为0
        self.plate_temp = []  # 用于暂存所排部件的过程信息
        self.layout_component_info = []  # 该列表存放的是矩形块左上角坐标高于最低水平线的信息，用于提升最低水平线

    def init_parameters(self):
        self.lowest_level_line = 0
        self.plate_temp = [[0 for col in range(11)] for row in range(self._each_package_part_num * OneLayerMaxPlates)]
        self.plate_temp[0] = [0, 0, self._box_long, self._box_short, 0, 0, 0, 0, 0, 0, 0]
        self.layout_component_info = []

    def put_each_package(self):
        """
        该方法用于将每一包部件放好
        :return: 包中每一块部件所放置的信息
        """
        current_layer_num = 0  # 记录当前层数，进行层数限制
        plates = []  # 存放打包后的结果信息
        """
        plates和plate_temp列表：
        column 11列字段协议:
        [x,y,wait_fill_area_long,wait_fill_area_width,height,width,thick,is_rotate,layer_num,package_id,part_id]
        x,y:以左下角为坐标原点，向右为x+,向上为y+建立坐标系，(x,y)表示最低水平线上部件左下角的坐标
        wait_fill_area_long,wait_fill_area_width：待填充区域的长宽
        is_rotate：排板时，height,width需要是否旋转，0为不旋转，1为旋转
        layer_num,package_id：该部件属于第几层；该部件属于的包编号
        is_change_state:部件高宽是否旋转，0不旋转，1旋转
        注：此处的height为与x轴平行的部件长度，width为与y轴平行的部件长度，不一定为原部件高宽
        """
        while len(self._value):
            current_layer_num = self.put_each_layer(current_layer_num)
            # if current_layer_num > OnePackageMaxLayers:
            #     print time.strftime("%Y年%m月%d日 %H:%M:%S  ", time.localtime(time.time())) + \
            #           u"该包超过10层，请重新打！"
            #     break
            for p in self.plate_temp:
                if p[10] != 0:
                    p[8] = current_layer_num
                    # 暂时为了测试
                    if p[7] == 1:
                        temp = p[4]
                        p[4] = p[5]
                        p[5] = temp
                    plates.append(p)
        return plates, current_layer_num

    def put_each_layer(self, current_layer_num):
        """
        该方法用于将每一层部件放好
        :param current_layer_num: 待放好的层编号
        :return: 已放好的层编号
        """
        self.init_parameters()  # 放好一层后，需要把参数初始化
        current_each_layer_plate_num = 0  # 记录每层的块数，进行块数限制
        i = 0  # 可以理解为当前放好的块数编号
        j = 1  # 可以理解为当前水平线上，待放好下一块的块数编号
        while i < j:
            wait_fill_area_long = self.plate_temp[i][2]
            wait_fill_area_width = self.plate_temp[i][3]
            for k in range(len(self._value)):
                if wait_fill_area_long >= self._value[k][2] and wait_fill_area_width >= self._value[k][1]:  # 能放进待填充区域
                    self.plate_temp[i][7] = 0  # is_rotate=0
                    self.can_layout(i, j, k)
                    j += 1
                    current_each_layer_plate_num += 1
                    del self._value[k]
                    break
                elif wait_fill_area_long >= self._value[k][1] and wait_fill_area_width >= self._value[k][2]:
                    self.plate_temp[i][7] = 1  # is_rotate=1
                    temp_part_height = self._value[k][2]  # 转换height,width,用于计算wait_fill_area_long，wait_fill_area_width
                    self._value[k][2] = self._value[k][1]
                    self._value[k][1] = temp_part_height
                    self.can_layout(i, j, k)
                    j += 1
                    current_each_layer_plate_num += 1
                    del self._value[k]
                    break
            i += 1
            if current_each_layer_plate_num >= OneLayerMaxPlates:  # 层中块数限制
                break
            if i == j:
                self.improve_lowest_level_line()  # 提升最低水平线
                if not self.layout_component_info:  # self.layout_component_info == []
                    break
                j = self.get_new_wait_fill_region(j)
        current_layer_num += 1
        return current_layer_num

    def can_layout(self, current_level, current_level_next, index):
        """
        1.记录当前最低水平线上放置好的部件尺寸与部件号
        2.产生当前最低水平线上下一个待填充区域的坐标与大小
        :param current_level:
        :param current_level_next:
        :param index:
        :return:
        """
        self.plate_temp[current_level][4] = self._value[index][2]  # 记录height
        self.plate_temp[current_level][5] = self._value[index][1]  # 记录width
        self.plate_temp[current_level][6] = self._value[index][3]  # 记录thick
        self.plate_temp[current_level][10] = self._value[index][0]  # 记录part_id

        self.plate_temp[current_level_next][0] = self.plate_temp[current_level][0] + self._value[index][2]
        self.plate_temp[current_level_next][1] = self.plate_temp[current_level][1]
        self.plate_temp[current_level_next][2] = self.plate_temp[current_level][2] - self._value[index][2]
        self.plate_temp[current_level_next][3] = self.plate_temp[current_level][3]

    def improve_lowest_level_line(self):
        """
        self.layout_component_info列表协议：
        [x, y, is_rotate,x_size]
        x,y:部件左上角坐标
        is_rotate：部件排板时，height,width需要是否旋转，0为不旋转，1为旋转
        x_size:与x轴平行的部件的长度
        """
        self.layout_component_info = []  # 使用时先初始化该列表
        for i in range(len(self.plate_temp)):
            if self.plate_temp[i][10] != 0:  # 滤除没有放部件的row
                if self.plate_temp[i][1] + self.plate_temp[i][5] > self.lowest_level_line:  # 左上角坐标的y大于最低水平线，滤除最低水平线上和最低水平线之下已放置好的部件
                    self.layout_component_info.append([self.plate_temp[i][0], self.plate_temp[i][1] + self.plate_temp[i][5], self.plate_temp[i][7], self.plate_temp[i][4]])
        if self.layout_component_info:  # 当该列表不为空的时候才执行,等价于self.layout_component_info！= []
            self.layout_component_info.sort(key=lambda x: x[1])  # 按照y进行升序排列
            for j in range(len(self.layout_component_info)):
                if self.layout_component_info[j][1] != self.lowest_level_line:
                    self.lowest_level_line = self.layout_component_info[j][1]  # 提升最低水平线
                    break

    def get_new_wait_fill_region(self, current_level_next):
        self.layout_component_info.sort(key=lambda x: x[0])  # 按照x进行升序排列
        i = 0
        while i < len(self.layout_component_info):
            # 上一最低水平线所放矩形块的左上角坐标所处位置有两种情况：1.在最低水平线上；2.在最低水平线之上
            if self.layout_component_info[i][1] == self.lowest_level_line:  # 在最低水平线上
                if i == len(self.layout_component_info) - 1:
                    self.plate_temp[current_level_next][2] = self._box_long - self.layout_component_info[i][0]
                    current_level_next = self.get_new_plate_info(current_level_next, self.layout_component_info[i][0])
                for j in range(i + 1, len(self.layout_component_info)):
                    if self.layout_component_info[j][1] != self.lowest_level_line:  # 不在提升后的最低水平线上
                        if i == 0 and self.layout_component_info[j][0] != 0:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[j][0]
                            current_level_next = self.get_new_plate_info(current_level_next, 0)
                        else:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[j][0] - self.layout_component_info[i][0]
                            current_level_next = self.get_new_plate_info(current_level_next, self.layout_component_info[i][0])
                        i = j - 1
                        break
                    elif j == len(self.layout_component_info) - 1 and self.layout_component_info[j][1] == self.lowest_level_line:
                        if i == 0 and self.layout_component_info[j][0] != 0:
                            self.plate_temp[current_level_next][2] = self._box_long
                            current_level_next = self.get_new_plate_info(current_level_next, 0)
                        else:
                            self.plate_temp[current_level_next][2] = self._box_long - self.layout_component_info[i][0]
                            current_level_next = self.get_new_plate_info(current_level_next, self.layout_component_info[i][0])
                        i = j
                        break
            else:  # 在最低水平线之上
                get_x_lists = [x[0] for x in self.layout_component_info]  # 上一最低水平线所放所有部件左上角坐标x组成的列表
                get_x = self.layout_component_info[i][0] + self.layout_component_info[i][3]
                if i == len(self.layout_component_info) - 1:
                    self.plate_temp[current_level_next][2] = self._box_long - get_x
                    current_level_next = self.get_new_plate_info(current_level_next, get_x)
                elif get_x not in get_x_lists:
                    if i == 0 and self.layout_component_info[i][0] != 0:
                        self.plate_temp[current_level_next][2] = self.layout_component_info[i][0]
                        current_level_next = self.get_new_plate_info(current_level_next, 0)
                    for k in range(i + 1, len(self.layout_component_info)):
                        if self.layout_component_info[k][1] != self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[k][0] - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = k - 1
                            break
                        elif k == len(self.layout_component_info) - 1 and self.layout_component_info[k][1] == self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self._box_long - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = k
                            break
                elif i == 0 and self.layout_component_info[i][0] != 0:
                    self.plate_temp[current_level_next][2] = self._box_long - get_x
                    current_level_next = self.get_new_plate_info(current_level_next, get_x)
                elif self.layout_component_info[i + 1][1] != self.lowest_level_line:
                    pass
                elif self.layout_component_info[i + 1][1] == self.lowest_level_line:
                    if i == len(self.layout_component_info) - 2:
                        self.plate_temp[current_level_next][2] = self._box_long - get_x
                        current_level_next = self.get_new_plate_info(current_level_next, get_x)
                        i += 1
                    for r in range(i + 2, len(self.layout_component_info)):
                        if self.layout_component_info[r][1] != self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[r][0] - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = r - 1
                            break
                        elif r == len(self.layout_component_info) - 1 and self.layout_component_info[r][1] == self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self._box_long - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = r
                            break
            i += 1
        return current_level_next

    def get_new_plate_info(self, current_level_next, _x):
        self.plate_temp[current_level_next][0] = _x
        self.plate_temp[current_level_next][1] = self.lowest_level_line
        self.plate_temp[current_level_next][3] = self._box_short - self.lowest_level_line
        current_level_next += 1
        return current_level_next

class LowestHoriztonal:
    """
    input：一批板件，一个纸盒信息
    output：部分板件排好的信息，没有排好的板件，排好板件总厚度
    """
    def __init__(self, part_lists, box_list):
        self._part_lists = part_lists[:]
        self._box = box_list[:]
        self._box_long = self._box[box_length_index]
        self._box_width = self._box[box_width_index]
        self._box_height = self._box[box_height_index]
        self._part_thickness = self._part_lists[0][part_thickness_index]  # 默认一批板件厚度一致

        self._part_amount = len(self._part_lists)  # 这批板件总数量
        self.lowest_level_line = 0  # 设置初始最低水平线为0
        self.plate_temp = []  # 用于暂存所排部件的过程信息
        self.layout_component_info = []  # 该列表存放的是矩形块左上角坐标高于最低水平线的信息，用于提升最低水平线

    def init_parameters(self):
        self.lowest_level_line = 0
        self.plate_temp = [[0 for col in range(19)] for row in range(self._part_amount * 10)]
        self.plate_temp[0] = [0, 0, self._box_long, self._box_width, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.layout_component_info = []

    def put_main(self):
        """
        放置板件主函数，直接调用该函数返回输出output
        :return: 部分板件排好的信息，没有排好的板件，排好板件总厚度
        """
        current_layer_num = 0  # 记录当前层数，进行层数限制
        plates = []  # 存放打包后的结果信息
        """
        plates和plate_temp列表：
        column 11列字段协议:
        [x,y,wait_fill_area_long,wait_fill_area_width,length,width,thick,is_rotate,layer_num,package_id,part_id,part_type,area,volume,weight,box_type,box_length,box_width,box_height]
        x,y:以左下角为坐标原点，向右为x+,向上为y+建立坐标系，(x,y)表示最低水平线上部件左下角的坐标
        wait_fill_area_long,wait_fill_area_width：待填充区域的长宽
        is_rotate：排板时，length,width需要是否旋转，0为不旋转，1为旋转
        layer_num,package_id：该部件属于第几层；该部件属于的包编号
        is_change_state:部件高宽是否旋转，0不旋转，1旋转
        注：此处的height为与x轴平行的部件长度，width为与y轴平行的部件长度，不一定为原部件高宽
        """
        while len(self._part_lists): # 两个结束条件：1.这批部件被放置完了；2.放置部件总厚度超过纸箱高度
            # current_layer_num * self._part_thickness > self._box_height会超出纸箱高度，造成数据丢失
            if (current_layer_num + 1) * self._part_thickness > self._box_height:
                break
            current_layer_num = self.put_each_layer(current_layer_num)
            for plate_temp_item in self.plate_temp:
                if plate_temp_item[10] != 0:  # 取放好的板件
                    plate_temp_item[8] = current_layer_num

                    if plate_temp_item[7] == 1:
                        temp = plate_temp_item[4]
                        plate_temp_item[4] = plate_temp_item[5]
                        plate_temp_item[5] = temp
                        # 为了将is_rotate=1时，布局排样的板件长宽再次转换过来
                        # 例如，原板件的length=282,width=484，在布局排样is_rotate=1时将282和484调换进行布局排样
                        # 结束时，再将282和484再次转换过来，保存的信息为&282&484&1，1表示旋转状态，放置板件时先旋转90度
                        # 将484放在纸箱长度方向，将282放在纸箱宽度方向
                    plates.append(plate_temp_item)
                # print('旋转状态：%s' % plate_temp_item[7])

        return plates, self._part_lists, current_layer_num * self._part_thickness

    def put_each_layer(self, current_layer_num):
        """
        该方法用于将每一层部件放好
        :param current_layer_num: 待放好的层编号
        :return: 已放好的层编号
        """
        self.init_parameters()  # 放好一层后，需要把参数初始化
        current_each_layer_plate_num = 0  # 记录每层的块数，进行块数限制
        i = 0  # 可以理解为当前放好的块数编号
        j = 1  # 可以理解为当前水平线上，待放好下一块的块数编号
        while i < j:
            wait_fill_area_long = self.plate_temp[i][2]
            wait_fill_area_width = self.plate_temp[i][3]
            for k in range(len(self._part_lists[:])):
                if wait_fill_area_long >= self._part_lists[k][part_length_index] and wait_fill_area_width >= self._part_lists[k][part_width_index]:  # 能放进待填充区域
                    self.plate_temp[i][7] = 0  # is_rotate=0
                    self.can_layout(i, j, k)
                    j += 1
                    current_each_layer_plate_num += 1
                    del self._part_lists[k]
                    break
                elif wait_fill_area_long >= self._part_lists[k][part_width_index] and wait_fill_area_width >= self._part_lists[k][part_length_index]:
                    self.plate_temp[i][7] = 1  # is_rotate=1
                    temp_part_height = self._part_lists[k][part_length_index]  # 转换height,width,用于计算wait_fill_area_long，wait_fill_area_width
                    self._part_lists[k][part_length_index] = self._part_lists[k][part_width_index]
                    self._part_lists[k][part_width_index] = temp_part_height
                    self.can_layout(i, j, k)
                    j += 1
                    current_each_layer_plate_num += 1
                    del self._part_lists[k]
                    break
            i += 1
            if i == j:
                self.improve_lowest_level_line()  # 提升最低水平线
                if not self.layout_component_info:  # self.layout_component_info == []
                    break
                j = self.get_new_wait_fill_region(j)
        current_layer_num += 1
        return current_layer_num

    def can_layout(self, current_level, current_level_next, index):
        """
        1.记录当前最低水平线上放置好的部件尺寸与部件号
        2.产生当前最低水平线上下一个待填充区域的坐标与大小
        :param current_level:
        :param current_level_next:
        :param index:
        :return:
        """
        self.plate_temp[current_level][4] = self._part_lists[index][part_length_index]  # 记录height
        self.plate_temp[current_level][5] = self._part_lists[index][part_width_index]  # 记录width
        self.plate_temp[current_level][6] = self._part_lists[index][part_thickness_index]  # 记录thick
        self.plate_temp[current_level][10] = self._part_lists[index][part_id_index]  # 记录part_id

        # 新增
        self.plate_temp[current_level][11] = self._part_lists[index][door_type_index]
        self.plate_temp[current_level][12] = self._part_lists[index][area_index]
        self.plate_temp[current_level][13] = self._part_lists[index][volume_index]
        self.plate_temp[current_level][14] = self._part_lists[index][weight_index]
        self.plate_temp[current_level][15] = self._box[box_type_index]
        self.plate_temp[current_level][16] = self._box[box_length_index]
        self.plate_temp[current_level][17] = self._box[box_width_index]
        self.plate_temp[current_level][18] = self._box[box_height_index]
        # self.plate_temp[current_level][9] = 'P' + self._part_lists[index][sec_id_index] + '-' + str(package_num)

        self.plate_temp[current_level_next][0] = self.plate_temp[current_level][0] + self._part_lists[index][part_length_index]
        self.plate_temp[current_level_next][1] = self.plate_temp[current_level][1]
        self.plate_temp[current_level_next][2] = self.plate_temp[current_level][2] - self._part_lists[index][part_length_index]
        self.plate_temp[current_level_next][3] = self.plate_temp[current_level][3]

    def improve_lowest_level_line(self):
        """
        self.layout_component_info列表协议：
        [x, y, is_rotate,x_size]
        x,y:部件左上角坐标
        is_rotate：部件排板时，height,width需要是否旋转，0为不旋转，1为旋转
        x_size:与x轴平行的部件的长度
        """
        self.layout_component_info = []  # 使用时先初始化该列表
        for i in range(len(self.plate_temp)):
            if self.plate_temp[i][10] != 0:  # 滤除没有放部件的row
                if self.plate_temp[i][1] + self.plate_temp[i][5] > self.lowest_level_line:  # 左上角坐标的y大于最低水平线，滤除最低水平线上和最低水平线之下已放置好的部件
                    self.layout_component_info.append([self.plate_temp[i][0], self.plate_temp[i][1] + self.plate_temp[i][5], self.plate_temp[i][7], self.plate_temp[i][4]])
        if self.layout_component_info:  # 当该列表不为空的时候才执行,等价于self.layout_component_info！= []
            self.layout_component_info.sort(key=lambda x: x[1])  # 按照y进行升序排列
            for j in range(len(self.layout_component_info)):
                if self.layout_component_info[j][1] != self.lowest_level_line:
                    self.lowest_level_line = self.layout_component_info[j][1]  # 提升最低水平线
                    break

    def get_new_wait_fill_region(self, current_level_next):
        self.layout_component_info.sort(key=lambda x: x[0])  # 按照x进行升序排列
        i = 0
        while i < len(self.layout_component_info):
            # 上一最低水平线所放矩形块的左上角坐标所处位置有两种情况：1.在最低水平线上；2.在最低水平线之上
            if self.layout_component_info[i][1] == self.lowest_level_line:  # 在最低水平线上
                if i == len(self.layout_component_info) - 1:
                    self.plate_temp[current_level_next][2] = self._box_long - self.layout_component_info[i][0]
                    current_level_next = self.get_new_plate_info(current_level_next, self.layout_component_info[i][0])
                for j in range(i + 1, len(self.layout_component_info)):
                    if self.layout_component_info[j][1] != self.lowest_level_line:  # 不在提升后的最低水平线上
                        if i == 0 and self.layout_component_info[j][0] != 0:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[j][0]
                            current_level_next = self.get_new_plate_info(current_level_next, 0)
                        else:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[j][0] - self.layout_component_info[i][0]
                            current_level_next = self.get_new_plate_info(current_level_next, self.layout_component_info[i][0])
                        i = j - 1
                        break
                    elif j == len(self.layout_component_info) - 1 and self.layout_component_info[j][1] == self.lowest_level_line:
                        if i == 0 and self.layout_component_info[j][0] != 0:
                            self.plate_temp[current_level_next][2] = self._box_long
                            current_level_next = self.get_new_plate_info(current_level_next, 0)
                        else:
                            self.plate_temp[current_level_next][2] = self._box_long - self.layout_component_info[i][0]
                            current_level_next = self.get_new_plate_info(current_level_next, self.layout_component_info[i][0])
                        i = j
                        break
            else:  # 在最低水平线之上
                get_x_lists = [x[0] for x in self.layout_component_info]  # 上一最低水平线所放所有部件左上角坐标x组成的列表
                get_x = self.layout_component_info[i][0] + self.layout_component_info[i][3]
                if i == len(self.layout_component_info) - 1:
                    self.plate_temp[current_level_next][2] = self._box_long - get_x
                    current_level_next = self.get_new_plate_info(current_level_next, get_x)
                elif get_x not in get_x_lists:
                    if i == 0 and self.layout_component_info[i][0] != 0:
                        self.plate_temp[current_level_next][2] = self.layout_component_info[i][0]
                        current_level_next = self.get_new_plate_info(current_level_next, 0)
                    for k in range(i + 1, len(self.layout_component_info)):
                        if self.layout_component_info[k][1] != self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[k][0] - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = k - 1
                            break
                        elif k == len(self.layout_component_info) - 1 and self.layout_component_info[k][1] == self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self._box_long - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = k
                            break
                elif i == 0 and self.layout_component_info[i][0] != 0:
                    self.plate_temp[current_level_next][2] = self._box_long - get_x
                    current_level_next = self.get_new_plate_info(current_level_next, get_x)
                elif self.layout_component_info[i + 1][1] != self.lowest_level_line:
                    pass
                elif self.layout_component_info[i + 1][1] == self.lowest_level_line:
                    if i == len(self.layout_component_info) - 2:
                        self.plate_temp[current_level_next][2] = self._box_long - get_x
                        current_level_next = self.get_new_plate_info(current_level_next, get_x)
                        i += 1
                    for r in range(i + 2, len(self.layout_component_info)):
                        if self.layout_component_info[r][1] != self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[r][0] - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = r - 1
                            break
                        elif r == len(self.layout_component_info) - 1 and self.layout_component_info[r][1] == self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self._box_long - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = r
                            break
            i += 1
        return current_level_next

    def get_new_plate_info(self, current_level_next, _x):
        self.plate_temp[current_level_next][0] = _x
        self.plate_temp[current_level_next][1] = self.lowest_level_line
        self.plate_temp[current_level_next][3] = self._box_width - self.lowest_level_line
        current_level_next += 1
        return current_level_next


class HeuristicPut:
    """
    input:一批货物的放置顺序和方向、一个纸箱的大小
    output:货物放置方案、扔出去的货物
    按照预先给定的顺序和方向放置，超出纸箱的货物扔出去
    """
    def __init__(self,putSeq, box):
        # 货物属性
        self.itemNum = len(putSeq) // 2  #货物数量
        self.plainSeq = putSeq[:self.itemNum]  #放置顺序序列信息
        self.orientSeq = putSeq[self.itemNum:]  #放置方向序列信息
        self.orientSeqBak = copy.deepcopy(self.orientSeq)
        self.thick = putSeq[0][part_thickness_index]
        # 纸箱属性
        self.boxType = box[box_type_index]
        self.boxLength = box[box_length_index]
        self.boxWidth = box[box_width_index]
        self.boxHeight = box[box_height_index]
        self.boxVolume = box[box_volume_index]
        self.boxWeight = box[box_weight_index]

    def initLayer(self):
        # 最低水平线
        self.lowest_level_line = 0
        # 用于暂存所排部件的过程信息
        self.plate_temp = [[0 for col in range(19)] for row in range(self.itemNum * 10)]
        self.plate_temp[0] = [0, 0, self.boxLength, self.boxWidth, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        # 该列表存放的是矩形块左上角坐标高于最低水平线的信息，用于提升最低水平线
        self.layout_component_info = []

    def put_main(self):
        """
        板件装箱布局算法主函数
        :return:
        plates：装箱方案
        self.plainSeq：放不进去纸箱的板件，即需要扔出去的板件
        self.orientSeq：放不进去纸箱的板件方向信息
        current_layer_num * self.thick：板件装箱总厚度
        """
        current_layer_num = 0  # 记录当前层数，进行层数限制
        plates = []  # 存放打包后的结果信息
        """
        plates和plate_temp列表：
        column 11列字段协议:
        [x,y,wait_fill_area_long,wait_fill_area_width,length,width,thick,is_rotate,layer_num,package_id,part_id,part_type,area,volume,weight,box_type,box_length,box_width,box_height]
        x,y:以左下角为坐标原点，向右为x+,向上为y+建立坐标系，(x,y)表示最低水平线上部件左下角的坐标
        wait_fill_area_long,wait_fill_area_width：待填充区域的长宽
        is_rotate：排板时，length,width需要是否旋转，0为不旋转，1为旋转
        layer_num,package_id：该部件属于第几层；该部件属于的包编号
        """
        while len(self.plainSeq):  # 两个结束条件：1.这批部件被放置完了；2.放置部件总厚度超过纸箱高度
            if (current_layer_num + 1) * self.thick > self.boxHeight:
                break
            current_layer_num = self.put_each_layer(current_layer_num)
            #获取每层装箱方案
            for plate_temp_item in self.plate_temp:
                if plate_temp_item[10] != 0:  # 取放好的板件
                    plate_temp_item[8] = current_layer_num#记录当前部件的层编号
                    plates.append(plate_temp_item)
                if plate_temp_item == [0]*19:
                    break
        return plates, self.plainSeq, self.orientSeqBak, current_layer_num * self.thick

    def put_each_layer(self, current_layer_num):
        """
        该方法用于将每一层部件放好
        :param current_layer_num: 待放好的层编号
        :return: 已放好的层编号
        """
        self.initLayer()  # 放好一层后，需要把参数初始化
        current_each_layer_plate_num = 0  # 记录每层的块数，进行块数限制
        self.plate_specification_height = self.boxLength
        self.plate_specification_width = self.boxWidth
        i = 0  # 可以理解为当前放好的块数编号
        j = 1  # 可以理解为当前水平线上，待放好下一块的块数编号
        while i < j:
            self.resortArea()
            wait_fill_area_long = self.plate_temp[i][2]
            wait_fill_area_width = self.plate_temp[i][3]
            if len(self.orientSeq)==0:
                break
            for k in range(self.itemNum):
                if wait_fill_area_long != 0 and wait_fill_area_width != 0:
                    if self.orientSeq[k] == 1:#方向旋转，调换长宽
                        self.plainSeq[k][part_length_index],self.plainSeq[k][part_width_index]=self.plainSeq[k][part_width_index],self.plainSeq[k][part_length_index]
                        self.orientSeq[k] = 0 # 表示已经旋转过了
                    if wait_fill_area_long >= self.plainSeq[k][part_length_index] and wait_fill_area_width >= self.plainSeq[k][part_width_index]:  # 能放进待填充区域
                        self.can_layout(i, j, k)
                        j += 1
                        current_each_layer_plate_num += 1
                        del self.plainSeq[k]
                        del self.orientSeq[k]
                        del self.orientSeqBak[k]
                    else:
                        i = j-1
                    break
            i += 1
            if i == j:
                self.improve_lowest_level_line()  # 提升最低水平线
                if len(self.layout_component_info)==0:  # self.layout_component_info == []
                    break
                j = self.get_new_wait_fill_region(j)
        current_layer_num += 1
        return current_layer_num

    def resortArea(self):
        tmpList = []
        sortedTmpList = []
        for i, v in enumerate(self.plate_temp):
            if v == [0] * len(v):  # 减少时间
                break
            if v[1] == self.lowest_level_line and v[10] == 0:
                tmpList.append(i)
                sortedTmpList.append(v)
        if len(tmpList) != 0:
            sortedTmpList.sort(key=lambda x: x[0])
            for idx, val in enumerate(sortedTmpList):
                self.plate_temp[tmpList[idx]] = val

    def can_layout(self, current_level, current_level_next, index):
        """
        1.记录当前最低水平线上放置好的部件尺寸与部件号
        2.产生当前最低水平线上下一个待填充区域的坐标与大小
        :param current_level:
        :param current_level_next:
        :param index:
        :return:
        """
        #放置货物信息
        #注：当板件放置时不旋转，长宽存储的是实际长宽；当板件放置时旋转了，长的内存空间存储的是宽，宽的内存空间存储的是长
        self.plate_temp[current_level][4] = self.plainSeq[index][part_length_index]  # 记录height
        self.plate_temp[current_level][5] = self.plainSeq[index][part_width_index]  # 记录width
        self.plate_temp[current_level][6] = self.plainSeq[index][part_thickness_index]  # 记录thick
        self.plate_temp[current_level][7] = self.orientSeqBak[index]  #记录是否旋转信息
        self.plate_temp[current_level][10] = self.plainSeq[index][part_id_index]  # 记录part_id
        self.plate_temp[current_level][11] = self.plainSeq[index][door_type_index]
        self.plate_temp[current_level][12] = self.plainSeq[index][area_index]
        self.plate_temp[current_level][13] = self.plainSeq[index][volume_index]
        self.plate_temp[current_level][14] = self.plainSeq[index][weight_index]
        #给出当前货物所处的纸箱信息
        self.plate_temp[current_level][15] = self.boxType
        self.plate_temp[current_level][16] = self.boxLength
        self.plate_temp[current_level][17] = self.boxWidth
        self.plate_temp[current_level][18] = self.boxHeight
        #给出放置后的lowestLine上的右端坐标和填充区域长宽
        self.plate_temp[current_level_next][0] = self.plate_temp[current_level][0] + self.plainSeq[index][
            part_length_index]
        self.plate_temp[current_level_next][1] = self.plate_temp[current_level][1]
        self.plate_temp[current_level_next][2] = self.plate_temp[current_level][2] - self.plainSeq[index][
            part_length_index]
        self.plate_temp[current_level_next][3] = self.plate_temp[current_level][3]

    def improve_lowest_level_line(self):
        """
        self.layout_component_info列表协议：
        [x, y, is_rotate,x_size]
        x,y:部件左上角坐标
        is_rotate：部件排板时，height,width需要是否旋转，0为不旋转，1为旋转
        x_size:与x轴平行的部件的长度
        """
        self.layout_component_info = []  # 使用时先初始化该列表
        for i in range(len(self.plate_temp)):
            if self.plate_temp[i][10] != 0:  # 滤除没有放部件的row
                if self.plate_temp[i][1] + self.plate_temp[i][
                    5] > self.lowest_level_line:  # 左上角坐标的y大于最低水平线，滤除最低水平线上和最低水平线之下已放置好的部件
                    self.layout_component_info.append(
                        [self.plate_temp[i][0], self.plate_temp[i][1] + self.plate_temp[i][5], self.plate_temp[i][7],
                         self.plate_temp[i][4]])
        if self.layout_component_info:  # 当该列表不为空的时候才执行,等价于self.layout_component_info！= []
            self.layout_component_info.sort(key=lambda x: x[1])  # 按照y进行升序排列
            for j in range(len(self.layout_component_info)):
                if self.layout_component_info[j][1] != self.lowest_level_line:
                    self.lowest_level_line = self.layout_component_info[j][1]  # 提升最低水平线
                    break

    def get_new_wait_fill_region(self, current_level_next):
        self.layout_component_info.sort(key=lambda x: x[0])  # 按照x进行升序排列
        i = 0
        while i < len(self.layout_component_info):
            # 上一最低水平线所放矩形块的左上角坐标所处位置有两种情况：1.在最低水平线上；2.在最低水平线之上
            if self.layout_component_info[i][1] == self.lowest_level_line:  # 在最低水平线上
                if i == len(self.layout_component_info) - 1:
                    self.plate_temp[current_level_next][2] = self.plate_specification_height - self.layout_component_info[i][0]
                    current_level_next = self.get_new_plate_info(current_level_next, self.layout_component_info[i][0])
                for j in range(i + 1, len(self.layout_component_info)):
                    if self.layout_component_info[j][1] != self.lowest_level_line:  # 不在提升后的最低水平线上
                        if i == 0 and self.layout_component_info[j][0] != 0:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[j][0]
                            current_level_next = self.get_new_plate_info(current_level_next, 0)
                        else:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[j][0] - \
                                                                     self.layout_component_info[i][0]
                            current_level_next = self.get_new_plate_info(current_level_next,
                                                                         self.layout_component_info[i][0])
                        i = j - 1
                        break
                    elif j == len(self.layout_component_info) - 1 and self.layout_component_info[j][
                        1] == self.lowest_level_line:
                        if i == 0 and self.layout_component_info[j][0] != 0:
                            self.plate_temp[current_level_next][2] = self.plate_specification_height
                            current_level_next = self.get_new_plate_info(current_level_next, 0)
                        else:
                            self.plate_temp[current_level_next][2] = self.plate_specification_height - self.layout_component_info[i][0]
                            current_level_next = self.get_new_plate_info(current_level_next,
                                                                         self.layout_component_info[i][0])
                        i = j
                        break
            else:  # 在最低水平线之上
                get_x_lists = [x[0] for x in self.layout_component_info]  # 上一最低水平线所放所有部件左上角坐标x组成的列表
                get_x = self.layout_component_info[i][0] + self.layout_component_info[i][3]
                # if len(self.layout_component_info)>=2 and i!=len(self.layout_component_info)-1:
                #     if self.layout_component_info[i][1]< max([v[1] for v in self.layout_component_info]):
                #         # num=0
                #         # for v in range(i+1, len(self.layout_component_info)):
                #         #     if self.layout_component_info[v][1]==self.layout_component_info[i+1][1]:
                #         #         num+=1
                #         # get_x=get_x+num*self.layout_component_info[i+1][3]
                #         self.boxLength=self.layout_component_info[i+1][0]
                if i == len(self.layout_component_info) - 1:
                    self.plate_temp[current_level_next][2] = self.plate_specification_height - get_x
                    current_level_next = self.get_new_plate_info(current_level_next, get_x)
                elif get_x not in get_x_lists:
                    if i == 0 and self.layout_component_info[i][0] != 0:
                        self.plate_temp[current_level_next][2] = self.layout_component_info[i][0]
                        current_level_next = self.get_new_plate_info(current_level_next, 0)
                    for k in range(i + 1, len(self.layout_component_info)):
                        if self.layout_component_info[k][1] != self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[k][0] - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = k - 1
                            break
                        elif k == len(self.layout_component_info) - 1 and self.layout_component_info[k][
                            1] == self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self.plate_specification_height - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = k
                            break
                elif i == 0 and self.layout_component_info[i][0] != 0:
                    self.plate_temp[current_level_next][2] = self.layout_component_info[i][0]
                    # self.plate_temp[current_level_next][2] = self.plate_specification_height - get_x
                    current_level_next = self.get_new_plate_info(current_level_next, get_x)
                elif self.layout_component_info[i + 1][1] != self.lowest_level_line:
                    pass
                elif self.layout_component_info[i + 1][1] == self.lowest_level_line:
                    if i == len(self.layout_component_info) - 2:
                        self.plate_temp[current_level_next][2] = self.plate_specification_height - get_x
                        current_level_next = self.get_new_plate_info(current_level_next, get_x)
                        i += 1
                    for r in range(i + 2, len(self.layout_component_info)):
                        if self.layout_component_info[r][1] != self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[r][0] - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = r - 1
                            break
                        elif r == len(self.layout_component_info) - 1 and self.layout_component_info[r][
                            1] == self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self.plate_specification_height - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = r
                            break
            i += 1
        return current_level_next

    def get_new_plate_info(self, current_level_next, _x):
        self.plate_temp[current_level_next][0] = _x
        self.plate_temp[current_level_next][1] = self.lowest_level_line
        self.plate_temp[current_level_next][3] = self.boxWidth - self.lowest_level_line
        current_level_next += 1
        return current_level_next


class HeuristicPut1:
    """
    input:一批货物的放置顺序和方向、一个纸箱的大小
    output:货物放置方案、扔出去的货物
    按照预先给定的顺序和方向放置，超出纸箱的货物扔出去
    """
    def __init__(self,putSeq, box):
        # 货物属性
        self.itemNum = len(putSeq) // 2  #货物数量
        self.plainSeq = putSeq[:self.itemNum]  #放置顺序序列信息
        self.orientSeq = putSeq[self.itemNum:]  #放置方向序列信息
        self.thick = putSeq[0][part_thickness_index]
        # 纸箱属性
        self.boxType = box[box_type_index]
        self.boxLength = box[box_length_index]
        self.boxWidth = box[box_width_index]
        self.boxHeight = box[box_height_index]
        self.boxVolume = box[box_volume_index]
        self.boxWeight = box[box_weight_index]

    def initLayer(self):
        # 最低水平线
        self.lowest_level_line = 0
        # 用于暂存所排部件的过程信息
        self.plate_temp = [[0 for col in range(19)] for row in range(self.itemNum * 10)]
        self.plate_temp[0] = [0, 0, self.boxLength, self.boxWidth, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        # 该列表存放的是矩形块左上角坐标高于最低水平线的信息，用于提升最低水平线
        self.layout_component_info = []

    def put_main(self):
        """
        板件装箱布局算法主函数
        :return:
        plates：装箱方案
        self.plainSeq：放不进去纸箱的板件，即需要扔出去的板件
        self.orientSeq：放不进去纸箱的板件方向信息
        current_layer_num * self.thick：板件装箱总厚度
        """
        current_layer_num = 0  # 记录当前层数，进行层数限制
        plates = []  # 存放打包后的结果信息
        """
        plates和plate_temp列表：
        column 11列字段协议:
        [x,y,wait_fill_area_long,wait_fill_area_width,length,width,thick,is_rotate,layer_num,package_id,part_id,part_type,area,volume,weight,box_type,box_length,box_width,box_height]
        x,y:以左下角为坐标原点，向右为x+,向上为y+建立坐标系，(x,y)表示最低水平线上部件左下角的坐标
        wait_fill_area_long,wait_fill_area_width：待填充区域的长宽
        is_rotate：排板时，length,width需要是否旋转，0为不旋转，1为旋转
        layer_num,package_id：该部件属于第几层；该部件属于的包编号
        """
        while len(self.plainSeq):  # 两个结束条件：1.这批部件被放置完了；2.放置部件总厚度超过纸箱高度
            if (current_layer_num + 1) * self.thick > self.boxHeight:
                break
            current_layer_num = self.put_each_layer(current_layer_num)
            #获取每层装箱方案
            for plate_temp_item in self.plate_temp:
                if plate_temp_item[10] != 0:  # 取放好的板件
                    plate_temp_item[8] = current_layer_num#记录当前部件的层编号
                    plates.append(plate_temp_item)
                if plate_temp_item == [0]*19:
                    break
        return plates, self.plainSeq, self.orientSeq, current_layer_num * self.thick

    def put_each_layer(self, current_layer_num):
        """
        该方法用于将每一层部件放好
        :param current_layer_num: 待放好的层编号
        :return: 已放好的层编号
        """
        self.initLayer()  # 放好一层后，需要把参数初始化
        current_each_layer_plate_num = 0  # 记录每层的块数，进行块数限制
        i = 0  # 可以理解为当前放好的块数编号
        j = 1  # 可以理解为当前水平线上，待放好下一块的块数编号
        while i < j:
            wait_fill_area_long = self.plate_temp[i][2]
            wait_fill_area_width = self.plate_temp[i][3]
            if len(self.orientSeq)==0:
                break
            for k in range(self.itemNum):
                if self.orientSeq[k] == 1:#方向旋转，调换长宽
                    self.plainSeq[k][part_length_index],self.plainSeq[k][part_width_index]=self.plainSeq[k][part_width_index],self.plainSeq[k][part_length_index]
                if wait_fill_area_long >= self.plainSeq[k][part_length_index] and wait_fill_area_width >= self.plainSeq[k][part_width_index]:  # 能放进待填充区域
                    self.can_layout(i, j, k)
                    j += 1
                    current_each_layer_plate_num += 1
                    del self.plainSeq[k]
                    del self.orientSeq[k]
                else:
                    i=j-1
                break
            i += 1
            if i == j:
                self.improve_lowest_level_line()  # 提升最低水平线
                if len(self.layout_component_info)==0:  # self.layout_component_info == []
                    break
                j = self.get_new_wait_fill_region(j)
        current_layer_num += 1
        return current_layer_num

    def can_layout(self, current_level, current_level_next, index):
        """
        1.记录当前最低水平线上放置好的部件尺寸与部件号
        2.产生当前最低水平线上下一个待填充区域的坐标与大小
        :param current_level:
        :param current_level_next:
        :param index:
        :return:
        """
        #放置货物信息
        #注：当板件放置时不旋转，长宽存储的是实际长宽；当板件放置时旋转了，长的内存空间存储的是宽，宽的内存空间存储的是长
        self.plate_temp[current_level][4] = self.plainSeq[index][part_length_index]  # 记录height
        self.plate_temp[current_level][5] = self.plainSeq[index][part_width_index]  # 记录width
        self.plate_temp[current_level][6] = self.plainSeq[index][part_thickness_index]  # 记录thick
        self.plate_temp[current_level][7] = self.orientSeq[index]  #记录是否旋转信息
        self.plate_temp[current_level][10] = self.plainSeq[index][part_id_index]  # 记录part_id
        self.plate_temp[current_level][11] = self.plainSeq[index][door_type_index]
        self.plate_temp[current_level][12] = self.plainSeq[index][area_index]
        self.plate_temp[current_level][13] = self.plainSeq[index][volume_index]
        self.plate_temp[current_level][14] = self.plainSeq[index][weight_index]
        #给出当前货物所处的纸箱信息
        self.plate_temp[current_level][15] = self.boxType
        self.plate_temp[current_level][16] = self.boxLength
        self.plate_temp[current_level][17] = self.boxWidth
        self.plate_temp[current_level][18] = self.boxHeight
        #给出放置后的lowestLine上的右端坐标和填充区域长宽
        self.plate_temp[current_level_next][0] = self.plate_temp[current_level][0] + self.plainSeq[index][
            part_length_index]
        self.plate_temp[current_level_next][1] = self.plate_temp[current_level][1]
        self.plate_temp[current_level_next][2] = self.plate_temp[current_level][2] - self.plainSeq[index][
            part_length_index]
        self.plate_temp[current_level_next][3] = self.plate_temp[current_level][3]

    def improve_lowest_level_line(self):
        """
        self.layout_component_info列表协议：
        [x, y, is_rotate,x_size]
        x,y:部件左上角坐标
        is_rotate：部件排板时，height,width需要是否旋转，0为不旋转，1为旋转
        x_size:与x轴平行的部件的长度
        """
        self.layout_component_info = []  # 使用时先初始化该列表
        for i in range(len(self.plate_temp)):
            if self.plate_temp[i][10] != 0:  # 滤除没有放部件的row
                if self.plate_temp[i][1] + self.plate_temp[i][
                    5] > self.lowest_level_line:  # 左上角坐标的y大于最低水平线，滤除最低水平线上和最低水平线之下已放置好的部件
                    self.layout_component_info.append(
                        [self.plate_temp[i][0], self.plate_temp[i][1] + self.plate_temp[i][5], self.plate_temp[i][7],
                         self.plate_temp[i][4]])
        if self.layout_component_info:  # 当该列表不为空的时候才执行,等价于self.layout_component_info！= []
            self.layout_component_info.sort(key=lambda x: x[1])  # 按照y进行升序排列
            for j in range(len(self.layout_component_info)):
                if self.layout_component_info[j][1] != self.lowest_level_line:
                    self.lowest_level_line = self.layout_component_info[j][1]  # 提升最低水平线
                    break

    def get_new_wait_fill_region(self, current_level_next):
        self.layout_component_info.sort(key=lambda x: x[0])  # 按照x进行升序排列
        i = 0
        while i < len(self.layout_component_info):
            # 上一最低水平线所放矩形块的左上角坐标所处位置有两种情况：1.在最低水平线上；2.在最低水平线之上
            if self.layout_component_info[i][1] == self.lowest_level_line:  # 在最低水平线上
                if i == len(self.layout_component_info) - 1:
                    self.plate_temp[current_level_next][2] = self.boxLength - self.layout_component_info[i][0]
                    current_level_next = self.get_new_plate_info(current_level_next, self.layout_component_info[i][0])
                for j in range(i + 1, len(self.layout_component_info)):
                    if self.layout_component_info[j][1] != self.lowest_level_line:  # 不在提升后的最低水平线上
                        if i == 0 and self.layout_component_info[j][0] != 0:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[j][0]
                            current_level_next = self.get_new_plate_info(current_level_next, 0)
                        else:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[j][0] - \
                                                                     self.layout_component_info[i][0]
                            current_level_next = self.get_new_plate_info(current_level_next,
                                                                         self.layout_component_info[i][0])
                        i = j - 1
                        break
                    elif j == len(self.layout_component_info) - 1 and self.layout_component_info[j][
                        1] == self.lowest_level_line:
                        if i == 0 and self.layout_component_info[j][0] != 0:
                            self.plate_temp[current_level_next][2] = self.boxLength
                            current_level_next = self.get_new_plate_info(current_level_next, 0)
                        else:
                            self.plate_temp[current_level_next][2] = self.boxLength - self.layout_component_info[i][0]
                            current_level_next = self.get_new_plate_info(current_level_next,
                                                                         self.layout_component_info[i][0])
                        i = j
                        break
            else:  # 在最低水平线之上
                get_x_lists = [x[0] for x in self.layout_component_info]  # 上一最低水平线所放所有部件左上角坐标x组成的列表
                get_x = self.layout_component_info[i][0] + self.layout_component_info[i][3]
                if i == len(self.layout_component_info) - 1:
                    self.plate_temp[current_level_next][2] = self.boxLength - get_x
                    current_level_next = self.get_new_plate_info(current_level_next, get_x)
                elif get_x not in get_x_lists:
                    if i == 0 and self.layout_component_info[i][0] != 0:
                        self.plate_temp[current_level_next][2] = self.layout_component_info[i][0]
                        current_level_next = self.get_new_plate_info(current_level_next, 0)
                    for k in range(i + 1, len(self.layout_component_info)):
                        if self.layout_component_info[k][1] != self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[k][0] - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = k - 1
                            break
                        elif k == len(self.layout_component_info) - 1 and self.layout_component_info[k][
                            1] == self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self.boxLength - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = k
                            break
                elif i == 0 and self.layout_component_info[i][0] != 0:
                    self.plate_temp[current_level_next][2] = self.boxLength - get_x
                    current_level_next = self.get_new_plate_info(current_level_next, get_x)
                elif self.layout_component_info[i + 1][1] != self.lowest_level_line:
                    pass
                elif self.layout_component_info[i + 1][1] == self.lowest_level_line:
                    if i == len(self.layout_component_info) - 2:
                        self.plate_temp[current_level_next][2] = self.boxLength - get_x
                        current_level_next = self.get_new_plate_info(current_level_next, get_x)
                        i += 1
                    for r in range(i + 2, len(self.layout_component_info)):
                        if self.layout_component_info[r][1] != self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self.layout_component_info[r][0] - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = r - 1
                            break
                        elif r == len(self.layout_component_info) - 1 and self.layout_component_info[r][
                            1] == self.lowest_level_line:
                            self.plate_temp[current_level_next][2] = self.boxLength - get_x
                            current_level_next = self.get_new_plate_info(current_level_next, get_x)
                            i = r
                            break
            i += 1
        return current_level_next

    def get_new_plate_info(self, current_level_next, _x):
        self.plate_temp[current_level_next][0] = _x
        self.plate_temp[current_level_next][1] = self.lowest_level_line
        self.plate_temp[current_level_next][3] = self.boxWidth - self.lowest_level_line
        current_level_next += 1
        return current_level_next


class LHLA2D:
    def __init__(self, putSeq, box):
        """
        args:
            putSeq:
                type -- list
                dim -- [sublist(n个),binary(n个)]
                前n为序列编码type -- list 后n为0,1编码type -- int
                sublist格式 -- [Contract_id(0), Order_id(1), Sec_id(2), Part_id(3), Door_type(4), Door_width(5),
                Door_height(6), Door_thick(7), Package_state(8), Element_type_id(9), area(10), volume(11), weight(12)]
                len(sublist) -- 13
            box:
                type -- list
            格式 -- [boxType(0), boxLen(1), boxWidth(2), boxHeight(3),boxVolume(4), boxWeight(5), boxNum(6)]
        """
        self.itemNum = len(putSeq) // 2  # 货物数量
        self.plainSeq = putSeq[:self.itemNum]  # 放置顺序序列信息
        self.orientSeq = putSeq[self.itemNum:]  # 放置方向序列信息
        self.orientSeqBak = copy.deepcopy(self.orientSeq)
        self.thick = putSeq[0][7]
        # 纸箱属性
        self.boxType = box[0]
        self.boxLength = box[1]
        self.boxWidth = box[2]
        self.boxHeight = box[3]
        self.boxVolume = box[4]
        self.boxWeight = box[5]

        self.plainSeq = [v + [0] for v in self.plainSeq]  # 增加一维表示放置状态

    def run(self):
        """
        args:
        plates和plate_temp列表：
        column 19列字段协议:
        [x(0),y(1),wait_fill_area_long(2),wait_fill_area_width(3),length(4),width(5),thick(6),is_rotate(7),layer_num(8),
        package_id(9),part_id(10),part_type(11),area(12),volume(13),weight(14),box_type(15),box_length(16),
        box_width(17),box_height(18)]
        x,y:以左下角为坐标原点，向右为x+,向上为y+建立坐标系，(x,y)表示最低水平线上部件左下角的坐标
        wait_fill_area_long,wait_fill_area_width：待填充区域的长宽
        is_rotate：排板时，length,width需要是否旋转，0为不旋转，1为旋转
        """
        self.left_area = 0
        self.min_line = 0 # 最低水平线
        self.left_wait_layout_width = self.boxWidth
        i = 0
        j = 1
        self.plates = [[0 for col in range(19)] for row in range(10 * self.itemNum)]
        self.plates[0][2:4] = self.boxLength, self.boxWidth
        while i < j:
            can_not_layout_enable = 0  # 该变量为0表示所有矩形块都放不进当前待填充矩形块
            wait_layout_long = self.plates[i][2]
            for k in range(len(self.plainSeq)):
                if self.plainSeq[k][-1]==0:  # 矩形件没放好
                    if wait_layout_long >= self.plainSeq[k][5] and \
                                    self.left_wait_layout_width >= self.plainSeq[k][6]:  # 容器长--矩形件长
                        if self.orientSeq[k] == 0:
                            can_not_layout_enable = self.Can_Layout(i, j, k)
                            j += 1
                            break
                        else:
                            self.plainSeq[k][5],self.plainSeq[k][6] = self.plainSeq[k][6],self.plainSeq[k][5]
                            can_not_layout_enable = self.Can_Layout(i, j, k)
                            j += 1
                            break
                    elif wait_layout_long  >= self.plainSeq[k][6] and \
                                    self.left_wait_layout_width >= self.plainSeq[k][5]:  # 容器长--矩形件宽，放置时需旋转一下
                        if self.orientSeq[k] == 0:
                            self.plainSeq[k][5], self.plainSeq[k][6] = self.plainSeq[k][6], self.plainSeq[k][5]
                            self.orientSeq[k]=1
                            can_not_layout_enable = self.Can_Layout(i, j, k)
                            j += 1
                            break
                        else:
                            self.plainSeq[k][5], self.plainSeq[k][6] = self.plainSeq[k][6], self.plainSeq[k][5]
                            self.orientSeq[k] = 0
                            can_not_layout_enable = self.Can_Layout(i, j, k)
                            j += 1
                            break
            i += 1
            if can_not_layout_enable == 0 and i == j:  # 当前水平线下所有待填充区域矩形块都放不进去，则提升最低水平线
                self.Lift_Level_Line()  # 提升最低水平线
                if self.layout_component_information == []:
                    break
                self.left_wait_layout_width = self.boxWidth - self.min_line  # 提升水平线之后，计算待填充区域的宽度
                j = self.Get_Wait_Layout_Region(j)
        utilization_ratio = round(float(self.left_area) / (self.boxWidth * self.boxLength), 4)

    def Can_Layout(self,current_level,total_level,index):
        """
        该函数的功能是：当举行块可以摆放进去时，记录摆放的信息以及新产生的待填充区域
        """
        # 放置货物信息
        # 注：当板件放置时不旋转，长宽存储的是实际长宽；当板件放置时旋转了，长的内存空间存储的是宽，宽的内存空间存储的是长
        self.plates[current_level][4] = self.plainSeq[index][6]  # 记录height
        self.plates[current_level][5] = self.plainSeq[index][5]  # 记录width
        self.plates[current_level][6] = self.plainSeq[index][7]  # 记录thick
        self.plates[current_level][7] = self.orientSeq[index]  # 记录是否旋转信息
        self.plates[current_level][10] = self.plainSeq[index][3]  # 记录part_id
        self.plates[current_level][11] = self.plainSeq[index][4]
        self.plates[current_level][12] = self.plainSeq[index][10]
        self.plates[current_level][13] = self.plainSeq[index][11]
        self.plates[current_level][14] = self.plainSeq[index][12]
        # 给出当前货物所处的纸箱信息
        self.plates[current_level][15] = self.boxType
        self.plates[current_level][16] = self.boxLength
        self.plates[current_level][17] = self.boxWidth
        self.plates[current_level][18] = self.boxHeight

        can_not_layout_enable = 1
        self.plainSeq[index][-1] = 1  # 已经放好
        self.plates[total_level][0] = self.plates[current_level][0] + self.plainSeq[index][6]
        self.plates[total_level][1] = self.plates[current_level][1]
        self.plates[total_level][2] = self.plates[current_level][2] - self.plainSeq[index][6]
        self.plates[total_level][3] = self.left_wait_layout_width
        self.left_area += self.plainSeq[index][5] * self.plainSeq[index][6]
        return can_not_layout_enable

    def Get_Wait_Layout_Region(self, total_level):
        '''
        当提升最低水平线之后，该函数用于获得用于存放矩形的待填充区域
        :return:
        '''
        self.layout_component_information.sort(key=lambda x: x[3])  # 将存储信息的列表按矩形块的横坐标升序排列
        i = 0
        while i < len(self.layout_component_information):
            if self.layout_component_information[i][
                0] == self.min_line:  # 矩形块的左上角坐标所处位置有两种情况：在最低水平线上与在最低水平线之上
                if i == len(self.layout_component_information) - 1:  # 左上角坐标在最低水平线上又分:三种情况：1.从第k块之后可以找到左上角坐标在水平线之上的矩形块2：从第k块之后直到最后一块也没找到左上角坐标在水平线之上的3：第k块本身就处于排放的最后一块
                    self.plates[total_level][2] = self.boxLength - self.layout_component_information[i][3]
                    total_level = self.Get_New_Plate_Information(total_level, self.layout_component_information[i][3])
                for j in range(i + 1, len(self.layout_component_information)):
                    if self.layout_component_information[j][0] != self.min_line:
                        if i == 0 and self.layout_component_information[i][3] != 0:  # 第一块在水平线上且横坐标不为0的情况
                            self.plates[total_level][2] = self.layout_component_information[j][3]
                            total_level = self.Get_New_Plate_Information(total_level, 0)
                        else:
                            self.plates[total_level][2] = self.layout_component_information[j][3] - \
                                                         self.layout_component_information[i][3]
                            total_level = self.Get_New_Plate_Information(total_level,
                                                                         self.layout_component_information[i][3])
                        i = j - 1
                        break
                    elif j == len(self.layout_component_information) - 1 and self.layout_component_information[j][
                        0] == self.min_line:
                        if i == 0 and self.layout_component_information[i][3] != 0:  # 第一块在水平线上且横坐标不为0的情况
                            self.plates[total_level][2] = self.boxLength
                            total_level = self.Get_New_Plate_Information(total_level, 0)
                        else:
                            self.plates[total_level][2] = self.boxLength - \
                                                         self.layout_component_information[i][3]
                            total_level = self.Get_New_Plate_Information(total_level,
                                                                         self.layout_component_information[i][3])
                        i = j
                        break
            else:  # 第k块矩形块的左上角坐标在最低水平线之上，此种情况
                x_label_list = [x[3] for x in self.layout_component_information]  # 该列表存放的是矩形块的横坐标
                get_x_label = self.layout_component_information[i][3] + self.layout_component_information[i][2]  # 将矩形块的横坐标加上矩形块的宽，将其赋值于get_x_label，self.layout_component_information列表中左上角坐标与get_x_label有两种关系：get_x_label在列表中或不在列表中（或者第k块处于本身就处于排放的最后一块）：
                # 在列表中的情况又可分为第k+1块的左上角坐标在最低水平线上（讨论情况如上）、在最低水平线之上（不做任何处理）或第k+1块本身就处于排放的最后一块
                # 不在列表中的情况又可分为1：从第k块之后可以找到左上角坐标在最低水平线之上的矩形块2：从第k+1块之后直到最后一块也没找到左上角坐标在水平线之上的
                if i == len(self.layout_component_information) - 1:  # 第k块处于排放的最后一块
                    self.plates[total_level][2] = self.boxLength - get_x_label
                    total_level = self.Get_New_Plate_Information(total_level, get_x_label)
                elif get_x_label not in x_label_list:  # 不在列表中的情况
                    if i == 0 and self.layout_component_information[i][3] != 0:  # 第一块在水平线之上且横坐标不为0的情况（该列表中有多块门板）
                        self.plates[total_level][2] = self.layout_component_information[i][3]
                        total_level = self.Get_New_Plate_Information(total_level, 0)
                    for k in range(i + 1, len(self.layout_component_information)):
                        if self.layout_component_information[k][0] != self.min_line:
                            self.plates[total_level][2] = self.layout_component_information[k][3] - get_x_label
                            total_level = self.Get_New_Plate_Information(total_level, get_x_label)
                            i = k - 1
                            break
                        elif k == len(self.layout_component_information) - 1 and self.layout_component_information[k][0] == self.min_line:
                            self.plates[total_level][2] = self.boxLength - get_x_label
                            total_level = self.Get_New_Plate_Information(total_level, get_x_label)
                            i = k
                            break
                elif i == 0 and self.layout_component_information[i][3] != 0:  # 第一块在水平线之上且横坐标不为0的情况（该列表中有多块门板）
                    self.plates[total_level][2] = self.layout_component_information[i][3]
                    total_level = self.Get_New_Plate_Information(total_level, 0)
                elif self.layout_component_information[i + 1][
                    0] != self.min_line:  # 在列表中的情况，但第i+1块处于最低水平线之上，此时啥也不做
                    pass
                elif self.layout_component_information[i + 1][
                    0] == self.min_line:  # 在列表中的情况（第k+1块矩形的左上角坐标在最低水平线上）
                    if i == len(self.layout_component_information) - 2:  # 在列表中的情况(第k+1块处于排放的最后一块)
                        self.plates[total_level][2] = self.boxLength - get_x_label
                        total_level = self.Get_New_Plate_Information(total_level, get_x_label)
                        i += 1
                    for l in range(i + 2, len(self.layout_component_information)):
                        if self.layout_component_information[l][0] != self.min_line:  # 从第k块之后可以找到左上角坐标在最低水平线之上的矩形块
                            self.plates[total_level][2] = self.layout_component_information[l][3] - get_x_label
                            total_level = self.Get_New_Plate_Information(total_level, get_x_label)
                            i = l - 1
                            break
                        elif l == len(self.layout_component_information) - 1 and self.layout_component_information[l][
                            0] == self.min_line:  # 找到末尾了还是没找到左上角坐标在最低水平线之上的
                            self.plates[total_level][2] = self.boxLength - get_x_label
                            total_level = self.Get_New_Plate_Information(total_level, get_x_label)
                            i = l
                            break
            i += 1
        return total_level

    def Get_New_Plate_Information(self, total_level, x_label):
        self.plates[total_level][0] = x_label
        self.plates[total_level][1] = self.min_line
        self.plates[total_level][3] = self.left_wait_layout_width
        total_level += 1
        return total_level

    def Lift_Level_Line(self):
        '''
        该函数用于提升最低水平线
        :return:
        '''
        self.layout_component_information = []  # 该列表存放的是矩形块左上角坐标高于最低水平线的矩形信息（左上角坐标，矩形块放入self.plate的序号，矩形的宽度以及矩形的横坐标）
        for i in range(len(self.plates)):
            if self.plates[i][10] != 0:
                if self.plates[i][1] + self.plates[i][4] > self.min_line:  # 矩形块的左上角坐标大于最低水平线
                    temporary_list = [self.plates[i][1] + self.plates[i][4], i, self.plates[i][5], self.plates[i][0]]
                    self.layout_component_information.append(temporary_list)
        if self.layout_component_information != []:
            self.layout_component_information.sort(key=lambda x: x[0])  # 将self.layout_component_information列表中的左上角坐标一列按升序排序，以便提升最低水平线
            for j in range(len(self.layout_component_information)):
                if self.layout_component_information[j][0] != self.min_line:
                    self.min_line = self.layout_component_information[j][0]
                    break