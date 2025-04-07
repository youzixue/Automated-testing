"""
OMP系统登录测试。

测试OMP系统的登录功能，包括成功和失败场景，使用页面对象模式实现。
"""

import pytest
import allure
import random
import string
import logging
from typing import Dict, Any

from src.web.driver import WebDriver
from src.web.pages import OmpLoginPage, DashboardPage
from src.core.base.errors import LoginError, CaptchaError, ElementNotFoundError, TimeoutError
from src.utils.allure_helpers import attach_screenshot
from src.utils.log.manager import get_logger


@allure.epic("Web自动化测试")
@allure.feature("OMP系统")
@allure.story("用户登录")
class TestOmpLogin:
    """OMP系统登录测试类。
    
    测试OMP系统的登录功能，包括:
    1. 成功登录
    2. 用户名错误
    3. 密码错误
    4. 验证码错误
    """
    
    # Use framework logger
    logger = get_logger(__name__)
    
    @allure.title("使用有效凭据登录成功")
    @allure.severity(allure.severity_level.CRITICAL)
    @pytest.mark.smoke
    @pytest.mark.omp
    @pytest.mark.login
    def test_login_success(self, web_driver: WebDriver, login_data: Dict[str, Any]) -> None:
        """测试成功登录场景。
        
        使用有效的用户名、密码和验证码登录，验证能够登录成功并跳转到仪表盘页面。
        
        Args:
            web_driver: WebDriver实例
            login_data: 登录测试数据
        """
        # 准备测试数据
        url = login_data["url"]
        user = login_data["users"]["valid"]
        
        with allure.step("打开OMP登录页面"):
            login_page = OmpLoginPage(web_driver, url)
            login_page.navigate()
            assert login_page.is_loaded(), "登录页面未正确加载"
            attach_screenshot(web_driver, "登录页面截图")
        
        with allure.step(f"使用用户名 {user['username']} 登录"):
            try:
                dashboard_page = login_page.login(user["username"], user["password"])
                
                # 验证登录成功
                assert dashboard_page.is_loaded(), "登录后未正确加载仪表盘页面"
                
                with allure.step("验证登录成功"):
                    # 添加仪表盘截图
                    attach_screenshot(web_driver, "仪表盘页面截图")
                
                with allure.step("执行登出操作"):
                    # 执行登出操作，清理测试环境
                    dashboard_page.logout()
            except Exception as e:
                attach_screenshot(web_driver, "登录失败截图")
                raise
    
    @allure.title("使用错误用户名无法登录")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.omp
    @pytest.mark.login
    def test_login_invalid_username(self, web_driver: WebDriver, login_data: Dict[str, Any]) -> None:
        """测试用户名错误场景。
        
        使用随机错误的用户名尝试登录，验证登录失败并显示正确的错误信息。
        使用随机用户名避免多次使用同一错误用户名导致账号被锁定。
        
        Args:
            web_driver: WebDriver实例
            login_data: 登录测试数据
        """
        # 准备测试数据
        url = login_data["url"]
        user = login_data["users"]["invalid_username"]
        
        # 生成随机用户名，避免账号锁定问题
        if user.get("use_random", False):
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            user["username"] = f"invalid_{random_suffix}"
        
        with allure.step("打开OMP登录页面"):
            login_page = OmpLoginPage(web_driver, url)
            login_page.navigate()
            assert login_page.is_loaded(), "登录页面未正确加载"
            attach_screenshot(web_driver, "登录页面截图")
        
        with allure.step(f"使用无效用户名 {user['username']} 尝试登录"):
            with pytest.raises(LoginError) as excinfo:
                login_page.login(user["username"], user["password"])
            
            # 验证错误信息
            error_message = str(excinfo.value)
            assert user["expected_error"] in error_message, f"错误信息不匹配: {error_message}"
            
            with allure.step("验证仍在登录页面"):
                # 确认仍在登录页面
                assert login_page.is_loaded(), "登录失败后应该停留在登录页面"
                attach_screenshot(web_driver, "错误提示截图")
    
    @allure.title("使用错误密码无法登录")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.omp
    @pytest.mark.login
    def test_login_invalid_password(self, web_driver: WebDriver, login_data: Dict[str, Any]) -> None:
        """测试密码错误场景。
        
        使用错误的密码尝试登录，验证登录失败并显示正确的错误信息。
        
        Args:
            web_driver: WebDriver实例
            login_data: 登录测试数据
        """
        # 准备测试数据
        url = login_data["url"]
        user = login_data["users"]["invalid_password"]
        
        with allure.step("打开OMP登录页面"):
            login_page = OmpLoginPage(web_driver, url)
            login_page.navigate()
            assert login_page.is_loaded(), "登录页面未正确加载"
            attach_screenshot(web_driver, "登录页面截图")
        
        with allure.step(f"使用正确用户名 {user['username']} 和错误密码尝试登录"):
            with pytest.raises(LoginError) as excinfo:
                login_page.login(user["username"], user["password"])
            
            # 验证错误信息
            error_message = str(excinfo.value)
            assert user["expected_error"] in error_message, f"错误信息不匹配: {error_message}"
            
            with allure.step("验证仍在登录页面"):
                # 确认仍在登录页面
                assert login_page.is_loaded(), "登录失败后应该停留在登录页面"
                attach_screenshot(web_driver, "错误提示截图")
    
    @allure.title("使用错误验证码无法登录")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.omp
    @pytest.mark.login
    def test_login_invalid_captcha(self, web_driver: WebDriver, login_data: Dict[str, Any]) -> None:
        """测试验证码错误场景。

        使用可能触发验证码错误的凭证尝试登录，验证登录失败并抛出LoginError。
        依赖 OmpLoginPage.login 方法内部的验证码处理和重试逻辑。

        Args:
            web_driver: WebDriver实例
            login_data: 登录测试数据
        """
        # 准备测试数据 - 假设 invalid_captcha 用户配置了正确的账号密码，
        # 但服务器端会对特定操作或频繁尝试后要求验证码，并可能因验证码错误而失败
        url = login_data["url"]
        user = login_data["users"]["invalid_captcha"]

        with allure.step("打开OMP登录页面"):
            login_page = OmpLoginPage(web_driver, url)
            login_page.navigate()
            assert login_page.is_loaded(), "登录页面未正确加载"
            attach_screenshot(web_driver, "登录页面截图")

        with allure.step("检查是否需要验证码"):
            if not login_page.has_captcha_input(timeout=2):
                pytest.skip("页面没有验证码输入框，无法测试验证码错误场景")

        with allure.step(f"使用用户 {user['username']} 尝试登录（预期验证码失败）"):
            # 调用 login 方法，期望它在内部处理验证码并最终因错误而失败
            with pytest.raises(LoginError) as excinfo:
                # OmpLoginPage.login 应该处理验证码识别、输入和潜在的重试
                # 如果验证码始终错误或识别失败达到最大次数，应抛出 LoginError
                login_page.login(user["username"], user["password"])

            # 验证捕获到的 LoginError 包含预期的错误信息
            error_message = str(excinfo.value)
            expected_substring = user.get("expected_error", "验证码错误") # 从数据文件获取预期错误信息
            assert expected_substring in error_message, \
                f"预期的错误信息 '{expected_substring}' 未在异常中找到: {error_message}"

            with allure.step("验证仍在登录页面"):
                # 确认仍在登录页面
                assert login_page.is_loaded(), "登录失败后应该停留在登录页面"
                attach_screenshot(web_driver, "验证码错误提示截图")
    
    @allure.title("空字段验证")
    @allure.severity(allure.severity_level.MINOR)
    @pytest.mark.omp
    @pytest.mark.login
    def test_login_empty_fields(self, web_driver: WebDriver, login_data: Dict[str, Any]) -> None:
        """测试空用户名或密码登录场景。"""
        # TODO: 实现空字段测试逻辑
        # 1. 打开登录页面
        # 2. 尝试空用户名/密码登录
        # 3. 断言出现预期的错误提示（可能需要 FormValidator 或特定错误元素）
        pass
    
    @allure.title("特殊字符用户名/密码登录")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.omp
    @pytest.mark.login
    def test_login_special_characters(self, web_driver: WebDriver, login_data: Dict[str, Any]) -> None:
        """测试包含特殊字符的用户名或密码登录场景。"""
        # TODO: 实现特殊字符测试逻辑
        # 1. 从 login_data 获取包含特殊字符的用户数据
        # 2. 打开登录页面
        # 3. 尝试登录
        # 4. 断言登录结果（成功或失败，根据预期）
        pass