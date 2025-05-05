"""
Web测试专用的pytest固件配置。
提供Web UI测试所需的浏览器、页面对象、数据和截图功能。
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
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

# --- .env 加载逻辑到 Web Conftest --- 
project_root = Path(__file__).parents[2]
env_path = project_root / '.env'
if env_path.is_file():
    # 使用 override=True 确保 .env 优先
    load_dotenv(dotenv_path=env_path, override=True) 
    logger.info(f"[Web Conftest] Loaded environment variables from: {env_path}")
else:
    logger.warning(f"[Web Conftest] .env file not found at: {env_path}")
# -------------------------------------------


@pytest_asyncio.fixture(scope="function")
async def browser() -> Browser:
    """浏览器实例 (Function Scope)，恢复旧版实现。"""
    # 直接从环境变量获取 headless
    headless_env = os.environ.get("HEADLESS", "true").lower()
    headless = headless_env in ("1", "true", "yes")
    logger.info(f"[Web Conftest] Launching browser (Function Scope, Old Style): Hardcoding Chromium, headless={headless} (from env)")
    
    # 在 fixture 内部创建 playwright 上下文
    async with async_playwright() as p:
        # 硬编码启动 chromium, 只传递 headless
        browser_instance = await p.chromium.launch(headless=headless)
        yield browser_instance
        logger.info("[Web Conftest] Closing browser (Function Scope, Old Style).")
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
def test_users() -> Dict[str, Any]:
    """加载并合成 Web 登录测试用户数据（接近旧版），修正数据文件路径。"""
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
        
        # 在 fixture 内部调用 get_config 来填充 valid 用户
        config = get_config()
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
def login_url() -> str:
    """获取 OMP 登录 URL，优先使用 omp_login_url，若未配置则回退到 base_url。"""
    # 在 fixture 内部调用 get_config
    config = get_config()
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
    """用例失败自动截图并集成Allure报告（同步hookwrapper，兼容pytest机制）"""
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        page = item.funcargs.get("page")
        if page:
            safe_test_name = item.name.replace("[", "-").replace("]", "")
            file_name = gen_screenshot_filename(safe_test_name) 
            
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            file_path = None
            try:
                logger.info(f"[Web Conftest] Test failed, attempting Playwright screenshot: {file_name}")
                file_path = loop.run_until_complete(save_screenshot(page, file_name, report=True))
            except Exception as e:
                 logger.error(f"[Web Conftest] Failed to save screenshot: {e}", exc_info=True)
            
            if file_path and allure and os.path.exists(file_path):
                try:
                    with open(file_path, "rb") as f:
                        allure.attach(f.read(), name=file_name, attachment_type=allure.attachment_type.PNG)
                    logger.info(f"[Web Conftest] Screenshot attached to Allure: {file_name}")
                except Exception as attach_err:
                    logger.error(f"[Web Conftest] Failed to attach screenshot to Allure: {attach_err}")
            elif file_path:
                 logger.warning(f"[Web Conftest] Screenshot file not found, cannot attach: {file_path}")
        else:
            logger.warning("[Web Conftest] 'page' fixture not found in failed test, skipping screenshot.")
