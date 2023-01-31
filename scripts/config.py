import os

SYS_CONFIG = {
    'LOCAL_OR_WEBDAV' : ''
}

# 首先读取 面板变量 或者 github action 运行变量
for k in SYS_CONFIG:
    if os.getenv(k):
        v = os.getenv(k)
        SYS_CONFIG[k] = v

# getting content root directory
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)

## LOCAL 配置
LOCAL_DB_DIR = os.path.join(parent, "db")
OUTPUT_DIR = os.path.join(parent, "activities")
GPX_FOLDER = os.path.join(parent, "GPX_OUT")
TCX_FOLDER = os.path.join(parent, "TCX_OUT")
FIT_FOLDER = os.path.join(parent, "FIT_OUT")
FIT_UNZIP_FOLDER = os.path.join(parent, "FIT_UNZIP_OUT")
ENDOMONDO_FILE_DIR = os.path.join(parent, "Workouts")

FOLDER_DICT = {
    "gpx": GPX_FOLDER,
    "tcx": TCX_FOLDER,
    "fit": FIT_FOLDER,
    "fit_unzip": FIT_UNZIP_FOLDER,
}

## WEBDAV 配置
DB_WEBDAV_DIR = os.path.join(parent, "webdav-db")
FIT_WEBDAV_DIR = os.path.join(parent, "webdav-fit")

JIAN_GOU_YUN_WEBDAV_PATH = "/sport-sync"
JIAN_GOU_YUN_WEBDAV_FIT_FOLDER = "FIT_OUT"
JIAN_GOU_YUN_WEBDAV_FIT_UNZIP_FOLDER = "FIT_UNZIP_OUT"
JIAN_GOU_YUN_WEBDAV_DB_DIR = 'db'

LOCAL_OR_WEBDAV = True if SYS_CONFIG['LOCAL_OR_WEBDAV'] == "True" else False
DB_DIR =  DB_WEBDAV_DIR if LOCAL_OR_WEBDAV else LOCAL_DB_DIR
FIT_DIR = FIT_WEBDAV_DIR if LOCAL_OR_WEBDAV else FIT_FOLDER