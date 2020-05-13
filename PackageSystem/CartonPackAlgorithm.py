#!/usr/bin/env python3
# coding=utf-8

from MYSQL.MysqlHelper import MysqlPool
from confs.Setting import *
from ThreadHelper import LoopTimer
from PublicRef.PublicRef import current_time
from DataSet import Cdata,Cbox
import numpy as np
import math
import random
import re
import matplotlib.pyplot as plt
from Layout import LowestHoriztonal
from collections import defaultdict, Counter
import copy

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
        sql = "SELECT `Box_type`, `Box_long`, `Box_short`, `Box_height` FROM `equipment_package_box` WHERE " \
              "`State`=5"
        box_info = self.mysql.do_sql(sql)
        if box_info is None:
            return None
        else:
            for i in range(len(box_info)):
                box_lists.append(list(box_info[i]))
            return box_lists

def PartSort(part_lists):
    """
    将部件按照长为第一优先级，宽为第二优先级进行从大到小排序
    :param part_lists: 原始部件列表信息
    :return:排序后的列表 or None
    """
    if isinstance(part_lists, list):
        if len(part_lists) != 0:
            part_sort_lists = part_lists[:]  # 复制一份副本，避免part_lists随part_sort_lists同时变化
            # 按照部件的长为第一优先级，宽为第二优先级进行从大到小排序
            part_sort_lists.sort(key=lambda x: (x[part_length_index], x[part_width_index]), reverse=True)
            return part_sort_lists

def PartSizeMax(part_lists):
    """
    获取该批部件的长度最大值和宽度最大值
    :param part_lists: 原始部件列表信息
    :return: 长度最大值与宽度最大值 or None
    """
    if isinstance(part_lists, list):
        if len(part_lists) != 0:
            return max([part_length_col[part_length_index] for part_length_col in part_lists]), max([part_width_col[part_width_index] for part_width_col in part_lists])
def convertSize(part_lists):
    for part in part_lists:
        if part[part_length_index]<part[part_width_index]:
            part[part_length_index],part[part_width_index]=part[part_width_index],part[part_length_index]
    return part_lists
def PartWeightAreaVolume(part_lists):
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

def SelectBoxByManhattanDistance(max_part_length, max_part_width, box_lists):
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
            #  挑选纸箱长宽距离max_part_length和max_part_width距离最近的纸箱
            box_return_index = 0
            if len(box_temp_lists) != 0:
                for box_temp_index, box_temp_item in enumerate(box_temp_lists):
                    min_distance = math.fabs(max_part_length - box_temp_lists[0][box_length_index]) + math.fabs(max_part_width - box_temp_lists[0][box_width_index])  # 假设第一个元素为最小距离
                    distance = math.fabs(max_part_length - box_temp_item[box_length_index]) + math.fabs(max_part_width - box_temp_item[box_width_index])
                    if distance < min_distance:
                        min_distance = distance
                        box_return_index = box_temp_index
            return box_temp_lists[box_return_index]

def SelectAllFeasibleBox(max_part_length, max_part_width, box_lists):
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
            return box_temp_lists[random_index]

def PutPart(part_lists, box_lists, section_id):
    """
    获取放置板件布局结果
    :param part_lists:
    :param box_lists:
    :return:
    """
    package_num = 0
    package_dict = defaultdict(list)
    while len(part_lists) != 0:
        part_lists=convertSize(part_lists)#增，防止长小于宽
        max_part_length, max_part_width = PartSizeMax(part_lists)
        # box = SelectAllFeasibleBox(max_part_length, max_part_width, box_lists)
        box = SelectBoxByManhattanDistance(max_part_length, max_part_width, box_lists)

        # 测试最低水平线
        lowest = LowestHoriztonal(part_lists, box)
        finished_part, part_lists, total_thickness = lowest.put_main()
        package_num += 1
        package_id = 'P' + section_id + '-' + str(package_num)
        package_dict[package_id] = finished_part
    return package_dict

def GetTwoDimensionListIndex(L,value):
    """获得二维列表某个值的一维索引值的一种方法"""
    if isinstance(L, list):
        for i in range(len(L)):
            for j in range(len(L[i])):
                if L[i][j] == value:
                    return i

