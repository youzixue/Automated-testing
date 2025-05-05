import pytest
import allure

# 导入 Fixtures (直接使用 fixture 名称作为参数即可，pytest 会自动注入)
# from tests.mobile.conftest import mobile_device_poco_session, jiyu_entry_screen, monthly_card_webview_flow_mobile
# from tests.conftest import config # 全局 config

# 导入需要实例化的对象类型用于类型提示 (可选，但推荐)
from src.mobile.screens.jiyu_entry_screen import JiyuEntryScreen
from src.common.components.monthly_card_flow import MonthlyCardWebViewFlow, SUBMIT_PAY_IMAGE
from typing import Dict, Any, Tuple, Optional

# 导入断言工具
from src.utils.waits import wait_for_activity
from src.utils.log.manager import get_logger # 使用统一 logger
from airtest.core.api import wait, touch, device as current_device, snapshot # 导入 airtest 函数和 Device
from airtest.core.device import Device # 导入 Device 类型

logger = get_logger(__name__)

@pytest.mark.mobile # 标记为 mobile 测试
@allure.feature("积余服务App") # Allure 功能分类
@allure.story("月卡续费") # Allure 用户故事
class TestJiyuMonthlyCard:

    @allure.title("积余App月卡续费支付流程")
    @allure.description("测试通过积余App入口，完成月卡续费直至拉起支付页面的流程")
    def test_jiyu_renewal_payment_flow(self, config: Dict[str, Any],
                                       mobile_device_poco_session: Tuple[Optional[Device], Optional[Any], int],
                                       jiyu_entry_screen: Optional[JiyuEntryScreen],
                                       monthly_card_webview_flow: Optional[MonthlyCardWebViewFlow]):
        """测试积余服务 App 月卡续费支付流程.

        Args:
            config: 全局配置字典 (来自 fixture).
            mobile_device_poco_session: 提供 device, poco, timeout (来自 fixture).
            jiyu_entry_screen: 积余 App 入口屏幕对象 (来自 fixture).
            monthly_card_webview_flow: 共享月卡流程组件 (来自 fixture).
        """
        # 增加检查，如果 fixture 返回 None 则跳过测试
        if jiyu_entry_screen is None or monthly_card_webview_flow is None:
            pytest.skip("依赖的屏幕对象或流程组件未能初始化 (可能 Poco 不可用)，跳过测试")
            
        device, _, timeout = mobile_device_poco_session # 解包获取转换好的 timeout
        logger.info(f"开始测试积余 App 月卡续费流程 (使用超时: {timeout}s)...")

        try:
            # 1. 入口导航
            with allure.step("导航至月卡WebView入口"):
                # jiyu_entry_screen 在 fixture 级别已处理 None 情况
                jiyu_entry_screen.navigate_to_monthly_card_webview()
                logger.info("成功导航至月卡 WebView 入口。")

            # 2. 执行共享 WebView 流程 (至确认支付)
            with allure.step("执行共享月卡续费流程（至确认支付）"):
                monthly_card_webview_flow.execute_renewal_up_to_confirm_pay()
                logger.info("共享月卡续费流程（至确认支付）执行完毕。")

            # 3. 点击提交支付 (积余 App 特定步骤)
            with allure.step("点击提交支付按钮"):
                 logger.debug(f"等待并点击提交支付图标 (超时: {timeout}s)...")
                 wait(SUBMIT_PAY_IMAGE, timeout=timeout) 
                 touch(SUBMIT_PAY_IMAGE)
                 logger.info("已点击提交支付按钮。")

            # 4. 断言支付 Activity 是否拉起
            with allure.step("断言支付Activity是否拉起"):
                expected_activity_suffix = config.get('app', {}).get('payment', {}).get('activity_suffix', '.framework.app.UIPageFragmentActivity')
                logger.info(f"开始检查支付 Activity (应包含: '{expected_activity_suffix}', 超时: {timeout}s)...")
                activity_found = wait_for_activity(device, expected_activity_suffix, timeout)
                if not activity_found:
                    # 如果断言失败，尝试截图
                    try:
                        snapshot(msg=f"支付Activity_{expected_activity_suffix}_未出现截图")
                    except Exception as snap_err:
                        logger.warning(f"断言失败后尝试截图也失败: {snap_err}")
                assert activity_found, \
                       f"支付 Activity (含 {expected_activity_suffix}) 未在 {timeout} 秒内出现"
                logger.info("测试通过: 积余 App 月卡续费成功拉起支付页面。")

        except AssertionError as ae:
            logger.error(f"积余 App 月卡续费流程测试失败: {ae}", exc_info=True)
            # 截图和附加报告由全局 hook 处理
            pytest.fail(f"测试断言失败: {ae}") # 保持 pytest 失败状态
        except Exception as e:
            logger.error(f"积余 App 月卡续费流程测试中发生意外错误: {e}", exc_info=True)
            # 截图和附加报告由全局 hook 处理
            pytest.fail(f"测试执行时发生意外错误: {e}") # 保持 pytest 失败状态 