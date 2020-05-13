# coding=utf-8
# use geatpy lib to build algorithm for solving packing problem
# gs by 2020-04-15

import numpy as np
import time, turtle, os
import geatpy as ea
import matplotlib.pyplot as plt
from MyProblem import *  # 导入自定义问题接口

n = N  # N1-->10个rect


def check():
    global resDir, curDate, curTime
    curDate = time.strftime('%Y{y}%m{m}%d{d}').format(y='', m='', d='')
    curTime = time.strftime('%Y{y}%m{m}%d{d}%H{h}%M{f}%S{s}').format(y='-', m='-', d=' ', h='-', f='-', s='')
    resDir = '.\\res\\res%s' % curDate
    if not os.path.isdir(resDir):  # 存在.\\res\\iterG，并且是dir
        os.makedirs(resDir)
        print('It is successful to create %s dir.' % resDir)


class LayoutGraph:
    def __init__(self, resSol):
        self.resSol = resSol
        self.pen = turtle.Pen()
        turtle.hideturtle()
        self.pen.speed(12)
        self.pen.pencolor('grey')
        self.drawBoxL, self.drawBoxW =1000, 600
        self.boxL, self.boxW = resSol[0][10], resSol[0][11]
        turtle.setup(width=1040, height=640, startx=200, starty=50)
        turtle.getscreen().title('装箱布局')
        self.drawBox()
        self.drawRect(-500, -300, self.drawBoxL, self.drawBoxW)
        # self.writeText(-500 + self.drawBoxL/2, -320, str(self.boxL))
        # self.writeText(-500 + self.drawBoxL + 20, -320+self.drawBoxW/2, str(self.boxW))

        # self.pen.forward(200)
        self.drawLayout()
        self.pen.hideturtle()
        self.layoutImg()
        if RUNMODE == 0:
            turtle.resetscreen()
        else:
            turtle.done()

    def layoutImg(self):
        filePath = os.path.join(resDir, 'layout%s.eps' % curTime)
        ts = turtle.getscreen()
        ts.getcanvas().postscript(file=filePath)
        print('It is successful to save layout graph in %s.' % filePath)

    def drawBox(self):
        if self.boxL <= self.drawBoxL and self.boxW <= self.drawBoxW:
            ratioL, ratioW = self.drawBoxL / self.boxL, self.drawBoxW / self.boxW
            self.ratio = min(ratioL, ratioW)
            self.drawBoxL, self.drawBoxW = int(self.boxL*self.ratio), int(self.boxW*self.ratio)
        else:
            if self.boxL / 2 <=self.drawBoxL and self.boxW / 2 <= self.drawBoxW:
                self.ratio = min(self.drawBoxL/(self.boxL / 2), self.drawBoxW/(self.boxW / 2))
                self.drawBoxL, self.drawBoxW = int(self.boxL * self.ratio/2), int(self.boxW * self.ratio/2)
            else:
                print('please check the size of box.')

    def move(self, x, y):
        self.pen.penup()
        self.pen.goto(x, y)
        self.pen.pendown()

    def writeText(self, x, y, text):
        self.move(x, y)
        self.pen.write(text, move=False, align='center', font=('arial', 10, 'normal'))

    def drawRect(self,lbx,lby,len,width):
        self.move(lbx, lby)
        for i in range(2):
            self.pen.forward(len)
            self.pen.left(90)
            self.pen.forward(width)
            self.pen.left(90)

    def drawLayout(self):
        self.pen.pencolor('grey')
        for rect in self.resSol:
            lbx, lby = rect[0:2]
            len, width = rect[4:6]
            rect_id, rotate = rect[7:9]
            draw_lbx, draw_lby = int(self.ratio*lbx), int(self.ratio*lby)
            draw_len, draw_width = int(self.ratio*len), int(self.ratio*width)
            if rotate == 1:
                draw_len, draw_width = int(self.ratio * width), int(self.ratio * len)
            self.pen.fillcolor(220/255,220/255,220/255)
            self.pen.begin_fill()
            self.drawRect(-500+draw_lbx,-300+draw_lby,draw_len,draw_width)
            self.pen.end_fill()
            # self.writeText(-500 + draw_lbx + draw_len / 2, -300 + draw_lby + draw_width / 2, str(rect_id))


