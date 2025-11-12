"""
Controllers - 預約控制器
負責處理預約和取消預約的業務邏輯
"""
from typing import Tuple, Optional
from models.repository import repository
from models.activity_model import User
from views.line_view import line_view


class ReservationController:
    """預約控制器 - 處理預約相關業務邏輯"""
    
    def __init__(self):
        self.repository = repository
    
    # ==================== 司機活動預約 ====================
    
    def reserve_driver_as_passenger(self, index: int, user: User) -> Tuple[bool, str]:
        """
        預約司機活動（乘客身份）
        
        返回: (success, message, activity)
        """
        # 刷新資料
        self.repository.refresh_driver_activities(force = True)
        
        # 取得活動
        activity = self.repository.get_driver_activity_by_index(index)
        if not activity:
            return False, line_view.ERROR_ACTIVITY_NOT_FOUND
        
        # 檢查是否已經是乘客
        if activity.is_user_passenger(user.user_id):
            return False, line_view.ERROR_ALREADY_RESERVED_AS_PASSENGER
        
        # 檢查是否已滿
        if not activity.can_add_passenger():
            return False, line_view.ERROR_ACTIVITY_FULL
        
        # 執行預約
        success = self.repository.add_passenger_to_driver_activity(index, user)
        
        if success:
            message = line_view.format_reservation_success(activity, '乘客')
            return True, message
        else:
            return False, line_view.ERROR_LOADING_FAILED
    
    def cancel_driver_reservation(self, index: int, user_id: str) -> Tuple[bool, str]:
        """
        取消司機活動預約(乘客身分)
        
        返回: (success, message)
        """
        # 刷新資料
        self.repository.refresh_driver_activities(force = True)
        
        # 取得活動
        activity = self.repository.get_driver_activity_by_index(index)
        if not activity:
            return False, line_view.ERROR_ACTIVITY_NOT_FOUND
        
        # 檢查使用者預約狀態
        is_passenger = activity.is_user_passenger(user_id)
        
        if not is_passenger:
            return False, line_view.ERROR_NOT_RESERVED
        else:
            success = self.repository.remove_passenger_from_driver_activity(index, user_id)
            role = '乘客'
        
        if success:
            message = line_view.format_cancellation_success(activity.carpool_id, role)
            return True, message
        else:
            return False, line_view.ERROR_LOADING_FAILED
    
    # ==================== 乘客活動預約 ====================
    
    def reserve_passenger_as_passenger(self, index: int, user: User) -> Tuple[bool, str]:
        """
        預約乘客活動（乘客身份）
        
        返回: (success, message, activity)
        """
        # 刷新資料
        self.repository.refresh_passenger_activities(force = True)
        
        # 取得活動
        activity = self.repository.get_passenger_activity_by_index(index)
        if not activity:
            return False, line_view.ERROR_ACTIVITY_NOT_FOUND
        
        # 檢查是否已經是司機
        if activity.is_user_driver(user.user_id):
            return False, line_view.ERROR_ALREADY_RESERVED_AS_DRIVER
        
        # 檢查是否已經是乘客
        if activity.is_user_passenger(user.user_id):
            return False, line_view.ERROR_ALREADY_RESERVED_AS_PASSENGER
        
        # 檢查是否已滿
        if not activity.can_add_passenger():
            return False, line_view.ERROR_ACTIVITY_FULL
        
        # 執行預約
        success = self.repository.add_passenger_to_passenger_activity(index, user)
        
        if success:
            driver_info = f'\n司機名稱：{activity.driver.name}' if activity.driver else ''
            message = line_view.format_reservation_success(activity, '乘客') + driver_info
            return True, message
        else:
            return False, line_view.ERROR_LOADING_FAILED
    
    def reserve_passenger_as_driver(self, index: int, user: User) -> Tuple[bool, str, Optional[object]]:
        """
        預約乘客活動（司機身份）
        
        返回: (success, message, activity)
        """
        # 刷新資料
        self.repository.refresh_passenger_activities(force = True)
        
        # 取得活動
        activity = self.repository.get_passenger_activity_by_index(index)
        if not activity:
            return False, line_view.ERROR_ACTIVITY_NOT_FOUND
        
        # 檢查是否已經是乘客
        if activity.is_user_passenger(user.user_id):
            return False, line_view.ERROR_ALREADY_RESERVED_AS_PASSENGER
        
        # 檢查是否已有司機
        if activity.can_add_driver() != '無':
            return False, line_view.ERROR_DRIVER_POSITION_TAKEN
        
        # 執行預約
        success = self.repository.add_driver_to_passenger_activity(index, user)
        
        if success:
            message = line_view.format_reservation_success(activity, '司機')
            return True, message
        else:
            return False, line_view.ERROR_LOADING_FAILED
    
    def cancel_passenger_reservation(self, index: int, user_id: str) -> Tuple[bool, str]:
        """
        取消乘客活動預約
        
        返回: (success, message)
        """
        # 刷新資料
        self.repository.refresh_passenger_activities(force = True)
        
        # 取得活動
        activity = self.repository.get_passenger_activity_by_index(index)
        if not activity:
            return False, line_view.ERROR_ACTIVITY_NOT_FOUND
        
        # 檢查使用者預約狀態
        is_passenger = activity.is_user_passenger(user_id)
        is_driver = activity.is_user_driver(user_id)
        
        if not is_passenger and not is_driver:
            return False, line_view.ERROR_NOT_RESERVED
        
        # 執行取消
        if is_passenger:
            success = self.repository.remove_passenger_from_passenger_activity(index, user_id)
            role = '乘客'
        else:  # is_driver
            success = self.repository.remove_driver_from_passenger_activity(index)
            role = '司機'
        
        if success:
            message = line_view.format_cancellation_success(activity.carpool_id, role)
            return True, message
        else:
            return False, line_view.ERROR_LOADING_FAILED


# 全局單例
reservation_controller = ReservationController()
