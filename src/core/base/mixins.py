"""
功能性Mixin类。

提供可复用的功能组件，用于不同类之间共享通用功能。
采用组合优于继承的设计理念，避免代码重复。
"""

from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union
import logging
import base64
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar, Union, cast

from src.core.base.errors import AutomationError, ElementNotFoundError
from src.core.base.wait import WaitStrategy, ElementCondition


T = TypeVar('T')  # 泛型类型，用于方法返回值


class JavaScriptMixin:
    """JavaScript执行功能混入类。
    
    提供执行JavaScript脚本的能力。
    """
    
    def __init__(self, executor: Callable[[str, Any], Any]):
        """初始化JavaScript混入类。
        
        Args:
            executor: 执行JavaScript的函数，接收脚本和参数并返回结果
        """
        self._executor = executor
    
    def execute_script(self, script: str, *args: Any) -> Any:
        """执行JavaScript脚本。
        
        Args:
            script: JavaScript脚本
            *args: 传递给脚本的参数
            
        Returns:
            脚本执行结果
        """
        return self._executor(script, *args)


class NavigationMixin:
    """导航功能混入类。
    
    提供页面导航功能。
    """
    
    def __init__(self, navigator: Any):
        """初始化导航混入类。
        
        Args:
            navigator: 提供导航功能的对象，必须支持navigate、refresh等方法
        """
        self._navigator = navigator
    
    def navigate(self, url: str) -> None:
        """导航到指定URL。
        
        Args:
            url: 目标URL
        """
        return self._navigator.navigate(url)
    
    def refresh(self) -> None:
        """刷新当前页面。"""
        return self._navigator.refresh()
    
    def go_back(self) -> None:
        """返回上一页。"""
        return self._navigator.go_back()
    
    def go_forward(self) -> None:
        """前进到下一页。"""
        return self._navigator.go_forward()
    
    def get_current_url(self) -> str:
        """获取当前页面URL。
        
        Returns:
            当前页面URL
        """
        return self._navigator.get_current_url()
    
    def get_title(self) -> str:
        """获取当前页面标题。
        
        Returns:
            当前页面标题
        """
        return self._navigator.get_title()


class ScreenshotMixin:
    """截图功能混入类。
    
    提供截图功能。
    """
    
    def __init__(self, screenshot_taker: Callable[[Optional[str]], bytes]):
        """初始化截图混入类。
        
        Args:
            screenshot_taker: 提供截图功能的函数，接收文件名并返回二进制数据
        """
        self._screenshot_taker = screenshot_taker
    
    def take_screenshot(self, filename: Optional[str] = None) -> bytes:
        """获取截图。
        
        Args:
            filename: 保存截图的文件名，None表示不保存
            
        Returns:
            截图的二进制数据
        """
        return self._screenshot_taker(filename)


class ElementFinderMixin:
    """元素查找混入类。
    
    提供元素查找功能。
    """
    
    def __init__(self, element_finder: Any):
        """初始化元素查找混入类。
        
        Args:
            element_finder: 提供元素查找功能的对象
        """
        self._element_finder = element_finder
    
    def get_element(self, selector: str) -> Any:
        """获取元素。
        
        Args:
            selector: 元素选择器
            
        Returns:
            元素对象
            
        Raises:
            ElementNotFoundError: 元素未找到
        """
        return self._element_finder.get_element(selector)
    
    def get_elements(self, selector: str) -> List[Any]:
        """获取匹配的所有元素。
        
        Args:
            selector: 元素选择器
            
        Returns:
            元素对象列表
            
        Raises:
            ElementNotFoundError: 没有找到任何元素
        """
        return self._element_finder.get_elements(selector)
    
    def has_element(self, selector: str) -> bool:
        """检查是否存在指定元素。
        
        Args:
            selector: 元素选择器
            
        Returns:
            元素是否存在
        """
        return self._element_finder.has_element(selector)


# ErrorHandlingMixin, CookieHandlingMixin, DialogHandlingMixin removed as they are unused. 