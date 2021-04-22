import re
import js2py
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from sqlalchemy import create_engine, Column, String
from sqlalchemy.orm import sessionmaker, declarative_base
from config import username, password, hostname, dbname

engine = create_engine("mysql+pymysql://{username}:{password}@{hostname}/{dbname}?charset=utf8"
                       .format(username=username, password=password, hostname=hostname, dbname=dbname))
Session = sessionmaker(bind=engine)
Base = declarative_base()


class Fund(Base):
    __tablename__ = "funds"
    code = Column(String(20), primary_key=True)
    capitals = Column(String(40))
    name = Column(String(40))
    fund_type = Column(String(20))
    pinyin = Column(String(120))

    def __repr__(self):
        return "<Fund(name='{}', code='{}')>".format(self.name, self.code)


Base.metadata.create_all(engine)


def get_all_funds_info():
    Fund.__table__.drop(engine)
    Base.metadata.create_all(engine)
    all_funds_url = 'http://fund.eastmoney.com/js/fundcode_search.js'
    response = requests.get(all_funds_url)
    js_code = response.text
    context = js2py.EvalJs()
    context.execute(js_code)
    all_funds_list = context.r
    session = Session()
    for fund_info in all_funds_list:
        if fund_info[3] == '股票指数':
            fund_info[3] = '指数型'
        fund = Fund(code=fund_info[0], capitals=fund_info[1], name=fund_info[2],
                    fund_type=fund_info[3], pinyin=fund_info[4])
        session.add(fund)
    session.commit()


def get_fund_net_worth(fund_code, start_date, end_date):
    """
    input:
        fund_code, 基金代码; start_date, 查询起始日; end_date, 查询截止日

    output:
        净值日期, 单位净值, 累计净值, 日增长率, 申购状态, 赎回状态, 分红送配
    """
    days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days + 1
    url_model = 'https://fundf10.eastmoney.com/F10DataApi.aspx?type=lsjz&code={}&sdate={}&edate={}&per={}'
    url = url_model.format(fund_code, start_date, end_date, days)
    r = requests.get(url)
    js_code = r.text
    record_num = int(re.search('(?<=records:)\\d+', js_code).group(0))
    soup = BeautifulSoup(js_code, 'lxml')
    table_rows = []
    for rows in soup.findAll("tbody")[0].findAll("tr"):
        table_records = []
        for record in rows.findAll('td'):
            val = record.contents
            if len(val) == 0:
                table_records.append(None)
            else:
                table_records.append(val[0])
        table_rows.append(table_records)
    if len(table_rows) > record_num:
        table_rows = table_rows[:record_num]
    return table_rows


r = get_fund_net_worth('000176', '2021-04-20', '2021-04-21')
for x in r:
    print(x)
# get_all_funds_info()
