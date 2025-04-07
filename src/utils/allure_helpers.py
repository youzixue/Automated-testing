"""
Allure报告帮助工具。提供便捷的Allure报告功能封装，简化报告生成。
"""

import os
import inspect
import functools
import platform
import allure
import datetime
import json
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast, Tuple, Protocol

# 函数返回类型
T = TypeVar('T')

# 定义截图接口，避免直接依赖WebDriver
class ScreenshotProvider(Protocol):
    """截图提供者协议。
    
    定义能够提供截图的对象接口，避免直接依赖具体实现类。
    """
    def take_screenshot(self) -> bytes:
        """获取截图。
        
        Returns:
            截图数据（PNG格式）
        """
        ...

def attach_screenshot(driver: ScreenshotProvider, name: str = "截图") -> None:
    """捕获并附加截图到Allure报告。
    
    Args:
        driver: 任何实现了take_screenshot方法的对象
        name: 截图名称
    """
    try:
        screenshot = driver.take_screenshot()
        allure.attach(
            screenshot,
            name=name,
            attachment_type=allure.attachment_type.PNG
        )
    except Exception as e:
        # 捕获截图失败时，添加错误信息到报告
        allure.attach(
            f"截图捕获失败: {str(e)}",
            name=f"{name} (失败)",
            attachment_type=allure.attachment_type.TEXT
        )


def attach_html(html_content: str, name: str = "HTML内容") -> None:
    """附加HTML内容到Allure报告。
    
    Args:
        html_content: HTML内容
        name: 附件名称
    """
    allure.attach(html_content, name=name, attachment_type=allure.attachment_type.HTML)


def attach_file(file_path: str, name: Optional[str] = None) -> None:
    """附加文件到Allure报告。
    
    根据文件扩展名自动确定附件类型。
    
    Args:
        file_path: 文件路径
        name: 附件名称，默认为文件名
    """
    if not os.path.exists(file_path):
        allure.attach(
            f"文件不存在: {file_path}",
            name=name or os.path.basename(file_path),
            attachment_type=allure.attachment_type.TEXT
        )
        return
    
    # 使用文件名作为默认名称
    if name is None:
        name = os.path.basename(file_path)
    
    # 根据文件扩展名确定类型
    _, ext = os.path.splitext(file_path.lower())
    attachment_type = allure.attachment_type.TEXT  # 默认类型
    
    # 映射文件扩展名到Allure附件类型
    ext_map = {
        '.png': allure.attachment_type.PNG,
        '.jpg': allure.attachment_type.JPG,
        '.jpeg': allure.attachment_type.JPG,
        '.gif': allure.attachment_type.PNG,
        '.html': allure.attachment_type.HTML,
        '.htm': allure.attachment_type.HTML,
        '.xml': allure.attachment_type.XML,
        '.json': allure.attachment_type.JSON,
        '.css': allure.attachment_type.TEXT,
        '.js': allure.attachment_type.TEXT,
        '.log': allure.attachment_type.TEXT,
        '.txt': allure.attachment_type.TEXT,
        '.csv': allure.attachment_type.CSV
    }
    
    attachment_type = ext_map.get(ext, allure.attachment_type.TEXT)
    
    # 读取文件并附加到报告
    with open(file_path, 'rb') as f:
        content = f.read()
    
    allure.attach(content, name=name, attachment_type=attachment_type)


def step_decorator(title: str) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Allure步骤装饰器。
    
    创建一个带有标题的Allure测试步骤。步骤开始前记录参数，结束后记录返回值。
    如果发生异常，将异常信息作为步骤结果记录。
    
    Args:
        title: 步骤标题，可以包含格式化占位符，如"{}"
        
    Returns:
        装饰器函数
    
    示例:
        @step_decorator("登录系统，用户名: {}")
        def login(username, password):
            # username将作为格式化参数传入标题
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            # 获取函数参数名称
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            
            # 格式化步骤标题
            if '{' in title and '}' in title:
                # 参数用于格式化标题
                format_args = []
                
                # 首先添加位置参数（通常第一个是self）
                if len(args) > 0 and len(param_names) > 0:
                    # 如果第一个参数是self，跳过它
                    if param_names[0] in ('self', 'cls'):
                        format_args.extend([str(arg) for arg in args[1:]])
                    else:
                        format_args.extend([str(arg) for arg in args])
                
                # 添加关键字参数
                for name, value in kwargs.items():
                    # 避免添加复杂对象
                    if isinstance(value, (str, int, float, bool)):
                        format_args.append(str(value))
                
                step_title = title.format(*format_args)
            else:
                step_title = title
            
            # 执行步骤
            with allure.step(step_title):
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    # 捕获异常并添加到报告
                    allure.attach(
                        str(e),
                        name="异常信息",
                        attachment_type=allure.attachment_type.TEXT
                    )
                    raise
        
        return wrapper
    
    return decorator


