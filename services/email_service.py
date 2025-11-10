"""
Services - Email 服務層
封裝郵件發送的底層操作
"""
import smtplib
from email.mime.text import MIMEText
from config import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD


class EmailService:
    """Email 服務 - 封裝郵件發送"""
    
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.smtp_user = SMTP_USER
        self.smtp_password = SMTP_PASSWORD
    
    def send_email(self, to_email: str, subject: str, body_html: str) -> bool:
        """
        發送郵件
        
        Args:
            to_email: 收件人信箱
            subject: 郵件主旨
            body_html: HTML 格式的郵件內容
            
        Returns:
            成功返回 True，失敗返回 False
        """
        try:
            # 建立郵件
            msg = MIMEText(body_html, 'html')
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # 發送郵件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f'郵件已發送至 {to_email}')
            return True
            
        except Exception as e:
            print(f'發送郵件失敗: {e}')
            return False


# 全局單例
email_service = EmailService()
