#coding=utf-8
import numpy as np
import random
import copy
import re
import math
import matplotlib.pyplot as plt
from collections import Counter
from MYSQL.MysqlHelper import MysqlPool
from confs.Setting import *
from Layout import HeuristicPut
from ThreadHelper import LoopTimer
from DataSet import Cdata,Cbox,Ndata,Nbox
import time,os,datetime,sys

class GetData:
    """
    从MySQL数据库中获取组件、部件、纸箱信息的类
    """
    def __init__(self, log=None):
        self.log = log
        self.mysql = MysqlPool()

    def is_needing_pack(self):
        """
        查询组件表单是否有需要打包的组件
        :return: None(没有需要打包的组件) or Sec_id(组件号)
        """
        sql = "SELECT `Index`, `Sec_id` FROM `order_section_online` WHERE `Package_state`=0"
        section_info = self.mysql.do_sql_one(sql)
        if section_info is None:  # 没有需要打包的组件
            return None
        else:
            return section_info[1]

    def get_part_info(self):
        """
        获取部件表单信息(原始数据)
        :return: None(没有组件或部件信息) or part_lists(部件二维列表信息)
        """
        sec_id = self.is_needing_pack()
        part_lists = []
        if sec_id:
            sql = "SELECT `Contract_id`, `Order_id`, `Sec_id`, `Part_id`, `Door_type`, `Door_height`, `Door_width`, " \
                  "`Door_thick`, `Package_state`, `Element_type_id` FROM `order_part_online` WHERE `Sec_id` = '%s'" % \
                  sec_id
            part_info = self.mysql.do_sql(sql)
            if part_info is None:  # 部件表单无部件信息
                return None, part_lists
            else:
                for i in range(len(part_info)):
                    part_lists.append(list(part_info[i]))
                return sec_id, part_lists
        else:
            return None, part_lists

    def get_box_info(self):
        """
        获取纸箱表单信息(原始数据)
        :return: None(没有纸箱信息) or box_lists(纸箱二维列表信息)
        """
        box_lists = []
        sql = "SELECT `Box_type`, `Box_long`, `Box_short`, `Box_height`,`Box_volume`,`Box_weight`,`Box_num` FROM `equipment_package_box` WHERE " \
              "`State`=5"
        box_info = self.mysql.do_sql(sql)
        if box_info is None:
            return None
        else:
            for i in range(len(box_info)):
                box_lists.append(list(box_info[i]))
            return box_lists

class Util:
    def partWeightAreaVolume(self,part_lists):
        """
        计算部件重量和面积
        :param part_lists: 原始部件列表信息
        :return: 向part_lists列表中添加weight和area元素后的列表return_part_lists or None
        """
        # weightLists=[1027,1495,935,1038,1250,933,1145,1655,1043,885,1287,822,867,1165,1210,925]
        # i = 0
        # if isinstance(part_lists, list):
        #     if len(part_lists) != 0:
        #         for part_item in part_lists:
        #             area = part_item[part_length_index] * part_item[part_width_index]
        #             volume = area * part_item[part_thickness_index] * 0.001  # 单位是立方厘米
        #             area = round(area * 10 ** (-2), 6)  # 保留6位小数，以平方厘米为单位
        #             weight = part_item[part_length_index] * part_item[part_width_index] * part_item[
        #                 part_thickness_index] * BaseMaterialDensity * 10 ** (-9)
        #             if part_item[part_id_index]=='95O1S1':#调试
        #                 weight = weightLists[i]  # 保留6位小数，以kg为单位
        #                 i+=1
        #             weight=round(weight,2)
        #             part_item.append(area)
        #             part_item.append(volume)
        #             part_item.append(weight)
        #         return part_lists
        """
            计算部件重量和面积
            :param part_lists: 原始部件列表信息
            :return: 向part_lists列表中添加weight和area元素后的列表return_part_lists or None
            """
        if isinstance(part_lists, list):
            if len(part_lists) != 0:
                return_part_lists = part_lists[:]
                for part_item in return_part_lists:
                    area = part_item[part_length_index] * part_item[part_width_index]
                    volume = area * part_item[part_thickness_index]  # 单位是立方毫米
                    weight = 1
                    # area = round(area * 10 ** (-6), 6)  # 保留6位小数，以平方米为单位
                    # weight = part_item[part_length_index] * part_item[part_width_index] * part_item[part_thickness_index] * BaseMaterialDensity * 10 ** (-9)
                    # weight = round(weight, 6)  # 保留6位小数，以kg为单位
                    part_item.append(area)
                    part_item.append(volume)
                    part_item.append(weight)
                return return_part_lists

    def getTwoDimensionListIndex(self, L, value):
        """获得二维列表某个值的一维索引值的一种方法"""
        if isinstance(L, list):
            for i in range(len(L)):
                for j in range(len(L[i])):
                    if L[i][j] == value:
                        return i

    def selectBoxByManhattanDistance(self,max_part_length, max_part_width, box_lists):
        """
        从纸箱库中选择一个合适的纸箱进行待装箱
        :param max_part_length: 最大部件长度
        :param max_part_width: 最大部件宽度
        :param box_lists: 纸箱库信息列表
        :return: 一个最合适的纸箱（一维列表） or None
        """
        if isinstance(box_lists, list):
            if len(box_lists) != 0:
                box_temp_lists = []
                for box_item in box_lists:
                    if box_item[box_length_index] >= max_part_length and box_item[box_width_index] >= max_part_width:
                        box_temp_lists.append(box_item)
                # 挑选纸箱长宽距离max_part_length和max_part_width距离最近的纸箱
                boxTempGraded= [x for x in sorted(box_temp_lists, key=lambda g: math.fabs(g[box_length_index]-max_part_length)+math.fabs(g[box_width_index]-max_part_width), reverse=False)]
                return boxTempGraded[0]

    def partSizeMax(self,part_lists):
        """
        获取该批部件的长度最大值和宽度最大值
        :param part_lists: 原始部件列表信息
        :return: 长度最大值与宽度最大值 or None
        """
        if isinstance(part_lists, list):
            if len(part_lists) != 0:
                return max([part_length_col[part_length_index] for part_length_col in part_lists]), max(
                    [part_width_col[part_width_index] for part_width_col in part_lists])

    def convertSize(self, part_lists):
        for part in part_lists:
            if part[part_length_index]<part[part_width_index]:
                part[part_length_index],part[part_width_index]=part[part_width_index],part[part_length_index]
        return part_lists

    def selectAllFeasibleBox(self,max_part_length, max_part_width, box_lists,mod=False):
        """
        :param max_part_length:
        :param max_part_width:
        :param box_lists:
        :return:
        """
        if isinstance(box_lists, list):
            if len(box_lists) != 0:
                box_temp_lists = []
                for box_item in box_lists:
                    if box_item[box_length_index] >= max_part_length and box_item[box_width_index] >= max_part_width:
                        box_temp_lists.append(box_item)
                random_length = len(box_temp_lists)
                random_index = random.randint(0, random_length - 1)
                if mod:
                    return box_temp_lists
                return box_temp_lists[random_index]

