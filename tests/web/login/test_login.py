import os
import asyncio
import random
import string
from typing import Any, Dict
import pytest
import allure

from src.core.base.errors import LoginError, CaptchaError
from src.web.pages.login_page import OmpLoginPage
from src.web.driver_playwright_adapter import PlaywrightDriverAdapter
from src.utils.log.manager import get_logger

logger = get_logger(__name__)

def random_username(length: int = 8) -> str:
    """生成随机无效用户名，避免账号锁定。

    Args:
        length (int): 随机部分长度
    Returns:
        str: 随机用户名
    """
    return "invalid_" + ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

async def wait_and_get_popup_message(
    page: Any, timeout: int = 2000, retry_delay: float = 0.2, retry_timeout: int = 1000
) -> str:
    """等待弹窗出现并获取内容，若第一次未捕捉到则兜底重试一次。

    Args:
        page (Any): Playwright页面对象
        timeout (int): 首次等待超时时间(ms)
        retry_delay (float): 兜底重试前等待时间(s)
        retry_timeout (int): 兜底重试超时时间(ms)
    Returns:
        str: 弹窗内容文本，若未捕捉到则返回空字符串
    Raises:
        Exception: 若等待过程中发生异常
    """
    error_text = ""
    try:
        await page.wait_for_selector('.el-message__content', state='visible', timeout=timeout)
        error_text = await page.inner_text('.el-message__content')
    except Exception as e:
        logger.debug(f"首次未检测到弹窗内容: {e}")
        await asyncio.sleep(retry_delay)
        try:
            await page.wait_for_selector('.el-message__content', state='visible', timeout=retry_timeout)
            error_text = await page.inner_text('.el-message__content')
        except Exception as e2:
            error_text = ""
            logger.debug(f"仍未检测到弹窗内容: {e2}")
    logger.debug(f"弹窗内容: {error_text}")
    return error_text

