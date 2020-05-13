# coding=utf-8
# decode for GA to place object by heuristic packing algorithm
# gs by 2020-04-15

import numpy as np
from copy import deepcopy
from prepare_data import processor
from collections import Counter
from confs.geatpy_conf import *

# 数据直接在此处加载，为了减少在aimFunc()处不断传递参数加载所耗费的时间
DATASET = processor(DATA_DIR, SUBSET, RECT_BOX_ID)
RECTARRAY = DATASET['rect'][TEST]
BOX = DATASET['box'][TEST]
SORT = DATASET['sort_seq'][TEST]
N = len(RECTARRAY)


class Rectangle:  # 矩形类，记录在(lbx, lby)放置好矩形(length, width)后的各部分信息
    # __slots__限制类的属性绑定，Rectangle类只能绑定元组中的几个属性，否则抛出AttributeError异常
    # __slots__定义的属性仅对当前类起作用，对继承的子类是不起作用的
    __slots__ = ('length', 'width', 'lbx', 'lby', 'rid', 'rotate')

    def __init__(self, lbx, lby, length, width, rid, rotate):
        """
        Args:
            lbx -- type: int  放置矩形的左下角x坐标
            lby -- type:int   放置矩形的左下角y坐标
            length -- type:int  矩形长度    规则：人正对着矩形，其上边沿或下边沿长度为矩形长度，左边沿或右边沿长度为矩形宽度
            width -- type:int  矩形宽度     有时会讲高度和宽度，则依据上面规则，此时length=宽度，width=高度
            rid -- type: int/str    矩形id
            rotate -- type:int  放置矩形是否旋转，其值为0 or 1
        """
        assert length > 0 and width > 0 and lbx >= 0 and lby >= 0
        if rotate not in (0, 1):
            raise AttributeError("The rotate must be 0 or 1.")
        self.length = length
        self.width = width
        self.lbx = lbx
        self.lby = lby
        self.rid = rid
        self.rotate = rotate

    def __repr__(self):  # __repr__方法可以描述类
        return "R({}, {}, {}, {}, {}, {})".format(self.lbx, self.lby, self.length, self.width, self.rid, self.rotate)

    @property
    def bottom(self):
        """
        Rectangle bottom edge y coordinate
        """
        return self.lby

    @property
    def top(self):
        """
        Rectangle top edge y coordinate
        """
        if self.rotate == 0:
            return self.lby + self.width
        else:
            return self.lby + self.length

    @property
    def left(self):
        """
        Rectangle left edge x coordinate
        """
        return self.lbx

    @property
    def right(self):
        """
        Rectangle right edge x coordinate
        """
        if self.rotate == 0:
            return self.lbx + self.length
        else:
            return self.lbx + self.width

    @property
    def lt_corner(self):
        """
        Rectangle left-top corner coordinate
        """
        return [self.left, self.top]

    @property
    def rt_corner(self):
        """
        Rectangle right-top corner coordinate
        """
        return [self.right, self.top]

    @property
    def rb_corner(self):
        """
        Rectangle right-bottom corner coordinate
        """
        return [self.right, self.bottom]

    @property
    def lb_corner(self):
        """
        Rectangle left-bottom corner coordinate
        """
        return [self.left, self.bottom]


