"""
仪表盘页面对象。

展示页面对象模式在仪表盘场景中的实现，包含页面元素、操作以及组件封装。
"""

import logging
from typing import Optional, List, Any

from src.core.base.errors import ElementNotFoundError, TimeoutError
from src.web.driver import WebDriver
from src.web.element import WebElement
from src.core.base.page import CompositePage
from src.utils.config.manager import get_config


class DashboardPage(CompositePage[WebDriver, WebElement]):
    """仪表盘页面对象。
    
    封装仪表盘页面的元素和操作，作为登录成功后的页面验证和后续操作的入口。
    """
    
    def __init__(self, driver: WebDriver, url: Optional[str] = None):
        """初始化仪表盘页面对象。
        
        Args:
            driver: WebDriver实例
            url: 仪表盘页面URL
        """
        super().__init__(driver, driver.wait_strategy, url, title="仪表盘")
        
        # 从配置加载选择器
        config = get_config()
        dashboard_config = config.get("web", {}).get("dashboard", {})
        self._selectors = dashboard_config.get("selectors", {})
        self._logger.debug(f"加载到的 dashboard selectors: {self._selectors}")
    
    # 使用 @property 动态获取选择器
    @property
    def WELCOME_MESSAGE(self) -> str:
        return self._selectors.get("welcome_message")
        
    @property
    def USER_INFO(self) -> str:
        return self._selectors.get("user_info")
        
    @property
    def DASHBOARD_CONTENT(self) -> str:
        return self._selectors.get("dashboard_content")
        
    @property
    def NOTIFICATION_PANEL(self) -> str:
        return self._selectors.get("notification_panel")
        
    @property
    def HOME_LINK(self) -> str:
        return self._selectors.get("home_link")
        
    @property
    def PROFILE_LINK(self) -> str:
        return self._selectors.get("profile_link")
        
    @property
    def SETTINGS_LINK(self) -> str:
        return self._selectors.get("settings_link")
        
    @property
    def LOGOUT_BUTTON(self) -> str:
        return self._selectors.get("logout_button")
    
    def is_loaded(self) -> bool:
        """检查仪表盘页面是否已加载。
        
        通过验证欢迎信息元素的存在来确认页面已加载。
        
        Returns:
            页面是否已加载
        """
        try:
            welcome_element = self.get_element(self.WELCOME_MESSAGE)
            return welcome_element.is_visible()
        except ElementNotFoundError:
            return False
    
    def get_welcome_message(self) -> str:
        """获取欢迎信息文本。
        
        Returns:
            欢迎信息文本
            
        Raises:
            ElementNotFoundError: 欢迎信息元素未找到
        """
        welcome_element = self.get_element(self.WELCOME_MESSAGE)
        return welcome_element.get_text()
    
    def get_user_info(self) -> str:
        """获取用户信息文本。
        
        Returns:
            用户信息文本
            
        Raises:
            ElementNotFoundError: 用户信息元素未找到
        """
        user_info_element = self.get_element(self.USER_INFO)
        return user_info_element.get_text()
    
    def get_notifications(self) -> List[str]:
        """获取通知信息列表。
        
        Returns:
            通知信息文本列表
            
        Raises:
            ElementNotFoundError: 通知面板元素未找到
        """
        try:
            notification_elements = self.get_elements(f"{self.NOTIFICATION_PANEL} .notification, {self.NOTIFICATION_PANEL} .alert")
            return [element.get_text() for element in notification_elements]
        except ElementNotFoundError:
            return []
    
    def click_home(self) -> None:
        """点击首页链接。"""
        self._logger.debug("点击首页链接")
        home_link = self.get_element(self.HOME_LINK)
        home_link.click()
    
    def click_profile(self) -> None:
        """点击个人资料链接。"""
        self._logger.debug("点击个人资料链接")
        profile_link = self.get_element(self.PROFILE_LINK)
        profile_link.click()
    
    def click_settings(self) -> None:
        """点击设置链接。"""
        self._logger.debug("点击设置链接")
        settings_link = self.get_element(self.SETTINGS_LINK)
        settings_link.click()
    
    def click_logout(self) -> None:
        """点击登出按钮。
        
        Raises:
            ElementNotFoundError: 登出按钮未找到
            TimeoutError: 登出操作超时
        """
        self._logger.info("执行登出操作")
        logout_button = self.get_element(self.LOGOUT_BUTTON)
        logout_button.click()
        
        # 等待登出后的页面加载 - 使用 Driver 的方法
        # 等待登出后的页面加载
        self._driver.wait_for_navigation()
    
    @classmethod
    def open(cls, driver: WebDriver, url: str) -> 'DashboardPage':
        """打开仪表盘页面。
        
        Args:
            driver: WebDriver实例
            url: 仪表盘页面URL
            
        Returns:
            DashboardPage实例
            
        Raises:
            NavigationError: 导航失败
            TimeoutError: 页面加载超时
        """
        page = cls(driver, url)
        page.navigate()
        page.wait_until_loaded()
        return page 

    def wait_until_loaded(self, timeout: Optional[float] = None) -> 'DashboardPage':
        """等待仪表盘页面加载完成。

        Args:
            timeout: 超时时间(秒)，None表示使用默认超时时间

        Returns:
            当前页面对象(用于链式调用)

        Raises:
            TimeoutError: 在指定时间内页面未加载完成
        """
        self.logger.info(f"等待仪表盘页面加载... (超时: {timeout or self.wait.timeout} 秒)")
        try:
            # 使用 wait_until 等待 is_loaded 返回 True
            self.wait.wait_until(self.is_loaded, timeout=timeout, message="等待仪表盘页面加载超时")
            self.logger.info("仪表盘页面加载完成")
            return self
        except TimeoutError as e:
            self.logger.error(f"仪表盘页面加载失败: {e}")
            raise 