class GACross:
    def partialMatchCross(self, male, female, cross_pos_low, cross_pos_up, mod=False):
        """
        本方法为局部匹配法，针对与自然数编码，如[0,1,2,3,4,5,6,9,7,8,10,11,12]类型
        :param male: 父代
        :param female: 母代
        :param cross_pos_low: 交叉点下限
        :param cross_pos_up: 交叉点上限
        :param mod: False（返回一个child）,True（返回两个child）
        :return: child
        """
        assert len(male) == len(female)
        if len(male) == cross_pos_up - cross_pos_low + 1:  # 边界情况:交叉点在最开始和最后的位置
            if mod:
                return female, male
            else:
                return female
        child1 = [-1] * len(male)  # 为子代分配内存
        child2 = [-1] * len(male)
        male_between_low_and_up_lists = male[cross_pos_low: cross_pos_up + 1]
        female_between_low_and_up_lists = female[cross_pos_low: cross_pos_up + 1]
        cross_pos_index_lists = [k for k in np.arange(cross_pos_low, cross_pos_up + 1, 1)]  # 获取交叉点[low,up]之间的index

        child1[cross_pos_low: cross_pos_up + 1] = female_between_low_and_up_lists  # 交换交叉点之间信息
        child2[cross_pos_low: cross_pos_up + 1] = male_between_low_and_up_lists

        child1[:cross_pos_low] = male[:cross_pos_low]  # 复制交叉点外的父母代信息
        child1[cross_pos_up + 1:] = male[cross_pos_up + 1:]
        child2[:cross_pos_low] = female[:cross_pos_low]
        child2[cross_pos_up + 1:] = female[cross_pos_up + 1:]

        cross_pos_lists = [[k1, k2] for k1, k2 in zip(male_between_low_and_up_lists, female_between_low_and_up_lists)]
        cross_pos_lists = [[x[0], x[1]] for x in sorted(cross_pos_lists, key=lambda x: x[0])]

        for i in range(len(child1)):
            if i in cross_pos_index_lists:  # 跳过交叉的部分
                continue
            else:
                if child1[i] in child1[cross_pos_low: cross_pos_up + 1]:
                    child1[i] = self.match(child1[i], cross_pos_lists, child1[cross_pos_low: cross_pos_up + 1])
        for j in range(len(child2)):
            if j in cross_pos_index_lists:  # 跳过交叉的部分
                continue
            else:
                if child2[j] in child2[cross_pos_low: cross_pos_up + 1]:
                    child2[j] = self.match(child2[j], cross_pos_lists, child2[cross_pos_low: cross_pos_up + 1])
        if mod:
            return child1, child2
        else:
            return child1

    def match(self, target, match_lists, cross_lists):
        """
        :param target:待匹配的目标
        :param match_lists:匹配列表
        :param cross_lists:交叉列表部分
        :return: 匹配的数值
        """
        is_match = True
        while is_match:
            for match_item in match_lists:
                if target in match_item:
                    if match_item[0] == target:
                        target = match_item[1]
                    else:
                        target = match_item[0]
                    if target not in cross_lists:
                        is_match = False  # 找到匹配的数，外循环结束条件
                        return target

    def singlePosCross(self, male, female, r1, r2, mod=False):
        """
        单点交叉
        :param male:
        :param female:
        :param r1:
        :param r2:
        :param mod:
        :return:False（返回一个child）,True（返回两个child）
        """
        if mod:
            male[r1] = 1 if male[r1]==0 else 0
            female[r2] = 1 if female[r2] == 0 else 0
            return male,female
        else:
            male[r1] = 1 if male[r1] == 0 else 0
            return male

