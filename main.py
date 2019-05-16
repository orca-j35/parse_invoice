import invoice_parser
import os
import csv
from datetime import datetime
from pprint import pprint

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


def get_pdf_paths(pdf_dir: str) -> list:
    """获取输入文件夹中pdf电子发票的路径
    """
    pdf_paths = [
        os.path.join(pdf_dir, i.name) for i in os.scandir(pdf_dir)
        if i.is_file() and i.name.endswith('.pdf')
    ]
    return pdf_paths


def get_invoice_data(pdf_paths: list) -> list:
    """获取pdf发票中的数据,并对成功解析的pdf进行改名
    """
    invoice_data = []
    for pdf_path in pdf_paths:
        text = invoice_parser.get_page_text(pdf_path)
        data_dict = invoice_parser.parse_text(text)
        if data_dict:
            invoice_data.append(data_dict)
            new_name = '_'.join((data_dict.get('购买方', ''),
                                 data_dict.get('发票号码', ''),
                                 data_dict.get('开票日期', ''),
                                 data_dict.get('价税合计_小写', ''),
                                 data_dict.get('价税合计_大写', ''), '.pdf'))
            head, tail = os.path.split(pdf_path)
            new_path = os.path.join(head, new_name)
            os.rename(pdf_path, new_path)
        else:
            print(f'解析失败:{pdf_path}')
    return invoice_data


def write2csv(invoice_data: list, pdf_dir: str):
    """将invoice_data中的内容写入到pdf_dir下的csv文件中
    """
    csv_file_name = f"{str(datetime.now()).replace(':','.')}.csv"
    csv_file_path = os.path.join(pdf_dir, csv_file_name)
    with open(csv_file_path, 'w', newline='') as csvfile:
        fieldnames = invoice_parser.fieldnames
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for i in invoice_data:
            writer.writerow(i)


if __name__ == '__main__':
    pdf_dir = input('输入内含pdf电子发票的文件夹:')
    pdf_paths = get_pdf_paths(pdf_dir)
    invoice_data = get_invoice_data(pdf_paths)
    write2csv(invoice_data, pdf_dir)
    # path1 = r'c:\Users\iwhal\Documents\GitHub\parse_invoice\tests\1.txt'
    # path2 = r'c:\Users\iwhal\Documents\GitHub\parse_invoice\2.txt'
    # path3 = r'c:\Users\iwhal\Documents\GitHub\parse_invoice\tests'
    # # path2 = r'四川省太阳运输有限公司_60535240_2019年05月07日_肆拾玖圆伍角叁分_49.53'
    # os.rename(path1, path2)
    # # os.rename("1.txt", "2.txt", src_dir_fd=path3, dst_dir_fd=path3)
