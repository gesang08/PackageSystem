#!/usr/bin/env python3
# encoding:utf-8


from MYSQL.MysqlHelper import Mysql, MysqlPool
from CONFING.Setting import *
from ThreadHelper import LoopTimer
import numpy as np
import math
import random
import matplotlib.pyplot as plt


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
        获取部件表单信息
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
        获取纸箱表单信息
        :return: False(没有纸箱信息) or box_lists(纸箱二维列表信息)
        """
        box_lists = []
        sql = "SELECT `Index`, `Box_type`, `Box_long`, `Box_short`, `Box_height` FROM `equipment_package_box` WHERE " \
              "`State`=5"
        box_info = self.mysql.do_sql(sql)
        if box_info is None:
            return False
        else:
            for i in range(len(box_info)):
                box_lists.append(list(box_info[i]))
            return box_lists


if __name__ == '__main__':
    data = GetData()
    part = data.get_part_info()
    if part:
        print(part)
        box = data.get_box_info()
        print(box)