class GA:
    def __init__(self, section_id, parts,
                 boxes, chromosome_length,
                 count=50, retain_rate=0.1,
                 random_select_rate=0.5,
                 crossRate=0.85,
                 mutation_rate=0.6,):
        #纸箱和货物信息
        self.section_id = section_id
        self._parts = copy.deepcopy(parts)
        self._boxes = copy.deepcopy(boxes)
        self._map = copy.deepcopy(parts)  # 原始板件的index（排序数字编号编码）与板件信息列表为一一对应的映射关系，此列表保持一直不变，供信息查找
        #实例化Util类
        self.util=Util()
        #遗传算法涉及参数
        self.chromosome_length = chromosome_length  # 该批板件数量
        self.count = count
        self.retain_rate = retain_rate
        self.random_select_rate = random_select_rate
        self.crossRate = crossRate
        self.mutation_rate = mutation_rate
        self.ksi = 1.6  # 适应值标定参数
        self.pop = self.initPop(chromosome_length, count)

    def putItem(self, putSeq,mod=True):
        """
        :param putSeq:
        :param mod: True：对一个序列装箱，False：对多个序列装箱
        :return:
        """
        solution=[]
        if mod:
            putObj = HeuristicPut(copy.deepcopy(putSeq), self._boxes)
            putRes, remainPart, remainPartOrient, totalThick = putObj.put_main()
            solution=self.decode(putRes, remainPart,remainPartOrient)
        else:
            for seq in putSeq:
                putObj = HeuristicPut(copy.deepcopy(seq),self._boxes)
                putRes, remainPart, remainPartOrient,totalThick=putObj.put_main()
                solution.append(self.decode(putRes, remainPart,remainPartOrient))
        return solution

    def initPop(self, chromosome_length, count):
        encodeRes=[]
        natureSeq=[i+1 for i in range(chromosome_length)]
        for count_index in range(count):
            #S1~Sn:自然数编码；Sn+1~S2n：二进制编码
            confuseSeq = list(np.random.permutation(natureSeq))
            binarySeq=[random.randint(0,1) for j in range(chromosome_length)]
            # if count_index==0:  # 调试
            #     confuseSeq=natureSeq
            #     binarySeq=[0]*16
            assert len(confuseSeq) == len(binarySeq)
            confuseSeq = self.codeMap(copy.deepcopy(confuseSeq))
            encodeRes.append(confuseSeq+binarySeq)
        solution = self.putItem(encodeRes, mod=False)
        return solution

    def codeMap(self, seq, convert_digit=False, needSelectState=False):
        """
        自然编码序列与解决方案序列一一映射查找方法
        :param seq:
        :param convert_digit: True:部件序列转换成自然编码序列，False:反之
        :return:
        """
        _parts_sorted = [0] * self.chromosome_length  # 分配内存空间
        if isinstance(seq, list):
            if convert_digit:
                binCode=[0]*self.chromosome_length
                selectState = [0] * self.chromosome_length
                for seq_index, seq_item in enumerate(seq):
                    _parts_sorted[seq_index] = seq_item.natureCode
                    binCode[seq_index]=seq_item.rotation_scheme
                    selectState[seq_index]=seq_item.selectState
                if needSelectState:
                    return _parts_sorted + binCode + ['装载状态=====>'] + selectState
                else:
                    return _parts_sorted + binCode
            else:
                for seq_index, seq_item in enumerate(seq):
                    _parts_sorted[seq_index] = self._map[seq_item-1]#自然序列从1开始，列表index从0开始，所以此处要减1
                return _parts_sorted

    def decode(self, putRes, remainPart,remainPartOrient):
        res=[]
        #解码装箱方案
        for put_part_item in putRes:
            part=PART()
            part.part_type_scheme = put_part_item[11]
            part.part_id_scheme = put_part_item[10]
            part.position_scheme = [put_part_item[0], put_part_item[1], put_part_item[8]]
            part.part_size_scheme = [put_part_item[4], put_part_item[5], put_part_item[6]]
            part.area_scheme = put_part_item[12]
            part.volume_scheme = put_part_item[13]
            part.weight_scheme = put_part_item[14]
            part.box_type_scheme = put_part_item[15]
            part.box_size_scheme = [put_part_item[16], put_part_item[17], put_part_item[18]]
            # part.package_id_scheme = package_id
            part.rotation_scheme = put_part_item[7]
            part.natureCode = self.util.getTwoDimensionListIndex(self._map, put_part_item[10])+1 # 自然码是在index基础上+1
            part.selectState = 1
            res.append(part)
        #将未装下的板件信息进行解码
        #板件放置位置，纸箱信息，选择selectState=0未选择
        if len(remainPart)!=0:
            assert len(remainPart)==len(remainPartOrient)
            for notPutPartIdx,notPutPartItem in enumerate(remainPart):
                part=PART()
                part.part_type_scheme = notPutPartItem[door_type_index]
                part.part_id_scheme = notPutPartItem[part_id_index]
                part.part_size_scheme = [notPutPartItem[part_length_index], notPutPartItem[part_width_index], notPutPartItem[part_thickness_index]]
                part.area_scheme = notPutPartItem[area_index]
                part.volume_scheme = notPutPartItem[volume_index]
                part.weight_scheme = notPutPartItem[weight_index]
                part.rotation_scheme = remainPartOrient[notPutPartIdx]
                part.natureCode = self.util.getTwoDimensionListIndex(self._map,
                                                                     notPutPartItem[part_id_index]) + 1  # 自然码是在index基础上+1
                part.selectState = 0
                res.append(part)
        assert len(res)==self.chromosome_length
        return res

    def evolve(self):
        # parents, retain_length = self.select()
        # self.crossover(copy.deepcopy(parents))
        # self.mutate()

        # self.scale()
        # self.sigmaScale()
        # self.rouletteGambling()
        # self.crossover2()
        # self.mutate()

        self.select2()
        self.crossover2()
        self.mutate()

    def rouletteGambling(self):
        """
        轮盘赌方法进行选择操作
        :return:
        """
        newPop=[]
        childGen = copy.deepcopy(self.pop)  # 复制一份子代
        # self.fitness=[self.fitFunc(chromosome) for chromosome in self.pop]
        totalFitness=sum(self.fitness)  # 总的适应度
        sumFitness=[0] * self.count #适应度累计值

        #获取轮盘赌各区间（累计区间）
        s = 0
        for i in range(0, self.count):
            sumFitness[i]=s + self.fitness[i]/totalFitness
            s = sumFitness[i]

        # 遍历所有个体
        for j in range(0,self.count):
            r = np.random.rand()#随机产生一个服从0~1均匀分布的样本值，样本取值范围[0,1)
            idx=0
            # 寻找这个个体所在的轮盘区间范围，适应度值越大，随机转到对应个体区间的概率越大，
            # 因此newPop中是有重复的个体，概率越大，在对应区间个体重复的个体数量越多
            for k in range(0, self.count-1):
                if k == 0 and r < sumFitness[k]:
                    idx=0
                    break
                elif (r >= sumFitness[k]) and (r < sumFitness[k+1]):
                    idx = k + 1
                    break
            newPop.append(childGen[idx])
        # 更新种群
        # self.pop = newPop
        self.pop.extend(newPop)
        # 获取每个方案对应的适应度值
        solutionFit = [(chromosome, self.fitFunc(chromosome)) for chromosome in self.pop]
        # 按照适应度值从大到小排序
        self.pop = [x[0] for x in sorted(solutionFit, key=lambda g: g[1], reverse=True)]
        del self.pop[self.count:]
        assert len(self.pop) == self.count

    def select(self):
        # 获取每个方案对应的适应度值

        solutionFit = [(chromosome, self.fitFunc(chromosome)) for chromosome in self.pop]
        curFitness=[v[1] for v in solutionFit]
        self.fitnessAvg=sum(curFitness)/self.count
        self.fitnessMax = max(curFitness)
        # 按照适应度值从大到小排序
        solutionGraded = [x[0] for x in sorted(solutionFit, key=lambda g: g[1], reverse=True)]
        assert len(solutionGraded)==self.count
        retain_length = int(len(solutionGraded) * self.retain_rate)

        # 保存适应度值大的个体作为一部分父代
        parents = solutionGraded[:retain_length]  # 按照self.retain_rate百分率保留父代
        # 从适应度值较小的个体中按照给定的选择概率射杀一定个体，保留一部分个体到父代中
        for chromosome in solutionGraded[retain_length:]:  # 从父代的剩余个体中以self.random_select_rate选择率选出幸存个体，添加到保留的父代中
            if random.random() < self.random_select_rate:  # 随机射杀的概率要大于选择率
                parents.append(chromosome)
        return parents, retain_length

    def select2(self):
        # 获取每个方案对应的适应度值
        solutionFit = [(chromosome, self.fitFunc(chromosome)) for chromosome in self.pop]
        # 按照适应度值从大到小排序
        solutionGraded = [x[0] for x in sorted(solutionFit, key=lambda g: g[1], reverse=True)]

        # 改进选择算子：根据适应度对个体进行排序；排在前面的个体复制两份；中间的复制一份；后面的不复制；
        copyLen = self.count // 3
        foreIndividual = copy.deepcopy(solutionGraded[0:copyLen]) * 2  # 排在前面的个体复制两份
        midIndividual = copy.deepcopy(solutionGraded[copyLen:self.count - copyLen])  # 中间的复制一份
        foreIndividual.extend(midIndividual)
        self.pop = foreIndividual

    def crossover(self,parents):
        # 新出生的孩子，最终会被加入存活下来的父母之中，形成新一代的种群
        children = []
        # 需要繁殖的孩子的数量
        target_count = len(self.pop) - len(parents)
        crossObj=GACross()
        while len(children) < target_count:
            male_index = random.randint(0, len(parents) - 1)  # 从parents父代中随机获取一个父亲的index，准备交叉
            female_index = random.randint(0, len(parents) - 1)  # # 从parents父代中随机获取一个母亲的index，准备交叉
            if male_index != female_index:  # 如果父与母亲的染色体一样，交叉（杂交）就没有了意义
                # 随机产生4个交叉点：r1、r2为S1~Sn的交叉点，r3、r4为Sn+1~S2n的交叉点
                r1 = random.randint(0, self.chromosome_length-1)
                r2 = random.randint(0, self.chromosome_length-1)
                r3 = random.randint(0, self.chromosome_length-1)
                r4 = random.randint(0, self.chromosome_length-1)
                # 获取交叉的父代和母代

                male = parents[male_index]
                female = parents[female_index]
                f = max(self.fitFunc(male), self.fitFunc(female))
                if f >= self.fitnessAvg:
                    self.crossRate= 0.8*(self.fitnessMax-f)/(self.fitnessMax-self.fitnessAvg+eps)
                elif f< self.fitnessAvg or self.crossRate==0:
                    self.crossRate= 0.98
                # 将父代、母代转换成自然数编码和二进制编码
                # print("交叉率：", self.crossRate)
                male = self.codeMap(male,convert_digit=True)
                female = self.codeMap(female, convert_digit=True)
                r = np.random.rand()
                if r < self.crossRate:  # 增加交叉率
                    natureChild = crossObj.partialMatchCross(male[:self.chromosome_length],
                                                            female[:self.chromosome_length],
                                                            r1,r2,mod=False)
                    natureChild=self.codeMap(copy.deepcopy(natureChild))
                    binChild = crossObj.singlePosCross(male[self.chromosome_length:],
                                                       female[self.chromosome_length:],
                                                       r3,r4,mod=False)
                    child=natureChild+binChild
                    #将交叉后的子代进行装箱
                    child = self.putItem(copy.deepcopy(child))
                    children.append(child)
        self.pop = parents + children

    def crossover2(self):
        childGen = copy.deepcopy(self.pop)  # 复制一份子代
        crossObj = GACross()
        # curFitness = [self.fitFunc(chromosome) for chromosome in childGen]
        # self.fitnessAvg = sum(curFitness) / self.count
        # self.fitnessMax = max(curFitness)
        for i in range(0, self.count, 2):
            idx1 = random.randint(0, self.count - 1)
            idx2 = random.randint(0, self.count - 1)
            while idx1 ==  idx2:
                idx2 = random.randint(0, self.count - 1)
            male = copy.deepcopy(childGen[idx1])
            female = copy.deepcopy(childGen[idx2])

            # f = max(self.fitFunc(male), self.fitFunc(female))
            # if f >= self.fitnessAvg:
            #     self.crossRate = 0.8 * (self.fitnessMax - f) / (self.fitnessMax - self.fitnessAvg + eps)
            # else:
            #     self.crossRate = 0.98
            # if self.crossRate == 0:
            #     self.crossRate = 1

            # print("交叉率：", self.crossRate)
            # 将父代、母代转换成自然数编码和二进制编码
            male = self.codeMap(male, convert_digit=True)
            female = self.codeMap(female, convert_digit=True)
            r = np.random.rand()
            if r < self.crossRate:
                # 随机产生4个交叉点：r1、r2为S1~Sn的交叉点，r3、r4为Sn+1~S2n的交叉点
                r1 = random.randint(0, self.chromosome_length - 1)
                r2 = random.randint(0, self.chromosome_length - 1)
                r3 = random.randint(0, self.chromosome_length - 1)
                r4 = random.randint(0, self.chromosome_length - 1)
                natureChild1, natureChild2= crossObj.partialMatchCross(male[:self.chromosome_length],
                                                         female[:self.chromosome_length],
                                                         r1, r2, mod=True)
                natureChild1 = self.codeMap(copy.deepcopy(natureChild1))
                natureChild2 = self.codeMap(copy.deepcopy(natureChild2))
                binChild1, binChild2 = crossObj.singlePosCross(male[self.chromosome_length:],
                                                   female[self.chromosome_length:],
                                                   r3, r4, mod=True)
                child1 = natureChild1 + binChild1
                child2 = natureChild2 + binChild2
                # 将交叉后的子代进行装箱
                child1 = self.putItem(copy.deepcopy(child1))
                child2 = self.putItem(copy.deepcopy(child2))
                childGen[i] = child1
                childGen[i+1] = child2
        self.pop.extend(childGen)
        # 获取每个方案对应的适应度值
        solutionFit = [(chromosome, self.fitFunc(chromosome)) for chromosome in self.pop]
        # 按照适应度值从大到小排序
        self.pop = [x[0] for x in sorted(solutionFit, key=lambda g: g[1], reverse=True)]
        del self.pop[self.count:]
        assert len(self.pop) == self.count

    def mutate(self):
        childGen = copy.deepcopy(self.pop)  # 复制一份子代
        # 经过交叉后，self.pop发生了变化，需要重新计算fitnessMax和fitnessAvg，要不然会出现mutation_rate<0问题
        # curFitness = [self.fitFunc(chromosome) for chromosome in childGen]
        # self.fitnessAvg = sum(curFitness)/self.count
        # self.fitnessMax = max(curFitness)
        r1,r2,r3,r4=0,0,0,0
        for i in range(len(childGen)):
            # f = self.fitFunc(childGen[i])
            # if f >= self.fitnessAvg:
            #     self.mutation_rate = 0.5 * (self.fitnessMax - f) / (self.fitnessMax - self.fitnessAvg + eps)
            # else:
            #     self.mutation_rate = 0.55
            # if self.mutation_rate==0:
            #     self.mutation_rate=0.65
            # print("变异率：",self.mutation_rate)
            if random.random() < self.mutation_rate:
                while r1 == r2 or r3 == r4:  # 直到随机产生的位置不一致才结束，这样才有意义
                    r1 = random.randint(0, self.chromosome_length - 1)
                    r2 = random.randint(0, self.chromosome_length - 1)
                    r3 = random.randint(0, self.chromosome_length - 1)
                    r4 = random.randint(0, self.chromosome_length - 1)
                    if self.chromosome_length < 2:  # 可能的死循环
                        break
                mutation_chromosome = self.codeMap(childGen[i], convert_digit=True)
                mutation_chromosome[r1],mutation_chromosome[r2]=mutation_chromosome[r2],mutation_chromosome[r1]
                mutation_chromosome[r3+self.chromosome_length]=1 if mutation_chromosome[r3+self.chromosome_length]==0 else 0
                mutation_chromosome[r4 + self.chromosome_length] = 1 if mutation_chromosome[r4 + self.chromosome_length] == 0 else 0

                natureChild = self.codeMap(copy.deepcopy(mutation_chromosome[:self.chromosome_length]))
                binChild=mutation_chromosome[self.chromosome_length:]
                child = natureChild + binChild
                mutation_child = self.putItem(copy.deepcopy(child))
                childGen[i] = mutation_child  # 将变异个体更新到种群中
        self.pop.extend(childGen)
        # 获取每个方案对应的适应度值
        solutionFit = [(chromosome, self.fitFunc(chromosome)) for chromosome in self.pop]
        # 按照适应度值从大到小排序
        self.pop = [x[0] for x in sorted(solutionFit, key=lambda g: g[1], reverse=True)]
        del self.pop[self.count:]
        assert len(self.pop) == self.count

    def fitFunc(self,solution):
        """
        :param solution: 一个解决方案
        :return: 适应度值
        """
        # boxVolume= self._boxes[box_length_index]*self._boxes[box_width_index]*self._boxes[box_height_index]*0.001
        boxVolume = self._boxes[box_length_index] * self._boxes[box_width_index] * self._boxes[box_height_index]
        curVolume=0
        for idx,part in enumerate(solution):
            curVolume+=part.volume_scheme * part.selectState#selectState=0直接把没有放的板件过滤掉
        volumeRate=curVolume/ boxVolume

        if volumeRate>1:
            pass
        return volumeRate

    def scale(self):
        """
        适应值的动态线性标定
        :return: 目标函数====》适应值函数
        """
        self.fitness = [self.fitFunc(chromosome) for chromosome in self.pop]
        r = 0.999
        self.ksi = self.ksi * r
        minFitness = min(self.fitness)  # 获取第k代目标函数最小值
        for i in range(len(self.fitness)):
            self.fitness[i] = self.fitness[i] - minFitness + self.ksi

    def sigmaScale(self):
        """
        sigma尺度截断法
        :return: 目标函数====》适应值函数
        """
        c= 0.85
        self.fitness = [self.fitFunc(chromosome) for chromosome in self.pop]
        aveFitness = sum(self.fitness)/len(self.fitness)
        sigma=math.sqrt(sum([(v - aveFitness) ** 2 for v in self.fitness])/len(self.fitness))
        for i in range(len(self.fitness)):
            self.fitness[i]=self.fitness[i]-(aveFitness-c*sigma)

    def getSolution(self):
        # 获取每个方案对应的适应度值
        solutionFit = [(chromosome, self.fitFunc(chromosome)) for chromosome in self.pop]
        # 按照适应度值从大到小排序
        solutionGraded = [x for x in sorted(solutionFit, key=lambda g: g[1], reverse=True)]
        # if solutionGraded[0][1]>1:  # 测试
        #     print(111)
        seq=self.codeMap(copy.deepcopy(solutionGraded[0][0]),convert_digit=True,needSelectState=False)
        return solutionGraded[0][0], seq, solutionGraded[0][1]

