import datetime
import enum
from sqlalchemy import Column, String, Integer, DateTime, Enum, BigInteger, UniqueConstraint, Index
import sqlalchemy
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class ExMailType(enum.Enum):
    ALL = 0
    SEND = 1
    RECEIVE = 2

class ExLoginType(enum.Enum):
    WEB = 1
    PHONE = 2
    APP = 3
    CLIENT = 4
    OTHER = 5

class ExMailStatus(enum.Enum):
    OTHER = 0
    SENDING = 1
    REJECTED = 2
    SEND_SUCCESS = 3
    SEND_FAILURE = 4
    RECV_REJECTED = 11
    RECV_JUNK = 12
    RECV_SUCCESS = 13
    RECV_PERSONAL = 14
    ADMIN_DELETED = 15

class ExMailOpQueryType(enum.Enum):
    ALL = 0
    PROTOCOL_SYNC = 1
    EDIT_ADMIN = 2
    SET_SUB_ADMIN = 3
    EDIT_CORP = 4
    BLACKLIST = 5
    MAIL_TRANSFER = 6
    MEMBER_MANAGE = 7
    MAIL_BACKUP = 8
    MEMBER_PERMISSION = 9

class ExMailOpType(enum.Enum):
    RESERVED = 0  # Not documented
    LOGIN = 1
    CHANGE_PASSWORD = 2
    ADD_DOMAIN = 3
    DELETE_DOMAIN = 4
    ADD_LOGO = 5
    DELETE_LOGO = 6
    CHANGE_SECURITY_MAIL = 7
    CHANGE_ADMIN_MAIL = 8
    PUBLISH_ANNOUNCEMENT = 9
    BATCH_SEND = 10
    ADD_BLACKLIST = 11
    DELETE_BLACKLIST = 12
    CLEAR_BLACKLIST = 13
    ADD_WHITELIST = 14
    DELETE_WHITELIST = 15
    CLEAR_WHITELIST = 16
    ADD_DOMAIN_WHITELIST = 17
    DELETE_DOMAIN_WHITELIST = 18
    ADD_USER = 19
    DELETE_USER = 20
    ENABLE_USER = 21
    DISABLE_USER = 22
    EDIT_USER = 23
    EDIT_USER_ALIAS = 24
    IMPORT_USER = 25
    ADD_SUB_ADMIN = 26
    DELETE_SUB_ADMIN = 27
    ADD_DEPARTMENT = 28
    DELETE_DEPARTMENT = 29
    EDIT_DEPARTMENT = 30
    MOVE_DEPARTMENT = 31
    ADD_MAILGROUP = 32
    DELETE_MAILGROUP = 33
    EDIT_MAILGROUP = 34
    SETUP_MAIL_BACKUP = 35
    TRANSFER_MAIL = 36
    SETUP_IP_PERMISSION = 37
    LIMIT_SEND_OUTSIDE = 38
    ENABLE_API = 39
    RESET_API_KEY = 40
    DISABLE_API = 41
    CHANGE_CORP_NAME = 42
    EXPORT_ARCHIVE_MAIL = 43
    REBIND_MAILBOX = 44
    CHANGE_PASSWORD_45 = 45  # TODO: distinguish with 2
    CHANGE_DOMAIN_LIMIT = 46
    MEMBER_CHANGE_PASSWORD = 47
    ENABLE_AUTO_FORWARD = 48
    DISABLE_AUTO_FORWARD = 49
    ENABLE_SAFE_LOGIN = 50
    DISABLE_SAFE_LOGIN = 51
    ALLOW_MEMBER_RECOVER_MAIL = 52
    DISALLOW_MEMBER_RECOVER_MAIL = 53
    ALLOW_MEMBER_AUTO_FORWARD = 54
    DISALLOW_MEMBER_AUTO_FORWARD = 55
    ENABLE_ARCHIVE = 56
    DISABLE_ARCHIVE = 57
    EXPORT_ARCHIVE = 58
    VIEW_ARCHIVE = 59
    ADD_LIMIT_SEND_OUTSIDE = 60
    DELETE_LIMIT_SEND_OUTSIDE = 61
    ENABLE_CHANGE_PASSWORD_PERIOD = 62
    DISABLE_CHANGE_PASSWORD_PERIOD = 63
    ADD_BACKUP_RULE = 64
    DELETE_BACKUP_RULE = 65
    CHANGE_MEMBER_PASSWORD = 66
    CLEAR_LIMIT_SEND_OUTSIDE = 67
    CONVERT_TO_SHARED_MAIL = 68
    ADD_SHARED_MAIL = 69
    DELETE_SHARED_MAIL = 70
    CHANGE_SHARED_MAIL = 71
    ADD_LABEL = 72
    CHANGE_LABEL = 73
    DELETE_LABEL = 74
    ADD_LABEL_MEMBER = 75
    DELETE_LABEL_MEMBER = 76
    IMPORT_LABEL = 77
    CONVERT_DEPARTMENT_TO_GROUP = 78
    UNBIND_MAIL = 79
    DELETE_UNBINDED_MAIL = 80
    RECYCLE_SHARED_MAIL = 81
    DELETE_MAILBOX = 82
    MERGE_DATA_AND_MAILBOX = 83


class Department:
    id: int
    name: str
    parentId: int = 1
    order: int = 1
    hasChild: bool = False

    def __init__(self, data: dict = None) -> None:
        if data is not None:
            self.id = data['id']
            self.name = data['name']
            self.parentId = data['parentid']
            self.order = data['order']

    def __repr__(self) -> str:
        return f'Department(id={self.id}, name={self.name}, parentId={self.parentId})'

    @staticmethod
    def root():
        data = {
            'id': 1,
            'name': 'ROOT',
            'parentid': None,
            'order': 1
        }
        return Department(data)

class MailBox(Base):
    __tablename__ = 'mail_box'
    address = Column(String(255), primary_key=True)
    department_id = Column(String(255))
    alias = Column(String(255))
    need_reset_password = Column(Integer)
    updated = Column(DateTime, default=datetime.datetime.fromtimestamp(0))

class LoginLog(Base):
    __tablename__ = 'login_log'

    id = Column(BigInteger, primary_key=True)
    time = Column(DateTime, index=True)
    address = Column(String(255), index=True)
    type = Column(Enum(ExLoginType))
    ip = Column(String(64), index=True)

    uniqueIndex = UniqueConstraint(time, address, type, ip)
    

    def __repr__(self) -> str:
        return f'LoginLog(time={self.time}, address={self.address}, ip={self.ip}, type={self.type})'

class MailLog(Base):
    __tablename__ = 'mail_log'

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, index=True)
    sender = Column(String(255), index=True)
    receiver = Column(String(255), index=True)
    subject = Column(String(255))
    type = Column(Enum(ExMailType))
    status = Column(Enum(ExMailStatus))

    uniqueIndex = UniqueConstraint(time, sender, receiver, subject, type)

    def __repr__(self) -> str:
        return f'MailLog(time={self.time}, from={self.sender}, to={self.receiver}, status={self.status})'

class OpLog(Base):
    __tablename__ = 'op_log'

    id = Column(BigInteger, primary_key=True)
    time = Column(DateTime, index=True)
    operator = Column(String(255))
    type = Column(Enum(ExMailOpType))
    operand = Column(String(255))

    uniqueIndex = UniqueConstraint(time, operator, type, operand)

    def __repr__(self) -> str:
        return f'OpLog(time={self.time}, operator={self.operator}, type={self.type}, operand={self.operand})'


def create_all(engine: sqlalchemy.engine):
    Base.metadata.create_all(engine)