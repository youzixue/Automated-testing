# 自动化测试框架

一个基于Python的现代化自动化测试框架，支持Web UI、API和移动应用的自动化测试。框架采用分层架构设计，提供了灵活、可扩展和易维护的测试解决方案。

## 架构设计

本框架采用七层分层架构，确保代码清晰、解耦和可维护：

1. **测试用例层 (Tests)**：包含实际的测试用例和测试场景。
2. **固件层 (Fixtures)**：负责测试数据、环境和依赖的设置与清理。
3. **业务对象层 (Business)**：封装页面对象、API服务和业务流程。
4. **平台实现层 (Platform)**：实现各平台（Web、API、移动）的具体功能。
5. **核心抽象层 (Core)**：定义框架的核心接口和抽象类。
6. **工具层 (Utils)**：提供通用工具类和辅助功能。
7. **外部集成层 (External)**：管理外部依赖和第三方库。

### 目录结构

## 框架目录结构

```
Automated-testing/
├── config/                       # 配置文件目录
├── data/                         # 测试数据目录
├── output/logs/                  # 日志目录 (gitignore)
├── output/screenshots/           # 截图目录 (gitignore)
├── output/reports/               # 报告目录 (gitignore)
├── src/                          # 源代码目录
└── tests/                        # 测试用例目录
├── .gitignore                        # Git忽略文件
```

## 核心功能

### 1. Web测试功能

- 基于Playwright的浏览器自动化
- 页面对象模式封装页面交互
- 智能等待策略提高测试稳定性
- 元素操作封装（点击、输入、拖放等）
- 截图和视频录制支持

### 2. API测试功能

- 多协议支持（REST、GraphQL、SOAP）
- 请求响应验证
- 模拟服务器（Mock Server）
- 性能指标收集

### 3. 移动测试功能

- Android和iOS测试支持
- 跨平台元素定位策略
- 手势操作模拟
- 应用生命周期管理

### 4. 公共功能

- 统一的配置管理系统
- 完整的异常处理机制
- 资源自动管理和释放
- 详细的日志记录
- 适配多环境的数据管理
- OCR验证码识别支持

## 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/yourusername/automated-testing.git
cd automated-testing

# 安装依赖
pip install -e .
```

### 配置

项目支持多级配置，优先级从高到低：

1. 环境变量
2. 本地配置 (config/local.yaml)
3. 环境配置 (config/env/{env}.yaml)
4. 默认配置 (config/settings.yaml)

主要配置项：

```yaml
# config/settings.yaml 示例
global:
  timeout: 30  # 默认超时时间(秒)
  headless: false  # 是否使用无头浏览器
  