class PART:
    """
    利用PART存储待解决方案（板件装箱的编码）
    物品（板件）item的编码方式(所有的item的编码后的串即为解，也即为打包方案)：
    PART={
    str 板件类型    part_type
    str 板件部件编号  part_id
    float   板件空间坐标位置  (x,y,layer)，layer表示在第几层
    float   板件三维尺寸  (length,width,thickness)
    float   板件面积    area
    float   板件体积    volume
    float   板件重量    weight
    int     板件摆放方向  rotation
    str     板件所放纸箱类型    box_type
    float   板件所放纸箱尺寸    (L,W,H)
    str     板件的打包编号      package_id
    }
    """
    def __init__(self):
        self.part_type_scheme = ""
        self.part_id_scheme = ""
        self.position_scheme = [0, 0, 0]  # 需要求解
        self.part_size_scheme = [0, 0, 0]
        self.area_scheme = 0
        self.volume_scheme = 0
        self.weight_scheme = 0
        self.rotation_scheme = 0  # 需要求解，此处编码给出
        self.box_type_scheme = ""
        self.box_size_scheme = [0, 0 ,0]
        self.package_id_scheme = ""  # 需要求解
        self.natureCode = 0  # 需要求解，此处编码给出
        self.selectState = 0  # 0:部件没有被选中，1：部件被选中，暂留