def PartialMatchCross(male, female, cross_pos_low, cross_pos_up, mod=False):
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
                child1[i] = Match(child1[i], cross_pos_lists, child1[cross_pos_low: cross_pos_up + 1])
    for j in range(len(child2)):
        if j in cross_pos_index_lists:  # 跳过交叉的部分
            continue
        else:
            if child2[j] in child2[cross_pos_low: cross_pos_up + 1]:
                child2[j] = Match(child2[j], cross_pos_lists, child2[cross_pos_low: cross_pos_up + 1])
    if mod:
        return child1, child2
    else:
        return child1

def Match(target, match_lists, cross_lists):
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

class GA:
    """
    随机的是板件的顺序，初始化为经过PartSort排序经最低水平线给出每块板件放置方案，目标函数暂时定空间利用率最大
    """
    def __init__(self, parts, boxes, chromosome_length, count, retain_rate, random_select_rate, mutation_rate, section_id):
        self._parts = copy.deepcopy(parts)  # 深拷贝
        self._boxes = copy.deepcopy(boxes)
        self._map = copy.deepcopy(parts)  # 原始板件的index（排序数字编号编码）与板件信息列表为一一对应的映射关系，此列表保持一直不变，供信息查找
        self.chromosome_length = chromosome_length  # 该批板件数量
        self.count = count
        self.retain_rate = retain_rate
        self.random_select_rate = random_select_rate
        self.mutation_rate = mutation_rate
        self.section_id = section_id
        self.population = self.init_population(chromosome_length, count)

    def random_sort(self, chromosome_length):
        """
        随机产生[0, chromosome_length]的所有整数，每个整数不重复且都有
        :param chromosome_length: 染色体长度（这批板件数量）
        :return: 随机排序后的板件列表数据
        """
        # _parts_sorted = [0] * chromosome_length  # 分配内存空间
        random_seq = np.arange(0, chromosome_length)  # ndarray类型
        random_seq = list(random_seq)  # list类型
        random_seq = random.sample(random_seq, chromosome_length)  # 随机产生一定范围的整数，每个整数不重复且都有
        # if isinstance(random_seq, list):
        #     for random_seq_index, random_seq_item in enumerate(random_seq):
        #         _parts_sorted[random_seq_index] = self._map[random_seq_item]
        return self.decode(random_seq)

    def decode(self, seq, convert_digit=False):
        """
        数字编码序列与解决方案序列一一映射查找方法
        :param seq:
        :param convert_digit: True:部件序列转换成数字编码序列，False:反之
        :return:
        """
        _parts_sorted = [0] * self.chromosome_length  # 分配内存空间
        if isinstance(seq, list):
            if convert_digit:
                for seq_index, seq_item in enumerate(seq):
                    _parts_sorted[seq_index] = GetTwoDimensionListIndex(self._map, seq_item.part_id_scheme)
            else:
                for random_seq_index, random_seq_item in enumerate(seq):
                    _parts_sorted[random_seq_index] = self._map[random_seq_item-1]
            return _parts_sorted

    def get_chromosome(self, chromosome_length, is_more_sort=False, seq=[]):
        """
        :param chromosome_length: 染色体长度（这批板件数量）
        :param is_more_sort: False随机排序，True以长度第一优先级，宽度第二优先级降序排序
        :return: 产生一个个体（染色体）
        """
        chromosome = []
        if not seq:  # 序列表为空
            if not is_more_sort:
                _parts_sorted = self.random_sort(chromosome_length)
            else:
                _parts_sorted = PartSort(self._parts)
        else:
            _parts_sorted = seq

        # 运行最低水平线布局算法，放置板件，获取解决方案（chromosome）
        package_dict = PutPart(_parts_sorted, self._boxes, self.section_id)
        if package_dict:
            for package_id_key in package_dict.keys():
                for put_part_value in package_dict[package_id_key]:
                    part = self.encode(package_id_key, put_part_value)
                    chromosome.append(part)
        return chromosome

    def init_population(self, chromosome_length, count):
        """
        初始化产生数量为count种群
        :param chromosome_length: 染色体长度
        :param count: 种群数量
        :return: 种群列表数据
        """
        population_lists = []
        population_lists.append(self.get_chromosome(chromosome_length, is_more_sort=True))  # 种群中有一个初始较好的个体
        population_lists = population_lists + [self.get_chromosome(chromosome_length) for count_index in range(count - 1)]
        return population_lists

    def encode(self, package_id, put_part_item):
        """
        :param package_id: 包编号
        :param put_part_item: 打包方案
        :return: PART类的对象各属性
        """
        part = PART()
        if isinstance(part, PART):
            part.part_type_scheme = put_part_item[11]
            part.part_id_scheme = put_part_item[10]
            part.position_scheme = [put_part_item[0], put_part_item[1], put_part_item[8]]
            part.part_size_scheme = [put_part_item[4], put_part_item[5], put_part_item[6]]
            part.area_scheme = put_part_item[12]
            part.volume_scheme = put_part_item[13]
            part.weight_scheme = put_part_item[14]
            part.box_type_scheme = put_part_item[15]
            part.box_size_scheme = [put_part_item[16], put_part_item[17], put_part_item[18]]
            part.package_id_scheme = package_id
            part.rotation_scheme = put_part_item[7]
            return part

    def evolve(self):
        parents = self.selection()
        self.crossover(parents)
        self.mutation()

    def selection(self):
        # 对适应度从大到小排序（个体适应度评价）
        fitness_graded = [(chromosome, self.fitness(chromosome)) for chromosome in self.population]
        fitness_graded = [x[0] for x in sorted(fitness_graded, key=lambda g: g[1], reverse=True)]
        assert len(fitness_graded) == self.count
        retain_length = int(len(fitness_graded) * self.retain_rate)

        # 保存适应度值大的个体作为一部分父代
        parents = fitness_graded[:retain_length]  # 按照self.retain_rate百分率保留父代
        # 从适应度值较小的个体中按照给定的选择概率射杀一定个体，保留一部分个体到父代中
        for chromosome in fitness_graded[retain_length:]:  # 从父代的剩余个体中以self.random_select_rate选择率选出幸存个体，添加到保留的父代中
            if random.random() < self.random_select_rate:  # 随机射杀的概率要大于选择率
                parents.append(chromosome)
        return parents

    def crossover(self, parents):
        # 新出生的孩子，最终会被加入存活下来的父母之中，形成新一代的种群
        children = []
        # 需要繁殖的孩子的数量
        target_count = len(self.population) - len(parents)
        while len(children) < target_count:
            male_index = random.randint(0, len(parents) - 1)  # 从parents父代中随机获取一个父亲的index，准备交叉
            female_index = random.randint(0, len(parents) - 1)  # # 从parents父代中随机获取一个母亲的index，准备交叉
            if male_index != female_index:  # 如果父与母亲的染色体一样，交叉（杂交）就没有了意义
                cross_pos_low = random.randint(0, self.chromosome_length)
                cross_pos_up = random.randint(0, self.chromosome_length)
                male = parents[male_index]
                female = parents[female_index]

                male = self.decode(male, convert_digit=True)
                female = self.decode(female, convert_digit=True)
                child = PartialMatchCross(male, female, cross_pos_low, cross_pos_up, mod=False)
                child = self.decode(child)

                child = self.get_chromosome(self.chromosome_length, seq=child)  # 获取解决方案
                children.append(child)
        self.population = parents + children

    def mutation(self):
        """
        变异，对种群的所有个体，随机改变某个个体中的某个基因
        例如[0, 1, 2, 3, 4, 5]随机生成2个不同位置，如位置1，4，然后通过交换数据进行变异
        """
        switch_pos1 = 0
        switch_pos2 = 0
        for i in range(len(self.population)):
            if random.random() < self.mutation_rate:
                while switch_pos1 == switch_pos2:  # 直到随机产生的位置不一致才结束，这样才有意义
                    switch_pos1 = random.randint(0, self.chromosome_length - 1)
                    switch_pos2 = random.randint(0, self.chromosome_length - 1)
                    if self.chromosome_length < 2:  # 可能的死循环
                        break
                mutation_chromosome = self.decode(self.population[i], convert_digit=True)
                temp = mutation_chromosome[switch_pos1]
                mutation_chromosome[switch_pos1] = mutation_chromosome[switch_pos2]
                mutation_chromosome[switch_pos2] = temp

                mutation_child = self.decode(mutation_chromosome)
                mutation_child = self.get_chromosome(self.chromosome_length, seq=mutation_child)

                self.population[i] = mutation_child  # 将变异个体更新到种群中

    def fitness(self, chromosome, is_perpackage_volume=False):
        """
        :param chromosome: solution
        :return: the average rate of volume or None when it occurs to the false
        """
        volume_rate_lists = []
        package_id_lists = list(set([item.package_id_scheme for item in chromosome]))
        for package in package_id_lists:
            volume = 0
            box_volume = 0
            for chromosome_item in chromosome:
                if chromosome_item.package_id_scheme == package:
                    volume += chromosome_item.volume_scheme
                    box_volume = chromosome_item.box_size_scheme[0] * chromosome_item.box_size_scheme[1] * chromosome_item.box_size_scheme[2]
            try:
                volume_rate = volume / box_volume
                volume_rate_lists.append(volume_rate)
            except ZeroDivisionError: # 没有该包
                volume_rate_lists.append(False)
        assert len(volume_rate_lists) == len(package_id_lists)
        if volume_rate_lists and False not in volume_rate_lists:
            average_volume_rate = sum(volume_rate_lists) / len(volume_rate_lists)
            if is_perpackage_volume:
                return average_volume_rate, volume_rate_lists
            return average_volume_rate
        else:
            return None

    def sloution(self):
        """
        :return: 输出GA算法的解决方案及目标函数值
        """
        # 按照适应度值进行降序排序，并取第一个chromosome为最优或近似最优解决方案
        fitness_graded = [(chromosome, self.fitness(chromosome)) for chromosome in self.population]
        fitness_graded = [x[0] for x in sorted(fitness_graded, key=lambda g: g[1], reverse=True)]
        return fitness_graded[0], self.decode(fitness_graded[0], convert_digit=True), self.fitness(fitness_graded[0])+0.1

