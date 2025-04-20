from __future__ import annotations
import re
from typing import Pattern, Dict, Optional, Type

from src.utils.log.manager import get_logger

logger = get_logger(__name__)

def Singleton(cls: Type) -> Type:
    """
    单例装饰器，用于修饰类，使其实例全局唯一。
    """
    instances: Dict[Type, object] = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

class RegexPatterns:
    """
    常用正则表达式模式集中管理类。
    """

    EMAIL: Pattern = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    PHONE: Pattern = re.compile(r"^1[3-9]\d{9}$")
    URL: Pattern = re.compile(r"^https?://[\w.-]+(?:\.[\w\.-]+)+[/#?]?.*$")
    USERNAME: Pattern = re.compile(r"^[a-zA-Z][a-zA-Z0-9_]{4,15}$")
    PASSWORD: Pattern = re.compile(r"^[\w!@#$%^&*()_+=-]{6,20}$")
    IPV4: Pattern = re.compile(r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$")
    CHINESE: Pattern = re.compile(r"^[\u4e00-\u9fa5]+$")
    ID_CARD: Pattern = re.compile(r"^\d{15}|\d{18}$")

    @classmethod
    def match(cls, pattern: Pattern, text: str) -> bool:
        logger.info(f"[match] 正则匹配开始，pattern: {pattern.pattern}, text: {text}")
        try:
            result = bool(pattern.fullmatch(text))
            logger.info(f"[match] 匹配结果: {result}")
            return result
        except Exception as e:
            logger.error(f"[match] 匹配异常: {e}", exc_info=True)
            return False

    @classmethod
    def search(cls, pattern: Pattern, text: str) -> Optional[re.Match]:
        logger.info(f"[search] 正则搜索开始，pattern: {pattern.pattern}, text: {text}")
        try:
            match = pattern.search(text)
            logger.info(f"[search] 搜索结果: {bool(match)}")
            return match
        except Exception as e:
            logger.error(f"[search] 搜索异常: {e}", exc_info=True)
            return None

    @classmethod
    def get_all_patterns(cls) -> Dict[str, Pattern]:
        logger.info("[get_all_patterns] 获取所有正则模式")
        patterns = {
            "EMAIL": cls.EMAIL,
            "PHONE": cls.PHONE,
            "URL": cls.URL,
            "USERNAME": cls.USERNAME,
            "PASSWORD": cls.PASSWORD,
            "IPV4": cls.IPV4,
            "CHINESE": cls.CHINESE,
            "ID_CARD": cls.ID_CARD,
        }
        logger.debug(f"[get_all_patterns] 模式字典: {list(patterns.keys())}")
        return patterns