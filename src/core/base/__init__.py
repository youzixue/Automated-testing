"""
核心基础模块，定义接口、基础类和异常。
"""

from .driver import BaseDriver
from .element import WebElement
from .errors import (
    AutomationError,
    ApiError,
    ApiRequestError,
    CaptchaError,
    ConfigurationError,
    DriverError,
    DriverInitError,
    ElementError,
    ElementNotInteractableError,
    ElementNotFoundError,
    ElementNotVisibleError,
    LoginError,
    NavigationError,
    ReportGenerationError,
    TimeoutError,
    BrowserError
)
from .wait import ElementCondition, WaitStrategy

__all__ = [
    "BaseDriver",
    "WebElement",
    "AutomationError",
    "ApiError",
    "ApiRequestError",
    "CaptchaError",
    "ConfigurationError",
    "DriverError",
    "DriverInitError",
    "ElementError",
    "ElementNotInteractableError",
    "ElementNotFoundError",
    "ElementNotVisibleError",
    "LoginError",
    "NavigationError",
    "ReportGenerationError",
    "TimeoutError",
    "BrowserError",
    "ElementCondition",
    "WaitStrategy",
] 