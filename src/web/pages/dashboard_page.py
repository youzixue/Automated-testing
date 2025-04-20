from __future__ import annotations
from typing import List, Optional
from src.core.base.driver import BaseDriver
from src.utils.log.manager import get_logger
from src.core.base.errors import ElementNotFoundError

class DashboardPage:
    """仪表盘页面对象，封装欢迎语、导航栏、统计卡片等核心元素和操作。"""

    # 元素定位符
    USERNAME_TEXT = ".user .name"  # 用户名显示
    SIDEBAR_MENU = ".el-menu"
    MAIN_CARD = ".main-card, .dashboard-card"
    QUICK_ENTRY = ".quick-entry, .dashboard-quick-entry"
    WELCOME_MESSAGE = ".welcome-message"
    LOGOUT_BUTTON = ".logout-btn"

    def __init__(self, driver: BaseDriver):
        self.driver = driver
        self.logger = get_logger(self.__class__.__name__)

    async def is_logged_in(self, expected_username: Optional[str] = None) -> bool:
        """
        判断是否已登录成功（用户名和侧边栏可见）。
        Args:
            expected_username: 期望用户名
        Returns:
            bool: 是否已登录
        """
        self.logger.info(f"[is_logged_in] 检查登录状态，期望用户名: {expected_username}")
        try:
            user_ok = await self.driver.has_element(self.USERNAME_TEXT)
            menu_ok = await self.driver.has_element(self.SIDEBAR_MENU)
            self.logger.debug(f"[is_logged_in] user_ok={user_ok}, menu_ok={menu_ok}")
            if not user_ok or not menu_ok:
                self.logger.warning("[is_logged_in] 用户名或侧边栏元素未找到，判定未登录")
                return False
            if expected_username:
                el = await self.driver.get_element(self.USERNAME_TEXT)
                if not el:
                    self.logger.error("[is_logged_in] 未找到用户名元素")
                    raise ElementNotFoundError("未找到用户名元素")
                username = await el.inner_text()
                self.logger.info(f"[is_logged_in] 页面用户名: {repr(username.strip())}, 期望: {repr(expected_username)}")
                result = username.strip() == expected_username
                if not result:
                    self.logger.warning(f"[is_logged_in] 用户名不匹配: 实际={username.strip()}, 期望={expected_username}")
                return result
            self.logger.info("[is_logged_in] 登录状态判定为已登录")
            return True
        except Exception as e:
            self.logger.warning(f"Dashboard登录状态检测失败: {e}")
            return False

    async def wait_until_logged_in(self, expected_username: Optional[str] = None, timeout: float = 10) -> DashboardPage:
        """
        等待登录成功（用户名和侧边栏可见）。
        Args:
            expected_username: 期望用户名
            timeout: 超时时间
        Returns:
            DashboardPage: self
        Raises:
            ElementNotFoundError: 未找到关键元素
        """
        self.logger.info(f"[wait_until_logged_in] 等待登录，期望用户名: {expected_username}, 超时: {timeout}s")
        await self.driver.wait_for_element(self.USERNAME_TEXT, timeout=timeout)
        await self.driver.wait_for_element(self.SIDEBAR_MENU, timeout=timeout)
        if expected_username:
            el = await self.driver.get_element(self.USERNAME_TEXT)
            if not el:
                self.logger.error("[wait_until_logged_in] 未找到用户名元素")
                raise ElementNotFoundError("未找到用户名元素")
            username = await el.inner_text()
            self.logger.info(f"[wait_until_logged_in] 页面用户名: {repr(username.strip())}, 期望: {repr(expected_username)}")
            assert username.strip() == expected_username, f"用户名断言失败: 期望{expected_username}, 实际{username}"
        self.logger.info("[wait_until_logged_in] 登录成功")
        return self

    async def get_welcome_message(self) -> str:
        """
        获取欢迎语内容。
        Returns:
            str: 欢迎语
        Raises:
            ElementNotFoundError: 未找到欢迎语元素
        """
        self.logger.info("[get_welcome_message] 获取欢迎语内容")
        el = await self.driver.get_element(self.WELCOME_MESSAGE)
        if not el:
            self.logger.error("[get_welcome_message] 未找到欢迎语元素")
            raise ElementNotFoundError("未找到欢迎语元素")
        msg = await el.inner_text()
        self.logger.info(f"[get_welcome_message] 欢迎语内容: {msg}")
        return msg

    async def click_logout(self) -> None:
        """
        点击退出登录按钮。
        Raises:
            ElementNotFoundError: 未找到退出按钮
        """
        self.logger.info("[click_logout] 尝试点击退出按钮")
        el = await self.driver.get_element(self.LOGOUT_BUTTON)
        if not el:
            self.logger.error("[click_logout] 未找到退出按钮")
            raise ElementNotFoundError("未找到退出按钮")
        await el.click()
        self.logger.info("[click_logout] 已点击退出按钮")

    async def get_sidebar_menus(self) -> List[str]:
        """
        获取侧边栏所有菜单项文本。
        Returns:
            List[str]: 菜单项文本列表
        Raises:
            ElementNotFoundError: 未找到菜单项
        """
        self.logger.info("[get_sidebar_menus] 获取侧边栏菜单项")
        elements = await self.driver.get_elements(f"{self.SIDEBAR_MENU} .el-menu-item")
        if not elements:
            self.logger.error("[get_sidebar_menus] 未找到侧边栏菜单项")
            raise ElementNotFoundError("未找到侧边栏菜单项")
        texts = [await el.inner_text() for el in elements]
        self.logger.info(f"[get_sidebar_menus] 菜单项: {texts}")
        return texts

    async def get_main_cards(self) -> List[str]:
        """
        获取主要统计卡片内容。
        Returns:
            List[str]: 卡片内容列表
        Raises:
            ElementNotFoundError: 未找到卡片
        """
        self.logger.info("[get_main_cards] 获取主要统计卡片内容")
        elements = await self.driver.get_elements(self.MAIN_CARD)
        if not elements:
            self.logger.error("[get_main_cards] 未找到主要统计卡片")
            raise ElementNotFoundError("未找到主要统计卡片")
        texts = [await el.inner_text() for el in elements]
        self.logger.info(f"[get_main_cards] 卡片内容: {texts}")
        return texts

    async def get_quick_entries(self) -> List[str]:
        """
        获取快捷入口内容。
        Returns:
            List[str]: 快捷入口内容列表
        Raises:
            ElementNotFoundError: 未找到快捷入口
        """
        self.logger.info("[get_quick_entries] 获取快捷入口内容")
        elements = await self.driver.get_elements(self.QUICK_ENTRY)
        if not elements:
            self.logger.error("[get_quick_entries] 未找到快捷入口")
            raise ElementNotFoundError("未找到快捷入口")
        texts = [await el.inner_text() for el in elements]
        self.logger.info(f"[get_quick_entries] 快捷入口内容: {texts}")
        return texts