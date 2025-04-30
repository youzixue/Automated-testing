"""
核心WebElement接口定义。

定义与Web元素交互的标准方法。
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

# 可以在这里添加其他必要的类型导入

class WebElement(ABC):
    """表示Web元素的抽象基类。"""

    @abstractmethod
    def click(self) -> None:
        """点击此元素。"""
        pass

    @abstractmethod
    def get_text(self) -> str:
        """获取此元素的可见文本内容。"""
        pass

    @abstractmethod
    def get_attribute(self, name: str) -> Optional[str]:
        """获取此元素的指定属性值。"""
        pass

    @abstractmethod
    def find_element(self, selector: str) -> Optional["WebElement"]:
        """在此元素的上下文中查找子元素。"""
        pass

    @abstractmethod
    def find_elements(self, selector: str) -> List["WebElement"]:
        """在此元素的上下文中查找所有匹配的子元素。"""
        pass

    @abstractmethod
    def is_visible(self) -> bool:
        """检查元素当前是否可见。"""
        pass