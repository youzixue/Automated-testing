"""
Playwright条件处理器实现。

为Playwright提供特定的元素条件处理器实现。
"""

from typing import Any, Optional, TypeVar, Union, cast, Dict, List, Type
from abc import ABC, abstractmethod

from playwright.sync_api import Locator, ElementHandle, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from src.core.base.conditions import (
    BaseConditionHandler,
    BaseConditionHandlerRegistry,
    PresentConditionHandler,
    VisibleConditionHandler,
    InvisibleConditionHandler,
    ClickableConditionHandler,
    EnabledConditionHandler,
    DisabledConditionHandler,
    SelectedConditionHandler,
    StalenessConditionHandler,
    TextConditionHandler,
    AttributeConditionHandler
)
from src.core.base.wait import ElementCondition
from src.core.base.errors import ElementNotVisibleError, ElementNotInteractableError

# 元素类型
PlaywrightElement = Union[Locator, Page]
T = TypeVar('T', bound=PlaywrightElement)

# Define Playwright-specific return type
R = TypeVar('R', bound=Locator)

# --- Playwright Specific Condition Handlers --- #

class PlaywrightBaseHandler(BaseConditionHandler[Locator], ABC):
    """Playwright 条件处理器的基类，提供共享功能。"""
    def __init__(self, page: Optional[Page] = None):
        self._page = page
        if self._page is None:
             # Log warning or handle cases where page might not be immediately available
             # print("Warning: PlaywrightBaseHandler initialized without a page.")
             pass

    def _get_locator(self, selector: str) -> Locator:
        """Helper to get locator, requires page to be set."""
        if self._page is None:
            raise RuntimeError("无法获取定位器，因为 Page 对象未设置")
        return self._page.locator(selector)

    def update_page(self, page: Page) -> None:
         """更新处理器持有的 Page 对象。"""
         self._page = page


class PlaywrightPresentHandler(PlaywrightBaseHandler, PresentConditionHandler[Locator]):
    """Playwright元素存在条件处理器。"""
    
    def matches(self, condition: ElementCondition) -> bool:
        return condition == ElementCondition.PRESENT
    
    def check(self, selector: str, **kwargs: Any) -> Optional[Locator]:
        """检查元素是否至少有一个匹配项在DOM中。"""
        locator = self._get_locator(selector)
        # count() is a quick check in Playwright
        return locator if locator.count() > 0 else None


class PlaywrightVisibleHandler(PlaywrightBaseHandler, VisibleConditionHandler[Locator]):
    """Playwright元素可见条件处理器。"""
    
    def matches(self, condition: ElementCondition) -> bool:
        return condition == ElementCondition.VISIBLE
    
    def check(self, selector: str, **kwargs: Any) -> Optional[Locator]:
        """检查元素是否可见。"""
        locator = self._get_locator(selector)
        # Use is_visible() with a minimal timeout to avoid long waits here
        # The main wait loop handles the overall timeout and polling
        try:
            # is_visible includes attached check
            return locator if locator.is_visible(timeout=100) else None 
        except PlaywrightTimeoutError:
            return None # Not visible within the short check time

class PlaywrightInvisibleHandler(PlaywrightBaseHandler, InvisibleConditionHandler[Locator]):
    """Playwright元素不可见条件处理器。"""
    
    def matches(self, condition: ElementCondition) -> bool:
        return condition == ElementCondition.INVISIBLE
    
    def check(self, selector: str, **kwargs: Any) -> Optional[Locator]:
        """检查元素是否不可见或不存在。"""
        locator = self._get_locator(selector)
        try:
             # is_hidden includes not attached
            return locator if locator.is_hidden(timeout=100) else None
        except PlaywrightTimeoutError:
             # If it times out checking for hidden, it might mean it's visible or doesn't exist in a stable state
             # Let's consider timeout here as condition NOT met for invisibility check
             return None

class PlaywrightClickableHandler(PlaywrightBaseHandler, ClickableConditionHandler[Locator]):
    """Playwright元素可点击条件处理器。"""
    
    def matches(self, condition: ElementCondition) -> bool:
        return condition == ElementCondition.CLICKABLE
    
    def check(self, selector: str, **kwargs: Any) -> Optional[Locator]:
        """检查元素是否可见且启用。"""
        locator = self._get_locator(selector)
        try:
            # Check both visible and enabled with short timeouts
            is_vis = locator.is_visible(timeout=100)
            is_enb = locator.is_enabled(timeout=100)
            return locator if is_vis and is_enb else None
        except PlaywrightTimeoutError:
             # If either check times out, it's not clickable
            return None

class PlaywrightEnabledHandler(PlaywrightBaseHandler, EnabledConditionHandler[Locator]):
    """Playwright元素启用条件处理器。"""

    def matches(self, condition: ElementCondition) -> bool:
        return condition == ElementCondition.ENABLED

    def check(self, selector: str, **kwargs: Any) -> Optional[Locator]:
        """检查元素是否已启用。"""
        locator = self._get_locator(selector)
        try:
            return locator if locator.is_enabled(timeout=100) else None
        except PlaywrightTimeoutError:
            return None

class PlaywrightDisabledHandler(PlaywrightBaseHandler, DisabledConditionHandler[Locator]):
    """Playwright元素禁用条件处理器。"""

    def matches(self, condition: ElementCondition) -> bool:
        return condition == ElementCondition.DISABLED

    def check(self, selector: str, **kwargs: Any) -> Optional[Locator]:
        """检查元素是否被禁用。"""
        locator = self._get_locator(selector)
        try:
            # is_disabled() checks the 'disabled' attribute/property
            return locator if locator.is_disabled(timeout=100) else None
        except PlaywrightTimeoutError:
             # If it times out, it might be enabled or not exist stably
             return None

