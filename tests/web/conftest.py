import os
from dotenv import load_dotenv
import pytest
import pytest_asyncio
from playwright.async_api import async_playwright, Page, Browser
import yaml
from pathlib import Path
from src.utils.screenshot import save_screenshot, gen_screenshot_filename
from src.utils.config.manager import get_config
import allure
import asyncio

# 明确指定.env路径，保证任何目录运行都能加载
load_dotenv(dotenv_path=os.path.abspath(os.path.join(os.path.dirname(__file__), '../../.env')))

@pytest_asyncio.fixture(scope="session")
async def playwright_instance():
    """全局Playwright上下文"""
    async with async_playwright() as p:
        yield p

@pytest_asyncio.fixture(scope="function")
async def browser():
    """浏览器实例，自动关闭"""
    headless_env = os.environ.get("HEADLESS", "true").lower()
    headless = headless_env in ("1", "true", "yes")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        yield browser
        await browser.close()

@pytest_asyncio.fixture
async def page(browser: Browser) -> Page:
    """新建页面，自动关闭"""
    page = await browser.new_page()
    yield page
    await page.close()

@pytest.fixture
def login_data():
    """加载登录测试数据（YAML）。"""
    data_path = Path(__file__).parent.parent.parent / "data/web/login/login_data.yaml"
    with open(data_path, encoding="utf-8") as f:
        return yaml.safe_load(f)

@pytest.fixture
def test_users(login_data):
    """动态合成所有登录测试用户数据。"""
    config = get_config()
    users = login_data["users"].copy()

    # 用配置系统的账号密码填充valid场景
    users["valid"]["username"] = config["credentials"]["default"]["username"]
    users["valid"]["password"] = config["credentials"]["default"]["password"]

    return users

@pytest.fixture
def login_url():
    """提供登录页面URL（通过统一配置获取）"""
    config = get_config()
    return config["web"]["base_url"]

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """用例失败自动截图并集成Allure报告（同步hookwrapper，兼容pytest机制）"""
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        page = item.funcargs.get("page")
        if page:
            file_name = gen_screenshot_filename(item.name)
            # 用同步方式调用异步截图
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            file_path = loop.run_until_complete(save_screenshot(page, file_name, report=True))
            if file_path and allure:
                with open(file_path, "rb") as f:
                    allure.attach(f.read(), name=file_name, attachment_type=allure.attachment_type.PNG)