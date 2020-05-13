# coding=utf-8
import os
import numpy as np
from collections import defaultdict,Counter
thick = 1  # 假定二维矩形具有厚度1
fileDirC21 = ".\\data\\Hopper2001"
fileDirN13 = ".\\data\\Burke2004"
RE = ".\\data\\RE"

def Cdata():
    CSet = Load2DSet().getC21(fileDir=fileDirC21)
    return '1O1S1',CSet

def Cbox():
    CBoxSet = defaultdict(list)
    filePath = os.path.join(fileDirC21, 'box.txt')
    num = 0
    with open(file=filePath, mode='r') as f:
        for line in f.readlines():
            lineList = line.strip().split('\t')
            if 'w' in line:
                continue
            else:
                num+=1
                for i in range(1,4):
                    CBoxSet['C'+str(num)+str(i)] = [['BT'+str(lineList[0]+'X'+str(lineList[1])), int(lineList[0]), int(lineList[1]), 1, 1, 10, 1]]
    return CBoxSet

def Ndata():
    NSet = Load2DSet().getN13(fileDir=fileDirN13)
    return '1O1S1',NSet

def Nbox():
    NBoxSet = defaultdict(list)
    filePath = os.path.join(fileDirN13, 'box.txt')
    num = 0
    with open(file=filePath, mode='r') as f:
        for line in f.readlines():
            lineList = line.strip().split('\t')
            if 'w' in line or 'h' in line:
                continue
            else:
                num +=1
                NBoxSet['N'+str(num)] = [['BT'+str(lineList[0]+'X'+str(lineList[1])), int(lineList[0]), int(lineList[1]), 1, 1, 10, 1]]
    return NBoxSet

def encode(num, w, h, mode=0):
    if mode == 0:
       return ['1', '1O1', '1O1S1', '1O1S1P' + str(num), 'MY_1735_平板', w, h, thick, 0, 0]
    elif mode == 1:
        return ['R' + str(num), w, h]  # R代表Rectangle, 表示矩形的id
    else:
        raise IOError('no such mode,please make other choice.')

class Load2DSet:
    """加载2D装箱C21数据集和N13数据集"""
    def getC21(self, fileDir, mode=0):
        """mode=0获取2D矩形宽高；mode=1获取含有部件号的2D矩形"""
        if not os.path.exists(fileDir):
            raise FileExistsError('no %s file directory.' % fileDir)
        CSet = defaultdict(list)
        fileList = os.listdir(fileDir)  # 获取文件夹下面的文件名列表
        fileList = [v for v in fileList if 'C' in v]  # 过滤其他与C数据集无关的文件
        if len(fileList) != 21:
            raise FileExistsError('C21 data set is not complete.')
        for i, v in enumerate(fileList):
            num = 0
            key = v.split('.')[0]
            filePath = os.path.join(fileDir, v)  # 拼接文件名，将fileList[i]和fileDir目录拼成完整路径
            with open(filePath, 'r') as f:
                for line in f.readlines():
                    if 'w' in line or 'h' in line or line == '' or line=='\n':
                        continue
                    lineList = line.strip().split('\t')  # 以一个空格为分隔符，进行分隔
                    if len(lineList) == 2:
                        num += 1
                        CSet[key].append(encode(num, int(lineList[0]), int(lineList[1]), mode))
        return CSet

    def getN13(self, fileDir, mode=0):
        if not os.path.exists(fileDir):
            raise FileExistsError('no %s file directory.' % fileDir)
        NSet = defaultdict(list)
        fileList = os.listdir(fileDir)  # 获取文件夹下面的文件名列表
        fileList = [v for v in fileList if 'N' in v]  # 过滤其他与C数据集无关的文件
        if len(fileList) != 13:
            raise FileExistsError('N13 data set is not complete.')
        for i in range(1, len(fileList) + 1):
            k = 0
            p = []
            filePath = os.path.join(fileDir, fileList[i - 1])  # 拼接文件名，将fileList[i]和fileDir目录拼成完整路径
            with open(file=filePath, mode='r') as f:
                for line in f.readlines():
                    if 'w' in line or 'h' in line:
                        continue
                    lineList = line.strip().split('\t')  # 以一个空格为分隔符，进行分隔
                    if len(lineList) % 2 == 0:
                        for j in range(0, len(lineList), 2):
                            k += 1
                            p.append(encode(k, int(lineList[j]), int(lineList[j + 1]),mode))
            NSet[fileList[i - 1].split('.')[0]] = p
        return NSet

