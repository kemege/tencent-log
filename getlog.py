import datetime
import json
import fire
import logging
import sqlalchemy
import multiprocessing
from sqlalchemy import sql
from sqlalchemy.dialects.mysql import insert
from exmail import *

DEPARTMENT_JSON = 'department.json'
DEPT_USER_JSON = 'dept-user.json'

logging.basicConfig(level=logging.INFO, filename='exmail.log',
                    format='%(asctime)s - %(levelname)s : %(message)s')

def getDepartment(deptId: int):
    '''获取部门信息'''
    with open(DEPARTMENT_JSON) as fp:
        data: dict = json.load(fp)
    d = data.get(deptId, None)
    if d is not None:
        dept = Department()
        dept.__dict__.update(d)
        return dept
    else:
        return None


def syncDepartmentList(client: ExMailContactApi):
    '''同步部门列表'''
    deptList = client.getFullDepartmentList()
    with open(DEPARTMENT_JSON, 'w') as fp:
        json.dump(deptList, fp,
                  default=lambda x: x.__dict__,
                  indent=4)

def syncDepartmentUserList(client: ExMailContactApi, deptId: int):
    '''同步指定部门下的用户列表'''
    deptUserList = client.getMemberBrief(getDepartment(deptId))
    with open(DEPT_USER_JSON, 'w') as fp:
        json.dump(deptUserList, fp,
                  default=lambda x: x.__dict__,
                  indent=4)

def syncUserList(client: ExMailContactApi, config: dict):
    '''同步用户列表'''
    userList = client.getMemberDetail(Department.root(), True)
    logging.info(f'Fetched {len(userList)} users')
    db = getDB(config['db'])
    with sqlalchemy.orm.Session(db) as session:
        session.begin()
        for u in userList.values():
            data = {
                'address': u['userid'],
                'department_id': ','.join([str(x) for x in u['department']]),
                'alias': ','.join(u['slaves']),
                'need_reset_password': u['cpwd_login']
            }
            stmt = sqlalchemy.dialects.mysql.insert(MailBox).values(data).on_duplicate_key_update(data)
            session.execute(stmt)
        session.commit()
    logging.info('User fetching is finished')

def loginLogs(client: ExMailLogApi, config: dict, date1: datetime.date, date2: datetime.date):
    '''同步登录日志'''
    db = getDB(config['db'])
    logging.info('Selecting users for fetching login logs')
    stmt = sqlalchemy.select(MailBox)
    mailboxes = []
    with sqlalchemy.orm.Session(db) as session:
        for row in session.execute(stmt):
            mailboxes.append(row[0].address)
    logging.info(f'Fetching login logs for {len(mailboxes)} users')

    with sqlalchemy.orm.Session(db) as session:
        for m in mailboxes:
            logging.info(f'Fetching login log for user {m} from {date1.isoformat()} to {date2.isoformat()}')
            logs = client.getLoginLog(m, date1, date2)
            session.begin()
            # session.execute(sqlalchemy.delete(LoginLog)
            #                           .where(LoginLog.time >= datetime.datetime.combine(date1, timeStart))
            #                           .where(LoginLog.time <= datetime.datetime.combine(date2, timeEnd))
            #                           .where(LoginLog.address == m))
            for log in logs:
                data = {
                    'time': datetime.datetime.fromtimestamp(log['time']),
                    'address': m,
                    'type': ExLoginType(log['type']),
                    'ip': log['ip']
                }
                session.execute(insert(LoginLog).values(data).on_duplicate_key_update(data))
            session.commit()


def mailLogs(client: ExMailLogApi, config: dict, date1: datetime.date, date2: datetime.date):
    '''同步邮件日志'''
    db = getDB(config['db'])
    logging.info('Selecting users for fetching mail logs')
    stmt = sqlalchemy.select(MailBox)
    mailboxes = []
    with sqlalchemy.orm.Session(db) as session:
        for row in session.execute(stmt):
            mailboxes.append(row[0].address)
    logging.info(f'Fetching mail logs for {len(mailboxes)} users')

    with sqlalchemy.orm.Session(db) as session:
        for m in mailboxes:
            logging.info(f'Fetching mail log for user {m} from {date1.isoformat()} to {date2.isoformat()}')
            logs = client.getMailLog(m, date1, date2)
            session.begin()
            for log in logs:
                data = {
                    'time': datetime.datetime.fromtimestamp(log['time']),
                    'sender': log['sender'],
                    'receiver': log['receiver'],
                    'subject': log['subject'],
                    'status': ExMailStatus(log['status']),
                    'type': ExMailType(log['mailtype'])
                }
                session.execute(insert(MailLog).values(data).on_duplicate_key_update(data))
            session.commit()

def getDB(config: dict):
    '''连接数据库'''
    url = f'mysql+pymysql://{config["user"]}:{config["password"]}@{config["host"]}:{config["port"]}/{config["database"]}'
    return sqlalchemy.create_engine(url)

class CLI:
    '''控制对外暴露的函数列表'''
    def __init__(self) -> None:
        with open('config.json') as fp:
            self.config = json.load(fp)
        self.logClient = ExMailLogApi()
        self.contactClient = ExMailContactApi()

    def syncDepartment(self) -> None:
        '''同步所有部门信息'''
        syncDepartmentList(self.contactClient)
    
    def syncLoginLog(self) -> None:
        '''同步最近两天的登录日志'''
        date1 = datetime.date.today() - datetime.timedelta(days=2)
        date2 = datetime.date.today()
        loginLogs(self.logClient, self.config, date1, date2)
    
    def syncMailLog(self) -> None:
        '''同步最近两天的邮件日志'''
        date1 = datetime.date.today() - datetime.timedelta(days=2)
        date2 = datetime.date.today()
        mailLogs(self.logClient, self.config, date1, date2)
    
    def initDB(self) -> None:
        '''初始化数据表'''
        db = getDB(self.config['db'])
        create_all(db)
    
    def syncUser(self) -> None:
        '''同步用户列表'''
        syncUserList(self.contactClient, self.config)

if __name__ == '__main__':
    fire.Fire(CLI)
