import pdfplumber
import re
import os
from pprint import pprint
from decimal import Decimal

regex_list = [  # 不解析纳税人识别号
    re.compile(r'\s?(?P<城市>\w*普通发票)'),
    re.compile(r'发票号码\s*[:：]\s*(?P<发票号码>\d{8})?'),
    re.compile(r'开票日期\s*[:：]\s*(?P<开票日期>.+?年.+?月.+?日)?'),
    re.compile(r'机器编号\s*[:：]\s*(?P<机器编号>\d{12})?'),
    re.compile(r'校\s*验\s*码\s*[:：]\s*(?P<校验码>(?:\d{5}\D*?){3}\d{5})'),
    re.compile(
        r'名\s*称\s*[:：]\s*(?P<购买方>\w*).*?名\s*称\s*[:：]\s*(?P<销售方>\w*)',
        flags=re.DOTALL),
    re.compile(r'价税合计.*?大写[)）]\s*(?P<价税合计_大写>\w*[整分角]).*?'),
]

regex_amount = re.compile(r'(?<=[￥¥])\s*(?P<价税合计_小写>\d*\.\d*)')

fieldnames = [
    '城市',
    '发票号码',
    '开票日期',
    '机器编号',
    '校验码',
    '购买方',
    '销售方',
    '价税合计_大写',
    '价税合计_小写',
]


def get_page_text(pdf_file, page_num=0):
    """提取电子发票某一页中的文本.

    page_num=0:因为电子发票通常只有一页，因此默认获取第一页
    """
    with pdfplumber.open(pdf_file) as pdf:
        p0 = pdf.pages[page_num]
        return p0.extract_text()


def parse_text(text: str, regex_list=regex_list,
               regex_amount=regex_amount) -> dict:
    """使用正则表达式解析text中的内容
    """
    groupdict = dict()
    for regex in regex_list:
        match_obj = regex.search(text)
        if match_obj:
            for k, v in match_obj.groupdict().items():
                if v:
                    v = v.replace(' ', '')
                groupdict[k] = v
            # groupdict.update(match_obj.groupdict())
    groupdict['价税合计_小写'] = max(
        [Decimal(i) for i in regex_amount.findall(text)])
    return groupdict


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
        invoice_data = parse_text(text, regex_list, regex_amount)
        pprint(invoice_data)


if __name__ == '__main__':
    _test_parser()
