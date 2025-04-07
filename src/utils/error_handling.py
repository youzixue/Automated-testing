"""
错误处理工具。

提供统一的错误处理机制，包括异常捕获、日志记录和重试逻辑。
"""

import logging
import functools
import time
import traceback
from typing import Any, Callable, List, Optional, Type, TypeVar, Union, cast
from functools import wraps
from pathlib import Path

# 类型变量
T = TypeVar('T')  # 函数返回类型
E = TypeVar('E', bound=Exception)  # 异常类型


def log_exception(logger: Optional[logging.Logger] = None, 
                 level: int = logging.ERROR,
                 reraise: bool = True) -> Callable:
    """异常日志装饰器。
    
    捕获并记录异常，可选择是否重新抛出。
    
    Args:
        logger: 日志记录器，如果为None使用函数模块的记录器
        level: 日志级别
        reraise: 是否重新抛出异常
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            nonlocal logger
            
            # 如果没有提供日志记录器，使用函数模块的记录器
            if logger is None:
                logger = logging.getLogger(func.__module__)
                
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 获取异常详细信息
                exc_info = (type(e), e, traceback.extract_tb(e.__traceback__))
                
                # 记录异常
                logger.log(level, f"异常：{func.__name__}: {e}", exc_info=True)
                
                # 重新抛出异常
                if reraise:
                    raise
                
                # 如果不重新抛出，返回默认值
                return cast(T, None)
                
        return wrapper
    return decorator


def retry(max_attempts: int = 3, 
         retry_interval: float = 1.0,
         backoff_factor: float = 2.0,
         exceptions: Optional[List[Type[Exception]]] = None,
         logger: Optional[logging.Logger] = None) -> Callable:
    """重试装饰器。
    
    在异常发生时自动重试函数，支持退避策略。
    
    Args:
        max_attempts: 最大尝试次数
        retry_interval: 初始重试间隔(秒)
        backoff_factor: 退避因子，每次重试后间隔增大的倍数
        exceptions: 触发重试的异常类型列表，None表示所有异常
        logger: 日志记录器
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            nonlocal logger
            
            # 如果没有提供日志记录器，使用函数模块的记录器
            if logger is None:
                logger = logging.getLogger(func.__module__)
                
            # 记录重试信息的辅助函数
            def _log_retry(attempt: int, wait: float, error: Exception) -> None:
                if logger:
                    logger.warning(
                        f"重试 {func.__name__}：第 {attempt}/{max_attempts} 次尝试失败: {error}. "
                        f"等待 {wait:.2f} 秒后重试."
                    )
            
            attempt = 1
            current_interval = retry_interval
            
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    # 检查是否是指定的异常类型
                    if exceptions is not None and not any(isinstance(e, exc) for exc in exceptions):
                        raise
                    
                    # 检查是否达到最大尝试次数
                    if attempt >= max_attempts:
                        if logger:
                            logger.error(f"{func.__name__} 失败，已达到最大重试次数({max_attempts}): {e}")
                        raise
                    
                    # 记录重试信息
                    _log_retry(attempt, current_interval, e)
                    
                    # 等待后重试
                    time.sleep(current_interval)
                    
                    # 增加下次等待时间
                    current_interval *= backoff_factor
                    attempt += 1
                
        return wrapper
    return decorator


def safe_operation(default_value: Optional[T] = None,
                  exceptions: Optional[List[Type[Exception]]] = None,
                  logger: Optional[logging.Logger] = None,
                  log_level: int = logging.WARNING,
                  error_message: Optional[str] = None) -> Callable:
    """安全操作装饰器。
    
    捕获特定类型的异常并返回默认值，避免异常传播。
    
    Args:
        default_value: 异常发生时返回的默认值
        exceptions: 要捕获的异常类型列表，None表示所有异常
        logger: 日志记录器
        log_level: 日志级别
        error_message: 自定义错误消息
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            nonlocal logger
            
            # 如果没有提供日志记录器，使用函数模块的记录器
            if logger is None:
                logger = logging.getLogger(func.__module__)
                
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 检查是否是指定的异常类型
                if exceptions is not None and not any(isinstance(e, exc) for exc in exceptions):
                    raise
                
                # 记录异常
                if logger:
                    message = error_message or f"{func.__name__} 失败: {e}"
                    logger.log(log_level, message)
                
                # 返回默认值
                return default_value if default_value is not None else cast(T, None)
                
        return wrapper
    return decorator


def convert_exceptions(target_exception: Type[E],
                      source_exceptions: Optional[List[Type[Exception]]] = None,
                      message_template: str = "{original}") -> Callable:
    """异常转换装饰器。
    
    将特定类型的异常转换为目标异常类型，便于统一异常处理。
    
    Args:
        target_exception: 目标异常类型
        source_exceptions: 要转换的源异常类型列表，None表示所有异常
        message_template: 异常消息模板，{original}将被替换为原始异常消息
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 检查是否是指定的异常类型
                if source_exceptions is not None and not any(isinstance(e, exc) for exc in source_exceptions):
                    raise
                
                # 格式化异常消息
                message = message_template.format(original=str(e))
                
                # 转换异常
                raise target_exception(message, cause=e)
                
        return wrapper
    return decorator