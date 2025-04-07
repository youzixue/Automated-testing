"""
OMP系统登录页面对象。

封装OMP系统登录功能，包括验证码处理能力。
"""

import logging
from typing import Optional, Dict
from src.core.base.page import CompositePage
from src.core.base.errors import ElementNotFoundError, CaptchaError, TimeoutError, LoginError, ElementError
from src.web.driver import WebDriver
from src.web.element import WebElement
from src.utils.ocr.captcha import recognize_captcha
from src.utils.config.manager import get_config
import time
from src.web.pages.dashboard_page import DashboardPage



# 更新继承关系
class OmpLoginPage(CompositePage[WebDriver, WebElement]):
    """OMP系统登录页面对象。
    
    为OMP系统定制的登录页面，提供完整的登录流程和验证码处理功能。
    
    Attributes:
        USERNAME_INPUT: 用户名输入框选择器
        PASSWORD_INPUT: 密码输入框选择器
        CAPTCHA_INPUT: 验证码输入框选择器
        CAPTCHA_IMAGE: 验证码图片选择器
        LOGIN_BUTTON: 登录按钮选择器
        ERROR_MESSAGE: 错误消息选择器
    """
    
    def __init__(self, driver: WebDriver, url: Optional[str] = None) -> None:
        """初始化OMP登录页面对象。
        
        Args:
            driver: WebDriver实例
            url: 登录页面URL
        """
        # 直接调用父类 __init__，它会初始化 self.logger
        super().__init__(driver, driver.wait_strategy, url, title="OMP登录") # 假设 title
        self._override_captcha: Optional[str] = None
        
        # 从配置加载选择器
        config = get_config() # config is now a dict
        self.logger.debug(f"配置对象类型: {type(config)}")

        # Access nested dictionary structure
        web_config = config.get("web", {})
        login_config = web_config.get("login", {}) # Get the login section

        self._selectors = login_config.get("selectors", {})
        self.logger.debug(f"加载到的 selectors: {self._selectors}")
        self._timeouts = login_config.get("timeouts", {})
        self._captcha_config = login_config.get("captcha", {})
        urls_config = login_config.get("urls", {})
        self._success_patterns = urls_config.get("success_patterns", [])
        self._max_captcha_attempts = self._captcha_config.get("max_retry", 3) # 获取最大验证码尝试次数

        # Simplified debug log for the relevant config section
        self.logger.debug(f"获取到的 web.login 配置: {login_config}")
    
    @property
    def USERNAME_INPUT(self) -> str:
        return self._selectors.get("username_input")
        
    @property
    def PASSWORD_INPUT(self) -> str:
        return self._selectors.get("password_input")
        
    @property
    def CAPTCHA_INPUT(self) -> str:
        return self._selectors.get("captcha_input")
        
    @property
    def CAPTCHA_IMAGE(self) -> str:
        return self._selectors.get("captcha_image")
        
    @property
    def LOGIN_BUTTON(self) -> str:
        return self._selectors.get("login_button")
        
    @property
    def ERROR_MESSAGE(self) -> str:
        return self._selectors.get("error_message")
    
    def has_captcha_input(self, timeout: float = 1.0) -> bool:
        """检查验证码输入框是否存在且可见。

        Args:
            timeout: 检查的超时时间 (秒)

        Returns:
            True 如果验证码输入框存在且可见，否则 False。
        """
        self.logger.debug("检查验证码输入框是否存在")
        try:
            # 使用 get_element 并检查可见性
            captcha_input = self.get_element(self.CAPTCHA_INPUT)
            return captcha_input.is_visible()
        except (ElementNotFoundError, TimeoutError):
            self.logger.debug("验证码输入框未找到或不可见")
            return False
        except Exception as e:
            self.logger.warning(f"检查验证码输入框时发生意外错误: {e}")
            return False
    
    def is_loaded(self) -> bool:
        """检查页面是否已正确加载，通过验证关键元素存在来确认
        
        Returns:
            bool: 页面加载状态，True表示成功加载，False表示加载失败
        """
        try:
            timeout = self._timeouts.get("page_load", 10)
            self.logger.debug(f"开始检查登录页面加载状态，等待用户名输入框出现 (超时: {timeout}s)")
            
            # 使用 wait_for_element 等待关键元素出现并可见
            self.driver.wait_for_element(self.USERNAME_INPUT, timeout=timeout, state='visible')
            self.logger.debug("用户名输入框已找到且可见")
            
            # 可以选择性地检查更多元素，如果需要更严格的加载判断
            # self.driver.wait_for_element(self.PASSWORD_INPUT, timeout=1, state='visible') # 使用较短超时，因为通常和用户名一起出现
            # self.logger.debug("密码输入框已找到且可见")

            self.logger.info("登录页面已成功加载")
            return True
        except TimeoutError as e:
            self.logger.warning(f"登录页面加载检查失败: 关键元素在规定时间内未出现。{e}")
            return False
        except ElementNotFoundError as e:
             self.logger.error(f"登录页面加载检查失败: 关键元素的选择器无效或未找到。{e}")
             return False
        except Exception as e:
            self.logger.error(f"页面加载检查时发生意外错误: {e}", exc_info=True)
            return False
    
    def get_captcha_image(self) -> bytes:
        """获取验证码图片。
        
        Returns:
            bytes: 验证码图片的字节数据
            
        Raises:
            ElementNotFoundError: 验证码图片元素未找到
            AutomationError: 获取截图失败等其他错误
        """
        try:
            # 等待验证码图片元素可见 - 使用 CompositePage 的 get_element
            element = self.get_element(self.CAPTCHA_IMAGE)
            # element.wait_for_visible() # take_screenshot 通常会等待
            
            # 尝试从src属性中提取验证码值
            src = element.get_attribute("src")
            if src and "text=" in src:
                captcha_text = src.split("text=")[1].split("&")[0]
                if len(captcha_text) == self._captcha_config.get("length", 4): # 简单验证长度
                    self.logger.info(f"从验证码图片URL中提取到验证码: {captcha_text}")
                    self.set_override_captcha(captcha_text)
                else:
                    self.logger.warning(f"从URL提取的验证码 '{captcha_text}' 长度不符，忽略。")
            
            # 获取图片字节数据
            image_bytes = element.take_screenshot()
            if not image_bytes:
                 raise ElementError(f"获取验证码图片 '{self.CAPTCHA_IMAGE}' 的截图失败，返回为空。")
            return image_bytes
            
        except ElementError as e: # Catch specific ElementError first
             self.logger.error(f"获取验证码图片 '{self.CAPTCHA_IMAGE}' 时发生元素错误: {e}", exc_info=True)
             raise
        except Exception as e:
            # Log other potential errors
            self.logger.error(f"获取验证码图片 '{self.CAPTCHA_IMAGE}' 时发生意外错误: {e}", exc_info=True)
            # Wrap in a more general error if needed, or re-raise ElementError if appropriate
            raise ElementError(f"获取验证码图片 '{self.CAPTCHA_IMAGE}' 失败: {e}") from e
    
    def recognize_captcha(self) -> str:
        """识别验证码。
        
        Returns:
            str: 识别出的验证码
            
        Raises:
            CaptchaError: 验证码识别失败
        """
        if self._override_captcha:
            self.logger.info(f"使用覆盖验证码: {self._override_captcha}")
            return self._override_captcha

        try:
            # 获取验证码图片
            image_bytes = self.get_captcha_image()
            
            # 调用OCR识别
            captcha_text = recognize_captcha(image_bytes, **self._captcha_config)
            
            if not captcha_text:
                raise CaptchaError("OCR未能识别验证码")
                
            self.logger.info(f"识别出验证码: {captcha_text}")
            return captcha_text
            
        except (ElementNotFoundError, CaptchaError, ElementError) as e: # Include ElementError
            self.logger.error(f"验证码识别失败: {e}")
            raise
        except Exception as e:
            self.logger.error(f"验证码识别过程中发生意外错误: {e}", exc_info=True)
            raise CaptchaError(f"验证码识别过程中发生意外错误: {e}") from e
    
    def set_override_captcha(self, captcha: str) -> None:
        """设置覆盖验证码，用于跳过验证码识别。
        
        Args:
            captcha: 要使用的验证码
        """
        self.logger.info(f"设置覆盖验证码为: {captcha}")
        self._override_captcha = captcha
    
    def fill_username(self, username: str) -> None:
        """填写用户名。"""
        self.get_element(self.USERNAME_INPUT).fill(username)
        self.logger.info(f"填写用户名: {username}")
    
    def fill_password(self, password: str) -> None:
        """填写密码。"""
        self.get_element(self.PASSWORD_INPUT).fill(password)
        self.logger.info("填写密码")
    
    def fill_captcha(self, captcha: str) -> None:
        """填写验证码。"""
        if self.has_captcha_input():
            self.get_element(self.CAPTCHA_INPUT).fill(captcha)
            self.logger.info(f"填写验证码: {captcha}")
        else:
            self.logger.warning("验证码输入框不存在，跳过填写")
    
    def click_login_button(self) -> None:
        """点击登录按钮。"""
        self.get_element(self.LOGIN_BUTTON).click()
        self.logger.info("点击登录按钮")
    
    def enter_captcha(self, captcha: str) -> None:
        """输入验证码并处理潜在的错误。

        Args:
            captcha: 要输入的验证码

        Raises:
            LoginError: 验证码输入错误或相关错误
        """
        try:
            self.fill_captcha(captcha)
            # 短暂等待，看是否立即出现错误提示 (可选)
            time.sleep(0.2)
            error_msg = self.get_error_message(timeout=0.5)
            if error_msg:
                if "验证码" in error_msg: # 假设错误消息包含关键词
                     self.logger.warning(f"检测到验证码错误提示: {error_msg}")
                     # Don't raise here, let the main login loop handle retries based on login failure
                     # raise LoginError(f"验证码输入错误: {error_msg}")
                # else: # 其他错误暂时不处理，由后续登录点击判断
                #    self.logger.debug(f"检测到非验证码错误: {error_msg}")

        except (ElementNotFoundError, ElementError, TimeoutError) as e:
            self.logger.error(f"输入验证码时发生错误: {e}")
            raise LoginError(f"输入验证码失败: {e}") from e
    
    def refresh_captcha(self) -> str:
        """刷新验证码并重新识别。
        
        Returns:
            str: 新识别出的验证码
            
        Raises:
            ElementNotFoundError: 验证码刷新元素未找到
            CaptchaError: 验证码识别失败
        """
        self.logger.info("刷新验证码")
        try:
            # 点击验证码图片或刷新按钮
            captcha_element = self.get_element(self.CAPTCHA_IMAGE)
            captcha_element.click()
            
            # 等待验证码刷新完成（可能需要短暂等待）
            time.sleep(self._captcha_config.get("refresh_delay", 0.5)) # 使用配置的延迟
            
            # 重新识别
            return self.recognize_captcha()
        except Exception as e:
            self.logger.error(f"刷新验证码失败: {e}", exc_info=True)
            # 包装为 CaptchaError
            raise CaptchaError(f"刷新验证码失败: {e}") from e
    
    def get_error_message(self, timeout: Optional[float] = None) -> Optional[str]:
        """获取登录错误消息。
        
        尝试查找并返回页面上显示的错误消息。
        
        Returns:
            str or None: 错误消息文本，如果未找到则返回None
        """
        self.logger.debug(f"检查登录错误消息 (超时: {timeout or 3.0}s)")
        if not self.ERROR_MESSAGE:
             self.logger.warning("未配置错误消息选择器 (web.login.selectors.error_message)")
             return None
        try:
            # 等待错误消息元素出现
            error_element = self.driver.wait_for_element(
                self.ERROR_MESSAGE,
                timeout=(timeout or self._timeouts.get("error_message", 3.0)),
                state='visible'
            )
            error_message = error_element.get_text_content().strip()
            if error_message:
                self.logger.warning(f"检测到错误消息: {error_message}")
                return error_message
            else:
                 self.logger.debug("错误消息元素可见但无文本内容")
                 return None
        except (ElementNotFoundError, TimeoutError):
            self.logger.debug("未找到或超时未出现错误消息")
            return None
        except Exception as e:
            self.logger.error(f"获取错误消息时发生意外错误: {e}", exc_info=True)
            return None # Treat unexpected errors as no message found
    
    def login_with_captcha(self, username: str, password: str) -> 'DashboardPage':
        """使用验证码进行登录，并处理验证码错误。
        
        包含内部重试逻辑，如果验证码错误，会尝试刷新并重新输入，最多尝试配置的次数。
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            DashboardPage: 登录成功后的仪表盘页面对象
            
        Raises:
            LoginError: 登录失败 (包括所有尝试后验证码仍然错误的情况)
        """
        self.logger.info(f"开始登录 (带验证码)，用户名: {username}")
        
        self.fill_username(username)
        self.fill_password(password)
        
        captcha_attempts = 0
        while captcha_attempts < self._max_captcha_attempts:
            captcha_attempts += 1
            self.logger.info(f"验证码尝试次数: {captcha_attempts}/{self._max_captcha_attempts}")

            # 处理验证码
            if self.has_captcha_input():
                try:
                    captcha = self.recognize_captcha()
                    self.fill_captcha(captcha)
                except CaptchaError as e:
                    self.logger.warning(f"第 {captcha_attempts} 次验证码处理失败: {e}")
                    if captcha_attempts >= self._max_captcha_attempts:
                        self.logger.error("验证码处理达到最大尝试次数，登录失败")
                        raise LoginError(f"验证码处理失败: {e}")
                    # 尝试刷新验证码
                    try:
                        self.logger.info("尝试刷新验证码后重试...")
                        self.refresh_captcha() # refresh_captcha 内部会调用 recognize_captcha
                        continue # 继续下一次循环尝试填写和登录
                    except CaptchaError as refresh_e:
                        self.logger.error(f"刷新验证码也失败了: {refresh_e}")
                        raise LoginError(f"刷新和识别验证码失败: {refresh_e}")
            
            self.click_login_button()
            
            # 验证登录是否成功
            try:
                # 使用更健壮的登录成功检查
                if self._is_login_successful():
                    self.logger.info(f"用户 {username} 在第 {captcha_attempts} 次尝试时登录成功")
                    # 返回新的页面对象
                    dashboard_url = get_config().get("web", {}).get("urls", {}).get("dashboard")
                    return DashboardPage(self.driver, url=dashboard_url)
                else:
                    # 获取错误消息
                    error_msg = self.get_error_message() or "登录失败，原因未知"
                    self.logger.warning(f"第 {captcha_attempts} 次登录尝试失败: {error_msg}")
                    # 如果是验证码错误，继续下一次循环
                    if "验证码" in error_msg:
                        if captcha_attempts >= self._max_captcha_attempts:
                             self.logger.error(f"验证码错误达到最大尝试次数: {error_msg}")
                             raise LoginError(error_msg)
                        else:
                            self.logger.info("检测到验证码错误，将尝试刷新并重试...")
                            # 在下一次循环开始前尝试刷新验证码图片元素本身，增加成功率
                            try:
                                self.refresh_captcha()
                            except CaptchaError as refresh_e:
                                 self.logger.error(f"尝试刷新验证码失败: {refresh_e}")
                                 # 即使刷新失败，也可能只是识别问题，继续循环
                            continue # 继续下一次循环
                    else:
                        # 如果是其他错误 (如用户名/密码错)，直接抛出登录错误，不重试
                        self.logger.error(f"登录失败，非验证码错误: {error_msg}")
                        raise LoginError(error_msg)
            except TimeoutError as e:
                # 登录后页面加载超时
                error_msg = f"登录后等待页面加载超时: {e}"
                self.logger.error(error_msg)
                raise LoginError(error_msg)

        # 如果循环结束仍未成功，说明达到最大尝试次数
        self.logger.error("登录失败：验证码重试次数已用完")
        raise LoginError("登录失败：验证码重试次数已用完")
    
    def _is_login_successful(self) -> bool:
        """检查登录是否成功。
        
        检查URL是否跳转到预期页面，或者是否存在登录错误信息。
        
        Returns:
            True 如果登录成功，否则 False。
        """
        # 1. 检查URL是否包含成功模式
        success = False
        try:
            # 等待导航完成或URL包含成功模式
            self.driver.wait_for_navigation(timeout=self._timeouts.get("login_success", 5))
            current_url = self.driver.get_current_url()
            self.logger.debug(f"登录后当前URL: {current_url}")
            if any(pattern in current_url for pattern in self._success_patterns):
                 self.logger.info("URL 匹配成功模式，判断为登录成功")
                 success = True
            else:
                 self.logger.warning(f"URL {current_url} 未匹配任何成功模式: {self._success_patterns}")
                 # 即使URL不匹配，也可能通过其他方式成功，继续检查错误信息
                 # success = False # 不要在这里直接设为 False

        except TimeoutError:
            self.logger.warning("登录后等待导航超时，可能登录失败或页面加载缓慢")
            # 超时也可能表示成功，需要进一步检查错误信息
            # success = False # 不要在这里直接设为 False
        
        # 2. 检查是否有错误消息出现
        if not success:
            # 只有在URL检查未确认成功时，才检查错误消息
            error_message = self.get_error_message() # 使用较短超时检查错误
            if error_message:
                self.logger.warning(f"检测到错误消息，判断为登录失败: {error_message}")
                return False # 明确失败
            else:
                # 没有错误消息，URL也不匹配，但也没有超时，这可能是慢速加载的成功？
                # 或者成功了但URL模式不匹配？
                # 增加仪表盘页面加载检查作为最终确认
                try:
                    dashboard_url = get_config().get("web", {}).get("urls", {}).get("dashboard")
                    dashboard = DashboardPage(self.driver, url=dashboard_url)
                    if dashboard.is_loaded(): # 检查Dashboard是否加载成功
                         self.logger.info("Dashboard页面已加载，判断为登录成功")
                         return True
                    else:
                         self.logger.warning("Dashboard页面未加载，判断为登录失败")
                         return False
                except Exception as e:
                     self.logger.warning(f"检查Dashboard页面时出错: {e}")
                     return False # 无法确认，判断为失败
        else:
            # URL 匹配成功模式，直接返回 True
            return True

    def login(self, username: str, password: str) -> 'DashboardPage':
        """执行标准登录流程。
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            DashboardPage: 登录成功后的仪表盘页面对象
            
        Raises:
            LoginError: 登录失败
        """
        if self._captcha_config.get("enabled", False):
            self.logger.info("启用验证码登录流程")
            return self.login_with_captcha(username, password)
        else:
            self.logger.info("执行无验证码登录流程")
            self.fill_username(username)
            self.fill_password(password)
            self.click_login_button()
            
            # 验证登录是否成功
            try:
                if self._is_login_successful():
                    self.logger.info(f"用户 {username} 登录成功 (无验证码)")
                    dashboard_url = get_config().get("web", {}).get("urls", {}).get("dashboard")
                    return DashboardPage(self.driver, url=dashboard_url)
                else:
                    error_msg = self.get_error_message() or "登录失败，原因未知"
                    self.logger.error(f"用户 {username} 登录失败 (无验证码): {error_msg}")
                    raise LoginError(error_msg)
            except TimeoutError as e:
                error_msg = f"登录后等待页面加载超时: {e}"
                self.logger.error(error_msg)
                raise LoginError(error_msg)

    # 实现 wait_until_loaded
    def wait_until_loaded(self, timeout: Optional[float] = None) -> 'OmpLoginPage':
        """等待登录页面加载完成。

        Args:
            timeout: 超时时间(秒)，None表示使用默认超时时间

        Returns:
            当前页面对象(用于链式调用)

        Raises:
            TimeoutError: 在指定时间内页面未加载完成
        """
        self.logger.info(f"等待OMP登录页面加载... (超时: {timeout or self.wait.timeout} 秒)")
        try:
            self.wait.wait_until(self.is_loaded, timeout=timeout, message="等待OMP登录页面加载超时")
            self.logger.info("OMP登录页面加载完成")
            return self
        except TimeoutError as e:
            self.logger.error(f"OMP登录页面加载失败: {e}")
            raise 