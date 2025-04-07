import logging
from typing import List

from src.core.base.errors import ElementNotFoundError, TimeoutError
from src.web.driver import WebDriver


class FormValidator:
    """表单验证工具类。
    
    提供通用的表单验证方法。
    """
    
    def __init__(self, driver: WebDriver):
        """初始化表单验证器。
        
        Args:
            driver: WebDriver实例
        """
        self._driver = driver
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def check_field_error(self, field_selector: str, timeout: float = 2.0) -> bool:
        """检查字段是否显示错误状态。
        
        Args:
            field_selector: 字段选择器
            timeout: 检查错误提示的超时时间(秒)
            
        Returns:
            bool: 是否找到错误提示
        """
        try:
            # 尝试等待任何可能出现的通用错误提示元素
            generic_error_selectors = [
                ".error", ".is-error", ".has-error", ".invalid-feedback",
                "[role='alert']", "[data-testid='error-message']"
            ]
            for selector in generic_error_selectors:
                try:
                    self._driver.wait_for_element(selector, timeout=timeout, state="visible")
                    self._logger.debug(f"找到通用错误提示: {selector}")
                    return True
                except (ElementNotFoundError, TimeoutError):
                    continue # Not found, try next generic selector
            
            # 如果没有找到通用错误提示，再检查特定字段相关的错误
            field = self._driver.get_element(field_selector)
            
            # 检查字段是否有错误样式类
            error_classes = ["is-invalid", "error", "has-error"]
            for cls in error_classes:
                if field.has_class(cls):
                    self._logger.debug(f"字段 {field_selector} 有错误样式类: {cls}")
                    return True
            
            # 检查字段是否有 aria-invalid="true" 属性
            if field.get_attribute("aria-invalid") == "true":
                self._logger.debug(f"字段 {field_selector} 有 aria-invalid='true'")
                return True
            
            # 检查字段旁边是否有错误消息元素
            adjacent_error_selectors = [
                "+ .error-message", "+ .invalid-feedback", "+ .form-error",
                "~ .error-message", "~ .invalid-feedback", "~ .form-error"
            ]
            for adj_selector in adjacent_error_selectors:
                full_selector = f"{field_selector}{adj_selector}"
                try:
                    self._driver.wait_for_element(full_selector, timeout=timeout, state="visible")
                    self._logger.debug(f"找到相邻错误提示: {full_selector}")
                    return True
                except (ElementNotFoundError, TimeoutError):
                    continue # Not found, try next adjacent selector
            
            self._logger.debug(f"未找到字段 {field_selector} 的明显错误提示")
            return False
            
        except (ElementNotFoundError, TimeoutError) as e: # Catch specific expected errors
            self._logger.warning(f"检查字段 {field_selector} 错误状态时未找到元素或超时: {e}")
            return False
        except Exception as e:
            self._logger.error(f"检查字段 {field_selector} 错误状态时发生意外错误: {e}")
            return False 