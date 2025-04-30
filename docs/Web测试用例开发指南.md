# Web自动化测试开发指南

## 1. 引言

### 1.1 指南目的

本指南旨在为测试人员提供一个清晰、详细的步骤指导，以便在本自动化测试框架内开发**Web UI自动化测试用例**。无论你是否熟悉本项目，遵循本指南都可以帮助你快速上手并编写出符合规范、可维护的Web测试。本指南不仅包含操作步骤，也致力于解释关键的技术概念和设计思想。

### 1.2 目标读者

本指南主要面向负责Web UI自动化测试开发的**测试工程师**，包括对Python、Playwright和自动化测试框架有不同程度了解的同学。

### 1.3 基础要求

在开始之前，建议具备以下基础知识：

*   **基本的Python编程知识**: 理解变量、函数、类、数据类型（字典、列表等）、`async`/`await` 异步编程概念（因为本项目使用 Playwright 的异步 API）。
*   **了解HTML和CSS**: 知道基本的HTML标签（`input`, `button`, `div` 等）和CSS选择器（用于定位元素）。
*   **了解Web浏览器工作原理**: 对页面加载、**DOM（文档对象模型 - 网页的结构化表示）**有基本概念。
*   **了解自动化测试基础**: 知道什么是自动化测试、页面对象模型（POM）等基本概念。

## 2. 项目背景与核心概念

### 2.1 七层架构概览

本项目采用标准的七层架构设计。Web UI测试主要涉及以下几个层级和目录：

*   **测试用例层 (`tests/`)**:
    *   `tests/web/`: 存放所有Web UI测试脚本 (`test_*.py` 文件)。**这是你主要编写测试逻辑的地方**。
*   **固件层 (`tests/`)**:
    *   `tests/conftest.py`: 全局共享的测试配置和辅助函数 (**Fixtures**)。全局共享的 Fixtures（比如通用的日志配置）可以放在这里。
    *   `tests/web/conftest.py`: Web测试专用的 **Fixtures**。特定于 Web 测试的 Fixtures（如 `page` 实例, `login_page` 对象等）应放在这里，以保持模块化。
*   **业务对象层 (`src/`, `data/`)**:
    *   `src/web/pages/`: **页面对象 (Page Objects)**。每个页面或重要的UI组件对应一个类，封装了该页面的元素定位和用户交互操作。**你的测试用例主要通过调用页面对象的方法来与Web界面交互**。
    *   `data/web/`: (如果需要) 存放Web测试所需的数据文件（YAML、JSON等），用于数据驱动。
*   **平台实现层 (`src/`)**:
    *   `src/web/`: 可能包含Web测试相关的底层封装，如自定义的浏览器驱动管理（如果需要）。测试人员一般**不需要直接修改**。
*   **核心抽象层 (`src/`)**:
    *   `src/core/base/`: 可能包含 `BasePage` 类（定义页面对象的通用方法和属性）、自定义异常等。
*   **工具层 (`src/`)**:
    *   `src/utils/`: 提供各种通用工具，如配置加载、日志记录、截图处理、验证码识别（OCR）等。

> **重要**: 在开始编码前，请务必花时间阅读 `docs/enhanced_architecture.md` 文档，以深入理解项目架构。 (遵循 `project-documentation-first` 规则, 详见 `.cursor/rules/project-documentation-first.mdc`)

### 2.2 核心组件与技术点解释

理解以下核心组件和技术点，有助于你更好地开发Web测试：