class PutData:
    def __init__(self, solution, section_id):
        self.solution = solution
        self.section_id = section_id
        self.mysql = MysqlPool()

    def convert_package(self):
        result_dict = self.init_result_dict()
        if isinstance(self.solution, list):
            package_lists = [part_item.package_id_scheme for part_item in self.solution]
            count = Counter(package_lists)
            for package_id in count.keys():
                total_area = 0
                total_weight = 0
                total_volume = 0
                current_counter = 0
                solution_item = []
                for part_item in self.solution:
                    if part_item.package_id_scheme == package_id:
                        total_area += part_item.area_scheme
                        total_weight += part_item.weight_scheme
                        total_volume += part_item.volume_scheme
                        current_counter += 1
                        solute = '&'.join((str(part_item.position_scheme[0]), str(part_item.position_scheme[1]),
                                             str(part_item.position_scheme[2]), str(part_item.part_size_scheme[0]),
                                             str(part_item.part_size_scheme[1]), str(part_item.part_size_scheme[2]),
                                           str(part_item.rotation_scheme),part_item.part_id_scheme))
                        solution_item.append(solute)
                        # print('旋转状态：%s'%part_item.rotation_scheme)
                        if current_counter == count[package_id]:
                            result_dict['package_id'] = package_id
                            result_dict['total_layers'] = part_item.position_scheme[2]
                            result_dict['total_area'] = total_area
                            result_dict['total_weight'] = total_weight
                            result_dict['total_volume'] = total_volume
                            result_dict['section_id'] = re.findall(".*P(.*)-.*",package_id)[0]  # 获取两个字符之间的字符串
                            result_dict['order_id'] = re.findall(".*P(.*)S.*", package_id)[0]
                            result_dict['box_type'] = part_item.box_type_scheme
                            result_dict['box_length'] = part_item.box_size_scheme[0]
                            result_dict['box_width'] = part_item.box_size_scheme[1]
                            result_dict['box_height'] = part_item.box_size_scheme[2]
                            result_dict['part_num'] = count[package_id]
                            result_dict['volume_rate'] = total_volume / (part_item.box_size_scheme[0] * part_item.box_size_scheme[1] * part_item.box_size_scheme[2])
                            if len(solution_item) > 1:
                                solution_str = '#'.join(solution_item)
                                result_dict['solution'] = solution_str
                            else:
                                result_dict['solution'] = solution_item[0]
                            self.put_package_table(result_dict)
                    else:
                        continue
            self.update_database()

    def init_result_dict(self):
        result_dict = {'package_id': '', 'total_layers': 0, 'total_area': 0 , 'total_weight':0, 'total_volume': 0,
                     'section_id': '', 'order_id': '', 'box_type': '', 'box_length': 0, 'box_width': 0, 'box_height': 0,
                     'solution': '', 'part_num': 0, 'volume_rate': 0}
        return result_dict

    def put_package_table(self, result_dict):
        if result_dict:
            column_str = ''  # 列的字段
            row_str = ''  # 行字段
            for key in result_dict.keys():
                column_str = column_str + ' ' + '`' + key + '`,'
                row_str = (row_str + '"%s"' + ',') % str(result_dict[key])
            sql = "INSERT INTO %s (%s) VALUES (%s);" % (
                'package_result', column_str[:-1], row_str[:-1])  # 取[:-1]是去除字符串最后的逗号
            self.mysql.insert(sql)

    def update_database(self):
        sql = "UPDATE `order_section_online` SET `Package_state` = 5 WHERE `Sec_id` = '%s'" % self.section_id
        self.mysql.upda_sql(sql)

