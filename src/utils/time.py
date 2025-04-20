from __future__ import annotations
import time
import datetime
from typing import Optional, Union
from src.utils.log.manager import get_logger

class TimeUtils:
    """
    通用时间工具类，支持格式化、解析、等待等常用操作。
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def now_str(self, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        获取当前时间的字符串表示。
        Args:
            fmt: 时间格式
        Returns:
            str: 当前时间字符串
        """
        now = datetime.datetime.now().strftime(fmt)
        self.logger.debug(f"当前时间字符串: {now}")
        return now

    def parse(self, time_str: str, fmt: str = "%Y-%m-%d %H:%M:%S") -> datetime.datetime:
        """
        解析时间字符串为datetime对象。
        Args:
            time_str: 时间字符串
            fmt: 时间格式
        Returns:
            datetime.datetime: 解析结果
        Raises:
            ValueError: 解析失败
        """
        try:
            dt = datetime.datetime.strptime(time_str, fmt)
            self.logger.debug(f"解析时间字符串: {time_str} -> {dt}")
            return dt
        except ValueError as e:
            self.logger.error(f"解析时间字符串失败: {time_str}, 错误: {e}")
            raise

    def format(self, dt: Union[datetime.datetime, float], fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
        """
        格式化datetime对象或时间戳为字符串。
        Args:
            dt: datetime对象或时间戳
            fmt: 时间格式
        Returns:
            str: 格式化字符串
        """
        if isinstance(dt, float):
            dt_obj = datetime.datetime.fromtimestamp(dt)
        else:
            dt_obj = dt
        result = dt_obj.strftime(fmt)
        self.logger.debug(f"格式化时间: {dt} -> {result}")
        return result

    def sleep(self, seconds: float) -> None:
        """
        睡眠指定秒数。
        Args:
            seconds: 睡眠时间（秒）
        """
        self.logger.info(f"睡眠 {seconds} 秒")
        time.sleep(seconds)

    def diff_seconds(self, t1: Union[datetime.datetime, float], t2: Union[datetime.datetime, float]) -> float:
        """
        计算两个时间点的秒数差。
        Args:
            t1: 时间点1（datetime或时间戳）
            t2: 时间点2（datetime或时间戳）
        Returns:
            float: 秒数差
        """
        if isinstance(t1, float):
            t1 = datetime.datetime.fromtimestamp(t1)
        if isinstance(t2, float):
            t2 = datetime.datetime.fromtimestamp(t2)
        diff = (t1 - t2).total_seconds()
        self.logger.debug(f"时间差: {t1} - {t2} = {diff} 秒")
        return diff

    def utcnow_str(self, fmt: str = "%Y-%m-%dT%H:%M:%SZ") -> str:
        """
        获取当前UTC时间的字符串表示。
        Args:
            fmt: 时间格式
        Returns:
            str: 当前UTC时间字符串
        """
        now = datetime.datetime.utcnow().strftime(fmt)
        self.logger.debug(f"当前UTC时间字符串: {now}")
        return now