"""
时间处理工具。

提供时间格式化、时间计算、计时器等功能。
"""

import time
import datetime
from enum import Enum
from typing import Union, Optional, Callable, Any, Dict, List, Tuple
from functools import wraps
import logging


class TimeFormat(Enum):
    """常用时间格式枚举。"""
    
    STANDARD = "%Y-%m-%d %H:%M:%S"
    COMPACT = "%Y%m%d%H%M%S"
    DATE_ONLY = "%Y-%m-%d"
    TIME_ONLY = "%H:%M:%S"
    DATETIME_ISO = "%Y-%m-%dT%H:%M:%S"
    DATETIME_ISO_MS = "%Y-%m-%dT%H:%M:%S.%f"
    HUMAN_READABLE = "%Y年%m月%d日 %H时%M分%S秒"
    LOG_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
    FILE_SAFE = "%Y_%m_%d_%H_%M_%S"


class Timer:
    """计时器类，用于性能分析和测量耗时。
    
    支持上下文管理器模式和手动启停。
    """
    
    def __init__(self, autostart: bool = False):
        """初始化计时器。
        
        Args:
            autostart: 是否自动开始计时
        """
        self._start_time = None
        self._end_time = None
        self._running = False
        self._splits: List[Tuple[str, float]] = []
        
        if autostart:
            self.start()
    
    def start(self) -> 'Timer':
        """开始计时。
        
        如果计时器已经在运行，则重置开始时间。
        
        Returns:
            计时器实例
        """
        self._start_time = time.time()
        self._end_time = None
        self._running = True
        self._splits = []
        return self
    
    def stop(self) -> float:
        """停止计时。
        
        Returns:
            从开始到结束的耗时(秒)
        
        Raises:
            RuntimeError: 计时器未启动
        """
        if not self._running:
            raise RuntimeError("计时器未启动")
        
        self._end_time = time.time()
        self._running = False
        return self.elapsed
    
    def reset(self) -> 'Timer':
        """重置计时器。
        
        Returns:
            计时器实例
        """
        self._start_time = None
        self._end_time = None
        self._running = False
        self._splits = []
        return self
    
    def split(self, label: str = "") -> float:
        """记录中间时间点。
        
        Args:
            label: 时间点标签
            
        Returns:
            从开始到当前的耗时(秒)
            
        Raises:
            RuntimeError: 计时器未启动
        """
        if not self._running:
            raise RuntimeError("计时器未启动")
        
        current_time = time.time()
        elapsed = current_time - self._start_time
        self._splits.append((label, elapsed))
        return elapsed
    
    @property
    def elapsed(self) -> float:
        """获取计时器已计时的时间。
        
        Returns:
            已经过的时间(秒)
            
        Raises:
            RuntimeError: 计时器未启动
        """
        if self._start_time is None:
            raise RuntimeError("计时器未启动")
        
        if self._running:
            return time.time() - self._start_time
        return self._end_time - self._start_time
    
    @property
    def splits(self) -> List[Tuple[str, float]]:
        """获取所有中间时间点。
        
        Returns:
            (标签, 耗时)元组列表
        """
        return self._splits.copy()
    
    @property
    def is_running(self) -> bool:
        """检查计时器是否在运行。
        
        Returns:
            计时器运行状态
        """
        return self._running
    
    def __enter__(self) -> 'Timer':
        """开始计时（上下文管理器入口）。
        
        Returns:
            计时器实例
        """
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """停止计时（上下文管理器出口）。"""
        self.stop()
    
    def __str__(self) -> str:
        """返回计时器状态的字符串表示。"""
        if self._start_time is None:
            return "计时器未启动"
        
        elapsed = self.elapsed
        if elapsed < 0.001:
            time_str = f"{elapsed*1000000:.2f}微秒"
        elif elapsed < 1:
            time_str = f"{elapsed*1000:.2f}毫秒"
        else:
            time_str = f"{elapsed:.6f}秒"
            
        status = "运行中" if self._running else "已停止"
        return f"计时器({status}): {time_str}"


