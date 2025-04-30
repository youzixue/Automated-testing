"""
全局通用pytest固件配置。
提供在所有测试中都可使用的基本固件和帮助函数。
"""
import os
from pathlib import Path
from typing import Dict, Any

import pytest
import yaml
from dotenv import load_dotenv

# 在所有测试运行之前加载 .env 文件
# 使用 autouse=True 和 session scope 确保它在会话开始时自动运行一次
@pytest.fixture(scope="session", autouse=True)
def load_env():
    """加载项目根目录下的 .env 文件到环境变量。"""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.is_file():
        load_dotenv(dotenv_path=env_path, verbose=True)
        print(f"Loaded environment variables from: {env_path}")
    else:
        print(f".env file not found at: {env_path}, skipping dotenv loading.")

@pytest.fixture(scope="session")
def captcha_config() -> Dict[str, Any]:
    """加载验证码相关配置

    Returns:
        Dict[str, Any]: 验证码相关配置字典
    """
    with open("data/web/login/login_data.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("captcha", {})