import time
from typing import TYPE_CHECKING, Dict, Any

from src.utils.log.manager import get_logger
from airtest.core.api import snapshot # 用于失败时截图

if TYPE_CHECKING:
    from airtest.core.device import Device

logger = get_logger(__name__) # 模块级 logger

def wait_for_activity(device: 'Device', expected_activity_suffix: str,
                      timeout: int = 20, check_interval: float = 0.5) -> bool:
    """轮询检查当前顶层 Activity 名称是否包含预期的后缀。

    Args:
        device: Airtest 设备对象.
        expected_activity_suffix: 预期的 Activity 名称后缀 (例如 ".ui.MainActivity").
        timeout: 超时时间 (秒)，默认20秒.
        check_interval: 检查间隔时间 (秒).

    Returns:
        bool: 如果在超时时间内找到匹配的 Activity 则返回 True, 否则返回 False.
    """
    logger.debug(f"[{time.time():.3f}] 开始等待 Activity (包含 '{expected_activity_suffix}', 超时 {timeout}s, 间隔 {check_interval}s)...")
    start_time = time.time()
    activity_found = False
    last_logged_activity = None # 用于避免重复记录相同的Activity

    while time.time() - start_time < timeout:
        current_activity_info = None # 初始化
        try:
            current_activity_info = device.get_top_activity()
            if current_activity_info:
                current_package_name, current_activity_name = current_activity_info
                # 只有当Activity名称变化时才记录，或者首次记录
                if current_activity_name != last_logged_activity:
                    logger.info(f"[{time.time():.3f}] 当前顶层 Activity: {current_package_name}/{current_activity_name}")
                    last_logged_activity = current_activity_name

                if expected_activity_suffix in current_activity_name:
                    activity_found = True
                    logger.info(f"[{time.time():.3f}] 成功检测到目标 Activity: {current_package_name}/{current_activity_name}")
                    break
            else:
                # 只有当获取失败的状态变化时才记录
                if last_logged_activity != "FAILED_TO_GET_ACTIVITY":
                    logger.info(f"[{time.time():.3f}] 未能获取到当前 Activity 信息，稍后重试...")
                    last_logged_activity = "FAILED_TO_GET_ACTIVITY"
        except Exception as e:
            # 只有当错误信息变化时才记录
            error_message = f"获取 Activity 时出错: {e}"
            if last_logged_activity != error_message:
                 logger.warning(f"[{time.time():.3f}] {error_message}", exc_info=False)
                 last_logged_activity = error_message
        time.sleep(check_interval)

    if not activity_found:
        logger.warning(f"[{time.time():.3f}] 超时 {timeout} 秒未检测到 Activity (包含 '{expected_activity_suffix}')")
        # snapshot(msg=f"Activity_{expected_activity_suffix}_未出现截图") # Snapshot call removed
        return False
    else:
        return True 