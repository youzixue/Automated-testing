import os
import time
from typing import TYPE_CHECKING, Dict, Any

from airtest.core.api import Template, touch, wait, snapshot
from airtest.core.error import TargetNotFoundError

from src.utils.log.manager import get_logger

# 导入 allure 用于报告附件
import allure

# 显式导入 Device 用于类型注解，避免运行时循环导入
if TYPE_CHECKING:
    from airtest.core.device import Device

# --- 常量定义 (遵循 PEP8) ---
# 图像根目录，使用相对路径，便于跨环境部署
IMAGE_ROOT = "data/common/images/monthly_card"

# --- 图像模板定义 ---
# 使用 f-string 提高可读性，并确保路径正确
MONTH_CARD_IMAGE = Template(rf"{IMAGE_ROOT}/month_card_image.png")
CHECK_FEE_IMAGE = Template(rf"{IMAGE_ROOT}/check_fee_image.png")
RENEW_IMAGE = Template(rf"{IMAGE_ROOT}/renew_image.png")
AGREEMENT_IMAGE = Template(rf"{IMAGE_ROOT}/agreement_image.png")
CONFIRM_PAY_IMAGE = Template(rf"{IMAGE_ROOT}/confirm_pay.png")
SUBMIT_PAY_IMAGE = Template(rf"{IMAGE_ROOT}/submit_pay.png")
PAYMENT_INDICATOR_IMAGE = Template(rf"{IMAGE_ROOT}/pay_option.png")


class MonthlyCardWebViewFlow:
    """封装共享的、基于图像识别的月卡续费到提交支付的 WebView 流程.

    该组件负责执行从点击月卡图标开始，直至点击提交支付按钮结束的
    一系列基于图像识别的操作.
    """

    def __init__(self, device: 'Device', config: Dict[str, Any], timeout: int):
        """初始化流程组件.

        Args:
            device (Device): Airtest 设备对象实例.
            config (Dict[str, Any]): 加载后的项目配置字典.
            timeout (int): 操作的默认超时时间 (秒).
        """
        self.device = device
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.timeout = timeout # 直接使用传入的 timeout
        self.logger.debug(f"MonthlyCardWebViewFlow 使用超时值: {self.timeout}. 图像根目录: {IMAGE_ROOT}")

        self.logger.debug(f"共享月卡 WebView 流程组件已初始化. 图像根目录: {IMAGE_ROOT}")

    def execute_renewal_up_to_confirm_pay(self):
        """执行从点击月卡图标到点击确认支付按钮的共享 WebView 流程.

        Raises:
            AssertionError: 如果在流程中未找到预期元素或发生其他异常.
        """
        self.logger.info("开始执行共享 WebView 月卡续费流程 (至确认支付)...")
        try:
            # 逐步执行图像点击操作，日志清晰记录每一步
            self.logger.debug("等待并点击月卡图标...")
            wait(MONTH_CARD_IMAGE, timeout=self.timeout)
            touch(MONTH_CARD_IMAGE)

            self.logger.debug("等待并点击查费图标...")
            wait(CHECK_FEE_IMAGE, timeout=self.timeout)
            touch(CHECK_FEE_IMAGE)

            self.logger.debug("等待并点击续费图标...")
            wait(RENEW_IMAGE, timeout=self.timeout)
            touch(RENEW_IMAGE)

            self.logger.debug("等待并点击协议图标...")
            wait(AGREEMENT_IMAGE, timeout=self.timeout)
            touch(AGREEMENT_IMAGE)

            self.logger.debug("等待并点击确认支付图标...")
            wait(CONFIRM_PAY_IMAGE, timeout=self.timeout)
            touch(CONFIRM_PAY_IMAGE)

            self.logger.info("共享 WebView 月卡续费流程操作完成（已点击确认支付）。")

        except TargetNotFoundError as e:
            error_msg = f"共享 WebView 流程 (至确认支付) 中未找到预期元素: {e}"
            self.logger.error(error_msg)
            raise AssertionError(error_msg) from e
        except Exception as e:
            error_msg = f"共享 WebView 流程 (至确认支付) 中发生意外错误: {e}"
            self.logger.error(error_msg, exc_info=True)
            raise AssertionError(error_msg) from e

    # --- 辅助方法 ---
    def _wait_and_click(self, template: Template, description: str):
        """封装等待图像出现并点击的操作，包含日志记录."""
        self.logger.debug(f"等待并点击 '{description}'...")
        wait(template, timeout=self.timeout)
        touch(template)
        self.logger.debug(f"已点击 '{description}'.")

    def _take_snapshot(self, reason: str):
        """封装截图操作，保存到报告截图目录，附加到Allure报告，并生成带时间戳和原因的文件名."""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        filename = f"截图_{self.__class__.__name__}_{reason}_{timestamp}.png"
        full_path = ""

        try:
            # 从配置获取报告截图目录
            report_screenshot_dir = self.config.get('screenshot', {}).get('report_dir', 'output/reports/screenshots')
            os.makedirs(report_screenshot_dir, exist_ok=True)
            full_path = os.path.join(report_screenshot_dir, filename)

            # 1. 保存截图 - 使用 filename 参数
            snapshot(filename=full_path)
            self.logger.info(f"已保存报告截图: {full_path} (原因: {reason})")

            # 2. 附加到 Allure 报告
            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    allure.attach(f.read(), name=filename, attachment_type=allure.attachment_type.PNG)
                self.logger.info(f"截图已附加到 Allure 报告: {filename}")
            else:
                self.logger.warning(f"尝试附加截图失败，文件不存在: {full_path}")

        except Exception as snap_err:
            self.logger.error(f"保存或附加报告截图失败: {snap_err}") 