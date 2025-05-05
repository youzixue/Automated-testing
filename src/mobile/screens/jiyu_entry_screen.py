from typing import Dict, Any, TYPE_CHECKING

from src.utils.log.manager import get_logger
from poco.exceptions import PocoNoSuchNodeException, PocoTargetTimeout
from airtest.core.api import stop_app, start_app

# 类型检查时导入 Poco
if TYPE_CHECKING:
    from poco.drivers.android.uiautomation import AndroidUiautomationPoco

class JiyuEntryScreen:
    """封装积余服务 App 的入口导航逻辑，直至进入月卡 WebView.

    主要负责启动 App 并点击"停车支付"按钮。
    """

    def __init__(self, poco: 'AndroidUiautomationPoco', config: Dict[str, Any], timeout: int):
        """初始化积余 App 入口屏幕对象.

        Args:
            poco: Poco 对象实例.
            config: 加载后的项目配置字典.
            timeout: 操作的默认超时时间 (秒).
        """
        self.poco = poco
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.timeout = timeout # 直接使用传入的 timeout
        self.logger.debug(f"JiyuEntryScreen 使用超时值: {self.timeout}")
        
        # 停车支付按钮的文本
        self.parking_payment_text = "停车支付"
        
        # 应用包名
        self.package_name = self.config.get('app', {}).get('jiyu', {}).get('package_name', "com.zsck.yq")
        self.wechat_package_name = self.config.get('app', {}).get('wechat', {}).get('package_name', 'com.tencent.mm')

    def navigate_to_home_screen(self):
        """尝试通过发送系统返回键事件来返回上一级或关闭弹窗，
        作为找不到目标元素时的简单恢复尝试。
        
        Returns:
            bool: 操作是否尝试执行 (不保证效果)。
        """
        self.logger.warning("找不到目标元素，尝试发送系统返回键以恢复...")
        try:
            device = getattr(self.poco, 'device', None)
            if device:
                device.keyevent("BACK")
                self.logger.info("已发送系统返回键事件。")
                return True
            else:
                self.logger.warning("无法获取关联设备对象，无法发送系统返回键。")
                return False
        except Exception as e:
            self.logger.error(f"尝试发送系统返回键时发生错误: {e}", exc_info=True)
            return False

    def navigate_to_monthly_card_webview(self, max_retries=3):
        """执行从 App 启动后到点击"停车支付"进入月卡 WebView 的导航操作.
        
        Args:
            max_retries: 最大重试次数，如果找不到停车支付按钮，尝试返回主页面并重试的次数

        Raises:
            AssertionError: 如果无法找到或点击"停车支付"按钮。
        """
        from airtest.core.api import stop_app, start_app # 确保导入

        # 重置应用状态 - 先停止积余App
        self.logger.info(f"重置应用状态: 停止 {self.package_name}...")
        stop_app(self.package_name)

        # 尝试停止微信进程 
        self.logger.info(f"尝试停止微信进程: {self.wechat_package_name}...")
        try:
            stop_app(self.wechat_package_name)
            self.logger.info(f"已发送停止微信 ({self.wechat_package_name}) 命令。")
        except Exception as e:
            self.logger.warning(f"停止微信进程 {self.wechat_package_name} 时发生错误: {e}")
        
        # 启动积余应用
        self.logger.info(f"启动应用: {self.package_name}...")
        start_app(self.package_name)
        
        self.logger.info(f"开始导航至月卡 WebView 入口，查找并点击 '{self.parking_payment_text}'...")
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # 定位元素
                parking_payment_element = self.poco(text=self.parking_payment_text)

                # 等待元素出现
                self.logger.debug(f"等待 '{self.parking_payment_text}' 元素出现 (超时 {self.timeout}s)... ")
                parking_payment_element.wait_for_appearance(timeout=self.timeout)
                self.logger.debug(f"'{self.parking_payment_text}' 元素已找到.")

                # 点击元素
                parking_payment_element.click()
                self.logger.info(f"已点击 '{self.parking_payment_text}'。")
                # 假设点击后即进入 WebView，后续流程由 MonthlyCardWebViewFlow 处理
                return True

            except (PocoNoSuchNodeException, PocoTargetTimeout) as e:
                retry_count += 1
                if retry_count <= max_retries:
                    self.logger.warning(f"未找到 '{self.parking_payment_text}' 元素 (第 {retry_count} 次尝试)，尝试导航回主页...")
                    self.navigate_to_home_screen()
                    # 等待片刻以便界面刷新
                else:
                    error_msg = f"导航失败：在 {max_retries} 次尝试后仍未能找到或超时等待元素 '{self.parking_payment_text}': {e}"
                    self.logger.error(error_msg)
                    # 截图操作应由调用者（如测试用例或 fixture）在捕获异常后执行，以便附加到报告
                    raise AssertionError(error_msg) from e
            except Exception as e:
                error_msg = f"导航至月卡 WebView 时发生意外错误: {e}"
                self.logger.error(error_msg, exc_info=True)
                raise AssertionError(error_msg) from e 