class TimeUtils:
    """时间处理工具类。
    
    提供时间格式化、时间计算等静态方法。
    """
    
    @staticmethod
    def now() -> datetime.datetime:
        """获取当前时间。
        
        Returns:
            当前时间的datetime对象
        """
        return datetime.datetime.now()
    
    @staticmethod
    def today() -> datetime.date:
        """获取今天的日期。
        
        Returns:
            今天的date对象
        """
        return datetime.date.today()
    
    @staticmethod
    def timestamp() -> float:
        """获取当前时间戳（秒）。
        
        Returns:
            当前时间戳(秒)
        """
        return time.time()
    
    @staticmethod
    def milliseconds() -> int:
        """获取当前时间戳（毫秒）。
        
        Returns:
            当前时间戳(毫秒)
        """
        return int(time.time() * 1000)
    
    @staticmethod
    def format_time(dt: Optional[Union[datetime.datetime, datetime.date]] = None, 
                   fmt: Union[str, TimeFormat] = TimeFormat.STANDARD) -> str:
        """格式化时间。
        
        Args:
            dt: 要格式化的时间，None表示当前时间
            fmt: 格式化模板
            
        Returns:
            格式化后的时间字符串
        """
        if dt is None:
            dt = TimeUtils.now()
            
        if isinstance(fmt, TimeFormat):
            fmt = fmt.value
            
        return dt.strftime(fmt)
    
    @staticmethod
    def parse_time(time_str: str, fmt: Union[str, TimeFormat] = TimeFormat.STANDARD) -> datetime.datetime:
        """解析时间字符串。
        
        Args:
            time_str: 时间字符串
            fmt: 解析格式
            
        Returns:
            解析后的datetime对象
            
        Raises:
            ValueError: 解析失败
        """
        if isinstance(fmt, TimeFormat):
            fmt = fmt.value
            
        return datetime.datetime.strptime(time_str, fmt)
    
    @staticmethod
    def add_seconds(dt: Optional[datetime.datetime] = None, seconds: float = 0) -> datetime.datetime:
        """增加秒数。
        
        Args:
            dt: 基准时间，None表示当前时间
            seconds: 要增加的秒数，可以为负数
            
        Returns:
            增加后的时间
        """
        if dt is None:
            dt = TimeUtils.now()
            
        return dt + datetime.timedelta(seconds=seconds)
    
    @staticmethod
    def add_days(dt: Optional[Union[datetime.datetime, datetime.date]] = None, days: int = 0) -> Union[datetime.datetime, datetime.date]:
        """增加天数。
        
        Args:
            dt: 基准时间，None表示当前时间
            days: 要增加的天数，可以为负数
            
        Returns:
            增加后的时间
        """
        if dt is None:
            dt = TimeUtils.now()
            
        return dt + datetime.timedelta(days=days)
    
    @staticmethod
    def date_range(start_date: Union[datetime.datetime, datetime.date, str],
                  end_date: Union[datetime.datetime, datetime.date, str],
                  include_end: bool = True) -> List[datetime.date]:
        """获取日期范围。
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            include_end: 是否包含结束日期
            
        Returns:
            日期列表
            
        Raises:
            ValueError: 开始日期晚于结束日期
        """
        # 转换字符串为日期对象
        if isinstance(start_date, str):
            start_date = TimeUtils.parse_time(start_date, TimeFormat.DATE_ONLY).date()
        elif isinstance(start_date, datetime.datetime):
            start_date = start_date.date()
            
        if isinstance(end_date, str):
            end_date = TimeUtils.parse_time(end_date, TimeFormat.DATE_ONLY).date()
        elif isinstance(end_date, datetime.datetime):
            end_date = end_date.date()
        
        # 如果包含结束日期，则增加一天
        if include_end:
            end_date = TimeUtils.add_days(end_date, 1)
        
        if start_date > end_date:
            raise ValueError("开始日期不能晚于结束日期")
            
        result = []
        current = start_date
        while current < end_date:
            result.append(current)
            current = TimeUtils.add_days(current, 1)
            
        return result
    
    @staticmethod
    def is_same_day(dt1: Union[datetime.datetime, datetime.date], 
                   dt2: Union[datetime.datetime, datetime.date]) -> bool:
        """判断两个时间是否为同一天。
        
        Args:
            dt1: 第一个时间
            dt2: 第二个时间
            
        Returns:
            是否为同一天
        """
        if isinstance(dt1, datetime.datetime):
            dt1 = dt1.date()
        if isinstance(dt2, datetime.datetime):
            dt2 = dt2.date()
            
        return dt1 == dt2
    
    @staticmethod
    def days_between(dt1: Union[datetime.datetime, datetime.date], 
                    dt2: Union[datetime.datetime, datetime.date]) -> int:
        """计算两个日期之间相差的天数。
        
        Args:
            dt1: 第一个日期
            dt2: 第二个日期
            
        Returns:
            天数差(绝对值)
        """
        if isinstance(dt1, datetime.datetime):
            dt1 = dt1.date()
        if isinstance(dt2, datetime.datetime):
            dt2 = dt2.date()
            
        delta = abs(dt2 - dt1)
        return delta.days
    
    @staticmethod
    def seconds_between(dt1: datetime.datetime, dt2: datetime.datetime) -> float:
        """计算两个时间之间相差的秒数。
        
        Args:
            dt1: 第一个时间
            dt2: 第二个时间
            
        Returns:
            秒数差(绝对值)
        """
        delta = abs(dt2 - dt1)
        return delta.total_seconds()
    
    @staticmethod
    def format_duration(seconds: float) -> str:
        """格式化时间间隔。
        
        Args:
            seconds: 秒数
            
        Returns:
            格式化后的时间间隔字符串
        """
        if seconds < 0.001:
            return f"{seconds*1000000:.2f}微秒"
        elif seconds < 1:
            return f"{seconds*1000:.2f}毫秒"
        elif seconds < 60:
            return f"{seconds:.2f}秒"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            remaining_seconds = seconds % 60
            return f"{minutes}分{remaining_seconds:.2f}秒"
        else:
            hours = int(seconds / 3600)
            remaining = seconds % 3600
            minutes = int(remaining / 60)
            remaining_seconds = remaining % 60
            return f"{hours}小时{minutes}分{remaining_seconds:.2f}秒"
    
    @staticmethod
    def get_weekday(dt: Optional[Union[datetime.datetime, datetime.date]] = None) -> int:
        """获取星期几。
        
        Args:
            dt: 日期，None表示当前日期
            
        Returns:
            星期几，1-7分别代表星期一到星期日
        """
        if dt is None:
            dt = TimeUtils.today()
            
        if isinstance(dt, datetime.datetime):
            dt = dt.date()
            
        # Python中weekday()返回0-6，0表示星期一
        return dt.weekday() + 1
    
    @staticmethod
    def get_month_first_day(dt: Optional[Union[datetime.datetime, datetime.date]] = None) -> datetime.date:
        """获取月份的第一天。
        
        Args:
            dt: 日期，None表示当前日期
            
        Returns:
            月份第一天的日期
        """
        if dt is None:
            dt = TimeUtils.today()
            
        if isinstance(dt, datetime.datetime):
            dt = dt.date()
            
        return datetime.date(dt.year, dt.month, 1)
    
    @staticmethod
    def get_month_last_day(dt: Optional[Union[datetime.datetime, datetime.date]] = None) -> datetime.date:
        """获取月份的最后一天。
        
        Args:
            dt: 日期，None表示当前日期
            
        Returns:
            月份最后一天的日期
        """
        if dt is None:
            dt = TimeUtils.today()
            
        if isinstance(dt, datetime.datetime):
            dt = dt.date()
            
        # 获取下个月的第一天，然后减去一天
        if dt.month == 12:
            next_month = datetime.date(dt.year + 1, 1, 1)
        else:
            next_month = datetime.date(dt.year, dt.month + 1, 1)
            
        return TimeUtils.add_days(next_month, -1)
    
    @staticmethod
    def get_quarter(dt: Optional[Union[datetime.datetime, datetime.date]] = None) -> int:
        """获取季度。
        
        Args:
            dt: 日期，None表示当前日期
            
        Returns:
            季度(1-4)
        """
        if dt is None:
            dt = TimeUtils.today()
            
        if isinstance(dt, datetime.datetime):
            dt = dt.date()
            
        return (dt.month - 1) // 3 + 1
    
    @staticmethod
    def to_timestamp(dt: datetime.datetime) -> float:
        """将datetime转换为时间戳。
        
        Args:
            dt: 要转换的datetime对象
            
        Returns:
            时间戳(秒)
        """
        return dt.timestamp()
    
    @staticmethod
    def from_timestamp(timestamp: float) -> datetime.datetime:
        """将时间戳转换为datetime。
        
        Args:
            timestamp: 时间戳(秒)
            
        Returns:
            datetime对象
        """
        return datetime.datetime.fromtimestamp(timestamp)
    
    @staticmethod
    def time_it(func: Callable) -> Callable:
        """函数执行时间计时器装饰器。
        
        Args:
            func: 要计时的函数
            
        Returns:
            包装后的函数
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            
            timer = Timer()
            timer.start()
            result = func(*args, **kwargs)
            elapsed = timer.stop()
            logger.debug(f"函数 {func.__name__} 执行耗时: {TimeUtils.format_duration(elapsed)}")
            return result
        return wrapper