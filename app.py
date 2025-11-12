"""
主應用程式 - Flask 伺服器和 LINE Bot 事件處理
遵循 MVC 架構模式
"""
import os
import re
from flask import Flask, request, abort
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, FollowEvent, PostbackEvent, TextMessageContent

from config import CHANNEL_SECRET
from controllers.activity_controller import activity_controller
from controllers.reservation_controller import reservation_controller
from controllers.notification_controller import notification_controller
from services.line_service import line_service
from models.activity_model import User
from views.line_view import line_view


# 初始化 Flask 應用
app = Flask(__name__)

# 初始化 LINE Bot Handler
line_handler = WebhookHandler(CHANNEL_SECRET)

# ==================== Flask 路由 ====================

@app.route("/callback", methods=['POST'])
def callback():
    """LINE Bot Webhook 回調端點"""
    # 取得 X-Line-Signature header
    signature = request.headers['X-Line-Signature']
    
    # 取得請求內容
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    # 處理 webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    
    return 'OK'


@app.route("/")
def index():
    """首頁端點"""
    return "共乘阿穿 LINE Bot (MVC架構) 運行中"


@app.route("/health")
def health():
    """健康檢查端點"""
    return {"status": "healthy", "architecture": "MVC"}, 200


# ==================== LINE Bot 事件處理器 ====================

@line_handler.add(MessageEvent, message=TextMessageContent)
def handle_text_message(event):
    """處理文字訊息事件"""
    text = event.message.text
    reply_token = event.reply_token
    user_id = event.source.user_id
    if text == '目前有哪些共乘（已有司機）？':
        activities_status, error = activity_controller.return_valid_driver_activity()
        if error:
            line_service.reply_text(reply_token, '伺服器維修中！')
        elif activities_status == 'full':
            line_service.reply_text(reply_token, line_view.ERROR_DRIVER_ACTIVITY_FULL)
        elif activities_status == 'empty':
            line_service.reply_text(reply_token, line_view.ERROR_NO_DRIVER_ACTIVITIES)
        else:    
            line_service.reply_template(reply_token, '目前有的共乘（司機揪團）', activities_status)

    elif text == '目前有哪些共乘（揪團）？':
        activities_status, error = activity_controller.return_valid_passenger_activity()
        if error:
            line_service.reply_text(reply_token, '伺服器維修中！')
        elif activities_status == 'full':
            line_service.reply_text(reply_token, line_view.ERROR_PASSENGER_ACTIVITY_FULL)
        elif activities_status == 'empty':
            line_service.reply_text(reply_token, line_view.ERROR_NO_PASSENGER_ACTIVITIES)
        else:
            line_service.reply_template(reply_token, '目前有的共乘（司機揪團）', activities_status)
    elif text == '我的預約':
        user_activities_status = activity_controller.return_user_all_reservations_carousel(user_id)
        if user_activities_status == 'None':
            line_service.reply_text(reply_token, line_view.ERROR_NOT_RESERVED)
        else:
            line_service.reply_template(reply_token, '目前預約的共乘活動', user_activities_status)

@line_handler.add(FollowEvent)
def handle_follow(event):
    """處理使用者追蹤事件"""
    reply_token = event.reply_token
    welcome_msg = line_view.format_welcome_message()
    line_service.reply_text(reply_token, welcome_msg)


