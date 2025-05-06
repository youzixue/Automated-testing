"""
Mobile (Airtest/Poco) 测试专用的 pytest fixtures 配置。
提供 Mobile 测试所需的设备连接、Poco 实例、屏幕对象和截图功能。
"""
import pytest
from typing import Dict, Any, Tuple, Union, Optional
import time
import os
from pathlib import Path

import allure
from airtest.core.api import connect_device, G, snapshot
from airtest.core.device import Device
from airtest.core.error import DeviceConnectionError, AdbError, TargetNotFoundError
from airtest.core.settings import Settings as AirtestSettings
from airtest.core.android.android import Android # 导入 Android 类用于类型检查
from poco.drivers.android.uiautomation import AndroidUiautomationPoco
# 不再在顶层导入 IosUiautomationPoco
# from poco.drivers.ios.uiautomation import IosUiautomationPoco 

from src.utils.log.manager import get_logger
from src.mobile.screens.jiyu_entry_screen import JiyuEntryScreen
from src.common.components.monthly_card_flow import MonthlyCardWebViewFlow
from src.utils.config.manager import get_config 

# 导入 Airtest/Poco 相关，即使不可用也要定义虚拟类型
from tests.conftest import AIRTEST_AVAILABLE, Device, G, snapshot, AdbError, TargetNotFoundError, DeviceConnectionError
# 导入辅助函数
from tests.conftest import _setup_device_poco_session, _attach_airtest_screenshot

logger = get_logger(__name__)

# # --- 不再需要在顶层检查 iOS 驱动 --- #
# IOS_DRIVER_AVAILABLE = False
# try:
#     from poco.drivers.ios.uiautomation import IosUiautomationPoco
#     IOS_DRIVER_AVAILABLE = True
# except ImportError:
#     warnings.warn("iOS UI Automation 驱动未找到。iOS相关测试将无法运行。")
#     logger.warning("iOS UI Automation 驱动未找到。iOS相关测试将无法运行。")

# Mobile 平台特定的设备和 Poco 管理
# 使用 session scope 以优化设备连接次数，但注意会话期间设备状态可能变化
# 如果需要每个测试函数独占设备，改为 function scope
@pytest.fixture(scope="function")
def mobile_device_poco_session(config: Dict[str, Any]) -> Tuple[Optional[Device], Optional[Any], int]:
    """Mobile 设备/Poco 会话 Fixture (Function Scope)，使用全局辅助函数。"""
    platform_logger = get_logger("mobile_device_setup") # 使用项目统一的 logger
    # 定义用于查找配置的键路径 (优先查找 Jiyu 特定 URI)
    device_uri_keys = ['app.jiyu.device_uri', 'app.device_uri']
    timeout_keys = ['airtest.timeouts.default']
    
    # 调用辅助函数进行设置
    device, poco, timeout = _setup_device_poco_session(config, device_uri_keys, timeout_keys, platform_logger)
    
    # 如果辅助函数返回 None (表示设置失败)，则跳过测试
    if device is None and AIRTEST_AVAILABLE: # 只有 Airtest 可用时才需要跳过
        pytest.skip("Mobile device/poco setup failed, skipping test.")
        
    yield device, poco, timeout
    
    # 清理逻辑 (主要是日志)
    # 实际的设备断开和 G 变量清理应该由辅助函数或 Airtest 本身处理（如果需要）
    # 但为了保持日志一致性，可以添加清理日志
    platform_logger.info("[Mobile] Cleaning up mobile_device_poco_session (Function Scope)...")
    # 可选: 如果需要强制清理 G 变量
    # if G:
    #     if hasattr(G, 'DEVICE') and G.DEVICE == device:
    #         G.DEVICE = None
    #     if hasattr(G, 'POCO') and G.POCO == poco:
    #         G.POCO = None
    # 尝试断开设备连接，如果 device 对象存在且有 stop 方法
    if device and hasattr(device, 'stop'):
        try:
            platform_logger.info(f"[Mobile] Attempting to stop/disconnect device: {device}")
            device.stop()
            platform_logger.info(f"[Mobile] Device stop/disconnect successful.")
        except Exception as e:
            platform_logger.warning(f"[Mobile] Error stopping/disconnecting device: {e}", exc_info=True)
            
    time.sleep(0.5) # 确保日志写入
    platform_logger.info("[Mobile] Fixture cleanup finished.")


# --- Screen/Component Fixtures --- 
# 使用 function scope，确保每个测试获取新的屏幕/组件实例
# 依赖 session scope 的 mobile_device_poco_session
@pytest.fixture(scope="function")
def jiyu_entry_screen(mobile_device_poco_session: Tuple[Optional[Device], Optional[Any], int], config: Dict[str, Any]) -> Optional[JiyuEntryScreen]:
    """提供 JiyuEntryScreen 实例。"""
    _, poco, timeout = mobile_device_poco_session
    if poco is None and AIRTEST_AVAILABLE: # 只有 Airtest 可用时才需要跳过
        logger.warning("Poco instance is None, cannot create JiyuEntryScreen.")
        # 返回 None，让测试函数处理
        return None 
    # 如果 Airtest 不可用，poco 总是 None，直接返回 None
    elif not AIRTEST_AVAILABLE:
         return None
    return JiyuEntryScreen(poco=poco, config=config, timeout=timeout)

@pytest.fixture(scope="function")
def monthly_card_webview_flow(mobile_device_poco_session: Tuple[Optional[Device], Optional[Any], int], config: Dict[str, Any]) -> Optional[MonthlyCardWebViewFlow]:
    """为 Mobile 测试提供 MonthlyCardWebViewFlow 组件实例。"""
    device, _, timeout = mobile_device_poco_session
    if device is None and AIRTEST_AVAILABLE:
        logger.warning("Device instance is None, cannot create MonthlyCardWebViewFlow.")
        return None
    elif not AIRTEST_AVAILABLE:
        return None
    return MonthlyCardWebViewFlow(device=device, config=config, timeout=timeout)

# --- Mobile 失败截图 Hook (调用全局辅助函数) ---
@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Pytest hook to take screenshot on mobile test failure and attach to Allure report."""
    outcome = yield
    report = outcome.get_result()

    if report.when == 'call' and report.failed:
        hook_logger = get_logger("mobile_screenshot_hook")
        possible_fixture_names = ['mobile_device_poco_session']
        # 调用全局截图辅助函数
        _attach_airtest_screenshot(item, report, get_config, hook_logger, possible_fixture_names) 