def seat_main():
    """================================目录检查============================"""
    check()
    """================================实例化问题对象============================"""
    # problem = MyProblem()  # 生成问题对象
    #
    # """==================================种群设置==============================="""
    # Encodings = ['P', 'RI']        # 编码方式，采用排列编码和二进制编码混合方式
    # NIND = 80  # 种群规模
    # # 创建区域描述器，这里需要创建两个，前n个变量用P编码，后n个变量RI(0,1)整数离散编码
    # Field1 = ea.crtfld(Encodings[0], problem.varTypes[:n], problem.ranges[:, :n], problem.borders[:, :n])
    # Field2 = ea.crtfld(Encodings[1], problem.varTypes[n:], problem.ranges[:, n:], problem.borders[:, n:])
    # Fields = [Field1, Field2]
    # population = ea.PsyPopulation(Encodings, Fields, NIND)  # 实例化种群对象（此时种群还没被初始化，仅仅是完成种群对象的实例化）
    #
    # """================================算法参数设置============================="""
    # myAlgorithm = ea.soea_psy_SEGA_templet(problem, population)  # 实例化一个算法模板对象
    # myAlgorithm.MAXGEN = 1000  # 最大进化代数
    # # myAlgorithm.mutOpers[1].Pm = 0.5  # 变异概率
    # myAlgorithm.drawing = 1  # 设置绘图方式（0：不绘图；1：绘制结果图；2：绘制目标空间过程动画；3：绘制决策空间过程动画）
    # # 设置初始评价次数，因为使用Algorithm.call_aimFunc()时，初始self.evalsNum=None，否则self.evalsNum += pop.sizes报错
    # myAlgorithm.evalsNum = 0
    #
    # """===========================根据先验知识创建先知种群======================="""
    # orientSeq = np.random.randint(2, size=(7, N))
    # prophetChrom = [SORT, orientSeq]
    # prophetPop = ea.PsyPopulation(Encodings, Fields, 7, prophetChrom)
    # myAlgorithm.call_aimFunc(prophetPop)  # 计算先知种群的目标函数值及约束（假如有约束）
    #
    # """===========================调用算法模板进行种群进化======================="""
    # [population, obj_trace, var_trace] = myAlgorithm.run(prophetPop)  # 执行算法模板
    # population.save()  # 把最后一代种群的信息保存到文件中
    #
    # # 输出结果
    # best_gen = np.argmin(problem.maxormins * obj_trace[:, 1])  # 记录最优种群个体是在哪一代
    # best_ObjV = obj_trace[best_gen, 1]
    # print('时间已过 %s 秒' % (myAlgorithm.passTime))
    # print('有效进化代数：%s' % (obj_trace.shape[0]))
    # print('最优的一代是第 %s 代' % (best_gen + 1))
    # print('评价次数：%s' % (myAlgorithm.evalsNum))
    # print('最优容器装填率为：%s' % best_ObjV)
    # print('最优装箱对应的编码：')
    # x = var_trace[best_gen, :].astype(dtype=np.int)
    # print(list(x))
    # print('最优装箱对应的编码：')
    # x = np.array([7, 6, 1, 9, 4, 10, 2, 8, 3, 5, 1, 0, 1, 1, 1, 0, 1, 1, 0, 0])
    # x = np.array([13, 14, 15, 16, 40, 41, 10, 11, 12, 48, 49, 50, 28, 29, 53, 54, 39, 58, 59, 32, 33, 34, 37, 38, 46, 47, 42, 43, 30, 31, 44, 45, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 1, 2, 3, 4, 51, 52, 5, 6, 7, 8, 9, 35, 36, 55, 56, 57,
    #               1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1])
    # x = np.array([1, 9, 11, 15, 17, 24, 25, 10, 14, 22, 23, 2, 3, 5, 18, 7, 8, 12, 19, 20, 21, 6, 16, 13, 4]+[0]*25)
    # x = np.array([23, 11, 36, 20, 35, 17, 33, 30, 28, 26, 42, 8, 2, 6, 32, 46, 7, 15, 1, 19, 31, 49, 22, 13, 5, 24, 12, 45, 9, 14, 37, 4, 27, 18, 34, 25, 41, 16, 48, 40, 38, 29, 3, 39, 10, 50, 47, 44, 43, 21,
    #               0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0])
    # x = np.array([12, 6, 36, 9, 13, 30, 2, 1, 22, 32, 11, 40, 17, 48, 38, 24, 49, 34, 26, 25, 19, 3, 10, 28, 29, 33, 15, 23, 21, 45, 14, 4, 20, 31, 47, 39, 37, 8, 42, 16, 41, 5, 7, 50, 46, 43, 35, 27, 44, 18, 0, 1, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 1, 1, 1, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 1])
    # 绘图
    # plt.figure()
    # plt.plot(problem.places[best_journey.astype(int), 0], problem.places[best_journey.astype(int), 1], c='black')
    # plt.plot(problem.places[best_journey.astype(int), 0], problem.places[best_journey.astype(int), 1], 'o', c='black')
    # for i in range(len(best_journey)):
    #     plt.text(problem.places[int(best_journey[i]), 0], problem.places[int(best_journey[i]), 1],
    #              chr(int(best_journey[i]) + 65), fontsize=20)
    # plt.grid(True)
    # plt.xlabel('x坐标')
    # plt.ylabel('y坐标')
    # plt.savefig('roadmap.svg', dpi=600, bbox_inches='tight')
    x = np.array([1, 2, 21, 22, 23, 18, 19, 20, 36, 8, 7, 6, 5, 4, 24, 25, 26, 27, 35, 40, 41, 17, 12, 14, 9, 13, 10, 11, 15, 16, 29, 30, 31, 32, 33, 34, 28, 39, 38, 37, 3, 42, 43, 44, 46, 47, 48, 49, 45, 50, 0, 1, 1, 1, 1, 0, 1, 1, 1, 1, 0, 1, 0, 1, 1, 1, 1, 0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 1, 1, 0, 1, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 1] )
    volRate, solutions, _ = ImprovementLHLA2D(x).run()
    print('再次计算的最优容器装填率为：%s' % volRate)
    LayoutGraph(solutions)


if __name__ == '__main__':
    seat_main()
