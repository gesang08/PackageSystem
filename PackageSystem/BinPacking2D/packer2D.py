#coding=utf-8
from DataSet import RectBox2D
from copy import deepcopy
from rectpack import newPacker,PackingBin,SkylineMwflWm,GuillotineBafMaxas

name = 'C21'
fileDirC21 = r"C:\Users\gs\OneDrive\graduate\DataSource\Hopper2001"
fileDirN13 = r"C:\Users\gs\OneDrive\graduate\DataSource\Burke2004"

def packer2D():
    if name == 'C21':
        fileDir = fileDirC21
    elif name == 'N13':
        fileDir = fileDirN13
    else:
        raise Exception("the name must be C21 or N13.")
    rect_box = RectBox2D(fileDir, name=name)
    rectangles = rect_box.rectangles
    boxes = rect_box.boxes

    rectangleList = rectangles['C11']
    box = boxes['C11']

    Put(deepcopy(box), deepcopy(rectangleList)).tryPut()


    # for setName in rectangles.keys():
    #     packer = newPacker()
    #
    #     rectangleList = rectangles[setName]
    #     box = boxes[setName]
    #     for rect in rectangleList:
    #         packer.add_rect(*rect)
    #     packer.add_bin(box[0], box[1], count=1, bid=box[2])
    #     # Start packing
    #     packer.pack()
    #
    #     # Full rectangle list
    #     all_rects = packer.rect_list()
    #     for rect in all_rects:
    #         print(rect, len(all_rects))
    #         b, x, y, w, h, rid = rect
    #     pass

class Put:
    def __init__(self, box, rectangles):
        self.box=box
        self.rectangles = rectangles

    def tryPut(self):
        cornerPoint = [[0,0]]

        for r in self.rectangles:
            rect = Rectangle(0,0,r[0],r[1], r[2],0)

class Rectangle:
    # __slots__限制类的属性绑定，Rectangle类只能绑定元组中的几个属性，否则抛出AttributeError异常
    # __slots__定义的属性仅对当前类起作用，对继承的子类是不起作用的
    __slots__ = ('length', 'width', 'x', 'y', 'rid', 'rotation')

    def __init__(self, x, y, length, width, rid=None, rotation=None):
        """
        Args:
            x (int, float): 放置矩形的左下角x坐标
            y (int, float): 放置矩形的左下角y坐标
            width (int, float): 矩形宽度
            length (int, float): 矩形长度
            rid (int, str): 矩形id
            rotation(int): 放置矩形是否旋转，其值为0 or 1
        """
        assert length > 0 and width > 0
        if rotation not in (0, 1):
            raise AttributeError("the rotation must be 0 or 1.")
        self.length = length
        self.width = width
        self.x = x
        self.y = y
        self.rid = rid
        self.rotation = rotation

    def __repr__(self):  # __repr__方法可以描述类
        return "R({}, {}, {}, {}, {}, {})".format(self.x, self.y, self.length, self.width, self.rid, self.rotation)

    @property
    def bottom(self):
        """
        Rectangle bottom edge y coordinate
        """
        return self.y

    @property
    def top(self):
        """
        Rectangle top edge y coordinate
        """
        if self.rotation == 0:
            return self.y + self.width
        else:
            return self.y + self.length

    @property
    def left(self):
        """
        Rectangle left edge x coordinate
        """
        return self.x

    @property
    def right(self):
        """
        Rectangle right edge x coordinate
        """
        if self.rotation == 0:
            return self.x + self.length
        else:
            return self.x + self.width

    @property
    def corner_lt(self):
        """
        Rectangle left-top corner coordinate
        """
        return [self.left, self.top]

    @property
    def corner_rt(self):
        """
        Rectangle right-top corner coordinate
        """
        return [self.right, self.top]

    @property
    def corner_rb(self):
        """
        Rectangle right-bottom corner coordinate
        """
        return [self.right, self.bottom]

    @property
    def corner_lb(self):
        """
        Rectangle left-bottom corner coordinate
        """
        return [self.left, self.bottom]



if __name__ == '__main__':
    packer2D()
    r = Rectangle(0,0,20,30,'r1',1)