class PlainLHLA2D:  # 定位算法：启发式最低水平线，用于Geatpy使用
    def __init__(self, codes):
        """
        args:
            codes -- type:ndarray   subtype:int dim:(2n,)   n为矩形件数量
                  -- 前n为次序编码，表示放置次序；后n为0,1离散编码，表示旋转状态
            rectArray -- type:ndarray   subtype:int dim:(n,[3,4])  width,height,thick,[id]  []表示可选
            box -- type:ndarray   subtype:int dim:(3,) or (4,)  width,height,thick,[id]  []表示可选
        """
        self.codes = deepcopy(codes).astype(dtype=np.int)
        self.rectArray = deepcopy(RECTARRAY)  # 载入矩形数据
        self.box = deepcopy(BOX)  # 载入容器数据
        self.thick = self.rectArray[0][2]  # 矩形厚度

        self.itemNum = N  # 矩形件数量
        self.plainSeq = self.codes[:self.itemNum]  # 放置顺序序列信息
        self.orientSeq = self.codes[self.itemNum:]  # 放置方向序列信息
        self.orientSeqBak = deepcopy(self.orientSeq)
        self.rectArraySorted = np.zeros(shape=self.rectArray.shape, dtype=np.int)
        for i, v in enumerate(self.plainSeq):  # 将放置序列与矩形件信息对应起来
            self.rectArraySorted[i] = self.rectArray[v-1]
        self.boxLength, self.boxWidth, self.boxHeight, self.boxId = self.box

    def initLayer(self):
        """
        args:
            plate_temp -- type:list dim:(n,15)
                       -- [x(0),y(1),areaLen(2),areaWidth(3),width(4),height(5),thick(6),rectId(7),
                       rotate(8),layerNum(9),boxLen(10),boxWidth(11),boxHeight(12),boxId(13),areaState(14)]
                       -- thick, layerNum, boxHeight is compatible 2.5D packing
        """
        # 最低水平线
        self.lowest_level_line = 0
        # 用于暂存所排部件的过程信息
        self.plate_temp = [[0 for col in range(15)] for row in range(self.itemNum * 10)]
        self.plate_temp[0] = [0, 0, self.boxLength, self.boxWidth, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,0]
        # 该列表存放的是矩形块左上角坐标高于最低水平线的信息，用于提升最低水平线
        self.layout_component_info = []

    def put_main(self):
        current_layer_num = 0  # 记录当前层数，进行层数限制
        plates = []  # 存放打包后的结果信息
        while len(self.plainSeq):  # 两个结束条件：1.这批部件被放置完了；2.放置部件总厚度超过纸箱高度
            if (current_layer_num + 1) * self.thick > self.boxHeight:
                break
            current_layer_num = self.put_each_layer(current_layer_num)
            #获取每层装箱方案
            for plate_temp_item in self.plate_temp:
                if plate_temp_item[10] != 0:  # 取放好的板件
                    plate_temp_item[9] = current_layer_num  # 记录当前部件的层编号
                    plates.append(plate_temp_item)
                if plate_temp_item == [0]*15:
                    break
        target = 0
        for i, v in enumerate(plates):
            target = target+v[4]*v[5]*v[6]
        volRate = target / (self.boxWidth*self.boxLength*self.boxHeight)  # self.boxHeight=thick=1为2D面积利用率或填充率，此处考虑2.5D兼容问题

        return volRate, plates

    def put_each_layer(self, current_layer_num):
        """
        该方法用于将每一层部件放好
        :param current_layer_num: 待放好的层编号
        :return: 已放好的层编号
        """
        self.initLayer()  # 放好一层后，需要把参数初始化
        current_each_layer_plate_num = 0  # 记录每层的块数，进行块数限制
        self.plate_specification_height = self.boxLength
        i = 0  # 可以理解为当前放好的块数编号
        j = 1  # 可以理解为当前水平线上，待放好下一块的块数编号
        while i < j:
            self.resortArea()
            wait_fill_area_long = self.plate_temp[i][2]
            wait_fill_area_width = self.plate_temp[i][3]
            if len(self.orientSeq) == 0:
                break
            for k in range(self.itemNum):
                if wait_fill_area_long != 0 and wait_fill_area_width != 0:
                    if self.orientSeq[k] == 1:  # 方向旋转，调换长宽
                        self.rectArraySorted[k][0], self.rectArraySorted[k][1]=self.rectArraySorted[k][1],self.rectArraySorted[k][0]
                        self.orientSeq[k] = 0  # 表示已经旋转过了
                    if wait_fill_area_long >= self.rectArraySorted[k][0] and wait_fill_area_width >= self.rectArraySorted[k][1]:  # 能放进待填充区域
                        self.can_layout(i, j, k)
                        j += 1
                        current_each_layer_plate_num += 1
                        self.rectArraySorted = np.delete(self.rectArraySorted,[k],axis=0)
                        self.orientSeq = np.delete(self.orientSeq,[k], axis=0)
                        self.orientSeqBak = np.delete(self.orientSeqBak, [k], axis=0)
                        self.plainSeq = np.delete(self.plainSeq, [k], axis=0)
                    else:
                        i = j-1
                    break
            i += 1
            if i == j:
                self.improve_lowest_level_line()  # 提升最低水平线
                if len(self.layout_component_info) == 0:  # self.layout_component_info == []
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
            if v[1] == self.lowest_level_line and v[7] == 0:
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
        self.plate_temp[current_level][4] = self.rectArraySorted[index][0]  # 记录width
        self.plate_temp[current_level][5] = self.rectArraySorted[index][1]  # 记录height
        self.plate_temp[current_level][6] = self.rectArraySorted[index][2]  # 记录thick
        self.plate_temp[current_level][7] = self.rectArraySorted[index][3]  # 记录rectId

        self.plate_temp[current_level][8] = self.orientSeqBak[index]  #记录是否旋转信息
        #给出当前货物所处的纸箱信息
        self.plate_temp[current_level][10] = self.boxLength
        self.plate_temp[current_level][11] = self.boxWidth
        self.plate_temp[current_level][12] = self.boxHeight
        self.plate_temp[current_level][13] = self.boxId
        #给出放置后的lowestLine上的右端坐标和填充区域长宽
        self.plate_temp[current_level_next][0] = self.plate_temp[current_level][0] + self.rectArraySorted[index][0]
        self.plate_temp[current_level_next][1] = self.plate_temp[current_level][1]
        self.plate_temp[current_level_next][2] = self.plate_temp[current_level][2] - self.rectArraySorted[index][0]
        # TODO:将第一个矩形40x16横放在40x40的容器上，此处的self.plate_temp[current_level_next][3]计算不对，目前不影响放置
        self.plate_temp[current_level_next][3] = self.plate_temp[current_level][3]
        # if self.plate_temp[current_level+1][1] == self.lowest_level_line and \
        #         self.plate_temp[current_level_next][1] == self.lowest_level_line and self.plate_temp[current_level+1][4] == 0:
        #     if self.plate_temp[current_level+1][2] > self.plate_temp[current_level_next][2]:
        #         self.plate_temp[current_level + 1], self.plate_temp[current_level_next] = \
        #             self.plate_temp[current_level_next], self.plate_temp[current_level + 1]

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
            if self.plate_temp[i][7] != 0:  # 滤除没有放部件的row
                if self.plate_temp[i][1] + self.plate_temp[i][5] > self.lowest_level_line:  # 左上角坐标的y大于最低水平线，滤除最低水平线上和最低水平线之下已放置好的部件
                    self.layout_component_info.append(
                        [self.plate_temp[i][0], self.plate_temp[i][1] + self.plate_temp[i][5], self.plate_temp[i][8],
                         self.plate_temp[i][4]])
        if self.layout_component_info:  # 当该列表不为空的时候才执行,等价于self.layout_component_info！= []
            self.layout_component_info.sort(key=lambda x: x[1])  # 按照y进行升序排列
            for j in range(len(self.layout_component_info)):
                if self.layout_component_info[j][1] != self.lowest_level_line:
                    self.lowest_level_line = self.layout_component_info[j][1]  # 提升最低水平线
                    self.underLineArea()
                    break

    def underLineArea(self):
        for i, v in enumerate(self.plate_temp):
            if v == [0]*15:
                break
            if v[7] == 0 and v[2]!=0 and v[3]!=0 and self.lowest_level_line>v[1]:  # 表示该区域没有放部件，并且区域size不为0，形成空腔区域
                v[3] = self.lowest_level_line - v[1]  # 更新区域高度方向范围
                v[14] = 1 # 更新区域状态为1，表示为水平线之下的空腔区域

    def get_new_wait_fill_region(self, current_level_next):
        self.layout_component_info.sort(key=lambda x: x[0])  # 按照x进行升序排列
        i = 0
        while i < len(self.layout_component_info):
            # 上一最低水平线所放矩形块的左上角坐标所处位置有两种情况：1.在最低水平线上；2.在最低水平线之上
            if self.layout_component_info[i][1] == self.lowest_level_line:  # 在最低水平线上
                if i == len(self.layout_component_info) - 1:
                    self.plate_temp[current_level_next][2] = self.plate_specification_height - \
                                                             self.layout_component_info[i][0]
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
                            self.plate_temp[current_level_next][2] = self.plate_specification_height - \
                                                                     self.layout_component_info[i][0]
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


