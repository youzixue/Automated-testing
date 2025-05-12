"""
全局通用pytest固件配置。
提供在所有测试中都可使用的基本固件和帮助函数。
"""
import os
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List, Callable
import pytest
import yaml
from dotenv import load_dotenv
import sys
import time
import allure
import logging

from src.utils.config.manager import get_config
from src.utils.log.manager import get_logger, setup_logging

# 尝试导入 Airtest/Poco 相关模块 (如果未安装则定义虚拟类型)
try:
    from airtest.core.helper import set_logdir
    from airtest.core.api import G, snapshot, connect_device
    from airtest.core.device import Device
    from airtest.core.error import DeviceConnectionError, AdbError, TargetNotFoundError
    from airtest.core.settings import Settings as AirtestSettings
    from airtest.core.android.android import Android
    from poco.drivers.android.uiautomation import AndroidUiautomationPoco
    AIRTEST_AVAILABLE = True
except ImportError:
    # Airtest/Poco 未安装，定义虚拟类型以确保类型提示和代码结构正常
    class Device: pass
    class Android: pass
    class AndroidUiautomationPoco: pass
    G = None
    snapshot = None
    connect_device = None
    set_logdir = None
    DeviceConnectionError = Exception
    AdbError = Exception
    TargetNotFoundError = Exception
    AirtestSettings = type('AirtestSettings', (object,), {'LOG_DIR': ''})
    AIRTEST_AVAILABLE = False
    print("Airtest/Poco 未安装或导入失败，相关功能可能受限。")


@pytest.fixture(scope="session", autouse=True)
def load_env():
    """加载项目根目录下的 .env 文件到环境变量。"""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.is_file():
        load_dotenv(dotenv_path=env_path, verbose=True)
        print(f"Loaded environment variables from: {env_path}")
    else:
        print(f".env file not found at: {env_path}, skipping dotenv loading.")

# 模块级别的全局变量来存储会话配置
session_config_global: Dict[str, Any] | None = None

# captcha_config fixture 已移至 tests/web/conftest.py

def pytest_sessionstart(session):
    """在测试会话开始时执行，配置日志。"""
    env_param = session.config.getoption("--env")
    global session_config_global
    session_config_global = get_config(env=env_param) 
    
    setup_logging(session_config_global)
    logger = get_logger("global_session_start")
    logger.info(f"======== 测试会话开始 (环境: {session_config_global.get('env', '未知')}) ========")
    logger.info(f"使用的 Python 版本: {sys.version}")
    logger.info(f"Pytest 版本: {pytest.__version__}")
    logger.debug(f"会话配置已加载: {session_config_global}")

def pytest_sessionfinish(session):
    """在测试会话结束时执行。"""
    logger = get_logger("global_session_finish")
    logger.info("======== 测试会话结束 ========")
    # 可在此处添加全局清理逻辑

def pytest_addoption(parser):
    """添加命令行选项。"""
    parser.addoption(
        "--env", action="store", default="test", help="指定运行环境 (dev, test, uat, prod)"
    )

