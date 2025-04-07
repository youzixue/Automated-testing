"""
全局测试固件。

提供所有测试通用的pytest fixtures。
"""

import os
import tempfile
import threading
import json
import pytest
import platform
import allure
from datetime import datetime
from contextlib import contextmanager
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Dict, Any, Generator, Optional, Union
from pathlib import Path
import logging
import time
import sys
import shutil

from src.utils.config.manager import get_config
from src.utils.email_notifier import get_email_notifier
from src.utils.log.manager import get_logger

# Use framework logger
logger = get_logger(__name__)

# --- Pytest Hooks ---

def pytest_addoption(parser):
    """向pytest添加命令行选项。"""
    # --browser 选项由 pytest-playwright 插件提供，此处移除
    # parser.addoption(
    #     \"--browser\", action=\"store\", default=\"chromium\", help=\"指定浏览器类型: chromium, firefox, webkit\"
    # )
    parser.addoption(
        "--headless", action="store_true", default=False, help="以无头模式运行浏览器"
    )
    # --base-url 选项由 pytest-base-url 插件提供，此处移除

# 全局变量，用于记录开始时间
start_time = time.time()

@pytest.fixture(scope='session', autouse=True)
def allure_environment_info(request):
    """设置Allure环境信息"""
    config_data = get_config() # 获取配置字典
    report_config = config_data.get("report", {}) # 使用字典 get 方法
    allure_env_file = report_config.get("allure", {}).get("environment_file", "output/allure-results/environment.properties")
    
    # 确保目录存在
    allure_env_path = Path(allure_env_file)
    allure_env_path.parent.mkdir(parents=True, exist_ok=True)
    
    environment_info = {
        "Browser": request.config.getoption("--browser"),
        "BaseURL": request.config.getoption("--base-url"),
        "Headless": str(request.config.getoption("--headless")), # 转换为字符串
        "PythonVersion": sys.version.split()[0],
        "Platform": sys.platform,
        # 可以从配置中添加更多环境信息
        "TestEnvironment": config_data.get("environment", "unknown") # 使用字典 get 方法
    }
    
    with open(allure_env_path, 'w') as f:
        for key, value in environment_info.items():
            if value: # 只写入非空值
                f.write(f"{key}={value}\n")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_protocol(item: pytest.Item, nextitem: Optional[pytest.Item]) -> Generator[None, None, None]:
    """处理测试执行过程。
    
    为每个测试用例添加测试开始和结束时间等元数据。
    
    Args:
        item: 当前测试项
        nextitem: 下一个测试项
    """
    # 记录测试开始时间
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 将测试开始时间添加到allure报告
    allure.dynamic.label("startTime", start_time)
    
    # 执行测试
    yield
    
    # 记录测试结束时间
    end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    allure.dynamic.label("endTime", end_time)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo) -> Generator[None, None, None]:
    """处理测试结果报告。
    
    捕获测试失败的截图和日志，添加到Allure报告中。
    
    Args:
        item: 测试项
        call: 测试调用
    """
    # 执行测试
    outcome = yield
    report = outcome.get_result()
    
    # 仅在用例执行阶段和失败时处理
    if report.when == "call" and report.failed:
        try:
            # 尝试获取driver
            if hasattr(item, "funcargs") and "web_driver" in item.funcargs:
                driver = item.funcargs["web_driver"]
                # 捕获截图
                screenshot = driver.take_screenshot()
                allure.attach(
                    screenshot,
                    name="失败截图",
                    attachment_type=allure.attachment_type.PNG
                )
                
                # 添加页面源码
                page_source = driver.get_page_source()
                allure.attach(
                    page_source,
                    name="页面源码",
                    attachment_type=allure.attachment_type.HTML
                )
        except Exception as e:
            logger.error(f"捕获截图失败: {e}")


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session):
    """所有测试会话结束后执行一次"""
    # 运行结束时间
    end_time = time.time()
    logger.info(f"测试会话结束于: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(end_time))}")
    total_duration = end_time - start_time
    logger.info(f"总耗时: {total_duration:.2f} 秒")

    # 获取配置 (现在是字典)
    config_data = get_config()

    # 从配置字典中获取报告配置
    report_config = config_data.get("report", {})
    notification_config = config_data.get("notification", {})

    # 检查是否启用通知
    if notification_config.get("enabled", False):
        email_config = notification_config.get("email", {})
        if email_config.get("enabled", False):
            try:
                notifier = get_email_notifier()

                recipients = email_config.get("recipients", [])
                subject_template = email_config.get("subject_template", "自动化测试报告 [{status}]")

                # 获取测试统计信息
                # 注意: session._collected 不可靠，使用 session.results
                stats = session.config.cache.get("terminalreporter/stats", {})
                num_passed = len(stats.get("passed", []))
                num_failed = len(stats.get("failed", []))
                num_skipped = len(stats.get("skipped", []))
                num_error = len(stats.get("error", []))
                total_tests = num_passed + num_failed + num_skipped + num_error
                status = "成功" if num_failed == 0 and num_error == 0 else "失败"

                # 格式化邮件主题和正文
                subject = subject_template.format(status=status)
                body = f"""
自动化测试执行完成。

测试总结:
- 总计: {total_tests}
- 通过: {num_passed}
- 失败: {num_failed}
- 跳过: {num_skipped}
- 错误: {num_error}
- 总耗时: {total_duration:.2f} 秒

测试环境:
- 浏览器: {session.config.getoption("--browser")}
- BaseURL: {session.config.getoption("--base-url")}
- 无头模式: {session.config.getoption("--headless")}
- 平台: {sys.platform}

详情请查看附件中的Allure报告。
"""

                # 查找Allure报告路径
                attachment_path = None
                allure_report_dir = report_config.get("allure", {}).get("report_dir", "output/allure-report")
                allure_index_path = Path(allure_report_dir) / "index.html"

                if allure_index_path.exists():
                    # 需要打包整个报告目录才能在邮件中正常查看
                    report_zip_path = shutil.make_archive(
                        base_name=f"allure-report-{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        format='zip',
                        root_dir=allure_report_dir
                    )
                    attachment_path = report_zip_path
                    logger.info(f"将附加Allure报告压缩包: {attachment_path}")
                else:
                    logger.warning(f"未找到Allure报告入口文件: {allure_index_path}, 邮件将不包含报告附件")

                notifier.send_notification(recipients, subject, body, attachment_path=attachment_path)

                # 清理压缩文件
                if attachment_path and os.path.exists(attachment_path):
                    os.remove(attachment_path)
                    logger.debug(f"已删除临时报告压缩包: {attachment_path}")

            except Exception as e:
                logger.error(f"发送邮件通知失败: {e}", exc_info=True)

    # Allow pytest to continue teardown
    yield


# --- Web 测试相关的 Fixtures ---

def _count_tests(stats: Dict) -> int:
    """
    计算测试用例总数
    
    Args:
        stats: 测试统计信息
        
    Returns:
        int: 测试用例总数
    """
    return sum(len(x) for x in stats.values() if isinstance(x, list))


def _get_failure_message(report) -> str:
    """
    获取测试失败信息
    
    Args:
        report: 测试报告对象
        
    Returns:
        str: 失败信息
    """
    if report.longreprtext:
        return report.longreprtext
    elif isinstance(report.longrepr, tuple):
        return str(report.longrepr)
    elif report.longrepr:
        return str(report.longrepr)
    return "No failure message available"


def _get_failure_trace(report) -> str:
    """提取失败的traceback信息"""
    try:
        return report.longreprtext
    except AttributeError:
        return "Traceback not available."


# --- 全局 Fixtures ---

# 在这里添加其他全局通用的fixtures
# 将特定的fixtures移到更专一的测试模块中 