class ImprovementLHLA2D(PlainLHLA2D):  # TODO: 排放时检查水平线以下的空腔区域是否可以放置
    def __init__(self, codes):
        """
        规则：人正对着矩形，其上边沿或下边沿长度为矩形长度length，左边沿或右边沿长度为矩形宽度width
        有时会讲高度和宽度，则依据上面规则，此时length=宽度，width=高度
        容器的规则与矩形一样
        args:
            codes -- type:ndarray   subtype:int dim:(2n,)   n为矩形件数量
                  -- 前n为次序编码，表示放置次序；后n为0,1离散编码，表示旋转状态
            rectArray -- type:ndarray   subtype:int dim:(n,[3,4])  length,width,thick,[id]  []表示可选
            box -- type:ndarray   subtype:int dim:(3,) or (4,)  length,width,thick,[id]  []表示可选
        """
        super(ImprovementLHLA2D, self).__init__(codes)

    def run(self):
        curLayer = 0  # 记录当前层数
        plates = []  # 存放装箱后的结果信息
        while len(self.plainSeq):  # 两个结束条件：1.这批部件被放置完了；2.放置部件总厚度超过纸箱高度
            if (curLayer + 1) * self.thick > self.boxHeight:
                break
            curLayer = self.putPerLayer(curLayer)
            for v in self.platesTemp:
                if v == [0] * len(v):  # 减少时间
                    break
                if v[14] == 1:  # 放置好的矩形
                    plates.append(v)
        target = 0
        putedOrientSeq = []
        for i, v in enumerate(plates):
            target = target + v[4] * v[5] * v[6]
            putedOrientSeq.append(v[8])
        putedOrientSeq = putedOrientSeq + list(self.orientSeqBak)[len(putedOrientSeq):]
        # self.boxHeight=thick=1为2D面积利用率或填充率，此处考虑2.5D兼容问题
        volRate = target / (self.boxWidth * self.boxLength * self.boxHeight)
        return volRate, plates, putedOrientSeq

    def initLayer(self):
        """
        args:
            platesTemp -- type:list dim:(n,15)
                       -- [x(0),y(1),areaLen(2),areaWidth(3),width(4),height(5),thick(6),rectId(7),
                       rotate(8),layerNum(9),boxLen(10),boxWidth(11),boxHeight(12),boxId(13),areaState(14)]
                       -- thick, layerNum, boxHeight is compatible 2.5D packing
        """
        # 最低水平线
        self.minLine = 0
        # 用于暂存所排部件的过程信息
        self.platesTemp = [[0 for col in range(15)] for row in range(self.itemNum * 3)]
        self.platesTemp[0][2], self.platesTemp[0][3] = self.boxLength, self.boxWidth
        # 该列表存放的是矩形块左上角坐标高于最低水平线的信息，用于提升最低水平线
        self.infoArea = []

    def putPerLayer(self, curLayer):
        self.initLayer()  # 放好一层后，需要把参数初始化
        # self.plateLength , self.plateWidth放置过程可能会变，self.boxLength, self.boxWidth始终不变
        self.plateLength , self.plateWidth = self.boxLength, self.boxWidth
        i = 0  # 可以理解为当前放好的块数编号
        j = 1  # 可以理解为当前水平线上，待放好下一块的块数编号
        m = 0
        n = 1
        while i < j:
            # for idx, val in enumerate(self.platesTemp):
            #     if val == [0] * len(val):
            #         break
            #     if val[14] == 2:  # 为空腔区域
            #         m = idx
            #         m, n = self.tryPut(m, m+1, self.platesTemp[m][2], self.platesTemp[m][3])  # TODO:继续
            self.resortArea()
            areaLength = self.platesTemp[i][2]
            areaWidth = self.platesTemp[i][3]
            if len(self.orientSeq) == 0:  # 该层需要放的矩形已经放完
                break
            if areaLength != 0 and areaWidth != 0:
                i, j = self.tryPut(i, j, areaLength, areaWidth)
            i = i + 1
            if i == j:
                self.liftMinLine()  # 提升最低水平线
                if len(self.infoArea) == 0:
                    break
                j = self.liftedNewArea(j)  # 提升最低水平线后产生的新填充区域
        curLayer = curLayer + 1
        return curLayer

    def tryPut(self, i, j, areaLength, areaWidth):
        for k in range(self.itemNum):
            if self.orientSeq[k] == 0 and self.rectArraySorted[k][0] <= areaLength and \
                    self.rectArraySorted[k][1] <= areaWidth:  # 不旋转
                self.layout(i, j, k)
                j = j + 1
                self.rectArraySorted = np.delete(self.rectArraySorted, [k], axis=0)
                self.orientSeq = np.delete(self.orientSeq, [k], axis=0)
                self.plainSeq = np.delete(self.plainSeq, [k], axis=0)
            elif self.orientSeq[k] == 1 and self.rectArraySorted[k][0] <= areaWidth and \
                    self.rectArraySorted[k][1] <= areaLength:  # 旋转90度
                self.layout(i, j, k)
                j = j + 1
                self.rectArraySorted = np.delete(self.rectArraySorted, [k], axis=0)
                self.orientSeq = np.delete(self.orientSeq, [k], axis=0)
                self.plainSeq = np.delete(self.plainSeq, [k], axis=0)

            elif self.orientSeq[k] == 0 and self.rectArraySorted[k][0] <= areaWidth and \
                    self.rectArraySorted[k][1] <= areaLength:  # 不旋转，但按照给定的放又放不进去，旋转下，试试是否放进去
                self.orientSeq[k] = 1  # 改变旋转方向
                self.layout(i, j, k)
                j = j + 1
                self.rectArraySorted = np.delete(self.rectArraySorted, [k], axis=0)
                self.orientSeq = np.delete(self.orientSeq, [k], axis=0)
                self.plainSeq = np.delete(self.plainSeq, [k], axis=0)
            elif self.orientSeq[k] == 1 and self.rectArraySorted[k][0] <= areaLength and \
                    self.rectArraySorted[k][1] <= areaWidth:  # 旋转90度，但按照给定的放又放不进去，再旋转下，试试是否放进去
                self.orientSeq[k] = 0  # 改变旋转方向
                self.layout(i, j, k)
                j = j + 1
                self.rectArraySorted = np.delete(self.rectArraySorted, [k], axis=0)
                self.orientSeq = np.delete(self.orientSeq, [k], axis=0)
                self.plainSeq = np.delete(self.plainSeq, [k], axis=0)

            else:
                i = j - 1
            break
        return i, j

    def resortArea(self):
        tmpList = []
        sortedTmpList = []
        for i, v in enumerate(self.platesTemp):
            if v == [0] * len(v):  # 减少时间
                break
            if v[1] == self.minLine and v[14] == 0:
                tmpList.append(i)
                sortedTmpList.append(v)
        if len(tmpList) != 0:
            sortedTmpList.sort(key=lambda x: x[0])
            for idx, val in enumerate(sortedTmpList):
                self.platesTemp[tmpList[idx]] = val

    def liftMinLine(self):
        """
        self.infoArea列表：
        [x, y, is_rotate, x_size]
        x,y:部件左上角坐标
        is_rotate：部件排板时，length,width需要是否旋转，0为不旋转，1为旋转
        x_size:与x轴平行的部件的长度
        """
        self.infoArea = []  # 使用时先初始化该列表
        for i in range(len(self.platesTemp)):
            if self.platesTemp[i] == [0] * len(self.platesTemp[i]):  # 减少时间
                break
            if self.platesTemp[i][14] == 1:  # 计算在提升前self.minLine上已放矩形信息
                if self.platesTemp[i][8] == 0 and self.platesTemp[i][1] + self.platesTemp[i][5] > self.minLine:  # 不旋转
                    self.infoArea.append([self.platesTemp[i][0], self.platesTemp[i][1] + self.platesTemp[i][5],
                                          self.platesTemp[i][8], self.platesTemp[i][4]])
                elif self.platesTemp[i][8] == 1 and self.platesTemp[i][1] + self.platesTemp[i][4] > self.minLine:  # 旋转
                    self.infoArea.append([self.platesTemp[i][0], self.platesTemp[i][1] + self.platesTemp[i][4],
                                          self.platesTemp[i][8], self.platesTemp[i][5]])
        if len(self.infoArea) != 0:
            self.infoArea.sort(key=lambda x: x[1])  # 按照y进行升序排列
            for j in range(len(self.infoArea)):
                if self.infoArea[j][1] != self.minLine:
                    self.minLine = self.infoArea[j][1]  # 提升最低水平线
                    # self.updateUnderMinLineArea()
                    break

    def updateUnderMinLineArea(self):
        for i, v in enumerate(self.platesTemp):
            if v == [0] * len(self.platesTemp[i]):  # 减少时间
                break
            # 表示该区域没有放部件，并且区域size不为0，形成空腔区域
            if v[14] == 0 and v[2] != 0 and v[3] != 0 and self.minLine > v[1]:
                v[3] = self.minLine - v[1]  # 更新区域高度方向范围
                v[14] = 2  # 更新区域状态为2，表示为水平线之下的空腔区域

    def liftedNewArea(self, curNext):
        self.infoArea.sort(key=lambda x: x[0])  # 按照坐标x进行升序排列
        i = 0
        while i < len(self.infoArea):
            # 2种情况：1.已放矩形的上边沿top在self.minLine上  2.已放矩形的上边沿top在self.minLine之上
            if self.infoArea[i][1] == self.minLine:  # 矩形top在提升后的水平线上
                if i == len(self.infoArea) - 1:
                    # 矩形i的top在self.minLine上，并且是self.infoArea中的最右边那个矩形(包含处理只有一个矩形top在self.minLine上的情况)
                    self.platesTemp[curNext][2] = self.plateLength - self.platesTemp[i][0]
                    curNext = self.getNewArea(curNext, self.platesTemp[i][0])
                for j in range(i + 1, len(self.infoArea)):  # 矩形i的top在self.minLine上，处理i+1(后面那块)到最右边那个矩形
                    if self.infoArea[j][1] != self.minLine:  # 矩形j的top不在self.minLine上
                        if i == 0 and self.infoArea[j][0] != 0:  # 最左边那个矩形top在self.minLine上，矩形j没有靠容器左边缘
                            self.platesTemp[curNext][2] = self.infoArea[j][0]
                            curNext = self.getNewArea(curNext, 0)
                        else:
                            self.platesTemp[curNext][2] = self.infoArea[j][0] - self.infoArea[i][0]
                            curNext = self.getNewArea(curNext, self.infoArea[i][0])
                        i = j - 1
                        break
                    elif j == len(self.infoArea) - 1 and self.infoArea[j][1] == self.minLine:
                        # 最右边那个矩形top在self.minLine上
                        if i == 0 and self.infoArea[j][0] != 0:
                            self.platesTemp[curNext][2] = self.plateLength
                            curNext = self.getNewArea(curNext, 0)
                        else:
                            self.platesTemp[curNext][2] = self.plateLength - self.infoArea[i][0]
                            curNext = self.getNewArea(curNext, self.infoArea[i][0])
                        i = j
                        break
            else:  # 矩形top在提升后的水平线之上
                xList = [v[0] for v in self.infoArea]
                x = self.infoArea[i][0] + self.infoArea[i][3]
                if i == len(self.infoArea) - 1:
                    self.platesTemp[curNext][2] = self.plateLength - x
                    curNext = self.getNewArea(curNext, x)
                elif x not in xList:
                    if i == 0 and self.infoArea[i][0] != 0:
                        self.platesTemp[curNext][2] = self.infoArea[i][0]
                        curNext = self.getNewArea(curNext, 0)
                    for k in range(i + 1, len(self.infoArea)):
                        if self.infoArea[k][1] != self.minLine:
                            self.platesTemp[curNext][2] = self.infoArea[k][0] - x
                            curNext = self.getNewArea(curNext, x)
                            i = k - 1
                            break
                        elif k == len(self.infoArea) - 1 and self.infoArea[k][1] == self.minLine:
                            self.platesTemp[curNext][2] = self.plateLength - x
                            curNext = self.getNewArea(curNext, x)
                            i = k
                            break
                elif i == 0 and self.infoArea[i][0] != 0:
                    self.platesTemp[curNext][2] = self.infoArea[i][0]
                    curNext = self.getNewArea(curNext, x)
                elif self.infoArea[i + 1][1] != self.minLine:
                    pass
                elif self.infoArea[i + 1][1] == self.minLine:
                    if i == len(self.infoArea) - 2:
                        self.platesTemp[curNext][2] = self.plateLength - x
                        curNext = self.getNewArea(curNext, x)
                        i = i + 1
                    for r in range(i + 2, len(self.infoArea)):
                        if self.infoArea[r][1] != self.minLine:
                            self.platesTemp[curNext][2] = self.infoArea[r][0] - x
                            curNext = self.getNewArea(curNext, x)
                            i = r - 1
                            break
                        elif r == len(self.infoArea) - 1 and self.infoArea[r][1] == self.minLine:
                            self.platesTemp[curNext][2] = self.plateLength - x
                            curNext = self.getNewArea(curNext, x)
                            i = r
                            break
            i = i + 1
        return curNext

    def layout(self, cur, curNext, k):
        """
        1.记录当前最低水平线上放置好的部件尺寸与部件号
        2.产生当前最低水平线上下一个待填充区域的坐标与大小
        """
        #  放置货物信息
        self.platesTemp[cur][4] = self.rectArraySorted[k][0]  # 记录放置矩形的length
        self.platesTemp[cur][5] = self.rectArraySorted[k][1]  # 记录放置矩形的width
        self.platesTemp[cur][6] = self.rectArraySorted[k][2]  # 记录放置矩形的thick
        self.platesTemp[cur][7] = self.rectArraySorted[k][3]  # 记录放置矩形的rectId
        self.platesTemp[cur][8] = self.orientSeq[k]  # 记录放置矩形的旋转状态

        # 放置的容器信息
        self.platesTemp[cur][10] = self.boxLength  # 记录放置矩形容器的length
        self.platesTemp[cur][11] = self.boxWidth  # 记录放置矩形容器的width
        self.platesTemp[cur][12] = self.boxHeight  # 记录放置矩形容器的height
        self.platesTemp[cur][13] = self.boxId  # 记录放置矩形容器的boxId

        self.platesTemp[cur][14] = 1  # 记录该区域已经被放置的状态

        # 放置后的minLine上的右端坐标和填充区域长宽 --> 产生填充区域
        if self.platesTemp[cur][8] == 0:  # 不旋转，矩形长对应区域长
            self.platesTemp[curNext][0] = self.platesTemp[cur][0] + self.rectArraySorted[k][0]  # 新区域x坐标
            self.platesTemp[curNext][2] = self.platesTemp[cur][2] - self.rectArraySorted[k][0]  # 新区域length
        else:
            self.platesTemp[curNext][0] = self.platesTemp[cur][0] + self.rectArraySorted[k][1]
            self.platesTemp[curNext][2] = self.platesTemp[cur][2] - self.rectArraySorted[k][1]
        self.platesTemp[curNext][1] = self.platesTemp[cur][1]  # 新区域y坐标
        self.platesTemp[curNext][3] = self.platesTemp[cur][3]  # 新区域width

    def getNewArea(self, curNext, x):
        self.platesTemp[curNext][0] = x
        self.platesTemp[curNext][1] = self.minLine
        self.platesTemp[curNext][3] = self.plateWidth - self.minLine
        curNext = curNext + 1
        return curNext


