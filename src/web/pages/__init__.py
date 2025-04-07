"""
页面对象模块。

本模块封装了Web UI的页面和组件，使用页面对象模式将UI元素和操作封装为类。
"""

import logging
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

# 移除对旧 BasePage, Component 的导入
# from src.web.pages.base_page import BasePage, Component
from src.web.driver import WebDriver
from src.web.element import WebElement
from src.core.base.page import CompositePage # 导入核心 CompositePage
from src.core.base.errors import ElementNotFoundError # 导入异常

# 移除 NavigationBar 的导入
# from src.web.pages.dashboard_page import DashboardPage, NavigationBar
from src.web.pages.dashboard_page import DashboardPage
from src.web.pages.omp_login_page import OmpLoginPage

__all__ = [
    'DashboardPage',
    # 移除 NavigationBar 的导出
    # 'NavigationBar',
    'OmpLoginPage',
] 