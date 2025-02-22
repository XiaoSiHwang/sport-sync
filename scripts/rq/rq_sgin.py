import time
import httpx
import random
import asyncio
import os
import sys 
CURRENT_DIR = os.path.split(os.path.abspath(__file__))[0]  # 当前目录
config_path = CURRENT_DIR.rsplit('/', 1)[0]  # 上三级目录
sys.path.append(config_path)

from config import DB_DIR, AESKEY
from sqlite_db import  SqliteDB
from aestools import AESCipher
from rq_connect import RQConnect
import notify

import ddddocr


ocr = ddddocr.DdddOcr(beta=True, show_ad=False)

TIME_OUT = httpx.Timeout(1000.0, connect=1000.0)

RQ_CONFIG = {
    "RQ_EMAIL": '',
    "RQ_PASSWORD": '',
}

class RqSgin:
    def __init__(self, userId, token) :
        self.req = httpx.AsyncClient(timeout=TIME_OUT)
        ## 签到请求头
        self.headers = {
            "Host": "rq.runningquotient.cn",
            "Origin": "https://rq.runningquotient.cn",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148",
            # "Referer": f"https://rq.runningquotient.cn/Minisite/SignIn/index?userId={userId}&token={token}",
            "Referer": "https://rq.runningquotient.cn/Minisite/SignIn/index",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        ## RQ用户ID
        self.userId = userId
        ## RQ用户token
        self.token = token
    
    async def sigin(self):
        ## 随机数
        randomNum = random.uniform(0,2)
        ## 签到Url
        siginUrl = f"https://rq.runningquotient.cn/MiniApi/SignIn/sign_in/rand/{randomNum}"
        ## PHPSESSID 目前不作存储不清楚RQ原理这块是否会过期故每次请求签到都获取新的PHPSESSID，防止RQ判断用户会脚本执行签到
        PHPSESSID = await self.getSiginPHPSESSID()
        ## 设置请求头Cookie
        self.headers['Cookie'] = f"PHPSESSID={PHPSESSID}"
        threshold = 10
        signVerifyCodeStatus = False
        i = 1
        ## 10次阈值，超过10次都登录不了不执行等下一轮再执行了
        while not signVerifyCodeStatus and i <= threshold:
          try:
              signVerifyCode = await self.getSignVerifyCode(PHPSESSID)
              
              ## 执行签到
              response = await self.req.post(
                  siginUrl,
                  headers=self.headers,
                  data={'codes': signVerifyCode}
              )
              result = response.json()
              print(result)
              status = result['status']
              ## 判断是否签到成功
              if status == 1:
                  notify.send("RQ签到任务", "签到成功！！！！")
                  return
              ## 判断验证码是否错误
              elif status == 10011:
                  pass
              ## 判断是否已经签到了
              elif status == 10009:
                  return
              i+=1
              time.sleep(1)
              
          except Exception as err:
              raise err

    async def getSignVerifyCode(self, PHPSESSID):
        ## 验证码URL
        signVerifyCodeUrl = f"https://rq.runningquotient.cn/Minisite/SignIn/sign_verify_code"
        ## PHPSESSID 目前不作存储不清楚RQ原理这块是否会过期故每次请求签到都获取新的PHPSESSID，防止RQ判断用户会脚本执行签到
        ## 设置请求头Cookie
        self.headers['Cookie'] = f"PHPSESSID={PHPSESSID}"
             ## 执行签到
        response = await self.req.get(
                signVerifyCodeUrl,
                headers=self.headers
            )
        
        res = ocr.classification(response.content)
        return res

    ## 调用获取请求头Referer里面的Cookie
    async def getSiginPHPSESSID(self):
        try:
            response = await self.req.get(
                 f"https://rq.runningquotient.cn/Minisite/SignIn/index?userId={self.userId}&token={self.token}",
            )
            return response.cookies['PHPSESSID']
        except Exception as err:
            raise err


def isKeyValid(aesChiper, text):
    try:
        aesChiper.decrypt(text)
        return True
    except Exception as e:
        return False

async def rq_sigin(email, password, AES_KEY):
    aesChiper = AESCipher(AES_KEY)
    # rq_login = RqLogin(email,password)
    rq_connect = RQConnect(email, password, rqdbpath)
    encrypt_email = aesChiper.encrypt(email)
    with SqliteDB(rqdbpath) as db:
        ## 加密email
        
        ## 查询数据库是否存在已保存的帐号信息
        query_set = db.execute('select * from user_info where email=?', (encrypt_email, )).fetchall()
        ## 查询返回条数
        query_size = len(query_set)
        ## 判断是否唯一
        if query_size == 1:
            ## 加密user_id
            encrypt_user_id = query_set[0][2]
            ## 加密access_token
            encrypt_access_token = query_set[0][3]
            
            ## 判断AES KEY 能否解密当前加密数据
            isValid = isKeyValid(aesChiper, encrypt_user_id)
            
            ## 能解密则执行如下
            if isValid:
                ## 判断存储的token是否过期
                isExpired = await rq_connect.isExpiredToken(aesChiper, encrypt_user_id, encrypt_access_token)
                if not isExpired:
                    rqs = RqSgin(
                        aesChiper.decrypt(encrypt_user_id),
                        aesChiper.decrypt(encrypt_access_token)
                    )
                    ## 登录一次更新一次时间保证action不掉线
                await rqs.sigin()
                db.execute('''UPDATE user_info SET update_date = datetime('now','localtime') ''')
                return
            
        ## 如果数据库中存储的帐号条数大于一条默认全部删除登录后再插入一条保持数据的唯一
        elif query_size > 1:
            for row in query_set:
                db.execute('delete from user_info where id = ? ', (row[0],))
        else:
            pass
    with SqliteDB(rqdbpath) as db:
        isSuccessLogin = await rq_connect.login(aesChiper)
        
        if isSuccessLogin == True:
            query_set = db.execute('select * from user_info where email=?', (encrypt_email, )).fetchall()
            ## 加密user_id
            encrypt_user_id = query_set[0][2]
            ## 加密access_token
            encrypt_access_token = query_set[0][3]
            rqs = RqSgin(
                aesChiper.decrypt(encrypt_user_id),
                aesChiper.decrypt(encrypt_access_token)
            )
            await rqs.sigin()
        else:
            print("帐号密码有误，请检查帐号密码信息！！！")

## 初始化建表
def initRQDB(rqdbpath):
    with SqliteDB(rqdbpath) as db:
        db.execute('''CREATE TABLE user_info (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(100), user_id  VARCHAR(100),
            access_token VARCHAR(100),
            create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            update_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )'''
        )


class AESKEYTooLongExceptin(Exception):
    "this is user's Exception for check the length of name "
    def __init__(self, meeasge, lens):
        self.meeasge = meeasge
        self.lens = lens
    def __str__(self):
        print(f"AES key must be either 16, 24, or 32 bytes long, current AES Key length is {str(self.lens)}")


if __name__ == "__main__":
    db_name = 'rq.db'

    # 首先读取 面板变量 或者 github action 运行变量
    for k in RQ_CONFIG:
        if os.getenv(k):
            v = os.getenv(k)
            RQ_CONFIG[k] = v

    ## AES─KEY不能超过32位
    try:
        if(len(AESKEY) > 32):
            raise AESKEYTooLongExceptin(f"AES KEY Too Long", len(AESKEY))
    except AESKEYTooLongExceptin as e_result:
        print(e_result)

    ## 判断存储数据文件夹是否存在
    if not os.path.exists(DB_DIR):
        os.mkdir(DB_DIR)
    

    rqdbpath = os.path.join(DB_DIR, db_name)

    ## 判断RQ数据库是否存在
    if not os.path.exists(rqdbpath):
        ## 初始化建表
        initRQDB(rqdbpath)
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(
        rq_sigin(RQ_CONFIG['RQ_EMAIL'], RQ_CONFIG['RQ_PASSWORD'], AESKEY)
    )
    loop.run_until_complete(future)
   