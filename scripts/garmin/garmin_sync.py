import os
import asyncio
import pickle
import io
import typing
import aiofiles
import traceback
import zipfile

import time
import sys 
CURRENT_DIR = os.path.split(os.path.abspath(__file__))[0]  # 当前目录
config_path = CURRENT_DIR.rsplit('/', 1)[0]  # 上三级目录
sys.path.append(config_path)

from config import JIAN_GOU_YUN_WEBDAV_PATH, JIAN_GOU_YUN_WEBDAV_DB_DIR, JIAN_GOU_YUN_WEBDAV_FIT_FOLDER,FIT_DIR, DB_DIR, LOCAL_OR_WEBDAV,AESKEY
from garmin_connect import GarminConnect
from garmin_db import GarminDB, initGarminDB
from garmin_cookie import GarminCookie
from jianguoyun_client import JianGuoYunClient

SYNC_CONFIG = {
    'SOURCE_GARMIN_AUTH_DOMAIN': '',
    'SOURCE_GARMIN_EMAIL': '',
    'SOURCE_GARMIN_PASSWORD': '',
    'SYNC_GARMIN_AUTH_DOMAIN': '',
    'SYNC_GARMIN_EMAIL': '',
    'SYNC_GARMIN_PASSWORD': '',
}


async def load_garmin_db(client, is_main, garmin_cookie):
    garmin_db_client = GarminDB(client, db_name, AESKEY, garmin_cookie)
    serial_cookeie = garmin_db_client.getCookie(is_main)
    if serial_cookeie != None:
        cookeie = pickle.loads(serial_cookeie)
        client.req.cookies = cookeie
        client.is_login = True
        await client.test_login()
        if not client.is_login:
            client.login()
            garmin_db_client.saveCookeie(is_main)
        if  is_main:
            garmin_cookie.set_id(garmin_db_client.getId())
    if serial_cookeie == None:
        client.login()
        if client.is_login:
            id = garmin_db_client.saveCookeie(is_main)
            if is_main:
                garmin_cookie.set_id(id)
    return garmin_db_client

def init_webdav_source():
    ## 判断RQ数据库是否存在
    if not os.path.exists(os.path.join(DB_DIR, db_name)):
        ## 初始化建表
        initGarminDB(db_name)

    if not os.path.exists(FIT_DIR):
        os.mkdir(FIT_DIR)

async def upload_activity(main_client, sync_client, activity_id):
    try:

        #下载保存路径
        download_folder = os.path.join(FIT_DIR, 'FIT-' + main_client.email + "-" + main_client.auth_domain) 
        if not os.path.exists(download_folder):
            os.mkdir(download_folder)
        

        unzip_folder = os.path.join(FIT_DIR, "FIT-UNZIP-" + main_client.email + "-" + main_client.auth_domain)
         ## 如果下载类型是fit需要新增解压路径
        if not os.path.exists(unzip_folder):
            os.mkdir(unzip_folder)
        file_data = await main_client.download_activity_fit(activity_id)
        file_path = os.path.join(download_folder, f"{activity_id}.zip")
        async with aiofiles.open(file_path, "wb") as fb:
            await fb.write(file_data)
        unzip_fit_name_list = await unzip_fit(str(activity_id) + '.zip', unzip_folder, download_folder)
        for file_name in unzip_fit_name_list:
            file_path = os.path.join(unzip_folder, file_name)
            upload_file_type = os.path.splitext(file_path)[-1]
            flag = await sync_client.upload_activity(file_path, upload_file_type, activity_id)
        ## 选择WEBDAV
        if LOCAL_OR_WEBDAV and flag:
            activity_fit_zip_name = JIAN_GOU_YUN_WEBDAV_PATH + '/' + JIAN_GOU_YUN_WEBDAV_FIT_FOLDER + '/' + str(ma.activityId) + '.zip'
            jianguoyun_client.upload_file(file_path, activity_fit_zip_name)
            time.sleep(5)

    except:
        print(f"Failed to upload_activity {activity_id}: ")
        traceback.print_exc()

async def unzip_fit(zip_file_name, unzip_folder, zip_folder):
    try:
        zFile = zipfile.ZipFile(zip_folder + "/" + zip_file_name, "r")
        uizip_file_name_list = []
        for fileM in zFile.namelist(): 
            zFile.extract(fileM, unzip_folder)
            uizip_file_name_list.append(fileM)
        zFile.close()
        return uizip_file_name_list
    except:
        print(f"Failed to unzip flie, the zip name is : {zip_file_name}")