class Graph:
    def pltIterGraph(self, x, y, name='',mod=0):  # 0:默认画利用率迭代图，1：画利用率、交叉率、变异率动态变化图
        if mod not in (0,1):
            raise AttributeError("tne mode must be 0 or 1.")
        fig = plt.figure(num="遗传算法", )
        plt.plot(x, y[0], 'b-', label="利用率")
        yName = "容器利用率"
        volumeRate = y[3]
        spendTime=y[4]
        if mod==1:
            plt.plot(x, y[1], 'r-.', label='交叉率')
            plt.plot(x, y[2], 'g--', label='变异率')
            yName = "指标"
        plt.title(name+"迭代结果图（目标=%s，时间=%s）"%(round(volumeRate,2),round(spendTime,2)), fontproperties=simsun)
        plt.xlabel("迭代次数", fontproperties=simsun)
        plt.ylabel(yName, fontproperties=simsun)
        if max(x) < 30:  # 迭代次数比较小，设置坐标轴刻度，要不然会出现小数
            plt.xticks(x)  # 设置坐标轴数值不为小数
        plt.legend(loc=1)
        plt.legend(prop=simsun)
        # plt.show()

        # 自动保存
        curDate = time.strftime('%Y{y}%m{m}%d{d}').format(y='', m='', d='')
        saveFolder = './result/test%s/' % curDate
        if not os.path.exists(saveFolder):
            os.mkdir(saveFolder)

        curTime = time.strftime('%Y{y}%m{m}%d{d}%H{h}%M{f}%S{s}').format(y='', m='', d='', h='', f='', s='')
        plt.savefig(saveFolder+curTime+'.png',dpi=600,format='png')  # 自动保存图片
        plt.clf()  # 清空上一个图片，连续保存多个图片

