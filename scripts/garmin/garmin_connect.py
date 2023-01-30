import argparse
import asyncio
import email
import logging
import os
import re
import traceback
import json
import copy
import cloudscraper
import httpx
import sys 
CURRENT_DIR = os.path.split(os.path.abspath(__file__))[0]  # 当前目录
config_path = CURRENT_DIR.rsplit('/', 1)[0]  # 上三级目录
sys.path.append(config_path)

import notify
from entity.activity import Activity

logger = logging.getLogger(__name__)

TIME_OUT = httpx.Timeout(240.0, connect=360.0)
GARMIN_COM_URL_DICT = {
    "BASE_URL": "https://connect.garmin.com",
    "SSO_URL_ORIGIN": "https://sso.garmin.com",
    "SSO_URL": "https://sso.garmin.com/sso",
    # "MODERN_URL": "https://connect.garmin.com/modern",
    "MODERN_URL": "https://connect.garmin.com",
    "SIGNIN_URL": "https://sso.garmin.com/sso/signin",
    "CSS_URL": "https://static.garmincdn.com/com.garmin.connect/ui/css/gauth-custom-v1.2-min.css",
    "UPLOAD_URL": "https://connect.garmin.com/modern/proxy/upload-service/upload/.gpx",
    "ACTIVITY_URL": "https://connect.garmin.com/proxy/activity-service/activity/{activity_id}",
}

GARMIN_CN_URL_DICT = {
    "BASE_URL": "https://connect.garmin.cn",
    "SSO_URL_ORIGIN": "https://sso.garmin.com",
    "SSO_URL": "https://sso.garmin.cn/sso",
    # "MODERN_URL": "https://connect.garmin.cn/modern",
    "MODERN_URL": "https://connect.garmin.cn",
    "SIGNIN_URL": "https://sso.garmin.cn/sso/signin",
    "CSS_URL": "https://static.garmincdn.cn/cn.garmin.connect/ui/css/gauth-custom-v1.2-min.css",
    "UPLOAD_URL": "https://connect.garmin.cn/modern/proxy/upload-service/upload/.gpx",
    "ACTIVITY_URL": "https://connect.garmin.cn/proxy/activity-service/activity/{activity_id}",
}

ACTIVITY_DICT = {}

