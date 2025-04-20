"""
驱动接口（Playwright异步自动化核心接口）。
"""

from abc import ABC, abstractmethod

class BaseDriver(ABC):
    """浏览器驱动基础接口，仅保留异步自动化常用方法。"""
    @abstractmethod
    async def get_element(self, selector: str):
        pass

    @abstractmethod
    async def get_elements(self, selector: str):
        pass

    @abstractmethod
    async def wait_for_element(self, selector: str, timeout: float = None):
        pass

    @abstractmethod
    async def has_element(self, selector: str) -> bool:
        pass

    @abstractmethod
    async def get_screenshot_as_bytes(self):
        pass 