"""
随机数据生成工具。

提供各种类型的随机测试数据生成功能，支持自定义约束条件。
"""

import random
import string
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union, Callable

import logging


class DataGenerator:
    """数据生成器。
    
    生成各种类型的随机测试数据，支持自定义约束条件。
    """
    
    def __init__(self, seed: Optional[int] = None):
        """初始化数据生成器。
        
        Args:
            seed: 随机数种子，用于生成可重现的随机数据
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        
        # 设置随机种子（如果提供）
        if seed is not None:
            random.seed(seed)
            self._logger.debug(f"使用随机种子初始化: {seed}")
    
    def random_string(self, 
                     length: int = 8, 
                     chars: str = string.ascii_letters + string.digits,
                     prefix: str = "",
                     suffix: str = "") -> str:
        """生成随机字符串。
        
        Args:
            length: 字符串长度
            chars: 可选字符集
            prefix: 前缀字符串
            suffix: 后缀字符串
            
        Returns:
            随机字符串
            
        Raises:
            ValueError: 长度小于0
        """
        if length < 0:
            raise ValueError("字符串长度不能小于0")
            
        random_part = ''.join(random.choice(chars) for _ in range(length))
        return f"{prefix}{random_part}{suffix}"
    
    def random_email(self, domain: Optional[str] = None) -> str:
        """生成随机电子邮件地址。
        
        Args:
            domain: 电子邮件域名，None使用常见域名随机选择
            
        Returns:
            随机电子邮件地址
        """
        domains = ["example.com", "test.org", "sample.net", "demo.cn"]
        username = self.random_string(8, string.ascii_lowercase + string.digits)
        actual_domain = domain or random.choice(domains)
        
        return f"{username}@{actual_domain}"
    
    def random_phone(self, region: str = "CN") -> str:
        """生成随机电话号码。
        
        Args:
            region: 国家/地区代码，目前支持CN(中国)
            
        Returns:
            随机电话号码
            
        Raises:
            ValueError: 不支持的地区
        """
        if region == "CN":
            # 中国手机号码格式: 1xx xxxx xxxx
            prefixes = ["130", "131", "132", "133", "134", "135", "136", "137", "138", "139",
                       "150", "151", "152", "153", "155", "156", "157", "158", "159",
                       "170", "176", "177", "178", "180", "181", "182", "183", "184", "185",
                       "186", "187", "188", "189", "198", "199"]
            
            prefix = random.choice(prefixes)
            suffix = ''.join(random.choice(string.digits) for _ in range(8))
            return f"{prefix}{suffix}"
        else:
            raise ValueError(f"不支持的地区: {region}")
    
    def random_name(self, region: str = "CN") -> str:
        """生成随机姓名。
        
        Args:
            region: 国家/地区代码，目前支持CN(中国)
            
        Returns:
            随机姓名
        """
        if region == "CN":
            # 中文姓氏
            surnames = [
                "李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
                "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗"
            ]
            
            # 中文名字常用字
            name_chars = [
                "伟", "芳", "娜", "敏", "静", "秀", "明", "丽", "强", "林",
                "洋", "宇", "宁", "建", "文", "涛", "琴", "杰", "楠", "凯"
            ]
            
            # 随机生成1-2个字的名
            name_length = random.randint(1, 2)
            given_name = ''.join(random.choice(name_chars) for _ in range(name_length))
            
            return random.choice(surnames) + given_name
        else:
            # 英文名字
            first_names = [
                "James", "John", "Robert", "Michael", "William",
                "Mary", "Patricia", "Jennifer", "Linda", "Elizabeth"
            ]
            
            last_names = [
                "Smith", "Johnson", "Williams", "Jones", "Brown",
                "Davis", "Miller", "Wilson", "Moore", "Taylor"
            ]
            
            return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def random_date(self, 
                   start_date: Optional[datetime] = None, 
                   end_date: Optional[datetime] = None,
                   date_format: str = "%Y-%m-%d") -> str:
        """生成随机日期。
        
        Args:
            start_date: 起始日期，None表示10年前
            end_date: 结束日期，None表示当前日期
            date_format: 日期格式字符串
            
        Returns:
            格式化的随机日期字符串
        """
        # 默认时间范围：10年前到现在
        if end_date is None:
            end_date = datetime.now()
            
        if start_date is None:
            start_date = end_date - timedelta(days=365 * 10)
            
        # 计算时间戳范围
        start_timestamp = time.mktime(start_date.timetuple())
        end_timestamp = time.mktime(end_date.timetuple())
        
        # 生成随机时间戳并转换为日期
        random_timestamp = start_timestamp + random.random() * (end_timestamp - start_timestamp)
        random_date = datetime.fromtimestamp(random_timestamp)
        
        return random_date.strftime(date_format)
    
    def random_int(self, min_value: int = 0, max_value: int = 100) -> int:
        """生成随机整数。
        
        Args:
            min_value: 最小值（包含）
            max_value: 最大值（包含）
            
        Returns:
            随机整数
        """
        return random.randint(min_value, max_value)
    
    def random_float(self, min_value: float = 0.0, max_value: float = 1.0, precision: int = 2) -> float:
        """生成随机浮点数。
        
        Args:
            min_value: 最小值
            max_value: 最大值
            precision: 小数位数
            
        Returns:
            随机浮点数
        """
        value = min_value + random.random() * (max_value - min_value)
        return round(value, precision)
    
    def random_bool(self, true_probability: float = 0.5) -> bool:
        """生成随机布尔值。
        
        Args:
            true_probability: 生成True的概率(0.0-1.0)
            
        Returns:
            随机布尔值
        """
        return random.random() < true_probability
    
    def random_element(self, elements: List[Any]) -> Any:
        """从列表中随机选择元素。
        
        Args:
            elements: 元素列表
            
        Returns:
            随机选择的元素
            
        Raises:
            ValueError: 列表为空
        """
        if not elements:
            raise ValueError("元素列表不能为空")
            
        return random.choice(elements)
    
    def random_elements(self, elements: List[Any], count: int) -> List[Any]:
        """从列表中随机选择多个元素。
        
        Args:
            elements: 元素列表
            count: 选择的元素数量
            
        Returns:
            随机选择的元素列表
            
        Raises:
            ValueError: 列表为空或count大于列表长度
        """
        if not elements:
            raise ValueError("元素列表不能为空")
            
        if count > len(elements):
            raise ValueError(f"请求的元素数量({count})大于列表长度({len(elements)})")
            
        return random.sample(elements, count)
    
    def random_dict(self, fields: Dict[str, Callable[[], Any]]) -> Dict[str, Any]:
        """生成随机字典数据。
        
        Args:
            fields: 字段及其生成函数的字典
            
        Returns:
            随机字典
        """
        return {key: generator() for key, generator in fields.items()}
    
    def random_uuid(self) -> str:
        """生成随机UUID。
        
        Returns:
            随机UUID字符串
        """
        return str(uuid.uuid4())
    
    def random_ip(self, version: int = 4) -> str:
        """生成随机IP地址。
        
        Args:
            version: IP版本(4或6)
            
        Returns:
            随机IP地址
            
        Raises:
            ValueError: 不支持的IP版本
        """
        if version == 4:
            return f"{self.random_int(1, 255)}.{self.random_int(0, 255)}.{self.random_int(0, 255)}.{self.random_int(1, 254)}"
        elif version == 6:
            parts = [f"{self.random_int(0, 65535):x}" for _ in range(8)]
            return ":".join(parts)
        else:
            raise ValueError(f"不支持的IP版本: {version}")
            
    def random_user_agent(self) -> str:
        """生成随机User-Agent。
        
        Returns:
            随机User-Agent字符串
        """
        # 模拟常见的浏览器和操作系统
        platforms = ["Windows NT 10.0; Win64; x64", "Macintosh; Intel Mac OS X 10_15_7", "X11; Linux x86_64"]
        browsers = [
            ("Chrome", f"{self.random_int(90, 110)}.0.0.0"),
            ("Firefox", f"{self.random_int(90, 109)}.0"),
            ("Safari", f"{self.random_int(600, 605)}.1.15")
        ]
        
        os = self.random_element(platforms)
        browser, version = self.random_element(browsers)
        
        return f"Mozilla/5.0 ({os}) AppleWebKit/537.36 (KHTML, like Gecko) {browser}/{version} Safari/537.36" 