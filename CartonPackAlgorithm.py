#!/usr/bin/env python3
# encoding:utf-8


from MYSQL.MysqlHelper import Mysql, MysqlPool
from CONFING.Setting import *
from ThreadHelper import LoopTimer
import numpy as np
import math
import random
import matplotlib.pyplot as plt

"""
物品item的编码方式(所有的item的编码后即为解，也即为打包方案)：
PART={
    str 板件类型    part_type
    str 板件部件编号  part_id
    float   板件空间坐标位置  (x,y,layer)
    float   板件三维尺寸  (length,width,thickness)
    float   板件面积    area
    float   板件重量    weight
    int     板件摆放方向  rotation
    str     板件所放纸箱类型    box_type
    float   板件所放纸箱尺寸    (L,W,H)
    str     板件的打包编号  
}
"""


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
        :return: False(没有需要打包的组件) or Sec_id(组件号)
        """
        sql = "SELECT `Index`, `Sec_id` FROM `order_section_online` WHERE `Package_state`=0"
        section_info = self.mysql.do_sql_one(sql)
        if section_info is None:  # 没有需要打包的组件
            return False
        else:
            return section_info[1]

    def get_part_info(self):
        """
        获取部件表单信息(原始数据)
        :return: False(没有组件或部件信息) or part_lists(部件二维列表信息)
        """
        sec_id = self.is_needing_pack()
        part_lists = []
        if sec_id:
            sql = "SELECT `Contract_id`, `Order_id`, `Sec_id`, `Part_id`, `Door_type`, `Door_height`, `Door_width`, " \
                  "`Door_thick`, `Package_state`, `Element_type_id` FROM `order_part_online` WHERE `Sec_id` = '%s'" % \
                  sec_id
            part_info = self.mysql.do_sql(sql)
            if part_info is None:  # 部件表单无部件信息
                return False
            else:
                for i in range(len(part_info)):
                    part_lists.append(list(part_info[i]))
                return part_lists
        else:
            return False

    def get_box_info(self):
        """
        获取纸箱表单信息(原始数据)
        :return: False(没有纸箱信息) or box_lists(纸箱二维列表信息)
        """
        box_lists = []
        sql = "SELECT `Box_type`, `Box_long`, `Box_short`, `Box_height` FROM `equipment_package_box` WHERE " \
              "`State`=5"
        box_info = self.mysql.do_sql(sql)
        if box_info is None:
            return False
        else:
            for i in range(len(box_info)):
                box_lists.append(list(box_info[i]))
            return box_lists


def PartSort(part_lists):
    """
    将部件按照长为第一优先级，宽为第二优先级进行从大到小排序
    :param part_lists: 原始部件列表信息
    :return:
    """
    if isinstance(part_lists, list):
        if len(part_lists) != 0:
            part_sort_lists = part_lists[:]  # 复制一份副本，避免part_lists随part_sort_lists同时变化
            # 按照部件的长为第一优先级，宽为第二优先级进行从大到小排序
            part_sort_lists.sort(key=lambda x: (x[part_length_index], x[part_width_index]), reverse=True)
            return part_sort_lists


def PartSizeMax(part_lists):
    if isinstance(part_lists, list):
        if len(part_lists) != 0:
            return max([part_length_col for part_length_col in part_lists])


def SelectBox(max_part_length, max_part_width, box_lists):
    """
    从纸箱库中选择一个合适的纸箱进行待装箱
    :param max_part_length: 最大部件长度
    :param max_part_width: 最大部件宽度
    :param box_lists: 纸箱库信息列表
    :return: 一个合适的纸箱
    """




if __name__ == '__main__':
    data = GetData()
    part = data.get_part_info()
    if part:
        print(part)
        part = PartSort(part)
        box = data.get_box_info()
        print(box)


