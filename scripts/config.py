import os


# getting content root directory
current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)

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

DB_DIR = os.path.join(parent, "db")
DB_WEBDAV_DIR = os.path.join(parent, "webdav-db")
FIT_WEBDAV_DIR = os.path.join(parent, "webdav-fit")

JIAN_GOU_YUN_WEBDAV_PATH = "/sport-sync"
JIAN_GOU_YUN_WEBDAV_FIT_FOLDER = "FIT_OUT"
JIAN_GOU_YUN_WEBDAV_FIT_UNZIP_FOLDER = "FIT_UNZIP_OUT"
JIAN_GOU_YUN_WEBDAV_DB_DIR = 'db'
