#!/usr/bin/env python3
# encoding:utf-8

"""
用遗传算法和粒子群算法求解f(x)= x + 10*sin5x + 7*cos4x在[-10, 10]上的最大值
"""

import numpy as np
import math
import random
import matplotlib.pyplot as plt


class GA:
    def __init__(self, length, count, low, up, retain_rate, random_select_rate, mutation_rate):
        # GA参数初始化
        self.length = length  # 染色体遗传基因长度
        self.count = count  # 种群数量
        self.retain_rate = retain_rate  # 父代保留的百分率，如某一代种群有count个父代，则保留count*self.retain_rate的父代
        self.random_select_rate = random_select_rate  # 选择概率
        self.mutation_rate = mutation_rate  # 基因突变概率
        self.low = low  # 求解最值问题的区间范围
        self.up = up
        self.population = self.init_population(length, count)  # 初始化种群

    def init_chromosome(self, length):
        """
        产生仅包含0，1基因且长度为length的染色体,此过程也称为编码coding过程
        :param length: 染色体基因长度（码长）
        :return:基因二进制编码列表（个体individual的染色体基因）
        """
        chromosome = []
        for i in range(length):
            bit = random.randint(0, 1)
            chromosome.append(bit)
        return chromosome

    def binary_convert_decimal(self, length):
        """
        将基因二进制编码列表转换成十进制数
        :param length: 码长
        :return: 一个十进制数（个体individual）
        """
        d = 0
        chromosome = self.init_chromosome(length)  # chromosome[0]为高位
        chromosome.reverse()
        for i in range(len(chromosome)):
            d += chromosome[i] * 2 ** i
        return d

    def init_population(self, length, count):
        """
        初始数量为count的种群列表
        :param length: 码长
        :param count: 种群数量
        :return: 种群population列表
        """
        return [self.binary_convert_decimal(length) for j in range(count)]

    def evolve(self):
        """
        种群进化包括选择(选择哪些优秀个体进行杂交)、交叉(父代杂交)、变异(基因突变)
        :return:
        """
        parents = self.selection()
        self.crossover(parents)
        self.mutation()

    def selection(self):
        # 对适应度从大到小排序（个体适应度评价）
        garded = [(chromosome, self.fitness(self.decode(chromosome))) for chromosome in self.population]
        garded = [x[0] for x in sorted(garded, key=lambda g: g[1], reverse=True)]
        # 选出适应性强的染色体
        assert len(garded) == self.count
        retain_length = int(len(garded) * self.retain_rate)
        parents = garded[:retain_length]  # 按照self.retain_rate百分率保留父代
        # 选出的是影响不强，但是幸存的染色体
        for chromosome in garded[retain_length:]:  # 从父代的剩余个体中以self.random_select_rate选择率选出幸存个体，添加到保留的父代中
            if random.random() < self.random_select_rate:  # 随机射杀的概率要大于选择率
                parents.append(chromosome)
        return parents

    def crossover(self, parents):
        """
        染色体的交叉，反之，生成新一代的种群
        """
        # 新出生的孩子，最终会被加入存活下来的父母之中，形成新一代的种群
        children = []
        # 需要繁殖的孩子的量
        target_count = len(self.population) - len(parents)
        # 开始根据需要的量进行繁殖
        while len(children) < target_count:
            male = random.randint(0, len(parents) - 1)  # 从parents父代中随机获取一个父亲的index，准备交叉
            female = random.randint(0, len(parents) - 1)  # # 从parents父代中随机获取一个母亲的index，准备交叉
            if male != female:  # 如果父与母亲的染色体一样，交叉（杂交）就没有了意义
                # 从长度为self.length染色体中随机选取交叉点
                cross_pos = random.randint(0, self.length)
                # 生成掩码，方便位操作
                mask = 0
                for i in range(cross_pos):
                    mask |= (1 << i)
                male = parents[male]
                female = parents[female]
                # 孩子将获得父亲在交叉点前的基因和母亲在交叉点后（包括交差点）的基因
                child = ((male & mask) | (female & ~mask))  # 取父亲的1~8个基因，母亲的9~17个基因，进行交叉重组
                # other_child = ((male & ~mask) | (female & mask))  # 取母亲的1~8个基因，父亲的9~17个基因，进行交叉重组
                children.append(child)
                # 经过繁殖后，孩子和父母的数量与原始种群数量相等，可以更新种群
        self.population = parents + children

    def mutation(self):
        """
        变异，对种群的所有个体，随机改变某个个体中的某个基因
        """
        for i in range(len(self.population)):
            if random.random() < self.mutation_rate:
                j = random.randint(0, self.length - 1)
                self.population[i] ^= 1 << j  # 此处如果用| or & 不能保证基因会发生突变

    def decode(self, chromosome):
        """
        解码是将二进制或二进制转十进制的数映射到[low, up]区间的实数-->对应的的x轴数值
        :param chromosome:十进制数个体individual
        """
        a=self.low + chromosome * (self.up - self.low) / (2 ** self.length - 1)
        print(a)
        return a

    def fitness(self, x):
        """
        适应度函数
        :param x:解码后实数区间的x值
        :return: 函数值y
        """
        y = x + 10 * math.sin(5 * x) + 7 * math.cos(4 * x)
        return y

    def result(self):
        """
        获得当前代的最优值点[x, y]
        :return: [x, y]
        """
        # 对适应度从大到小排序
        garded = [(chromosome, self.fitness(self.decode(chromosome))) for chromosome in self.population]
        garded = [x[0] for x in sorted(garded, key=lambda g: g[1], reverse=True)]
        return [self.decode(garded[0]), self.fitness(self.decode(garded[0]))]


