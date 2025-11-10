"""
Controllers - 通知控制器
負責處理自動通知的業務邏輯
"""
import schedule
import time
import threading
from typing import Set
from datetime import datetime, timedelta
from models.repository import repository
from views.email_view import email_view
from services.email_service import email_service
from config import NOTIFICATION_HOURS_BEFORE, CHECK_INTERVAL_SECONDS


class NotificationController:
    """通知控制器 - 處理通知邏輯"""
    
    def __init__(self):
        self.repository = repository
        # 追蹤已處理的活動
        self.processed_driver_indices: Set[int] = set()
        self.processed_passenger_indices: Set[int] = set()
    
    @staticmethod
    def parse_activity_time(time_str: str) -> datetime:
        """解析活動時間字串"""
        parts = time_str.split()
        date_part = parts[0]
        ampm = parts[1]
        time_part = parts[2]
        
        # 轉換中文上午/下午為 AM/PM
        ampm_en = "AM" if ampm == "上午" else "PM"
        datetime_str = f"{date_part} {time_part} {ampm_en}"
        
        return datetime.strptime(datetime_str, "%Y/%m/%d %I:%M:%S %p")
    
    @staticmethod
    def should_notify(activity_time: str, hours_before: int = NOTIFICATION_HOURS_BEFORE) -> bool:
        """判斷是否應該發送通知"""
        try:
            # 解析活動時間並調整為整點
            activity_dt = NotificationController.parse_activity_time(activity_time)
            activity_dt = activity_dt.replace(minute=0, second=0, microsecond=0)
            
            # 計算通知時間（活動前 N 小時）
            notification_time = activity_dt - timedelta(hours=hours_before)
            
            # 取得當前時間（UTC+8）並調整為整點
            now = datetime.now() + timedelta(hours=8)
            now = now.replace(minute=0, second=0, microsecond=0)
            
            return notification_time == now
        except Exception as e:
            print(f"解析時間失敗: {e}")
            return False
    
    def check_driver_notifications(self):
        """檢查並發送司機活動通知"""
        print(f"檢查司機活動通知 - 已處理: {self.processed_driver_indices}")
        
        try:
            # 刷新資料
            self.repository.refresh_driver_activities()
            activities = self.repository.get_all_driver_activities()
            
            for activity in activities:
                # 跳過已處理或已通知的活動
                if activity.index in self.processed_driver_indices or activity.is_notified():
                    continue
                
                # 檢查是否到達通知時間
                if not self.should_notify(activity.time):
                    continue
                
                try:
                    # 根據活動狀態發送不同通知
                    if not activity.is_valid_limit():
                        # 未註明人數上限
                        subject, body = email_view.format_driver_no_limit_email(activity)
                        email_service.send_email(activity.email, subject, body)
                    elif activity.is_full():
                        # 已滿
                        subject, body = email_view.format_driver_full_email(activity)
                        email_service.send_email(activity.email, subject, body)
                    else:
                        # 未滿
                        subject, body = email_view.format_driver_not_full_email(activity)
                        email_service.send_email(activity.email, subject, body)
                    
                    # 更新通知狀態
                    self.repository.mark_driver_activity_notified(activity.index)
                    self.processed_driver_indices.add(activity.index)
                    
                    print(f"已發送司機活動通知 - 編號: {activity.carpool_id}, 索引: {activity.index}")
                
                except Exception as e:
                    print(f"處理司機活動 {activity.index} 通知時發生錯誤: {e}")
        
        except Exception as e:
            print(f"檢查司機活動通知時發生錯誤: {e}")
    
    def check_passenger_notifications(self):
        """檢查並發送乘客活動通知"""
        print(f"檢查乘客活動通知 - 已處理: {self.processed_passenger_indices}")
        
        try:
            # 刷新資料
            self.repository.refresh_passenger_activities()
            activities = self.repository.get_all_passenger_activities()
            
            for activity in activities:
                # 跳過已處理或已通知的活動
                if activity.index in self.processed_passenger_indices or activity.is_notified():
                    continue
                
                # 檢查是否到達通知時間
                if not self.should_notify(activity.time):
                    continue
                
                try:
                    # 根據活動狀態發送不同通知
                    if activity.has_driver():
                        # 有司機
                        subject, body = email_view.format_passenger_has_driver_email(activity)
                        email_service.send_email(activity.email, subject, body)
                    else:
                        # 無司機
                        subject, body = email_view.format_passenger_no_driver_email(activity)
                        email_service.send_email(activity.email, subject, body)
                    
                    # 更新通知狀態
                    self.repository.mark_passenger_activity_notified(activity.index)
                    self.processed_passenger_indices.add(activity.index)
                    
                    print(f"已發送乘客活動通知 - 編號: {activity.carpool_id}, 索引: {activity.index}")
                
                except Exception as e:
                    print(f"處理乘客活動 {activity.index} 通知時發生錯誤: {e}")
        
        except Exception as e:
            print(f"檢查乘客活動通知時發生錯誤: {e}")
    
    def check_all_notifications(self):
        """檢查所有通知"""
        self.check_driver_notifications()
        self.check_passenger_notifications()
    
    def start_scheduler(self):
        """啟動排程器"""
        # 設定排程任務
        schedule.every(CHECK_INTERVAL_SECONDS).seconds.do(self.check_all_notifications)
        
        # 在背景執行緒中運行
        def run_schedule():
            while True:
                schedule.run_pending()
                time.sleep(1)
        
        thread = threading.Thread(target=run_schedule, daemon=True)
        thread.start()
        print(f"通知排程器已啟動，每 {CHECK_INTERVAL_SECONDS} 秒檢查一次")


# 全局單例
notification_controller = NotificationController()
