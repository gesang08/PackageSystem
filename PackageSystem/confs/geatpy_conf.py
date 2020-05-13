# coding=utf-8
# prepare the configure for problem research with geatpy tool
# gs by 2020-05-09

# ----------------------------配置数据获取--------------------------------
DATA_DIR = '.\\data'
RECT_BOX_ID = True
# SUBSET = 'Hopper2001'
# SUBSET = 'Burke2004'
SUBSET = 'RE'

EXIST_SET = {
    'N': ('N1', 'N2', 'N3', 'N4', 'N5', 'N6', 'N7', 'N8', 'N9', 'N10', 'N11', 'N12', 'N13'),
    'C': ('C11', 'C12', 'C13', 'C21', 'C22', 'C23', 'C31', 'C32', 'C33', 'C41', 'C42', 'C43',
          'C51', 'C52', 'C53', 'C61', 'C62', 'C63', 'C71', 'C72', 'C73'),
    'RE': ('RE', 'J1', 'J2'),
}
TEST = 'J2'

# ----------------------------配置运行模式--------------------------------
RUNMODE = 1

