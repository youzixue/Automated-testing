"""
驱动接口。

定义与浏览器交互的标准接口，提供统一的浏览器操作方法。
支持上下文管理协议，确保资源正确释放。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Union, Callable

from src.core.base.errors import (
    DriverError, NavigationError, ElementNotFoundError, TimeoutError
)
from src.core.base.wait import WaitStrategy
from src.core.base.conditions import ElementState  # 导入 ElementState


# 泛型类型定义
E = TypeVar('E')  # 元素类型


class BaseDriver(ABC):
    """驱动基础接口。
    
    定义与浏览器交互的标准方法，所有驱动实现类必须继承此接口。
    支持上下文管理协议(with语句)，确保资源正确释放。
    """
    
    def __init__(self, wait_strategy: Optional[WaitStrategy] = None):
        """初始化驱动。
        
        Args:
            wait_strategy: 等待策略，如果为None则创建默认策略
        """
        self._wait_strategy = wait_strategy or WaitStrategy() # 创建默认策略
        # 子类应在此处调用 super().__init__(...) 并进行特定初始化

    @abstractmethod
    def __enter__(self) -> 'BaseDriver':
        """进入上下文管理器，负责启动和准备驱动。
        
        Returns:
            驱动实例
            
        Raises:
            DriverError: 启动或准备失败
        """
        pass
    
    @abstractmethod
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """退出上下文管理器，负责停止驱动和清理资源。
        
        确保资源正确释放，即使发生异常。
        
        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常回溯
            
        Raises:
            DriverError: 停止或清理失败
        """
        pass
    
    @abstractmethod
    def navigate(self, url: str) -> None:
        """导航到指定URL。
        
        Args:
            url: 目标URL
            
        Raises:
            NavigationError: 导航失败
        """
        pass
    
    @abstractmethod
    def refresh(self) -> None:
        """刷新当前页面。
        
        Raises:
            NavigationError: 刷新失败
        """
        pass
    
    @abstractmethod
    def go_back(self) -> None:
        """返回上一页。
        
        Raises:
            NavigationError: 返回失败
        """
        pass
    
    @abstractmethod
    def go_forward(self) -> None:
        """前进到下一页。
        
        Raises:
            NavigationError: 前进失败
        """
        pass
    
    @abstractmethod
    def get_element(self, selector: str) -> E:
        """获取元素。
        
        Args:
            selector: 元素选择器
            
        Returns:
            元素对象
            
        Raises:
            ElementNotFoundError: 元素未找到
        """
        pass
    
    @abstractmethod
    def get_elements(self, selector: str) -> List[E]:
        """获取匹配的所有元素。
        
        Args:
            selector: 元素选择器
            
        Returns:
            元素对象列表
            
        Raises:
            ElementNotFoundError: 没有找到任何元素
        """
        pass
    
    @abstractmethod
    def has_element(self, selector: str) -> bool:
        """检查是否存在指定元素。
        
        Args:
            selector: 元素选择器
            
        Returns:
            元素是否存在
        """
        pass
    
    @abstractmethod
    def wait_for_element(self, 
                        selector: str, 
                        timeout: Optional[float] = None,
                        state: ElementState = ElementState.VISIBLE) -> E: # 使用枚举
        """等待元素达到指定状态。
        
        Args:
            selector: 元素选择器
            timeout: 超时时间(秒)，None表示使用默认超时时间
            state: 等待的状态 (使用 ElementState 枚举)
            
        Returns:
            元素对象
            
        Raises:
            TimeoutError: 在指定时间内未达到状态
            ElementNotFoundError: 选择器未匹配到任何元素 (可能在状态检查前)
        """
        pass
    
    @abstractmethod
    def wait_for_navigation(self, timeout: Optional[float] = None) -> None:
        """等待页面导航完成。
        
        Args:
            timeout: 超时时间(秒)，None表示使用默认超时时间
            
        Raises:
            TimeoutError: 在指定时间内导航未完成
        """
        pass
    
    @abstractmethod
    def execute_script(self, script: str, *args: Any) -> Any:
        """执行JavaScript脚本。
        
        Args:
            script: JavaScript脚本
            *args: 传递给脚本的参数
            
        Returns:
            脚本执行结果
            
        Raises:
            DriverError: 脚本执行失败
        """
        pass
    
    @abstractmethod
    def get_current_url(self) -> str:
        """获取当前页面URL。
        
        Returns:
            当前页面URL
            
        Raises:
            DriverError: 获取URL失败
        """
        pass
    
    @abstractmethod
    def get_title(self) -> str:
        """获取当前页面标题。
        
        Returns:
            当前页面标题
            
        Raises:
            DriverError: 获取标题失败
        """
        pass
    
    @abstractmethod
    def get_screenshot_as_bytes(self) -> bytes: # 修改方法名和返回类型
        """获取页面截图的二进制数据。
        
        Returns:
            截图的bytes数据
            
        Raises:
            DriverError: 获取截图失败
        """
        pass
    
    @property
    @abstractmethod
    def wait_strategy(self) -> WaitStrategy:
        """获取当前驱动的等待策略。"""
        pass
    
    @abstractmethod
    def get_cookies(self) -> List[Dict[str, Any]]:
        """获取所有cookies。
        
        Returns:
            包含cookie字典的列表
            
        Raises:
            DriverError: 获取cookies失败
        """
        pass
    
    @abstractmethod
    def get_cookie(self, name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取cookie。
        
        Args:
            name: cookie名称
            
        Returns:
            cookie字典，如果不存在则返回None
            
        Raises:
            DriverError: 获取cookie失败
        """
        pass
    
    @abstractmethod
    def add_cookie(self, cookie: Dict[str, Any]) -> None:
        """添加cookie。
        
        Args:
            cookie: cookie字典 (需包含 'name' 和 'value')
            
        Raises:
            DriverError: 添加cookie失败
        """
        pass
    
    @abstractmethod
    def delete_cookie(self, name: str) -> None:
        """根据名称删除cookie。
        
        Args:
            name: cookie名称
            
        Raises:
            DriverError: 删除cookie失败
        """
        pass
    
    @abstractmethod
    def delete_all_cookies(self) -> None:
        """删除所有cookies。
        
        Raises:
            DriverError: 删除cookies失败
        """
        pass
    
    @abstractmethod
    def get_page_source(self) -> str:
        """获取当前页面源码。
        
        Returns:
            页面HTML源码
            
        Raises:
            DriverError: 获取源码失败
        """
        pass
    
    @abstractmethod
    def switch_to_frame(self, frame_reference: Union[int, str, E]) -> None:
        """切换到指定的frame。
        
        Args:
            frame_reference: frame的索引、名称/ID或元素对象
            
        Raises:
            NoSuchFrameError: frame不存在
            DriverError: 切换失败
        """
        pass
    
    @abstractmethod
    def switch_to_default_content(self) -> None:
        """切换回主文档。
        
        Raises:
            DriverError: 切换失败
        """
        pass
    
    @abstractmethod
    def accept_alert(self) -> None:
        """接受当前弹窗。
        
        Raises:
            NoAlertPresentError: 没有弹窗
            DriverError: 操作失败
        """
        pass
    
    @abstractmethod
    def dismiss_alert(self) -> None:
        """取消当前弹窗。
        
        Raises:
            NoAlertPresentError: 没有弹窗
            DriverError: 操作失败
        """
        pass 