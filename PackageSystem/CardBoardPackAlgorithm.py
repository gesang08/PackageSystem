#!/usr/bin/env python3
# encoding:utf-8

"""
说明：针对纸板打包，将一个组件下的板件，通过算法的方式进行分包，给出打包方案存储到数据库中
算法：分包：全区域划分算法-->整合算法；分层：最低水平线算法
输入：板件的长宽厚、门型等信息；
输出：打包方案（哪些板件分在一包，每一块板件的放置位置，纸板需要剪切的长宽高）
"""

import pymysql as MySQLdb
from collections import defaultdict
import time
import datetime
import sys
import os
from collections import Counter
import numpy as np
import math
from MYSQL.MysqlHelper import Mysql as MyDb
from confs.Setting import *
from ThreadHelper import LoopTimer


class CardBoardPack:
    def __init__(self, log=None):
        self.log = log
        self.running = False

    def is_connection_db(self):
        """
        是否成功连接数据库方法
        :return: 成功为True,否则为False
        """
        try:
            self.db = MySQLdb.connect(host=SERVER_IP, user=USER, passwd=PASSWORD, db=DB, port=PORT, charset=CHARSET)
        except Exception as e:
            self.log = get_time() + u"打包程序is_connection_db()方法报错，数据库连接不成功！"
            self.write_log()
            print(self.log)
            return False
        else:
            return True

    def is_new_package(self):
        """
        查询组件表单是否有需要打包的组件
        :return: 无需要打包的组件返回False,否则返回True
        """
        have_new_package = False
        if self.is_connection_db():
            cursor = self.db.cursor()
            cursor.execute("SELECT `Index`, `Sec_id` FROM `order_section_online` WHERE `Package_state`=0")
            record = cursor.fetchone()
            if record == () or record is None:
                have_new_package = False
            else:
                have_new_package = True
                self.section_id = record[1]
            self.db.close()
            return have_new_package
        else:
            return have_new_package

    # *****************************************************上层方法**********************************************************
    def package_main(self):
        have_new_package = self.is_new_package()
        if have_new_package:
            self.isrunning = True
            if self.is_connection_db():
                error_id, info_box_lists = self.pro_package()
                if error_id == 0:
                    error_id, info_package_plies_plate = self.core_package(info_box_lists)
                    if error_id == 0:
                        error_id = self.after_package(info_package_plies_plate)
                        if error_id == 0:
                            self.isrunning = False
                        else:
                            self.log = get_time() + u"调用after_package()方法出现错误！"
                    else:
                        self.log = get_time() + u"调用core_package()方法出现错误！"
                else:
                    self.log = get_time() + u"调用pro_package()方法出现错误！"
            else:
                self.log = get_time() + u"调用is_connection_db()方法出现错误！"
            self.log = get_time() + self.section_id + u"组件打包完成！"
            self.write_log()
            print(self.log)
            # end = time.time()
            # print end - self.start  # 计算程序运行时间，单位为秒

    # *****************************************************中层方法**********************************************************

    def pro_package(self):
        info_box_lists = []
        error_id = self.pre_package_get_part_info()
        if error_id == 0:
            info_box_lists = self.create_virtual_box_size(self.info_parts[0][7])
        else:
            self.log = get_time() + u"调用pre_package_get_part_info()方法出现错误！"
            self.write_log()
            print(self.log)
        return error_id, info_box_lists

    def core_package(self, info_box_lists):
        error_id = 0
        spilt_flag = False
        current_layer_list = []
        exist_remain = False
        error_id = self.place_part_to_range(info_box_lists)
        for value in self.remain_num_and_state.values():
            if value[1] == 0:  # 存在不可以打一包的区域
                exist_remain = True
        if error_id == 0 and exist_remain:  # 程序无异常且存在有不可打一包的才调用重组函数
            self.recombine_remain_part()

        # 部件已经放到了划分好的区域中，接下来进行每包部件下每层的具体放置情况
        info_package_plies_plate = []  # 3维列表，存放一个组件下每块部件在每包每层的信息
        package_num = 0  # 记录当前包数编号
        for key, value in zip(list(self.info_box_part_dicts.keys()), list(self.info_box_part_dicts.values())):  # 在字典遍历过程中，修改字典元素，会报RuntimeError: dictionary changed size during iteration的错误，可将遍历条件改为列表，就可修改字典元素
            if len(value) != 0:  # 剔除重组后为空的值
                box_long, box_short = self.get_box_long_short(value)
                lowest_horiztonal_algorithm = LowestHoriztonalAlgorithm(key, value, box_long, box_short)
                plates, current_layer_num = lowest_horiztonal_algorithm.put_each_package()
                current_layer_list.append(current_layer_num)  # 解决多包层数大于阈值问题
                if max(current_layer_list) > OnePackageMaxLayers:  # 判断是否存在包的层数大于阈值，存在就把当前包拆分
                    self.spilt_package(key, value)
                    spilt_flag = True
                else:
                    package_num += 1
                    for plate in plates:
                        plate[-2] = 'P' + self.section_id + '-' + str(package_num)
                        # info_package_plies_plate.append(plate)
                    info_package_plies_plate.append(plates)
                    del self.info_box_part_dicts[key]

        if spilt_flag:
            for key, value in self.info_box_part_dicts.items():
                if len(value) != 0:
                    box_long, box_short = self.get_box_long_short(value)
                    lowest_horiztonal_algorithm = LowestHoriztonalAlgorithm(key, value, box_long, box_short)
                    plates, current_layer_num = lowest_horiztonal_algorithm.put_each_package()
                    package_num += 1
                    for plate in plates:
                        plate[-2] = 'P' + self.section_id + '-' + str(package_num)
                    info_package_plies_plate.append(plates)
        return error_id, info_package_plies_plate

    def after_package(self, info_package_plies_plate):
        error_id = 0
        error_id = self.send_package_info_to_work_package_task_list(info_package_plies_plate)
        if error_id == 0:
            self.update_package_info_to_db()
        else:
            self.log = get_time() + u"调用after_package()方法出现错误！"
            self.write_log()
            print(self.log)
        return error_id

    # *****************************************************底层方法**********************************************************

    def pre_package_get_part_info(self):
        error_id = 0
        self.info_parts = []  # 2维列表，将部件信息存储到列表中
        self.part_sizes = []  # 2维列表，存部件高宽厚与转换状态
        if self.is_connection_db():
            cursor = self.db.cursor()
            cursor.execute(
                "SELECT `Contract_id`, `Order_id`, `Sec_id`, `Part_id`, `Door_type`, `Door_height`, `Door_width`, `Door_thick`, `Package_state`, `Element_type_id` FROM `order_part_online` WHERE `Sec_id` = '%s'" % self.section_id)
            info_part1 = cursor.fetchall()
            if info_part1 == () or info_part1 is None:
                self.log = get_time() + u"打包程序pre_package_get_part_info()报错，给定组件下的部件信息为空！"
                self.write_log()
                print(self.log)
                error_id = 100
            else:
                for i in range(len(info_part1)):
                    self.info_parts.append(list(info_part1[i]))
                    self.info_parts[i][8] = 0  # 不管部件表单打包状态是多少，读取部件信息的打包状态都置0
                for info_part in self.info_parts:
                    width, height, is_change_state = self.is_change_height_width(info_part[5], info_part[6])
                    part_size = [info_part[3], width, height, info_part[7], is_change_state]
                    self.part_sizes.append(part_size)
            self.db.close()
            # plt.scatter([w[1] for w in self.part_sizes], [h[2] for h in self.part_sizes], s=10, marker='.', c='r')
            # plt.title('Original data')
            # plt.xlabel('w/mm')
            # plt.ylabel('h/mm')
            # plt.axis([0, 1220, 30, 2436])
            # plt.xticks(range(0, 1201, 100))
            # plt.yticks(range(0, 2437, 100))
            # plt.grid()
            # plt.show()
        return error_id

    def create_virtual_box_size(self, thick):
        """
        将30<=H<=2436,30<=W<=1200组成的2维区域细分区间，其细分算法为：100<=H<=2300，100<=W<=1200以100为间隔细分，余下30-100
        和2300-2436为一个区间，根据重量生成每个区间的最少可以放的块数和最多可以放的块数
        :return: 288 * 7二维列表info_box_lists,
        格式为[Index,short_range_low, short_range_up, long_range_low, long_range_up, box_block_low, box_block_up]
        """
        index = 0
        info_box_lists = []
        interval = 100
        long_range_num = (HeightOrWidthMax - HeightOrWidthMin) // interval  # 以100为间隔获得长度区间数为24个
        short_range_num = (HeightAndWidthLimit - HeightOrWidthMin) // interval + 1  # 以100为间隔获得宽度区间数为12个
        for i in range(short_range_num):
            for j in range(long_range_num):
                short_range_low = i * interval
                short_range_up = (i + 1) * interval
                long_range_low = j * interval
                long_range_up = (j + 1) * interval
                if j == 0:
                    long_range_low = HeightOrWidthMin
                if j == long_range_num - 1:
                    long_range_up = HeightOrWidthMax
                if i == 0:
                    short_range_low = HeightOrWidthMin
                index += 1
                box_block_low = int(round(
                    OnePackageMinWeight / (
                                short_range_up * long_range_up * thick * 10 ** (-9) * BaseMaterialDensity)))
                box_block_up = int(round(OnePackageMaxWeight / (
                        short_range_low * long_range_low * thick * 10 ** (-9) * BaseMaterialDensity)))
                if box_block_low == 1:
                    if (np.mean([short_range_low, short_range_up]) * np.mean([long_range_low, long_range_up]) <=
                            HeightOrWidthMax * HeightAndWidthLimit / 2):  # 不超过基材一半面积的，最少可以放2块
                        box_block_low += 1
                if box_block_low == 0:
                    box_block_low += 1
                    box_block_up+=1#暂加调试
                info_box_lists.append(
                    [str(index), short_range_low, short_range_up, long_range_low, long_range_up,
                     box_block_low, box_block_up])
        return info_box_lists

    def is_change_height_width(self, init_height, init_width):
        """
        :param init_height:
        :param init_width:
        :return:0表示无需转换高宽，1表示转化了高宽
        """
        if init_height >= init_width:
            return init_width, init_height, 0
        else:
            return init_height, init_width, 1

    def handle_bar(self):
        """
        该方法用于处理条子
        定义：条子长度不超过1000可以拼接，条子长度超过1000单独打包
        :return:
        """
        pass

    def place_part_to_range(self, info_box_lists):
        """
        将实际的部件放到288个区间盒子里
        将实际部件放到区域里，存放在字典中的格式为self.info_box_parts={key=Index:[[part_id,width,height,thick,is_change_state,
        Index,short_range_low, short_range_up, long_range_low, long_range_up, box_block_low,box_block_up],...]}
        考虑到某个区域会出现大于一包的情况，需要对包在区域进行划分，此时将key标记为id-1,id-2,...
        self.remain_num_and_state = {key=Index:[remain_num,package_state]},remain_num存储包的剩余可放块数，package_state
        记录包的状态:-1表示初始化，0表示不可打一包，1表示可打一包，2表示正好一包,5表示不可打一包且包里块数为0
        """
        error_id = 0
        part_info_and_ranges = []
        range_nums = []
        self.info_box_part_dicts = defaultdict(list)  # info_box_part_dicts以区域id为键，以实际板件信息为值的字典,存放实际部件所放得区域
        self.remain_num_and_state = defaultdict()
        is_finish_put_in_range = False
        for part_size in self.part_sizes:
            for box_size in info_box_lists:  # ( ]范围是包含右边不包含左边，所以当部件高宽为30时，此部件信息会丢失，所以需要考虑部件高宽为30的情况
                if ((part_size[1] > box_size[1]) and (part_size[1] <= box_size[2]) and (part_size[2] > box_size[3])
                    and (part_size[2] <= box_size[4])) or ((part_size[1] >= HeightOrWidthMin) and
                                                           (part_size[1] <= box_size[2]) and
                                                           (part_size[2] >= HeightOrWidthMin) and
                                                           (part_size[2] <= box_size[4])):
                    part_info_and_ranges.append(part_size + box_size)
                    break
                else:
                    continue
        part_info_and_ranges.sort(key=lambda x: x[5])  # 按288个区域的Index进行排序
        for row in part_info_and_ranges:
            range_nums.append(row[5])
        # key = list(set(range_nums))  # 整合列表中的重复元素，使列表元素不重复，并将其按照大小进行排序
        # key.sort(key=range_nums.index)
        for i in range(len(part_info_and_ranges)):
            for range_num in range_nums:
                if range_num == part_info_and_ranges[i][5]:
                    self.info_box_part_dicts[range_num].append(part_info_and_ranges[i])
                    break
                else:
                    continue
        for key, value in self.info_box_part_dicts.items():
            self.remain_num_and_state[key] = [value[0][11], -1]
        # temp_box_part_dicts = self.info_box_part_dicts
        for key, value in self.info_box_part_dicts.items():  # 优先级大小：超过一包>可以打一包>不可以打一包
            if len(value) > value[0][11]:
                # self.is_recombine_package = 1
                del self.info_box_part_dicts[key]
                del self.remain_num_and_state[key]
                # print u"超过一包"
                # print key, value
                error_id = self.beyond_one_package_handle(key, value)
            else:
                if (len(value) >= value[0][10]) and (len(value) <= value[0][11]):
                    # self.is_recombine_package = 0
                    if len(value) == value[0][11]:
                        self.remain_num_and_state[key] = [value[0][11] - len(value), 2]
                    else:
                        self.remain_num_and_state[key] = [value[0][11] - len(value), 1]
                    # print u"可以打一包"
                    # print key, value
                else:
                    if len(value) < value[0][10]:
                        # self.is_recombine_package = -1
                        self.remain_num_and_state[key] = [value[0][11] - len(value), 0]
                        # print u"不能够打一包，从临近且有部件的区域寻找，进行重组"
                        # print key, value
                        # self.less_one_package_handle(key, value)
                    else:
                        error_id = 110
        return error_id

    def beyond_one_package_handle(self, key, value):
        """
        按H为第一优先级，W为第二优先级进行升级排序，截取以box_block_up个数进行划分，此处缺点是截取点左右可能有相同尺寸的部件，
        导致相同尺寸可能不能放在一起进行打包
        :param key:
        :param value:二维列表
        :return:
        """
        error_id = 0
        value.sort(key=lambda x: (x[2], x[1]))  # 将其按H为第一优先级，W为第二优先级进行排序
        if len(value) % value[0][-1] == 0:
            id_i = len(value) / value[0][-1]
        else:
            id_i = len(value) / value[0][-1] + 1
        j = 1  # 累计划分的包数
        package_i = 1  # 累计划分的块数到box_block_up
        for i in range(len(value)):
            if j < id_i:
                if package_i < value[0][-1]:
                    value[i][5] = key + "-" + str(j)
                    self.info_box_part_dicts[key + "-" + str(j)].append(value[i])
                    package_i += 1
                else:
                    value[i][5] = key + "-" + str(j)
                    self.info_box_part_dicts[key + "-" + str(j)].append(value[i])
                    self.remain_num_and_state[key + "-" + str(j)] = [0, 2]
                    package_i = 1
                    j += 1
            elif j == id_i:
                value[i][5] = key + "-" + str(j)
                self.info_box_part_dicts[key + "-" + str(j)].append(value[i])
                remain_num = len(value) - (id_i - 1) * value[0][-1]
                if remain_num == value[0][-1]:
                    self.remain_num_and_state[key + "-" + str(j)] = [value[0][-1] - remain_num, 2]
                if (remain_num >= value[0][-2]) and (remain_num < value[0][-1]):
                    self.remain_num_and_state[key + "-" + str(j)] = [value[0][-1] - remain_num, 1]
                if remain_num < value[0][-2]:
                    # print u"不能打一包，须重组！"
                    self.remain_num_and_state[key + "-" + str(j)] = [value[0][-1] - remain_num, 0]
            else:
                error_id = 105
        return error_id

    def recombine_remain_part(self):
        """
        将不能够打一包的区域进行重组recombine
        算法：先将区域剩余块数比较少的优先按照部件尺寸距离区域中心最近的板子放到该区域，计算当前包数的重量，如果当前区域大于该
        区域重量最大容量，停止往该区域放板子
        :return:
        """
        remain_lists = []
        remain_lists1 = []
        remain_lists2 = []
        remain_lists3 = []
        weight = 0
        current_weight = 0
        for key, value in self.remain_num_and_state.items():
            for row in self.info_box_part_dicts[key]:
                weight = weight + row[1] * row[2] * row[3] * BaseMaterialDensity / (10 ** 9)
            remain_lists.append([key, value[0], value[1], self.info_box_part_dicts[key][0][-1], round(weight, 4)])
            weight = 0
        remain_lists.sort(key=lambda x: (x[4], x[2]), reverse=False)  # 按照区域所放得部件重量和包状态进行升序排序
        # 若有可打一包的，取包重量最小为为目标区域；若无可打一包的，取不可打一包的重量最大为为目标区域
        for remain_list in remain_lists:
            if remain_list[2] == 0:
                remain_lists1.append(remain_list)  # 不可打一包的放remain_lists1中
            elif remain_list[2] == 1:
                remain_lists2.append(remain_list)  # 可打一包的放remain_lists2中
            else:
                remain_lists3.append(remain_list)  # 正好打一包的放remain_lists3中
        remain_lists1.sort(key=lambda x: x[4], reverse=True)
        remain_lists = remain_lists2 + remain_lists1
        is_finish = False
        for i in range(len(remain_lists)):
            if is_finish or ((not 1 in [recombine[2] for recombine in remain_lists]) and len(
                    remain_lists) == 1):  # 组件下有且仅有一包且不能够打一包,此时把这些部件放在一包
                break
            if self.info_box_part_dicts[remain_lists[i][0]] != []:
                target_key = remain_lists[i][0]
            else:
                continue
            current_weight = remain_lists[i][4]
            while current_weight < OnePackageMaxWeight:
                is_recombine_area, part_id, weight = self.find_one_most_suitable_part(target_key,
                                                                                      self.info_box_part_dicts[
                                                                                          target_key][0][6:10])
                current_weight = current_weight + weight
                if (0 not in [r[1] for r in self.remain_num_and_state.values()]) or (not is_recombine_area):
                    is_finish = True
                    break

    def find_one_most_suitable_part(self, target_key, range_lists):
        """
        寻找当前没有放好的部件，使其离目标区域中心距离最近，注：要考虑尺寸相同时不止一块的情况
        :param range_lists:
        :return:
        """
        is_recombie_area = True
        part_id = ''
        weight = 0
        x_center = (range_lists[0] + range_lists[1]) / 2.0
        y_center = (range_lists[2] + range_lists[3]) / 2.0
        remain_list_3Ds = []
        remain_list_2Ds = []
        for k, v in self.remain_num_and_state.items():
            if k != target_key:  # 将不是当前区域k的部件放到目标区域key
                if v[0] != 0:  # 当前区域k有可剩余空间放
                    if v[1] == 0:  # 从不可打一包的里面找
                        remain_list_3Ds.append(self.info_box_part_dicts[k])
        for row in remain_list_3Ds:
            for r in row:
                remain_list_2Ds.append(r)
        if len(remain_list_2Ds) == 0:
            is_recombie_area = False
            part_id = ''
            weight = 0
        # 将所有没有放好部件按照到目标区域的距离进行升序排序，取第一个部件即离目标区域中心距离最近的部件,尺寸相同也考虑在内
        if is_recombie_area:
            remain_list_2Ds.sort(key=lambda x: (x[1] - x_center) ** 2 + (x[2] - y_center) ** 2)
            part_id = remain_list_2Ds[0][0]
            weight = round(
                remain_list_2Ds[0][1] * remain_list_2Ds[0][2] * remain_list_2Ds[0][3] * BaseMaterialDensity / (
                            10 ** 9), 4)
            current_key = remain_list_2Ds[0][5]
            for row in self.info_box_part_dicts[current_key]:
                if part_id in row:
                    self.info_box_part_dicts[current_key].remove(row)
                    self.info_box_part_dicts[target_key].append(row)
            if self.info_box_part_dicts[current_key] == []:
                self.remain_num_and_state[current_key][1] = 5
            self.remain_num_and_state[current_key][0] = self.remain_num_and_state[current_key][0] + 1
            self.remain_num_and_state[target_key][0] = self.remain_num_and_state[target_key][0] - 1
            target_box_block_up = self.info_box_part_dicts[target_key][0][-1]
            if self.remain_num_and_state[target_key][0] == target_box_block_up:
                self.remain_num_and_state[target_key][1] = 2
            else:
                self.remain_num_and_state[target_key][1] = 1
        return is_recombie_area, part_id, weight

    def get_box_long_short(self, value, md=0):
        """
        取该包最大长度尺寸和最大宽度尺寸
        :param value:
        :param md:
        :return:
        """
        delt_height = []
        delt_width = []
        box_type = []
        value.sort(key=lambda x: (x[2], x[1]), reverse=True)  # 按照(height,width)进行降序排列
        height_list = [row[2] for row in value]
        width_list = [row[1] for row in value]
        box_long = int(max(height_list))
        box_short = int(max(width_list))
        # if md != 0:
        #     sql = "SELECT `Box_type`, `Box_long`, `Box_short`, `Box_height` FROM `equipment_package_box` WHERE `State`=5"
        #     da_box = MyDb.Database()
        #     info_box = da_box.get_more_row(sql)
        #     info_box = list(info_box)
        #     for i in range(len(info_box)):
        #         delt_height.append(math.fabs(info_box[i][1] - box_long))
        #         delt_width.append(math.fabs(info_box[i][2] - box_short))
        #         box_type.append(info_box[i][0])
        #     assert len(delt_height) == len(delt_width)
        #     assert len(delt_width) == len(box_type)
        #     delt_width_height = [h + w for h, w in zip(delt_height, delt_width)]
        #     delt = min(delt_width_height)
        #     id = delt_width_height.index(delt)
        #
        #     for j in range(len(info_box)):
        #         if j == id:
        #             box_long = info_box[j][1]
        #             box_short = info_box[j][2]
        #             obj_box_type = info_box[j][3]
        #             break
        return box_long, box_short

    def spilt_package(self, key, value):
        """
        拆分算法：将层数大于最大层数阈值的包进行拆分
        例如：
            将一个大于10的数拆分成不超过10的多个值相加形式，且各值之间相差最小，如17=8+9,18=9+9,29=10+10+9等
        :param key:
        :param value:
        :return:
        """
        i = 0
        value.sort(key=lambda x: (x[2], x[1]), reverse=True)  # 按照(height,width)进行降序排列
        if len(value) % OnePackageMaxLayers == 0:  # 首先判断它是否能被OnePackageMaxLayers整数
            key_num = len(value) / OnePackageMaxLayers
        else:
            key_num = len(value) / OnePackageMaxLayers + 1
        if len(value) % key_num == 0:
            new_nums = [len(value) / key_num] * key_num
        else:
            new_nums = [len(value) / key_num] * key_num
            while sum(new_nums) != len(value):
                new_nums[i] = new_nums[i] + 1
                i += 1
        new_nums.insert(0, 0)  # 在new_nums列表最前面插入一个0，用于下面将value列表拆分
        del self.info_box_part_dicts[key]  # 删除原来的包
        for i in range(len(new_nums) - 1):
            self.info_box_part_dicts[key + '-' + str(i + 1)] = value[new_nums[i]: new_nums[i] + new_nums[
                i + 1]]  # 加入拆分后的新包

    def layout_2dim_simple_binary_tree(self, key, value):
        """
        简单二叉树方法排每一层(暂未使用)
        :param key:
        :param value:
        :return:
        """
        value.sort(key=lambda x: (x[2], x[1]), reverse=True)
        value = [row + [0] for row in value]  # 增加一列记录状态
        height_list = [row[2] for row in value]
        width_list = [row[1] for row in value]
        if len(value) <= OnePackageMaxLayers:  # 这样控制最大层数不好
            max_part_height = max(height_list) + 20  # 取当前包的最大height并加上20可移动量为区域高度
            max_part_width = max(width_list) + 20  # 取当前包的最大width并加上20可移动量为区域宽度
        else:
            max_part_height = round(np.mean(height_list) + max(height_list))
            max_part_width = round(np.mean(width_list) + max(width_list))
        lowest_horiztonal_algorithm = LowestHoriztonalAlgorithm(key, value, max_part_height, max_part_width)
        plates, current_layer_num = lowest_horiztonal_algorithm.put_each_package()
        '''
        layer_num = 0
        plates = []
        """
        plates与Plate列表：
        column 12列字段协议:
        [x,y,low_x_length,low_y_length,is_change,height,width,is_change_state,thick,plies_num,package_id,part_id]
        column 11列字段协议:
        [x,y,low_x_length,low_y_length,height,width,thick,is_rotate,plies_num,package_id,part_id]
        x,y:以右上角为坐标原点，向右为x+，向下为y+建立坐标系
        low_x_length,low_y_length：最低水平线(以距离x轴距离为依据)的坐标x轴长度与y轴长度
        is_change：low_x_length,low_y_length是否转变，0为不转变，1为转变
        plies_num,package_num：该部件属于第几层；该部件属于第几包
        is_change_state:部件高宽是否旋转，0不旋转，1旋转
        """
        left_area = max_part_height * max_part_width
        while len(value) != 0:
            current_level = 0  # 当前水平线
            total_level = 1
            position = 0
            spill = False
            Plate = [[0 for col in range(11)] for row in range(len(value) * 10)]
            Plate[0] = [0, 0, max_part_height, max_part_width, 0, 0, 0, 0, 0, 0, 0]
            while (current_level < total_level):  # 加入这个条件主要是为了，判断每一块新生成的板能否容下未排样的部件
                long_edge = Plate[current_level][2]
                short_edge = Plate[current_level][3]
                for i in range(0, len(value)):
                    if value[i][-1] == 0:  # 0表示部件没放好
                        if ((long_edge >= value[i][2]) and (short_edge >= value[i][1])):  # 芯板能放进去
                            if position >= OneLayerMaxPlates:  # 每层最多放10块,多于10块，溢出
                                spill = True
                                break
                            value[i][-1] = 1  # 1表示部件可放
                            position += 1
                            left_area = left_area - value[i][2] * value[i][1]
                            Plate[current_level][4] = value[i][2]
                            Plate[current_level][5] = value[i][1]
                            Plate[current_level][6] = value[i][3]
                            Plate[current_level][10] = value[i][0]  # 把该部件的编号放入Plate列表里，用于输出生成工位工单
                            if ((value[i][2] >= short_edge - value[i][1]) and (
                                    Plate[current_level][7] == 0)):  # 新生成第一块待填充芯板是横的，且上一块待填充芯板是横的
                                Plate[total_level][7] = 0  # 当前待填充芯板的旋转状态为0
                                Plate[total_level][2] = value[i][2]  # 待填充芯板的尺寸
                                Plate[total_level][3] = short_edge - value[i][1]
                                Plate[total_level][0] = Plate[current_level][0]  # 赋值左下角坐标
                                Plate[total_level][1] = Plate[current_level][1] + value[i][1]
                            elif ((value[i][2] < short_edge - value[i][1]) and (
                                    Plate[current_level][7] == 0)):  # 新生成第一块待填充芯板是竖直的，且上一块待填充芯板是横的
                                Plate[total_level][7] = 1
                                Plate[total_level][2] = short_edge - value[i][1]  # 赋值当前待填充芯板的尺寸
                                Plate[total_level][3] = value[i][2]
                                Plate[total_level][0] = Plate[current_level][0]
                                Plate[total_level][1] = Plate[current_level][1] + value[i][1]
                            elif ((value[i][1] >= long_edge - value[i][2]) and (Plate[current_level][7] == 1)):
                                Plate[total_level][2] = value[i][1]
                                Plate[total_level][3] = long_edge - value[i][2]
                                Plate[total_level][7] = 0
                                Plate[total_level][0] = Plate[current_level][0]
                                Plate[total_level][1] = Plate[current_level][1] + value[i][2]
                            elif ((value[i][1] < long_edge - value[i][2]) and (
                                    Plate[current_level][7] == 1)):  # 新生成的第一块待填充芯板是竖直的，并且上一块待填充芯板是竖直的
                                Plate[total_level][3] = value[i][1]
                                Plate[total_level][2] = long_edge - value[i][2]
                                Plate[total_level][7] = 1
                                Plate[total_level][0] = Plate[current_level][0]
                                Plate[total_level][1] = Plate[current_level][1] + value[i][2]

                            if ((short_edge <= long_edge - value[i][2]) and (
                                    Plate[current_level][7] == 0)):  # 新生成的第二块可填充区域是横的，且上一块待填充区域也是横的（四种情况）
                                Plate[total_level + 1][7] = 0  # 旋转状态
                                Plate[total_level + 1][3] = short_edge  # 赋值可填充区域长度
                                Plate[total_level + 1][2] = long_edge - value[i][2]
                                Plate[total_level + 1][0] = Plate[current_level][0] + value[i][2]  # 赋值左下角坐标
                                Plate[total_level + 1][1] = Plate[current_level][1]
                            elif ((short_edge > long_edge - value[i][2]) and (Plate[current_level][7] == 0)):
                                Plate[total_level + 1][7] = 1
                                Plate[total_level + 1][3] = long_edge - value[i][2]
                                Plate[total_level + 1][2] = short_edge
                                Plate[total_level + 1][0] = Plate[current_level][0] + value[i][2]
                                Plate[total_level + 1][1] = Plate[current_level][1]
                            elif ((long_edge >= short_edge - value[i][1]) and (Plate[current_level][7] == 1)):
                                Plate[total_level + 1][7] = 1
                                Plate[total_level + 1][3] = short_edge - value[i][1]
                                Plate[total_level + 1][2] = long_edge
                                Plate[total_level + 1][0] = Plate[current_level][0] + value[i][1]
                                Plate[total_level + 1][1] = Plate[current_level][1]
                            elif ((long_edge < short_edge - value[i][1]) and (Plate[current_level][7] == 1)):
                                Plate[total_level + 1][7] = 0
                                Plate[total_level + 1][2] = short_edge - value[i][1]
                                Plate[total_level + 1][3] = long_edge
                                Plate[total_level + 1][0] = Plate[current_level][0] + value[i][1]
                                Plate[total_level + 1][1] = Plate[current_level][1]
                            total_level = total_level + 2
                            del value[i]
                            break
                if spill:
                    break
                current_level += 1
            layer_num += 1  # 记录部件所属当前层数
            if layer_num > 10:
                print time.strftime("%Y年%m月%d日 %H:%M:%S  ", time.localtime(time.time())) + \
                      u"该包超过10层，请重新打！"
                break
            for plate in Plate:
                if plate[-1] != 0:
                    plate[-3] = layer_num
                    plates.append(plate)
            '''
        return plates

    def send_package_info_to_work_package_task_list(self, info_package_plies_plate):
        """
        将包信息存储到work_package_task_list表单
        存到每层部件信息字段Plies1_element_information1的协议：
        x & y & height & width & is_change & part_id
        is_change：low_x_length,low_y_length是否转变，0为不转变，1为转变
        :param info_package_plies_plate:
        :return:
        """
        error_id = 0
        split_sym = '&'
        if self.is_connection_db():
            for package in info_package_plies_plate:  # 对组件下每一包进行循环，一包对应work_package_task_list表单一条记录
                package_id = package[-1][-2]
                total_plies = max([row[-3] for row in package])
                total_area = sum([row[4] * row[5] / (10 ** 6) for row in package])
                sec_id = package[-1][-1].split('P')[0]
                create_package_time = datetime.datetime.now()
                ij = [row[-3] for row in package]
                same_count = Counter(ij)
                cursor = self.db.cursor()
                # cursor.execute("INSERT INTO `work_package_task_list` (`Ap_id`, `Total_plies`, `Total_area_gs`, "
                #                "`Sec_id`, `Create_Time`, `Long`, `Short`, `Order_id`, `Package_num`) VALUES "
                #                "('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" %
                #                (package_id, total_plies, total_area, sec_id, create_package_time, package[0][2],
                #                 package[0][3], sec_id.split('S')[0], len(package)))
                cursor.execute(
                    "INSERT INTO `work_package_task_list` (`Ap_id`, `Total_plies`, `Total_area`, `Sec_id`, `Create_Time`, `Long`, `Short`, `Order_id`, `Package_num`) VALUES ('%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s', '%s')" % (
                    package_id, total_plies, total_area, sec_id, create_package_time, package[0][2], package[0][3],
                    sec_id.split('S')[0], len(package)))
                self.db.commit()
                cursor.close()
                for i in range(total_plies):  # 循环层数
                    element_info = [row for row in package if row[-3] == i + 1]
                    num_plies_i = 'Num_plies' + str(i + 1)
                    for j in range(same_count[i + 1]):  # 循环层下面的块数
                        current_part_id = element_info[j][-1]
                        plies_i_element_information_j = 'Plies' + str(i + 1) + '_element_information' + str(j + 1)
                        seq = (str(element_info[j][0]), str(element_info[j][1]), str(element_info[j][4]),
                               str(element_info[j][5]), str(element_info[j][7]), str(element_info[j][-1]))
                        element_str = split_sym.join(seq)
                        cursor = self.db.cursor()
                        cursor.execute(
                            "UPDATE `work_package_task_list` SET `%s`='%s', `%s`='%s' WHERE  `Ap_id`='%s'" % (
                            plies_i_element_information_j, element_str, num_plies_i, same_count[i + 1],
                            str(package_id)))
                        self.db.commit()
                        cursor = self.db.cursor()  # 更新order_part_online表单部件所属的package_id
                        cursor.execute(
                            "UPDATE `order_part_online` SET `Package_task_list_ap_id` = '%s' WHERE `Part_id` = '%s'" % (
                            package_id, current_part_id))
                        self.db.commit()
            self.db.close()
        else:
            self.log = get_time() + u"调用send_package_info_to_work_package_task_list()方法出现错误！"
            self.write_log()
            print(self.log)
            error_id = 105
        return error_id

    def update_package_info_to_db(self):
        error_id = 0
        if self.is_connection_db():
            cursor = self.db.cursor()
            cursor.execute(
                "UPDATE `order_section_online` SET `Package_state` = 5 WHERE `Sec_id` = '%s'" % (self.section_id))
            self.db.commit()
            self.db.close()
        else:
            error_id = 105
            self.log = get_time() + u"调用update_package_info_to_db()方法出现错误！"
            self.write_log()
            print(self.log)
        return error_id

    def write_log(self):
        log_file = 'log.txt'
        all_files = os.listdir(os.getcwd())  # 获取当前工程项目文件夹下所有文件名
        if log_file not in all_files:  # 若该文件不存在，在当前目录创建一个日志文件
            log_file = open(log_file, 'w+')
            log_file.close()
            log_file = log_file.name
        with open(log_file, 'a+') as file_obj:  # 向日志文件加log
            file_obj.write(self.log + "\r")


class LowestHoriztonalAlgorithm(object):
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


def get_time():
    t = time.strftime('%Y{y}%m{m}%d{d} %H{h}%M{f}%S{s}').format(y=u'年', m=u'月', d=u'日', h=u'时', f=u'分', s=u'秒')
    return t


if __name__ == '__main__':
    pack = CardBoardPack()
    loop = LoopTimer(interval=2, target=pack.package_main)
    loop.start()
    loop.join()
