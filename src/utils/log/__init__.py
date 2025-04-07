"""
日志工具模块。

提供日志管理器和相关工具。
"""

# Import LogManager and get_logger function
from .manager import LogManager, get_logger

# Remove import from old location
# from .interfaces import LogLevel, LogFormatter, LogHandler, Logger

# No need to re-export interfaces from here if they are in core.base

__all__ = [
    "LogManager",
    "get_logger",
    # "LogLevel",  # Don't export from here
    # "LogFormatter",
    # "LogHandler",
    # "Logger"
] 