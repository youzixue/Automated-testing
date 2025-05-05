import pytest
import warnings
from typing import Dict, Any, Tuple, Callable, Union, Optional
import time
import os
from pathlib import Path
import allure

from airtest.core.api import connect_device, G, snapshot
from airtest.core.device import Device
from airtest.core.error import DeviceConnectionError, AdbError, TargetNotFoundError
from airtest.core.settings import Settings as AirtestSettings
from airtest.core.android.android import Android
from poco.drivers.android.uiautomation import AndroidUiautomationPoco

# 导入 Airtest/Poco 相关，即使不可用也要定义虚拟类型
from tests.conftest import AIRTEST_AVAILABLE, Device, G, snapshot, AdbError, TargetNotFoundError, DeviceConnectionError, Android
# 导入辅助函数
from tests.conftest import _setup_device_poco_session, _attach_airtest_screenshot
# 导入日志和配置工具
from src.utils.log.manager import get_logger
from src.utils.config.manager import get_config
# 导入屏幕和组件对象
from src.wechat.screens.official_account_entry import OfficialAccountEntryScreen
from src.common.components.monthly_card_flow import MonthlyCardWebViewFlow

logger = get_logger(__name__)

# 不再需要在顶层检查 iOS 驱动

# --- WeChat Fixtures --- 

@pytest.fixture(scope="session")
def wechat_device_poco_session(config: Dict[str, Any]) -> Tuple[Optional[Device], Optional[Any], int]:
    """WeChat 设备/Poco 会话 Fixture (Session Scope)，使用全局辅助函数。"""
    platform_logger = get_logger("wechat_conftest")
    device_uri_keys = ['app.wechat.device_uri', 'app.device_uri']
    timeout_keys = ['airtest.timeouts.default']
    
    device, poco, timeout = _setup_device_poco_session(config, device_uri_keys, timeout_keys, platform_logger)
    
    if device is None and AIRTEST_AVAILABLE:
        pytest.skip("WeChat device/poco setup failed, skipping test.")
        
    yield device, poco, timeout
    
    # 清理日志
    platform_logger.info("[WeChat] Cleaning up wechat_device_poco_session (Session Scope)...")
    time.sleep(0.5)
    platform_logger.info("[WeChat] Fixture cleanup finished.")

@pytest.fixture(scope="function")
def official_account_entry_screen(wechat_device_poco_session: Tuple[Optional[Device], Optional[Any], int], config: Dict[str, Any]) -> Optional[OfficialAccountEntryScreen]:
    """提供 OfficialAccountEntryScreen 实例。"""
    device, _, timeout = wechat_device_poco_session
    if device is None and AIRTEST_AVAILABLE:
        logger.warning("[WeChat] Device is None, cannot create OfficialAccountEntryScreen.")
        return None
    elif not AIRTEST_AVAILABLE:
        return None
    return OfficialAccountEntryScreen(device=device, config=config)

@pytest.fixture(scope="function")
def monthly_card_webview_flow_wechat(wechat_device_poco_session: Tuple[Optional[Device], Optional[Any], int], config: Dict[str, Any]) -> Optional[MonthlyCardWebViewFlow]:
    """为 WeChat 测试提供 MonthlyCardWebViewFlow 组件实例。"""
    device, _, timeout = wechat_device_poco_session
    if device is None and AIRTEST_AVAILABLE:
        logger.warning("[WeChat] Device is None, cannot create MonthlyCardWebViewFlow.")
        return None
    elif not AIRTEST_AVAILABLE:
        return None
    return MonthlyCardWebViewFlow(device=device, config=config, timeout=timeout)

@pytest.fixture(scope="function")
def wechat_navigator(wechat_device_poco_session: Tuple[Optional[Device], Optional[Any], int], config: Dict[str, Any]) -> Callable[[str, str], None]:
    """提供一个预配置好的微信导航函数。"""
    device, _, _ = wechat_device_poco_session
    if device is None and AIRTEST_AVAILABLE:
        pytest.skip("[WeChat] Device is None, cannot provide navigator.")
    elif not AIRTEST_AVAILABLE:
         pytest.skip("[WeChat] Airtest is not available, cannot provide navigator.")
         
    def _navigate(target_name: str, target_type: str):
        try:
            # 在函数内部导入，确保只在使用时导入
            from src.wechat.utils.navigation import launch_target_in_wechat
            launch_target_in_wechat(device=device, config=config, target_name=target_name, target_type=target_type)
        except ImportError:
            logger.error("[WeChat] 无法导入 launch_target_in_wechat 函数")
            pytest.fail("无法导入导航函数")
        except Exception as nav_err:
             logger.error(f"[WeChat] 导航时出错: {nav_err}", exc_info=True)
             pytest.fail(f"导航失败: {nav_err}")
             
    return _navigate

# --- WeChat 失败截图 Hook (调用全局辅助函数) ---
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """(Hook) WeChat 测试失败时截图并附加到 Allure 报告。"""
    outcome = yield
    report = outcome.get_result()

    if report.when == 'call' and report.failed:
        hook_logger = get_logger("wechat_screenshot_hook") 
        possible_fixture_names = ['wechat_device_poco_session'] 
        # 调用全局截图辅助函数
        _attach_airtest_screenshot(item, report, get_config, hook_logger, possible_fixture_names) 