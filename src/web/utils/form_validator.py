from __future__ import annotations
from typing import List
from src.utils.log.manager import get_logger
from src.core.base.errors import ElementNotFoundError, TimeoutError
from src.web.driver_playwright_adapter import PlaywrightDriverAdapter

class FormValidator:
    """
    表单验证工具类，提供通用的表单验证方法。
    """

    def __init__(self, driver: PlaywrightDriverAdapter):
        """
        初始化表单验证器。
        Args:
            driver: PlaywrightDriverAdapter实例
        """
        self._driver = driver
        self._logger = get_logger(self.__class__.__name__)

    async def check_field_error(self, field_selector: str, timeout: float = 2.0) -> bool:
        """
        检查字段是否显示错误状态。
        Args:
            field_selector: 字段选择器
            timeout: 检查错误提示的超时时间(秒)
        Returns:
            bool: 是否找到错误提示
        Raises:
            ElementNotFoundError: 未找到字段或错误提示
            TimeoutError: 检查超时
        """
        generic_error_selectors = [
            ".error", ".is-error", ".has-error", ".invalid-feedback",
            "[role='alert']", "[data-testid='error-message']"
        ]
        for selector in generic_error_selectors:
            try:
                await self._driver.wait_for_element(selector, timeout=timeout)
                self._logger.debug(f"找到通用错误提示: {selector}")
                return True
            except TimeoutError:
                continue

        try:
            field = await self._driver.get_element(field_selector)
        except Exception as e:
            self._logger.warning(f"未找到字段元素: {field_selector}, 错误: {e}")
            raise ElementNotFoundError(f"未找到字段元素: {field_selector}")

        error_classes = ["is-invalid", "error", "has-error"]
        for cls in error_classes:
            if await field.get_attribute("class") and cls in (await field.get_attribute("class")).split():
                self._logger.debug(f"字段 {field_selector} 有错误样式类: {cls}")
                return True

        if await field.get_attribute("aria-invalid") == "true":
            self._logger.debug(f"字段 {field_selector} 有 aria-invalid='true'")
            return True

        adjacent_error_selectors = [
            "+ .error-message", "+ .invalid-feedback", "+ .form-error",
            "~ .error-message", "~ .invalid-feedback", "~ .form-error"
        ]
        for adj_selector in adjacent_error_selectors:
            full_selector = f"{field_selector}{adj_selector}"
            try:
                await self._driver.wait_for_element(full_selector, timeout=timeout)
                self._logger.debug(f"找到相邻错误提示: {full_selector}")
                return True
            except TimeoutError:
                continue

        self._logger.debug(f"未找到字段 {field_selector} 的明显错误提示")
        return False