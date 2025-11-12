"""
Models - 資料模型層
定義共乘活動的資料結構和業務邏輯
"""
from dataclasses import dataclass
from typing import List, Optional
#  因為json讀取google sheet的時間格式會錯誤，因此引入函數做矯正
import datetime
from datetime import datetime as datetime_datetime

@dataclass
class User:
    """使用者模型"""
    user_id: str
    name: str
    
    def __str__(self):
        return self.name


@dataclass
class Activity:
    """共乘活動基礎模型"""
    index: int  # 在試算表中的索引
    timestamp: str
    email: str
    departure: str
    time: str
    destination: str
    limit: str
    duration: int
    rules: str
    description: str
    organizer_name: str
    organizer_line_id: str
    organizer_phone: str
    carpool_id: str
    notified: bool

    def transform_timestamp_datetime(self) -> datetime:
    # 解析含中文上午/下午的時間字符串為 datetime 對象
        parts = self.timestamp.split()
        date_part = parts[0]
        ampm = parts[1]
        time_part = parts[2]
        # 轉換中文上午/下午為 AM/PM
        ampm_en = "AM" if ampm == "上午" else "PM"
        # 合併為可解析的字符串
        datetime_str = f"{date_part} {time_part} {ampm_en}"
        return datetime_datetime.strptime(datetime_str, "%Y/%m/%d %I:%M:%S %p")
    
    def transform_time_datetime(self):
    # 解析含中文上午/下午的時間字符串為 datetime 對象
        parts = self.time.split()
        date_part = parts[0]
        ampm = parts[1]
        time_part = parts[2]
        # 轉換中文上午/下午為 AM/PM
        ampm_en = "AM" if ampm == "上午" else "PM"
        # 合併為可解析的字符串
        datetime_str = f"{date_part} {time_part} {ampm_en}"
        return datetime_datetime.strptime(datetime_str, "%Y/%m/%d %I:%M:%S %p")    
    
    def is_notified(self) -> bool:
        """檢查是否已通知"""
        return self.notified
    
    # 換算總時程函數
    def format_time_duration(self) -> str:
        """格式化時間長度"""
        hours = int(self.duration / 60)
        minutes = int(self.duration % 60)
        
        if hours == 0:
            return f'{minutes}分鐘'
        elif minutes == 0:
            return f'{hours}小時'
        else:
            return f'{hours}小時{minutes}分鐘'
        
    def isOutDate(self) -> bool:
        driver_case_date = self.transform_time_datetime().replace(hour=0, minute=0, second=0, microsecond=0)
        now_date = (datetime_datetime.now() + datetime.timedelta(hours = 8)).replace(hour=0, minute=0, second=0, microsecond=0)
        return driver_case_date < now_date 
    
    def isNowPost(self) -> bool:
        driver_case_launchdate = self.transform_timestamp_datetime().replace(hour=0, minute=0, second=0, microsecond=0)
        now_date = (datetime_datetime.now() + datetime.timedelta(hours = 8)).replace(hour=0, minute=0, second=0, microsecond=0)
        return driver_case_launchdate == now_date


@dataclass
class DriverActivity(Activity):
    """司機揪團活動模型"""
    cost: str
    vehicle: str
    passengers: List[User]
    
    def get_passenger_count(self) -> int:
        """取得目前乘客人數"""
        return len(self.passengers)
    
    def passenger_isfull(self) -> bool:
        """檢查是否已滿"""
        return self.get_passenger_count() == self.limit
    
    def is_user_passenger(self, user_id: str) -> bool:
        """檢查使用者是否為乘客"""
        return any(p.user_id == user_id for p in self.passengers)
    
    def can_add_passenger(self) -> bool:
        """檢查是否可以新增乘客"""
        return not self.passenger_isfull()
    

