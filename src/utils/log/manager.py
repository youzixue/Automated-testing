"""
日志管理模块。

提供统一的日志记录接口，支持日志级别配置、文件输出和控制台输出。
"""

import os
import sys
import logging
import datetime
from pathlib import Path
from typing import Dict, Optional, Union, List, Any, Callable
from abc import ABC, abstractmethod
import time
import inspect

from src.utils.patterns import Singleton
from src.utils.event import EventBus
# from src.core.base.errors import LogError # 移除此导入
# Import logging interfaces from the new location
from src.core.base.log_interfaces import LogLevel, LogFormatter, LogHandler, Logger

class StandardLogFormatter(LogFormatter):
    """标准日志格式化器实现。
    
    将框架日志格式转换为Python标准库格式。
    """
    
    def __init__(self, formatter: Optional[logging.Formatter] = None):
        """初始化格式化器。
        
        Args:
            formatter: Python标准库格式化器
        """
        self._formatter = formatter or logging.Formatter(
            "%(asctime)s [%(levelname)s] [%(name)s] [%(thread)d] - %(message)s"
        )
    
    def format(self, level: LogLevel, message: str, **context) -> str:
        """格式化日志消息。
        
        Args:
            level: 日志级别
            message: 日志消息
            **context: 日志上下文参数
            
        Returns:
            格式化后的日志消息
        """
        # 创建一个LogRecord对象用于格式化
        record = logging.LogRecord(
            name=context.get('name', ''),
            level=self._convert_level(level),
            pathname=context.get('pathname', ''),
            lineno=context.get('lineno', 0),
            msg=message,
            args=(),
            exc_info=context.get('exc_info', None),
            func=context.get('func', None),
            sinfo=context.get('sinfo', None)
        )
        
        # 添加额外的上下文
        for key, value in context.items():
            setattr(record, key, value)
            
        return self._formatter.format(record)
    
    def _convert_level(self, level: LogLevel) -> int:
        """转换日志级别。
        
        Args:
            level: 框架日志级别
            
        Returns:
            Python标准库日志级别
        """
        level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        return level_map.get(level, logging.INFO)


class StandardLogHandler(LogHandler):
    """标准日志处理器实现。
    
    包装Python标准库的日志处理器。
    """
    
    def __init__(self, handler: logging.Handler):
        """初始化处理器。
        
        Args:
            handler: Python标准库处理器
        """
        self._handler = handler
        # Use the standard formatter associated with the handler initially
        self._formatter = StandardLogFormatter(handler.formatter)
        # Store the base level converter for use in emit
        self._level_converter = self._formatter._convert_level
    
    def emit(self, level: LogLevel, message: str, **context) -> None:
        """输出日志消息。
        
        Args:
            level: 日志级别
            message: 日志消息
            **context: 日志上下文参数
        """
        # 转换日志级别 using the stored converter
        std_level = self._level_converter(level)
        
        # 创建LogRecord并发送到处理器
        record = logging.LogRecord(
            name=context.get('name', ''),
            level=std_level,
            pathname=context.get('pathname', ''),
            lineno=context.get('lineno', 0),
            msg=message,
            args=(),
            exc_info=context.get('exc_info', None),
            func=context.get('func', None),
            sinfo=context.get('sinfo', None)
        )
        
        # 添加额外的上下文
        for key, value in context.items():
            if key not in record.__dict__: # Avoid overwriting standard attributes
                 setattr(record, key, value)
            
        self._handler.handle(record)
    
    def set_level(self, level: LogLevel) -> None:
        """设置日志级别。
        
        Args:
            level: 日志级别
        """
        self._handler.setLevel(self._level_converter(level))
    
    def set_formatter(self, formatter: LogFormatter) -> None:
        """设置日志格式化器。
        
        Args:
            formatter: 日志格式化器 (framework interface)
        """
        if not isinstance(formatter, LogFormatter):
             raise TypeError("formatter 必须是 LogFormatter 的实例")
             
        # Store the new framework formatter
        self._formatter = formatter
        
        # Attempt to convert framework formatter to standard logging.Formatter
        # This requires StandardLogFormatter to expose its underlying logging.Formatter
        # Or we need a way to represent any LogFormatter as a logging.Formatter string/config
        # Option 1: Expose underlying formatter (if StandardLogFormatter)
        if isinstance(formatter, StandardLogFormatter):
            std_formatter = formatter._formatter # Access protected member
        else:
            # Option 2: Try to create a generic standard formatter based on the LogFormatter interface?
            # This is difficult. Let's fallback to a default standard formatter if a custom one is provided.
            # Log a warning.
            print(f"警告: 应用非 StandardLogFormatter ({type(formatter).__name__}) 到 StandardLogHandler。将使用默认的标准格式。")
            std_formatter = logging.Formatter(
                 "%(asctime)s [%(levelname)s] [%(name)s] [%(thread)d] - %(message)s")
                 
        self._handler.setFormatter(std_formatter)


