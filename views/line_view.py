"""
Views - LINE Bot 訊息視圖層
負責所有 LINE Bot 訊息的格式化和模板
"""
from typing import List
from linebot.v3.messaging import (
    CarouselTemplate,
    CarouselColumn,
    PostbackAction,
    ConfirmTemplate,
    TemplateMessage,
)
from models.activity_model import DriverActivity, PassengerActivity

class LineMessageView:
    """LINE Bot 訊息視圖類別"""
    
    @staticmethod
    def format_welcome_message() -> str:
        """格式化歡迎訊息"""
        return (
            '歡迎使用共乘阿穿！\n\n'
            '請選擇功能：\n'
            '• 司機揪團 - 查看司機發起的共乘活動\n'
            '• 乘客揪團 - 查看乘客發起的共乘活動\n'
            '• 我的預約 - 查看您的所有預約\n'
            '• 取消預約(司機) - 取消司機揪團預約\n'
            '• 取消預約(乘客) - 取消乘客揪團預約'
        )
    
    @staticmethod
    def format_driver_carousel_column(activity: DriverActivity, index: int) -> CarouselColumn:
        """格式化單個司機活動輪播欄位"""
        web_driver_data_case={
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "FROM",
                        "color": "#ffffff66",
                        "size": "xxs"
                    },
                    {
                        "type": "text",
                        "text": activity.departure,
                        "color": "#ffffff",
                        "size": "lg",
                        "weight": "bold"
                    }
                    ]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "TO",
                        "color": "#ffffff66",
                        "size": "xxs"
                    },
                    {
                        "type": "text",
                        "text": activity.destination,
                        "color": "#ffffff",
                        "size": "lg",
                        "weight": "bold",
                        "margin": "none"
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": f"出發時間：{activity.time}",
                    "color": "#000000",
                    "size": "xs",
                    "contents": [],
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"預估時程：{activity.format_time_duration()}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"發起人（司機）：{activity.organizer_name}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"共乘人數上限：{activity.limit}",
                    "color": "#000000",
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": f"共乘費用分攤：{activity.cost}",
                    "color": "#000000",
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": f"當前預約人數：{activity.get_passenger_count()}",
                    "color": "#000000",
                    "size": "xs"
                }
                ],
                "paddingAll": "20px",
                "backgroundColor": "#e6b89d",
                "spacing": "md",
                "height": "265px",
                "paddingTop": "22px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "text",
                    "text": f"共乘編號：{activity.carpool_id}",
                    "margin": "none",
                    "size": "sm",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": f"交通工具：{activity.vehicle}",
                    "margin": "none",
                    "size": "sm",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": f"備註：{activity.description}",
                    "margin": "xl"
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "button",
                    "action": {
                    "type": "postback",
                    "label": "我要共乘（詳細資訊）",
                    "data": f"driver_Num_detail_{index}",
                    "displayText": f"{activity.departure}到{activity.destination}的共乘資訊"
                    },
                    "style": "secondary"
                }
                ]
            }
        }
        # 新增規範
        driver_speci_set = ['上下車地點可討論', '自備零錢不找零', '接受線上付款 / 轉帳', '禁食', '不聊天', '寵物需裝籠', '謝絕寵物']
        for specification in driver_speci_set:
            if specification in activity.rules:
                r = {
                        "type": "text",
                        "text": specification,
                        "size": "sm",
                        "margin": "none",
                        "contents": [],
                        "offsetEnd": "none"
                    }
                web_driver_data_case['body']['contents'].insert(2,r)
            else:
                pass
        if '※ 人滿才發車' in activity.rules:
            r = {
                    "type": "text",
                    "text": '※ 人滿才發車',
                    "size": "sm",
                    "margin": "none",
                    "color": "#ff5551",
                    "contents": [],
                    "offsetEnd": "none"
                }
            web_driver_data_case['body']['contents'].insert(2,r)
        else:
            pass
        return web_driver_data_case
    
    @staticmethod
    def format_driver_carousel(activities: List[PassengerActivity]) -> CarouselTemplate:
        """格式化司機活動輪播"""
        line_flex_json = {
            "type": "carousel",
            "contents": []
        }   
        for activity in activities:
            if activity.passenger_isfull() == False and activity.isOutDate() == False or activity.isNowPost() == True:
                line_flex_json['contents'].append(LineMessageView.format_driver_carousel_column(activity, activity.index))
        return line_flex_json
    
    @staticmethod
    def format_passenger_carousel_column(activity: PassengerActivity, index: int) -> CarouselColumn:
        """格式化單個乘客活動輪播欄位"""
        web_passenger_data_case={
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "FROM",
                        "color": "#ffffff66",
                        "size": "xxs"
                    },
                    {
                        "type": "text",
                        "text": activity.departure,
                        "color": "#ffffff",
                        "size": "lg",
                        "weight": "bold"
                    }
                    ]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "TO",
                        "color": "#ffffff66",
                        "size": "xxs"
                    },
                    {
                        "type": "text",
                        "text": f"目的地點{activity.destination}",
                        "color": "#ffffff",
                        "size": "lg",
                        "weight": "bold",
                        "margin": "none"
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": f"出發時間：{activity.time}",
                    "color": "#000000",
                    "size": "xs",
                    "contents": [],
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"預估時程：{activity.format_time_duration()}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"發起人（乘客）：{activity.organizer_name}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"司機：{activity.has_driver_return_name()}",
                    "color": "#000000",
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": f"共乘人數上限：{activity.limit}",
                    "color": "#000000",
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": f"當前預約人數：{int(activity.get_passenger_count())}",
                    "color": "#000000",
                    "size": "xs"
                }
                ],
                "paddingAll": "20px",
                "backgroundColor": "#e6b89d",
                "spacing": "md",
                "height": "265px",
                "paddingTop": "22px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "text",
                    "text": f"共乘編號：{activity.carpool_id}",
                    "margin": "none",
                    "size": "sm",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": f"交通工具：{activity.vehicle}",
                    "margin": "none",
                    "size": "sm",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": f"備註：{activity.description}",
                    "margin": "xl"
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "button",
                    "action": {
                    "type": "postback",
                    "label": "我要共乘∕當司機（詳細資訊）",
                    "data": f"passenger_Num_detail_{index}",
                    "displayText": f"{activity.departure}到{activity.destination}的共乘資訊"
                    },
                    "style": "secondary"
                }
                ]
            }
        }
        # 新增規範
        passenger_speci_set = ['上下車地點可討論', '不聊天', '嚴禁喝酒及抽菸', '禁食', '謝絕寵物', '寵物需裝籠']
        passenger_speci_red_set = ['已有司機', '尚未有司機（徵求司機！）', '叫車分攤費用', '※ 人滿才發車']
        for specification in passenger_speci_set:
            if specification in activity.rules:
                r = {
                        "type": "text",
                        "text": specification,
                        "size": "sm",
                        "margin": "none",
                        "contents": [],
                        "offsetEnd": "none"
                    }
                web_passenger_data_case['body']['contents'].insert(2,r)
            else:
                pass
        for specification in passenger_speci_red_set:
            if specification in activity.rules:
                r = {
                        "type": "text",
                        "text": specification,
                        "size": "sm",
                        "margin": "none",
                        "color": "#ff5551",
                        "contents": [],
                        "offsetEnd": "none"
                    }
                web_passenger_data_case['body']['contents'].insert(2,r)
            else:
                pass
            pass
        return web_passenger_data_case
    
    @staticmethod
    def format_passenger_carousel(activities: List[PassengerActivity]) -> CarouselTemplate:
        """格式化乘客活動輪播"""
        line_flex_json = {
            "type": "carousel",
            "contents": []
        }   
        for activity in activities:
            if activity.passenger_isfull() == False and activity.isOutDate() == False or activity.isNowPost() == True:
                line_flex_json['contents'].append(LineMessageView.format_passenger_carousel_column(activity, activity.index))
        return line_flex_json
    
    @staticmethod
    def format_driver_detail_AsConfirmTemplate(activity: DriverActivity) -> str:
        """格式化司機活動詳細資訊"""
        confirm_template = ConfirmTemplate(
            text = f"📎共乘編號：{activity.carpool_id}\n📍出發地點：{activity.departure}\n📍目的地點：{activity.destination}\n🕒出發時間：\n{activity.time}\n⏳預估時程：{activity.format_time_duration()}\n#️⃣共乘上限：{activity.limit} 人\n✨發起人（司機）：\n{activity.organizer_name}\n💰費用分攤：{activity.cost}\n🛞交通工具：{activity.vehicle}\n❗️行車規範：\n{activity.rules}\n💬簡介：\n{activity.description}\n",
            actions=[ #只能放兩個Action
                PostbackAction(label='我想共乘！', text='我想共乘！', data=f'reserve_driver_AsPassenger_{activity.index}'),
                PostbackAction(label='司機聯絡資訊', text='司機聯絡資訊', data = f'driver_info_{activity.index}')
            ]
        )
        template_message = TemplateMessage(
            alt_text = f'從{activity.departure}到{activity.destination}的詳細資訊',
            template = confirm_template
        )
        return template_message

    @staticmethod
    def format_passenger_detail_AsConfirmTemplate(activity: DriverActivity) -> str:
        """格式化乘客活動詳細資訊"""
        driver_name = activity.driver.name if activity.driver else '無'
        confirm_template = ConfirmTemplate(
            text = f"📎共乘編號：{activity.carpool_id}\n📍出發地點：{activity.departure}\n📍目的地點：{activity.destination}\n🕒出發時間：\n{activity.time}\n⏳預估時程：{activity.format_time_duration()}\n#️⃣共乘上限：{activity.limit} 人\n✨發起人（乘客）：\n{activity.organizer_name}\n🆔LineID：{activity.organizer_line_id}\n📱手機號碼：{activity.organizer_phone}\n🚗司機名稱：{driver_name}\n🛞交通工具：{activity.vehicle}\n❗️行車規範：\n{activity.rules}\n💬備註：\n{activity.description}\n",
            actions=[ #一定只能放兩個Action
                PostbackAction(label='我要共乘！', text='我要共乘！', data=f'reserve_passenger_AsPassenger_{activity.index}'),
                PostbackAction(label='我想當司機！', text='我想當司機！', data=f'reserve_passenger_AsDriver_{activity.index}')   
            ]
        )
        template_message = TemplateMessage(
            alt_text = f'從{activity.departure}到{activity.destination}的詳細資訊',
            template = confirm_template
        )
        return template_message
    
    @staticmethod
    def format_reservation_success(activity, role: str) -> str:
        """格式化預約成功訊息"""
        return (
            f'已幫您預約為{role}，記得透過LineID聯繫活動發起人!\n'
            f'發起人名稱：\n{activity.organizer_name}\n'
            f'LineID：{activity.organizer_line_id}\n'
            f'手機號碼：{activity.organizer_phone}'
        )
    
    @staticmethod
    def format_cancellation_success(carpool_id: str, role: str) -> str:
        """格式化取消預約成功訊息"""
        return f'已幫您取消共乘編號：{carpool_id}的{role}預約'
    
    @staticmethod
    def format_user_reservations_carousel(driver_activities: List[DriverActivity], passenger_activities: List[PassengerActivity], user_id: str) -> str:
        """格式化使用者預約列表"""
        # 司機揪團
        line_flex_json = {
            "type": "carousel",
            "contents": []
        } 
        for activity in driver_activities:
            if activity.is_user_passenger(user_id):
                """格式化司機活動輪播"""
                if activity.passenger_isfull() == False and activity.isOutDate() == False or activity.isNowPost() == True:
                    line_flex_json['contents'].append(LineMessageView.format_driver_AsPassenger_ReservationType(activity))
        # 乘客揪團
        for activity in passenger_activities:
            if activity.is_user_passenger(user_id):
                """格式化乘客活動(使用者為乘客)輪播"""
                if activity.isOutDate() == False or activity.isNowPost() == True:
                    line_flex_json['contents'].append(LineMessageView.format_passenger_AsPassenger_ReservationType(activity))
            elif activity.is_user_driver(user_id):
                """格式化乘客活動(使用者為司機)輪播"""
                if activity.isOutDate() == False or activity.isNowPost() == True:
                    line_flex_json['contents'].append(LineMessageView.format_passenger_AsDriver_ReservationType(activity, activity.index))
        return line_flex_json
    
    @staticmethod
    def format_driver_AsPassenger_ReservationType(activity: PassengerActivity):
        """格式化單個司機活動輪播欄位"""
        web_driver_data_case={
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "FROM",
                        "color": "#ffffff66",
                        "size": "xxs"
                    },
                    {
                        "type": "text",
                        "text": activity.departure,
                        "color": "#ffffff",
                        "size": "lg",
                        "weight": "bold"
                    }
                    ]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "TO",
                        "color": "#ffffff66",
                        "size": "xxs"
                    },
                    {
                        "type": "text",
                        "text": activity.destination,
                        "color": "#ffffff",
                        "size": "lg",
                        "weight": "bold",
                        "margin": "none"
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": f"出發時間：{activity.time}",
                    "color": "#000000",
                    "size": "xs",
                    "contents": [],
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"總時程：{activity.format_time_duration()}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"發起人（司機）：{activity.organizer_name}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"手機號碼：{activity.organizer_phone}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"LineID：{activity.organizer_line_id}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"共乘人數上限：{activity.limit}",
                    "color": "#000000",
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": f"共乘費用分攤：{activity.cost}",
                    "color": "#000000",
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": f"當前預約人數：{activity.get_passenger_count()}",
                    "color": "#000000",
                    "size": "xs"
                }
                ],
                "paddingAll": "20px",
                "backgroundColor": "#e6b89d",
                "spacing": "md",
                "height": "300px",
                "paddingTop": "22px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "text",
                    "text": f"共乘編號：{activity.carpool_id}",
                    "margin": "none",
                    "size": "sm",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": f"交通工具：{activity.vehicle}",
                    "margin": "none",
                    "size": "sm",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": f"備註：{activity.description}",
                    "margin": "xl"
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                        "type": "postback",
                        "label": "詳細資訊",
                        "data": f"driver_Num_reserved_detail_{activity.index}",
                        "displayText": f"{activity.departure}到{activity.destination}的共乘資訊"
                        },
                        "style": "link",
                        "margin": "none",
                        "height": "sm"
                    },
                    {
                        "type": "button",
                        "action": {
                        "type": "postback",
                        "label": "取消乘客預約",
                        "data": f"cancel_DriverActivity_AsPassenger_{activity.index}",
                        "displayText": f"我想取消共乘編號：{activity.carpool_id}的乘客預約"
                        },
                        "style": "primary",
                        "height": "sm",
                        "color": "#ff5757"
                    }
                ]
            }
        }
        # 新增規範
        driver_speci_set = ['上下車地點可討論', '自備零錢不找零', '接受線上付款 / 轉帳', '禁食', '不聊天', '寵物需裝籠', '謝絕寵物']
        for specification in driver_speci_set:
            if specification in activity.rules:
                r = {
                        "type": "text",
                        "text": specification,
                        "size": "sm",
                        "margin": "none",
                        "contents": [],
                        "offsetEnd": "none"
                    }
                web_driver_data_case['body']['contents'].insert(2,r)
            else:
                pass
        if '※ 人滿才發車' in activity.rules:
            r = {
                    "type": "text",
                    "text": '※ 人滿才發車',
                    "size": "sm",
                    "margin": "none",
                    "color": "#ff5551",
                    "contents": [],
                    "offsetEnd": "none"
                }
            web_driver_data_case['body']['contents'].insert(2,r)
        else:
            pass
        return web_driver_data_case   
    
    @staticmethod
    def format_passenger_AsPassenger_ReservationType(activity: PassengerActivity):
        """格式化單個乘客活動輪播欄位"""
        web_passenger_data_case={
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "FROM",
                        "color": "#ffffff66",
                        "size": "xxs"
                    },
                    {
                        "type": "text",
                        "text": activity.departure,
                        "color": "#ffffff",
                        "size": "lg",
                        "weight": "bold"
                    }
                    ]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "TO",
                        "color": "#ffffff66",
                        "size": "xxs"
                    },
                    {
                        "type": "text",
                        "text": activity.destination,
                        "color": "#ffffff",
                        "size": "lg",
                        "weight": "bold",
                        "margin": "none"
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": f"出發時間：{activity.time}",
                    "color": "#000000",
                    "size": "xs",
                    "contents": [],
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"預估時程：{activity.format_time_duration()}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"發起人（乘客）：{activity.organizer_name}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"手機號碼：{activity.organizer_phone}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"LineID：{activity.organizer_line_id}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"司機：{activity.has_driver_return_name()}",
                    "color": "#000000",
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": f"共乘人數上限：{activity.limit}",
                    "color": "#000000",
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": f"當前預約人數：{int(activity.get_passenger_count())}",
                    "color": "#000000",
                    "size": "xs"
                }
                ],
                "paddingAll": "20px",
                "backgroundColor": "#e6b89d",
                "spacing": "md",
                "height": "300px",
                "paddingTop": "22px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "text",
                    "text": f"共乘編號：{activity.carpool_id}",
                    "margin": "none",
                    "size": "sm",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": f"交通工具：{activity.vehicle}",
                    "margin": "none",
                    "size": "sm",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": f"備註：{activity.description}",
                    "margin": "xl"
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                        "type": "postback",
                        "label": "詳細資訊",
                        "data": f"passenger_Num_reserved_detail_{activity.index}",
                        "displayText": f"{activity.departure}到{activity.destination}的共乘資訊"
                        },
                        "style": "link",
                        "margin": "none",
                        "height": "sm"
                    },
                    {
                        "type": "button",
                        "action": {
                        "type": "postback",
                        "label": "取消乘客預約",
                        "data": f"cancel_PassengerActivity_AsPassenger_{activity.index}",
                        "displayText": f"我想取消共乘編號：{activity.carpool_id}的乘客預約"
                        },
                        "style": "primary",
                        "height": "sm",
                        "color": "#ff5757"
                    }
                ]
            }
        }
        # 新增規範
        passenger_speci_set = ['上下車地點可討論', '不聊天', '嚴禁喝酒及抽菸', '禁食', '謝絕寵物', '寵物需裝籠']
        passenger_speci_red_set = ['已有司機', '尚未有司機（徵求司機！）', '叫車分攤費用', '※ 人滿才發車']
        for specification in passenger_speci_set:
            if specification in activity.rules:
                r = {
                        "type": "text",
                        "text": specification,
                        "size": "sm",
                        "margin": "none",
                        "contents": [],
                        "offsetEnd": "none"
                    }
                web_passenger_data_case['body']['contents'].insert(2,r)
            else:
                pass
        for specification in passenger_speci_red_set:
            if specification in activity.rules:
                r = {
                        "type": "text",
                        "text": specification,
                        "size": "sm",
                        "margin": "none",
                        "color": "#ff5551",
                        "contents": [],
                        "offsetEnd": "none"
                    }
                web_passenger_data_case['body']['contents'].insert(2,r)
            else:
                pass
            pass
        return web_passenger_data_case
    
    def format_passenger_AsDriver_ReservationType(activity: PassengerActivity, index: int):
        """格式化單個乘客活動輪播欄位"""
        web_passenger_data_case={
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "FROM",
                        "color": "#ffffff66",
                        "size": "xxs"
                    },
                    {
                        "type": "text",
                        "text": activity.departure,
                        "color": "#ffffff",
                        "size": "lg",
                        "weight": "bold"
                    }
                    ]
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                    {
                        "type": "text",
                        "text": "TO",
                        "color": "#ffffff66",
                        "size": "xxs"
                    },
                    {
                        "type": "text",
                        "text": activity.destination,
                        "color": "#ffffff",
                        "size": "lg",
                        "weight": "bold",
                        "margin": "none"
                    }
                    ]
                },
                {
                    "type": "text",
                    "text": f"出發時間：{activity.time}",
                    "color": "#000000",
                    "size": "xs",
                    "contents": [],
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"預估時程：{activity.format_time_duration()}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"發起人（乘客）：{activity.organizer_name}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"手機號碼：{activity.organizer_phone}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"LineID：{activity.organizer_line_id}",
                    "color": "#000000",
                    "size": "xs",
                    "decoration": "underline"
                },
                {
                    "type": "text",
                    "text": f"司機：{activity.has_driver_return_name()}",
                    "color": "#000000",
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": f"共乘人數上限：{activity.limit}",
                    "color": "#000000",
                    "size": "xs"
                },
                {
                    "type": "text",
                    "text": f"當前預約人數：{int(activity.get_passenger_count())}",
                    "color": "#000000",
                    "size": "xs"
                }
                ],
                "paddingAll": "20px",
                "backgroundColor": "#c89273",
                "spacing": "md",
                "height": "300px",
                "paddingTop": "22px"
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                {
                    "type": "text",
                    "text": f"共乘編號：{activity.carpool_id}",
                    "margin": "none",
                    "size": "sm",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": f"交通工具：{activity.vehicle}",
                    "margin": "none",
                    "size": "sm",
                    "weight": "bold"
                },
                {
                    "type": "text",
                    "text": f"備註：{activity.description}",
                    "margin": "xl"
                }
                ]
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "button",
                        "action": {
                        "type": "postback",
                        "label": "詳細資訊",
                        "data": f"passenger_Num_reserved_detail_{activity.index}",
                        "displayText": f"{activity.departure}到{activity.destination}的共乘資訊"
                        },
                        "style": "link",
                        "margin": "none",
                        "height": "sm"
                    },
                    {
                        "type": "button",
                        "action": {
                        "type": "postback",
                        "label": "取消乘客預約",
                        "data": f"cancel_PassengerActivity_AsDriver_{activity.index}",
                        "displayText": f"我想取消共乘編號：{activity.carpool_id}的司機預約"
                        },
                        "style": "primary",
                        "height": "sm",
                        "color": "#ff5757"
                    }
                ]
            }
        }
        # 新增規範
        passenger_speci_set = ['上下車地點可討論', '不聊天', '嚴禁喝酒及抽菸', '禁食', '謝絕寵物', '寵物需裝籠']
        passenger_speci_red_set = ['已有司機', '尚未有司機（徵求司機！）', '叫車分攤費用', '※ 人滿才發車']
        for specification in passenger_speci_set:
            if specification in activity.rules:
                r = {
                        "type": "text",
                        "text": specification,
                        "size": "sm",
                        "margin": "none",
                        "contents": [],
                        "offsetEnd": "none"
                    }
                web_passenger_data_case['body']['contents'].insert(2,r)
            else:
                pass
        for specification in passenger_speci_red_set:
            if specification in activity.rules:
                r = {
                        "type": "text",
                        "text": specification,
                        "size": "sm",
                        "margin": "none",
                        "color": "#ff5551",
                        "contents": [],
                        "offsetEnd": "none"
                    }
                web_passenger_data_case['body']['contents'].insert(2,r)
            else:
                pass
            pass
        return web_passenger_data_case


    # 錯誤訊息
    ERROR_ACTIVITY_NOT_FOUND = '活動不存在'

    ERROR_DRIVER_ACTIVITY_FULL = '目前司機發起之活動預約人數皆已滿，或是逾期。'
    ERROR_PASSENGER_ACTIVITY_FULL = '目前乘客發起之活動預約人數皆已滿，或是逾期。'

    ERROR_ALREADY_RESERVED_AS_PASSENGER = '您已預約為乘客！'
    ERROR_ALREADY_RESERVED_AS_DRIVER = '您已預約為司機！'

    ERROR_DRIVER_POSITION_TAKEN = '此活動已有司機囉！'
    ERROR_NOT_RESERVED = '您尚未預約任何活動'
    ERROR_NO_DRIVER_ACTIVITIES = '目前尚無司機發起共乘活動'
    ERROR_NO_PASSENGER_ACTIVITIES = '目前尚無乘客發起共乘活動'
    ERROR_LOADING_FAILED = '載入資料時發生錯誤'
    ERROR_ACTIVITY_FULL = '此活動人數已滿'


# 全局單例
line_view = LineMessageView()