class NewPlainLHLA2D:
    def __init__(self, codes):
        """
        规则：人正对着矩形，其上边沿或下边沿长度为矩形长度length，左边沿或右边沿长度为矩形宽度width
        有时会讲高度和宽度，则依据上面规则，此时length=宽度，width=高度
        容器的规则与矩形一样
        args:
            codes -- type:ndarray   subtype:int dim:(2n,)   n为矩形件数量
                  -- 前n为次序编码，表示放置次序；后n为0,1离散编码，表示旋转状态
            rectArray -- type:ndarray   subtype:int dim:(n,[3,4])  length,width,thick,[id]  []表示可选
            box -- type:ndarray   subtype:int dim:(3,) or (4,)  length,width,thick,[id]  []表示可选
        """
        self.codes = deepcopy(codes).astype(dtype=np.int)
        self.rectArray = deepcopy(RECTARRAY)  # 载入矩形数据
        self.box = deepcopy(BOX)  # 载入容器数据
        self.thick = self.rectArray[0][2]  # 矩形厚度

        self.itemNum = N  # 矩形件数量
        self.plainSeq = self.codes[:self.itemNum]  # 放置顺序序列信息
        self.orientSeq = self.codes[self.itemNum:]  # 放置方向序列信息
        self.rectArraySorted = np.zeros(shape=self.rectArray.shape, dtype=np.int)
        for i, v in enumerate(self.plainSeq):  # 将放置序列与矩形件信息对应起来
            self.rectArraySorted[i] = self.rectArray[v-1]
        self.boxLength, self.boxWidth, self.boxHeight, self.boxId = self.box

    def run(self):
        curLayer = 0  # 记录当前层数
        plates = []  # 存放打包后的结果信息
        while len(self.plainSeq):  # 两个结束条件：1.这批部件被放置完了；2.放置部件总厚度超过纸箱高度
            if (curLayer + 1) * self.thick > self.boxHeight:
                break
            curLayer = self.putPerLayer(curLayer)
        target = 0
        for i, v in enumerate(plates):
            target = target + v[4] * v[5] * v[6]
        # self.boxHeight=thick=1为2D面积利用率或填充率，此处考虑2.5D兼容问题
        volRate = target / (self.boxWidth * self.boxLength * self.boxHeight)
        return volRate, plates

    def putPerLayer(self, curLayer):
        # 放置的时候，只记录旋转状态，不改变矩形length, width
        self.minLine = 0
        self.platesTemp = [[0, 0, self.boxLength, self.boxWidth, 0, 0]]
        i = 0
        while self.minLine <= self.boxWidth:  # 两个结束条件：1.最低水平线超过容器高度结束该层放置；2.仅放一层时，矩形放好了
            for idx, val in enumerate(self.rectArraySorted):
                self.areaLength, self.areaWidth = self.platesTemp[i][2], self.platesTemp[i][3]
                if self.orientSeq[idx] == 0 and val[0] <= self.areaLength and val[1] <= self.areaWidth:
                    rect = Rectangle(self.platesTemp[i][0], self.platesTemp[i][1],
                                     val[0], val[1], val[3], self.orientSeq[idx])
                    self.platesTemp[i][4] = rect
                    self.platesTemp[i][5] = 1  # 记录该矩形放置好了
                    self.updateArea(rect)
                    i = i + 1
                elif self.orientSeq[idx] == 1 and val[0] <= self.areaWidth and val[1] <= self.areaLength:
                    rect = Rectangle(self.platesTemp[i][0], self.platesTemp[i][1],
                                     val[0], val[1], val[3], self.orientSeq[idx])
                    self.platesTemp[i][4] = rect
                    self.platesTemp[i][5] = 1  # 记录该矩形放置好了
                    self.updateArea(rect)
                    i = i + 1  # 加入一个新区域
                else:
                    self.liftMinLine()

    def updateArea(self, rect):
        if rect.rotate == 0:
            putedAreaLength = self.areaLength - rect.length
        else:
            putedAreaLength = self.areaLength - rect.width
        putedAreaWidth = self.areaWidth  # 此时还在水平线上
        self.platesTemp.append([rect.rb_corner[0], rect.rb_corner[1], putedAreaLength, putedAreaWidth, 0, 0])

    def liftMinLine(self):
        lineDict = {}
        for idx, rect in enumerate(self.platesTemp):
            if rect[1] == self.minLine and rect[5] == 1:  # 已放在minLine上的矩形
                lineDict[idx] = rect[4].top
        self.minLine = min(lineDict.values())  # 提升minLine
        # 假设minLine=7，分3种情况：1.一个7；2.两个以上连续7；3.两个以上非连续7；2与3的情况组合也是有的  TODO：情况有点多
        minLineNum = list(lineDict.values()).count(self.minLine)
        # if minLineNum == 1:  # 分2种情况：1.矩形右边无矩形高过minLine；2.矩形右边有矩形高过minLine
        for k, v in lineDict.items():
            if v == self.minLine:
                print()
