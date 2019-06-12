import pdfplumber
import re
import os
import csv
import pandas
from pprint import pprint
from decimal import Decimal
from datetime import datetime


class Invoice(dict):
    regex_list = [  # 不解析纳税人识别号
        re.compile(r'\s?(?P<城市>\w*普通发票)'),
        re.compile(r'发票代码\s*[:：]\s*(?P<发票代码>(?:\d\s*){11}\d)?'),
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

    field_names = [
        '城市',
        '发票代码',
        '发票号码',
        '开票日期',
        '机器编号',
        '校验码',
        '购买方',
        '销售方',
        '价税合计_大写',
        '价税合计_小写',
    ]

    def __init__(self, pdf_path):
        self.is_success: bool  # 是否成功解析到了regex_list和regex_amount中的所有内容
        self.pdf_path = pdf_path
        self.page0_text = self.get_page_text(self.pdf_path)
        self.data_dict = self.get_data_dict(self.page0_text)

        super().__init__(self.data_dict)

    def get_page_text(self, pdf_path, page_num=0):
        """提取电子发票某一页中的文本.

        因为电子发票通常只有一页，因此默认获取第一页的文本
        """
        with pdfplumber.open(pdf_path) as pdf:
            p0 = pdf.pages[page_num]
            text = p0.extract_text()
            return '' if text is None else text

    def get_data_dict(self, text: str) -> dict:
        """使用正则表达式解析并获取text中的内容
        """
        self.is_success = True
        data_dict = dict()
        for regex in Invoice.regex_list:
            match_obj = regex.search(text)
            if match_obj:
                data_dict.update({
                    k: v.replace(' ', '')
                    for k, v in match_obj.groupdict().items() if v
                })
            else:
                self.is_success = False
                print(f'解析异常:{self.pdf_path}\n==>{regex.pattern}')
        try:
            data_dict['价税合计_小写'] = str(
                max(Decimal(i) for i in Invoice.regex_amount.findall(text)))
        except ValueError:
            self.is_success = False
            print(f'解析异常:{self.pdf_path}\n==>{Invoice.regex_amount.pattern}')
        return data_dict

    @property
    def identity(self):
        """id由'发票代码'+'发票号码'构成

        发票的唯一性由'发票代码'+'发票号码'来确定。
        增值税电子普通发票的发票代码为12位，编码规则为：
        第1位为0，第2—5位代表省、自治区、直辖市和计划单列市，
        第6—7位代表年度，第8—10位代表批次，
        第11—12位代表票种（11代表电子增值税普通发票）。
        发票号码为8位，按年度、分批次编制。
        http://www.chinatax.gov.cn/n810219/n810724/c1925563/content.html

        """
        value = self.get('发票代码', '') + self.get('发票号码', '')
        return value if self.is_success else ''

    def write2text(self):
        """将解析到的数据写至与pdf_file同名的txt文件中
        """
        txt_path = f'{self.pdf_path[:-4]}.txt'
        with open(txt_path, 'w', encoding='utf-8', newline='') as fin:
            fin.write(self.page0_text)
            fin.write('\n===================\n')
            fin.writelines(f'{n}:{item}\n'
                           for n, item in enumerate(self.data_dict.items()))


class Invoices(dict):
    def __init__(self, pdf_dir: str):
        """获取目录中pdf文件路径列表
        """
        self.pdf_dir = pdf_dir
        self.pdf_paths = [
            os.path.join(self.pdf_dir, i.name)
            for i in os.scandir(self.pdf_dir)
            if i.is_file() and i.name.endswith('.pdf')
        ]

        id_key_dict = dict()
        for n, pdf_path in enumerate(self.pdf_paths):
            invoice = Invoice(pdf_path)
            id_key = invoice.identity
            if id_key not in id_key_dict:
                id_key_dict[id_key] = []
            new_path = os.path.join(self.pdf_dir, f'{n:02d}.pdf')
            os.rename(invoice.pdf_path, new_path)
            invoice.pdf_path = new_path
            id_key_dict[id_key].append(invoice)
        super().__init__(id_key_dict)
        self.rename_invoice()

    def rename_invoice(self):
        for id_key, invoice_list in self.items():
            if id_key != '':
                for i, invoice in enumerate(invoice_list):
                    head, tail = os.path.split(invoice.pdf_path)
                    if i == 0:
                        new_path = os.path.join(
                            head,
                            '_'.join(invoice.data_dict.values()) + '.pdf')
                        os.rename(invoice.pdf_path, new_path)
                        invoice.pdf_path = new_path
                    else:
                        new_path = os.path.join(
                            head,
                            f"_重复_{invoice.get('发票代码')}_{invoice.get('发票号码')}_{i:02d}.pdf"
                        )
                        os.rename(invoice.pdf_path, new_path)
                        invoice.pdf_path = new_path
            else:
                for i, invoice in enumerate(invoice_list):
                    head, tail = os.path.split(invoice.pdf_path)
                    file_name, ext = tail.rsplit('.', 1)
                    file_name = f"__{file_name.split('_')[0]}"
                    new_path = os.path.join(head,
                                            f"{file_name}_解析失败__{i:02d}.pdf")
                    os.rename(invoice.pdf_path, new_path)
                    invoice.pdf_path = new_path

    def write2csv(self):
        """将非重复数据写入到pdf_dir目录下的csv文件中
        """
        csv_file_name = f"{str(datetime.now()).replace(':','.')}.csv"
        csv_file_path = os.path.join(self.pdf_dir, csv_file_name)
        with open(csv_file_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=Invoice.field_names)
            writer.writeheader()
            for invoice in (v[0] for k, v in self.items() if k != ''):
                writer.writerow(invoice)

    def write2excel(self):
        """将非重复数据写入到pdf_dir目录下的xlsx文件中
        """
        xlsx_file_name = f"{str(datetime.now()).replace(':','.')}.xlsx"
        xlsx_file_path = os.path.join(self.pdf_dir, xlsx_file_name)
        # 将数据转换为DataFrame对象
        df = pandas.DataFrame(v[0] for k, v in self.items() if k != '')
        # For compatibility with to_csv(), to_excel serializes lists and dicts to strings before writing.
        # http://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.to_excel.html
        # 需要调整excel中小写金额的格式
        df.to_excel(xlsx_file_path)

    def write2txt(self):
        for invoice in (v[0] for k, v in self.items() if k != ''):
            invoice.write2text()


def test_Invoice():
    pdf_paths = [
        os.path.join(r'.\tests', i.name) for i in os.scandir(r'.\tests')
        if i.is_file() and i.name.endswith('.pdf')
    ]
    for pdf_path in pdf_paths:
        invoice = Invoice(pdf_path)
        invoice.write2text()
        print(f"{invoice.pdf_path}-->{invoice.id}")
        # 解析到的内容见对应的txt文件


def test_Invoices():
    invoices = Invoices(r'.\tests')

    invoices.write2csv()
    invoices.write2excel()
    invoices.write2txt()
    # pprint(invoices)


if __name__ == '__main__':
    # test_Invoice()
    test_Invoices()
