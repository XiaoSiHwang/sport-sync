from webdav4.client import Client
import os
import notify
from config import JIAN_GOU_YUN_WEBDAV_PATH, JIAN_GOU_YUN_WEBDAV_DB_DIR, DB_WEBDAV_DIR, JIAN_GOU_YUN_WEBDAV_FIT_FOLDER, JIAN_GOU_YUN_WEBDAV_FIT_UNZIP_FOLDER


WEBDAV_CONFIG = {
    'WEBDAV_URL': '',
    'WEBDAV_USERNAME': '',
    'WEBDAV_PASSWORD': ''
}


class JianGuoYunClient:
    
    def __init__(self) -> None:
        try:
            # 首先读取 面板变量 或者 github action 运行变量
            for k in WEBDAV_CONFIG:
                if os.getenv(k):
                    v = os.getenv(k)
                    WEBDAV_CONFIG[k] = v
            
            # username 为坚果云账号，password 为刚刚创建的密码
            self.client = Client(
                base_url= WEBDAV_CONFIG['WEBDAV_URL'],
                auth=(WEBDAV_CONFIG['WEBDAV_USERNAME'], WEBDAV_CONFIG['WEBDAV_PASSWORD'])
            )
           
            ## 判断是否存在/sport-sync文件夹
            if not self.client.exists(JIAN_GOU_YUN_WEBDAV_PATH):
                self.client.mkdir(JIAN_GOU_YUN_WEBDAV_PATH)
            
            ## 判断是否存在存放db文件夹
            if not self.client.exists(JIAN_GOU_YUN_WEBDAV_PATH + '/' + JIAN_GOU_YUN_WEBDAV_DB_DIR):
                self.client.mkdir(JIAN_GOU_YUN_WEBDAV_PATH + '/' + JIAN_GOU_YUN_WEBDAV_DB_DIR)
            
            ## 判断是否存在存放FIT未解压文件文件夹
            if not self.client.exists(JIAN_GOU_YUN_WEBDAV_PATH + '/' + JIAN_GOU_YUN_WEBDAV_FIT_FOLDER):
                self.client.mkdir(JIAN_GOU_YUN_WEBDAV_PATH + '/' + JIAN_GOU_YUN_WEBDAV_FIT_FOLDER)
            
            ## 判断是否存在存放FIT解压文件文件夹
            if not self.client.exists(JIAN_GOU_YUN_WEBDAV_PATH + '/' + JIAN_GOU_YUN_WEBDAV_FIT_UNZIP_FOLDER):
                self.client.mkdir(JIAN_GOU_YUN_WEBDAV_PATH + '/' + JIAN_GOU_YUN_WEBDAV_FIT_UNZIP_FOLDER)
 
        except Exception as err:
            print(err)
            raise JianGuoYunInitError("初始化坚果云异常，请检查帐号密码是否正确或网络链接情况！！！\n异常信息为：" + str(err)) from err
    
    ## 打开文件
    def open_file(self):
        pass

    ## 上传文件
    def upload_file(self, local_path, remote_path):
        try:
            self.client.upload_file(local_path, remote_path, overwrite=True)
        except Exception as err:
            raise JianGuoYunOptionError("上传文件异常！！！\n异常信息为：" + str(err)) from err
        finally:
            return 
    
    def upload_file_obj(self, file_obj, remote_path):
        try:
            self.client.upload_fileobj(file_obj, remote_path, overwrite=True)
        except Exception as err:
            raise JianGuoYunOptionError("上传文件异常！！！\n异常信息为：" + str(err)) from err
        finally:
            return 

    ## 上传文件
    def upload_file_db(self, local_path, remote_path):
        try:
            if self.is_exists(remote_path):
                self.client.remove(remote_path)
            self.client.upload_file(local_path, remote_path, overwrite=True)
        except Exception as err:
            raise JianGuoYunOptionError("上传文件异常！！！\n异常信息为：" + str(err)) from err
        finally:
            return 

    ##初始DB
    def init_db_file(self, db_name) -> bool:
        try:
            flag = False
            remote_path = JIAN_GOU_YUN_WEBDAV_PATH + '/' + JIAN_GOU_YUN_WEBDAV_DB_DIR + '/' + db_name
            if not self.is_exists(remote_path):
                return flag

            self.client.download_file(remote_path, DB_WEBDAV_DIR+ '/' + db_name)
            flag =  True
        except Exception as err:
            raise JianGuoYunOptionError("初始化DB异常！！！\n异常信息为：" + str(err)) from err
        finally:
            return flag
    
    def is_exists(self, path) -> bool:
        try:
            flag = False
            flag = self.client.exists(path)
        except Exception as err:
            raise JianGuoYunOptionError("文件查询异常！！！\n异常信息为：" + str(err)) from err
        finally:
            return flag



        
        

class JianGuoYunInitError(Exception):
    """Raised when communication ended in error."""

    def __init__(self, status):
        """Initialize."""
        super(JianGuoYunInitError, self).__init__(status)
        notify.send("初始化坚果云异常", status)
        self.status = status


class JianGuoYunOptionError(Exception):
    """Raised when communication ended in error."""

    def __init__(self, status):
        """Initialize."""
        super(JianGuoYunOptionError, self).__init__(status)
        notify.send("坚果云操作异常", status)
        self.status = status
