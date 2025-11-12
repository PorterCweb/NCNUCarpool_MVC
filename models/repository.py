"""
Repository - 資料存取層（改進版：加入智能快取）
負責與資料來源（Google Sheets）互動，提供 CRUD 操作
"""
import gspread
from typing import List, Optional
from datetime import datetime, timedelta
from tenacity import retry, stop_after_attempt, retry_if_exception_type, wait_exponential
from models.activity_model import DriverActivity, PassengerActivity, ActivityFactory, User
from config import get_credentials_dict, SHEET_URL, DriverColumns, PassengerColumns, REDIS_HOST, REDIS_PASSWORD, REDIS_PORT


class ActivityRepository:
    """活動資料存取層 - 實現 Repository Pattern + 智能快取"""
    
    def __init__(self):
        credentials_dict = get_credentials_dict()
        self.gc = gspread.service_account_from_dict(credentials_dict)
        self.carpool = self.gc.open_by_url(SHEET_URL)
        self.driver_sheet = self.carpool.get_worksheet(0)
        self.passenger_sheet = self.carpool.get_worksheet(1)
        
        # 快取資料
        self._driver_data_cache = []
        self._passenger_data_cache = []
        
        # 快取管理（新增）
        self._driver_cache_time = None
        self._passenger_cache_time = None
        self._cache_ttl = 60  # 快取有效期：60 秒
    
    # ==================== 快取管理（新增）====================
    
    def set_cache_ttl(self, seconds: int):
        """設定快取有效期（秒）"""
        self._cache_ttl = seconds
    
    def clear_cache(self):
        """清除所有快取"""
        self._driver_data_cache = []
        self._passenger_data_cache = []
        self._driver_cache_time = None
        self._passenger_cache_time = None
        print("✓ 快取已清除")
    
    # ==================== 司機活動相關 ====================
    
    def refresh_driver_activities(self, force: bool = False) -> List[List[str]]:
        """
        重新載入司機表單資料（智能快取）
        
        Args:
            force: 是否強制刷新
                  - True: 立即從 Google Sheets 讀取
                  - False: 如果快取有效則使用快取
        
        Returns:
            試算表資料列表
        """
        # 強制刷新：直接讀取
        if force:
            print("🔄 強制刷新：從 Google Sheets 讀取司機活動")
            return self._fetch_driver_data_from_sheets()
        
        # 檢查快取是否還有效
        if self._is_driver_cache_valid():
            elapsed = (datetime.now() - self._driver_cache_time).total_seconds()
            print(f"✓ 使用快取：司機活動（{elapsed:.1f} 秒前更新）")
            return self._driver_data_cache
        
        # 快取過期：讀取新資料
        print("🔄 快取過期：從 Google Sheets 讀取司機活動")
        return self._fetch_driver_data_from_sheets()
    
    def _is_driver_cache_valid(self) -> bool:
        """檢查司機活動快取是否還有效"""
        # 沒有快取時間記錄
        if not self._driver_cache_time:
            return False
        
        # 快取資料為空
        if not self._driver_data_cache:
            return False
        
        # 檢查是否過期
        elapsed = (datetime.now() - self._driver_cache_time).total_seconds()
        return elapsed < self._cache_ttl
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(gspread.exceptions.APIError)
    )
    def _fetch_driver_data_from_sheets(self) -> List[List[str]]:
        """從 Google Sheets 讀取司機資料（內部方法）"""
        self._driver_data_cache = self.driver_sheet.get_all_values()
        self._driver_cache_time = datetime.now()
        return self._driver_data_cache
    
    def get_all_driver_activities(self) -> List[DriverActivity]:
        """取得所有司機活動"""
        data = self._driver_data_cache
        activities = []
        
        # 跳過標題列
        for i, row in enumerate(data[1:], start=1):
            if len(row) >= 21:
                activity = ActivityFactory.create_driver_activity(row, i)
                activities.append(activity)
        
        return activities
    
    def get_driver_activity_by_index(self, index: int) -> Optional[DriverActivity]:
        """根據索引取得司機活動"""
        data = self._driver_data_cache
        if 0 < index < len(data):
            return ActivityFactory.create_driver_activity(data[index], index)
        return None
    
    def find_DriverActivities_ByUser_AsPassenger(self, user_id: str) -> List[DriverActivity]:
        """查詢使用者參與的司機活動"""
        activities = self.get_all_driver_activities()
        return [
            activity for activity in activities
            if activity.is_user_passenger(user_id)
        ]
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(gspread.exceptions.APIError)
    )
    def add_passenger_to_driver_activity(self, index: int, user: User) -> bool:
        """新增乘客到司機活動"""
        try:
            activity = self.get_driver_activity_by_index(index)
            if not activity or not activity.can_add_passenger():
                return False
            
            # 準備新資料
            new_count = activity.get_passenger_count() + 1
            
            # 組合 ID 和名稱
            ids = [p.user_id for p in activity.passengers] + [user.user_id]
            names = [p.name for p in activity.passengers] + [user.name]
            
            new_ids = ','.join(ids)
            new_names = ','.join(names)
            
            # 更新試算表
            range_str = f'O{index + 1}:Q{index + 1}'
            self.driver_sheet.update([[new_count, new_ids, new_names]], range_str)
            
            # 同步更新快取（新增）
            if index < len(self._driver_data_cache):
                self._driver_data_cache[index][DriverColumns.PASSENGER_COUNT] = str(new_count)
                self._driver_data_cache[index][DriverColumns.PASSENGER_IDS] = new_ids
                self._driver_data_cache[index][DriverColumns.PASSENGER_NAMES] = new_names
                print("✓ 快取已同步更新：新增乘客")
            
            return True
        except Exception as e:
            print(f"新增乘客失敗: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(gspread.exceptions.APIError)
    )
    def remove_passenger_from_driver_activity(self, index: int, user_id: str) -> bool:
        """從司機活動移除乘客"""
        try:
            activity = self.get_driver_activity_by_index(index)
            if not activity or not activity.is_user_passenger(user_id):
                return False
            
            # 過濾掉要移除的使用者
            remaining_passengers = [p for p in activity.passengers if p.user_id != user_id]
            
            new_count = len(remaining_passengers)
            new_ids = ','.join([p.user_id for p in remaining_passengers])
            new_names = ','.join([p.name for p in remaining_passengers])
            
            # 更新試算表
            range_str = f'O{index + 1}:Q{index + 1}'
            self.driver_sheet.update([[new_count, new_ids, new_names]], range_str)
            
            # 同步更新快取（新增）
            if index < len(self._driver_data_cache):
                self._driver_data_cache[index][DriverColumns.PASSENGER_COUNT] = str(new_count)
                self._driver_data_cache[index][DriverColumns.PASSENGER_IDS] = new_ids
                self._driver_data_cache[index][DriverColumns.PASSENGER_NAMES] = new_names
                print("✓ 快取已同步更新：移除乘客")
            
            return True
        except Exception as e:
            print(f"移除乘客失敗: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(gspread.exceptions.APIError)
    )
    def mark_driver_activity_notified(self, index: int) -> bool:
        """標記司機活動已通知"""
        try:
            cell = f'T{index + 1}'
            self.driver_sheet.update([['是']], cell)
            
            # 同步更新快取（新增）
            if index < len(self._driver_data_cache):
                self._driver_data_cache[index][DriverColumns.NOTIFIED] = '是'
                print("✓ 快取已同步更新：標記已通知")
            
            return True
        except Exception as e:
            print(f"更新通知狀態失敗: {e}")
            return False
    
    # ==================== 乘客活動相關 ====================
    
    def refresh_passenger_activities(self, force: bool = False) -> List[List[str]]:
        """
        重新載入乘客表單資料（智能快取）
        
        Args:
            force: 是否強制刷新
        
        Returns:
            試算表資料列表
        """
        if force:
            print("🔄 強制刷新：從 Google Sheets 讀取乘客活動")
            return self._fetch_passenger_data_from_sheets()
        
        if self._is_passenger_cache_valid():
            elapsed = (datetime.now() - self._passenger_cache_time).total_seconds()
            print(f"✓ 使用快取：乘客活動（{elapsed:.1f} 秒前更新）")
            return self._passenger_data_cache
        
        print("🔄 快取過期：從 Google Sheets 讀取乘客活動")
        return self._fetch_passenger_data_from_sheets()
    
    def _is_passenger_cache_valid(self) -> bool:
        """檢查乘客活動快取是否還有效"""
        if not self._passenger_cache_time:
            return False
        
        if not self._passenger_data_cache:
            return False
        
        elapsed = (datetime.now() - self._passenger_cache_time).total_seconds()
        return elapsed < self._cache_ttl
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(gspread.exceptions.APIError)
    )
    def _fetch_passenger_data_from_sheets(self) -> List[List[str]]:
        """從 Google Sheets 讀取乘客資料（內部方法）"""
        self._passenger_data_cache = self.passenger_sheet.get_all_values()
        self._passenger_cache_time = datetime.now()
        return self._passenger_data_cache
    
    def get_all_passenger_activities(self) -> List[PassengerActivity]:
        """取得所有乘客活動"""
        data = self._passenger_data_cache
        activities = []
        
        # 跳過標題列
        for i, row in enumerate(data[1:], start=1):
            if len(row) >= 21:
                activity = ActivityFactory.create_passenger_activity(row, i)
                activities.append(activity)
        
        return activities
    
    def get_passenger_activity_by_index(self, index: int) -> Optional[PassengerActivity]:
        """根據索引取得乘客活動"""
        data = self._passenger_data_cache
        if 0 < index <= len(data):
            return ActivityFactory.create_passenger_activity(data[index], index)
        return None
    
    def find_PassengerActivities_ByUser(self, user_id: str) -> List[DriverActivity]:
        """查詢使用者參與的司機活動"""
        activities = self.get_all_passenger_activities()
        return [
            activity for activity in activities
            if activity.is_user_passenger(user_id) or activity.is_user_driver(user_id)
        ]
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(gspread.exceptions.APIError)
    )
    def add_passenger_to_passenger_activity(self, index: int, user: User) -> bool:
        """新增乘客到乘客活動"""
        try:
            activity = self.get_passenger_activity_by_index(index)
            if not activity or not activity.can_add_passenger():
                return False
            
            # 準備新資料
            new_count = activity.get_passenger_count() + 1
            
            # 組合 ID 和名稱
            ids = [p.user_id for p in activity.passengers] + [user.user_id]
            names = [p.name for p in activity.passengers] + [user.name]
            
            new_ids = ','.join(ids)
            new_names = ','.join(names)
            
            # 更新試算表
            range_str = f'N{index + 1}:P{index + 1}'
            self.passenger_sheet.update([[new_count, new_ids, new_names]], range_str)
            
            # 同步更新快取（新增）
            if index < len(self._passenger_data_cache):
                self._passenger_data_cache[index][PassengerColumns.PASSENGER_COUNT] = str(new_count)
                self._passenger_data_cache[index][PassengerColumns.PASSENGER_IDS] = new_ids
                self._passenger_data_cache[index][PassengerColumns.PASSENGER_NAMES] = new_names
                print("✓ 快取已同步更新：新增乘客")
            
            return True
        except Exception as e:
            print(f"新增乘客失敗: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(gspread.exceptions.APIError)
    )
    def remove_passenger_from_passenger_activity(self, index: int, user_id: str) -> bool:
        """從乘客活動移除乘客"""
        try:
            activity = self.get_passenger_activity_by_index(index)
            if not activity or not activity.is_user_passenger(user_id):
                return False
            
            # 過濾掉要移除的使用者
            remaining_passengers = [p for p in activity.passengers if p.user_id != user_id]
            
            new_count = len(remaining_passengers)
            new_ids = ','.join([p.user_id for p in remaining_passengers])
            new_names = ','.join([p.name for p in remaining_passengers])
            
            # 更新試算表
            range_str = f'N{index + 1}:P{index + 1}'
            self.passenger_sheet.update([[new_count, new_ids, new_names]], range_str)
            
            # 同步更新快取（新增）
            if index < len(self._passenger_data_cache):
                self._passenger_data_cache[index][PassengerColumns.PASSENGER_COUNT] = str(new_count)
                self._passenger_data_cache[index][PassengerColumns.PASSENGER_IDS] = new_ids
                self._passenger_data_cache[index][PassengerColumns.PASSENGER_NAMES] = new_names
                print("✓ 快取已同步更新：移除乘客")
            
            return True
        except Exception as e:
            print(f"移除乘客失敗: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(gspread.exceptions.APIError)
    )
    def add_driver_to_passenger_activity(self, index: int, user: User) -> bool:
        """新增司機到乘客活動"""
        try:
            activity = self.get_passenger_activity_by_index(index)
            if not activity or not activity.can_add_driver():
                return False
            
            # 更新試算表
            range_str = f'S{index + 1}:T{index + 1}'
            self.passenger_sheet.update([[user.name, user.user_id]], range_str)
            
            # 同步更新快取（新增）
            if index < len(self._passenger_data_cache):
                self._passenger_data_cache[index][PassengerColumns.DRIVER_NAME] = user.name
                self._passenger_data_cache[index][PassengerColumns.DRIVER_ID] = user.user_id
                print("✓ 快取已同步更新：新增司機")
            
            return True
        except Exception as e:
            print(f"新增司機失敗: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(gspread.exceptions.APIError)
    )
    def remove_driver_from_passenger_activity(self, index: int) -> bool:
        """從乘客活動移除司機"""
        try:
            range_str = f'S{index + 1}:T{index + 1}'
            self.passenger_sheet.update([['', '']], range_str)
            
            # 同步更新快取（新增）
            if index < len(self._passenger_data_cache):
                self._passenger_data_cache[index][PassengerColumns.DRIVER_NAME] = ''
                self._passenger_data_cache[index][PassengerColumns.DRIVER_ID] = ''
                print("✓ 快取已同步更新：移除司機")
            
            return True
        except Exception as e:
            print(f"移除司機失敗: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=1, min=4, max=60),
        retry=retry_if_exception_type(gspread.exceptions.APIError)
    )
    def mark_passenger_activity_notified(self, index: int) -> bool:
        """標記乘客活動已通知"""
        try:
            cell = f'U{index + 1}'
            self.passenger_sheet.update([['是']], cell)
            
            # 同步更新快取（新增）
            if index < len(self._passenger_data_cache):
                self._passenger_data_cache[index][PassengerColumns.NOTIFIED] = '是'
                print("✓ 快取已同步更新：標記已通知")
            
            return True
        except Exception as e:
            print(f"更新通知狀態失敗: {e}")
            return False


# 全局單例
repository = ActivityRepository()