import pdfplumber
import re
import os
import csv
from pprint import pprint
from decimal import Decimal
from datetime import datetime


class Invoice(dict):
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

    field_names = [
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

    def __init__(self, pdf_path):
        self.is_success: bool  # 是否成功解析到了regex_list和regex_amount中的所有内容
        self.pdf_path = pdf_path
        self.page0_text = self.get_page_text(pdf_path)
        self.data_dict = self.get_data_dict(self.page0_text)
        # self.rename()

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

    def rename(self):
        """对pdf文件重命名
        """

        if self.is_success:
            head, tail = os.path.split(self.pdf_path)
            new_pdf_path = os.path.join(
                head, '_'.join(self.data_dict.values()) + '.pdf')

            if os.path.exists(new_pdf_path):
                if new_pdf_path != self.pdf_path:
                    # 新路径和旧路径不一致，但新路径被占用，说明当前发票重复
                    # 直接在文件名中提示发票重复
                    date = str(datetime.now()).replace(':', '.')
                    path = os.path.join(
                        head,
                        f"_发票号码_{self.data_dict.get('发票号码')}_存在重复_{date}.pdf")
                    os.rename(self.pdf_path, path)
                    self.pdf_path = path
            else:
                os.rename(self.pdf_path, new_pdf_path)
                self.pdf_path = new_pdf_path
        else:
            head, tail = os.path.split(self.pdf_path)
            file_name, ext = tail.rsplit('.', 1)
            file_name = f"__{file_name.split('_')[0]}"
            new_pdf_path = os.path.join(
                head,
                f"{file_name}_解析失败_{str(datetime.now()).replace(':','.')}.pdf")
            os.rename(self.pdf_path, new_pdf_path)
            self.pdf_path = new_pdf_path

    def write2text(self):
        """将解析到的数据写至与pdf_file同名的txt文件中
        """
        txt_path = f'{self.pdf_path[:-4]}.txt'
        with open(txt_path, 'w', encoding='utf-8', newline='') as fin:
            fin.write(self.page0_text)
            fin.write('\n===================\n')
            fin.writelines(f'{n}:{item}\n'
                           for n, item in enumerate(self.data_dict.items()))


class Invoices(list):
    def __init__(self, pdf_dir: str):
        """获取目录中pdf文件路径列表
        """
        self.pdf_dir = pdf_dir
        self.pdf_paths = [
            os.path.join(pdf_dir, i.name) for i in os.scandir(pdf_dir)
            if i.is_file() and i.name.endswith('.pdf')
        ]
        self.invoice_list = []
        num_set = set()
        for invoice in (Invoice(path) for path in self.pdf_paths):
            num = invoice.get('发票号码')
            if num not in num_set and num is not None:
                num_set.add(num)
                self.invoice_list.append(invoice)
            invoice.rename()
        super().__init__(self.invoice_list)

    def write2csv(self):
        """将self.invoices写入到pdf_dir目录下的csv文件中
        """
        csv_file_name = f"{str(datetime.now()).replace(':','.')}.csv"
        csv_file_path = os.path.join(self.pdf_dir, csv_file_name)
        with open(csv_file_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=Invoice.field_names)
            writer.writeheader()
            for invoice in self.invoice_list:
                writer.writerow(invoice)


def test_Invoice():
    pdf_paths = [
        os.path.join(r'.\tests', i.name) for i in os.scandir(r'.\tests')
        if i.is_file() and i.name.endswith('.pdf')
    ]
    for pdf_path in pdf_paths:
        invoice = Invoice(pdf_path)
        invoice.rename()
        invoice.write2text()
        print(invoice.pdf_path)


def test_Invoices():
    invoices = Invoices(r'.\tests')
    pprint(list(invoices.invoice_iter))


if __name__ == '__main__':
    test_Invoice()
    # test_Invoices()
