from __future__ import annotations
from typing import Any, Optional, Callable, List
from src.utils.log.manager import get_logger
from src.core.base.errors import ElementNotFoundError, ConditionNotMetError
from src.core.base.wait import ElementCondition
from src.core.base.conditions import (
    BaseConditionHandler, ElementState, BaseConditionHandlerRegistry
)

logger = get_logger(__name__)

class VisibleConditionHandler(BaseConditionHandler[Any]):
    """
    元素可见条件处理器。
    """

    def matches(self, condition: ElementCondition) -> bool:
        """
        判断是否处理可见条件。

        Args:
            condition: 元素条件枚举

        Returns:
            bool: 是否匹配
        """
        return condition == ElementCondition.VISIBLE

    def check(self, selector: str, **kwargs) -> Optional[Any]:
        """
        检查元素是否可见。

        Args:
            selector: 元素选择器

        Returns:
            Optional[Any]: 元素对象或None

        Raises:
            ElementNotFoundError: 元素未找到
        """
        driver = kwargs.get("driver")
        if not driver:
            logger.error("未传入driver参数")
            raise ValueError("driver参数必传")
        el = driver.get_element_sync(selector)
        if not el:
            logger.warning(f"未找到元素: {selector}")
            raise ElementNotFoundError(f"未找到元素: {selector}")
        if el.is_visible():
            logger.info(f"元素可见: {selector}")
            return el
        logger.debug(f"元素不可见: {selector}")
        return None


class ConditionHandlerRegistry(BaseConditionHandlerRegistry[Any]):
    """
    条件处理器注册表，统一管理所有条件处理器。
    """

    def __init__(self):
        super().__init__()
        self.register_handler(VisibleConditionHandler())
        # 可继续注册其它条件处理器

    def get_handler(self, condition: ElementCondition) -> Optional[BaseConditionHandler[Any]]:
        """
        获取指定条件的处理器。

        Args:
            condition: 元素条件枚举

        Returns:
            Optional[BaseConditionHandler[Any]]: 匹配的处理器或None
        """
        handler = super().get_handler(condition)
        if handler:
            logger.debug(f"找到条件处理器: {handler.__class__.__name__} for {condition}")
        else:
            logger.warning(f"未找到条件处理器: {condition}")
        return handler