*   **`Playwright` (浏览器魔法师)**:
    *   **是什么**: 一个强大的、现代化的浏览器自动化库，由 Microsoft 开发。它允许我们用代码控制主流浏览器（Chromium, Firefox, WebKit）。
    *   **在框架中的作用**:
        1.  **浏览器交互**: 负责启动浏览器、打开页面、查找元素、点击、输入文本、截图等所有与浏览器界面交互的操作。
        2.  **异步优先**: 本项目主要使用 Playwright 的 **异步 API**。这意味着与页面交互的操作（如 `page.click()`, `page.fill()`）都需要使用 `await` 关键字，并且测试函数需要用 `async def` 定义并配合 `@pytest.mark.asyncio` 装饰器。异步可以提高测试执行效率。
        3.  **自动等待**: Playwright 内置了强大的[自动等待机制](https://playwright.dev/docs/actionability)。当你执行一个操作（如点击按钮）时，Playwright 会自动等待元素变为可操作状态再执行，**大大减少了不稳定和需要手动添加等待的情况** (遵循 `smart-wait-strategy`, 详见 `.cursor/rules/smart-wait-strategy.mdc`)。
        4.  **跨浏览器测试**: 可以轻松地在不同的浏览器引擎上运行相同的测试代码。
        5.  **强大的工具**: 提供了 [Playwright Inspector](https://playwright.dev/docs/inspector)（帮助生成和调试选择器）、[Trace Viewer](https://playwright.dev/docs/trace-viewer)（记录详细的测试执行过程，包括截图、网络请求、控制台日志，非常适合问题排查）等辅助工具。
    *   **测试人员交互**: 你主要通过 `conftest.py` 提供的 `page` **Fixture** 来获取一个已经初始化好的 Playwright 页面实例。然后，你会将这个 `page` 对象传递给你编写的**页面对象 (Page Objects)**，并通过页面对象封装好的方法来间接操作页面元素。

*   **页面对象模型 (Page Object Model, POM)**:
    *   **是什么**: 一种广泛应用于UI自动化测试的设计模式。核心思想是将每个页面（或可复用的UI组件）抽象成一个独立的类（Page Object）。
    *   **在框架中的作用**:
        1.  **封装**: 每个 Page Object 类负责**封装**该页面的**元素定位符**（Selectors）和**用户交互方法**。
        2.  **分离**: 将页面交互的实现细节与测试用例的业务逻辑**分离**。
        3.  **提高可维护性**: UI变化时，通常只需修改对应的 Page Object。
        4.  **提高可读性和复用性**: 测试代码更接近自然语言，页面操作逻辑可复用。
    *   **位置**: 页面对象类通常放在 `src/web/pages/` 目录下 (遵循 `page-object-pattern`, 详见 `.cursor/rules/page-object-pattern.mdc`)。

*   **`pytest` (测试引擎与指挥官)**:
    *   **作用**: 同样是Web测试的核心引擎，负责测试发现、执行、断言、Fixture管理等。
    *   **Web测试相关特性**:
        *   **Fixtures**: 对于Web测试至关重要。常见的 Fixture 包括：
            *   `browser` / `context` / `page`: 提供配置好的 Playwright 浏览器、浏览器上下文或页面实例。这些 Fixture 通常会处理浏览器的启动、关闭和环境配置。Fixture 可以设置不同的**作用域**（`function`, `class`, `module`, `session`），决定其多久被创建和销毁一次，对于管理资源生命周期非常重要。
            *   **页面对象 Fixture**: 可以创建 Fixture 来初始化并提供 Page Object 实例（如 `login_page` Fixture）。
            *   **测试数据 Fixture**: 可以创建 Fixture 来加载测试数据。
        *   **`@pytest.mark.asyncio`**: 由于使用 Playwright 的异步 API，**所有测试函数**都需要使用这个标记。
        *   **Markers**: 用 `@pytest.mark.web`, `@pytest.mark.smoke` 等标记来分类测试。
        *   **Parameterization**: 同样适用于Web测试，用于数据驱动。

*   **智能等待策略 (Smart Wait Strategy)**:
    *   **核心**: **优先依赖 Playwright 的自动等待机制**。避免使用 `time.sleep()`。
    *   **何时需要显式等待**: 只有在需要等待非 Playwright 自动处理的特定条件时（如特定网络请求完成、自定义的JS事件），才使用 Playwright 提供的显式等待方法（如 `page.wait_for_selector()`, `page.wait_for_load_state()`, `page.wait_for_event()` 等）。 (遵循 `smart-wait-strategy`, 详见 `.cursor/rules/smart-wait-strategy.mdc`)

*   **选择器 (Selectors)**:
    *   **是什么**: 用于定位页面元素的字符串表达式。
    *   **Playwright 支持**: 支持 [多种选择器引擎](https://playwright.dev/docs/selectors)，包括 CSS, XPath, text, role 等。
    *   **项目推荐**: 通常推荐使用**CSS 选择器**。应避免使用脆弱的选择器。建议使用**唯一的、稳定的属性**（如 `id`, `name`, `data-testid` 自定义属性）。

*   **Allure**: 同样用于生成Web测试的报告。

### 2.3 关键开发流程概览

1.  **理解需求与页面结构**: 分析待测试的Web页面功能和UI布局。
2.  **创建/更新页面对象**: 在 `src/web/pages/` 目录下，为页面定义Page Object类，封装元素定位符和交互方法。
3.  **(可选)准备测试数据**: 如果需要数据驱动，在 `data/web/` 创建或更新数据文件。
4.  **编写测试固件 (Fixtures)**: 在 `tests/web/conftest.py` 中，确保有提供 `page` 实例的Fixture，并可以添加初始化 Page Object 或加载数据的 Fixture。
5.  **编写测试用例**: 在 `tests/web/` 创建 `test_*.py` 文件，使用 Fixture 获取 `page` 对象或 Page Object 实例，调用 Page Object 方法执行操作，并使用 `assert` 验证结果。**记得使用 `async def` 和 `@pytest.mark.asyncio`**。
6.  **运行与调试**: 使用 `pytest` 命令执行测试，利用 Playwright 工具和日志进行调试。

## 3. 环境准备

### 3.1 安装项目依赖

同 API 指南，确保 Python 环境 (>=3.11) 和 `poetry install` 已执行。此外，首次运行 Playwright 可能需要安装浏览器驱动：

```bash
# 安装 Playwright 及其依赖 (poetry install 已包含)
# 安装浏览器驱动 (如果尚未安装)
poetry run playwright install
# 或者只安装特定浏览器，如 chromium
# poetry run playwright install chromium
```

(遵循 `environment-setup` 规则, 详见 `.cursor/rules/environment-setup.mdc`)

### 3.2 配置环境

*   **`.env` 文件**: 可能包含Web测试相关的URL (`WEB_BASE_URL`)、默认用户名/密码、浏览器设置（如 `HEADLESS=false` 用于本地调试）等。
*   **`config/` 目录**: `settings.yaml` 和环境特定文件可能包含默认超时时间、截图目录、浏览器类型等配置。

### 3.3 分析页面与元素

在编写代码前，需要：

1.  **熟悉待测页面**: 手动操作一遍，了解主要功能流程和元素。
2.  **定位关键元素**: 使用浏览器开发者工具（按 F12）检查需要交互的元素的 HTML 结构，确定合适的、稳定的**选择器**（推荐 CSS）。可以利用 Playwright Inspector 辅助生成和验证选择器。

## 4. 编写第一个Web测试（逐步指南 - 登录示例）

假设我们要测试一个Web登录页面：

*   **URL**: `/login` (基础URL在配置中)
*   **元素**: 用户名输入框、密码输入框、验证码图片、验证码输入框、登录按钮。
*   **成功场景**: 输入正确的凭据和验证码后，跳转到欢迎页面，并显示欢迎信息。
*   **失败场景**: 输入错误的凭据，停留在登录页，并显示错误提示。

### 步骤 1: 创建/更新页面对象 (Page Object)

*   **位置**: `src/web/pages/login_page.py`
*   **操作**: 定义 `LoginPage` 类，继承自 `BasePage` (如果存在)，封装元素和操作。 (遵循 `page-object-pattern`, 详见 `.cursor/rules/page-object-pattern.mdc`)

```python
# src/web/pages/login_page.py
from playwright.async_api import Page, Locator # 导入 Playwright 类型
from src.core.base.page import BasePage # 假设有一个 BasePage
# from src.utils.ocr import OCRHelper # 假设有 OCR 工具

class LoginPage(BasePage): # 继承 BasePage
    """封装登录页面的元素和操作"""

    # --- 元素定位符 (使用类变量存储，方便维护) ---
    _USERNAME_INPUT = "input[name='username']"
    _PASSWORD_INPUT = "input[name='password']"
    _CAPTCHA_INPUT = "input[name='captcha']"
    _CAPTCHA_IMG = "#captcha-img"
    _LOGIN_BUTTON = "button:has-text('登录')"
    _ERROR_MESSAGE = ".error-message"
    _WELCOME_MESSAGE = ".welcome-message" # 假设成功后页面有此元素

    # --- 页面操作方法 (使用 async/await) ---
    async def fill_username(self, username: str):
        """填写用户名"""
        await self.page.locator(self._USERNAME_INPUT).fill(username)
        self.logger.info(f"已填写用户名: {username}")

    async def fill_password(self, password: str):
        """填写密码"""
        await self.page.locator(self._PASSWORD_INPUT).fill(password)
        self.logger.info("已填写密码") # 不记录密码

    async def fill_captcha(self, captcha_code: str):
        """填写验证码"""
        await self.page.locator(self._CAPTCHA_INPUT).fill(captcha_code)
        self.logger.info(f"已填写验证码: {captcha_code}")

    async def click_login_button(self):
        """点击登录按钮"""
        await self.page.locator(self._LOGIN_BUTTON).click()
        self.logger.info("已点击登录按钮")

    async def get_captcha_code_from_image(self) -> str:
        """获取验证码图片并识别 (示例)"""
        captcha_img_locator: Locator = self.page.locator(self._CAPTCHA_IMG)
        screenshot_bytes = await captcha_img_locator.screenshot()
        # 调用 OCR (Optical Character Recognition) 工具识别验证码
        # captcha_text = await OCRHelper().recognize(screenshot_bytes)
        self.logger.warning("OCR识别功能未实现，返回固定值 'test'")
        return "test" # 暂时返回固定值

    async def login(self, username: str, password: str, auto_captcha: bool = True):
        """执行完整的登录操作"""
        await self.fill_username(username)
        await self.fill_password(password)
        if auto_captcha:
            captcha_code = await self.get_captcha_code_from_image()
            await self.fill_captcha(captcha_code)
        await self.click_login_button()

    async def is_login_successful(self, timeout: int = 5000) -> bool:
        """检查是否登录成功 (例如，检查欢迎信息是否可见)"""
        try:
            await self.page.locator(self._WELCOME_MESSAGE).wait_for(state="visible", timeout=timeout)
            self.logger.info("登录成功标识可见")
            return True
        except Exception: # Playwright 的 TimeoutError 等
            self.logger.warning("登录成功标识在指定时间内不可见")
            return False

    async def get_error_message(self, timeout: int = 3000) -> Optional[str]:
        """获取登录错误提示信息"""
        try:
            error_locator = self.page.locator(self._ERROR_MESSAGE)
            await error_locator.wait_for(state="visible", timeout=timeout)
            message = await error_locator.text_content()
            self.logger.info(f"获取到错误信息: {message}")
            return message
        except Exception:
            self.logger.warning("未找到或未在指定时间内看到错误信息")
            return None
```

**要点**:

*   封装元素定位符和页面操作方法。
*   方法使用 `async def` 和 `await`。
*   提供用于测试断言的方法。

### 步骤 2: 准备测试数据和 Fixture

*   **(可选)测试数据**: 如需参数化，可放在 `data/web/login_data.yaml`。
*   **Fixture (`tests/web/conftest.py`)**:
    *   确保有提供 Playwright `Page` 实例的 fixture (通常框架会提供名为 `page` 的 fixture)。
    *   可以创建 fixture 自动导航并提供 `LoginPage` 实例。

```python
# tests/web/conftest.py
import pytest
import pytest_asyncio # 用于异步 fixture
from playwright.async_api import Page
from src.web.pages.login_page import LoginPage
from src.utils.config import get_config # 假设有此工具

# 假设框架已提供了 'page' fixture (Page 实例)

@pytest_asyncio.fixture(scope="function") # 使用 pytest_asyncio 定义异步 fixture
async def login_page(page: Page) -> LoginPage: # 依赖 page fixture
    """
    Fixture: 导航到登录页并返回 LoginPage 实例。
    每个测试函数都会执行一次 (scope="function")。
    """
    # 从配置获取登录页面的基础 URL 和路径
    # 假设 base_url 可以从 page.context 或其他配置 fixture 获取
    # 这里仅作示例，实际获取方式可能不同
    try:
        # 尝试从 page 对象的上下文获取基础URL (更健壮的方式)
        # 注意：Playwright 的 Page 对象本身不直接包含完整的原始基础 URL，
        # 通常 base_url 是在创建 browser context 时设置的，或者从配置中获取。
        # 以下示例假设配置是主要来源
        config = get_config()
        base_url = config.get('web', {}).get('base_url', '')
        if not base_url:
             pytest.fail("无法确定基础 URL (请检查配置)")
    except Exception as e:
        pytest.fail(f"获取基础 URL 时出错: {e}")


    login_path = "/login" # 假设登录路径
    login_url = f"{base_url.rstrip('/')}{login_path}"

    await page.goto(login_url)
    login_page_obj = LoginPage(page) # 创建 LoginPage 实例
    return login_page_obj

# (可选) 提供测试用户的 fixture
@pytest.fixture(scope="session")
def test_users() -> dict:
    """Fixture: 提供测试用户信息 (可从配置或数据文件加载)"""
    return {
        "valid": {"username": "testuser", "password": "password123"},
        "invalid_password": {"username": "testuser", "password": "wrongpassword"},
        "non_existent": {"username": "nouser", "password": "password123"}
    }
```

**要点**:

*   使用 `@pytest_asyncio.fixture` 定义异步 fixture。
*   Fixture 负责准备测试环境和依赖对象。

### 步骤 3: 编写测试用例

*   **位置**: `tests/web/login/test_login.py`
*   **操作**: 编写 `async def` 测试函数，使用 Fixture 获取 `LoginPage` 实例和测试数据，调用页面对象方法，并使用 `assert` 验证结果。

```python
# tests/web/login/test_login.py
import pytest
from src.web.pages.login_page import LoginPage # 导入页面对象类

# 使用 @pytest.mark.asyncio 标记所有异步测试函数
@pytest.mark.asyncio
@pytest.mark.web # 添加 web 标记
@pytest.mark.login # 添加 login 功能标记
@pytest.mark.smoke # 添加 smoke 标记
async def test_successful_login(login_page: LoginPage, test_users: dict):
    """
    测试使用有效的用户名和密码成功登录。
    """
    user = test_users['valid']
    await login_page.login(user['username'], user['password'])
    success = await login_page.is_login_successful()
    assert success is True, "登录后未检测到成功标识 (如欢迎信息)"


@pytest.mark.asyncio
@pytest.mark.web
@pytest.mark.login
@pytest.mark.negative
async def test_login_with_invalid_password(login_page: LoginPage, test_users: dict):
    """
    测试使用无效的密码登录。
    """
    user = test_users['invalid_password']
    await login_page.login(user['username'], user['password'])
    success = await login_page.is_login_successful(timeout=1000) # 使用较短超时
    assert success is False, "使用无效密码时不应登录成功"
    error_message = await login_page.get_error_message()
    assert error_message is not None, "使用无效密码时应显示错误信息"
    assert "密码错误" in error_message or "invalid credentials" in error_message.lower(), \
           f"错误信息 '{error_message}' 不包含预期内容"

# 可以添加更多测试场景...

# 参数化示例：
# test_login_data = [
#     ("valid", True, None),
#     ("invalid_password", False, "密码错误"),
#     ("non_existent", False, "用户不存在"),
# ]
# @pytest.mark.parametrize("user_key, expected_success, expected_error_part", test_login_data)
# async def test_login_scenarios(login_page: LoginPage, test_users: dict, user_key, expected_success, expected_error_part):
#     # ... (测试逻辑同上) ...
```

**要点**:

*   **必须使用 `async def` 和 `@pytest.mark.asyncio`**。
*   通过 Fixture 获取 `LoginPage` 实例。
*   调用 Page Object 的方法执行操作和获取状态。
*   使用 `assert` 验证预期结果。

## 5. 执行测试与查看报告

### 5.1 执行测试

命令与 API 测试类似：

*   **执行所有测试**: `pytest`
*   **仅执行Web测试 (根据标记)**: `pytest -m web`
*   **执行特定文件**: `pytest tests/web/login/test_login.py`
*   **本地调试时显示浏览器界面**: `pytest tests/web/login/test_login.py --headed`
*   **减慢执行速度 (便于观察)**: `pytest tests/web/login/test_login.py --headed --slowmo 1000`
*   **生成Allure报告数据**: `pytest --alluredir=output/allure-results`

### 5.2 查看Allure报告

步骤同 API 指南，使用 `allure generate` 和 `allure open` 命令。

## 6. 遵循的最佳实践与项目规范

在开发Web测试时，请务必牢记并遵守以下项目规范：

*   **页面对象模型 (POM)**: 严格遵循 POM，将元素和操作封装在 `src/web/pages/` 中。 (遵循 `page-object-pattern`, 详见 `.cursor/rules/page-object-pattern.mdc`)
*   **智能等待**: 优先使用 Playwright 的自动等待。 (遵循 `smart-wait-strategy`, 详见 `.cursor/rules/smart-wait-strategy.mdc`)
*   **可靠的选择器**: 使用稳定、唯一的选择器（如 `data-testid`、`id`、`name` 或组合的 CSS 选择器），避免使用易变的 XPath 或过于依赖 DOM 结构的选择器。
*   **代码风格一致性**: 遵循项目代码风格规范。 (遵循 `code-consistency`, 详见 `.cursor/rules/code-consistency.mdc`)
*   **测试用例独立性**: 每个测试用例应能独立运行，不依赖于其他测试用例的执行顺序或状态。使用 Fixture 来确保测试环境的隔离。
*   **清晰的断言**: 断言应明确且与测试目的相关。断言消息应清晰说明失败原因。
*   **日志标准化**: 添加清晰的日志。 (遵循 `logging-standards`, 详见 `.cursor/rules/logging-standards.mdc`)
*   **异常处理**: Page Object 方法应妥善处理 Playwright 异常。
*   **配置外部化**: URL、凭据等应配置化。 (遵循 `external-configuration`, 详见 `.cursor/rules/external-configuration.mdc`)
*   **资源自动释放**: 浏览器/页面资源由 Fixture 管理。 (遵循 `resource-management`, 详见 `.cursor/rules/resource-management.mdc`)
*   **安全数据处理**: 不硬编码敏感信息。 (遵循 `secure-data-handling`, 详见 `.cursor/rules/secure-data-handling.mdc`)
*   **七层架构设计**: 代码放置在正确目录。 (遵循 `seven-layer-architecture`, 详见 `.cursor/rules/seven-layer-architecture.mdc`)
*   **类型注解强制**: 使用类型提示。 (遵循 `type-annotations`, 详见 `.cursor/rules/type-annotations.mdc`)
*   **版本控制**: 遵循提交规范。 (遵循 `version-control`, 详见 `.cursor/rules/version-control.mdc`)
*   **代码分析优先**: 在创建新的页面对象或测试用例前，检查是否已有类似实现。(遵循 `code-analysis-first`, 详见 `.cursor/rules/code-analysis-first.mdc`)
*   **强制业务代码实现**: 直接编写与业务相关的测试逻辑，不要写示例或通用代码。(遵循 `force-business-implementation`, 详见 `.cursor/rules/force-business-implementation.mdc`)
*   **测试数据分离**: 如果使用了数据驱动，确保测试数据与逻辑分离。(遵循 `test-data-separation`, 详见 `.cursor/rules/test-data-separation.mdc`)
*   **(参考)**: 还可以参考 `API自动化测试开发指南.md` 获取更多关于 `pytest`、Fixtures、配置、日志等通用概念的详细信息。

## 7. 常见问题与调试 (Web UI)

*   **元素找不到 (`playwright._impl._api_types.TimeoutError`)**:
    *   **原因**: 选择器错误、元素尚未加载、元素被遮挡、页面跳转过快。
    *   **调试**:
        *   **Playwright Inspector**: 使用 `PWDEBUG=1 pytest ...` 启动 Inspector 进行调试。
        *   **Trace Viewer**: 运行 `pytest --tracing=on`，打开 `trace.zip` 查看详细过程。
        *   **增加显式等待**: 谨慎使用 `page.wait_for_selector(...)` 或 `locator.wait_for(...)`。
        *   **检查选择器**: 在开发者工具中验证。
*   **元素不可交互 (Element is not visible, stable, enabled)**:
    *   **原因**: 元素被遮挡、禁用、动画中、不在视口内。
    *   **调试**:
        *   **Trace Viewer/Inspector**: 检查元素状态。
        *   **滚动页面**: `locator.scroll_into_view_if_needed()`。
        *   **等待**: 等待动画结束或特定状态。
*   **测试不稳定 (Flaky Tests)**:
    *   **原因**: 等待不足、动态数据、环境问题。
    *   **调试**:
        *   **检查等待**: 确保依赖 Playwright 自动等待。
        *   **Trace Viewer**: 分析时序问题。
        *   **隔离测试**: 单独运行看是否复现。
*   **页面加载问题**:
    *   **原因**: 网络问题、URL错误、加载超时。
    *   **调试**:
        *   **检查URL**: 确认 `page.goto()` URL。
        *   **增加超时**: `page.goto(timeout=...)`。
        *   **等待状态**: `page.wait_for_load_state(...)` (谨慎使用 `networkidle`)。
        *   **Trace Viewer**: 查看网络请求。

**通用调试技巧**:

*   **日志**: 查看 `pytest` 输出和框架日志。
*   **截图/录屏**: Trace Viewer 自动包含。
*   **调试器**: `import pdb; pdb.set_trace()` 或 IDE 调试器。
*   **简化场景**: 剥离出最小复现问题的代码。

---

希望这份经过大幅补充和优化的Web测试开发指南能更好地帮助你和其他测试同学！如果在实践中遇到任何问题，请参考项目文档或与其他团队成员交流。