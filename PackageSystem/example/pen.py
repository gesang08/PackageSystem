import matplotlib.pyplot as plt
from confs.Setting import *
import numpy as np
mod = 6
if mod == 0:
    fig = plt.figure(num='弱异构算例',figsize=(8, 6))
    x = ['LN01' , 'LN02' , 'LN03' , 'LN04' , 'LN05' , 'LN06', 'LN07', 'LN08', 'LN09', 'LN10', 'LN11', 'LN12'  ,'LN13' , 'LN14' ,'LN15']
    y1 = [62.5,80.4,53.4,55.0,77.2,84.8,77.0,59.4,61.9,67.3,62.2,69.5,73.3,62.8,59.5]
    y2 = [62.5, 88.3,  53.4,  55.0,  77.2,  84.8, 82.9, 59.4, 61.9, 67.3, 62.2, 78.5,  79.4,  62.8, 59.5]
    plt.plot(x, y1, 'r--',label=u"Lim2012")
    plt.plot(x, y2, 'blue',label='Jun Zhang2019')
    plt.xlabel('算例',fontproperties=simsun)
    plt.ylabel('体积利用率(%)',fontproperties=simsun)
    plt.title('三维装箱弱异构算例结果',fontproperties=simsun)
    plt.xticks(rotation=30)
    plt.ticklabel_format()
    plt.legend(loc=1)
    plt.legend(prop=simsun)  # 设置label的字体显示为中文
    plt.show()

elif mod == 1:
    fig = plt.figure(num='空间平均利用率', figsize=(8, 6))
    x = ['HB1','HB2','HDB', 'HT', 'HM','HGA']
    y1 = [81.97, 83.45, 84.19, 88.51, 86.41,88.40]
    y2 = [62.5, 88.3, 53.4, 55.0, 77.2, 84.8, 82.9, 59.4, 61.9, 67.3, 62.2, 78.5, 79.4, 62.8, 59.5]
    plt.plot(x, y1, 'r--')
    # plt.plot(x, y2, 'blue', label='Jun Zhang2019')
    plt.xlabel('算法简称', fontproperties=simsun)
    plt.ylabel('空间平均利用率(%)', fontproperties=simsun)
    plt.title('几种算法平均空间利用率水平比较', fontproperties=simsun)
    plt.xticks(rotation=30)
    plt.ticklabel_format()
    plt.legend(loc=0)
    plt.show()

elif mod==2:
    fig = plt.figure(num='', figsize=(8, 6))
    x = ['BR1','BR2','BR3','BR4','BR5','BR6','BR7']
    y1 = [77.8,82.2,80.1,80.2,79.6,81.0,80.1]
    y2 = [94.4,94.3,91.7,92.5,90.0,90.2,88.6]
    y3 = [88.4,88.1,86.4,85.9,85.8,85.3,85.0]
    plt.plot(x, y1, 'r--', label="min")
    plt.plot(x, y2, 'b-.', label='max')
    plt.plot(x, y3, 'k-', label='aver')
    plt.xlabel('算例', fontproperties=simsun)
    plt.ylabel('体积利用率(%)', fontproperties=simsun)
    plt.title('三维装箱BR算例水平', fontproperties=simsun)
    plt.xticks(rotation=30)
    plt.ticklabel_format()
    plt.legend(loc=0)
    plt.show()
elif mod==3:
    fig = plt.figure(num='', figsize=(8, 6))
    x = ['N1','N2','N3','N4','N5','N6','N7','N8','N9','N10','N11','N12','N13']

    y1 = [100,100,100,99.75,98.68,99.82,99.95,99.89,100,100,100,99.85,100]
    y2 = [100,100,100,99.75,99.40,100,99.90,100,100,100,100,99.97,100]

    plt.plot(x, y1, 'r--', label="BFA 2012")
    plt.plot(x, y2, 'b-', label='BRSA 2017')

    plt.xlabel('算例', fontproperties=simsun)
    plt.ylabel('填充率(%)', fontproperties=simsun)
    plt.title('二维N算例水平', fontproperties=simsun)
    plt.xticks(rotation=30)
    plt.ticklabel_format()
    plt.legend(loc=0)
    plt.show()