@pytest.mark.web
@pytest.mark.asyncio
@allure.epic("WEB")
@allure.feature("OMP系统登录验证")
@pytest.mark.parametrize("scenario_key", [
    "valid",
    "invalid_username",
    "invalid_password",
    "invalid_captcha",
    "empty_username",
    "empty_password"
])
async def test_login_scenarios(
    page: Any,
    test_users: Dict[str, Dict[str, Any]],
    login_url: str,
    scenario_key: str,
    captcha_config: Dict[str, Any]
) -> None:
    """
    OMP系统登录场景测试，支持多浏览器和Allure报告。

    Args:
        page (Any): Playwright页面对象
        test_users (Dict[str, Dict[str, Any]]): 测试用户数据字典
        login_url (str): 登录页URL
        scenario_key (str): 当前测试场景key
        captcha_config (Dict[str, Any]): 验证码相关配置
    Raises:
        AssertionError: 用于断言各类登录场景的预期结果
        LoginError: 登录业务异常
        CaptchaError: 验证码识别异常
    """
    # 设置测试场景动态标题
    scenario_titles = {
        "valid": "有效账号登录成功验证",
        "invalid_username": "无效用户名登录失败验证",
        "invalid_password": "错误密码登录失败验证",
        "invalid_captcha": "错误验证码登录失败验证",
        "empty_username": "空用户名表单验证",
        "empty_password": "空密码表单验证"
    }
    allure.dynamic.title(scenario_titles.get(scenario_key, f"登录场景: {scenario_key}"))
    
    # 添加测试描述和重要性级别
    scenario_descriptions = {
        "valid": "验证使用正确的用户名和密码能够成功登录系统",
        "invalid_username": "验证使用不存在的用户名登录时系统给出正确提示",
        "invalid_password": "验证使用正确用户名但错误密码登录时系统给出正确提示",
        "invalid_captcha": "验证输入错误验证码时系统给出正确提示",
        "empty_username": "验证用户名为空时表单验证阻止提交",
        "empty_password": "验证密码为空时表单验证阻止提交"
    }
    allure.dynamic.description(scenario_descriptions.get(scenario_key, ""))
    
    # 根据场景设置不同优先级
    if scenario_key == "valid":
        allure.severity(allure.severity_level.CRITICAL)
    elif scenario_key in ["invalid_username", "invalid_password"]:
        allure.severity(allure.severity_level.NORMAL)
    else:
        allure.severity(allure.severity_level.MINOR)
        
    logger.info(f"HEADLESS: {os.environ.get('HEADLESS')}")
    logger.debug(f"page fixture type: {type(page)}")
    logger.debug(f"login_url: {login_url}")

    user_data = test_users[scenario_key].copy()
    if user_data.get("use_random"):
        user_data["username"] = random_username()

    with allure.step(f"跳转到登录页: {login_url}"):
        logger.info(f"[LOGIN] 跳转到登录页: {login_url}")
        await page.goto(login_url)

    driver = PlaywrightDriverAdapter(page)
    login_page = OmpLoginPage(driver)
    await login_page.wait_until_loaded()

    expected_result = user_data.get("expected_result")
    expected_error = user_data.get("expected_error")

    max_retry = captcha_config.get("max_retry", 3)

    try:
        with allure.step(f"登录场景: {scenario_key}"):
            if scenario_key in ["invalid_username", "invalid_password"]:
                retry = 0
                last_img_src = None
                while retry < max_retry:
                    await login_page.login(
                        username=user_data["username"],
                        password=user_data["password"],
                        scenario_key=scenario_key
                    )
                    error_text = await wait_and_get_popup_message(page)
                    if "验证码错误" in error_text:
                        try:
                            await page.wait_for_selector('.el-message__content', state='hidden', timeout=2000)
                        except Exception as e:
                            logger.debug(f"等待弹窗消失异常: {e}")
                        try:
                            captcha_img = await page.query_selector('img[src*=\"captcha\"]')
                            if captcha_img:
                                new_src = await captcha_img.get_attribute('src')
                                if last_img_src and new_src == last_img_src:
                                    await asyncio.sleep(0.8)
                                    new_src = await captcha_img.get_attribute('src')
                                last_img_src = new_src
                        except Exception as e:
                            logger.debug(f"等待验证码图片刷新异常: {e}")
                            await asyncio.sleep(0.8)
                        retry += 1
                        continue
                    break
                else:
                    assert False, "多次尝试后验证码始终未识别正确，无法验证账号密码逻辑"
                assert ("账户或密码错误" in error_text or "用户名或密码错误" in error_text), \
                    f"期望账号或密码错误，实际弹窗内容: {error_text}"
                return
            elif scenario_key == "invalid_captcha":
                await login_page.login(
                    username=user_data["username"],
                    password=user_data["password"],
                    captcha="wrong_captcha",
                    scenario_key=scenario_key
                )
                error_text = await wait_and_get_popup_message(page)
                assert "验证码错误" in error_text, f"期望验证码错误，实际弹窗内容: {error_text}"
                return
            elif scenario_key in ["empty_username", "empty_password"]:
                await page.goto(login_url)
                driver = PlaywrightDriverAdapter(page)
                login_page = OmpLoginPage(driver)
                await login_page.wait_until_loaded()
                if scenario_key == "empty_username":
                    await page.fill('input[placeholder=\"用户名\"]', "")
                    await page.fill('input[type=\"password\"][placeholder=\"密码\"]', user_data["password"])
                else:
                    await page.fill('input[placeholder=\"用户名\"]', user_data["username"])
                    await page.fill('input[type=\"password\"][placeholder=\"密码\"]', "")
                await page.click('button.login-form__btn')
                await page.wait_for_selector('.el-form-item__error', state='visible', timeout=1000)
                error_text = await page.inner_text('.el-form-item__error')
                logger.debug(f"表单错误提示: {error_text}")
                assert ("账号不能为空" in error_text or "密码不能为空" in error_text), \
                    f"期望提示'账号或密码不能为空'，实际: {error_text}"
                return
            else:
                await login_page.login(
                    username=user_data["username"],
                    password=user_data["password"],
                    captcha="wrong_captcha" if scenario_key == "invalid_captcha" else None,
                    scenario_key=scenario_key
                )
                error_text = await wait_and_get_popup_message(page)
                if scenario_key == "invalid_captcha":
                    assert "验证码错误" in error_text, f"期望验证码错误，实际弹窗内容: {error_text}"
                    return
                elif scenario_key in ["invalid_username", "invalid_password"]:
                    if "验证码错误" in error_text:
                        assert False, f"验证码识别失败，实际弹窗内容: {error_text}"
                    assert ("账户或密码错误" in error_text or "用户名或密码错误" in error_text), \
                        f"期望账号或密码错误，实际弹窗内容: {error_text}"
                    return
                if expected_result == "success":
                    # 支持后续参数化expected_url_pattern，默认/workbench
                    expected_url_pattern = user_data.get("expected_url_pattern", "/workbench")
                    login_success = await login_page.wait_for_login_result(expected_url_pattern=expected_url_pattern)
                    assert login_success, f"有效账号登录应成功，实际: {login_success}"
                else:
                    assert not login_success, f"无效账号({scenario_key})登录应失败，实际: {login_success}"
    except LoginError as e:
        allure.attach(str(e), name="登录错误", attachment_type=allure.attachment_type.TEXT)
        logger.warning(f"[LOGIN] 捕获到登录错误: {e}")
        assert expected_error is not None, f"未预期的登录错误: {e}"
        assert expected_error in str(e), f"错误信息不符: 期望'{expected_error}', 实际'{e}'"
    except CaptchaError as e:
        allure.attach(str(e), name="验证码错误", attachment_type=allure.attachment_type.TEXT)
        logger.warning(f"[LOGIN] 捕获到验证码错误: {e}")
        assert scenario_key == "invalid_captcha", f"仅invalid_captcha场景应抛出验证码错误，当前场景: {scenario_key}，错误: {e}"