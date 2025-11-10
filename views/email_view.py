"""
Views - Email 訊息視圖層
負責所有 Email 訊息的格式化和模板
"""
from models.activity_model import DriverActivity, PassengerActivity


class EmailMessageView:
    """Email 訊息視圖類別"""
    
    @staticmethod
    def format_driver_activity_info(activity: DriverActivity) -> str:
        """格式化司機活動基本資訊（HTML）"""
        return (
            f'共乘編號：{activity.carpool_id}<br>'
            f'發車地點：{activity.departure}<br>'
            f'目的地：{activity.destination}<br>'
            f'出發時間：<br>{activity.time}<br>'
            f'總時程：{activity.format_time_duration()}<br>'
            f'發起人：{activity.organizer_name}<br>'
            f'手機號碼：{activity.organizer_phone}<br>'
            f'LineID：{activity.organizer_line_id}<br>'
            f'共乘人數上限：{activity.limit}<br>'
            f'共乘費用分攤：{activity.cost}<br>'
            f'交通工具：{activity.vehicle}<br>'
            f'行車規範：<br>{activity.rules}<br>'
            f'簡介：<br>{activity.description}<br>'
        )
    
    @staticmethod
    def format_passenger_activity_info(activity: PassengerActivity) -> str:
        """格式化乘客活動基本資訊（HTML）"""
        return (
            f'共乘編號：{activity.carpool_id}<br>'
            f'出發地點：{activity.departure}<br>'
            f'目的地點：{activity.destination}<br>'
            f'出發時間：<br>{activity.time}<br>'
            f'預估時程：{activity.format_time_duration()}<br>'
            f'共乘上限：{activity.limit} 人<br>'
            f'發起人（乘客）：<br>{activity.organizer_name}<br>'
            f'LineID：{activity.organizer_line_id}<br>'
            f'手機號碼：{activity.organizer_phone}<br>'
            f'交通工具：{activity.vehicle}<br>'
            f'行車規範：<br>{activity.rules}<br>'
            f'備註：<br>{activity.description}<br>'
        )
    
    @staticmethod
    def format_participant_names(participants) -> str:
        """格式化參與者名稱列表"""
        if not participants:
            return '無'
        names = [p.name for p in participants]
        return '、'.join(names)
    
    @staticmethod
    def format_driver_no_limit_email(activity: DriverActivity) -> tuple:
        """
        格式化司機未註明人數上限的通知郵件
        返回: (subject, body_html)
        """
        subject = '您在 共乘阿穿 發起的（司機揪團）共乘活動報名已截止'
        
        participant_names = EmailMessageView.format_participant_names(activity.passengers)
        
        body = (
            f'您在 共乘阿穿 發起的（司機揪團）共乘活動報名已截止，'
            f'因為您未註明共乘人數上限，因此僅以此郵件做通知，'
            f'也請留意是否有乘客臨時聯絡您需要共乘，共乘編號：{activity.carpool_id}。'
            f'活動資訊如下：<br><br>'
            f'{EmailMessageView.format_driver_activity_info(activity)}<br>'
            f'參與者Line名稱:{participant_names}'
        )
        
        return subject, body
    
    @staticmethod
    def format_driver_full_email(activity: DriverActivity) -> tuple:
        """
        格式化司機活動已滿的通知郵件
        返回: (subject, body_html)
        """
        subject = '您在 共乘阿穿 發起的（司機揪團）共乘活動已額滿'
        
        participant_names = EmailMessageView.format_participant_names(activity.passengers)
        
        body = (
            f'您在 共乘阿穿 發起的（司機揪團）共乘活動已額滿，'
            f'共乘編號：{activity.carpool_id}。活動資訊如下：<br><br>'
            f'{EmailMessageView.format_driver_activity_info(activity)}<br>'
            f'參與者Line名稱:{participant_names}'
        )
        
        return subject, body
    
    @staticmethod
    def format_driver_not_full_email(activity: DriverActivity) -> tuple:
        """
        格式化司機活動未滿的通知郵件
        返回: (subject, body_html)
        """
        subject = '您在 共乘阿穿 發起的（司機揪團）共乘活動報名已截止'
        
        participant_names = EmailMessageView.format_participant_names(activity.passengers)
        
        body = (
            f'您在 共乘阿穿 發起的（司機揪團）共乘活動報名已截止，'
            f'但尚未額滿，共乘編號：{activity.carpool_id}。活動資訊如下：<br><br>'
            f'{EmailMessageView.format_driver_activity_info(activity)}<br>'
            f'參與者Line名稱:{participant_names}'
        )
        
        return subject, body
    
    @staticmethod
    def format_passenger_has_driver_email(activity: PassengerActivity) -> tuple:
        """
        格式化乘客活動已有司機的通知郵件
        返回: (subject, body_html)
        """
        subject = '您在 共乘阿穿 發起的（乘客揪團）共乘活動報名已截止'
        
        participant_names = EmailMessageView.format_participant_names(activity.passengers)
        driver_name = activity.driver.name if activity.driver else '無'
        
        body = (
            f'您在 共乘阿穿 發起的（乘客揪團）共乘活動報名已截止，'
            f'且已有司機接單，共乘編號：{activity.carpool_id}。活動資訊如下：<br><br>'
            f'{EmailMessageView.format_passenger_activity_info(activity)}<br>'
            f'司機名稱：{driver_name}<br>'
            f'參與者Line名稱:{participant_names}'
        )
        
        return subject, body
    
    @staticmethod
    def format_passenger_no_driver_email(activity: PassengerActivity) -> tuple:
        """
        格式化乘客活動無司機的通知郵件
        返回: (subject, body_html)
        """
        subject = '您在 共乘阿穿 發起的（乘客揪團）共乘活動報名已截止'
        
        participant_names = EmailMessageView.format_participant_names(activity.passengers)
        
        body = (
            f'您在 共乘阿穿 發起的（乘客揪團）共乘活動報名已截止，'
            f'但尚無司機接單，共乘編號：{activity.carpool_id}。活動資訊如下：<br><br>'
            f'{EmailMessageView.format_passenger_activity_info(activity)}<br>'
            f'參與者Line名稱:{participant_names}'
        )
        
        return subject, body


# 全局單例
email_view = EmailMessageView()
