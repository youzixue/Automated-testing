from __future__ import annotations
from typing import Callable, Dict, List, Any, Optional
from src.utils.log.manager import get_logger

class EventBus:
    """
    简单事件总线，支持事件订阅、取消订阅和事件发布。
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[..., Any]]] = {}
        self._logger = get_logger(self.__class__.__name__)

    def subscribe(self, event: str, callback: Callable[..., Any]) -> None:
        """
        订阅事件。
        Args:
            event: 事件名
            callback: 回调函数
        """
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)
        self._logger.info(f"[subscribe] 订阅事件: {event} -> {callback.__name__}")

    def unsubscribe(self, event: str, callback: Callable[..., Any]) -> None:
        """
        取消订阅事件。
        Args:
            event: 事件名
            callback: 回调函数
        """
        if event in self._subscribers and callback in self._subscribers[event]:
            self._subscribers[event].remove(callback)
            self._logger.info(f"[unsubscribe] 取消订阅事件: {event} -> {callback.__name__}")

    def publish(self, event: str, *args, **kwargs) -> None:
        """
        发布事件，通知所有订阅者。
        Args:
            event: 事件名
            *args: 回调参数
            **kwargs: 回调参数
        """
        subscribers = self._subscribers.get(event, [])
        self._logger.info(f"[publish] 发布事件: {event}，订阅者数量: {len(subscribers)}")
        for callback in subscribers:
            try:
                callback(*args, **kwargs)
                self._logger.debug(f"[publish] 成功调用回调: {callback.__name__}")
            except Exception as e:
                self._logger.error(f"[publish] 事件回调异常: {callback.__name__}，错误: {e}", exc_info=True)

    def clear(self, event: Optional[str] = None) -> None:
        """
        清除所有订阅者。
        Args:
            event: 事件名（如为None则清除所有事件）
        """
        if event:
            self._subscribers.pop(event, None)
            self._logger.info(f"[clear] 清除事件订阅: {event}")
        else:
            self._subscribers.clear()
            self._logger.info("[clear] 清除所有事件订阅")