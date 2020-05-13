# coding=utf-8
#########################################################
# function: prepare the data for problem research       #
# author: gesang                                        #
# time: 2020-04-14                                      #
#########################################################

import os
import numpy as np
from confs.geatpy_conf import *


def process(dir, subset, idFlag):
    """
    Args:
         dir -- 数据文件顶层目录
         subset -- 数据文件子目录
         idFlag -- box和rectangle是否需要编号ID，ID编号为1,2,3,...
    Res:
        格式：
        {'box':
                {'N1':ndarray},
                {'N2':ndarray}
                ...
        'rect':
                {'N1':ndarray},
                {'N2':ndarray},
                ...
        }
        ndarray
            数据类型 -- np.int
            维度 -- idFlag=False  (n,3)   width,height,thick
                -- idFlag=False  (n,4)  width,height,thick,id
    """

    if subset == 'Burke2004':
        names = EXIST_SET['N']
    elif subset == 'Hopper2001':
        names = EXIST_SET['C']
    elif subset == 'RE':
        names = EXIST_SET['RE']
    elif subset == 'Pisinger2001':
        names = EXIST_SET['P']
    else:
        raise NameError("The assigned subdir's name is false.")
    subPath = os.path.join(dir, subset)
    resDict = {'rect': {}, 'box': {}}
    fileList = os.listdir(subPath)
    boxes = np.fromfile(os.path.join(subPath, 'box.txt'), dtype=np.int, sep='\t').reshape(-1, 2)
    bid = 0
    for n,b in zip(names, boxes):
        bid +=1
        rawBox = b
        rawBoxThick = np.append(rawBox,np.array([1]))
        resDict['box'][n] = rawBoxThick
        if idFlag:  # 增加一列box高度，以便兼容板件装箱
            resDict['box'][n] = np.append(rawBoxThick,np.array([bid]))
    for file in fileList:
        if file[:-4] in names and file.endswith('.txt'):
            raw = np.fromfile(os.path.join(subPath, file), dtype=np.int, sep='\t').reshape(-1, 2)
            rawThick = np.append(raw,np.ones(shape=(raw.shape[0],1)),axis=1)  # 增加一列rect厚度，以便兼容板件装箱
            resDict['rect'][file[:-4]] = rawThick.astype(dtype=np.int)
            if idFlag:
                seqId=np.array([[i +1 for i in range(rawThick.shape[0])]]).T
                rawId = np.append(rawThick,seqId,axis=1)
                resDict['rect'][file[:-4]] = rawId.astype(dtype=np.int)
    return resDict


def covert():  # 转换成AGA算法所需要的格式数据
    resDict = resDict = process(DATA_DIR, SUBSET, RECT_BOX_ID)
    sec_id = '1O1S1'
    partList = []
    a = 0
    for i, v in enumerate(resDict['rect'][TEST]):
        a += int(v[0]) * int(v[1])*int(v[2])
        val = ['1', '1O1', '1O1S1', '1O1S1P' + str(v[3]), 'MY_1735_平板', int(v[0]), int(v[1]), int(v[2]), 0, 0]
        partList.append(val)
    print('矩形总面积', a)
    _box = resDict['box'][TEST]
    box = [str(_box[3]), int(_box[0]),int(_box[1]),int(_box[2]),1, 1, 10, 1]
    print('容器面积', int(_box[0])*int(_box[1]))
    return sec_id, partList, box


def sortSeq(dir, subset, idFlag):
    """
    6种初始化排序方法，来自于文章《A skyline heuristic for the 2D rectangular packing and strip packing problems》
    Args:
        resDict -- 同上
    Res:
        格式：
        {'box':
                {'N1':ndarray},
                {'N2':ndarray}
                ...
        'rect':
                {'N1':ndarray},
                {'N2':ndarray},
                ...
        'sort_seq':
                {'N1':ndarray},
                {'N2':ndarray},
                ...
        }
        ndarray
            数据类型 -- np.int
            维度 -- idFlag=False  (n,3)   width,height,thick
                -- idFlag=False  (n,4)  width,height,thick,id
            sort_seq ndarray -- dim (7, n), np.int
            1.第一行：矩形面积降序排序
            2.第二行：矩形长度降序排序
            3.第三行：矩形宽度降序排序
            4.第四行：矩形周长降序排序
            5.第五行：矩形max(长度, 宽度)降序排序
            6.第六行：矩形对角线+长度+宽度降序排序
        增加1种：
            7.第七行：矩形对角线降序排序
    """
    resDict = process(dir, subset, idFlag)
    resDict['sort_seq'] = {}

    for k, v in resDict['rect'].items():
        seqList = []
        for i in range(7):
            if i == 0:
                seqCode = np.array([val[-1] for val in sorted(v, key=lambda x: x[0] * x[1], reverse=True)])
            elif i == 1:
                seqCode = np.array([val[-1] for val in sorted(v, key=lambda x: x[0], reverse=True)])
            elif i == 2:
                seqCode = np.array([val[-1] for val in sorted(v, key=lambda x: x[1], reverse=True)])
            elif i == 3:
                seqCode = np.array([val[-1] for val in sorted(v, key=lambda x: 2 * (x[0] + x[1]), reverse=True)])
            elif i == 4:
                seqCode = np.array([val[-1] for val in sorted(v, key=lambda x: max(x[0], x[1]), reverse=True)])
            elif i == 5:
                seqCode = np.array([val[-1] for val in sorted(v, key=lambda x:
                x[0] + x[1] + (x[0] ** 2 + x[1] ** 2) ** 0.5, reverse=True)])
            else:
                seqCode = np.array([val[-1] for val in sorted(v, key=lambda x:
                (x[0] ** 2 + x[1] ** 2) ** 0.5, reverse=True)])
            seqList.append(seqCode)
        resDict['sort_seq'][k] = np.array(seqList)
    return resDict

# processor函数测试


# resDict = process(DATA_DIR, SUBSET, RECT_BOX_ID)
# covert()
# sortSeq(resDict)

processor = sortSeq





