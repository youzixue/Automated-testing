"""
页面对象接口。

定义页面对象的基本结构和接口。
"""

from abc import ABC, abstractmethod
from typing import Type, TypeVar, Generic, Optional, Dict, Any
import logging
import functools # 确保导入
from urllib.parse import urlencode, urlparse, urlunparse, parse_qs # 移到顶部

from src.core.base.driver import BaseDriver
from src.core.base.element import BaseElement
from src.core.base.errors import AutomationError, PageError, ElementNotFoundError, NavigationError, TimeoutError
from src.core.base.mixins import NavigationMixin, ElementFinderMixin, ScreenshotMixin, JavaScriptMixin
from src.core.base.wait import WaitStrategy
from src.utils.error_handling import convert_exceptions

# 泛型类型定义
D = TypeVar('D', bound=BaseDriver)  # 驱动类型
E = TypeVar('E')  # 元素类型

class BasePage(Generic[D, E], ABC):
    """页面对象的基类。
    
    所有页面对象都应继承自此类，提供标准的页面操作接口。
    
    Attributes:
        driver: 浏览器驱动实例
        wait_strategy: 等待策略实例
        logger: 日志记录器
        url: 页面URL (Optional)
        title: 页面标题 (Optional)
    """
    
    def __init__(self, driver: D, wait_strategy: WaitStrategy[E], url: Optional[str] = None, title: Optional[str] = None):
        """初始化页面对象。
        
        Args:
            driver: 浏览器驱动实例
            wait_strategy: 等待策略实例
            url: 页面URL路径(相对或绝对) (Optional)
            title: 期望的页面标题，用于验证页面 (Optional)
        """
        self.driver = driver
        self.wait_strategy = wait_strategy
        self._url = url
        self._title = title
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @property
    def url(self) -> Optional[str]:
        """获取页面URL。
        
        Returns:
            页面URL
        """
        return self._url
    
    @url.setter
    def url(self, value: str) -> None:
        """设置页面URL。
        
        Args:
            value: 新的URL值
        """
        self._url = value
    
    @property
    def title(self) -> Optional[str]:
        """获取期望的页面标题。
        
        Returns:
            期望的页面标题
        """
        return self._title
    
    @title.setter
    def title(self, value: str) -> None:
        """设置期望的页面标题。
        
        Args:
            value: 新的标题值
        """
        self._title = value
    
    @abstractmethod
    @convert_exceptions(PageError)
    def navigate(self, params: Optional[Dict[str, Any]] = None) -> 'BasePage':
        """导航到当前页面。
        
        Args:
            params: URL参数(如果需要)
            
        Returns:
            当前页面对象(用于链式调用)
            
        Raises:
            NavigationError: 导航失败
        """
        pass
    
    @abstractmethod
    def is_loaded(self) -> bool:
        """检查页面是否已加载。
        
        通常通过检查特定元素是否存在或页面标题是否匹配来实现。
        
        Returns:
            页面是否已加载
        """
        pass
    
    @abstractmethod
    @convert_exceptions(TimeoutError)
    def wait_until_loaded(self, timeout: Optional[float] = None) -> 'BasePage':
        """等待页面加载完成。
        
        Args:
            timeout: 超时时间(秒)，None表示使用默认超时时间
            
        Returns:
            当前页面对象(用于链式调用)
            
        Raises:
            TimeoutError: 在指定时间内页面未加载完成
        """
        pass


