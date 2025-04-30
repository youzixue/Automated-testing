from __future__ import annotations
import random
import string
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from src.utils.log.manager import get_logger

class DataGenerator:
    """
    通用数据生成器，支持生成用户名、密码、邮箱等常用测试数据。
    """

    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)

    def random_string(self, length: int = 8, chars: str = string.ascii_letters + string.digits) -> str:
        """
        生成指定长度的随机字符串。
        Args:
            length: 字符串长度
            chars: 可选字符集
        Returns:
            str: 随机字符串
        """
        result = ''.join(random.choices(chars, k=length))
        self.logger.debug(f"生成随机字符串: {result}")
        return result

    def random_email(self, prefix_length: int = 6, domain: str = "example.com") -> str:
        """
        生成随机邮箱地址。
        Args:
            prefix_length: 邮箱前缀长度
            domain: 邮箱域名
        Returns:
            str: 随机邮箱
        """
        prefix = self.random_string(prefix_length, string.ascii_lowercase)
        email = f"{prefix}@{domain}"
        self.logger.debug(f"生成随机邮箱: {email}")
        return email

    def random_username(self, length: int = 8) -> str:
        """
        生成随机用户名。
        Args:
            length: 用户名长度
        Returns:
            str: 随机用户名
        """
        username = self.random_string(length, string.ascii_lowercase)
        self.logger.debug(f"生成随机用户名: {username}")
        return username

    def random_password(self, length: int = 12) -> str:
        """
        生成随机密码，包含大小写字母、数字和特殊字符。
        Args:
            length: 密码长度
        Returns:
            str: 随机密码
        """
        chars = string.ascii_letters + string.digits + "!@#$%^&*()"
        password = self.random_string(length, chars)
        self.logger.debug(f"生成随机密码: {password}")
        return password

    def random_user(self) -> Dict[str, str]:
        """
        生成包含用户名、邮箱、密码的用户信息字典。
        Returns:
            Dict[str, str]: 用户信息
        """
        user = {
            "username": self.random_username(),
            "email": self.random_email(),
            "password": self.random_password()
        }
        self.logger.debug(f"生成随机用户: {user}")
        return user

    def random_users(self, count: int = 5) -> List[Dict[str, str]]:
        """
        批量生成随机用户信息。
        Args:
            count: 用户数量
        Returns:
            List[Dict[str, str]]: 用户信息列表
        """
        users = [self.random_user() for _ in range(count)]
        self.logger.debug(f"批量生成随机用户: {users}")
        return users

    def generate_nonce_str(self, length: int = 20, chars: str = '1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ') -> str:
        """
        生成支付接口所需的随机字符串 (nonce_str)。
        参考微信支付规范，默认使用大小写字母和数字。

        Args:
            length: 随机字符串长度 (默认 20)。
            chars: 允许的字符集。

        Returns:
            随机字符串。
        """
        nonce = self.random_string(length, chars)
        self.logger.debug(f"生成 nonce_str: {nonce}")
        return nonce

    def generate_out_trade_no(self, prefix: str = "") -> str:
        """
        生成商户订单号 (out_trade_no)。
        格式：可选前缀 + YYYYMMDDHHMMSS + 4位随机数。

        Args:
            prefix: 订单号前缀 (可选)。

        Returns:
            商户订单号字符串。
        """
        now_str = datetime.now().strftime("%Y%m%d%H%M%S")
        random_num_str = str(random.randint(1000, 9999))
        out_trade_no = f"{prefix}{now_str}{random_num_str}"
        self.logger.debug(f"生成 out_trade_no: {out_trade_no}")
        return out_trade_no

    def generate_trade_expire_time(self, hours_later: int = 24) -> str:
        """
        生成交易结束时间 (trade_expire_time)。
        格式：YYYYMMDDHHMMSS。

        Args:
            hours_later: 从当前时间开始的小时数 (默认 24 小时后)。

        Returns:
            交易结束时间字符串。
        """
        expire_time = datetime.now() + timedelta(hours=hours_later)
        expire_time_str = expire_time.strftime("%Y%m%d%H%M%S")
        self.logger.debug(f"生成 trade_expire_time ({hours_later}小时后): {expire_time_str}")
        return expire_time_str