"""
事件总线模块。

提供组件间松耦合的事件发布-订阅机制，支持异步事件处理。
"""

import logging
import threading
import asyncio
from typing import Any, Callable, Dict, List, Set, Optional, Union, Awaitable


class EventBus:
    """事件总线实现。
    
    提供基于发布-订阅模式的事件处理机制，允许组件之间松耦合通信。
    支持同步和异步事件处理。
    
    Attributes:
        _handlers: 事件名称到处理函数列表的映射
        _async_handlers: 事件名称到异步处理函数列表的映射
        _logger: 日志记录器
    """
    
    # 类变量用于全局事件处理
    _handlers: Dict[str, List[Callable]] = {}
    _async_handlers: Dict[str, List[Callable[..., Awaitable]]] = {}
    _lock = threading.RLock()
    _logger = logging.getLogger("EventBus")
    
    @classmethod
    def subscribe(cls, event_name: str, handler: Callable) -> None:
        """订阅事件。
        
        Args:
            event_name: 事件名称
            handler: 事件处理函数，可以是同步或异步函数
        """
        with cls._lock:
            # 检查是否为异步处理函数
            is_async = asyncio.iscoroutinefunction(handler)
            
            if is_async:
                if event_name not in cls._async_handlers:
                    cls._async_handlers[event_name] = []
                handlers = cls._async_handlers[event_name]
            else:
                if event_name not in cls._handlers:
                    cls._handlers[event_name] = []
                handlers = cls._handlers[event_name]
                
            if handler not in handlers:
                handlers.append(handler)
                cls._logger.debug(f"订阅事件: {event_name} -> {handler.__name__}")
    
    @classmethod
    def unsubscribe(cls, event_name: str, handler: Callable) -> bool:
        """取消订阅事件。
        
        Args:
            event_name: 事件名称
            handler: 事件处理函数
            
        Returns:
            是否成功取消订阅
        """
        with cls._lock:
            # 检查同步处理函数
            if event_name in cls._handlers:
                handlers = cls._handlers[event_name]
                if handler in handlers:
                    handlers.remove(handler)
                    cls._logger.debug(f"取消订阅事件: {event_name} -> {handler.__name__}")
                    return True
            
            # 检查异步处理函数
            if event_name in cls._async_handlers:
                handlers = cls._async_handlers[event_name]
                if handler in handlers:
                    handlers.remove(handler)
                    cls._logger.debug(f"取消订阅异步事件: {event_name} -> {handler.__name__}")
                    return True
                    
            return False
    
    @classmethod
    def publish(cls, event_name: str, *args: Any, **kwargs: Any) -> None:
        """发布事件。
        
        同步调用所有订阅的同步处理函数，并在后台线程执行异步处理函数。
        
        Args:
            event_name: 事件名称
            *args: 事件参数
            **kwargs: 事件关键字参数
        """
        cls._logger.debug(f"发布事件: {event_name}")
        
        # 调用同步处理函数
        if event_name in cls._handlers:
            handlers = cls._handlers[event_name].copy()  # 复制列表防止处理过程中修改
            for handler in handlers:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    cls._logger.error(f"处理事件 {event_name} 出错: {e}", exc_info=True)
        
        # 创建任务运行异步处理函数
        if event_name in cls._async_handlers:
            handlers = cls._async_handlers[event_name].copy()
            if handlers:
                # 在后台线程中创建事件循环执行异步处理函数
                threading.Thread(
                    target=cls._run_async_handlers, 
                    args=(event_name, handlers, args, kwargs), 
                    daemon=True
                ).start()
    
    @classmethod
    def publish_async(cls, event_name: str, *args: Any, **kwargs: Any) -> asyncio.Future:
        """异步发布事件。
        
        Args:
            event_name: 事件名称
            *args: 事件参数
            **kwargs: 事件关键字参数
            
        Returns:
            表示异步任务完成的Future对象
        """
        cls._logger.debug(f"异步发布事件: {event_name}")
        
        # 获取或创建事件循环
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # 创建并返回用于执行所有处理函数的任务
        future = asyncio.ensure_future(cls._process_event_async(event_name, *args, **kwargs))
        return future
    
    @classmethod
    async def _process_event_async(cls, event_name: str, *args: Any, **kwargs: Any) -> None:
        """异步处理事件。
        
        Args:
            event_name: 事件名称
            *args: 事件参数
            **kwargs: 事件关键字参数
        """
        # 运行同步处理函数
        if event_name in cls._handlers:
            handlers = cls._handlers[event_name].copy()
            for handler in handlers:
                try:
                    # 在事件循环中执行同步函数
                    await asyncio.to_thread(handler, *args, **kwargs)
                except Exception as e:
                    cls._logger.error(f"异步处理同步事件 {event_name} 出错: {e}", exc_info=True)
        
        # 运行异步处理函数
        if event_name in cls._async_handlers:
            handlers = cls._async_handlers[event_name].copy()
            tasks = []
            for handler in handlers:
                try:
                    # 创建任务
                    task = asyncio.create_task(handler(*args, **kwargs))
                    tasks.append(task)
                except Exception as e:
                    cls._logger.error(f"创建异步事件 {event_name} 任务出错: {e}", exc_info=True)
            
            # 等待所有异步任务完成
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
    
    @classmethod
    def _run_async_handlers(cls, event_name: str, handlers: List[Callable[..., Awaitable]], 
                           args: tuple, kwargs: dict) -> None:
        """在新线程中执行异步处理函数。
        
        Args:
            event_name: 事件名称
            handlers: 异步处理函数列表
            args: 事件参数
            kwargs: 事件关键字参数
        """
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # 创建所有异步处理函数的任务
            tasks = []
            for handler in handlers:
                try:
                    task = loop.create_task(handler(*args, **kwargs))
                    tasks.append(task)
                except Exception as e:
                    cls._logger.error(f"创建异步事件 {event_name} 任务出错: {e}", exc_info=True)
            
            # 运行所有任务
            if tasks:
                loop.run_until_complete(asyncio.gather(*tasks, return_exceptions=True))
        finally:
            # 关闭事件循环
            try:
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()
            except Exception as e:
                cls._logger.error(f"关闭事件循环出错: {e}", exc_info=True)
    
    @classmethod
    def clear_all_handlers(cls) -> None:
        """清除所有事件处理函数。
        
        通常用于测试或重置应用程序状态。
        """
        with cls._lock:
            cls._handlers.clear()
            cls._async_handlers.clear()
            cls._logger.debug("已清除所有事件处理函数") 