elif mod == 4:  # 绘制条形图
    fig = plt.figure(num='', figsize=(8, 6))
    # x = ['C11', 'C12', 'C13', 'C21', 'C22', 'C23', 'C31', 'C32', 'C33', 'C41', 'C42', 'C43', 'C51', 'C52', 'C53', 'C61', 'C62', 'C63', 'C71', 'C72', 'C73']
    #
    # y1 = [100]*21
    # y2 = [100]*21
    x= ['N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'N9', 'N10', 'N11', 'N12', 'N13']

    y1=[100, 100, 100, 100, 100, 100, 100, 100, 100, 100,0,0,0]
    y2 = [100,100,100,99.75,99.4,100,99.9,100,100,100,100,99.97,100]
    n_groups = 13
    index = np.arange(n_groups)
    bar_width = 0.35

    plt.bar(index, y1, bar_width,alpha=0.4,color='r', label="自己")
    plt.bar(index+bar_width, y2, bar_width,alpha=0.4,color='b', label='BRSA 2018')
    plt.xticks(index + bar_width, x)

    plt.xlabel('算例', fontproperties=simsun)
    plt.ylabel('填充率(%)', fontproperties=simsun)
    plt.title('二维N13算例填充率结果', fontproperties=simsun)
    plt.xticks(rotation=30)
    plt.ticklabel_format()
    plt.legend(loc=0)
    plt.legend(prop=simsun)
    plt.ylim(0, 120)
    plt.tight_layout()
    plt.show()

elif mod==5:
    fig = plt.figure(num='', figsize=(8, 6))
    x = ['C11', 'C12', 'C13', 'C21', 'C22', 'C23', 'C31', 'C32', 'C33', 'C41', 'C42', 'C43', 'C51', 'C52', 'C53', 'C61', 'C62', 'C63', 'C71', 'C72', 'C73']
    y1= [3.44,3.04,3.31,8.49,8.36,4.76,7.39,7.33,11.24,15.6,24.97,22.65,30.67,30.67,27.57,52.88,25.29,14.85,141.26,528.72,362.29]
    y2=[0.01,0.02,0,0.05,0.02,0.03,0.08,2.32,0.91,7.53,5.31,3.58,9.69,2.38,5.51,23.72,8.11,31.31,424.96,153.24,93.53]

    # x = ['N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'N9', 'N10', 'N11', 'N12', 'N13']
    # y1 = [1.33,4.51,5.03,5.26,6.08,11.84,10.75,52.51,77.27,126.14,None,None,None]
    # y2 = [0,0.41,0.76,27.12,50.46,4.62,65.94,17.33,5.06,23.29,0.67,483.22,25]

    plt.plot(x, y1, 'r--', label="自己")
    plt.plot(x, y2, 'b-', label='BRSA 2018')

    plt.xlabel('算例', fontproperties=simsun)
    plt.ylabel('时间(%)', fontproperties=simsun)
    plt.title('二维C21算例运行时间结果', fontproperties=simsun)
    plt.xticks(rotation=30)
    plt.ticklabel_format()
    plt.legend(loc=0)
    plt.legend(prop=simsun)
    plt.show()

elif mod==6:
    fig = plt.figure(num='', figsize=(8, 6))
    x = np.arange(0,100,1)
    # y = 1/(np.exp(-0.02*x)+1)
    # y = np.exp(-10/x)
    y = (1-np.exp(-0.2*x))/(1+np.exp(-0.2*x))
    # y = np.exp(-4/x)
    # y = 1- (1-2*x)**2
    plt.plot(x, y)
    plt.xlabel('迭代次数t', fontproperties=simsun)
    plt.ylabel('y', fontproperties=simsun)

    plt.show()

