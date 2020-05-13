# coding=utf-8
# build packing problem
# gs by 2020-04-15

import geatpy as ea
from Decode import *


class MyProblem(ea.Problem):
    def __init__(self):
        n = N
        name = 'MyProblem'  # 初始化name（函数名称，可以随意设置）
        M = 1  # 初始化M（目标维数）
        maxormins = [-1]  # 初始化maxormins（目标最小最大化标记列表，1：最小化该目标；-1：最大化该目标）
        Dim = n*2  # 初始化Dim（决策变量维数）
        varTypes = [1] * Dim  # 初始化varTypes（决策变量的类型，元素为0表示对应的变量是连续的；1表示是离散的）
        lb = [1]*n + [0]*n  # 决策变量下界
        ub = [n]*n + [1]*n  # 决策变量上界
        lbin = [1] * Dim  # 决策变量下边界（0表示不包含该变量的下边界，1表示包含）
        ubin = [1] * Dim  # 决策变量上边界（0表示不包含该变量的上边界，1表示包含）
        # 调用父类构造方法完成实例化
        ea.Problem.__init__(self, name, M, maxormins, Dim, varTypes, lb, ub, lbin, ubin)

        # 无需在此处新增属性，此需要在decode使用矩形件数据即可
        # 新增一个属性存储矩形件宽高厚，新增另一个属性存储容器属性
        # self.rectangles = rectlist
        # self.box = boxList

    def aimFunc(self, pop):  # 目标函数
        X = pop.Phen  # 得到决策变量矩阵
        # 解码-->计算pop.ObjV -- type:ndarray dim:(种群数量,1)列向量
        ObjV = []
        for idx, x in enumerate(X):
            volRate, _, putedOrientSeq= ImprovementLHLA2D(x).run()
            ObjV.append(volRate)
            for i in range(N):  # 更新矩形的旋转状态
                pop.Phen[idx, N + i] = putedOrientSeq[i]
                pop.Chroms[1][idx, i] = putedOrientSeq[i]
        pop.ObjV = np.array([ObjV]).T  # 把求得的目标函数值赋值给种群pop的ObjV

    def calReferObjV(self):  # 设定目标数参考值（本问题目标函数参考值设定为理论最优值）
        referenceObjV = np.array([[1]])
        return referenceObjV
