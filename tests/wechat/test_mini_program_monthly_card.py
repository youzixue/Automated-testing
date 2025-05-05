import pytest
import allure
from typing import Dict, Any, Callable, Tuple

# 导入 Fixtures
# from tests.wechat.conftest import wechat_navigator, monthly_card_webview_flow_wechat
# from tests.conftest import config

# 导入类型提示
from src.common.components.monthly_card_flow import MonthlyCardWebViewFlow

# 导入断言工具
from src.utils.waits import wait_for_activity
from src.utils.log.manager import get_logger

logger = get_logger(__name__)

@pytest.mark.wechat
@allure.feature("微信小程序")
@allure.story("月卡续费")
class TestWechatMiniProgramMonthlyCard:

    @allure.title("微信小程序月卡续费支付流程")
    @allure.description("测试通过微信小程序入口，完成月卡续费直至拉起支付页面的流程")
    def test_mini_program_renewal_payment_flow(self, config: Dict[str, Any],
                                               wechat_navigator: Callable[[str, str], None],
                                               monthly_card_webview_flow_wechat: MonthlyCardWebViewFlow,
                                               wechat_device_poco_session: Tuple[Any, Any, int]): # 修改签名接收 timeout
        """测试微信小程序月卡续费支付流程.

        Args:
            config: 全局配置字典.
            wechat_navigator: 预配置的微信导航函数.
            monthly_card_webview_flow_wechat: 共享月卡流程组件.
            wechat_device_poco_session: 提供 device, poco, timeout.
        """
        device, _, timeout = wechat_device_poco_session # 解包获取 timeout
        target_name = config.get('app', {}).get('wechat', {}).get('targets', {}).get('mini_program')
        if not target_name:
            pytest.fail("未在配置中找到 'app.wechat.targets.mini_program'！")

        logger.info(f"开始测试微信小程序 '{target_name}' 月卡续费流程...")

        try:
            # 1. 入口导航 (启动小程序)
            with allure.step(f"启动并导航至小程序 '{target_name}'"):
                wechat_navigator(target_name, "小程序")
                logger.info(f"已导航至小程序 '{target_name}'")
                # 小程序启动后直接可见月卡图标，无需额外导航步骤

            # 2. 执行共享 WebView 流程 (至确认支付)
            with allure.step("执行共享月卡续费流程（至确认支付）"):
                monthly_card_webview_flow_wechat.execute_renewal_up_to_confirm_pay()
                logger.info("共享月卡续费流程（至确认支付）执行完毕。")

            # 3. 断言支付 Activity (小程序在确认支付后直接拉起)
            with allure.step("断言支付Activity是否拉起"):
                expected_activity_suffix = config.get('app', {}).get('payment', {}).get('activity_suffix', '.framework.app.UIPageFragmentActivity')
                # --- 移除 timeout 获取和转换逻辑 --- 
                # timeout_from_config = config.get('airtest', {}).get('timeouts', {}).get('default', 20)
                # try:
                #     # ... (转换代码) ...
                # except (ValueError, TypeError):
                #     # ... (警告和默认值) ...
                #     timeout_assert = 20
                # --- timeout 处理结束 ---
                
                logger.info(f"开始检查支付 Activity (应包含: '{expected_activity_suffix}', 超时: {timeout}s)...")
                assert wait_for_activity(device, expected_activity_suffix, timeout), (
                       f"支付 Activity (含 {expected_activity_suffix}) 未在 {timeout} 秒内出现"
                )
                logger.info("测试通过: 小程序月卡续费成功拉起支付页面")

        except AssertionError as ae:
            logger.error(f"微信小程序 '{target_name}' 月卡续费流程测试失败: {ae}", exc_info=True)
            pytest.fail(f"测试断言失败: {ae}")
        except Exception as e:
            logger.error(f"微信小程序 '{target_name}' 月卡续费流程测试中发生意外错误: {e}", exc_info=True)
            pytest.fail(f"测试执行时发生意外错误: {e}") 