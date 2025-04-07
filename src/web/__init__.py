"""
Web自动化平台实现。

包含基于Playwright的WebDriver、WebElement、PageObject等实现。
"""

# 导出Web平台的关键组件
from .driver import WebDriver
from .element import WebElement
from .wait import PlaywrightWaitStrategy

# 导出Web相关的工具类 (如果需要)
from .utils.form_validator import FormValidator

__all__ = [
    "WebDriver",
    "WebElement",
    "PlaywrightWaitStrategy",
    "FormValidator",
]

# 初始化日志
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
