"""
Web测试固件。

为Web自动化测试提供pytest fixtures，包括浏览器驱动和配置管理。
"""

import os
import pytest
import yaml
from pathlib import Path
from typing import Any, Dict, Generator, Optional
import logging

from src.web.driver import WebDriver
from src.web.pages import OmpLoginPage, DashboardPage
from src.utils.config.manager import get_config
from src.utils.log.manager import get_logger as get_framework_logger

# Use framework logger
logger = get_framework_logger(__name__)

def _get_env_or_default(env_var: str, default_value: Optional[str] = None) -> Optional[str]:
    """获取环境变量或默认值。
    
    Args:
        env_var: 环境变量名称
        default_value: 默认值
        
    Returns:
        环境变量值或默认值
    """
    return os.environ.get(env_var, default_value)


def _parse_value_with_env(value: str) -> str:
    """解析包含环境变量引用的字符串。
    
    支持形如 ${env:VAR_NAME|default_value} 的格式：
    - 如果环境变量VAR_NAME存在，则使用其值
    - 否则使用default_value作为默认值
    
    Args:
        value: 包含环境变量引用的字符串
        
    Returns:
        解析后的值
    """
    if not isinstance(value, str) or not value.startswith("${env:"):
        return value
        
    # 提取环境变量名称和默认值
    env_part = value[6:-1]  # 去掉 ${env: 和 }
    if "|" in env_part:
        env_name, default = env_part.split("|", 1)
    else:
        env_name, default = env_part, None
        
    return _get_env_or_default(env_name, default)


@pytest.fixture(scope="session")
def web_config() -> Dict[str, Any]:
    """获取Web测试配置。
    
    Returns:
        Web测试配置 (从 DefaultConfigManager 获取)
    """
    config_manager = get_config()
    return config_manager.get("web", {})


@pytest.fixture(scope="session")
def login_data(web_config: Dict[str, Any]) -> Dict[str, Any]:
    """加载登录测试数据。
    
    从YAML文件加载登录测试数据，并处理环境变量引用。
    如果远程环境不可用，会使用备用的本地测试URL。
    
    Returns:
        登录测试数据字典
    """
    fixture_logger = get_framework_logger("fixtures.login_data")
    config_manager = get_config()

    project_root = Path(__file__).resolve().parent.parent.parent
    fixture_logger.debug(f"项目根目录: {project_root}")
    
    data_config = config_manager.get("data", {})
    data_file_path = data_config.get("login_file")
    
    if data_file_path:
        data_file = Path(data_file_path)
        if not data_file.is_absolute():
            data_file = project_root / data_file_path
    else:
        data_file = project_root / "data" / "web" / "login" / "login_data.yaml"
    
    fixture_logger.info(f"使用登录数据文件: {data_file}")

    if not data_file.exists():
         fixture_logger.error(f"登录数据文件未找到: {data_file}")
         pytest.fail(f"登录数据文件未找到: {data_file}", pytrace=False)
         return {}

    try:
        with open(data_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        fixture_logger.error(f"加载登录数据文件 {data_file} 失败: {e}", exc_info=True)
        pytest.fail(f"加载登录数据文件 {data_file} 失败: {e}", pytrace=False)
        return {}
    
    if "users" in data:
        for user_type, user_data in data["users"].items():
            if isinstance(user_data, dict) and "password" in user_data:
                user_data["password"] = _parse_value_with_env(user_data["password"])
    
    env_url = os.environ.get("TEST_LOGIN_URL")
    web_config_from_manager = config_manager.get("web", {})
    config_url = web_config_from_manager.get("base_url")
    data_url = data.get("url")
    
    if env_url:
        data["url"] = env_url
        fixture_logger.info(f"使用环境变量中的测试URL: {env_url}")
    elif config_url:
         data["url"] = config_url
         fixture_logger.info(f"使用配置中的测试URL: {config_url}")
    elif data_url:
         fixture_logger.info(f"使用数据文件中的测试URL: {data_url}")
    else:
         data["url"] = ""
         fixture_logger.warning("未找到登录URL配置，将使用空URL")

    env_backup_url = os.environ.get("BACKUP_TEST_URL")
    config_backup_url = web_config_from_manager.get("backup_url")
    data_backup_url = data.get("backup_url")

    if env_backup_url:
         data["backup_url"] = env_backup_url
    elif config_backup_url:
         data["backup_url"] = config_backup_url
    elif data_backup_url:
         pass
    else:
         data["backup_url"] = ""

    fixture_logger.info(f"主测试URL: {data.get('url', 'N/A')}, 备用URL: {data.get('backup_url', 'N/A')}")
    
    return data


@pytest.fixture
def web_driver() -> Generator[WebDriver, None, None]:
    """创建WebDriver实例。
    
    使用上下文管理器确保资源正确释放。
    
    Returns:
        WebDriver实例
    """
    config_manager = get_config()
    web_config_section = config_manager.get("web", {})

    browser_type = os.environ.get("BROWSER", web_config_section.get("browser", "chromium"))
    headless = os.environ.get("HEADLESS", "").lower() in ["true", "1", "yes"]
    debug_enabled = os.environ.get("DEBUG_MODE", "").lower() in ["true", "1", "yes"]
    slow_mo_str = os.environ.get("SLOW_MO", str(web_config_section.get("slow_mo", 0)))
    slow_mo_speed = int(slow_mo_str.split('#')[0].strip())
    devtools_enabled = os.environ.get("DEVTOOLS_ENABLED", "").lower() in ["true", "1", "yes"]

    extra_kwargs = {}
    if debug_enabled:
        if slow_mo_speed <= 0:
             slow_mo_speed = 500
        if not devtools_enabled:
             devtools_enabled = True
             
    if slow_mo_speed > 0:
         extra_kwargs['slow_mo'] = slow_mo_speed
    if devtools_enabled:
         extra_kwargs['devtools'] = devtools_enabled
         
    launch_options = web_config_section.get("launch_options", {})
    extra_kwargs.update(launch_options)

    logger.info(f"创建WebDriver: browser={browser_type}, headless={headless}, options={extra_kwargs}")
    with WebDriver(browser_type=browser_type, headless=headless, **extra_kwargs) as driver:
        yield driver


@pytest.fixture
def logged_in_driver(web_driver: WebDriver, login_data: Dict[str, Any]) -> Generator[WebDriver, None, None]:
    """提供已登录状态的WebDriver。
    
    先登录系统，然后提供已登录的浏览器驱动。
    
    Args:
        web_driver: WebDriver实例
        login_data: 登录测试数据
        
    Yields:
        已登录状态的WebDriver实例
    """
    url = login_data["url"]
    valid_user = login_data["users"]["valid"]
    
    omp_login_page = OmpLoginPage(web_driver, url)
    omp_login_page.navigate()
    
    dashboard_page = None
    try:
        dashboard_page = omp_login_page.login(
            valid_user["username"], valid_user["password"]
        )
        
        assert dashboard_page.is_loaded(), "登录失败，未能加载仪表盘页面"
        
        yield web_driver
    finally:
        try:
            if dashboard_page and dashboard_page.is_loaded():
                dashboard_page.logout()
        except Exception as e:
            logger.error(f"登出过程中发生错误: {e}") 