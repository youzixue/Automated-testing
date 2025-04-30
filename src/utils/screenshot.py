from __future__ import annotations
import os
import datetime
from typing import Optional, Any
from src.utils.log.manager import get_logger
import yaml

logger = get_logger(__name__)

def get_screenshot_dir(report: bool = False) -> str:
    """
    获取截图存放目录，支持原始和报告归档目录。
    Args:
        report: 是否为报告归档目录
    Returns:
        str: 目录路径
    """
    dir_env = "REPORT_SCREENSHOT_DIR" if report else "SCREENSHOT_DIR"
    dir_path = os.environ.get(dir_env)
    if dir_path:
        return dir_path
    try:
        with open("config/settings.yaml", "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        if report:
            return config.get("screenshot", {}).get("report_dir", "output/reports/screenshots")
        else:
            return config.get("screenshot", {}).get("output_dir", "output/screenshots")
    except Exception as e:
        logger.warning(f"读取配置文件失败，使用默认截图目录: {e}")
        return "output/reports/screenshots" if report else "output/screenshots"

async def save_screenshot(page: Any, file_name: str, report: bool = False) -> Optional[str]:
    """
    调用Playwright page的screenshot方法并保存到指定目录。
    Args:
        page: Playwright Page对象，需实现screenshot方法
        file_name: 文件名（不含路径）
        report: 是否保存到报告归档目录
    Returns:
        Optional[str]: 成功返回文件路径，失败返回None
    """
    try:
        img_bytes = await page.screenshot(type="png")
        dir_path = get_screenshot_dir(report)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, file_name)
        with open(file_path, "wb") as f:
            f.write(img_bytes)
        logger.info(f"截图已保存到: {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"保存截图失败: {e}", exc_info=True)
        return None

def gen_screenshot_filename(test_name: str, ext: str = "png") -> str:
    """
    生成带时间戳的截图文件名。
    Args:
        test_name: 用例名或业务标识
        ext: 文件扩展名（默认png）
    Returns:
        str: 文件名
    """
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{test_name}_{ts}.{ext}"