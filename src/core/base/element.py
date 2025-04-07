"""
元素接口.

定义与UI元素交互的标准接口，提供统一的元素操作方法.
采用组合模式，通过WaitMixin实现等待功能，避免代码重复.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, overload, cast, TypeVar
import logging

from src.core.base.errors import (
    ElementError, ElementNotFoundError, ElementStateError, ElementNotVisibleError,
    AutomationError
)
from src.core.base.wait import ElementCondition, WaitStrategy
from src.core.base.mixins import NavigationMixin, ElementFinderMixin, ScreenshotMixin, JavaScriptMixin

# 解决循环依赖，用于类型提示
D = TypeVar('D', bound='BaseDriver') # 假设 BaseDriver 定义在某处，或用字符串 'BaseDriver'


class BaseElement(ABC):
    """所有平台元素对象的抽象基类.

    定义元素共有的核心接口和属性.
    """

    def __init__(self, locator: Any, driver: D, wait_strategy: WaitStrategy):
        """初始化元素.

        Args:
            locator: 定位元素的标识 (具体类型由实现决定)
            driver: 关联的驱动实例
            wait_strategy: 等待策略
        """
        self._locator = locator
        self._driver = driver
        self._wait_strategy = wait_strategy
        self._logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        self._logger.debug(f"Element initialized with locator: {locator}")

    @abstractmethod
    def click(self) -> None:
        """点击元素.

        Raises:
            ElementNotFoundError: 元素未找到
            ElementStateError: 元素状态不允许点击操作 (例如, 不可见或禁用)
        """
        pass

    @abstractmethod
    def double_click(self) -> None:
        """双击元素.

        Raises:
            ElementNotFoundError: 元素未找到
            ElementStateError: 元素状态不允许双击操作
        """
        pass

    @abstractmethod
    def right_click(self) -> None:
        """右键点击元素.

        Raises:
            ElementNotFoundError: 元素未找到
            ElementStateError: 元素状态不允许右键点击操作
        """
        pass

    @abstractmethod
    def hover(self) -> None:
        """悬停在元素上.

        Raises:
            ElementNotFoundError: 元素未找到
            ElementStateError: 元素状态不允许悬停操作
        """
        pass

    @abstractmethod
    def drag_to(self, target: 'BaseElement') -> None:
        """将元素拖动到目标元素.

        Args:
            target: 目标元素

        Raises:
            ElementNotFoundError: 元素或目标元素未找到
            ElementStateError: 元素状态不允许拖动操作
        """
        pass

    @abstractmethod
    def fill(self, text: str) -> None:
        """填充文本到元素 (通常用于输入框).

        此方法通常会先清空输入框再输入文本.

        Args:
            text: 要填充的文本

        Raises:
            ElementNotFoundError: 元素未找到
            ElementStateError: 元素状态不允许填充操作 (例如, 非输入框, 禁用)
        """
        pass

    @abstractmethod
    def type(self, text: str, delay: Optional[float] = None) -> None:
        """模拟键盘逐字输入文本.

        与 fill 不同, 此方法不会清除现有文本, 而是模拟键盘输入, 更接近用户行为.

        Args:
            text: 要输入的文本
            delay: 按键之间的延迟(秒), None表示使用默认或平台特定延迟

        Raises:
            ElementNotFoundError: 元素未找到
            ElementStateError: 元素状态不允许输入操作
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """清除元素中的文本 (通常用于输入框).

        Raises:
            ElementNotFoundError: 元素未找到
            ElementStateError: 元素状态不允许清除操作
        """
        pass

    @abstractmethod
    def select_option(self, value: Optional[str] = None, text: Optional[str] = None, index: Optional[int] = None) -> None:
        """在下拉列表 (select 元素) 中选择单个选项.

        至少需要提供 value, text 或 index 中的一个参数.

        Args:
            value: 选项的 value 属性值
            text: 选项的可见文本内容
            index: 选项的索引 (从 0 开始)

        Raises:
            ElementNotFoundError: 元素未找到或不是 select 元素
            ElementStateError: 元素状态不允许选择操作
            ValueError: 未提供任何有效的参数或找不到匹配的选项
        """
        pass

    @abstractmethod
    def select_options(self, values: Optional[List[str]] = None, texts: Optional[List[str]] = None, indices: Optional[List[int]] = None) -> None:
        """在多选下拉列表 (select[multiple] 元素) 中选择多个选项.

        至少需要提供 values, texts 或 indices 中的一个参数.

        Args:
            values: 选项的 value 属性值列表
            texts: 选项的可见文本内容列表
            indices: 选项的索引列表

        Raises:
            ElementNotFoundError: 元素未找到或不是 select[multiple] 元素
            ElementStateError: 元素状态不允许选择操作
            ValueError: 未提供任何有效的参数或找不到匹配的选项
        """
        pass

    @abstractmethod
    def check(self) -> None:
        """选中复选框 (checkbox) 或单选按钮 (radio button).

        如果元素已经是选中状态, 则不执行任何操作.

        Raises:
            ElementNotFoundError: 元素未找到或不是可检查元素
            ElementStateError: 元素状态不允许选中操作 (例如, 禁用)
        """
        pass

    @abstractmethod
    def uncheck(self) -> None:
        """取消选中复选框 (checkbox).

        如果元素已经是未选中状态, 则不执行任何操作.通常对单选按钮无效.

        Raises:
            ElementNotFoundError: 元素未找到或不是复选框
            ElementStateError: 元素状态不允许取消选中操作 (例如, 禁用)
        """
        pass

    @abstractmethod
    def press_key(self, key: str) -> None:
        """在元素上模拟按下特定键盘按键.

        Args:
            key: 要按下的键名 (例如, 'Enter', 'Tab', 'Escape', 'ArrowDown').
                 具体支持的键名可能因平台而异.

        Raises:
            ElementNotFoundError: 元素未找到
            ElementStateError: 元素状态不允许按键操作
            ValueError: 无效或不支持的键名
        """
        pass

    @abstractmethod
    def is_visible(self) -> bool:
        """检查元素在页面上是否可见.

        可见性通常意味着元素本身及其所有父元素都可见, 且具有非零尺寸.

        Returns:
            如果元素可见, 返回 True, 否则返回 False.
        """
        pass

    @abstractmethod
    def is_enabled(self) -> bool:
        """检查元素是否已启用.

        通常用于表单元素, 如按钮、输入框等.

        Returns:
            如果元素已启用, 返回 True, 否则返回 False.
        """
        pass

    @abstractmethod
    def is_selected(self) -> bool:
        """检查元素是否被选中.

        通常用于复选框、单选按钮或下拉列表中的选项.

        Returns:
            如果元素被选中, 返回 True, 否则返回 False.
        """
        pass

    @abstractmethod
    def get_property(self, name: str) -> Any:
        """获取元素的 JavaScript DOM 属性值.

        例如: element.getProperty('checked'), element.getProperty('value')

        Args:
            name: JavaScript DOM 属性的名称.

        Returns:
            属性的值.类型取决于属性本身.

        Raises:
            ElementNotFoundError: 元素未找到.
            AttributeError: 如果元素没有该 DOM 属性.
        """
        pass

    @abstractmethod
    def highlight(self) -> 'BaseElement':
        """高亮显示元素 (通常用于调试).

        在UI上临时突出显示元素边界或背景.

        Returns:
            返回元素自身, 以便链式调用.

        Raises:
            ElementNotFoundError: 元素未找到.
        """
        pass

    @property
    @abstractmethod
    def exists(self) -> bool:
        """检查元素是否存在于 DOM 中 (不一定可见)"""
        pass

    @abstractmethod
    def get_inner_text(self) -> str:
        """获取元素的内部文本 (innerText).

        通常返回元素内所有可见文本内容的组合, 受 CSS 影响.

        Returns:
            元素的内部文本.

        Raises:
            ElementNotFoundError: 元素未找到.
        """
        pass

    @abstractmethod
    def get_text_content(self) -> str:
        """获取元素的文本内容 (textContent).

        返回元素及其所有后代节点的原始文本内容, 不受 CSS 影响.

        Returns:
            元素的文本内容.

        Raises:
            ElementNotFoundError: 元素未找到.
        """
        pass

    @abstractmethod
    def get_attribute(self, name: str) -> Optional[str]:
        """获取元素的 HTML 属性值.

        例如: element.getAttribute('href'), element.getAttribute('class')

        Args:
            name: HTML 属性的名称.

        Returns:
            属性的值 (字符串). 如果属性不存在, 返回 None.

        Raises:
            ElementNotFoundError: 元素未找到.
        """
        pass

    @abstractmethod
    def scroll_into_view(self, **kwargs) -> None:
        """将元素滚动到可见区域.

        Args:
            **kwargs: 特定平台支持的滚动选项 (例如, block, inline)

        Raises:
            ElementNotFoundError: 元素未找到.
            ElementStateError: 元素状态不允许滚动操作.
        """
        pass

    @abstractmethod
    def get_value(self) -> str:
        """获取输入元素 (input, textarea, select) 的当前值.

        通常等同于获取 'value' DOM 属性.

        Returns:
            元素的当前值.

        Raises:
            ElementNotFoundError: 元素未找到.
            ElementError: 元素类型不支持获取值.
        """
        pass

    @abstractmethod
    def get_inner_html(self) -> str:
        """获取元素的内部 HTML.

        Returns:
            内部 HTML 字符串.

        Raises:
            ElementNotFoundError: 元素未找到.
        """
        pass

    @abstractmethod
    def get_outer_html(self) -> str:
        """获取元素的外部 HTML (outerHTML).

        包括元素本身及其内部的 HTML 标记.

        Returns:
            元素的外部 HTML 标记字符串.

        Raises:
            ElementNotFoundError: 元素未找到.
        """
        pass

    @abstractmethod
    def get_position(self) -> Dict[str, float]:
        """获取元素的位置和大小.

        通常返回包含 x, y, width, height 的字典.

        Returns:
            包含元素位置和大小信息的字典.

        Raises:
            ElementNotFoundError: 元素未找到.
        """
        pass

    @abstractmethod
    def has_class(self, class_name: str) -> bool:
        """检查元素是否包含指定的 CSS 类名.

        Args:
            class_name: CSS 类名.

        Returns:
            如果元素包含该类名, 返回 True, 否则返回 False.
        """
        pass