"""
全局通用pytest固件配置。
提供在所有测试中都可使用的基本固件和帮助函数。
"""
import os
from pathlib import Path
from typing import Dict, Any

import pytest
import yaml


@pytest.fixture(scope="session")
def captcha_config() -> Dict[str, Any]:
    """加载验证码相关配置

    Returns:
        Dict[str, Any]: 验证码相关配置字典
    """
    with open("data/web/login/login_data.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("captcha", {})