def code_length(low, up, accuracy):
    """
    针对二进制映射到精度为accuracy的实数区间的码长计算公式
    :param low:区间下限
    :param up:区间上限
    :param accuracy:精度
    :return:至少需要的码长
    """
    return int(math.log(int((up - low) / accuracy) + 1, 2))  # int()函数是向下取整


def plot_result(ga, result):
    x = np.linspace(-10, 10, num=10000)
    y = np.array([ga.fitness(x_value) for x_value in x])
    plt.plot(x, y)
    plt.plot(result[0], result[1], 'o')
    plt.show()


class PSO:
    def __init__(self, low, up, w, c1, c2, count):
        self.low = low
        self.up = up
        self.w = w
        self.c1 = c1
        self.c2 = c2
        self.count = count
        self.gbest = 0  # 种群当前最好位置
        self.population = self.init_population(low , up ,count)

    def init_population(self, low, up, count):
        """
        在[low,up]上随机生成count个粒子
        :param low: 区间下限
        :param up: 区间上限
        :param count: 种群数量
        :return: 种群列表
        """
        pop = []
        for i in range(count):
            bird = Bird()
            bird.position = np.random.uniform(low, up)  # 随机产生粒子的当前位置（x坐标）
            bird.speed = 0
            bird.fitness = self.fitness(bird.position)  # 给类的实例化添加不存在的属性
            bird.pbest = bird.fitness
            pop.append(bird)
        return pop

    def fitness(self, x):
        """
        适应度值计算函数
        :param x: 粒子的位置（x坐标）
        :return: 适应度，此处也为y值
        """
        return x + 10 * np.sin(5 * x) + 7 * np.cos(4 * x)

    def g_best(self):
        """
        找到全局最优解
        :return:
        """
        for individual in self.population:
            if individual.fitness > self.fitness(self.gbest):
                self.gbest = individual.position

    def update(self):
        """
        更新粒子的位置和速度
        :return:
        """
        t = 1  # t一般默认取1
        for individual in self.population:
            speed = self.w * individual.speed + self.c1 * np.random.random() * (individual.pbest - individual.position) + \
                self.c2 * np.random.random() * (self.gbest - individual.position)
            position = individual.position + speed * t
            if self.low < position < self.up:
                individual.position = position  # 更新位置
                individual.speed = speed  # 更新速度
                individual.fitness = self.fitness(individual.position)  # 更新适应度
                if individual.fitness > self.fitness(individual.pbest):
                    individual.pbest = individual.position  # 更新本粒子历史最好位置

    def evolve(self):
        """
        粒子进化
        :return:
        """
        self.update()
        self.g_best()

    def visualize_result(self):
        # 绘制动画
        x = np.linspace(self.low, self.up, num=1000)
        y = np.array([self.fitness(x_value) for x_value in x])
        plt.clf()
        scatter_x = np.array([individual.position for individual in self.population])
        scatter_y = np.array([individual.fitness for individual in self.population])

        scatter_gbest = self.gbest
        scatter_gfitness = self.fitness(self.gbest)

        plt.plot(x, y)
        plt.scatter(scatter_x, scatter_y, c='b')
        plt.scatter(scatter_gbest, scatter_gfitness, c='r')
        plt.pause(0.02)


class Bird:  # 粒子（鸟）
    def __init__(self):
        self.position = 0  # 粒子当前位置
        self.speed = 0  # 粒子当前速度
        self.pbest = 0  # 粒子历史最好位置
        self.fitness = 0  # 粒子在当前位置对应的适应度，此处为y值



if __name__ == '__main__':
    #  输入的参数
    mod = 0

    if mod == 0:  # GA
        low = -10  # 区间下限
        up = 10  # 区间上限
        accuracy = 0.0001  # 精度
        length = code_length(low, up, accuracy)  # 码长
        count = 300  # 种群数量
        retain_rate = 0.2  # 父代保留的百分率，如某一代种群有count个父代，则保留count*self.retain_rate的父代
        random_select_rate = 0.5  # 选择概率
        mutation_rate = 0.01  # 基因突变概率
        iterN = 200  # 迭代次数
        ga = GA(length, count, low, up, retain_rate, random_select_rate, mutation_rate)
        for i in range(iterN):
            ga.evolve()
        plot_result(ga, ga.result())
        print(ga.result())

    if mod == 1:  # PSO
        low = -10
        up = 10
        c1 = 1  # 自我认知学习因子（向本粒子历史最好位置进行学习）
        c2 = 1  # 社会认知学习因子（向种群中当前最好位置进行学习）
        w = 0.2  # 惯性因子
        count = 50
        iterN = 200

        pso = PSO(low, up, w, c1, c2, count)
        for i in range(iterN):
            pso.evolve()
            pso.visualize_result()
        print([pso.gbest, pso.fitness(pso.gbest)])
        plt.show()


