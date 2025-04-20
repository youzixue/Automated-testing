"""
页面对象模块。

本模块封装了Web UI的页面和组件，使用页面对象模式将UI元素和操作封装为类。
"""

from src.web.pages.dashboard_page import DashboardPage
from src.web.pages.login_page import OmpLoginPage

__all__ = [
    'DashboardPage',
    'OmpLoginPage',
] 