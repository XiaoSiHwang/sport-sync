

import pickle

import os
import sys 
CURRENT_DIR = os.path.split(os.path.abspath(__file__))[0]  # 当前目录
config_path = CURRENT_DIR.rsplit('/', 1)[0]  # 上三级目录
sys.path.append(config_path)

# from sqlite_db import SqliteDB
from sqlite_db_webdav import SqliteWebDAVDB as SqliteDB
from aestools import AESCipher

from config import DB_WEBDAV_DIR

from jianguoyun_client import JianGuoYunClient


class GarminDB:

    def __init__(self, client, garmin_db_path, aes_key, garmin_cookie):
        ## 佳明数据库存储路径
        self.garmin_db_path = garmin_db_path
        ## 佳明链接客户端
        self.client = client
        
        self.garmin_cookie = garmin_cookie
        self.aesChiper = AESCipher(aes_key)
        self.jianguoyun_client = JianGuoYunClient()
        self.jianguoyun_client.init_db_file(garmin_db_path)

        
 
    ## 保存Garmin Cookie至数据库
    def saveCookeie(self, is_main=True):
        # 序列号cookie
        serial_cookeie = pickle.dumps(self.client.req.cookies)
        encrypt_main_email = self.aesChiper.encrypt(self.garmin_cookie.main_email)
        encrypt_main_auth_domain = self.aesChiper.encrypt(self.garmin_cookie.main_auth_domain)
        encrypt_sync_email = self.aesChiper.encrypt(self.garmin_cookie.sync_email)
        encrypt_sync_auth_domain = self.aesChiper.encrypt(self.garmin_cookie.sync_auth_domain)

        

        exists_select_sql = 'SELECT * FROM garmin_cookie WHERE main_email = ? and main_domain = ?  and sync_email = ? and sync_domain = ?'
        init_sql = 'insert into garmin_cookie (main_email, main_domain, sync_email,sync_domain) values (?, ?, ?, ?)'
        cookie_insert_sql = ''
        if is_main:
            cookie_insert_sql = '''
                UPDATE garmin_cookie
                SET main_cookie = ?,
                update_date = datetime('now')
                WHERE id = ?
            '''
        else:
            cookie_insert_sql = '''
                UPDATE garmin_cookie
                SET sync_cookie = ?,
                update_date =  datetime('now')
                WHERE id = ?
            '''

        with SqliteDB(os.path.join(DB_WEBDAV_DIR, self.garmin_db_path)) as db:
            ## 根据email 和 区域后缀查询查询是否存储了用户
            exists_query_set = db.execute(exists_select_sql, (encrypt_main_email, encrypt_main_auth_domain, encrypt_sync_email, encrypt_sync_auth_domain)).fetchall()

            query_size = len(exists_query_set)
            if query_size == 0:
                db.execute(init_sql, (encrypt_main_email, encrypt_main_auth_domain, encrypt_sync_email, encrypt_sync_auth_domain))
                id = exists_query_set = db.execute(exists_select_sql, (encrypt_main_email, encrypt_main_auth_domain, encrypt_sync_email, encrypt_sync_auth_domain)).fetchall()[0][0]

                db.execute(cookie_insert_sql, (serial_cookeie, str(id)))
            else:
                db.execute(cookie_insert_sql, (serial_cookeie, exists_query_set[0][0]))

    ## 从数据库获取Main Garmin Cookie 
    def getCookie(self, is_main=True):

        cookie_select_sql = ''


        encrypt_main_email = self.aesChiper.encrypt(self.garmin_cookie.main_email)
        encrypt_main_auth_domain = self.aesChiper.encrypt(self.garmin_cookie.main_auth_domain)
        encrypt_sync_email = self.aesChiper.encrypt(self.garmin_cookie.sync_email)
        encrypt_sync_auth_domain = self.aesChiper.encrypt(self.garmin_cookie.sync_auth_domain)


        exists_select_sql = 'SELECT * FROM garmin_cookie WHERE main_email = ? and main_domain = ?  and sync_email = ? and sync_domain = ?'

        if is_main:
            cookie_select_sql = 'SELECT main_cookie FROM garmin_cookie WHERE id = ? '
        else:
            cookie_select_sql = 'SELECT sync_cookie FROM garmin_cookie WHERE id = ?'

        with SqliteDB(os.path.join(DB_WEBDAV_DIR, self.garmin_db_path)) as db:
            exists_query_set = db.execute(exists_select_sql, (encrypt_main_email, encrypt_main_auth_domain, encrypt_sync_email, encrypt_sync_auth_domain)).fetchall()

            query_size = len(exists_query_set)
            if query_size == 0:
                return None
            else:
                id = str(exists_query_set[0][0])
                cookie_set = db.execute(cookie_select_sql, (id)).fetchall()
                result = cookie_set[0][0] if cookie_set[0][0] != ''   else None
                
                return result

    def getId(self):
    
        encrypt_main_email = self.aesChiper.encrypt(self.garmin_cookie.main_email)
        encrypt_main_auth_domain = self.aesChiper.encrypt(self.garmin_cookie.main_auth_domain)
        encrypt_sync_email = self.aesChiper.encrypt(self.garmin_cookie.sync_email)
        encrypt_sync_auth_domain = self.aesChiper.encrypt(self.garmin_cookie.sync_auth_domain)
        
        exists_select_sql = 'SELECT * FROM garmin_cookie WHERE main_email = ? and main_domain = ?  and sync_email = ? and sync_domain = ?'
        with SqliteDB(self.garmin_db_path) as db:
            exists_query_set = db.execute(exists_select_sql, (encrypt_main_email, encrypt_main_auth_domain, encrypt_sync_email, encrypt_sync_auth_domain)).fetchall()
            query_size = len(exists_query_set)
            if query_size == 0:
                return None
            else:
                id = str(exists_query_set[0][0])
                return id
    
    def uploaded_activity(self, activity_id):
        with SqliteDB(self.garmin_db_path) as db:
            db.execute('insert into uploaded_activity (garmin_cookie_id, activity_id) values (?, ?)', (self.garmin_cookie.id, activity_id) )


## 初始化建表
def initGarminDB(garmin_db_path):
    with SqliteDB(os.path.join(DB_WEBDAV_DIR, garmin_db_path)) as db:
        db.execute('''
        CREATE TABLE garmin_cookie (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            main_email VARCHAR(100), main_domain  VARCHAR(100), main_cookie TEXT DEFAULT "" NOT NULL,
            sync_email VARCHAR(100), sync_domain  VARCHAR(100), sync_cookie TEXT DEFAULT "" NOT NULL,
            create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            update_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        

        '''
        )

        db.execute('''
            CREATE TABLE uploaded_activity (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
           	garmin_cookie_id INTEGER NOT NULL,
           	activity_id varchar(255) NOT NULL,
            create_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            update_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')