from __future__ import annotations
from typing import Any, List, Optional
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from src.core.base.driver import BaseDriver
from src.utils.log.manager import get_logger
from src.core.base.errors import ElementNotFoundError, DriverError

class PlaywrightDriverAdapter(BaseDriver):
    """
    Playwright异步驱动适配器，实现BaseDriver接口。
    支持元素查找、等待、截图等常用自动化操作。
    """

    def __init__(
        self,
        page: Optional[Page] = None,
        browser_type: str = "chromium",
        headless: bool = True
    ):
        """
        初始化Playwright驱动。

        Args:
            page: 已有的Page实例（如pytest-playwright fixture注入）
            browser_type: 浏览器类型（chromium/firefox/webkit）
            headless: 是否无头模式
        """
        self.browser_type = browser_type
        self.headless = headless
        self.logger = get_logger(self.__class__.__name__)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = page  # 支持直接注入Page实例

    async def start(self, url: str) -> None:
        """
        启动浏览器并打开指定页面（如未注入page时使用）。

        Args:
            url: 目标页面URL

        Raises:
            DriverError: 启动失败
        """
        try:
            self.playwright = await async_playwright().start()
            browser_launcher = getattr(self.playwright, self.browser_type)
            self.browser = await browser_launcher.launch(headless=self.headless)
            self.context = await self.browser.new_context()
            self.page = await self.context.new_page()
            await self.page.goto(url)
            self.logger.info(f"浏览器已启动并打开: {url}")
        except Exception as e:
            self.logger.error(f"启动浏览器失败: {e}", exc_info=True)
            raise DriverError(f"启动浏览器失败: {e}")

    async def get_element(self, selector: str) -> Optional[Any]:
        """
        获取单个元素。

        Args:
            selector: 元素选择器

        Returns:
            Optional[Any]: 元素对象或None
        """
        if not self.page:
            raise DriverError("Page未初始化")
        el = await self.page.query_selector(selector)
        if not el:
            self.logger.warning(f"未找到元素: {selector}")
        return el

    async def get_elements(self, selector: str) -> List[Any]:
        """
        获取所有匹配的元素。

        Args:
            selector: 元素选择器

        Returns:
            List[Any]: 元素对象列表
        """
        if not self.page:
            raise DriverError("Page未初始化")
        return await self.page.query_selector_all(selector)

    async def wait_for_element(self, selector: str, timeout: float = 10) -> None:
        """
        等待元素出现。

        Args:
            selector: 元素选择器
            timeout: 超时时间（秒）

        Raises:
            ElementNotFoundError: 元素未找到
        """
        if not self.page:
            raise DriverError("Page未初始化")
        try:
            await self.page.wait_for_selector(selector, timeout=timeout * 1000)
            self.logger.info(f"元素已出现: {selector}")
        except Exception as e:
            self.logger.error(f"等待元素失败: {selector}, 错误: {e}")
            raise ElementNotFoundError(f"等待元素失败: {selector}, 错误: {e}")

    async def has_element(self, selector: str) -> bool:
        """
        判断元素是否存在。

        Args:
            selector: 元素选择器

        Returns:
            bool: 是否存在
        """
        if not self.page:
            raise DriverError("Page未初始化")
        el = await self.page.query_selector(selector)
        exists = el is not None
        self.logger.debug(f"元素是否存在: {selector} -> {exists}")
        return exists

    async def get_screenshot_as_bytes(self) -> bytes:
        """
        获取当前页面截图（二进制）。

        Returns:
            bytes: 截图内容

        Raises:
            DriverError: 截图失败
        """
        if not self.page:
            raise DriverError("Page未初始化")
        try:
            screenshot = await self.page.screenshot()
            self.logger.info("截图成功")
            return screenshot
        except Exception as e:
            self.logger.error(f"截图失败: {e}")
            raise DriverError(f"截图失败: {e}")

    async def close(self) -> None:
        """
        关闭浏览器和上下文。
        """
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.logger.info("浏览器已关闭")