# --- Helper Function for Device/Poco Setup ---
def _setup_device_poco_session(config: Dict[str, Any], 
                                device_uri_keys: List[str], 
                                timeout_keys: List[str],
                                platform_logger: logging.Logger) -> Tuple[Optional[Device], Optional[Any], int]:
    """(Helper) 连接设备, 初始化 Poco, 并计算超时时间."""
    if not AIRTEST_AVAILABLE:
        platform_logger.error("Airtest/Poco 不可用，无法设置设备会话。")
        return None, None, 20 # 返回默认超时

    # 1. Get ANDROID_SERIAL
    actual_android_serial = os.environ.get("ANDROID_SERIAL")
    platform_logger.info(f"ANDROID_SERIAL environment variable: '{actual_android_serial}'")

    # 2. Determine initial_device_uri from config
    initial_device_uri_from_config = None
    for key_path in device_uri_keys:
        keys = key_path.split('.')
        value = config
        try:
            for key in keys:
                value = value[key]
            if isinstance(value, str) and value.strip(): # Ensure value is a non-empty string
                initial_device_uri_from_config = value.strip()
                platform_logger.debug(f"Found device_uri '{initial_device_uri_from_config}' in config using key path '{key_path}'")
                break
        except (KeyError, TypeError):
            continue
    platform_logger.info(f"Initial device_uri from config: '{initial_device_uri_from_config}' (attempted keys: {device_uri_keys})")

    # 3. Determine effective_device_uri
    effective_device_uri = None
    is_android_target_by_serial = False

    if actual_android_serial and actual_android_serial.strip():
        effective_device_uri = f"android:///{actual_android_serial.strip()}"
        is_android_target_by_serial = True
        platform_logger.info(f"ANDROID_SERIAL is set. Using it as effective_device_uri: '{effective_device_uri}'")
    elif initial_device_uri_from_config:
        effective_device_uri = initial_device_uri_from_config
        platform_logger.info(f"ANDROID_SERIAL not set or empty. Using device_uri from config: '{effective_device_uri}'")
    else:
        platform_logger.error(f"Critical: Neither ANDROID_SERIAL env var nor a valid device URI in config (keys: {device_uri_keys}) was found.")
        pytest.fail(f"No device target specified (ANDROID_SERIAL or config URI). This is a configuration error.")
        # Should not reach here due to pytest.fail, but as a fallback:
        return None, None, 20 
            
    # Timeout Calculation (existing logic is fine)
    timeout_from_config = None
    for key_path in timeout_keys:
        keys = key_path.split('.')
        value = config
        try:
            for key in keys:
                value = value[key]
            timeout_from_config = value
            break
        except (KeyError, TypeError):
            continue
            
    default_timeout = 20
    timeout = default_timeout
    if timeout_from_config is not None:
        try:
            if isinstance(timeout_from_config, str):
                timeout = int(float(timeout_from_config))
            else:
                timeout = int(timeout_from_config)
            platform_logger.debug(f"Using timeout value: {timeout} (type: {type(timeout)}), from config: '{timeout_from_config}'")
        except (ValueError, TypeError):
            platform_logger.warning(f"Configured timeout '{timeout_from_config}' is invalid, using default {default_timeout}s.")
            timeout = default_timeout
    else:
        platform_logger.debug(f"No timeout configured (keys: {timeout_keys}), using default {default_timeout}s.")

    device: Optional[Device] = None
    poco: Optional[Any] = None
    platform_logger.info(f"Attempting to connect to device using effective URI: '{effective_device_uri}'...")
    
    try:
        # 4. Call connect_device
        device = connect_device(effective_device_uri)
        platform_logger.info(f"Device connection successful: {device} (Type: {type(device)}) for URI: '{effective_device_uri}'")
        
        if G:
            G.DEVICE = device

        # 5. Poco Initialization
        # Determine platform primarily by `isinstance(device, Android)` after connection
        if isinstance(device, Android):
            platform_logger.info("Device is instance of Android. Initializing AndroidUiautomationPoco...")
            poco = AndroidUiautomationPoco(device=device, use_airtest_input=True, screenshot_each_action=False)
            platform_logger.info("Poco (AndroidUiautomationPoco) initialized.")
        elif "ios" in effective_device_uri.lower() and not isinstance(device, Android): 
            # This case handles if URI clearly says "ios" and it's not an Android instance
            platform_logger.info("Effective URI suggests iOS and not an Android instance. Attempting IosUiautomationPoco...")
            try:
                from poco.drivers.ios.uiautomation import IosUiautomationPoco
                poco = IosUiautomationPoco(device=device)
                platform_logger.info("Poco (IosUiautomationPoco) initialized successfully.")
            except ImportError:
                 platform_logger.warning("Import IosUiautomationPoco failed. iOS Poco features will be unavailable.")
                 poco = None 
            except Exception as ios_init_error:
                 platform_logger.error(f"Error initializing IosUiautomationPoco: {ios_init_error}", exc_info=True)
                 poco = None 
        elif is_android_target_by_serial and not isinstance(device, Android):
            # Fallback: ANDROID_SERIAL was used (implying Android), but device isn't an Android instance.
            # This might happen with some emulators or indirect connections. Try AndroidPoco.
            platform_logger.warning(f"ANDROID_SERIAL was used, but connected device type is {type(device)} (not Android instance). Attempting AndroidUiautomationPoco as a fallback.")
            try:
                poco = AndroidUiautomationPoco(device=device, use_airtest_input=True, screenshot_each_action=False)
                platform_logger.info("Poco (AndroidUiautomationPoco) initialized via fallback for ANDROID_SERIAL case.")
            except Exception as e_poco_fallback:
                platform_logger.error(f"Fallback AndroidUiautomationPoco initialization failed: {e_poco_fallback}", exc_info=True)
                poco = None
        else: # Cannot determine platform for Poco
            platform_logger.error(f"Cannot determine platform type for Poco initialization from device type ({type(device)}) or URI ({effective_device_uri}). Poco will not be initialized.")
            poco = None
        
        if G:
            G.POCO = poco
        platform_logger.info("Device and Poco instances (if initialized) set to G (if G is available).")
        
        return device, poco, timeout
        
    # 6. Enhanced Exception Handling for connection phase
    except IndexError as ie: 
        platform_logger.error(f"Airtest IndexError during device connection for URI '{effective_device_uri}': {ie}. This often means 'ADB devices not found'.", exc_info=True)
        pytest.skip(f"Skipping test due to Airtest IndexError (likely ADB devices not found or access issue) for '{effective_device_uri}': {ie}")
    except AdbError as adbe:
        platform_logger.error(f"Airtest AdbError during device connection for URI '{effective_device_uri}': {adbe}", exc_info=True)
        pytest.skip(f"Skipping test due to Airtest AdbError for '{effective_device_uri}': {adbe}")
    except DeviceConnectionError as dce: # Airtest's base connection error
        platform_logger.error(f"Airtest DeviceConnectionError for URI '{effective_device_uri}': {dce}", exc_info=True)
        pytest.skip(f"Skipping test due to Airtest DeviceConnectionError for '{effective_device_uri}': {dce}")
    except TargetNotFoundError as tnfe: # If connect_device raises this (less common for connect, more for actions)
        platform_logger.error(f"Airtest TargetNotFoundError during device connection for URI '{effective_device_uri}': {tnfe}", exc_info=True)
        pytest.skip(f"Skipping test due to Airtest TargetNotFoundError for '{effective_device_uri}': {tnfe}")
    except RuntimeError as rte: 
        platform_logger.error(f"RuntimeError during device connection/Poco setup for URI '{effective_device_uri}': {rte}", exc_info=True)
        pytest.skip(f"Skipping test due to RuntimeError for '{effective_device_uri}': {rte}")
    except Exception as e: # Catch-all for other unexpected errors during setup
        platform_logger.error(f"Unexpected critical error during device/Poco setup for URI '{effective_device_uri}': {e}", exc_info=True)
        pytest.skip(f"Skipping test due to unexpected critical error during setup for '{effective_device_uri}': {e}")
    
    # This line should ideally not be reached if an exception occurs and pytest.skip is called.
    # However, as a very final fallback in case skip doesn't behave as expected in some edge pytest version/plugin combo.
    return None, None, timeout