class GarminConnect:
    def __init__(self, email, password, auth_domain, is_only_running=False):
        """
        Init module
        """
        self.auth_domain = auth_domain
        self.email = email
        self.password = password
        self.req = httpx.AsyncClient(timeout=TIME_OUT)
        self.cf_req = cloudscraper.CloudScraper()
        self.URL_DICT = (
            GARMIN_CN_URL_DICT
            if auth_domain and str(auth_domain).upper() == "CN"
            else GARMIN_COM_URL_DICT
        )
        self.modern_url = self.URL_DICT.get("MODERN_URL")

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36",
            "origin": self.URL_DICT.get("SSO_URL_ORIGIN"),
            "nk": "NT",
        }
        self.is_only_running = is_only_running
        self.upload_url = self.URL_DICT.get("UPLOAD_URL")
        self.activity_url = self.URL_DICT.get("ACTIVITY_URL")
        self.is_login = False

    def login(self):
        """
        Login to portal
        """
        params = {
            "webhost": self.URL_DICT.get("BASE_URL"),
            "service": self.modern_url,
            "source": self.URL_DICT.get("SIGNIN_URL"),
            "redirectAfterAccountLoginUrl": self.modern_url,
            "redirectAfterAccountCreationUrl": self.modern_url,
            "gauthHost": self.URL_DICT.get("SSO_URL"),
            "locale": "en_US",
            "id": "gauth-widget",
            "cssUrl": self.URL_DICT.get("CSS_URL"),
            "clientId": "GarminConnect",
            "rememberMeShown": "true",
            "rememberMeChecked": "false",
            "createAccountShown": "true",
            "openCreateAccount": "false",
            "usernameShown": "false",
            "displayNameShown": "false",
            "consumeServiceTicket": "false",
            "initialFocus": "true",
            "embedWidget": "false",
            "generateExtraServiceTicket": "false",
        }

        data = {
            "username": self.email,
            "password": self.password,
            "embed": "true",
            "lt": "e1s1",
            "_eventId": "submit",
            "displayNameRequired": "false",
        }

        try:
            self.cf_req.get(
                self.URL_DICT.get("SIGNIN_URL"), headers=self.headers, params=params
            )
            response = self.cf_req.post(
                self.URL_DICT.get("SIGNIN_URL"),
                headers=self.headers,
                params=params,
                data=data,
            )
        except Exception as err:
            pass
        response_url = re.search(r'"(https:[^"]+?ticket=[^"]+)"', response.text)

        if not response_url:
            pass

        response_url = re.sub(r"\\", "", response_url.group(1))
        try:
            response = self.cf_req.get(response_url)
            self.req.cookies = self.cf_req.cookies
            if response.status_code == 200:
                self.is_login = True
            response.raise_for_status()
        except Exception as err:
            pass
    
    async def get_activitys(self, limit, start):
        if not self.is_login:
            self.login()
        url = f"{self.modern_url}/proxy/activitylist-service/activities/search/activities?start={start}&limit={limit}"
        return await self.featch_get_request_data(url)

    async def featch_get_request_data(self, url):
        try:
            response = await self.req.get(
            url,
            headers=self.headers
        )
            if response.status_code == 429:
                print("429")
            logger.debug(f"fetch_data got response code {response.status_code}")
            response.raise_for_status()
            return response.json()
        except Exception as err:
            raise err

    async def download_activity_fit(self, activity_id):
        url = f"{self.modern_url}/proxy/download-service/files/activity/{activity_id}"
        logger.info(f"Download activity from {url}")
        response = await self.req.get(url, headers=self.headers)
        response.raise_for_status()
        return response.read()

    async def delete_activity(self, activity_id):
        try:
            if  self.auth_domain == 'cn':
                if not self.is_login:
                    self.login()
                url = f"{self.modern_url}/proxy/activity-service/activity/{activity_id}"
                delete_headers = copy.deepcopy(self.headers)
                delete_headers["x-http-method-override"] = "DELETE"
                delete_headers["x-requested-with"] = "XMLHttpRequest"
                response = await self.req.delete(
                    url,
                    headers=delete_headers
                )
                if response.status_code == 204:
                    print(f"success delete activity, id is {activity_id}")
        except Exception as err:
            raise err

    async def upload_activity(self, file_path, file_type, activity_id):
        activity = ACTIVITY_DICT[activity_id]
        activityName = activity.activityName
        activityType = activity.activityType
        startTimeLocal = activity.startTimeLocal
        calories = activity.calories if activity.calories != None else 0 
        averageHR = activity.averageHR if activity.averageHR != None else 0 
        titile = "同步佳明活动\n同步帐号: %s\n同步区域: %s" % (self.email, self.auth_domain)
        if not self.is_login:
            self.login()
        upload_url = f"{self.modern_url}/proxy/upload-service/upload/{file_type}"
        files = {"data": (f"file{file_type}", open(file_path, 'rb'))}
        
        try:
            res = await self.req.post(
                upload_url, files=files, headers={"nk": "NT"}
            )
            result_json = json.loads(res.text)
            if res.status_code == 201:
                message =  "成功上传运动数据\n运动数据ID为：%s\n运动数据名称为：%s\n运动数据类型为：%s\n运动开始时间：%s\n运动平均心率为:%d\n运动卡路里为:%d\n" % (str(activity_id), activityName,activityType,startTimeLocal,averageHR,calories)      
                notify.send(titile,message)
            elif res.status_code == 409 and result_json.get("detailedImportResult").get("failures")[0].get('messages')[0].get('content'):    
                message =  "重复上传运动数据\n运动数据ID为：%s\n运动数据名称为：%s\n运动数据类型为：%s\n运动开始时间：%s" % (str(activity_id), activityName,activityType,startTimeLocal)      
                notify.send(titile,message)
        except Exception as e:
            raise GarminUploadError("upload activity error ") from e
    
    async def test_login(self):
        try:
            isLogin = False
            response = await self.req.get(
            f"{self.modern_url}/proxy/activitylist-service/activities/search/activities?start=0&limit=10",
            headers=self.headers
        )
            if response.status_code == 200:
                isLogin = True
            else:
                self.is_login = False
        except Exception as err:
            self.is_login = False
            raise err
        finally:
            return isLogin

    async def get_all_activity_list(self, start):
        respone = await self.get_activitys(100, start)
        if len(respone) > 0:
            activity_list = []
            for result in respone:
                activity = Activity(result.get("activityId"), result.get("activityName"),
                                    result.get("activityType").get('typeKey'),
                                    result.get("startTimeLocal"),
                                    result.get("calories"),
                                    result.get("averageHR"))
                ACTIVITY_DICT[result.get("activityId")] = activity
                activity_list.append(activity)
            return activity_list + await self.get_all_activity_list(start + 100)
        else:
            return []
        
class GarminUploadError(Exception):
    """Raised when communication ended in error."""

    def __init__(self, status):
        """Initialize."""
        super(GarminUploadError, self).__init__(status)
        self.status = status


