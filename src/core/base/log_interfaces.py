"""
日志接口定义模块。

包含日志相关的抽象基类和枚举。
Moved from src/utils/log/interfaces.py
"""
from abc import ABC, abstractmethod
from enum import Enum, auto

# Define LogLevel Enum
class LogLevel(Enum):
    """日志级别枚举。"""
    DEBUG = auto()
    INFO = auto()
    WARNING = auto()
    ERROR = auto()
    CRITICAL = auto()

# Define LogFormatter Interface
class LogFormatter(ABC):
    """日志格式化器接口。"""
    @abstractmethod
    def format(self, level: LogLevel, message: str, **context) -> str:
        pass

# Define LogHandler Interface
class LogHandler(ABC):
    """日志处理器接口。"""
    @abstractmethod
    def emit(self, level: LogLevel, message: str, **context) -> None:
        pass
    @abstractmethod
    def set_level(self, level: LogLevel) -> None:
        pass
    @abstractmethod
    def set_formatter(self, formatter: LogFormatter) -> None:
        pass

# Define Logger Interface
class Logger(ABC):
    """日志记录器接口。"""
    @abstractmethod
    def debug(self, message: str, **context) -> None:
        pass
    @abstractmethod
    def info(self, message: str, **context) -> None:
        pass
    @abstractmethod
    def warning(self, message: str, **context) -> None:
        pass
    @abstractmethod
    def error(self, message: str, **context) -> None:
        pass
    @abstractmethod
    def critical(self, message: str, **context) -> None:
        pass
    @abstractmethod
    def log(self, level: LogLevel, message: str, **context) -> None:
        pass
    @abstractmethod
    def set_level(self, level: LogLevel) -> None:
        pass
    @abstractmethod
    def add_handler(self, handler: LogHandler) -> None:
        pass
    @abstractmethod
    def remove_handler(self, handler: LogHandler) -> None:
        pass 