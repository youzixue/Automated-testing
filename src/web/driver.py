"""
Web驱动实现模块.

基于核心抽象层接口，实现Web驱动相关功能，遵循资源自动释放原则.
"""

import os
import logging
from typing import Optional, Dict, Any, List, Union, cast, ForwardRef
import time
import re
from pathlib import Path

from playwright.sync_api import sync_playwright, Browser, Page, Playwright, BrowserContext, ElementHandle, Locator, TimeoutError as PlaywrightTimeoutError
from src.core.base.driver import BaseDriver
from src.core.base.errors import (
    ResourceError, DriverError, NavigationError, TimeoutError,
    ElementNotFoundError, DriverInitError, DriverNotStartedError,
    ElementNotInteractableError, ElementNotVisibleError
)
from src.utils.config.manager import get_config
from src.web.wait import PlaywrightWaitStrategy
from src.core.base.conditions import ElementState
from src.core.base.wait import WaitStrategy
from src.utils.error_handling import convert_exceptions

# 获取配置管理器实例
web_config = get_config().get("web", {}) # 直接调用 get_config()

# 解决循环导入问题
# 保留 ForwardRef 定义，但后续主要使用 WebElementImpl
if "WebElement" not in globals():
    WebElement = ForwardRef('WebElement')

# Import WebElement from its module after resolving potential circular dependency
from src.web.element import WebElement as WebElementImpl

