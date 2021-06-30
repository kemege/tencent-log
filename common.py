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

def create_all(engine: sqlalchemy.engine):
    Base.metadata.create_all(engine)