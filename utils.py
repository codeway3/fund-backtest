import js2py
import requests
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


get_all_funds_info()