@line_handler.add(PostbackEvent)
def handle_postback(event):
    """處理 Postback 事件"""
    data = event.postback.data
    reply_token = event.reply_token
    user_id = event.source.user_id
    
    # 取得使用者資料
    profile = line_service.get_user_profile(user_id)
    user = User(user_id=user_id, name=profile.display_name)
    
    # 查看司機活動詳細資訊
    if data.startswith('driver_Num_detail_'):
        index = int(data.replace('driver_Num_detail_', ''))
        message = activity_controller.format_driver_activity_detail(index)
        line_service.push_template(user_id, message)
    
    # 查看乘客活動詳細資訊
    elif data.startswith('passenger_Num_detail_'):
        index = int(data.replace('passenger_Num_detail_', ''))
        message = activity_controller.format_passenger_activity_detail(index)
        line_service.push_template(user_id, message)
    
    # 在一般查看司機資訊
    elif data.startswith('driver_info_'):
        index = int(data.replace('driver_info_', ''))
        message = activity_controller.return_driver_info(index)
        line_service.push_text(user_id, message)

    # 在已經預約模板查看司機揪團活動詳細資訊
    elif data.startswith('driver_Num_reserved_detail_'):
        index = int(data.replace('driver_Num_reserved_detail_', ''))
        message = activity_controller.return_driver_activity_detail_reserved(index)
        line_service.push_text(user_id, message)

    # 在已經預約模板查看乘客揪團活動詳細資訊
    elif data.startswith('passenger_Num_reserved_detail_'):
        index = int(data.replace('passenger_Num_reserved_detail_', ''))
        message = activity_controller.return_passenger_activity_detail_reserved(index)
        line_service.push_text(user_id, message)
        
    # 預約司機活動（乘客身份）
    elif data.startswith('reserve_driver_AsPassenger_'):
        index = int(data.replace('reserve_driver_AsPassenger_', ''))
        success, message = reservation_controller.reserve_driver_as_passenger(index, user)
        line_service.reply_text(reply_token, message)
    
    # 預約乘客活動（乘客身份）    
    elif data.startswith('reserve_passenger_AsPassenger_'):
        index = int(data.replace('reserve_passenger_AsPassenger_', ''))
        success, message = reservation_controller.reserve_passenger_as_passenger(index, user)
        line_service.reply_text(reply_token, message)
    
    # 預約乘客活動（司機身份）
    elif data.startswith('reserve_passenger_AsDriver_'):
        index = int(data.replace('reserve_passenger_AsDriver_', ''))
        success, message = reservation_controller.reserve_passenger_as_driver(index, user)
        line_service.reply_text(reply_token, message)

    # 取消司機活動預約(使用者為乘客)
    elif data.startswith('cancel_DriverActivity_AsPassenger_'):
        index = int(data.replace('cancel_DriverActivity_AsPassenger_', ''))
        success, message = reservation_controller.cancel_driver_reservation(index, user_id)
        line_service.reply_text(reply_token, message)

    # 取消乘客活動預約(使用者為司機)
    elif data.startswith('cancel_PassengerActivity_AsDriver_'):
        index = int(data.replace('cancel_PassengerActivity_AsDriver_', ''))
        success, message = reservation_controller.cancel_passenger_reservation(index, user_id)
        line_service.reply_text(reply_token, message)

    # 取消乘客活動預約(使用者為乘客)
    elif data.startswith('cancel_PassengerActivity_AsPassenger_'):
        index = int(data.replace('cancel_PassengerActivity_AsPassenger_', ''))
        success, message = reservation_controller.cancel_passenger_reservation(index, user_id)
        line_service.reply_text(reply_token, message)
    
    else:
        line_service.reply_text(reply_token, '未知的操作')



# ==================== 應用程式初始化 ====================

def initialize_app():
    """初始化應用程式"""
    print("=" * 50)
    print("初始化共乘阿穿 LINE Bot (MVC 架構)")
    print("=" * 50)
    
    # 載入初始資料
    print("\n[1/2] 載入試算表資料...")
    from models.repository import repository
    repository.refresh_driver_activities()
    repository.refresh_passenger_activities()
    
    driver_count = len(repository.get_all_driver_activities())
    passenger_count = len(repository.get_all_passenger_activities())
    
    print(f"✓ 已載入 {driver_count} 筆司機活動")
    print(f"✓ 已載入 {passenger_count} 筆乘客活動")
    
    # 啟動通知排程器
    print("\n[2/2] 啟動通知排程器...")
    notification_controller.start_scheduler()
    print("✓ 排程器已啟動")
    
    print("\n" + "=" * 50)
    print("初始化完成！")
    print("架構: Model-View-Controller (MVC)")
    print("=" * 50 + "\n")


# ==================== 主程式入口 ====================

if __name__ == "__main__":
    # 初始化應用
    initialize_app()
    
    # 取得埠號
    port = int(os.environ.get("PORT", 5000))
    
    # 啟動 Flask 應用
    print(f"啟動 Flask 應用，埠號：{port}\n")
    app.run(host="0.0.0.0", port=port)
