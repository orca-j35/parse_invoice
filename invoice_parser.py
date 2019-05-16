import pdfplumber
import re
import os
import csv
from pprint import pprint
from datetime import datetime

# 用于解析发票文本内容的正则表达式
regex = re.compile(
    r'(?P<城市>\w*普通发票).*'
    r'发票代码.*?(?P<发票代码>\d{12}).*?'
    r'发票号码.*?(?P<发票号码>\d{8}).*?'
    r'开票日期.*?(?P<开票日期>2\w+日).*?'
    r'机器编号.*?(?P<机器编号>\d{12}).*?'
    r'校.*?验.*?码.*?(?P<校验码>(?:\d{5}\D){3}\d{5}).*?'
    r'名.*?称.*?[:：](?:\s*)(?P<购买方>\w*).*?'  # 购买方名称
    r'纳税人识别号\s*?[:：](?:\s*)(?P<购买方纳税人识别号>(?:\d\s*)*(?a:\w?))?.*?'  # 购买方识别号
    r'价税合计.*?大写[)）]\s*(?P<价税合计_大写>\w*[整分]).*?'
    r'小写.*￥\s*(?P<价税合计_小写>\d*\.\d*).*?'
    r'名.*?称.*?[:：](?:\s*)(?P<销售方>\w*).*?'  # 销售方名称
    r'纳税人识别号\s*?[:：](?:\s*)(?P<销售方纳税人识别号>(?:\d\s*)\d+(?a:\w?))',  # 销售方纳税人识别号
    flags=re.DOTALL)

fieldnames = regex.groupindex.keys()


def get_page_text(pdf_file, page_num=0):
    """提取电子发票某一页中的文本.

    page_num=0:因为电子发票通常只有一页，因此默认获取第一页
    """
    with pdfplumber.open(pdf_file) as pdf:
        p0 = pdf.pages[page_num]
        return p0.extract_text()


def parse_text(text: str) -> dict:
    """使用正则表达式解析text中的内容
    """
    match_obj = regex.search(text)
    if match_obj:
        return match_obj.groupdict()
    return None


def _write2file(text, pdf_file):
    """将text写至与pdf_file同名的txt文件中
    """
    txt_file = f'{pdf_file[:-4]}.txt'
    with open(txt_file, 'w', encoding='utf-8', newline='') as fin:
        fin.write(text)


def _test_parser():
    """使用.\tests中的票据来测试解析器的输出
    """
    pdf_files = [
        os.path.join(r'.\tests', i.name) for i in os.scandir(r'.\tests')
        if i.is_file() and i.name.endswith('.pdf')
    ]
    for pdf_file in pdf_files:
        text = get_page_text(pdf_file=pdf_file)
        _write2file(text, pdf_file)
        invoice_data = parse_text(text)
        pprint(invoice_data)


if __name__ == '__main__':
    _test_parser()
