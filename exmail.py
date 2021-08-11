import requests
import datetime
import logging
import json
from common import *

class ExMailApi:
    _base: str = 'https://api.exmail.qq.com/cgi-bin/'
    _corpId: str = None
    _secret: str = None
    _token: str = None
    _tokenExpiry: datetime.datetime = None
    _tokenExpiryThreshold: datetime.timedelta = datetime.timedelta(minutes=10)
    _session: requests.Session = None
    _config: str = 'config.json'

    def __init__(self, configName: str = None) -> None:
        if configName is None:
            configName = self._config
        with open(configName) as fp:
            data = json.load(fp)
        self._corpId = data['corpId']
        self._secret = data['corpSecret']
        self._session = requests.session()
        if data['accessToken'] is not None:
            self._token = data['accessToken']
        if data['accessTokenExpiry'] is not None:
            self._tokenExpiry = datetime.datetime.strptime(data['accessTokenExpiry'], '%Y-%m-%d %H:%M:%S.%f')
    
    def _now(self) -> datetime.datetime:
        return datetime.datetime.now()

    def saveConfig(self) -> None:
        data = {
            'corpId': self._corpId,
            'corpSecret': self._secret,
            'accessToken': self._token,
            'accessTokenExpiry': self._tokenExpiry
        }
        with open(self._config, 'w') as fp:
            json.dump(data, fp, default=str)

    def getToken(self) -> str:
        if self._token == None or self._now() + self._tokenExpiryThreshold > self._tokenExpiry:
            # Get new token
            url = self._base + 'gettoken'
            params = {
                'corpid': self._corpId,
                'corpsecret': self._secret
            }
            r = self._session.get(url, params=params)
            resp = r.json()
            if 'access_token' in resp:
                self._token = resp['access_token']
                self._tokenExpiry = self._now() + datetime.timedelta(seconds=resp['expires_in'])
                self.saveConfig()
                logging.info(f'Token update succeeded, expiry is {self._tokenExpiry}')
            if 'errcode' in resp and resp['errcode'] != 0:
                self._token = None
                self._tokenExpiry = None
                logging.error(f'Token update failed, reason is {resp["errcode"]}({resp["errmsg"]})')
        
        return self._token

class ExMailLogApi(ExMailApi):
    _config = 'log.json'
    def getLoginLog(self, userId: str, dateFrom: datetime.date, dateTo: datetime.date) -> list:
        '''
        获取登录记录
        https://exmail.qq.com/qy_mng_logic/doc#10029
        '''
        url = self._base + 'log/login'
        jsonData = {
            'begin_date': dateFrom.isoformat(),
            'end_date': dateTo.isoformat(),
            'userid': userId
        }
        params = {
            'access_token': self.getToken()
        }
        r = self._session.post(url, json=jsonData, params=params)
        data = r.json()
        if data['errcode'] == 0:
            return data['list']
        else:
            logging.error(f'Error fetching login log for user {userId}, error is {data["errcode"]}({data["errmsg"]})')
            return []

    def getMailLog(self, userId: str, dateFrom: datetime.date, dateTo: datetime.date, type: ExMailType = ExMailType.ALL):
        '''
        获取邮件记录
        https://exmail.qq.com/qy_mng_logic/doc#10028
        '''
        url = self._base + 'log/mail'
        jsonData = {
            'begin_date': dateFrom.isoformat(),
            'end_date': dateTo.isoformat(),
            'userid': userId,
            'mailtype': type.value
        }
        params = {
            'access_token': self.getToken()
        }
        r = self._session.post(url, json=jsonData, params=params)
        data = r.json()
        if data['errcode'] == 0:
            return data['list']
        else:
            logging.error(f'Error fetching mail log for user {userId}, error is {data["errcode"]}({data["errmsg"]})')
            return []

class ExMailContactApi(ExMailApi):
    _config = 'contact.json'
    def getFullDepartmentList(self):
        '''
        获取完整部门列表
        '''
        root = Department.root()
        result = {root.id: root}
        rootList = self.getDepartmentList(root).values()
        for dept in rootList:
            childList = self.getDepartmentList(dept.id)
            if len(childList) > 0:
                dept.hasChild = True
            result[dept.id] = dept
            for childDept in childList.values():
                result[childDept.id] = childDept
        return result
    
    def getDepartmentList(self, id: int = 1):
        '''
        获取部门列表
        https://exmail.qq.com/qy_mng_logic/doc#10011
        '''
        url = self._base + 'department/list'
        params = {
            'id': id,
            'access_token': self.getToken()
        }
        r = self._session.get(url, params=params)
        data = r.json()
        if data['errcode'] == 0:
            result = {}
            for item in data['department']:
                d = Department(item)
                result[d.id] = d
            logging.info(f'Got {len(result)} departments from department [{id}]')
            return result
        else:
            logging.error(f'Error fetching departments for parent {id}, error is {data["errcode"]}({data["errmsg"]})')
            return {}
    
    def getMemberBrief(self, dept: Department, fetchChild: bool = False) -> dict:
        url = self._base + 'user/simplelist'
        params = {
            'department_id': dept.id,
            'access_token': self.getToken(),
            'fetch_child': 1 if fetchChild else 0
        }
        r = self._session.get(url, params=params)
        data = r.json()
        if data['errcode'] == 0:
            result = {}
            for user in data['userlist']:
                result[user['userid']] = user
            logging.info(f'Got {len(result)} users from department [{dept.id}]')
            return result
        else:
            logging.error(f'Error fetching users from department [{dept.id}], error is {data["errcode"]}({data["errmsg"]})')
            return {}
    
    def updateMember(self, userid: str, data: dict) -> bool:
        '''
        更新用户信息
        https://exmail.qq.com/qy_mng_logic/doc#10015
        '''
        url = self._base + 'user/update'
        params = {
            'access_token': self.getToken()
        }
        jsonData = {
            'userid': userid
        }
        jsonData.update(data)
        r = self._session.post(url, params=params, json=jsonData)
        data = r.json()
        logging.info(f'Update user info for {userid} with data {str(jsonData)}, result is {data["errcode"]}, message is {data["errmsg"]}')
        if data['errcode'] == 0:
            return True
        else:
            return False
