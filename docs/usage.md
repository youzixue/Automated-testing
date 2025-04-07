# 自动化测试框架使用指南

本文档介绍如何使用和扩展自动化测试框架。

## 目录

- [环境配置](#环境配置)
- [运行测试](#运行测试)
- [创建新测试](#创建新测试)
- [页面对象模式](#页面对象模式)
- [数据驱动测试](#数据驱动测试)
- [验证码处理](#验证码处理)
- [报告生成](#报告生成)
- [故障排除](#故障排除)

## 环境配置

### 本地开发环境

1. 创建本地配置文件:
```bash
cp config/env/template.yaml config/env/local.yaml
```

2. 编辑`local.yaml`文件，设置实际的测试环境URL和账号信息。

3. 设置环境变量以安全存储敏感信息:
```bash
export ADMIN_PASSWORD="your_admin_password"
export USER1_PASSWORD="your_user_password"
```

### 支持的浏览器

框架支持以下浏览器:
- Chromium (默认)
- Firefox
- WebKit

可在配置文件中修改:
```yaml
web:
  browser: firefox  # chromium, firefox, webkit
```

## 运行测试

### 基本命令

```bash
# 运行所有测试
poetry run pytest

# 运行特定标记的测试
poetry run pytest -m web
poetry run pytest -m "web and login"
poetry run pytest -m "not slow"

# 运行特定模块的测试
poetry run pytest tests/web/login/
```

### 并行执行

```bash
# 使用4个worker并行执行
poetry run pytest -n 4

# 按模块并行执行
poetry run pytest --dist=loadfile -n 4
```

### 失败重试

```bash
# 失败重试3次
poetry run pytest --reruns 3
```

## 创建新测试

### Web测试示例

1. 创建页面对象:

```python
# src/web/pages/login_page.py
from typing import Tuple

from src.core.base.element import BaseElement
from src.web.pages.base_page import BasePage

class LoginPage(BasePage):
    """登录页面对象"""
    
    def __init__(self, driver):
        """初始化登录页面对象
        
        Args:
            driver: Web驱动实例
        """
        super().__init__(driver)
        self.url = "/login"
        self.username_input = self._get_element("#username")
        self.password_input = self._get_element("#password")
        self.login_button = self._get_element("#login-btn")
        self.error_message = self._get_element(".error-notification")
        
    def login(self, username: str, password: str) -> "DashboardPage":
        """执行登录操作
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            DashboardPage: 登录成功后的仪表盘页面
            
        Raises:
            LoginError: 登录失败时抛出
        """
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()
        
        # 导入DashboardPage，避免循环引用
        from src.web.pages.dashboard_page import DashboardPage
        return DashboardPage(self.driver)
```

2. 创建测试用例:

```python
# tests/web/login/test_basic.py
import pytest
from src.web.pages.login_page import LoginPage

@pytest.mark.web
@pytest.mark.login
def test_valid_login(web_driver, valid_credentials):
    """测试有效账号登录"""
    login_page = LoginPage(web_driver)
    login_page.navigate()
    
    dashboard = login_page.login(
        valid_credentials["username"],
        valid_credentials["password"]
    )
    
    # 验证登录成功
    assert dashboard.is_loaded()
    assert dashboard.get_welcome_message() == f"欢迎, {valid_credentials['username']}"
```

## 页面对象模式

页面对象模式是一种设计模式，用于将UI元素和操作封装在专门的类中，使测试代码更清晰和可维护。

### 基本原则

1. 每个页面创建一个专门的类
2. 页面类负责封装元素定位和页面操作
3. 测试用例只通过页面类与UI交互
4. 页面方法应返回操作结果或新的页面对象

### 组件化页面对象

对于复杂页面，可以将共用部分抽取为可重用组件:

```python
# 页眉组件示例
class HeaderComponent:
    def __init__(self, driver):
        self.driver = driver
        self.logo = driver.get_element(".logo")
        self.user_menu = driver.get_element(".user-menu")
        
    def open_user_menu(self):
        self.user_menu.click()
        return UserMenuComponent(self.driver)
        
# 使用组件的页面对象
class DashboardPage(BasePage):
    def __init__(self, driver):
        super().__init__(driver)
        self.header = HeaderComponent(driver)
        # 页面特有元素...
```

## 数据驱动测试

框架支持从CSV、YAML和Excel文件加载测试数据:

```python
# tests/web/login/test_accounts.py
import pytest
from src.web.pages.login_page import LoginPage

@pytest.mark.web
@pytest.mark.login
@pytest.mark.parametrize("test_data", load_test_data("web/login/accounts.csv"))
def test_login_scenarios(web_driver, test_data):
    """测试不同账号登录场景"""
    login_page = LoginPage(web_driver)
    login_page.navigate()
    
    if test_data["expected_result"] == "success":
        dashboard = login_page.login(test_data["username"], test_data["password"])
        assert dashboard.is_loaded()
    else:
        with pytest.raises(LoginError) as exc_info:
            login_page.login(test_data["username"], test_data["password"])
        assert test_data["expected_result"] in str(exc_info.value)
```

## 验证码处理

框架集成了OCR验证码识别功能:

```python
from src.utils.ocr import recognize_captcha

def test_login_with_captcha(web_driver):
    login_page = LoginPage(web_driver)
    login_page.navigate()
    
    # 获取验证码图片并识别
    captcha_element = login_page.get_captcha_element()
    captcha_text = recognize_captcha(captcha_element.screenshot())
    
    # 填写验证码
    login_page.fill_captcha(captcha_text)
    
    # 完成登录
    dashboard = login_page.login("admin", "password")
    assert dashboard.is_loaded()
```

## 报告生成

框架集成了Allure报告生成功能:

```bash
# 运行测试并生成Allure结果：
poetry run pytest --alluredir=./output/allure-results tests/

# 在本地查看Allure报告：
poetry run allure serve ./output/allure-results
```

### 添加报告附件

```python
import allure

def test_with_attachments(web_driver):
    # 测试代码...
    
    # 添加截图
    allure.attach(
        web_driver.screenshot(), 
        name="screenshot", 
        attachment_type=allure.attachment_type.PNG
    )
    
    # 添加日志
    allure.attach(
        "日志内容", 
        name="log.txt", 
        attachment_type=allure.attachment_type.TEXT
    )
```

## 故障排除

### 常见问题

1. **测试超时**
   - 检查网络连接
   - 增加超时设置 `global.timeout: 60`
   - 检查目标系统是否可用

2. **元素未找到**
   - 检查定位器是否正确
   - 使用等待策略 `wait_for_element`
   - 检查页面是否有变化

3. **验证码识别失败**
   - 检查图片清晰度
   - 调整验证码截取区域
   - 更新OCR模型

### 查看日志

测试运行过程中产生的日志默认记录在 `output/logs/test_run.log` (请根据实际配置检查)。可以使用 `cat` 或其他文本查看工具查看：

```bash
cat output/logs/test_run.log
```

### 调试模式

```bash
# 启用调试日志
poetry run pytest --log-cli-level=DEBUG
``` 