class RectBox2D:
    def __init__(self, fileDir, name='C21'):
        if not os.path.exists(fileDir):
            raise FileExistsError('no %s file directory.' % fileDir)
        if name not in ('C21', 'N13'):
            raise AttributeError('the name must be C21 or N13.')
        fileList = os.listdir(fileDir)  # 获取文件夹下面的文件名列表
        if name == 'C21':
            rectFileList = [v for v in fileList if 'C' in v]  # 过滤其他与C21数据集无关的文件
        else:
            rectFileList = [v for v in fileList if 'N' in v]  # 过滤其他与N13数据集无关的文件
        boxFile = os.path.join(fileDir, 'box.txt')
        self.rectangles = self.__rect(fileDir, rectFileList)
        self.boxes = self.__box(name, boxFile)

    @classmethod
    def __rect(cls, fileDir, rectFileList):
        rectSet = defaultdict(list)
        for i, v in enumerate(rectFileList):
            rid = 0
            key = v.split('.')[0]
            filePath = os.path.join(fileDir, v)  # 拼接文件名，将fileList[i]和fileDir目录拼成完整路径
            with open(filePath, 'r') as f:
                for line in f.readlines():
                    lineList = line.strip().split('\t')  # 以一个空格为分隔符，进行分隔
                    rid += 1
                    rectSet[key].append([int(lineList[0]),int(lineList[0]),'R'+str(rid)])
        return rectSet

    @classmethod
    def __box(cls, name, boxFile):
        boxSet = defaultdict(list)
        if name == 'C21':
            num, bid= 0, 0
            with open(boxFile, 'r') as f:
                for line in f.readlines():
                    num += 1
                    lineList = line.strip().split('\t')  # 以一个空格为分隔符，进行分隔
                    for i in range(1,4):
                        bid+=1
                        boxSet['C'+str(num)+str(i)] = [int(lineList[0]),int(lineList[1]), 'B'+str(bid)]
        else:
            bid = 0
            with open(boxFile, 'r') as f:
                for line in f.readlines():
                    bid += 1
                    lineList = line.strip().split('\t')  # 以一个空格为分隔符，进行分隔
                    boxSet['N' + str(bid)] = [int(lineList[0]), int(lineList[1]), 'b' + str(bid)]
        return boxSet

def getSet(fileDir, setName='C21'):
    """
    :param fileDir: C21或N13数据集文件路径
    :param setName: C21或N13两种数据集
    :return: 数据集2D矩形、容器数据
    """
    if not os.path.exists(fileDir):
        raise FileExistsError('no %s file directory.' % fileDir)
    if setName not in ('C21', 'N13'):
        raise Exception('the name must be C21 or N13.')
    dataSet = defaultdict(list)
    fileList = os.listdir(fileDir)  # 获取文件夹下面的文件名列表
    if setName=='C21':
        fileList = [v for v in fileList if 'C' in v or 'box' in v]  # 过滤其他与C21数据集无关的文件
    else:
        fileList = [v for v in fileList if 'N' in v or 'box' in v]  # 过滤其他与N13数据集无关的文件
    for i, v in enumerate(fileList):
        key = v.split('.')[0]
        filePath = os.path.join(fileDir, v)  # 拼接文件名，将fileList[i]和fileDir目录拼成完整路径
        dataSet[key] = np.fromfile(filePath, dtype=np.int, sep='\t').reshape(-1, 2)
    return dataSet


if __name__ == '__main__':
    boxes = Cbox()
    rectangles = Load2DSet().getC21(fileDirC21, 0)

    boxes = Nbox()
    rectangles = Load2DSet().getN13(fileDirN13, 0)
    pass
    # 规整数据格式更加规范
    # for k, v in info.items():
    #     path = os.path.join(save_dir, k + '.txt')
    #
    #     with open(path, 'w') as f:
    #         f.write('h' + '\t' + 'w' + '\n')
    #         for i in range(len(v)):
    #             f.write(str(v[i][5]) + '\t' + str(v[i][6])+'\n')