class StandardLogger(Logger):
    """标准日志记录器实现。
    
    包装Python标准库的Logger对象。
    
    Attributes:
        _logger: Python标准库Logger对象
        _handlers: 日志处理器列表
    """
    
    def __init__(self, logger: logging.Logger):
        """初始化日志记录器。
        
        Args:
            logger: Python标准库Logger对象
        """
        self._logger = logger
        self._handlers = []
        
        # 包装已有的处理器
        for handler in logger.handlers:
            self._handlers.append(StandardLogHandler(handler))
    
    def debug(self, message: str, **context) -> None:
        """记录调试级别日志。
        
        Args:
            message: 日志消息
            **context: 日志上下文参数
        """
        self._logger.debug(message, **context)
    
    def info(self, message: str, **context) -> None:
        """记录信息级别日志。
        
        Args:
            message: 日志消息
            **context: 日志上下文参数
        """
        self._logger.info(message, **context)
    
    def warning(self, message: str, **context) -> None:
        """记录警告级别日志。
        
        Args:
            message: 日志消息
            **context: 日志上下文参数
        """
        self._logger.warning(message, **context)
    
    def error(self, message: str, **context) -> None:
        """记录错误级别日志。
        
        Args:
            message: 日志消息
            **context: 日志上下文参数
        """
        self._logger.error(message, **context)
    
    def critical(self, message: str, **context) -> None:
        """记录严重错误级别日志。
        
        Args:
            message: 日志消息
            **context: 日志上下文参数
        """
        self._logger.critical(message, **context)
    
    def log(self, level: LogLevel, message: str, **context) -> None:
        """记录指定级别日志。
        
        Args:
            level: 日志级别
            message: 日志消息
            **context: 日志上下文参数
        """
        level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        std_level = level_map.get(level, logging.INFO)
        self._logger.log(std_level, message, **context)
    
    def set_level(self, level: LogLevel) -> None:
        """设置日志级别。
        
        Args:
            level: 日志级别
        """
        level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.CRITICAL: logging.CRITICAL
        }
        std_level = level_map.get(level, logging.INFO)
        self._logger.setLevel(std_level)
    
    def add_handler(self, handler: LogHandler) -> None:
        """添加日志处理器。
        
        Args:
            handler: 日志处理器
        """
        if isinstance(handler, StandardLogHandler):
            # 如果是StandardLogHandler，直接添加其内部处理器
            self._logger.addHandler(handler._handler)
        
        self._handlers.append(handler)
    
    def remove_handler(self, handler: LogHandler) -> None:
        """移除日志处理器。
        
        Args:
            handler: 日志处理器
        """
        if isinstance(handler, StandardLogHandler):
            # 如果是StandardLogHandler，移除其内部处理器
            self._logger.removeHandler(handler._handler)
        
        if handler in self._handlers:
            self._handlers.remove(handler)