def create_environment_properties(output_dir: str = "output/allure-results") -> None:
    """创建环境属性文件。
    
    收集系统和配置信息，生成Allure报告的环境信息文件。
    
    Args:
        output_dir: 输出目录，默认为Allure结果目录
    """
    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 收集环境信息
    env_data = {
        "测试环境": os.environ.get("ENV", "dev"),
        "Python版本": platform.python_version(),
        "操作系统": f"{platform.system()} {platform.release()}",
        "浏览器": os.environ.get("BROWSER", "chromium"),
        "无头模式": os.environ.get("HEADLESS", "false"),
        "测试时间": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Git分支": os.environ.get("GIT_BRANCH", "unknown"),
        "Git提交": os.environ.get("GIT_COMMIT", "unknown"),
        "执行用户": os.environ.get("USER", platform.node())
    }
    
    # 尝试从配置读取更多信息
    try:
        from src.utils.config.manager import ConfigManager
        config = ConfigManager().get_config()
        
        # 添加Web配置
        if "web" in config:
            web_config = config["web"]
            if "browser" in web_config:
                env_data["浏览器"] = web_config["browser"]
            if "headless" in web_config:
                env_data["无头模式"] = str(web_config["headless"])
        
        # 添加API配置
        if "api" in config and "base_url" in config["api"]:
            env_data["API基础URL"] = config["api"]["base_url"]
    except:
        # 配置读取失败，使用默认值
        pass
    
    # 写入environment.properties文件
    with open(f"{output_dir}/environment.properties", "w", encoding="utf-8") as f:
        for key, value in env_data.items():
            f.write(f"{key}={value}\n")
    
    # 写入executor.json文件
    executor_info = {
        "name": "Automated Test Framework",
        "type": "python",
        "reportName": "自动化测试报告",
        "buildName": f"Build {datetime.datetime.now().strftime('%Y%m%d%H%M')}",
        "reportUrl": "",
        "buildUrl": ""
    }
    
    with open(f"{output_dir}/executor.json", "w", encoding="utf-8") as f:
        json.dump(executor_info, f, ensure_ascii=False, indent=2)


def create_categories_file(output_dir: str = "output/allure-results") -> None:
    """创建分类定义文件。
    
    创建Allure报告的测试结果分类定义，用于组织测试失败结果。
    
    Args:
        output_dir: 输出目录，默认为Allure结果目录
    """
    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 定义分类
    categories = [
        {
            "name": "接口超时",
            "matchedStatuses": ["failed"],
            "messageRegex": ".*[Tt]imeout.*"
        },
        {
            "name": "元素定位失败",
            "matchedStatuses": ["failed"],
            "messageRegex": ".*Unable to locate element.*|.*NoSuchElementException.*|.*ElementNotFound.*"
        },
        {
            "name": "断言失败",
            "matchedStatuses": ["failed"],
            "messageRegex": ".*AssertionError.*"
        },
        {
            "name": "认证失败",
            "matchedStatuses": ["failed"],
            "messageRegex": ".*Authentication.*|.*Login failed.*|.*401.*|.*403.*"
        },
        {
            "name": "其他错误",
            "matchedStatuses": ["failed", "broken"],
            "messageRegex": ".*"
        }
    ]
    
    # 写入categories.json文件
    with open(f"{output_dir}/categories.json", "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)


# 为了简化使用，提供一个直接可用的step装饰器
step = step_decorator 