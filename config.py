"""
配置文件 - 集中管理常數和環境變數
"""
import os
import json
from dotenv import(
    load_dotenv,
    find_dotenv
)

# 載入環境變數 (find_dotenv函數可以由根目錄網上尋找 .env 檔案)
load_dotenv(dotenv_path=find_dotenv())

# LINE Bot 設定
CHANNEL_ACCESS_TOKEN = os.getenv('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.getenv('CHANNEL_SECRET')

# Google Sheet 設定
GOOGLE_CREDENTIALS = os.getenv('GOOGLE_CREDENTIALS')
SHEET_URL = os.getenv('GOOGLESHEET_URL')

# Email 設定
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_USER = os.getenv('SMTP_USER')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')

# Redis 設定
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = os.getenv('REDIS_PORT')
REDIS_PASSWORD = os.getenv('dREDIS_PASSWORD')

# 時間設定
NOTIFICATION_HOURS_BEFORE = 3  # 提前幾小時通知
CHECK_INTERVAL_SECONDS = 30  # 檢查間隔（秒）

def get_credentials_dict():
    """取得 Google Credentials 字典"""
    credentials_str = GOOGLE_CREDENTIALS
    if credentials_str:
        return json.loads(credentials_str)
    return None

# Google Sheet 欄位索引
class DriverColumns:
    """司機表單欄位索引"""
    TIMESTAMP = 0
    EMAIL = 1
    DEPARTURE = 2
    TIME = 3
    DESTINATION = 4
    LIMIT = 5
    DURATION = 6
    RULES = 7
    DESCRIPTION = 8
    NAME = 9
    LINE_ID = 10
    COST = 11
    VEHICLE = 12
    PHONE = 13
    PASSENGER_COUNT = 14
    PASSENGER_IDS = 15
    PASSENGER_NAMES = 16
    CARPOOL_ID = 17
    DRIVER_NAMES = 18
    NOTIFIED = 19

class PassengerColumns:
    """乘客表單欄位索引"""
    TIMESTAMP = 0
    EMAIL = 1
    DEPARTURE = 2
    TIME = 3
    DESTINATION = 4
    LIMIT = 5
    DURATION = 6
    RULES = 7
    DESCRIPTION = 8
    NAME = 9
    LINE_ID = 10
    VEHICLE = 11
    PHONE = 12
    PASSENGER_COUNT = 13
    PASSENGER_IDS = 14
    PASSENGER_NAMES = 15
    CARPOOL_ID = 16
    PASSENGERS_BACKUP = 17
    DRIVER_NAME = 18
    DRIVER_ID = 19
    NOTIFIED = 20