# --- Helper Function for Airtest Screenshot Attachment ---
def _attach_airtest_screenshot(item, report, config_getter: Callable[[], Dict[str, Any]], 
                               logger: logging.Logger, possible_fixture_names: List[str]):
    """(Helper) 查找设备, 截图并附加到 Allure 报告."""
    if not AIRTEST_AVAILABLE:
        logger.warning("Airtest 不可用，跳过截图。")
        return
        
    device: Optional[Device] = None
    # 从 fixtures 查找 device
    if hasattr(item, 'funcargs'):
        for name in possible_fixture_names:
            if name in item.funcargs:
                fixture_value = item.funcargs[name]
                if isinstance(fixture_value, tuple) and len(fixture_value) > 0:
                    potential_device = fixture_value[0]
                    if isinstance(potential_device, Device) and hasattr(potential_device, 'snapshot'): 
                        device = potential_device
                        logger.debug(f"通过 fixture '{name}' 获取到 Airtest 设备对象")
                        break
    
    # 回退到 G.DEVICE
    if not device and G and hasattr(G, 'DEVICE') and G.DEVICE:
         if isinstance(G.DEVICE, Device):
            device = G.DEVICE
            logger.debug("通过全局 G.DEVICE 获取到 Airtest 设备对象")
         else:
             logger.warning(f"全局 G.DEVICE 不是有效的 Device 对象: {type(G.DEVICE)}")

    # 截图并附加
    if device and snapshot:
        try:
            current_config = config_getter()
            report_dir_config = current_config.get('screenshot', {}).get('report_dir', 'output/reports/screenshots')
            project_root = Path(item.fspath).parent.parent.parent 
            absolute_screenshot_dir = project_root / report_dir_config
            os.makedirs(absolute_screenshot_dir, exist_ok=True)

            timestamp = time.strftime('%Y%m%d_%H%M%S')
            safe_nodeid = report.nodeid.replace("::", "_").replace("/", "_").replace("[", "-").replace("]", "")
            max_len = 150
            if len(safe_nodeid) > max_len:
                safe_nodeid = safe_nodeid[-max_len:]
            filename = f"失败截图_{safe_nodeid}_{timestamp}.png"
            absolute_filepath = absolute_screenshot_dir / filename

            logger.info(f"保存失败截图到: {absolute_filepath}")
            snapshot(filename=str(absolute_filepath), msg=f"失败截图: {report.nodeid}", quality=90)

            if os.path.exists(absolute_filepath):
                with open(absolute_filepath, "rb") as f:
                    allure.attach(f.read(), name=filename, attachment_type=allure.attachment_type.PNG)
                logger.info(f"截图 '{filename}' 已成功附加到 Allure 报告")
            else:
                logger.warning(f"截图文件未找到，无法附加到报告: {absolute_filepath}")
        except Exception as e:
            logger.error(f"尝试截图或附加到 Allure 时出错: {e}", exc_info=True)
    else:
        logger.warning("无法获取到 Airtest 设备对象或 snapshot 函数，无法自动截图")

# --- Global Fixtures ---
@pytest.fixture(scope="session")
def config(request) -> Dict[str, Any]:
    """全局配置fixture，从命令行或默认值加载。"""
    global session_config_global
    if session_config_global:
        return session_config_global
    else:
        # Fallback: 如果会话开始时未加载 (例如直接运行单个文件)
        env_param = request.config.getoption("--env")
        fallback_config = get_config(env=env_param)
        setup_logging(fallback_config)
        logger = get_logger("fallback_config_fixture")
        logger.warning("全局会话配置未找到，fixture 重新加载配置。")
        session_config_global = fallback_config 
        return fallback_config