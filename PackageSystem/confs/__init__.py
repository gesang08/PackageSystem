#!usr/bin/env python3
# encoding:utf8

"""
python package的作用：
1.package包中有多个模块module,每个包中都有一个__init__.py文件
2.__init__.py文件定义了包的属性和方法
3.当将一个包作为模块导入（from confs import Setting）的时候，实际上导入了它的 __init__.py 文件，并运行它，类似于类的构造函数
4.包中可以定义子包，但子包也必须有__init__.py文件
5.__init__.py文件可以什么也不定义，可以只是一个空文件，但是必须存在，否则这个目录就仅仅是一个目录，而不是一个包，它就不能被导入或者包含其它的模块和嵌套包
"""