class CompositePage(BasePage[D, E], NavigationMixin, ElementFinderMixin, ScreenshotMixin, JavaScriptMixin):
    """组合式页面对象。
    
    通过组合各种功能Mixin类，提供完整的页面操作功能，避免与驱动类的代码重复。
    
    这种设计使得页面对象可以专注于业务操作封装，而底层功能通过委托给驱动实现。
    """
    
    def __init__(self, driver: D, wait_strategy: WaitStrategy[E], url: Optional[str] = None, title: Optional[str] = None):
        """初始化组合式页面对象。
        
        Args:
            driver: 浏览器驱动实例
            wait_strategy: 等待策略
            url: 页面URL路径(相对或绝对)
            title: 期望的页面标题，用于验证页面
        """
        super().__init__(driver, wait_strategy, url, title)
        NavigationMixin.__init__(self, driver)
        ElementFinderMixin.__init__(self, driver)
        ScreenshotMixin.__init__(self, driver.get_screenshot_as_bytes)
        JavaScriptMixin.__init__(self, driver.execute_script)
    
    @convert_exceptions(PageError)
    def navigate(self, params: Optional[Dict[str, Any]] = None) -> 'CompositePage':
        """导航到当前页面。
        
        组合使用NavigationMixin的功能，并添加URL参数处理。
        
        Args:
            params: URL参数(如果需要)
            
        Returns:
            当前页面对象(用于链式调用)
            
        Raises:
            NavigationError: 导航失败
        """
        if not self._url:
            self.logger.error("无法导航：页面URL未设置")
            raise NavigationError("无法导航：页面URL未设置")
        
        # Initialize url with the base url
        url = self._url

        # 构建带参数的URL
        if params:
            # from urllib.parse import urlencode, urlparse, urlunparse, parse_qs # 从这里移除
            
            # 解析现有URL
            parsed_url = urlparse(self._url)
            query_params = parse_qs(parsed_url.query)
            
            # 更新参数 (新参数覆盖旧参数)
            for key, value in params.items():
                query_params[key] = value
            
            # 重新编码查询字符串
            new_query = urlencode(query_params, doseq=True)
            
            # 构建新URL
            url = urlunparse((parsed_url.scheme,
                              parsed_url.netloc,
                              parsed_url.path,
                              parsed_url.params,
                              new_query,
                              parsed_url.fragment))

        # 使用底层导航对象避免递归
        self._navigator.navigate(url)
        
        # 等待页面加载
        return self.wait_until_loaded()
    
    def is_loaded(self) -> bool:
        """检查页面是否已加载。
        
        默认实现检查标题匹配，子类可以重写此方法以提供更精确的检查。
        
        Returns:
            页面是否已加载
        """
        if self._title:
            return self.get_title() == self._title
        return True
    
    @convert_exceptions(TimeoutError)
    def wait_until_loaded(self, timeout: Optional[float] = None) -> 'CompositePage':
        """等待页面加载完成。
        
        使用WaitMixin提供的等待功能，检查页面是否加载完成。
        
        Args:
            timeout: 超时时间(秒)，None表示使用默认超时时间
            
        Returns:
            当前页面对象(用于链式调用)
            
        Raises:
            TimeoutError: 在指定时间内页面未加载完成
        """
        self.wait_strategy.wait_until(
            lambda: self.is_loaded(),
            timeout=timeout,
            message=f"页面在{timeout}秒内未加载完成"
        )
        return self
    
    @convert_exceptions(PageError)
    def refresh(self) -> 'CompositePage':
        """刷新当前页面。
        
        重写NavigationMixin的方法，增加等待页面加载的功能。
        
        Returns:
            当前页面对象(用于链式调用)
        """
        NavigationMixin.refresh(self)
        return self.wait_until_loaded()
    
    @convert_exceptions(NavigationError)
    def go_back(self) -> 'CompositePage':
        """返回上一页。
        
        重写NavigationMixin的方法，增加等待页面加载的功能。
        
        Returns:
            当前页面对象(可能是新页面)
        """
        NavigationMixin.go_back(self)
        return self.wait_until_loaded()
    
    @convert_exceptions(NavigationError)
    def go_forward(self) -> 'CompositePage':
        """前进到下一页。
        
        重写NavigationMixin的方法，增加等待页面加载的功能。
        
        Returns:
            当前页面对象(可能是新页面)
        """
        NavigationMixin.go_forward(self)
        return self.wait_until_loaded() 