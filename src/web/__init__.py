"""
Web自动化平台实现。

包含基于Playwright的WebElement、PageObject等实现。
"""

from src.web.driver_playwright_adapter import PlaywrightDriverAdapter
from src.web.pages.dashboard_page import DashboardPage
from src.web.pages.login_page import OmpLoginPage

__all__ = [
    'PlaywrightDriverAdapter',
    'DashboardPage',
    'OmpLoginPage',
]