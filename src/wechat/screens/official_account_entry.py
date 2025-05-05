import os
from typing import Dict, Any, TYPE_CHECKING

from airtest.core.api import Template, touch, wait
from airtest.core.error import TargetNotFoundError

from src.utils.log.manager import get_logger

if TYPE_CHECKING:
    from airtest.core.device import Device

# --- 图像模板路径 ---
WECHAT_IMAGE_ROOT = os.path.join("data", "wechat", "images")
PARKING_IMAGE = Template(rf"{WECHAT_IMAGE_ROOT}/parking_image.png")

class OfficialAccountEntryScreen:
    """封装微信公众号进入月卡 WebView 前的特定导航步骤.

    主要负责在进入公众号后点击"停车缴费"按钮。
    """

    def __init__(self, device: 'Device', config: Dict[str, Any]):
        """初始化公众号入口屏幕对象.

        Args:
            device: Airtest 设备对象.
            config: 加载后的项目配置字典.
        """
        self.device = device # 可能未来需要 device
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.timeout = self.config.get('airtest', {}).get('timeouts', {}).get('default', 20)
        self.parking_payment_template = PARKING_IMAGE
        self.description = "停车缴费"

    def click_parking_payment(self):
        """等待并点击公众号内的"停车缴费"按钮.

        Raises:
            AssertionError: 如果无法找到或点击按钮。
        """
        self.logger.info(f"在公众号内查找并点击 '{self.description}'...")
        try:
            self.logger.debug(f"等待 '{self.description}' 图像出现...")
            wait(self.parking_payment_template, timeout=self.timeout)
            self.logger.debug(f"'{self.description}' 图像已找到.")
            touch(self.parking_payment_template)
            self.logger.info(f"已点击 '{self.description}'。")

        except TargetNotFoundError as e:
            error_msg = f"公众号导航失败：未找到预期元素 '{self.description}': {e}"
            self.logger.error(error_msg)
            # 截图由调用者处理
            raise AssertionError(error_msg) from e
        except Exception as e:
            error_msg = f"点击 '{self.description}' 时发生意外错误: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise AssertionError(error_msg) from e 