if __name__ == "__main__":
    start = time.time()
    db_name = "garmin.db"

    # 首先读取 面板变量 或者 github action 运行变量
    for k in SYNC_CONFIG:
        if os.getenv(k):
            v = os.getenv(k)
            SYNC_CONFIG[k] = v

    # print(LOCAL_OR_WEBDAV)
    # FIT_DIR = FIT_WEBDAV_DIR if LOCAL_OR_WEBDAV else FIT_FOLDER
    # DB_DIR = DB_WEBDAV_DIR if LOCAL_OR_WEBDAV else LOCAL_DB_DIR
    # print(DB_DIR)
    ## 初始化webdav文件
    init_webdav_source()
    jianguoyun_client = None
    if LOCAL_OR_WEBDAV:
        jianguoyun_client = JianGuoYunClient()
    
    ## 建立主Garmin 链接
    main_client = GarminConnect(SYNC_CONFIG["SOURCE_GARMIN_EMAIL"],SYNC_CONFIG["SOURCE_GARMIN_PASSWORD"],SYNC_CONFIG["SOURCE_GARMIN_AUTH_DOMAIN"],False)
    ## 建立Sync Garmin 链接
    sync_client = GarminConnect(SYNC_CONFIG["SYNC_GARMIN_EMAIL"],SYNC_CONFIG["SYNC_GARMIN_PASSWORD"],SYNC_CONFIG["SYNC_GARMIN_AUTH_DOMAIN"],False)
    
    garmin_cookie = GarminCookie(SYNC_CONFIG["SOURCE_GARMIN_EMAIL"],SYNC_CONFIG["SOURCE_GARMIN_AUTH_DOMAIN"],SYNC_CONFIG["SYNC_GARMIN_EMAIL"], SYNC_CONFIG["SYNC_GARMIN_AUTH_DOMAIN"])

    loop = asyncio.get_event_loop()
   
    ## 加载Cookie
    load_garmin_db_tasks = [
        asyncio.ensure_future(load_garmin_db(main_client, True, garmin_cookie)),
        
        asyncio.ensure_future(load_garmin_db(sync_client, False, garmin_cookie))
    ]

    loop.run_until_complete(asyncio.gather(*load_garmin_db_tasks))

    ## 获取主与Sync Garmin的所有运动信息List
    get_all_activity_list_tasks = [
        asyncio.ensure_future(main_client.get_all_activity_list(0)),
        
        asyncio.ensure_future(sync_client.get_all_activity_list(0))
    ]

    loop.run_until_complete(asyncio.gather(*get_all_activity_list_tasks))
    
    main_activity_list = get_all_activity_list_tasks[0].result()
    sync_activity_list = get_all_activity_list_tasks[1].result()
    
    ## 需要上传的主Garmin activityID
    upload_activityID_list = []

    webdav_zip_name_list = []
    ## 如果配置了WEBDAV
    if LOCAL_OR_WEBDAV:
        for i in jianguoyun_client.client.ls( JIAN_GOU_YUN_WEBDAV_PATH + '/' + JIAN_GOU_YUN_WEBDAV_FIT_FOLDER):
            webdav_zip_name_list.append(i['display_name'])

    sync_activity_key_list = []

    for sa in sync_activity_list:
        Key = str(sa.startTimeLocal)
        sync_activity_key_list.append(Key)
    
    # 遍历所有主garmin运动信息
    for ma in main_activity_list:
        # 是否上传标识
        uploadFlag = False
        Key = str(ma.startTimeLocal)
        if Key in sync_activity_key_list:
            ## 如果配置了WEBDAV
            # if LOCAL_OR_WEBDAV:
            #     zip_name = str(ma.activityId) + '.zip'
            #     activity_fit_zip_name = JIAN_GOU_YUN_WEBDAV_PATH + '/' + JIAN_GOU_YUN_WEBDAV_FIT_FOLDER + '/' + zip_name
            #     if zip_name not in webdav_zip_name_list:
            #         download_activity_fit_task = asyncio.ensure_future(main_client.download_activity_fit(ma.activityId))
            #         loop.run_until_complete(download_activity_fit_task)
            #         #运动数据上传至坚果云
            #         jianguoyun_client.upload_file_obj(typing.cast(typing.BinaryIO, io.BytesIO(download_activity_fit_task.result())) , activity_fit_zip_name)
            #         time.sleep(2)
            pass
        else:
            uploadFlag = True
                
        ## 如果没有该数据则加入upload_activityID_list
        if uploadFlag:
            upload_activityID_list.append(ma.activityId)

    for id in upload_activityID_list:
        upload_activity_task = asyncio.ensure_future(upload_activity(main_client, sync_client, id))
        loop.run_until_complete(upload_activity_task)
   
    ## 如果配置了WEBDAV
    if LOCAL_OR_WEBDAV:
        jianguoyun_client.upload_file_db(os.path.join(DB_DIR, db_name), JIAN_GOU_YUN_WEBDAV_PATH + '/' + JIAN_GOU_YUN_WEBDAV_DB_DIR + '/' + db_name)
    
    
    end = time.time()
    print('同步程序执行时间: ', end - start)