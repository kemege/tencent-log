import exmail
import logging

FILENAME = r'C:\Users\admin\XXBDOC\邮件系统相关\日常业务处置\新生别名邮箱\result_2021.txt'

logging.basicConfig(level=logging.INFO, filename='exmail.log',
                    format='%(asctime)s - %(levelname)s : %(message)s')

def setAlias(userid: str, alias: str):
    client.updateMember(userid, {'slaves': [alias]})
    # print(userid, alias)

def main(filename):                   
    data = (x.split('\t') for x in open(filename, encoding='utf-8').read().splitlines())
    for userid, _, alias in data:
        print("set alias %s for %s" % (alias, userid))
        setAlias(userid + '@m.fudan.edu.cn', alias)
        # logging.info("set alias %s for %s" % (alias, userid))

if __name__ == '__main__':
    client = exmail.ExMailContactApi('contact.json')
    main(FILENAME)