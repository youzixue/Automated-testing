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

    if AIRTEST_AVAILABLE and set_logdir:
        log_dir = session_config_global.get('log', {}).get('file', {}).get('path', 'output/logs/dev')
        airtest_log_dir = os.path.join(Path(log_dir).parent, 'airtest_logs')
        os.makedirs(airtest_log_dir, exist_ok=True)
        try:
            set_logdir(airtest_log_dir)
            logger.info(f"Airtest 日志目录设置为: {airtest_log_dir}")
        except Exception as e:
            logger.warning(f"设置 Airtest 日志目录失败: {e}")

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
        
    device_uri = None
    for key_path in device_uri_keys:
        keys = key_path.split('.')
        value = config
        try:
            for key in keys:
                value = value[key]
            if isinstance(value, str):
                device_uri = value
                break
        except (KeyError, TypeError):
            continue
            
    if not device_uri:
        platform_logger.error(f"在配置中未找到有效的设备 URI (尝试的键: {device_uri_keys})")
        pytest.fail(f"未配置设备 URI (尝试的键: {device_uri_keys})")
        
    # Timeout Calculation
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
            platform_logger.debug(f"使用超时值: {timeout} (类型: {type(timeout)})，来自配置: '{timeout_from_config}'")
        except (ValueError, TypeError):
            platform_logger.warning(f"配置中的超时值 '{timeout_from_config}' 无法转换为整数，使用默认值 {default_timeout}")
            timeout = default_timeout
    else:
        platform_logger.debug(f"未找到超时配置 (尝试的键: {timeout_keys})，使用默认值 {default_timeout}")

    device: Optional[Device] = None
    poco: Optional[Any] = None
    platform_logger.info(f"尝试连接设备: {device_uri}...")
    try:
        device = connect_device(device_uri)
        platform_logger.info(f"设备连接成功: {device} (类型: {type(device)})") 
        
        airtest_log_dir = config.get('log', {}).get('file', {}).get('path', 'output/logs/airtest')
        os.makedirs(airtest_log_dir, exist_ok=True)
        try:
            if set_logdir:
                AirtestSettings.LOG_DIR = airtest_log_dir
                platform_logger.info(f"Airtest 日志目录已设置为: {airtest_log_dir}")
        except Exception as logdir_err:
            platform_logger.warning(f"设置 Airtest 日志目录失败: {logdir_err}")

        if G:
            G.DEVICE = device 

        if isinstance(device, Android):
            platform_logger.info("检测到 Android 平台，初始化 AndroidUiautomationPoco...")
            poco = AndroidUiautomationPoco(device=device, use_airtest_input=True, screenshot_each_action=False)
            platform_logger.info("Poco (AndroidUiautomationPoco) 初始化成功.")
        elif "ios" in device_uri.lower():
            platform_logger.info("检测到 iOS 平台，尝试导入并初始化 IosUiautomationPoco...")
            try:
                from poco.drivers.ios.uiautomation import IosUiautomationPoco
                poco = IosUiautomationPoco(device=device)
                platform_logger.info("Poco (IosUiautomationPoco) 初始化成功.")
            except ImportError:
                 platform_logger.warning("导入 IosUiautomationPoco 失败，iOS Poco 功能将不可用。")
                 poco = None 
            except Exception as ios_init_error:
                 platform_logger.error(f"初始化 IosUiautomationPoco 时发生错误: {ios_init_error}", exc_info=True)
                 poco = None 
        else:
            platform_logger.error(f"无法从设备对象类型 ({type(device)}) 或 URI ({device_uri}) 判断平台类型.")
            device = None 
            poco = None
        
        if G:
            G.POCO = poco
        platform_logger.info("设备和 Poco 实例已设置到全局 G (如果可用)")
        
        return device, poco, timeout
        
    except (DeviceConnectionError, AdbError, TargetNotFoundError, RuntimeError) as e:
        platform_logger.error(f"连接设备或初始化 Poco 失败: {e}", exc_info=True)
        return None, None, timeout 
    except Exception as e:
        platform_logger.error(f"设置设备/Poco 会话时发生未知错误: {e}", exc_info=True)
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