web:
  browser: chromium  # 浏览器类型: chromium, firefox, webkit
  viewport:
    width: 1920
    height: 1080
  slow_mo: 0 # 慢动作执行 (毫秒)
  launch_options: {} # 额外的浏览器启动选项
  base_url: \"https://example.com\" # 默认基础 URL
  backup_url: \"\" # 备用 URL
  login:
    selectors:
      username_input: \"#username\" # 根据实际情况修改
      password_input: \"#password\"
      captcha_input: \"#captcha\"
      captcha_image: \"#captcha-image\"
      login_button: \"button[type='submit']\"
      error_message: \".error-message\"
    timeouts:
      page_load: 10
      login_success: 5
    captcha:
      enabled: true
      max_retry: 3
      refresh_delay: 0.5
    urls:
      success_patterns: [\"/dashboard\", \"/home\"]
  dashboard:
    selectors:
      welcome_message: \"#welcome\"
      logout_button: \"#logout\"

log:
  level: INFO
  format: "%(asctime)s [%(levelname)s] [%(name)s] [%(thread)d] - %(message)s"
  console:
    enabled: true
  file:
    enabled: true
    filename: \"output/logs/framework.log\"
    when: \"D\" # 按天轮转
```

### Web测试示例

```python
# tests/web/test_login.py
def test_login_success(web_driver):
    """测试登录成功场景"""
    # 使用页面对象模式
    login_page = OmpLoginPage(web_driver)
    login_page.navigate()
    
    # 执行登录操作
    # 假设 login_data fixture 提供了用户数据
    user = login_data[\"users\"][\"valid\"]
    dashboard = login_page.login(user[\"username\"], user[\"password\"])
    
    # 验证登录成功
    assert dashboard.is_loaded(), \"仪表盘页面未加载\"
    # 可以添加更具体的断言，例如检查欢迎消息
    # assert \"Welcome\" in dashboard.get_welcome_message()
```

### 页面对象示例

```python
# src/web/pages/omp_login_page.py
from src.web.pages.base_page import BasePage
from selenium.webdriver.common.by import By

class OmpLoginPage(BasePage):
    """登录页面对象"""
    
    # URL 通常在实例化时传入或从配置加载
    # URL = \"/login\" 
    
    # 页面元素选择器
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    CAPTCHA_INPUT = (By.ID, "captcha")
    CAPTCHA_IMAGE = (By.ID, "captcha-image")
    LOGIN_BUTTON = (By.ID, "login")
    ERROR_MESSAGE = (By.CLASS_NAME, "error-message")
    
    def navigate(self):
        """导航到登录页面"""
        self._driver.navigate(self.get_url())
        return self
    
    def login(self, username, password):
        """执行登录操作
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            DashboardPage: 登录成功后的仪表盘页面对象
            
        Raises:
            LoginError: 登录失败
        """
        self.fill_username(username)
        self.fill_password(password)
        
        if self.has_captcha_input(): # 假设有检查验证码的方法
            try:
                captcha = self.recognize_captcha() # 假设有识别验证码的方法
                self.fill_captcha(captcha) # 假设有填写验证码的方法
            except CaptchaError as e:
                raise LoginError(f\"验证码处理失败: {e}\") from e
                
        self.click_login_button()
        
        # 验证登录是否成功并返回 DashboardPage 或抛出 LoginError
        if self._is_login_successful(): # 假设有检查登录成功的方法
            from src.web.pages.dashboard_page import DashboardPage # 假设 DashboardPage 已定义
            return DashboardPage(self.driver)
        else:
            error_msg = self.get_error_message() or \"登录失败，未知原因\" # 假设有获取错误消息的方法
            raise LoginError(error_msg)

    # 其他页面操作方法，如填写用户名、密码、验证码，点击按钮等
    def fill_username(self, username: str):
        self.get_element(self.USERNAME_INPUT).fill(username)

    def fill_password(self, password: str):
        self.get_element(self.PASSWORD_INPUT).fill(password)

    def click_login_button(self):
        self.get_element(self.LOGIN_BUTTON).click()

    # ... 其他辅助方法 ...
```

## 运行测试

```bash
# 运行所有测试
pytest

# 运行Web测试
pytest tests/web/

# 运行特定测试文件
pytest tests/web/test_login.py

# 使用特定环境配置运行
ENV=prod pytest tests/api/
```

## 设计特点

1. **接口先行原则**：所有功能先定义抽象接口，再实现具体类。
2. **单一职责原则**：每个类和方法专注于单一职责。
3. **资源自动管理**：使用上下文管理器确保资源自动释放。
4. **智能等待策略**：使用动态退避算法优化等待策略。
5. **异常专一性**：为不同的错误场景定义专用的异常类型。
6. **配置外部化**：所有配置从外部加载，不硬编码。
7. **分层架构**：严格的层次结构确保清晰的依赖关系。

## 贡献指南

1. 创建功能分支进行开发 (`git checkout -b feature/your-feature`)
2. 提交更改 (`git commit -m 'Add some feature'`)
3. 推送到远程仓库 (`git push origin feature/your-feature`)
4. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 详见 [LICENSE](LICENSE) 文件

## 功能特点

- 基于Playwright的Web自动化测试
- 支持验证码OCR识别
- 集成Allure报告
- 支持多种浏览器和设备
- 智能等待策略
- 页面对象模式
- 邮件通知功能

## 安装

```bash
# 安装依赖
poetry install

# 安装Playwright浏览器
poetry run playwright install chromium

# 安装Allure报告工具
brew install allure  # macOS
```

## 使用方法

### 运行测试

```bash
# 运行所有测试
pytest

# 运行Web测试
pytest tests/web/

# 运行登录测试
pytest tests/web/login/

# 运行带标记的测试
pytest -m smoke
```

### 报告生成

测试执行后，Allure报告结果将自动保存到`output/allure-results`目录。

```bash
# 生成并打开Allure报告
./scripts/generate_allure_report.sh

# 指定结果目录
./scripts/generate_allure_report.sh path/to/results
```

### 邮件通知配置

邮件通知功能默认通过配置文件`config/settings.yaml`进行配置，敏感信息可通过环境变量提供。

#### 配置选项

- **enabled**: 是否启用邮件通知
- **smtp_server**: SMTP服务器地址
- **smtp_port**: SMTP服务器端口
- **use_ssl**: 是否使用SSL连接
- **use_tls**: 是否使用TLS连接
- **sender_email**: 发件人邮箱
- **recipients**: 收件人列表
- **subject_template**: 邮件主题模板
- **body_template**: 邮件正文模板
- **attach_report**: 是否附加测试报告
- **notify_on_failure**: 失败时立即通知

#### 环境变量配置

可以通过以下环境变量覆盖配置文件:

```bash
export EMAIL_ENABLED=true
export EMAIL_SMTP_SERVER=smtp.gmail.com
export EMAIL_SMTP_PORT=465
export EMAIL_USE_SSL=true
export EMAIL_SENDER=your-email@gmail.com
export EMAIL_RECIPIENTS=recipient1@example.com,recipient2@example.com
export EMAIL_PASSWORD=your-secure-password
```

## 目录结构说明

├── .github/                # GitHub Actions 工作流
├── .idea/                  # IDE 配置
├── .pytest_cache/          # Pytest 缓存
├── .venv/                  # Python 虚拟环境
├── config/                 # 项目配置
├── data/                   # 测试数据
├── docs/                   # 项目文档
├── output/                 # 输出目录 (日志, 报告, 截图)
│   ├── allure-results/
│   ├── coverage-data/
│   ├── logs/
│   ├── reports/
│   └── screenshots/
├── src/                    # 核心源代码
├── tests/                  # 测试用例
├── .cursor/                # Cursor 配置
├── .env                    # 本地环境变量
├── .env.example            # 环境变量示例
├── .gitignore              # Git 忽略配置
├── LICENSE                 # 项目许可证
├── pyproject.toml          # 项目依赖与配置
└── README.md               # 项目说明

## 项目设计

### 分层架构

1. **测试用例层**：tests/目录中的测试用例
2. **固件层**：tests/conftest.py中的测试固件
3. **业务对象层**：src/web/pages/等页面对象实现
4. **平台实现层**：src/web/、src/api/等平台特定实现
5. **核心抽象层**：src/core/base/中的抽象接口
6. **工具层**：src/utils/中的通用工具
7. **外部集成层**：依赖的第三方库 

## CI/CD集成

框架已与GitHub Actions完整集成，提供自动化测试执行、报告生成和结果通知功能。

### 工作流配置

CI/CD流程定义在`.github/workflows/test.yml`文件中，包含以下主要阶段：

1. **代码检查**: 执行Pylint和MyPy代码质量检查
2. **测试执行**: 并行运行Web、API和单元测试
3. **报告生成**: 聚合测试结果并生成Allure报告
4. **结果通知**: 自动发送测试结果邮件通知

### 触发方式

CI工作流可通过以下方式触发：

- 代码推送到main或develop分支
- 创建指向main或develop分支的Pull Request
- 计划任务（工作日每天凌晨1点自动运行）
- 手动触发（通过GitHub Actions界面）

### GitHub Secrets配置

需要在GitHub仓库设置中配置以下Secrets：

- **TEST_ADMIN_PASSWORD**: 管理员账号密码
- **TEST_USER_PASSWORD**: 普通用户密码
- **EMAIL_SMTP_SERVER**: SMTP服务器
- **EMAIL_SMTP_PORT**: SMTP端口
- **EMAIL_SENDER**: 发件人邮箱
- **EMAIL_RECIPIENTS**: 收件人列表（逗号分隔）
- **EMAIL_PASSWORD**: 邮箱密码

## 开发指南

### 添加新页面

1. 在`src/web/pages`目录下创建新页面类
2. 继承`BasePage`类
3. 定义页面元素和方法

```python
from src.web.pages.base_page import BasePage
from selenium.webdriver.common.by import By

class LoginPage(BasePage):
    # 定义页面元素
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.ID, "login")
    
    def login(self, username, password):
        """执行登录操作"""
        self.enter_text(self.USERNAME_INPUT, username)
        self.enter_text(self.PASSWORD_INPUT, password)
        self.click(self.LOGIN_BUTTON)
```

### 添加新测试用例

1. 在`tests/web`目录下创建新测试文件
2. 使用页面对象模型编写测试用例

```python
import pytest
import allure
from src.web.pages.login_page import LoginPage

@allure.feature("登录功能")
class TestLogin:
    @allure.story("有效凭据登录")
    def test_valid_login(self, driver):
        login_page = LoginPage(driver)
        login_page.navigate_to("/login")
        login_page.login("valid_user", "valid_password")
        assert login_page.is_success_message_displayed()
```

## 联系方式

- 邮箱: contact@example.com
- 项目地址: https://github.com/username/test-automation 