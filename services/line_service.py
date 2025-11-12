"""
Services - LINE Bot 服務層
封裝 LINE Bot API 的底層操作
"""
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer
)
from config import CHANNEL_ACCESS_TOKEN


class LineService:
    """LINE Bot 服務 - 封裝 LINE API"""
    
    def __init__(self):
        self.configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
    
    def get_user_profile(self, user_id: str):
        """
        取得使用者資料
        
        Args:
            user_id: 使用者 ID
            
        Returns:
            使用者資料物件（包含 display_name 等）
        """
        with ApiClient(self.configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            return line_bot_api.get_profile(user_id)
    
    def reply_text(self, reply_token: str, text: str):
        """
        回覆文字訊息
        
        Args:
            reply_token: 回覆 token
            text: 訊息內容
        """
        with ApiClient(self.configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=text)]
                )
            )
    
    def reply_template(self, reply_token: str, alt_text: str, contents):
        """
        回覆模板訊息
        
        Args:
            reply_token: 回覆 token
            alt_text: 替代文字
            template: 模板物件
        """
        with ApiClient(self.configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[FlexMessage(alt_text = alt_text, contents = FlexContainer.from_json(contents))]
                )
            )

    def push_text(self, to: str, text: str):
        """
        推送文字訊息
        
        Args:
            to: 接收者 ID
            text: 訊息內容
        """
        with ApiClient(self.configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message(
                PushMessageRequest(
                    to=to,
                    messages=[TextMessage(text=text)]
                )
            )
    
    def push_template(self, to: str, template):
        """
        推送模板訊息
        
        Args:
            to: 接收者 ID
            alt_text: 替代文字
            template: 模板物件
        """
        with ApiClient(self.configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.push_message(
                PushMessageRequest(
                    to=to,
                    messages=[template]
                )
            )


# 全局單例
line_service = LineService()
