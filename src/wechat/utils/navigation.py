import os
import time
from typing import Dict, Any, TYPE_CHECKING

from airtest.core.api import (Template, touch, wait, text, snapshot,
                            start_app, stop_app)
from airtest.core.error import TargetNotFoundError

from src.utils.log.manager import get_logger

if TYPE_CHECKING:
    from airtest.core.device import Device
    from poco.drivers.android.uiautomation import AndroidUiautomationPoco # 或其他 Poco 类型

# --- 图像模板路径 (使用新结构) ---
WECHAT_IMAGE_ROOT = os.path.join("data", "wechat", "images")
SEARCH_ICON_TEMPLATE = Template(rf"{WECHAT_IMAGE_ROOT}/search_image.png")
SOUSUO_INPUT_TEMPLATE = Template(rf"{WECHAT_IMAGE_ROOT}/sousuo.png") # 搜索输入确认图标
MINI_PROGRAM_TEMPLATE = Template(rf"{WECHAT_IMAGE_ROOT}/mini_program.png")
OFFICIAL_ACCOUNT_TEMPLATE = Template(rf"{WECHAT_IMAGE_ROOT}/official_account.png")

def launch_target_in_wechat(device: 'Device', config: Dict[str, Any],
                           target_name: str, target_type: str):
    """启动微信并导航到指定的小程序或公众号.

    Args:
        device: Airtest 设备对象.
        config: 加载后的项目配置字典.
        target_name: 目标小程序或公众号的名称.
        target_type: 目标类型，"小程序" 或 "公众号".

    Raises:
        AssertionError: 如果导航过程失败。
        ValueError: 如果 target_type 无效。
    """
    logger = get_logger(__name__) # 使用模块级 logger
    wechat_package_name = config.get('app', {}).get('wechat', {}).get('package_name', 'com.tencent.mm')
    
    # --- 获取并转换 timeout --- 
    timeout_from_config = config.get('airtest', {}).get('timeouts', {}).get('default', 20)
    try:
        # 尝试转换为整数或浮点数
        if isinstance(timeout_from_config, str):
            timeout = int(timeout_from_config)
        elif isinstance(timeout_from_config, (int, float)):
            timeout = timeout_from_config
        else:
            timeout = float(timeout_from_config) # 最后尝试转 float
        logger.debug(f"[WeChat Nav] 使用超时值: {timeout} (类型: {type(timeout)})，来自配置: '{timeout_from_config}'")
    except (ValueError, TypeError):
        logger.warning(f"[WeChat Nav] 配置中的超时值 '{timeout_from_config}' 无法转换为数字，使用默认值 20")
        timeout = 20
    # --- timeout 处理结束 ---

    logger.info(f"开始启动微信并导航至 '{target_name}' ({target_type})...")

    try:
        # 1. 重启微信确保状态纯净
        logger.debug(f"强制停止微信 ({wechat_package_name})...")
        stop_app(wechat_package_name)
        logger.debug(f"启动微信 ({wechat_package_name})...")
        start_app(wechat_package_name)

        # 2. 等待搜索图标出现并点击 (直接等待此图标作为启动成功的标志)
        logger.debug(f"等待微信加载并出现搜索图标 (超时 {timeout * 1.5}s)...")
        wait(SEARCH_ICON_TEMPLATE, timeout=timeout * 1.5)
        logger.debug("搜索图标已出现，点击搜索图标...")
        touch(SEARCH_ICON_TEMPLATE)

        # --- Removed search box clearing logic --- 
            
        # 3. 输入目标名称
        logger.debug(f"输入目标名称: {target_name}")
        text(target_name)

        # 4. 根据类型点击目标
        logger.debug(f"等待并点击 '{target_type}' 图标...")
        if target_type == "小程序":
            target_template = MINI_PROGRAM_TEMPLATE
        elif target_type == "公众号":
            target_template = OFFICIAL_ACCOUNT_TEMPLATE
        else:
            raise ValueError(f"无效的目标类型: {target_type}，应为 '小程序' 或 '公众号'")

        wait(target_template, timeout=timeout)
        touch(target_template)

        logger.info(f"已成功点击 '{target_name}' ({target_type})，导航操作完成。")
        # 后续的加载等待和特定导航应在调用此函数后进行

    except TargetNotFoundError as e:
        error_msg = f"启动微信导航失败：未找到预期元素 {e}"
        logger.error(error_msg)
        # 截图应由调用者处理
        raise AssertionError(error_msg) from e
    except Exception as e:
        error_msg = f"启动微信导航时发生意外错误: {e}"
        logger.error(error_msg, exc_info=True)
        raise AssertionError(error_msg) from e 