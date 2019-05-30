import invoice_parser
import os
import csv
from datetime import datetime
from pprint import pprint
from invoice_parser import Invoices

# 获取给定路径下文件和目录的列表:os.listdir(),os.scandir()
# 获取当前路径:os.getcwd()
# 创建目录：os.mkdir('/Users/michael/testdir')
# 删除目录：os.rmdir('/Users/michael/testdir')
# 重命名：os.rename('test.txt', 'test.py')
# 删除：os.remove('test.py')

# 复制：shutil模块提供了copyfile()的函数，
# 你还可以在shutil模块中找到很多实用函数，它们可以看做是os模块的补充。

# 获得文件的绝对路径:os.path.abspath('memo.txt')
# 合并路径:os.path.join('/Users/michael', 'testdir')
# 分拆路径：os.path.split('/Users/michael/testdir/file.txt')
# 分拆扩展名：os.path.splitext()

# 检查文件或目录是否存在:os.path.exists('memo.txt')
# 是否是一个目录:os.path.isdir('memo.txt')
# 是否是一个文件:os.path.isfile

if __name__ == '__main__':
    print('如需退出程序，可输入q')
    while True:
        pdf_dir = input('输入内含pdf电子发票的文件夹:')
        if pdf_dir in ('q', 'Q'):
            break
        invoices = Invoices(pdf_dir)
        invoices.write2csv()