class WebDriver(BaseDriver):
    """Web驱动实现.

    基于Playwright实现的Web驱动，支持资源自动释放.
    使用上下文管理器确保资源正确释放，防止资源泄漏.

    Attributes:
        browser_type: 浏览器类型 ("chromium", "firefox", "webkit")
        headless: 是否无头模式运行
        browser_options: 浏览器配置选项
    """

    def __init__(self, browser_type: str = "chromium", headless: bool = True, wait_strategy: Optional[PlaywrightWaitStrategy] = None, **kwargs):
        """初始化WebDriver.

        Args:
            browser_type: 浏览器类型，支持"chromium", "firefox", "webkit"
            headless: 是否使用无头模式
            wait_strategy: 等待策略，如果为None则创建默认策略
            **kwargs: 其他浏览器选项
        """
        # 直接使用 self._wait_strategy 初始化, 传递 None 给 super()
        # 在这里创建 PlaywrightWaitStrategy，但在 __enter__ 中设置 page
        self._wait_strategy: PlaywrightWaitStrategy = wait_strategy or PlaywrightWaitStrategy(page=None)
        super().__init__(self._wait_strategy) # 传递创建的策略给父类

        self._logger = logging.getLogger(self.__class__.__name__)
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._page: Optional[Page] = None
        self._context: Optional[BrowserContext] = None
        self._is_closed: bool = False # 跟踪 stop() 是否已被调用

        self._logger.debug(f"WebDriver初始化: {browser_type}, 无头模式: {headless}, 选项: {kwargs}")

        self.browser_type = browser_type.lower()
        self.headless = headless
        self.browser_options = kwargs

        # 确认浏览器类型有效
        if self.browser_type not in ["chromium", "firefox", "webkit"]:
            self._logger.error(f"不支持的浏览器类型: {browser_type}")
            raise ValueError(f"不支持的浏览器类型: {browser_type}，支持类型: chromium, firefox, webkit")

    def __enter__(self) -> 'WebDriver':
        """上下文管理器入口，启动浏览器并准备资源.

        Returns:
            WebDriver: 自身实例

        Raises:
            DriverInitError: 浏览器初始化失败
        """
        if self._is_closed: # 如果已关闭，则阻止重新进入
            raise DriverError("WebDriver实例已被关闭，无法重新进入上下文")
        if self._playwright is not None: # 如果已启动，则阻止重新进入
             self._logger.warning("WebDriver已启动，重复进入上下文")
             return self

        self._logger.info(f"启动{self.browser_type}浏览器 (上下文管理器入口)")
        try:
            # 1. 启动Playwright
            self._playwright = sync_playwright().start()
            self._logger.debug("Playwright实例已创建")

            # 2. 获取浏览器实例
            browser_launcher = getattr(self._playwright, self.browser_type)
            launch_options = {
                'headless': self.headless
            }
            # 合并用户提供的浏览器选项
            launch_options.update(self.browser_options)

            self._browser = browser_launcher.launch(**launch_options)
            self._logger.debug(f"{self.browser_type}浏览器已启动")

            # 3. 创建浏览器上下文
            self._context = self._browser.new_context()
            self._logger.debug("浏览器上下文已创建")

            # 4. 创建页面
            self._page = self._context.new_page()
            self._logger.debug("浏览器页面已创建")

            # 页面存在后，设置等待策略的页面对象
            if isinstance(self._wait_strategy, PlaywrightWaitStrategy):
                self._wait_strategy.set_page(self._page)
            else:
                 # 如果意外使用了其他类型的等待策略，记录警告
                 self._logger.warning(f"使用了非PlaywrightWaitStrategy类型的等待策略: {type(self._wait_strategy)}. 页面对象未设置.")

            # 设置页面事件监听器
            self._setup_page_listeners()

            self._logger.info(f"{self.browser_type}浏览器启动成功")
            self._is_closed = False # 标记为活动状态
            return self
        except Exception as e:
            self._logger.error(f"浏览器启动失败: {e}", exc_info=True)
            # 确保在启动失败时也清理资源
            self.__exit__(type(e), e, e.__traceback__) # 调用 exit 进行清理
            # 包装异常为DriverInitError
            raise DriverInitError(f"浏览器启动失败: {e}") from e

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """上下文管理器退出，停止浏览器并释放资源.

        无论执行过程中是否发生异常，都确保释放所有资源.

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常回溯

        Raises:
             DriverError: 如果关闭过程中发生错误
        """
        self._logger.info("停止WebDriver (上下文管理器退出)")

        # 如果已关闭，则直接返回，避免重复关闭
        if self._is_closed:
            self._logger.debug("WebDriver已经关闭，跳过重复关闭")
            return

        original_exception = None
        try:
            # 关闭过程按照资源获取的相反顺序进行
            if self._page:
                self._logger.debug("关闭页面")
                try:
                    self._page.close()
                except Exception as page_close_err:
                    self._logger.error(f"关闭页面时发生错误: {page_close_err}", exc_info=True)
                    original_exception = original_exception or page_close_err # 保留第一个错误
                self._page = None

            if self._context:
                self._logger.debug("关闭浏览器上下文")
                try:
                    self._context.close()
                except Exception as context_close_err:
                     self._logger.error(f"关闭浏览器上下文时发生错误: {context_close_err}", exc_info=True)
                     original_exception = original_exception or context_close_err
                self._context = None

            if self._browser:
                self._logger.debug("关闭浏览器")
                try:
                    self._browser.close()
                except Exception as browser_close_err:
                     self._logger.error(f"关闭浏览器时发生错误: {browser_close_err}", exc_info=True)
                     original_exception = original_exception or browser_close_err
                self._browser = None

            if self._playwright:
                self._logger.debug("关闭Playwright实例")
                try:
                    self._playwright.stop()
                except Exception as playwright_stop_err:
                     self._logger.error(f"关闭Playwright实例时发生错误: {playwright_stop_err}", exc_info=True)
                     original_exception = original_exception or playwright_stop_err
                self._playwright = None

            self._is_closed = True
            self._logger.info("WebDriver已成功关闭")

            if original_exception:
                 # 重新引发清理过程中遇到的第一个异常
                 raise DriverError(f"关闭WebDriver时发生错误: {original_exception}") from original_exception

        except Exception as e:
            # 捕获 __exit__ 内部逻辑的意外错误
            self._logger.error(f"关闭WebDriver时发生意外错误: {e}", exc_info=True)
            self._is_closed = True # 即使出错也要确保状态为关闭
            # 如果存在外部异常 (exc_type)，让它传播。
            # 否则，引发清理错误。
            if exc_type is None:
                 raise DriverError(f"关闭WebDriver时发生意外错误: {e}") from e

    def _ensure_page(self) -> Page:
        """确保页面对象存在且未关闭, 返回页面对象"""
        if self._is_closed or not self._page:
            self._logger.error("浏览器或页面未启动或已关闭")
            raise DriverNotStartedError("浏览器或页面未启动或已关闭")
        return self._page

    def _setup_page_listeners(self):
        """设置页面事件监听器.

        添加页面事件处理, 如控制台消息, 页面错误等.
        """
        page = self._ensure_page()

        # 监听控制台消息
        page.on("console", lambda msg:
            self._logger.debug(f"浏览器控制台 [{msg.type}]: {msg.text}")
        )

        # 监听页面错误
        page.on("pageerror", lambda err:
            self._logger.warning(f"页面错误: {err}")
        )

        # 可以添加更多监听器...

    @convert_exceptions(NavigationError)
    def navigate(self, url: str) -> None:
        """导航到指定URL.

        导航超时应由全局或页面等待策略控制.

        Args:
            url: 目标URL

        Raises:
            NavigationError: 导航失败
            DriverNotStartedError: 驱动未启动
        """
        self._logger.info(f"导航到URL: {url}")
        page = self._ensure_page()
        page.goto(url) # Playwright goto 有内置的加载状态等待

    @convert_exceptions(NavigationError)
    def refresh(self) -> None:
        """刷新当前页面.

        Raises:
            NavigationError: 刷新失败
            DriverNotStartedError: 驱动未启动
        """
        self._logger.info("刷新页面")
        page = self._ensure_page()
        page.reload() # Playwright reload 有内置等待

    @convert_exceptions(NavigationError)
    def go_back(self) -> None:
        """返回上一页.

        Raises:
            NavigationError: 返回失败
            DriverNotStartedError: 驱动未启动
        """
        self._logger.info("导航: 返回上一页")
        page = self._ensure_page()
        page.go_back() # Playwright go_back 有内置等待

    @convert_exceptions(NavigationError)
    def go_forward(self) -> None:
        """前进到下一页.

        Raises:
            NavigationError: 前进失败
            DriverNotStartedError: 驱动未启动
        """
        self._logger.info("导航: 前进到下一页")
        page = self._ensure_page()
        page.go_forward() # Playwright go_forward 有内置等待

    @convert_exceptions(ElementNotFoundError)
    def get_element(self, selector: str) -> WebElementImpl:
        """获取元素.

        Args:
            selector: 元素选择器

        Returns:
            WebElement实例

        Raises:
            ElementNotFoundError: 元素未找到
            DriverNotStartedError: 驱动未启动
        """
        self._logger.debug(f"查找元素: {selector}")
        page = self._ensure_page()
        locator = page.locator(selector)

        # 快速检查元素是否存在 (locator.count() 很快)
        if locator.count() == 0:
             self._logger.warning(f"使用选择器未找到元素: {selector}")
             raise ElementNotFoundError(f"使用选择器未找到元素: {selector}")

        # 返回包装了 locator 的 WebElement
        return WebElementImpl(locator, self, self._wait_strategy)

    @convert_exceptions(ElementNotFoundError)
    def get_elements(self, selector: str) -> List[WebElementImpl]:
        """获取匹配的所有元素.

        Args:
            selector: 元素选择器

        Returns:
            WebElement实例列表

        Raises:
            ElementNotFoundError: 没有找到任何元素
            DriverNotStartedError: 驱动未启动
        """
        self._logger.debug(f"查找所有元素: {selector}")
        page = self._ensure_page()
        locator = page.locator(selector)
        count = locator.count()

        if count == 0:
             self._logger.warning(f"使用选择器未找到任何元素: {selector}")
             raise ElementNotFoundError(f"使用选择器未找到任何元素: {selector}")

        # 为找到的每个元素创建 WebElement 实例列表
        elements = [WebElementImpl(locator.nth(i), self, self._wait_strategy) for i in range(count)]
        self._logger.debug(f"找到 {len(elements)} 个元素: {selector}")
        return elements

    def has_element(self, selector: str) -> bool:
        """检查是否存在指定元素.

        Args:
            selector: 元素选择器

        Returns:
            元素是否存在

        Raises:
            DriverNotStartedError: 驱动未启动
        """
        self._logger.debug(f"检查元素是否存在: {selector}")
        try:
            page = self._ensure_page()
            # locator.count() 对于存在性检查很高效
            return page.locator(selector).count() > 0
        except DriverNotStartedError:
            raise # 重新引发特定错误
        except Exception as e:
            # 记录其他意外错误但返回 False
            self._logger.error(f"检查元素 {selector} 时发生意外错误: {e}", exc_info=True)
            return False

    @convert_exceptions(TimeoutError)
    def wait_for_element(self,
                         selector: str,
                         timeout: Optional[float] = None,
                         state: ElementState = ElementState.VISIBLE) -> WebElementImpl:
        """等待元素达到指定状态.

        Args:
            selector: 元素选择器
            timeout: 超时时间(秒)，None表示使用默认超时时间
            state: 等待的状态 (使用 ElementState 枚举)

        Returns:
            WebElement实例

        Raises:
            TimeoutError: 在指定时间内未达到状态
            ElementNotFoundError: 选择器未匹配到任何元素 (可能在状态检查前)
            DriverNotStartedError: 驱动未启动
        """
        self._logger.info(f"等待元素: {selector}, 状态: {state.name}, 超时: {timeout}")
        page = self._ensure_page()

        # 将 ElementState 转换为 ElementCondition (假设存在简单映射)
        try:
            condition = ElementCondition[state.name] # 按名称简单映射
        except KeyError:
             raise ValueError(f"不支持的等待状态到条件的转换: {state}")

        # 使用等待策略的 wait_for 方法
        try:
            locator = self._wait_strategy.wait_for(
                selector=selector,
                condition=condition,
                timeout=timeout
            )
            # 将返回的 locator 包装在 WebElement 中
            return WebElementImpl(locator, self, self._wait_strategy)
        except TimeoutError as e: # 捕获框架的 TimeoutError
            self._logger.warning(f"等待元素 {selector} 达到状态 {state.name} 超时: {e}")
            raise # 重新引发框架的 TimeoutError
        except Exception as e:
             # 捕获其他潜在错误 (例如, 来自 wait_for 的 ValueError)
             self._logger.error(f"等待元素 {selector} 时发生错误: {e}", exc_info=True)
             # 如果需要，包装在更通用的错误中重新引发，或根据类型特定处理
             raise DriverError(f"等待元素 {selector} 时发生错误: {e}") from e


    @convert_exceptions(TimeoutError)
    def wait_for_navigation(self, timeout: Optional[float] = None) -> None:
        """等待页面导航完成.

        Playwright 的页面操作 (goto, click, reload 等) 通常有隐式等待。
        此方法可用于基于 URL、加载状态等的显式等待。

        Args:
            timeout: 超时时间(秒)，None表示使用默认超时时间

        Raises:
            TimeoutError: 在指定时间内导航未完成
            DriverNotStartedError: 驱动未启动
        """
        page = self._ensure_page()
        actual_timeout = timeout if timeout is not None else self._wait_strategy._default_timeout
        actual_timeout_ms = actual_timeout * 1000 # 转换为毫秒

        self._logger.info(f"等待导航完成, 超时: {actual_timeout}秒")
        try:
            # 示例: 等待 'load' 状态
            # 其他选项: 'domcontentloaded', 'networkidle'
            page.wait_for_load_state(state='load', timeout=actual_timeout_ms)
            self._logger.debug("页面加载状态 'load' 已达到")
        except PlaywrightTimeoutError as e:
            self._logger.warning(f"等待导航完成超时 ({actual_timeout}秒)")
            raise TimeoutError(f"等待导航完成超时 ({actual_timeout}秒)") from e

    @convert_exceptions(DriverError)
    def execute_script(self, script: str, *args: Any) -> Any:
        """执行JavaScript脚本.

        Args:
            script: JavaScript脚本
            *args: 传递给脚本的参数 (注意: Playwright的evaluate需要一个arg参数)

        Returns:
            脚本执行结果

        Raises:
            DriverError: 脚本执行失败
            DriverNotStartedError: 驱动未启动
        """
        self._logger.debug(f"执行JavaScript: {script[:50]}...")
        page = self._ensure_page()
        # Playwright 的 page.evaluate 接受 script 和一个可选的单个参数 `arg`
        # 如果传递了多个参数，我们可能需要调整传递方式或进行包装。
        # 为简单起见，假设如果存在 args 则使用 args[0]，或根据 args 长度处理。
        script_arg = args[0] if args else None
        try:
             result = page.evaluate(script, arg=script_arg)
             self._logger.debug(f"脚本执行结果: {result}")
             return result
        except Exception as e:
             self._logger.error(f"JavaScript执行失败: {e}", exc_info=True)
             raise DriverError(f"JavaScript执行失败: {e}") from e


    @convert_exceptions(DriverError)
    def get_current_url(self) -> str:
        """获取当前页面URL.

        Returns:
            当前页面URL

        Raises:
            DriverError: 获取URL失败
            DriverNotStartedError: 驱动未启动
        """
        page = self._ensure_page()
        url = page.url
        self._logger.debug(f"获取当前URL: {url}")
        return url

    @convert_exceptions(DriverError)
    def get_title(self) -> str:
        """获取当前页面标题.

        Returns:
            当前页面标题

        Raises:
            DriverError: 获取标题失败
            DriverNotStartedError: 驱动未启动
        """
        page = self._ensure_page()
        title = page.title()
        self._logger.debug(f"获取页面标题: {title}")
        return title

    @convert_exceptions(DriverError)
    def get_screenshot_as_bytes(self) -> bytes:
        """获取页面截图的二进制数据.

        Returns:
            截图的bytes数据

        Raises:
            DriverError: 获取截图失败
            DriverNotStartedError: 驱动未启动
        """
        self._logger.debug("获取页面截图 (bytes)")
        page = self._ensure_page()
        try:
            # 默认为 PNG
            screenshot_bytes = page.screenshot()
            return screenshot_bytes
        except Exception as e:
            self._logger.error(f"获取截图失败: {e}", exc_info=True)
            raise DriverError(f"获取截图失败: {e}") from e

    @property
    def wait_strategy(self) -> PlaywrightWaitStrategy:
        """获取当前驱动的等待策略."""
        # 类型检查以确保安全，尽管 __init__ 应该已保证
        if not isinstance(self._wait_strategy, PlaywrightWaitStrategy):
            raise TypeError("内部错误: 等待策略不是 PlaywrightWaitStrategy")
        return self._wait_strategy

    @convert_exceptions(DriverError)
    def get_cookies(self) -> List[Dict[str, Any]]:
        """获取所有cookies.

        Returns:
            包含cookie字典的列表

        Raises:
            DriverError: 获取cookies失败
            DriverNotStartedError: 驱动未启动
        """
        self._logger.debug("获取所有Cookies")
        context = self._ensure_context() # 需要 context 来获取 cookies
        try:
            cookies = context.cookies()
            self._logger.debug(f"获取到 {len(cookies)} 个Cookies")
            return cookies
        except Exception as e:
            self._logger.error(f"获取Cookies失败: {e}", exc_info=True)
            raise DriverError(f"获取Cookies失败: {e}") from e


    @convert_exceptions(DriverError)
    def add_cookie(self, cookie_dict: Dict[str, Any]) -> None:
        """添加单个cookie.

        Args:
            cookie_dict: 包含cookie信息的字典 (例如: {'name': 'foo', 'value': 'bar', 'domain': '.example.com', 'path': '/'})

        Raises:
            DriverError: 添加cookie失败
            DriverNotStartedError: 驱动未启动
        """
        self._logger.debug(f"添加Cookie: {cookie_dict.get('name')}")
        context = self._ensure_context()
        try:
            context.add_cookies([cookie_dict]) # add_cookies 期望一个列表
        except Exception as e:
             self._logger.error(f"添加Cookie失败: {e}", exc_info=True)
             raise DriverError(f"添加Cookie失败: {e}") from e

    @convert_exceptions(DriverError)
    def delete_cookie(self, name: str) -> None:
        """删除指定名称的cookie.

        Args:
            name: 要删除的cookie名称

        Raises:
            DriverError: 删除cookie失败
            DriverNotStartedError: 驱动未启动
        """
        self._logger.debug(f"删除Cookie: {name}")
        context = self._ensure_context()
        try:
            # Playwright 需要更具体的删除 (可能需要 domain/path)
            # 尝试清除匹配名称的 cookie - 如果 path/domain 不同，可能会移除超出预期的 cookie
            current_cookies = context.cookies()
            cookies_to_keep = [c for c in current_cookies if c['name'] != name]
            context.clear_cookies()
            if cookies_to_keep:
                context.add_cookies(cookies_to_keep)
            self._logger.debug(f"尝试删除名为 {name} 的Cookie")
        except Exception as e:
             self._logger.error(f"删除Cookie {name} 失败: {e}", exc_info=True)
             raise DriverError(f"删除Cookie {name} 失败: {e}") from e


    def delete_all_cookies(self) -> None:
        """删除所有Cookie。"""
        page = self._ensure_page()
        page.context.clear_cookies()
        self._logger.info("所有Cookie已删除")

    @convert_exceptions(DriverError)
    def get_cookie(self, name: str) -> Optional[Dict[str, Any]]:
        """获取指定名称的Cookie。

        Args:
            name: Cookie名称

        Returns:
            包含Cookie信息的字典，如果找不到则返回None
        """
        context = self._ensure_context()
        cookies = context.cookies()
        for cookie in cookies:
            if cookie.get('name') == name:
                self._logger.debug(f"找到Cookie: {name}")
                return cookie
        self._logger.debug(f"未找到Cookie: {name}")
        return None

    @property
    def page_source(self) -> str:
        """获取当前页面源代码.

        Returns:
            页面源代码 (HTML)

        Raises:
            DriverError: 获取源代码失败
            DriverNotStartedError: 驱动未启动
        """
        self._logger.debug("获取页面源代码")
        page = self._ensure_page()
        try:
            content = page.content()
            return content
        except Exception as e:
            self._logger.error(f"获取页面源代码失败: {e}", exc_info=True)
            raise DriverError(f"获取页面源代码失败: {e}") from e

    def switch_to_frame(self, frame_locator: Union[str, Locator, WebElementImpl]) -> None:
        """切换到指定的iframe.

        注意：Playwright 的 Frame 处理范式与 Selenium 不同。
        不直接 '切换' 上下文，而是获取 FrameLocator 并通过它与 Frame 内元素交互。
        此方法目前仅记录警告并引发 NotImplementedError。

        Args:
            frame_locator: iframe的选择器、Locator对象或WebElement实例

        Raises:
            NoSuchFrameError: 找不到指定的iframe
            DriverNotStartedError: 驱动未启动
            NotImplementedError: Playwright范式不同
        """
        page = self._ensure_page()
        target_locator: Optional[Locator] = None # 类型改为 Locator

        self._logger.warning("Playwright范式提醒: 不直接'切换'到Frame. 请使用FrameLocator与Frame内元素交互.")

        # 尝试确定 FrameLocator (但 Playwright sync API 有限)
        if isinstance(frame_locator, str):
            self._logger.info(f"尝试获取FrameLocator: {frame_locator}")
            # target_locator = page.frame_locator(frame_locator) # 这是正确的获取方式
        elif isinstance(frame_locator, Locator):
            # 假设传入的是 FrameLocator
             self._logger.info(f"假定传入的是FrameLocator: {frame_locator}")
             # target_locator = frame_locator
        elif isinstance(frame_locator, WebElementImpl):
             self._logger.info(f"尝试从WebElement获取FrameLocator: {frame_locator._get_selector_or_repr()}")
             raise NotImplementedError("通过WebElement切换Frame需要更具体的实现 (例如使用其选择器)")
        else:
             raise TypeError(f"不支持的Frame定位器类型: {type(frame_locator)}")

        # 由于不实际切换上下文，引发错误
        raise NotImplementedError("Playwright中Frame的切换模型不同于Selenium. 请使用FrameLocator进行交互.")


    def switch_to_default_content(self) -> None:
        """切换回主文档.

        在Playwright中，如果未使用特定的 FrameLocator，默认就在主文档上下文中操作。

        Raises:
            DriverNotStartedError: 驱动未启动
        """
        # 确保页面存在
        self._ensure_page()
        self._logger.info("切换回主文档内容 (在Playwright中通常是默认上下文)")
        # 无需显式操作，如果实现了上下文存储，在此重置。
        pass


    def switch_to_window(self, window_handle: str) -> None:
        """切换到指定句柄的窗口或标签页.

        在Playwright中，通常通过操作特定的 Page 对象来切换。
        此方法尝试根据句柄（假定为标题或索引）找到并切换 Page 上下文。

        Args:
            window_handle: 目标窗口的句柄 (尝试匹配页面标题或索引)

        Raises:
            NoSuchWindowError: 找不到指定句柄的窗口
            DriverNotStartedError: 驱动未启动
        """
        self._logger.warning("Playwright范式提醒: 窗口/标签页切换通过操作特定的Page对象完成.")
        context = self._ensure_context()
        pages = context.pages
        target_page: Optional[Page] = None

        # 尝试查找页面
        try:
            # 假定 window_handle 可能是索引 (不太可靠)
            handle_index = int(window_handle)
            if 0 <= handle_index < len(pages):
                target_page = pages[handle_index]
        except ValueError:
            # 假定 window_handle 可能是标题
            for p in pages:
                # 增加 None 检查
                page_title = p.title()
                if page_title and page_title == window_handle:
                    target_page = p
                    break

        if target_page:
            self._page = target_page # 更新当前页面上下文
            # 确保等待策略使用新的页面对象
            if isinstance(self._wait_strategy, PlaywrightWaitStrategy):
                 self._wait_strategy.set_page(target_page)
            self._logger.info(f"切换到页面: {target_page.title() or '[无标题]'}")
        else:
            raise NoSuchWindowError(f"找不到句柄为 '{window_handle}' 的窗口/页面")

    @property
    def window_handles(self) -> List[str]:
        """获取当前所有窗口/标签页的句柄.

        在Playwright上下文中，返回页面标题作为句柄。

        Returns:
            包含所有窗口句柄 (标题) 的列表

        Raises:
            DriverNotStartedError: 驱动未启动
        """
        context = self._ensure_context()
        # 返回页面标题作为句柄
        handles = [p.title() or f"[无标题_{i}]" for i, p in enumerate(context.pages)]
        self._logger.debug(f"获取窗口句柄 (标题): {handles}")
        return handles

    @property
    def current_window_handle(self) -> str:
        """获取当前窗口/标签页的句柄.

        Returns:
            当前窗口的句柄 (标题)

        Raises:
            DriverNotStartedError: 驱动未启动
        """
        page = self._ensure_page()
        # 增加 None 检查
        handle = page.title() or "[无标题]"
        self._logger.debug(f"获取当前窗口句柄 (标题): {handle}")
        return handle

    def maximize_window(self) -> None:
        """最大化当前窗口.

        Playwright 没有直接的最大化函数，尝试设置较大的视口尺寸。

        Raises:
            DriverNotStartedError: 驱动未启动
        """
        self._logger.warning("Playwright不支持直接最大化窗口. 将尝试设置较大的视口尺寸.")
        page = self._ensure_page()
        try:
             # 获取屏幕尺寸 (需要 JS 执行) - 可能需要特定于浏览器的方式
             # 目前设置一个较大的固定尺寸
             large_width = 1920
             large_height = 1080
             page.set_viewport_size({"width": large_width, "height": large_height})
             self._logger.info(f"设置视口尺寸为: {large_width}x{large_height}")
        except Exception as e:
             self._logger.error(f"设置视口尺寸时出错: {e}", exc_info=True)
             # 不引发错误，因为是变通方法

    def set_window_size(self, width: int, height: int) -> None:
        """设置窗口大小.

        Args:
            width: 窗口宽度
            height: 窗口高度

        Raises:
            DriverError: 设置窗口大小失败
            DriverNotStartedError: 驱动未启动
        """
        self._logger.info(f"设置窗口/视口尺寸: {width}x{height}")
        page = self._ensure_page()
        try:
             page.set_viewport_size({"width": width, "height": height})
        except Exception as e:
             self._logger.error(f"设置视口尺寸时出错: {e}", exc_info=True)
             raise DriverError(f"设置视口尺寸时出错: {e}") from e


    def close_window(self) -> None:
        """关闭当前窗口/标签页.

        如果这是最后一个窗口，通常会关闭浏览器.

        Raises:
            DriverError: 关闭窗口失败
            DriverNotStartedError: 驱动未启动
        """
        self._logger.info("关闭当前窗口/页面")
        page = self._ensure_page()
        try:
            current_page_title = page.title() # 获取标题用于日志
            page.close()
            self._logger.debug(f"页面 '{current_page_title}' 已关闭")
            # 关闭后，如果存在其他页面，需要更新 self._page
            context = self._ensure_context()
            if context.pages:
                 self._page = context.pages[-1] # 切换到最后一个可用页面
                 if isinstance(self._wait_strategy, PlaywrightWaitStrategy):
                     self._wait_strategy.set_page(self._page)
                 self._logger.info(f"切换到剩余页面: {self._page.title() or '[无标题]'}")
            else:
                 self._page = None
                 # 如果没有页面剩下，浏览器可能会隐式关闭，或者我们应该调用 __exit__?
                 # 假设上下文保持，直到 __exit__ 显式关闭
                 self._logger.warning("最后一个页面已关闭，浏览器上下文仍然存在，将在驱动退出时关闭。")

        except Exception as e:
             self._logger.error(f"关闭页面时出错: {e}", exc_info=True)
             raise DriverError(f"关闭页面时出错: {e}") from e


    def accept_alert(self) -> str:
        """接受当前弹出的警告框 (Alert).

        注意：Playwright 处理弹窗的范式不同，需要先注册监听器，再执行触发操作。
        此方法尝试接受已存在的弹窗（如果可能），但更推荐使用监听器模式。

        Returns:
            警告框的文本内容 (如果能获取到)

        Raises:
            NoAlertPresentError: 没有警告框弹出 (或无法处理已存在的)
            DriverNotStartedError: 驱动未启动
            NotImplementedError: Playwright范式不同，不保证能处理已存在弹窗
        """
        page = self._ensure_page()
        alert_text = "[未知文本]" # Default value

        # Playwright 推荐的模式是使用 page.on('dialog', ...)
        # 尝试处理已存在的弹窗比较困难且不可靠
        self._logger.warning("Playwright警告框处理范式: 需要先注册监听器，再执行触发操作。此方法尝试处理已存在弹窗，可能失败。")

        # 尝试使用 playwright-expect (如果安装了) 或 JS 执行来处理 (复杂)
        # 由于缺乏标准方法，引发错误
        raise NotImplementedError("Playwright中处理已存在的警告框需要不同的处理模式。请使用事件监听器。")


    def dismiss_alert(self) -> str:
        """取消当前弹出的警告框 (Alert).

        注意：Playwright 处理弹窗的范式不同。

        Returns:
            警告框的文本内容 (如果能获取到)

        Raises:
            NoAlertPresentError: 没有警告框弹出
            DriverNotStartedError: 驱动未启动
            NotImplementedError: Playwright范式不同，不保证能处理已存在弹窗
        """
        page = self._ensure_page()
        alert_text = "[未知文本]"

        self._logger.warning("Playwright警告框处理范式: 需要先注册监听器，再执行触发操作。此方法尝试处理已存在弹窗，可能失败。")
        raise NotImplementedError("Playwright中处理已存在的警告框需要不同的处理模式。请使用事件监听器。")


    def send_keys_to_alert(self, text: str) -> None:
        """向当前弹出的提示框 (Prompt) 输入文本.

        注意：Playwright 处理弹窗的范式不同。

        Args:
            text: 要输入的文本

        Raises:
            NoAlertPresentError: 没有提示框弹出
            DriverNotStartedError: 驱动未启动
            NotImplementedError: Playwright范式不同，不保证能处理已存在弹窗
        """
        page = self._ensure_page()

        self._logger.warning("Playwright提示框处理范式: 需要先注册监听器，再执行触发操作。此方法尝试处理已存在弹窗，可能失败。")
        raise NotImplementedError("Playwright中处理已存在的提示框需要不同的处理模式。请使用事件监听器。")


    # 辅助方法：确保上下文存在
    def _ensure_context(self) -> BrowserContext:
        """确保浏览器上下文存在且可用。"""
        if self._is_closed or not self._context:
            raise DriverNotStartedError("浏览器上下文不可用或驱动已关闭")
        return self._context

    # 显式实现 get_page_source 方法以满足抽象类要求
    @convert_exceptions(DriverError)
    def get_page_source(self) -> str:
        """获取当前页面源码。"""
        page = self._ensure_page()
        return page.content()

    # --- 实现缺失的抽象方法 (或已通过属性实现) --- #

    # 原有的 @property page_source 可以保留，或者移除（如果不再需要）
    # 保留 @property 可能会导致轻微的冗余，但也能工作
    @property
    def page_source(self) -> str:
        """获取当前页面源代码 (属性版本)。"""
        return self.get_page_source() # 委托给新添加的方法