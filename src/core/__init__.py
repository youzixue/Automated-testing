"""
核心模块。

提供自动化测试框架的核心功能和抽象层。
"""

# 从核心抽象层导出所有接口
from src.core.base import *

# 获取base模块的__all__
from src.core import base

__all__ = [
    # 从base模块导出的所有内容
    *base.__all__,
    # 'ReportGenerationError'
] 