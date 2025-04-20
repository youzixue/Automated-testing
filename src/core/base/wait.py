"""
等待条件枚举和等待策略接口。

定义等待元素时可使用的各种条件和等待策略接口。
提供智能等待机制，避免使用硬编码等待时间。

注意：该文件只包含接口定义，实现在wait_strategies.py或平台特定的实现文件中。
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Any, Callable, Optional, TypeVar, Union, List, Dict, Generic, overload

from src.core.base.errors import WaitError, TimeoutError, ConditionNotMetError


class ElementCondition(Enum):
    """元素等待条件枚举。
    
    定义等待元素时可使用的各种条件。
    """
    
    PRESENT = "present"  # 元素在DOM中存在
    VISIBLE = "visible"  # 元素可见
    CLICKABLE = "clickable"  # 元素可点击
    INVISIBLE = "invisible"  # 元素不可见
    DISABLED = "disabled"  # 元素被禁用
    ENABLED = "enabled"  # 元素已启用
    SELECTED = "selected"  # 元素被选中
    TEXT_CONTAINS = "text_contains"  # 元素文本包含指定内容
    TEXT_EQUALS = "text_equals"  # 元素文本完全匹配
    VALUE_CONTAINS = "value_contains"  # 元素值包含指定内容
    VALUE_EQUALS = "value_equals"  # 元素值完全匹配
    ATTRIBUTE_CONTAINS = "attribute_contains"  # 元素属性包含指定内容
    ATTRIBUTE_EQUALS = "attribute_equals"  # 元素属性完全匹配
    STALENESS = "staleness"  # 元素已过时(不再附加到DOM)


# 泛型类型定义
T = TypeVar('T')  # 等待返回的元素类型
C = TypeVar('C')  # 等待条件的参数类型


class WaitStrategy(Generic[T], ABC):
    """等待策略接口。
    
    提供智能等待机制，等待特定条件满足。
    """
    
    @abstractmethod
    def wait_for(self, 
                condition: Union[ElementCondition, Callable[..., bool]], 
                timeout: Optional[float] = None,
                condition_args: Optional[Dict[str, Any]] = None,
                poll_frequency: Optional[float] = None,
                message: Optional[str] = None) -> T:
        """等待条件满足。
        
        Args:
            condition: 等待条件，可以是ElementCondition枚举或自定义函数
            timeout: 超时时间(秒)，None表示使用默认超时时间
            condition_args: 传递给条件的参数
            poll_frequency: 轮询频率(秒)，None表示使用默认轮询频率
            message: 超时时显示的错误消息
            
        Returns:
            满足条件的元素(类型由具体实现决定)
            
        Raises:
            TimeoutError: 在指定时间内未满足条件
            ConditionNotMetError: 条件无法满足(某些不可恢复的情况)
        """
        pass
    
    @abstractmethod
    def wait_until(self,
                  condition_fn: Callable[[], T],
                  timeout: Optional[float] = None,
                  poll_frequency: Optional[float] = None,
                  message: Optional[str] = None) -> T:
        """等待直到条件函数返回真值。
        
        Args:
            condition_fn: 条件函数，返回任何真值表示条件满足
            timeout: 超时时间(秒)，None表示使用默认超时时间
            poll_frequency: 轮询频率(秒)，None表示使用默认轮询频率
            message: 超时时显示的错误消息
            
        Returns:
            条件函数的返回值
            
        Raises:
            TimeoutError: 在指定时间内未满足条件
        """
        pass
    
    @abstractmethod
    def wait_for_any(self,
                    conditions: List[Union[ElementCondition, Callable[..., bool]]],
                    timeout: Optional[float] = None,
                    condition_args: Optional[List[Dict[str, Any]]] = None,
                    poll_frequency: Optional[float] = None,
                    message: Optional[str] = None) -> T:
        """等待任意一个条件满足。
        
        Args:
            conditions: 等待条件列表，可以是ElementCondition枚举或自定义函数
            timeout: 超时时间(秒)，None表示使用默认超时时间
            condition_args: 传递给条件的参数列表，与conditions一一对应
            poll_frequency: 轮询频率(秒)，None表示使用默认轮询频率
            message: 超时时显示的错误消息
            
        Returns:
            满足任一条件的元素
            
        Raises:
            TimeoutError: 在指定时间内未满足任何条件
        """
        pass