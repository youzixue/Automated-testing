from __future__ import annotations
from typing import Optional
from src.core.base.driver import BaseDriver
from src.utils.log.manager import get_logger
from src.core.base.errors import ElementNotFoundError, CaptchaError

"""
OMP登录页面对象。

封装OMP系统登录页的元素定位、登录业务流程和验证码处理，支持多环境配置和智能等待。
"""

class OmpLoginPage:
    """OMP登录页面对象，封装登录流程和验证码处理。"""
    # 元素定位符
    USERNAME_INPUT = "input[placeholder='用户名']"
    PASSWORD_INPUT = "input[type='password'][placeholder='密码']"
    CAPTCHA_INPUT = "input[placeholder='验证码']"
    CAPTCHA_IMG = "img[src*='captcha']"
    LOGIN_BUTTON = "button.login-form__btn"
    WELCOME_MESSAGE = ".welcome-message"
    ERROR_MESSAGE = ".el-message--error, .login-error-message"

    def __init__(self, driver: BaseDriver):
        """
        初始化登录页面对象。

        Args:
            driver: 浏览器驱动实例
        """
        self.driver = driver
        self.logger = get_logger(self.__class__.__name__)

    async def is_loaded(self) -> bool:
        """
        判断登录页是否加载完成。

        Returns:
            bool: 是否加载完成

        Raises:
            ElementNotFoundError: 未检测到用户名输入框
        """
        if not await self.driver.has_element(self.USERNAME_INPUT):
            self.logger.warning("页面加载检测失败: 未找到用户名输入框")
            raise ElementNotFoundError("未检测到登录页用户名输入框")
        return True

    async def wait_until_loaded(self, timeout: float = 3) -> OmpLoginPage:
        """
        等待登录页加载完成。

        Args:
            timeout: 超时时间（秒）

        Returns:
            OmpLoginPage: self
        """
        self.logger.info("等待登录页加载...")
        await self.driver.wait_for_element(self.USERNAME_INPUT, timeout=timeout)
        self.logger.info("登录页已加载")
        return self

    async def _fill_credentials(self, username: str, password: str) -> None:
        """
        填充用户名和密码。

        Args:
            username: 用户名
            password: 密码

        Raises:
            ElementNotFoundError: 未找到用户名或密码输入框
        """
        self.logger.info("填充用户名和密码")
        username_el = await self.driver.get_element(self.USERNAME_INPUT)
        if not username_el:
            raise ElementNotFoundError("未找到用户名输入框")
        await username_el.fill(username)
        password_el = await self.driver.get_element(self.PASSWORD_INPUT)
        if not password_el:
            raise ElementNotFoundError("未找到密码输入框")
        await password_el.fill(password)

    async def _handle_captcha(
        self,
        captcha: Optional[str] = None,
        max_retry: int = 7,
        scenario_key: Optional[str] = None
    ) -> str:
        """
        处理验证码输入，支持OCR识别和重试。

        Args:
            captcha: 预设验证码（如有）
            max_retry: 最大重试次数
            scenario_key: 业务场景标识

        Returns:
            str: 最终输入的验证码

        Raises:
            ElementNotFoundError: 未找到验证码图片或输入框
            CaptchaError: 验证码识别失败
        """
        from src.utils.ocr import recognize_captcha
        retry = 0
        last_error = None
        captcha_value = captcha
        while retry < max_retry:
            try:
                if not captcha_value:
                    self.logger.info("等待验证码图片加载并识别...")
                    await self.driver.wait_for_element(self.CAPTCHA_IMG, timeout=5)
                    captcha_img_elem = await self.driver.get_element(self.CAPTCHA_IMG)
                    if not captcha_img_elem:
                        raise ElementNotFoundError("未找到验证码图片")
                    await captcha_img_elem.wait_for_element_state("visible")
                    await captcha_img_elem.evaluate("el => el.complete && el.naturalWidth > 0")
                    img_bytes = await captcha_img_elem.screenshot()
                    captcha_value = recognize_captcha(img_bytes)
                    self.logger.info(f"OCR识别验证码: {captcha_value} (场景: {scenario_key})")
                    if not captcha_value or len(captcha_value) != 4:
                        raise ValueError(f"OCR识别结果异常: {captcha_value}")
                captcha_el = await self.driver.get_element(self.CAPTCHA_INPUT)
                if not captcha_el:
                    raise ElementNotFoundError("未找到验证码输入框")
                await captcha_el.fill(captcha_value)
                self.logger.info("验证码输入完成")
                return captcha_value
            except Exception as e:
                last_error = e
                self.logger.warning(f"验证码识别失败，重试({retry+1}/{max_retry}): {e}")
                retry += 1
                captcha_value = None
        self.logger.error(f"验证码识别失败: {last_error}")
        raise CaptchaError(f"验证码识别失败: {last_error}")

    async def _click_login(self) -> None:
        """
        点击登录按钮。

        Raises:
            ElementNotFoundError: 未找到登录按钮
        """
        login_btn = await self.driver.get_element(self.LOGIN_BUTTON)
        if not login_btn:
            raise ElementNotFoundError("未找到登录按钮")
        await login_btn.click()
        self.logger.info("登录按钮已点击")

    async def login(
        self,
        username: str,
        password: str,
        captcha: Optional[str] = None,
        max_retry: int = 7,
        scenario_key: Optional[str] = None
    ) -> bool:
        """
        执行登录操作，自动处理验证码。

        Args:
            username: 用户名
            password: 密码
            captcha: 预设验证码（如有）
            max_retry: 最大重试次数
            scenario_key: 业务场景标识

        Returns:
            bool: 登录操作是否成功

        Raises:
            ElementNotFoundError: 未找到关键元素
            CaptchaError: 验证码识别失败
        """
        self.logger.info(f"开始登录: 用户名={username}")
        await self.wait_until_loaded()
        await self._fill_credentials(username, password)
        await self._handle_captcha(captcha, max_retry, scenario_key)
        await self._click_login()
        return True

    async def wait_for_login_result(
        self,
        timeout: float = 10,
        expected_url_pattern: str = "/workbench"
    ) -> bool:
        """
        智能判断登录是否成功（基于URL跳转）。
        - 等待URL跳转到包含expected_url_pattern
        - 检查是否有登录错误提示

        Args:
            timeout: 超时时间（秒）
            expected_url_pattern: 登录成功后URL应包含的路径片段

        Returns:
            bool: 是否登录成功
        """
        try:
            # 直接访问Playwright原生page对象
            page = getattr(self.driver, 'page', None)
            if not page:
                self.logger.error("Driver未包含page对象，无法判断URL跳转")
                return False
            await page.wait_for_url(f"**{expected_url_pattern}**", timeout=timeout * 1000)
            self.logger.info(f"检测到URL跳转到包含{expected_url_pattern}，登录成功")
            return True
        except Exception as e:
            self.logger.warning(f"登录后未跳转到预期页面: {e}")
            # 检查登录错误提示
            try:
                if await self.driver.has_element('.login-error', timeout=2):
                    self.logger.info("检测到登录错误提示，登录失败")
                    return False
            except Exception as err:
                self.logger.warning(f"检查登录错误提示异常: {err}")
            return False