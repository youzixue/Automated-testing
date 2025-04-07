"""
Core base components for the test automation framework.

Includes base classes and interfaces for drivers, elements, pages, and errors.
"""

# Import core interfaces and base classes
from .driver import BaseDriver
from .element import BaseElement
from .page import BasePage, CompositePage
from .wait import WaitStrategy, ElementCondition
from .config_defs import ConfigLevel, CONFIG_PRIORITY_ORDER, CONFIG_MERGE_ORDER
from .log_interfaces import LogLevel, LogFormatter, LogHandler, Logger
from .errors import *

# Import core exception types
from .errors import (
    AutomationError,
    ElementError,
    ElementNotFoundError,
    ElementNotVisibleError,
    ElementNotInteractableError,
    DriverError,
    DriverInitError,
    NavigationError,
    TimeoutError,
    ConfigurationError,
    ApiError,
    ApiRequestError,
    DataError,
    TestSetupError,
    TestTeardownError,
    SecurityError,
    ResourceError,
    ReportGenerationError,
    # Deprecated / Internal Errors (consider removal or making private)
    # LogError, # Removed, managed by utils.log now
    FrameworkError,
)

# Import conditions
from .conditions import ExpectedCondition, ElementStateCondition, VisibilityCondition, BaseConditionHandler, BaseConditionHandlerRegistry

# Define publicly available components
__all__ = [
    # Base interfaces and classes
    "BaseDriver",
    "BaseElement",
    "BasePage",
    "CompositePage",
    "WaitStrategy",
    "ElementCondition",
    "ExpectedCondition",
    "ElementStateCondition",
    "VisibilityCondition",
    "BaseConditionHandler",
    "BaseConditionHandlerRegistry",
    "ConfigLevel",
    "CONFIG_PRIORITY_ORDER",
    "CONFIG_MERGE_ORDER",
    "LogLevel",
    "LogFormatter",
    "LogHandler",
    "Logger",

    # Core Exception Hierarchy
    "AutomationError",
    "ElementError",
    "ElementNotFoundError",
    "ElementNotVisibleError",
    "ElementNotInteractableError",
    "DriverError",
    "DriverInitError",
    "NavigationError",
    "TimeoutError",
    "ConfigurationError",
    "ApiError",
    "ApiRequestError",
    "DataError",
    
    "TestSetupError",
    "TestTeardownError",
    "SecurityError",
    "ResourceError",
    "ReportGenerationError",

    # Internal/Advanced Errors (use with caution)
    "FrameworkError",
] 