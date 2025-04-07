"""
条件处理策略。

提供针对不同元素条件的处理策略，支持多种元素状态检查。
使用策略模式减少条件处理的重复代码。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Optional, TypeVar, Callable, List
from enum import Enum, auto

from src.core.base.wait import ElementCondition as ElementConditionEnum
from src.core.base.errors import AutomationError

T = TypeVar('T')  # Element type returned by handler

# Define base condition classes (interfaces)
class ExpectedCondition(ABC):
    """期望条件接口。
    
    所有等待条件必须实现此接口。
    """
    @abstractmethod
    def __call__(self, context: Any) -> Any:
        """执行条件检查。
        
        Args:
            context: 执行上下文 (通常是driver或element)
            
        Returns:
            满足条件时返回非False值，否则返回False或抛出异常。
        """
        pass

class VisibilityCondition(ExpectedCondition, ABC):
    """元素可见性条件接口。"""
    pass

class ElementStateCondition(ExpectedCondition, ABC):
    """元素状态条件接口。"""
    pass

# 添加 ElementState 枚举
class ElementState(Enum):
    VISIBLE = auto()
    HIDDEN = auto()
    ATTACHED = auto()
    DETACHED = auto()
    CLICKABLE = auto()
    ENABLED = auto()
    DISABLED = auto()
    PRESENT = auto()  # 存在于 DOM 中

class BaseConditionHandler(Generic[T], ABC):
    """条件处理器接口。
    
    定义处理元素条件的标准接口。
    """
    
    @abstractmethod
    def matches(self, condition: ElementConditionEnum) -> bool:
        """检查此处理器是否能处理给定的条件。
        
        Args:
            condition: 元素条件枚举
            
        Returns:
            如果能处理则返回 True，否则返回 False
        """
        pass
    
    @abstractmethod
    def check(self, selector: str, **kwargs: Any) -> Optional[T]:
        """检查由选择器定位的元素是否满足条件。
        
        Args:
            selector: 用于定位元素的字符串选择器。
            **kwargs: 特定条件所需的额外参数 (例如，文本值、属性名等)。
                     实现类应处理这些参数。
                     
        Returns:
            如果条件满足，返回元素对象 (类型 T)，否则返回 None。
            返回 None 表示条件在此次检查中未满足，等待应继续。
            如果发生无法恢复的错误（例如无效选择器），应抛出异常。
        """
        pass


class PresentConditionHandler(BaseConditionHandler[T], ABC):
    """元素存在条件处理器接口。"""
    pass

class VisibleConditionHandler(BaseConditionHandler[T], ABC):
    """元素可见条件处理器接口。"""
    pass

class InvisibleConditionHandler(BaseConditionHandler[T], ABC):
    """元素不可见条件处理器接口。"""
    pass

class ClickableConditionHandler(BaseConditionHandler[T], ABC):
    """元素可点击条件处理器接口。"""
    pass

class EnabledConditionHandler(BaseConditionHandler[T], ABC):
    """元素启用条件处理器接口。"""
    pass

class DisabledConditionHandler(BaseConditionHandler[T], ABC):
    """元素禁用条件处理器接口。"""
    pass

class SelectedConditionHandler(BaseConditionHandler[T], ABC):
    """元素选中条件处理器接口。"""
    pass

class StalenessConditionHandler(BaseConditionHandler[T], ABC):
    """元素过时条件处理器接口。"""
    pass

class TextConditionHandler(BaseConditionHandler[T], ABC):
    """元素文本条件处理器接口。"""
    pass

class AttributeConditionHandler(BaseConditionHandler[T], ABC):
    """元素属性条件处理器接口。"""
    pass


class BaseConditionHandlerRegistry(Generic[T]):
    """条件处理器注册表基类。
    
    存储和检索特定条件的处理器。
    """
    
    def __init__(self):
        """初始化注册表。"""
        self.handlers: List[BaseConditionHandler[T]] = []
        self._handler_map: Dict[ElementConditionEnum, BaseConditionHandler[T]] = {}

    def register_handler(self, handler: BaseConditionHandler[T]) -> None:
        """注册一个条件处理器。
        
        Args:
            handler: 要注册的条件处理器实例。
        """
        if not isinstance(handler, BaseConditionHandler):
            raise TypeError("注册的对象必须是 BaseConditionHandler 的实例")
        self.handlers.append(handler)
        # Update map for faster lookup
        for condition in ElementConditionEnum:
            if handler.matches(condition):
                 if condition in self._handler_map:
                      # Allow overwriting for potential customization, maybe add a warning?
                      pass 
                 self._handler_map[condition] = handler
                 
    def get_handler(self, condition: ElementConditionEnum) -> Optional[BaseConditionHandler[T]]:
        """根据条件获取合适的处理器。
        
        Args:
            condition: 元素条件
            
        Returns:
            匹配的条件处理器，如果未找到则返回 None
        """
        # Fast lookup using map
        return self._handler_map.get(condition)

    def get_all_handlers(self) -> List[BaseConditionHandler[T]]:
        """获取所有已注册的处理器。"""
        return list(self.handlers) 