class LogManager(Singleton):
    """日志管理器实现。
    
    提供统一的日志记录接口，支持多种日志级别和输出方式。
    支持控制台和文件输出，以及自定义格式。
    通过事件总线订阅配置变更，避免循环依赖。
    
    Attributes:
        log_dir: 日志文件目录
        log_level: 日志级别
        log_format: 日志格式
        console_output: 是否输出到控制台
        file_output: 是否输出到文件
    """
    
    # 配置键名常量
    CONFIG_LOG_DIR = "log.dir"
    CONFIG_LOG_LEVEL = "log.level"
    CONFIG_LOG_FORMAT = "log.format"
    CONFIG_CONSOLE_ENABLED = "log.console.enabled"
    CONFIG_FILE_ENABLED = "log.file.enabled"
    CONFIG_FILE_MAX_SIZE = "log.file.max_size"
    CONFIG_FILE_BACKUP_COUNT = "log.file.backup_count"
    
    def __init__(self, config_provider: Optional[Callable[[], Any]] = None):
        """初始化日志管理器。
        
        Args:
            config_provider: 配置提供者函数，用于解决循环依赖
        """
        # 避免重复初始化
        if getattr(self, "_initialized", False):
            return
        
        # 初始化父类
        Singleton.__init__(self)
        
        # 保存配置提供者函数
        self._config_provider = config_provider
        
        # 初始化配置 - 懒加载，只在需要时获取配置
        self._config = None
        
        # 日志配置默认值
        self._log_dir = "logs"
        self._log_level = logging.INFO
        self._log_format = "%(asctime)s [%(levelname)s] [%(name)s] [%(thread)d] - %(message)s"
        self._console_output = True
        self._file_output = False
        self._max_file_size = 10 * 1024 * 1024  # 默认10MB
        self._backup_count = 5
        
        # 根日志记录器
        self._root_logger = logging.getLogger()
        
        # 初始化日志系统 - 使用默认配置
        self._setup_logging()
        
        # 尝试从配置中加载设置
        self._load_config()
        
        # 订阅配置变更事件 - 延迟订阅，避免在导入时触发
        self._subscribe_to_config_events()
        
        # 标记为已初始化
        self._initialized = True
    
    def _create_logger(self, name: str) -> Logger:
        """创建新的日志记录器。
        
        实现BaseLogManager中的抽象方法，创建StandardLogger包装器。
        
        Args:
            name: 日志记录器名称
            
        Returns:
            新创建的日志记录器
        """
        # 创建Python标准库logger
        std_logger = logging.getLogger(name)
        
        # 使用StandardLogger包装
        return StandardLogger(std_logger)
    
    def _subscribe_to_config_events(self):
        """订阅配置相关事件。"""
        try:
            # 尝试导入ConfigManager以获取事件名称常量
            from src.utils.config.manager import ConfigManager
            
            # 订阅配置变更事件
            EventBus.subscribe(ConfigManager.EVENT_CONFIG_CHANGED, self._on_config_changed)
            
            # 订阅配置重载事件
            EventBus.subscribe(ConfigManager.EVENT_CONFIG_RELOADED, self._on_config_reloaded)
            
            # 创建临时日志记录器用于初始日志
            logger = logging.getLogger(self.__class__.__name__)
            logger.debug("已订阅配置变更事件")
            
        except ImportError:
            # 导入失败时不订阅事件，使用默认配置
            pass
    
    def _on_config_changed(self, **kwargs):
        """配置变更事件处理函数。
        
        Args:
            **kwargs: 事件参数，包含key、value等
        """
        # 获取变更的配置项
        key = kwargs.get('key', '')
        value = kwargs.get('value')
        
        # 处理日志相关配置变更
        if key == self.CONFIG_LOG_LEVEL:
            self._update_log_level(value)
        elif key == self.CONFIG_LOG_FORMAT:
            self._update_log_format(value)
        elif key == self.CONFIG_LOG_DIR:
            self._log_dir = value
        elif key == self.CONFIG_CONSOLE_ENABLED:
            self._update_console_output(value)
        elif key == self.CONFIG_FILE_ENABLED:
            self._update_file_output(value)
        elif key == self.CONFIG_FILE_MAX_SIZE:
            self._max_file_size = value
        elif key == self.CONFIG_FILE_BACKUP_COUNT:
            self._backup_count = value
    
    def _on_config_reloaded(self, **kwargs):
        """配置重载事件处理函数。
        
        Args:
            **kwargs: 事件参数
        """
        # 重新加载所有日志配置
        self.reload_config()
    
    def _update_log_level(self, level_value):
        """更新日志级别。
        
        Args:
            level_value: 日志级别值，可以是字符串或整数
        """
        if isinstance(level_value, str):
            level = self._get_log_level(level_value)
        else:
            level = level_value
            
        if level != self._log_level:
            self._log_level = level
            self._root_logger.setLevel(level)
            
            # 更新所有处理器的级别
            for handler in self._root_logger.handlers:
                handler.setLevel(level)
    
    def _update_log_format(self, format_value):
        """更新日志格式。
        
        Args:
            format_value: 新的日志格式字符串
        """
        if format_value != self._log_format:
            self._log_format = format_value
            formatter = logging.Formatter(format_value)
            
            # 更新所有处理器的格式
            for handler in self._root_logger.handlers:
                handler.setFormatter(formatter)
    
    def _update_console_output(self, enabled):
        """更新控制台输出设置。
        
        Args:
            enabled: 是否启用控制台输出
        """
        if enabled != self._console_output:
            self._console_output = enabled
            
            # 移除现有控制台处理器
            for handler in self._root_logger.handlers[:]:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    self._root_logger.removeHandler(handler)
            
            # 如果启用控制台输出，添加新的控制台处理器
            if enabled:
                console_handler = self._create_console_handler()
                self._root_logger.addHandler(console_handler)
    
    def _update_file_output(self, enabled):
        """更新文件输出设置。
        
        Args:
            enabled: 是否启用文件输出
        """
        if enabled != self._file_output:
            self._file_output = enabled
            
            # 移除现有文件处理器
            for handler in self._root_logger.handlers[:]:
                if isinstance(handler, logging.FileHandler):
                    self._root_logger.removeHandler(handler)
            
            # 如果启用文件输出，添加新的文件处理器
            if enabled:
                file_handler = self._create_file_handler("app.log")
                self._root_logger.addHandler(file_handler)
    
    def _get_config(self):
        """获取配置提供者。
        
        延迟导入ConfigManager，避免循环依赖问题。
        
        Returns:
            配置管理器实例
        """
        if self._config is None:
            if self._config_provider:
                self._config = self._config_provider()
            else:
                # 延迟导入
                try:
                    from src.utils.config.manager import get_config
                    self._config = get_config()
                except ImportError:
                    # 如果导入失败，使用默认配置
                    pass
        return self._config
    
    def _load_config(self):
        """从配置中加载日志设置。"""
        config = self._get_config()
        if config is None:
            return
        
        # 加载日志配置
        try:
            self._log_dir = self._get_config_value("log.dir", self._log_dir)
            self._log_level = self._get_log_level(self._get_config_value("log.level", "INFO"))
            self._log_format = self._get_config_value("log.format", self._log_format)
            self._console_output = self._get_config_bool("log.console.enabled", self._console_output)
            self._file_output = self._get_config_bool("log.file.enabled", self._file_output)
            self._max_file_size = self._get_config_value("log.file.max_size", self._max_file_size)
            self._backup_count = self._get_config_value("log.file.backup_count", self._backup_count)
            
            # 创建日志目录
            if self._file_output:
                os.makedirs(self._log_dir, exist_ok=True)
            
            # 重新设置日志
            self._setup_logging()
        except Exception as e:
            # 在日志系统初始化前捕获到异常，使用sys.stderr
            sys.stderr.write(f"Warning: 加载日志配置失败: {e}，使用默认配置\n")
            sys.stderr.flush()
    
    def _get_config_value(self, key: str, default: Any) -> Any:
        """安全获取配置值。
        
        如果配置管理器尚未初始化，返回默认值。
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        try:
            config = self._get_config()
            if config and hasattr(config, "get"):
                return config.get(key, default)
            return default
        except Exception:
            return default
    
    def _get_config_bool(self, key: str, default: bool) -> bool:
        """安全获取布尔配置值。
        
        Args:
            key: 配置键名
            default: 默认值
            
        Returns:
            布尔配置值或默认值
        """
        try:
            config = self._get_config()
            if config and hasattr(config, "get_bool"):
                return config.get_bool(key, default)
            return default
        except Exception:
            return default
    
    def _create_console_handler(self, stream=None) -> logging.Handler:
        """创建控制台日志处理器。
        
        Args:
            stream: 输出流，默认为sys.stdout
            
        Returns:
            控制台日志处理器
        """
        handler = logging.StreamHandler(stream or sys.stdout)
        handler.setFormatter(logging.Formatter(self._log_format))
        handler.setLevel(self._log_level)
        return handler
    
    def _create_file_handler(self, filename: str, max_bytes: int = None, 
                            backup_count: int = None) -> logging.Handler:
        """创建文件日志处理器。
        
        Args:
            filename: 日志文件名
            max_bytes: 单个日志文件最大字节数，None表示使用默认值
            backup_count: 备份文件数量，None表示使用默认值
            
        Returns:
            文件日志处理器，如果创建失败则返回NullHandler
        """
        try:
            from logging.handlers import RotatingFileHandler
            
            # 使用传入参数或默认值
            actual_max_bytes = max_bytes if max_bytes is not None else self._max_file_size
            actual_backup_count = backup_count if backup_count is not None else self._backup_count
            
            # 确保日志目录存在
            os.makedirs(self._log_dir, exist_ok=True)
            
            # 日志文件路径
            log_file = os.path.join(self._log_dir, filename)
            
            # 创建滚动文件处理器
            handler = RotatingFileHandler(
                log_file,
                maxBytes=actual_max_bytes,
                backupCount=actual_backup_count,
                encoding="utf-8"
            )
            handler.setFormatter(logging.Formatter(self._log_format))
            handler.setLevel(self._log_level)
            return handler
            
        except Exception as e:
            # 使用sys.stderr而不是print，因为这可能发生在日志系统初始化过程
            sys.stderr.write(f"Warning: 创建日志文件处理器失败: {e}\n")
            sys.stderr.flush()
            null_handler = logging.NullHandler()
            return null_handler
    
    def _setup_logging(self) -> None:
        """设置日志系统。
        
        配置根日志记录器，添加控制台和文件处理器。
        """
        # 清除现有的处理器
        for handler in self._root_logger.handlers[:]:
            self._root_logger.removeHandler(handler)
        
        # 设置日志级别
        self._root_logger.setLevel(self._log_level)
        
        # 添加控制台处理器
        if self._console_output:
            console_handler = self._create_console_handler()
            self._root_logger.addHandler(console_handler)
        
        # 添加文件处理器
        if self._file_output:
            file_handler = self._create_file_handler("app.log")
            self._root_logger.addHandler(file_handler)
    
    def _get_log_level(self, level_str: str) -> int:
        """转换日志级别字符串为常量。
        
        Args:
            level_str: 日志级别字符串
            
        Returns:
            日志级别常量
        """
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        
        level_str = level_str.upper()
        return level_map.get(level_str, logging.INFO)
    
    def get_logger(self, name: str) -> Logger:
        """获取命名的日志记录器。
        
        Args:
            name: 日志记录器名称
            
        Returns:
            日志记录器实例
        """
        # 获取标准库logger
        std_logger = logging.getLogger(name)
        
        # 包装为Logger接口实例
        return StandardLogger(std_logger)
    
    def set_level(self, level: LogLevel) -> None:
        """设置全局日志级别。
        
        Args:
            level: 日志级别
        """
        # 如果是字符串，转换为Python logging级别
        if isinstance(level, str):
            self._log_level = self._get_log_level(level)
        # 如果是LogLevel枚举，转换为标准库级别
        elif isinstance(level, LogLevel):
            level_map = {
                LogLevel.DEBUG: logging.DEBUG,
                LogLevel.INFO: logging.INFO,
                LogLevel.WARNING: logging.WARNING,
                LogLevel.ERROR: logging.ERROR,
                LogLevel.CRITICAL: logging.CRITICAL
            }
            self._log_level = level_map.get(level, logging.INFO)
        # 如果是整数，直接使用
        else:
            self._log_level = level
        
        # 设置根日志记录器级别
        self._root_logger.setLevel(self._log_level)
    
    def create_file_logger(self, name: str, filename: str) -> Logger:
        """创建文件日志记录器。
        
        创建一个将日志输出到指定文件的日志记录器。
        
        Args:
            name: 日志记录器名称
            filename: 日志文件名（不含路径，将被保存到log_dir目录）
            
        Returns:
            文件日志记录器
        """
        logger = logging.getLogger(name)
        
        # 创建文件处理器
        file_path = os.path.join(self._log_dir, filename)
        handler = self._create_file_handler(file_path)
        
        # 添加处理器
        logger.addHandler(handler)
        
        # 设置级别
        logger.setLevel(self._log_level)
        
        return StandardLogger(logger)
    
    def create_test_logger(self, test_name: str) -> Logger:
        """创建测试日志记录器。
        
        Args:
            test_name: 测试名称
            
        Returns:
            测试日志记录器
        """
        # 安全化测试名称作为文件名
        safe_name = "".join([c if c.isalnum() else "_" for c in test_name])
        log_file = f"test_{safe_name}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # 创建文件日志记录器
        return self.create_file_logger(f"test.{test_name}", log_file)
    
    def reload_config(self) -> None:
        """重新加载日志配置。
        
        从配置管理器重新加载日志配置并应用。
        """
        # 重新加载配置
        self._log_dir = self._get_config_value("log.dir", "logs")
        self._log_level = self._get_log_level(self._get_config_value("log.level", "INFO"))
        self._log_format = self._get_config_value("log.format", 
            "%(asctime)s [%(levelname)s] [%(name)s] [%(thread)d] - %(message)s")
        self._console_output = self._get_config_bool("log.console.enabled", True)
        self._file_output = self._get_config_bool("log.file.enabled", False)
        self._max_file_size = self._get_config_value("log.file.max_size", 10 * 1024 * 1024)
        self._backup_count = self._get_config_value("log.file.backup_count", 5)
        
        # 重新设置日志系统
        self._setup_logging()
    
    @property
    def log_dir(self) -> str:
        """获取日志目录。
        
        Returns:
            日志目录路径
        """
        return self._log_dir
    
    @property
    def log_level(self) -> int:
        """获取日志级别。
        
        Returns:
            日志级别常量
        """
        return self._log_level
    
    @property
    def log_format(self) -> str:
        """获取日志格式。
        
        Returns:
            日志格式字符串
        """
        return self._log_format


def get_logger(name: str) -> Logger:
    """获取指定名称的日志记录器。
    
    这是一个便捷函数，用于获取日志记录器。
    
    Args:
        name: 日志记录器名称
        
    Returns:
        日志记录器实例
    """
    # 使用当前模块中定义的LogManager实现类
    log_manager = LogManager()
    
    # 获取日志记录器
    return log_manager.get_logger(name) 