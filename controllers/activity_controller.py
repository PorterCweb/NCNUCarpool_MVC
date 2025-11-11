"""
Controllers - 活動控制器
負責處理活動查詢相關的業務邏輯
"""
from typing import List, Optional
from models.repository import repository
from models.activity_model import DriverActivity, PassengerActivity
from views.line_view import line_view
import json

class ActivityController:
    """活動控制器 - 處理活動查詢邏輯"""
    
    def __init__(self):
        self.repository = repository
    
    # ==================== 司機活動相關 ====================
    
    def get_all_driver_activities(self) -> List[DriverActivity]:
        """取得所有司機活動"""
        self.repository.refresh_driver_activities()
        return self.repository.get_all_driver_activities()
    
    def get_driver_activity(self, index: int) -> Optional[DriverActivity]:
        """取得特定司機活動"""
        return self.repository.get_driver_activity_by_index(index)
    
    def find_user_driver_activities(self, user_id: str) -> List[DriverActivity]:
        """查詢使用者參與的司機活動"""
        return self.repository.find_driver_activities_by_user(user_id)
    
    def format_driver_activities_carousel(self, activities: List[DriverActivity]):
        """格式化司機活動輪播"""
        if not activities:
            return None, line_view.ERROR_NO_ACTIVITIES
        carousel = line_view.format_driver_carousel(activities)
        return carousel, None
    
    def return_valid_driver_activity(self):
        activities = activity_controller.get_all_driver_activities()
        carousel, error = activity_controller.format_driver_activities_carousel(activities)
        if error:
            return None, error
        else: 
            if len(activities) != 0:
                # 若有活動且人數未滿
                if carousel != {
                        "type": "carousel",
                        "contents": []
                    }:
                    return json.dumps(carousel), None # 改成字串格式
                # 若有活動但人數皆已滿
                else:
                    return 'full', None
            else:
                return 'empty', None


    def format_driver_activity_detail(self, index: int) -> str:
        """格式化司機活動詳細資訊"""
        activity = self.get_driver_activity(index)
        if not activity:
            return line_view.ERROR_ACTIVITY_NOT_FOUND
        
        return line_view.format_driver_detail_AsConfirmTemplate(activity)
    
    # ==================== 乘客活動相關 ====================
    
    def get_all_passenger_activities(self) -> List[PassengerActivity]:
        """取得所有乘客活動"""
        self.repository.refresh_passenger_activities()
        return self.repository.get_all_passenger_activities()
    
    def get_passenger_activity(self, index: int) -> Optional[PassengerActivity]:
        """取得特定乘客活動"""
        return self.repository.get_passenger_activity_by_index(index)
    
    def find_user_passenger_activities(self, user_id: str) -> List[PassengerActivity]:
        """查詢使用者參與的乘客活動"""
        return self.repository.find_passenger_activities_by_user(user_id)
    
    def format_passenger_activities_carousel(self, activities: List[PassengerActivity]):
        """格式化乘客活動輪播"""
        if not activities:
            return None, line_view.ERROR_NO_ACTIVITIES
        
        carousel = line_view.format_passenger_carousel(activities)
        return carousel, None
    
    def return_valid_passenger_activity(self):
        activities = activity_controller.get_all_passenger_activities()
        carousel, error = activity_controller.format_passenger_activities_carousel(activities)
        if error:
            return None, error
        else: 
            if len(activities) != 0:
                # 若有活動且人數未滿
                if carousel != {
                        "type": "carousel",
                        "contents": []
                    }:
                    return json.dumps(carousel) # 改成字串格式
                # 若有活動但人數皆已滿
                else:
                    return 'full'
            else:
                return 'empty'

    def format_passenger_activity_detail(self, index: int) -> str:
        """格式化乘客活動詳細資訊"""
        activity = self.get_passenger_activity(index)
        if not activity:
            return line_view.ERROR_ACTIVITY_NOT_FOUND
        
        return line_view.format_passenger_detail_AsConfirmTemplate(activity)
    
    # ==================== 使用者預約查詢 ====================
    
    def get_user_all_reservations(self, user_id: str) -> str:
        """取得使用者所有預約"""
        driver_activities = self.find_user_driver_activities(user_id)
        passenger_activities = self.find_user_passenger_activities(user_id)
        
        return line_view.format_user_reservations(
            driver_activities, 
            passenger_activities, 
            user_id
        )


# 全局單例
activity_controller = ActivityController()