@dataclass
class PassengerActivity(Activity):
    """乘客揪團活動模型"""
    vehicle: str
    passengers: List[User]
    driver: Optional[User]
    
    def get_passenger_count(self) -> int:
        """取得目前乘客人數"""
        return len(self.passengers)
    
    def passenger_isfull(self) -> bool:
        """檢查是否已滿"""
        return self.get_passenger_count() == self.limit
    
    def has_driver_return_name(self) -> str:
        """檢查是否有司機"""
        if self.driver != None:
            return self.driver.name 
        else:
            return '無'
    
    def is_user_passenger(self, user_id: str) -> bool:
        """檢查使用者是否為乘客"""
        return any(p.user_id == user_id for p in self.passengers)
    
    def is_user_driver(self, user_id: str) -> bool:
        """檢查使用者是否為司機"""
        return self.driver and self.driver.user_id == user_id
    
    def can_add_passenger(self) -> bool:
        """檢查是否可以新增乘客"""
        return not self.passenger_isfull()
    
    def can_add_driver(self) -> bool:
        """檢查是否可以新增司機"""
        return not self.driver_isfull
    
    def can_add_driver(self) -> bool:
        """檢查是否可以新增司機"""
        return self.has_driver_return_name()


class ActivityFactory:
    """活動工廠類別 - 負責從原始資料創建活動物件"""
    
    @staticmethod
    def create_driver_activity(row: List[str], index: int) -> DriverActivity:
        """從試算表列創建司機活動物件"""
        from config import DriverColumns
        
        # 解析乘客列表
        passengers = []
        if row[DriverColumns.PASSENGER_IDS]:
            ids = row[DriverColumns.PASSENGER_IDS].split(',')
            names = row[DriverColumns.PASSENGER_NAMES].split(',')
            passengers = [User(user_id=uid, name=name) for uid, name in zip(ids, names)]
        
        return DriverActivity(
            index=index,
            timestamp=row[DriverColumns.TIMESTAMP],
            email=row[DriverColumns.EMAIL],
            departure=row[DriverColumns.DEPARTURE],
            time=row[DriverColumns.TIME],
            destination=row[DriverColumns.DESTINATION],
            limit=row[DriverColumns.LIMIT],
            duration=int(row[DriverColumns.DURATION]) if row[DriverColumns.DURATION] else 0,
            rules=row[DriverColumns.RULES],
            description=row[DriverColumns.DESCRIPTION],
            organizer_name=row[DriverColumns.NAME],
            organizer_line_id=row[DriverColumns.LINE_ID],
            organizer_phone=row[DriverColumns.PHONE],
            cost=row[DriverColumns.COST],
            vehicle=row[DriverColumns.VEHICLE],
            carpool_id=row[DriverColumns.CARPOOL_ID],
            notified=row[DriverColumns.NOTIFIED] == '是',
            passengers=passengers,
        )
    
    @staticmethod
    def create_passenger_activity(row: List[str], index: int) -> PassengerActivity:
        """從試算表列創建乘客活動物件"""
        from config import PassengerColumns
        
        # 解析乘客列表
        passengers = []
        if row[PassengerColumns.PASSENGER_IDS]:
            ids = row[PassengerColumns.PASSENGER_IDS].split(',')
            names = row[PassengerColumns.PASSENGER_NAMES].split(',')
            passengers = [User(user_id=uid, name=name) for uid, name in zip(ids, names)]
        
        # 解析司機
        driver = None
        if row[PassengerColumns.DRIVER_ID]:
            driver = User(
                user_id=row[PassengerColumns.DRIVER_ID],
                name=row[PassengerColumns.DRIVER_NAME]
            )
        
        return PassengerActivity(
            index=index,
            timestamp=row[PassengerColumns.TIMESTAMP],
            email=row[PassengerColumns.EMAIL],
            departure=row[PassengerColumns.DEPARTURE],
            time=row[PassengerColumns.TIME],
            destination=row[PassengerColumns.DESTINATION],
            limit=row[PassengerColumns.LIMIT],
            duration=int(row[PassengerColumns.DURATION]) if row[PassengerColumns.DURATION] else 0,
            rules=row[PassengerColumns.RULES],
            description=row[PassengerColumns.DESCRIPTION],
            organizer_name=row[PassengerColumns.NAME],
            organizer_line_id=row[PassengerColumns.LINE_ID],
            organizer_phone=row[PassengerColumns.PHONE],
            vehicle=row[PassengerColumns.VEHICLE],
            carpool_id=row[PassengerColumns.CARPOOL_ID],
            notified=row[PassengerColumns.NOTIFIED] == '是',
            passengers=passengers,
            driver=driver
        )
