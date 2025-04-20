import pytest
import yaml
from typing import Dict, Any

@pytest.fixture(scope="session")
def captcha_config() -> Dict[str, Any]:
    """加载验证码相关配置

    Returns:
        dict: 验证码相关配置字典
    """
    with open("data/web/login/login_data.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("captcha", {})