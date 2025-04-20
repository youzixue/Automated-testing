from __future__ import annotations
import asyncio
from typing import Callable, Any, Optional
from src.utils.log.manager import get_logger
from src.core.base.errors import TimeoutError, ConditionNotMetError

logger = get_logger(__name__)

class Waiter:
    """
    智能等待工具，支持自定义条件、超时和重试间隔。
    """

    def __init__(self, timeout: float = 10, interval: float = 0.5):
        """
        初始化等待器。

        Args:
            timeout: 最大等待时间（秒）
            interval: 重试间隔（秒）
        """
        self.timeout = timeout
        self.interval = interval

    async def until(
        self,
        condition: Callable[[], Any],
        timeout: Optional[float] = None,
        interval: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> Any:
        """
        等待直到条件成立或超时。

        Args:
            condition: 条件函数，返回True/非None表示满足
            timeout: 最大等待时间（秒），None使用默认
            interval: 重试间隔（秒），None使用默认
            error_message: 超时错误信息

        Returns:
            Any: 条件函数的返回值

        Raises:
            TimeoutError: 超时未满足条件
        """
        timeout = timeout if timeout is not None else self.timeout
        interval = interval if interval is not None else self.interval
        start = asyncio.get_event_loop().time()
        last_exception = None

        logger.info(f"[Waiter] 开始等待条件，超时: {timeout}s，间隔: {interval}s")
        while True:
            try:
                result = await condition() if asyncio.iscoroutinefunction(condition) else condition()
                if result:
                    logger.info("[Waiter] 条件满足，等待结束")
                    return result
            except Exception as e:
                last_exception = e
                logger.debug(f"[Waiter] 条件函数异常: {e}")
            await asyncio.sleep(interval)
            if asyncio.get_event_loop().time() - start > timeout:
                msg = error_message or f"等待条件超时({timeout}s)"
                logger.error(f"[Waiter] {msg}")
                if last_exception:
                    raise TimeoutError(f"{msg}，最后异常: {last_exception}")
                raise TimeoutError(msg)

    async def until_not(
        self,
        condition: Callable[[], Any],
        timeout: Optional[float] = None,
        interval: Optional[float] = None,
        error_message: Optional[str] = None
    ) -> None:
        """
        等待直到条件不成立或超时。

        Args:
            condition: 条件函数
            timeout: 最大等待时间（秒），None使用默认
            interval: 重试间隔（秒），None使用默认
            error_message: 超时错误信息

        Raises:
            TimeoutError: 超时条件仍然成立
        """
        timeout = timeout if timeout is not None else self.timeout
        interval = interval if interval is not None else self.interval
        start = asyncio.get_event_loop().time()

        logger.info(f"[Waiter] 开始等待条件不成立，超时: {timeout}s，间隔: {interval}s")
        while True:
            try:
                result = await condition() if asyncio.iscoroutinefunction(condition) else condition()
                if not result:
                    logger.info("[Waiter] 条件不成立，等待结束")
                    return
            except Exception as e:
                logger.debug(f"[Waiter] 条件函数异常: {e}")
                return
            await asyncio.sleep(interval)
            if asyncio.get_event_loop().time() - start > timeout:
                msg = error_message or f"等待条件不成立超时({timeout}s)"
                logger.error(f"[Waiter] {msg}")
                raise TimeoutError(msg)