class PART:
    """
    利用PART存储待解决方案（板件装箱的编码）
    物品（板件）item的编码方式(所有的item的编码后的串即为解，也即为打包方案)：
    PART={
    str 板件类型    part_type
    str 板件部件编号  part_id
    float   板件空间坐标位置  (x,y,layer)
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
        self.position_scheme = [0, 0, 0]  # (x, y, layer)，layer表示在第几层
        self.part_size_scheme = [0, 0, 0]
        self.area_scheme = 0
        self.volume_scheme = 0
        self.weight_scheme = 0
        self.rotation_scheme = 0
        self.box_type_scheme = ""
        self.box_size_scheme = [0, 0 ,0]
        self.package_id_scheme = ""

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

def CartonPackAlgorithmMain(log):
    data = GetData()
    sec_id, part_lists = data.get_part_info()
    # sec_id, part_lists1 = Cdata()
    # part_lists=part_lists1['C11']
    if sec_id:
        box_lists = data.get_box_info()
        # box_lists = Cbox()
        if part_lists and box_lists:
            PartWeightAreaVolume(part_lists)
            ga = GA(part_lists, box_lists, len(part_lists), count=100, retain_rate=0.25, random_select_rate=0.5,
                    mutation_rate=0.05, section_id=sec_id)
            fig = plt.figure(num="遗传算法")
            x , y = [], []
            for i in range(70):
                ga.evolve()
                solution, seq, average_volume = ga.sloution()
                mytest = "the %d iter: %s %s" % (i, average_volume, seq)
                log.write_textctrl_txt(mytest)
                print("the %d iter:" % i, average_volume, seq)
                x.append(i + 1)
                y.append(average_volume)
            solution, seq, average_volume = ga.sloution()
            # PutData(solution, sec_id).convert_package()
            plt.plot(x, y)
            plt.title("遗传算法——随机选纸箱迭代结果图", fontproperties=simsun)
            plt.xlabel("迭代次数", fontproperties=simsun)
            plt.ylabel("纸箱体积平均利用率", fontproperties=simsun)
            plt.show()
    else:
        print("{} No section is needed to pack.".format(current_time()))


if __name__ == '__main__':
    loop = LoopTimer(interval=2, target=CartonPackAlgorithmMain)
    loop.start()
    loop.join()
