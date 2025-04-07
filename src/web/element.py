"""
Playwright页面元素实现。

基于Playwright实现Web元素操作，提供统一的元素交互接口。
"""

import logging
from typing import Any, Dict, List, Optional, Union, Tuple, cast, ForwardRef

from playwright.sync_api import Locator, ElementHandle
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from src.core.base.element import BaseElement
from src.core.base.errors import ElementNotFoundError, ElementStateError, TimeoutError, ElementError, ElementNotInteractableError, ElementNotVisibleError
from src.core.base.wait import WaitStrategy, ElementCondition
from src.utils.error_handling import convert_exceptions
from src.web.wait import PlaywrightWaitStrategy

# 类型别名，提高可读性
WebElementType = Union[ElementHandle, Locator]

# WebDriver 的前向引用，解决循环导入问题
if "WebDriver" not in globals():
    WebDriver = ForwardRef('WebDriver')


class WebElement(BaseElement):
    """Playwright元素实现。
    
    封装Playwright元素操作，提供统一的元素交互接口。
    
    Attributes:
        locator: Playwright Locator对象
        wait_strategy: PlaywrightWaitStrategy实例
        driver: WebDriver实例
    """
    
    def __init__(self, locator: WebElementType, driver: 'WebDriver', wait_strategy: PlaywrightWaitStrategy):
        """初始化Web元素。
        
        Args:
            locator: Playwright Locator或ElementHandle对象。
            driver: WebDriver实例。
            wait_strategy: PlaywrightWaitStrategy实例。
            
        Raises:
            TypeError: 如果locator不是Locator或ElementHandle类型。
        """
        
        # 优先使用 Locator，对 ElementHandle 提出警告
        if isinstance(locator, ElementHandle):
            self._element_handle = locator
            self.locator = None 
            logging.getLogger(self.__class__.__name__).warning(
                "不推荐使用ElementHandle初始化WebElement，请优先使用Locator。"
            )
        elif isinstance(locator, Locator):
            self.locator = locator
            self._element_handle = None
        else:
            raise TypeError(f"locator必须是Locator或ElementHandle类型，不能是{type(locator)}")
        
        super().__init__(locator=locator, driver=driver, wait_strategy=wait_strategy)
        
        self.driver: 'WebDriver' = driver
        self._logger.debug(f"WebElement已初始化: {self._get_selector_or_repr()}")
    
    @property
    def wait(self) -> PlaywrightWaitStrategy:
        """获取等待策略实例。"""
        if not isinstance(self._wait_strategy, PlaywrightWaitStrategy):
            raise TypeError("内部错误: 等待策略不是 PlaywrightWaitStrategy 类型")
        return self._wait_strategy
    
    def _get_selector_or_repr(self) -> str:
        """获取定位符的选择器或对象表示，用于日志。"""
        loc = self.locator
        if hasattr(loc, 'selector'):
            return loc.selector
        return repr(loc)
    
    def _get_element(self) -> WebElementType:
        """获取可操作的 Playwright 元素对象 (Locator 或 ElementHandle)。"""
        element = self.locator if self.locator is not None else self._element_handle
        if element is None:
             # This case should ideally not happen due to __init__ logic
             raise ElementNotFoundError("无法获取底层Playwright元素对象")
        return element
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def click(self, force: bool = False) -> None:
        """点击元素。

        Args:
            force: 是否强制点击，忽略可点击状态检查。
        """
        self._logger.debug("点击元素")
        # Playwright Locator 的 click 会自动等待元素可交互
        self._get_element().click(force=force) # Pass force option
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def double_click(self) -> None:
        """双击元素。"""
        self._logger.debug("双击元素")
        self._get_element().dblclick()
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def right_click(self) -> None:
        """右键点击元素。"""
        self._logger.debug("右键点击元素")
        self._get_element().click(button="right")
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def hover(self) -> None:
        """悬停在元素上。"""
        self._logger.debug("悬停在元素上")
        self._get_element().hover()
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def drag_to(self, target: 'WebElement') -> None:
        """将元素拖动到目标元素。
        
        Args:
            target: 目标元素 (WebElement 实例)。
        """
        if not isinstance(target, WebElement):
            raise TypeError(f"目标必须是WebElement类型，不能是{type(target)}")
        
        self._logger.debug("拖动元素到目标位置")
        target_element = target._get_element() 
        self._get_element().drag_to(target_element)
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def fill(self, text: str) -> None:
        """填充文本到元素 (会先清空)。

        Args:
            text: 要填充的文本。
        """
        self._logger.debug(f"填充文本: {text}")
        self._get_element().fill(text)
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def type(self, text: str, delay: Optional[float] = None) -> None:
        """模拟键盘逐字输入文本 (不清空)。

        Args:
            text: 要输入的文本。
            delay: 按键之间的延迟(秒)，None表示默认延迟。
        """
        self._logger.debug(f"输入文本: {text}" + (f", 延迟: {delay}秒" if delay else ""))
        delay_ms = int(delay * 1000) if delay is not None else None
        self._get_element().type(text, delay=delay_ms)
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def clear(self) -> None:
        """清除元素中的文本 (通过填充空字符串实现)。"""
        self._logger.debug("清除文本")
        self._get_element().fill("")
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def select_option(self, value: Optional[str] = None, text: Optional[str] = None, index: Optional[int] = None) -> None:
        """选择下拉列表中的单个选项。
        
        Args:
            value: 选项的 value 属性。
            text: 选项的显示文本。
            index: 选项的索引。
        """
        if value is None and text is None and index is None:
            raise ValueError("必须提供value、text或index中的至少一个参数")
        
        self._logger.debug(f"选择选项: value={value}, text={text}, index={index}")
        options = {}
        if value is not None: options["value"] = value
        if text is not None: options["label"] = text
        if index is not None: options["index"] = index
        self._get_element().select_option(**options)
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def select_options(self, values: Optional[List[str]] = None, texts: Optional[List[str]] = None, indices: Optional[List[int]] = None) -> None:
        """在多选下拉列表中选择多个选项。

        Args:
            values: 选项的 value 属性列表。
            texts: 选项的显示文本列表。
            indices: 选项的索引列表。
        """
        if values is None and texts is None and indices is None:
            raise ValueError("必须提供values、texts或indices中的至少一个参数")
        
        self._logger.debug(f"选择多个选项: values={values}, texts={texts}, indices={indices}")
        options = []
        if values is not None: options.extend([{"value": value} for value in values])
        if texts is not None: options.extend([{"label": text} for text in texts])
        if indices is not None: options.extend([{"index": index} for index in indices])
        self._get_element().select_option(options)
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def check(self) -> None:
        """选中复选框或单选按钮 (如果未选中)。"""
        self._logger.debug("选中复选框/单选按钮")
        self._get_element().check()
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def uncheck(self) -> None:
        """取消选中复选框 (如果已选中)。"""
        self._logger.debug("取消选中复选框")
        self._get_element().uncheck()
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def press_key(self, key: str) -> None:
        """在元素上模拟按下特定键盘按键。

        Args:
            key: 键名 (例如, 'Enter', 'Tab', 'Escape')。
        """
        self._logger.debug(f"按下键: {key}")
        self._get_element().press(key)
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def is_visible(self) -> bool:
        """检查元素是否可见。"""
        self._logger.debug("检查元素是否可见")
        try:
            return self._get_element().is_visible()
        except Exception as e:
            self._logger.debug(f"检查元素可见性时出错: {e}")
            return False
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def is_enabled(self) -> bool:
        """检查元素是否启用。"""
        self._logger.debug("检查元素是否启用")
        return self._get_element().is_enabled()
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def is_selected(self) -> bool:
        """检查元素是否被选中 (复选框/单选按钮/下拉选项)。"""
        self._logger.debug("检查元素是否选中")
        return self._get_element().is_checked()
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def get_attribute(self, name: str) -> Optional[str]:
        """获取元素属性值。

        Args:
            name: 属性名。

        Returns:
            属性值，如果属性不存在则返回None。
        """
        self._logger.debug(f"获取元素属性: {name}")
        return self._get_element().get_attribute(name)
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def get_property(self, name: str) -> Any:
        """获取元素的 JavaScript DOM 属性值。

        Args:
            name: 属性名。
        """
        self._logger.debug(f"获取元素JS属性: {name}")
        return self._get_element().evaluate(f"el => el.{name}")
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def get_value(self) -> str:
        """获取表单元素的 value 属性值。"""
        self._logger.debug("获取元素value")
        return self._get_element().input_value()
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def get_inner_text(self) -> str:
        """获取元素的 innerText (仅元素自身文本)。"""
        self._logger.debug("获取元素的 innerText")
        return self._get_element().inner_text()
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def get_text_content(self) -> str:
        """获取元素的 textContent (包含子元素文本)。"""
        self._logger.debug("获取元素的 textContent")
        return self._get_element().text_content() or "" # 确保返回字符串
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def get_inner_html(self) -> str:
        """获取元素的 innerHTML。"""
        self._logger.debug("获取元素的 innerHTML")
        return self._get_element().inner_html()
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def get_outer_html(self) -> str:
        """获取元素的 outerHTML。"""
        self._logger.debug("获取元素的 outerHTML")
        # Playwright 的 Locator/ElementHandle 没有直接的 outer_html 方法
        # 使用 evaluate 获取
        return self._get_element().evaluate("element => element.outerHTML")
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def get_position(self) -> Dict[str, float]:
        """获取元素的位置和大小 (bounding box)。"""
        self._logger.debug("获取元素的位置信息")
        box = self._get_element().bounding_box()
        if box is None:
             raise ElementNotVisibleError("元素不可见或不存在，无法获取位置")
        return {"x": box["x"], "y": box["y"], "width": box["width"], "height": box["height"]}
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def take_screenshot(self, path: Optional[str] = None) -> bytes:
        """截取元素的截图。

        Args:
            path: 保存截图的路径，None则只返回字节数据。

        Returns:
            截图的二进制数据。
        """
        self._logger.debug(f"截取元素截图" + (f", 保存到: {path}" if path else ""))
        return self._get_element().screenshot(path=path)
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def scroll_into_view(self, **kwargs) -> None:
        """将元素滚动到视图中。"""
        self._logger.debug("将元素滚动到视图中")
        self._get_element().scroll_into_view_if_needed(**kwargs)
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def has_class(self, class_name: str) -> bool:
        """检查元素是否包含指定的CSS类。

        Args:
            class_name: 要检查的CSS类名。

        Returns:
            如果元素包含该类，则为True，否则为False。
        """
        self._logger.debug(f"检查元素是否包含类: {class_name}")
        classes = self.get_attribute("class")
        if classes:
            return class_name in classes.split()
        return False

    @property
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def exists(self) -> bool:
        """检查元素当前是否存在于DOM中（快速检查，不等待）。"""
        try:
            # is_attached 是一个无超时的快速检查
            return self._get_element().is_attached()
        except Exception:
             # 如果检查过程中发生任何错误（如元素分离），则认为不存在
            return False
    
    @convert_exceptions(ElementError, source_exceptions=[PlaywrightError, PlaywrightTimeoutError])
    def highlight(self) -> 'WebElement':
        """高亮元素（通常添加红色边框），用于调试。"
        
        Returns:
            当前元素对象(用于链式调用)。
        """
        self._logger.debug("高亮显示元素")
        self._get_element().highlight()
        return self