def LayoutGraph(solutions):
    app = wx.App()
    frame = LayoutFrame(parent=None,
                     id=-1,
                     title='布局图',
                     pos=wx.DefaultPosition,
                     size=(1200,700),
                     style=wx.DEFAULT_FRAME_STYLE,
                     solutions=solutions)
    frame.SetBackgroundColour('white')
    frame.Show()
    app.MainLoop()

class LayoutFrame(wx.Frame):
    def __init__(self, parent, id, title, pos, size, style, solutions):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        print(solutions)



def Instance1Main():
    name='C41'
    if 'N' in name and name in N13:
        sec_id, partSet = Ndata()
        part_lists = partSet[name]
        box_lists = Nbox()
        box = box_lists[name][0]
    elif 'C' in name and name in C21:
        sec_id, partSet = Cdata()
        part_lists = partSet[name]
        box_lists = Cbox()
        box = box_lists[name][0]
    else:
        raise AttributeError("the name must be C21 or N13 at present.")

    if sec_id:
        part_lists = Util().partWeightAreaVolume(copy.deepcopy(part_lists))
        part_lists = Util().convertSize(copy.deepcopy(part_lists))

        x, y, num ,unevolveNum= [], [], 0,0
        crossRates, mutateRates = [], []

        start_time = time.time()
        ga = GA(sec_id,part_lists,box,len(part_lists))
        for i in range(200):
            ga.evolve()
            solution, seq, volumeRate = ga.getSolution()
            crossRates.append(ga.crossRate)
            mutateRates.append(ga.mutation_rate)
            x.append(i+1)
            y.append(volumeRate)
            # print("the %d iter:" % (i + 1), volumeRate)
            print("the %d iter:" % (i + 1), volumeRate, crossRates[i], mutateRates[i])

            # 针对代数的AGA算法
            # if i!=0:
            #     if y[i-1]==y[i]:
            #         unevolveNum+=1
            #         f_influent=unevolveNum/10
            #         ga.crossRate = ga.crossRate + math.exp(-1/f_influent) * (1-ga.crossRate)
            #         ga.mutation_rate = ga.mutation_rate + math.exp(-1 / f_influent) * (1 - ga.mutation_rate)/10
            #     else:
            #         unevolveNum=0
            #         ga.crossRate = ga.crossRate - y[i]*ga.crossRate/3
            #         ga.mutation_rate = ga.mutation_rate - y[i] * ga.mutation_rate / 3
            if volumeRate == 1.0:
                break

            # 针对代数改进AGA：解决交叉率和变异率受适应值变化的影响
            pc_low, pc_up = 0.6, 0.99
            pm_low, pm_up = 0.05, 0.6
            beta = 0.01
            if i!=0:
                if y[i-1]==y[i]:
                    unevolveNum+=1
                else:
                    unevolveNum=0
            else:
                unevolveNum = 0
            ga.crossRate = pc_low + (pc_up - pc_low) * (1 - math.exp(-beta*unevolveNum))/(1 + math.exp(-beta*unevolveNum))
            ga.mutation_rate = pm_low + (pm_up - pm_low) * (1 - math.exp(-beta * unevolveNum)) / (1 + math.exp(-beta * unevolveNum))


        end_time = time.time()
        print('算法迭代所花费的时间为：%s' % (end_time - start_time))
        print(ga._boxes)
        # LayoutGraph(solution)
        # Graph().pltIterGraph(x, (y,), name)
        Graph().pltIterGraph(x,(y,crossRates,mutateRates,volumeRate,end_time-start_time),name,mod=1)

if __name__ == '__main__':
    loop = LoopTimer(interval=2, target=Instance1Main)
    loop.start()
    loop.join()