class PlaywrightSelectedHandler(PlaywrightBaseHandler, SelectedConditionHandler[Locator]):
    """Playwright元素选中条件处理器。"""

    def matches(self, condition: ElementCondition) -> bool:
        return condition == ElementCondition.SELECTED

    def check(self, selector: str, **kwargs: Any) -> Optional[Locator]:
        """检查元素是否被选中 (如 checkbox, radio)。"""
        locator = self._get_locator(selector)
        try:
             # is_checked() is appropriate for input elements
            return locator if locator.is_checked(timeout=100) else None
        except PlaywrightTimeoutError:
             return None
        except Exception as e:
             # is_checked might fail on non-input elements
             # print(f"Debug: is_checked failed on {selector}: {e}")
             return None # Treat error as condition not met

class PlaywrightStalenessHandler(PlaywrightBaseHandler, StalenessConditionHandler[Locator]):
    """Playwright元素过时条件处理器 (检查元素是否已从DOM中移除)。"""

    def matches(self, condition: ElementCondition) -> bool:
        return condition == ElementCondition.STALENESS

    def check(self, selector: str, **kwargs: Any) -> Optional[Locator]:
        """检查元素是否已不再附加到DOM。 
           注意: 这个条件的语义与Selenium不同。Playwright的Locator是自动等待的，
           检查 "staleness" 比较困难。我们检查元素是否变为隐藏或detached。
           返回 Locator 可能没有意义，因为我们期望它消失。
           Maybe return the locator if it IS found (condition not met)?
           Or return None if it IS hidden/detached (condition met)?
           Let's return None if hidden/detached (staleness condition met). Need to clarify WaitStrategy return.
           For now, return locator if hidden/detached.
        """
        locator = self._get_locator(selector)
        try:
            # Check if it's hidden (which includes detached)
            return locator if locator.is_hidden(timeout=100) else None
        except PlaywrightTimeoutError:
            # If checking for hidden times out, it means it's likely still visible/attached
            return None

class PlaywrightTextHandler(PlaywrightBaseHandler, TextConditionHandler[Locator]):
    """Playwright元素文本条件处理器。"""
    
    def matches(self, condition: ElementCondition) -> bool:
        return condition in (ElementCondition.TEXT_CONTAINS, ElementCondition.TEXT_EQUALS)
    
    def check(self, selector: str, **kwargs: Any) -> Optional[Locator]:
        """检查元素的文本内容。"""
        locator = self._get_locator(selector)
        text = kwargs.get("text")
        if text is None:
             raise ValueError("TextCondition 需要 'text' 参数")
        
        exact = kwargs.get("exact", condition == ElementCondition.TEXT_EQUALS) # Default exact based on condition
        
        try:
             # Use text_content() which gets text from node and descendants
            element_text = locator.text_content(timeout=100) or ""
            matches = (element_text == text) if exact else (text in element_text)
            return locator if matches else None
        except PlaywrightTimeoutError:
             return None # Element text not available/stable within short check
        except Exception as e:
             # print(f"Debug: Text check failed on {selector}: {e}")
             return None # Treat error as condition not met


class PlaywrightAttributeHandler(PlaywrightBaseHandler, AttributeConditionHandler[Locator]):
    """Playwright元素属性条件处理器。"""
    
    def matches(self, condition: ElementCondition) -> bool:
        return condition in (ElementCondition.ATTRIBUTE_CONTAINS, ElementCondition.ATTRIBUTE_EQUALS)
    
    def check(self, selector: str, **kwargs: Any) -> Optional[Locator]:
        """检查元素的属性值。"""
        locator = self._get_locator(selector)
        attribute = kwargs.get("attribute")
        value = kwargs.get("value")
        if attribute is None or value is None:
            raise ValueError("AttributeCondition 需要 'attribute' 和 'value' 参数")
        
        exact = kwargs.get("exact", condition == ElementCondition.ATTRIBUTE_EQUALS)
        
        try:
            attr_value = locator.get_attribute(attribute, timeout=100)
            if attr_value is None:
                return None # Attribute not found
            
            matches = (attr_value == value) if exact else (value in attr_value)
            return locator if matches else None
        except PlaywrightTimeoutError:
             return None # Element attribute not available/stable
        except Exception as e:
             # print(f"Debug: Attribute check failed on {selector}: {e}")
             return None


# --- Playwright Condition Handler Registry --- #

class PlaywrightConditionHandlerRegistry(BaseConditionHandlerRegistry[Locator]):
    """Playwright 条件处理器注册表实现。"""

    def __init__(self, page: Optional[Page] = None):
        """初始化并注册所有 Playwright 处理器。"""
        super().__init__()
        self._page = page
        self._register_all()

    def _register_all(self) -> None:
        """注册所有默认的 Playwright 条件处理器。"""
        handlers: List[Type[PlaywrightBaseHandler]] = [
            PlaywrightPresentHandler,
            PlaywrightVisibleHandler,
            PlaywrightInvisibleHandler,
            PlaywrightClickableHandler,
            PlaywrightEnabledHandler,
            PlaywrightDisabledHandler,
            PlaywrightSelectedHandler,
            PlaywrightStalenessHandler,
            PlaywrightTextHandler,
            PlaywrightAttributeHandler,
        ]
        for handler_cls in handlers:
             # Pass page only if it's available during init
            instance = handler_cls(self._page)
            self.register_handler(instance)

    def update_page(self, page: Page) -> None:
        """更新所有处理器持有的 Page 对象。"""
        self._page = page
        for handler in self.get_all_handlers():
            if isinstance(handler, PlaywrightBaseHandler):
                handler.update_page(page) 