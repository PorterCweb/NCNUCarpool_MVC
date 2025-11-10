"""
Views 模組初始化
"""
from .line_view import LineMessageView, line_view
from .email_view import EmailMessageView, email_view

__all__ = [
    'LineMessageView',
    'line_view',
    'EmailMessageView',
    'email_view'
]
