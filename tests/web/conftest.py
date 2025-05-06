"""
Web测试专用的pytest固件配置。
提供Web UI测试所需的浏览器、页面对象、数据和截图功能。
"""

import os
import asyncio
from pathlib import Path
import pytest
import pytest_asyncio
import yaml
import allure
from playwright.async_api import async_playwright, Page, Browser
from typing import Dict, Any

from src.utils.screenshot import save_screenshot, gen_screenshot_filename
from src.utils.config.manager import get_config
from src.utils.log.manager import get_logger

logger = get_logger(__name__)

# --- .env loading logic removed as it is handled globally in tests/conftest.py --- 


@pytest_asyncio.fixture(scope="function")
async def browser() -> Browser:
    """浏览器实例 (Function Scope)，根据配置启动浏览器。"""
    # 直接从环境变量获取 headless 和 browser type
    headless_env = os.environ.get("HEADLESS", "true").lower()
    headless = headless_env in ("1", "true", "yes")
    browser_type = os.environ.get("BROWSER", "chromium").lower()
    
    logger.info(f"[Web Conftest] Launching browser (Function Scope): Type={browser_type}, headless={headless} (from env)")
    
    # 在 fixture 内部创建 playwright 上下文
    async with async_playwright() as p:
        # 根据 browser_type 启动对应的浏览器
        if browser_type == "firefox":
            browser_instance = await p.firefox.launch(headless=headless)
        elif browser_type == "webkit":
            browser_instance = await p.webkit.launch(headless=headless)
        else: # 默认或无效时回退到 chromium
            if browser_type != "chromium":
                 logger.warning(f"Unsupported browser type '{browser_type}' specified in env, defaulting to chromium.")
            browser_instance = await p.chromium.launch(headless=headless)
            
        yield browser_instance
        logger.info(f"[Web Conftest] Closing browser (Function Scope, Type={browser_type}).")
        await browser_instance.close()


@pytest_asyncio.fixture(scope="function")
async def page(browser: Browser) -> Page:
    """每个测试函数获取新的浏览器页面 (Function Scope)"""
    logger.debug("[Web Conftest] Creating new page.")
    new_page = await browser.new_page()
    yield new_page
    logger.debug("[Web Conftest] Closing page.")
    await new_page.close()


@pytest.fixture(scope="function")
def test_users(config: Dict[str, Any]) -> Dict[str, Any]:
    """加载并合成 Web 登录测试用户数据（接近旧版），修正数据文件路径，使用注入的配置。"""
    # 修正路径：使用 parents[2] 回退到项目根目录
    data_file = Path(__file__).parents[2] / "data" / "web" / "login" / "login_data.yaml"
    logger.debug(f"[Web Conftest] Loading user data from: {data_file}")
    if not data_file.is_file():
        logger.error(f"User data file not found: {data_file}")
        return {}
    try:
        with open(data_file, encoding="utf-8") as f:
            login_data = yaml.safe_load(f)
        users = login_data.get("users", {}).copy()
        
        # 使用传入的 config
        default_creds = config.get('credentials', {}).get('default', {})
        if 'valid' in users and default_creds.get('username') and default_creds.get('password'):
            users['valid']['username'] = default_creds['username']
            users['valid']['password'] = default_creds['password']
            logger.debug("[Web Conftest] Updated 'valid' user credentials from config.")
        return users
    except Exception as e:
        logger.error(f"Error loading/processing user data: {e}", exc_info=True)
        return {}


@pytest.fixture(scope="function")
def login_url(config: Dict[str, Any]) -> str:
    """获取 OMP 登录 URL，优先使用 omp_login_url，若未配置则回退到 base_url。"""
    # 使用传入的 config
    web_config = config.get('web', {})
    
    # 1. 优先尝试获取 omp_login_url
    url = web_config.get('omp_login_url', "")
    
    if url:
        logger.debug(f"[Web Conftest] Using specific OMP Login URL: {url}")
    else:
        # 2. omp_login_url 未配置或为空，则回退到 base_url
        url = web_config.get('base_url', "")
        if url:
            logger.debug(f"[Web Conftest] omp_login_url not configured, falling back to base_url: {url}")
        else:
            # 3. 两者都未配置
            logger.warning("Neither web.omp_login_url nor web.base_url are configured!")
            
    return url


@pytest_asyncio.fixture(scope="session")
async def captcha_config() -> Dict[str, Any]:
    """加载验证码相关配置。使用session作用域的异步fixture，修正数据文件路径。"""
    # 修正路径：使用 parents[2] 回退到项目根目录
    login_data_path = Path(__file__).parents[2] / "data" / "web" / "login" / "login_data.yaml"
    logger.debug(f"[Web Conftest] Loading captcha config from: {login_data_path}")
    if not login_data_path.is_file():
        logger.warning(f"Captcha config file not found at {login_data_path}")
        return {}
    try:
        with open(login_data_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("captcha", {})
    except Exception as e:
        logger.error(f"Error loading captcha config from {login_data_path}: {e}")
        return {}


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """用例失败自动截图并集成Allure报告（同步hookwrapper，兼容pytest机制） - 简化事件循环处理"""
    outcome = yield
    rep = outcome.get_result()

    # 只在测试调用失败时截图
    if rep.when == "call" and rep.failed:
        page = item.funcargs.get("page") # 从 item.funcargs 获取 page fixture
        if not page:
            logger.warning("[Web Conftest] 'page' fixture not found in failed test, skipping screenshot.")
            return # 如果没有 page 对象，直接返回

        # 生成截图文件名
        safe_test_name = item.name.replace("[", "-").replace("]", "")
        file_name = gen_screenshot_filename(safe_test_name)
        file_path = None

        try:
            # 尝试获取当前事件循环并执行异步截图
            loop = asyncio.get_event_loop()
            logger.info(f"[Web Conftest] Test failed, attempting Playwright screenshot: {file_name}")
            # 简化：总是尝试用 run_until_complete 执行异步截图
            # 这依赖于 pytest-asyncio 的事件循环管理方式，可能在某些边缘情况不稳定
            # 但比之前检查 is_running() 更简洁
            file_path = loop.run_until_complete(save_screenshot(page, file_name, report=True))
            logger.info(f"[Web Conftest] Screenshot saved to: {file_path}")

        except RuntimeError as loop_err:
            # 捕获 run_until_complete 可能在错误状态下（如嵌套调用、循环关闭）抛出的 RuntimeError
            logger.error(f"[Web Conftest] Failed to run async screenshot due to event loop issue: {loop_err}", exc_info=True)
        except Exception as e:
            # 捕获截图或保存过程中的其他异常
            logger.error(f"[Web Conftest] Failed to save screenshot: {e}", exc_info=True)

        # 尝试将截图附加到 Allure 报告
        if file_path and allure and os.path.exists(file_path):
            try:
                with open(file_path, "rb") as f:
                    allure.attach(f.read(), name=file_name, attachment_type=allure.attachment_type.PNG)
                logger.info(f"[Web Conftest] Screenshot attached to Allure: {file_name}")
            except Exception as attach_err:
                logger.error(f"[Web Conftest] Failed to attach screenshot to Allure: {attach_err}")
        elif file_path:
            # 如果文件路径存在但文件不存在（截图失败但未抛异常？）
            logger.warning(f"[Web Conftest] Screenshot file path generated, but file not found, cannot attach: {file_path}")
        # 如果 file_path 为 None (截图过程中异常)，则不尝试附加
