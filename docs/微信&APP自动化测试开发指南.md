# 微信 & App 自动化测试开发指南

## 1. 引言

### 1.1 指南目的

本文档旨在为测试人员提供一个清晰、详细的步骤指导，以便在本自动化测试框架内开发**原生 App、微信小程序及微信公众号**的自动化测试用例。遵循本指南将帮助你快速上手，并编写出符合项目规范、高效、稳定和可维护的测试脚本。本文档致力于解释关键的技术概念 (`Airtest`, `PocoUI`) 和设计思想 (如页面对象模式)。**本文档主要基于 `Airtest` 和 `PocoUI` 技术栈。**

### 1.2 目标读者

本指南主要面向负责 App 及微信相关自动化测试开发的**测试工程师**，包括对 Python、移动端自动化有不同程度了解的同学。

### 1.3 基础要求

在开始之前，建议具备以下基础知识：

*   **基本的Python编程知识**: 理解变量、函数、类、数据类型（字典、列表等）。
*   **了解移动应用基础**: 知道什么是原生 App、WebView、小程序、公众号。了解基本的移动端交互（点击、滑动、输入）。
*   **基本的命令行操作**: 了解 `adb` (Android) 或与 iOS 设备交互的基础命令。
*   **了解 UI 自动化概念**: 知道什么是 UI 元素、定位器。

## 2. 项目背景与核心概念

### 2.1 七层架构概览 (遵循 `seven-layer-architecture.mdc`)

本项目采用标准的七层架构设计。App 和微信自动化测试主要涉及以下层级和目录：

*   **测试用例层 (`tests/`)**: (遵循 `platform-specific-testing.mdc`)
    *   `tests/mobile/`: 存放原生 App 测试脚本 (`test_*.py` 文件)。
    *   `tests/wechat/`: 存放微信小程序、公众号测试脚本 (`test_*.py` 文件)。**这是你主要编写代码的地方**。
*   **固件层 (`tests/`)**: (遵循 `test-data-separation.mdc`)
    *   `tests/conftest.py`: 全局共享的测试配置和 **Fixtures** (如日志配置)。
    *   `tests/mobile/conftest.py`: 原生 App 测试专用的 Fixtures (如提供设备连接、`Poco` 实例)。
    *   `tests/wechat/conftest.py`: 微信测试专用的 Fixtures (同上，可能包含微信特定操作如启动小程序)。
*   **业务对象层 (`src/`, `data/`)**: (遵循 `page-object-pattern.mdc`)
    *   `src/mobile/screens/`: **原生 App 的屏幕对象 (Screen Objects)**。封装了特定屏幕的元素定位 (Poco 选择器) 和用户交互操作。
    *   `src/wechat/components/` 或 `src/wechat/screens/`: **微信小程序/公众号的页面或组件对象**。封装 UI 元素和交互。
    *   `data/mobile/`, `data/wechat/`: 存放 App 和微信测试所需的数据文件 (YAML/JSON 格式)，实现**数据驱动**。 (遵循 `test-data-separation.mdc`)
*   **平台实现层 (`src/`)**: (遵循 `platform-specific-testing.mdc`)
    *   `src/mobile/`: **Airtest 和 Poco 的具体实现封装**。例如，设备连接的辅助函数、自定义的复杂手势操作、Poco 扩展功能等。测试人员一般**不需要直接修改**此层，而是通过业务对象层调用。
    *   `src/wechat/`: **微信自动化特定的底层操作封装**。如封装好的搜索并启动小程序/公众号的函数，处理微信特定 UI 变化的逻辑等。
*   **核心抽象层 (`src/`)**: (遵循 `interface-first-principle.mdc`)
    *   `src/core/base/`: 定义框架的基础接口（如 `Device`, `UiElement` 的抽象基类）、自定义**异常** (`src/core/base/errors.py`, 遵循 `specific-exceptions.mdc`) 等。
*   **工具层 (`src/`)**: (遵循 `logging-standards.mdc`, `smart-wait-strategy.mdc`)
    *   `src/utils/`: 提供各种通用工具，如配置加载 (`src/utils/config/manager.py`)、日志记录 (`src/utils/logger.py`)、Airtest/Poco 相关的智能等待 (`src/utils/waits.py`)、数据生成等。

> **重要**: 在开始编码前，请务必花时间阅读 `docs/enhanced_architecture.md` 文档，以深入理解项目架构。 (遵循 `project-documentation-first` 规则)

### 2.2 核心组件与技术点解释

理解以下核心组件和技术点，有助于你更好地进行 App 和微信自动化测试：

*   **`Airtest` (设备交互 & 图像识别专家)**:
    *   **是什么**: 一个跨平台的 UI 自动化测试框架，由网易开发。它包含两部分：基于**图像识别**的核心 (`airtest.core`) 和基于**原生 UI 控件识别**的 `Poco` (下一节详述)。
    *   **主要特性**:
        *   **设备连接与管理**: 提供 `connect_device` 函数连接 Android、iOS、Windows 等设备。
        *   **基础设备交互**: 提供 `touch`, `swipe`, `text`, `keyevent`, `snapshot` 等独立于 UI 框架的基础操作 API。
        *   **图像识别**: 这是 Airtest 的**核心能力之一**。你可以截取目标 UI 元素的图片 (模板 `Template`)，Airtest 会在当前屏幕上寻找该图片并进行操作（如 `touch(Template(...))`）。它对于无法通过控件识别定位的元素（如游戏界面、自定义控件、安全限制区域）非常有用。
        *   **跨平台性**: 一套脚本理论上可以在不同平台上运行（需要适配图像和设备连接）。
        *   **Airtest IDE**: 一个强大的辅助工具，集成了脚本录制、控件查看、图像编辑、设备管理和报告生成。
    *   **在框架中的作用**: 主要负责**连接和管理测试设备**，提供**基础的交互能力** (如点击坐标、输入文本、按键)，以及作为 **Poco 无法定位元素时的补充手段**（图像识别）。

*   **`PocoUI` (UI控件自动化引擎)**:
    *   **是什么**: 一个基于 UI 控件树分析的自动化测试框架，与 Airtest 紧密集成。它支持多种平台和引擎（Android 原生, iOS 原生, Unity3D, Cocos2d-x, WebView 等）。
    *   **核心思想**: 与 Airtest 的图像识别不同，Poco 通过**分析目标应用的 UI 层级结构**（控件树）来定位和操作元素。这使得定位更**精准、稳定**，且不易受 UI 视觉变化（如颜色、字体）的影响。
    *   **主要特性**:
        *   **UI 元素选择器 (Selector)**: 使用类似 URI 的语法 (`poco(...)`)，基于元素的**属性** (如 `name`, `text`, `type`) 和**层级关系** (如 `child`, `parent`, `sibling`, `offspring`) 来定位元素。这种方式通常比 XPath 更高效、更稳定。
        *   **跨引擎支持**: 通过不同的 Poco Driver（如 `AndroidUiautomationPoco`, `IOSPoco`, `UnityPoco`, `StdPoco` for Web/SDK）支持不同类型的应用。
        *   **丰富的交互 API**: 提供 `click()`, `swipe()`, `set_text()`, `long_click()`, `scroll()` 等面向 UI 元素的操作。
        *   **属性获取**: 可以方便地获取元素的各种属性（如 `get_text()`, `attr('visible')`, `get_position()`, `get_size()`）。
        *   **内建智能等待**: 提供 `wait_for_appearance()`, `wait_for_disappearance()`, `wait_for_condition()` 等强大的**隐式等待**机制，极大地提高了脚本的稳定性。 (遵循 `smart-wait-strategy.mdc`)
        *   **自动上下文处理 (大部分情况)**: 在原生和 WebView (若可识别或集成 SDK) 之间切换时，通常**无需手动管理上下文**。
    *   **在框架中的作用**: 是**主要的 UI 元素定位和交互方式**。我们优先使用 Poco 来编写测试脚本，因为它更稳定、更易维护。**仅在 Poco 无法有效定位元素时，才考虑使用 Airtest 的图像识别作为补充**。

*   **`pytest` (测试引擎与指挥官)**:
    *   (与 API 指南中的解释类似) 负责测试发现、执行、断言、提供 Fixtures、参数化、标记等。
    *   **Fixtures 在 App 测试中的应用**: 提供配置好的**设备连接 (`device`)** 和 **Poco 实例 (`poco`)**，管理它们的生命周期（连接和断开）。提供测试数据加载功能。
    *   **参数化**: 用于从 YAML 文件加载数据，实现对不同设备、不同用户、不同场景的测试。

*   **屏幕/组件对象 (Screen/Component Objects, 业务封装者)**:
    *   **是什么**: 位于 `src/mobile/screens/` 或 `src/wechat/components/` 的 Python 类。(遵循 `page-object-pattern.mdc`)
    *   **在框架中的作用**: 它们是**测试用例与底层 UI 操作之间的桥梁**。每个类封装了一个特定的屏幕、页面或可复用组件上的**元素定位逻辑 (Poco 选择器)** 和**用户操作流程** (如登录、搜索、添加到购物车等)。
    *   **为什么重要**:
        *   **提高可维护性**: 当 UI 发生变化时，只需要修改对应的屏幕/组件对象中的定位器或方法，而不需要修改所有使用该元素的测试用例。
        *   **提高可读性**: 测试用例代码更关注业务流程，而非具体的 UI 操作细节 (如 `login_page.perform_login("user", "pass")` 而非 `poco("username").set_text("user"); poco("password").set_text("pass"); poco("login_button").click()`)。
        *   **代码复用**: 封装的操作可以在多个测试用例中复用。
    *   (遵循 `force-business-implementation.mdc`) 应直接实现业务相关的屏幕和操作，避免示例性质的代码。
    *   **配置访问**: 屏幕对象应通过 `__init__` 方法接收所需的配置项，而不是全局导入配置模块，以提高可测试性和解耦。

*   **YAML/JSON (数据食谱)**:
    *   (与 API 指南中的解释类似) 用于在 `data/` 目录下存储测试数据（如登录凭证、搜索关键词、预期结果），在 `config/` 目录下存储配置信息。

*   **Allure (报告展示艺术家)**:
    *   (与 API 指南中的解释类似) 与 `pytest` 集成，生成详细的 HTML 测试报告，可以附加截图和日志。

*   **数据驱动 (测试设计思想)**:
    *   (与 API 指南中的解释类似) 通过 YAML 文件和 `pytest` 参数化实现，用多组数据测试相同的屏幕操作或业务流程。

*   **自定义异常 (错误信号灯)**:
    *   (与 API 指南中的解释类似) 在 `src/core/base/errors.py` 中定义特定于 UI 自动化的异常（如 `ElementNotFoundError`, `WechatLaunchError`），使错误处理更精确。(遵循 `specific-exceptions.mdc`)

### 2.3 主要挑战总结

在对 App、微信小程序及公众号进行自动化测试时，可能会遇到以下常见挑战：

1.  **App 内 WebView 元素的定位挑战:**
    *   **问题:** 当目标 App 的 WebView 未开启调试模式时，Poco (以及其他依赖控件树分析的工具) 无法直接检查和定位 WebView 内的 H5 元素。标准的原生定位器只能看到 WebView 容器本身。
    *   **影响:** 自动化脚本无法与 WebView 内容进行可靠的交互。
    *   **应对策略 (本框架推荐):** 优先使用 Poco 识别 WebView 容器周边的原生控件进行操作；对于 WebView 内部交互，主要依赖 Airtest 的图像识别，或者尝试基于坐标的操作（稳定性较差）。与开发团队沟通开启调试模式是根本解决方案。

2.  **微信小程序交互挑战:**
    *   **问题:**
        *   **启动流程复杂:** 需要模拟用户在微信中搜索、点击搜索结果等一系列操作才能进入目标小程序。
        *   **原生控件交互困难:** 进入小程序后，其自定义渲染的控件可能无法被 Poco 稳定识别为标准原生控件，导致点击、输入等操作失败。
        *   **内嵌 H5 操作:** 小程序中可能内嵌 H5 页面，需要结合 Poco 对原生控件的识别和对 H5 内容的可能识别（或图像识别）进行操作。
    *   **影响:** 测试脚本编写复杂，对控件的定位和交互稳定性要求高。
    *   **应对策略 (本框架推荐):** 封装可重用的启动小程序函数；优先使用 Poco 基于文本 (`text`) 或其他可见属性进行定位；对于无法识别的控件，采用 Airtest 图像识别；对于 H5 内容，尝试 Poco 定位或图像识别。

3.  **微信公众号交互挑战:**
    *   **问题:**
        *   **启动流程复杂:** 与小程序类似，需要通过搜索进入。
        *   **原生 UI 树不稳定:** 进入公众号（本质是 WebView）后，微信本身的原生控件（如顶栏、底栏）的 UI 树可能加载不稳定或发生变化，影响基于控件树的 Poco 定位。
        *   **传统等待失效:** UI 树的不稳定导致基于 `wait_for_appearance` 等待原生控件的方法效率降低或失效。
        *   **H5 交互:** 核心内容是 H5，需要与 H5 元素进行交互。
    *   **影响:** 定位微信原生控件困难，测试脚本稳定性受影响，需要更鲁棒的等待和定位策略。
    *   **应对策略 (本框架推荐):** 封装启动函数；尽量减少对微信原生控件的依赖，操作重心放在公众号的 H5 内容上；使用 Poco 定位 H5 内容（优先文本、name、tag），或使用 Airtest 图像识别；对于等待，结合 Poco 对 H5 元素的等待和 Airtest 对图像的等待。

## 3. 环境准备

### 3.1 安装项目依赖

确保你已经按照项目 `README.md` 或 `docs/enhanced_architecture.md` 中的说明设置好了 Python 环境 (>=3.11)。然后，在项目根目录下执行以下命令安装所有依赖 (包括 `airtest`, `pocoui` 及其相关驱动):

```bash
poetry install
```
(遵循 `environment-setup` 规则)

### 3.2 设备连接与配置

*   **Android**:
    *   确保已安装 Android SDK 并配置好 `adb`。
    *   在设备上开启 **USB 调试** 模式 (通常在"开发者选项"中)。
    *   连接设备到电脑，并授权 USB 调试。
    *   可以通过 `adb devices` 命令检查设备是否成功连接。
    *   Airtest 会自动查找连接的设备，也可以在 `connect_device` 时指定设备序列号 `Android://127.0.0.1:5037/YOUR_SERIAL_NO`。
*   **iOS**:
    *   需要 **macOS** 环境和 **Xcode**。
    *   **安装依赖**: 确保安装了 `tidevice` (`pip install -U tidevice`)。
    *   **WebDriverAgent (WDA)**: 这是连接和控制 iOS 设备的关键组件。
        *   你需要使用 Xcode 打开 Poco 提供的 `ios-tagent` 项目（通常在 Poco 库或其依赖中可以找到，或从 GitHub 获取）。
        *   配置好你的开发者账号和签名证书。
        *   选择你的测试设备，在 Xcode 中编译并运行 (Build & Run) WDA 到设备上。首次运行成功后，WDA 会在设备后台保持运行。
        *   需要确保 WDA 服务在设备上正常运行，可以通过 `tidevice wdaproxy -B <WDA_BUNDLE_ID> -p 8100` (端口可自定义) 启动代理来连接。
    *   **设备连接**: 确保设备通过 USB 连接到 Mac，并已信任该电脑。
    *   **Poco 初始化**: 使用 `IosUiautomationPoco(device=device)` 进行初始化。`device` 对象由 Airtest 的 `connect_device("iOS:///127.0.0.1:8100")` (端口需与 `wdaproxy` 启动的端口一致) 提供。
    *   **权限弹窗**: iOS 经常弹出权限请求（定位、通知、相机等）。测试脚本需要能识别并处理这些弹窗，通常可以使用 Poco 基于文本定位 "允许" 或 "好" 按钮，或者使用 Airtest 图像识别。建议在测试开始前手动处理一次常见权限。
*   **Airtest IDE (推荐)**: Airtest IDE 提供了一个图形化界面来管理设备连接，可以简化这个过程，特别是 WDA 的启动和代理配置。

### 3.3 (可选) Poco SDK 集成

如果需要对 App 内的 WebView 或游戏引擎（Unity3D, Cocos）进行更深入的控件识别，建议按 Poco 官方文档指引集成相应的 SDK。

*   **Web/H5:** 通过 `npm` 安装 `pocomon`。
*   **Unity3D/Cocos:** 集成对应的 Poco SDK Unity/Cocos 包。

对于无法集成 SDK 的目标（如无源码的 App、微信小程序/公众号），主要依赖 Poco 对标准原生控件的识别能力以及 Airtest 的图像识别。

## 4. 编写第一个App测试（逐步指南）

假设我们要测试一个简单的登录场景：

*   **屏幕**: 登录屏幕 (Login Screen)
*   **操作**: 输入用户名、输入密码、点击登录按钮。
*   **预期结果**: 成功登录后跳转到主屏幕 (Home Screen)，并显示欢迎信息。

### 步骤 1: (推荐) 使用 Airtest IDE 探索 UI

在编写代码前，强烈建议使用 **Airtest IDE** 连接你的测试设备，并打开目标 App：

1.  **查看 Poco UI 树**: 在 IDE 的 Poco 辅助窗格中，可以实时查看当前界面的 UI 控件层级结构。
2.  **获取元素属性**: 点击 UI 树中的节点，可以查看其详细属性（如 `name`, `text`, `label`, `type`, `resource-id` 等）。**这是编写 Poco 选择器的重要依据**。
3.  **生成选择器**: IDE 通常可以自动生成选中元素的 Poco 选择器代码。
4.  **尝试交互**: 可以直接在 IDE 中尝试点击、输入等操作，验证选择器和交互是否有效。
5.  **截取图像**: 对于 Poco 难以定位的元素，可以在 IDE 中方便地截取图像供 Airtest 使用。

### 步骤 2: 定义屏幕对象 (Screen Object)

根据 UI 探索结果，在 `src/mobile/screens/` 目录下创建或修改屏幕对象文件，例如 `login_screen.py` 和 `home_screen.py`。

**示例 `src/mobile/screens/login_screen.py`**: (遵循 `page-object-pattern.mdc`)

```python
# src/mobile/screens/login_screen.py
import logging
from poco.proxy import UIObjectProxy # 用于类型注解
from typing import Dict, Any # 导入类型

class LoginScreen:
    """封装登录屏幕的元素和操作"""

    def __init__(self, poco: UIObjectProxy, config: Dict[str, Any]): # 接收 Poco 实例和配置
        self.poco = poco
        self.config = config # 保存配置以备后用
        self.logger = logging.getLogger(self.__class__.__name__)

        # --- 元素定位器 (Poco Selectors) ---
        # 推荐使用项目统一的定位策略 (见 7. 最佳实践)
        # 示例: 优先使用 ID 或 name
        self.username_field = self.poco(name="com.example.app:id/username_input") # Android resource-id
        # self.username_field = self.poco("usernameTextField") # iOS name/label
        self.password_field = self.poco(name="com.example.app:id/password_input")
        # self.password_field = self.poco("passwordSecureTextField")
        self.login_button = self.poco(text="登录", type="Button") # 如果文本固定且类型明确
        # self.login_button = self.poco("loginButtonId") # iOS name/label

    def is_displayed(self, timeout=10) -> bool:
        """检查登录屏幕是否加载完成（通过关键元素判断）"""
        try:
            # 使用配置中的超时时间，如果存在的话
            actual_timeout = self.config.get('timeouts', {}).get('element_wait', timeout)
            self.login_button.wait_for_appearance(timeout=actual_timeout)
            self.logger.info("登录屏幕已显示")
            return True
        except Exception: # PocoNoSuchNodeException 或 PocoTargetTimeout
            self.logger.warning("登录屏幕未在预期时间内显示")
            return False

    def enter_username(self, username: str):
        """输入用户名"""
        self.logger.info(f"输入用户名: {username}")
        self.username_field.set_text(username)

    def enter_password(self, password: str):
        """输入密码"""
        self.logger.info("输入密码: ***") # 避免记录真实密码
        self.password_field.set_text(password)

    def click_login_button(self):
        """点击登录按钮"""
        self.logger.info("点击登录按钮")
        self.login_button.click()

    def perform_login(self, username: str, password: str):
        """执行完整的登录操作"""
        self.logger.info(f"执行登录流程，用户: {username}")
        if not self.is_displayed():
            raise RuntimeError("登录屏幕未加载，无法执行登录") # 或自定义异常
        self.enter_username(username)
        self.enter_password(password)
        self.click_login_button()
        # 注意：登录操作后，通常会跳转到新屏幕
        # 这个方法不返回 HomeScreen 实例，由测试用例负责后续的屏幕对象切换和验证
```

**示例 `src/mobile/screens/home_screen.py`**: (遵循 `page-object-pattern.mdc`)

```python
# src/mobile/screens/home_screen.py
import logging
from poco.proxy import UIObjectProxy
from typing import Dict, Any

class HomeScreen:
    """封装主屏幕的元素和操作"""

    def __init__(self, poco: UIObjectProxy, config: Dict[str, Any]):
        self.poco = poco
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)

        # --- 元素定位器 ---
        # 假设登录成功后会显示包含用户名的欢迎信息
        self.welcome_message = self.poco(name="welcome_message_label") # 假设 name 或 id
        # self.logout_button = self.poco("logoutButton")

    def is_displayed(self, timeout=15) -> bool:
        """检查主屏幕是否加载完成"""
        try:
            actual_timeout = self.config.get('timeouts', {}).get('page_load', timeout)
            self.welcome_message.wait_for_appearance(timeout=actual_timeout)
            self.logger.info("主屏幕已显示")
            return True
        except Exception:
            self.logger.warning("主屏幕未在预期时间内显示")
            return False

    def get_welcome_message(self) -> str:
        """获取欢迎信息文本"""
        if self.welcome_message.exists():
            text = self.welcome_message.get_text() # 或 attr('label') for iOS
            self.logger.info(f"获取到欢迎信息: {text}")
            return text
else:
            self.logger.warning("欢迎信息元素不存在")
            return ""

    # ... 其他主屏幕操作，如点击菜单、退出登录等 ...
```

**要点**: (与第 2.2 节呼应)
*   屏幕对象封装了 **Poco 选择器** 和 **交互逻辑**。
*   方法名应体现**业务含义**。
*   `__init__` 接收 **Poco 实例** 和 **config 字典** (体现**依赖注入**)。
*   使用 `wait_for_appearance` 等待元素加载，确保稳定性。
*   日志记录关键操作。 (遵循 `logging-standards.mdc`)

### 步骤 3: 准备测试数据 (YAML Data)

如果需要，在 `data/mobile/` 或 `data/common/` 目录下创建数据文件，例如 `login_data.yaml`。

```yaml
# data/mobile/login_data.yaml

successful_login:
  username: "testuser"
  password: "password123"
  expected_welcome_prefix: "欢迎"

invalid_login:
  username: "testuser"
  password: "wrongpassword"
  expected_error_message: "用户名或密码错误"
```

### 步骤 4: 编写测试用例 (Pytest Tests)

在 `tests/mobile/` 目录下创建测试文件，例如 `test_login.py`。

*   **确保 `conftest.py` (`tests/mobile/conftest.py`) 中有 Fixtures**:
    *   提供设备连接和 `Poco` 实例 (`poco`)。
    *   提供全局配置 (`config`)。
    *   (可选) 提供加载 `login_data.yaml` 的 fixture (`login_test_data`)。

**示例 `test_login.py`**: (遵循 `test-data-separation.mdc`)

```python
# tests/mobile/test_login.py
import pytest
import logging
from poco.proxy import UIObjectProxy # 用于类型注解
from typing import Dict, Any # 导入类型

# 导入屏幕对象
from src.mobile.screens.login_screen import LoginScreen
from src.mobile.screens.home_screen import HomeScreen
# 导入可能的自定义异常
# from src.core.base.errors import LoginError

# ---- 测试用例 ----

@pytest.mark.mobile
@pytest.mark.smoke
def test_successful_login(poco: UIObjectProxy, config: Dict[str, Any], login_test_data: dict):
    """
    测试有效的用户名和密码成功登录。
    使用 poco Fixture 和 config Fixture。
    使用 login_test_data Fixture 获取数据。
    """
    test_data = login_test_data.get('successful_login')
    if not test_data: pytest.fail("测试数据 'successful_login' 未找到")

    username = test_data['username']
    password = test_data['password']
    expected_prefix = test_data['expected_welcome_prefix']

    logging.info(f"测试场景: 成功登录 (用户: {username})" )

    # 1. 初始化登录屏幕对象, 传入 poco 和 config
    login_page = LoginScreen(poco, config)

    # 2. 执行登录操作
    try:
        login_page.perform_login(username, password)
    except Exception as e:
        # 这里可以考虑截图
        pytest.fail(f"执行登录操作时发生意外错误: {e}", pytrace=True)

    # 3. 初始化主屏幕对象, 传入 poco 和 config
    home_page = HomeScreen(poco, config)

    # 4. 断言: 检查是否成功跳转到主屏幕并显示欢迎信息
    assert home_page.is_displayed(timeout=20), "登录后未跳转到主屏幕或主屏幕加载超时"

    welcome_msg = home_page.get_welcome_message()
    assert welcome_msg.startswith(expected_prefix), \
           f"主屏幕欢迎信息 '{welcome_msg}' 不符合预期前缀 '{expected_prefix}'"
    # 可以进一步断言欢迎信息包含用户名等
    # assert username in welcome_msg

    logging.info("测试通过: 成功登录并验证主屏幕信息")

# @pytest.mark.mobile
# @pytest.mark.negative
# def test_invalid_login(poco: UIObjectProxy, config: Dict[str, Any], login_test_data: dict):
#     """
#     测试无效的用户名或密码登录失败。
#     预期停留在登录页并显示错误信息。
#     """
#     test_data = login_test_data.get('invalid_login')
#     if not test_data: pytest.fail("测试数据 'invalid_login' 未找到")
#
#     username = test_data['username']
#     password = test_data['password']
#     expected_error = test_data['expected_error_message']
#
#     logging.info(f"测试场景: 无效登录 (用户: {username})" )
#
#     login_page = LoginScreen(poco, config)
#
#     try:
#         login_page.perform_login(username, password)
#     except Exception as e:
#         pytest.fail(f"执行无效登录操作时发生意外错误: {e}", pytrace=True)
#
#     # 断言: 应该仍然停留在登录页
#     assert login_page.is_displayed(timeout=5), "无效登录后未停留在登录屏幕"
#
#     # 断言: 检查错误提示信息 (需要 LoginScreen 中定义 error_message 元素)
#     # error_msg = login_page.get_error_message()
#     # assert error_msg == expected_error, f"错误提示 '{error_msg}' 与预期 '{expected_error}' 不符"
#
#     logging.info("测试通过: 无效登录按预期失败")
```

**要点**: (与第 2.2 节呼应)
*   测试用例通过**屏幕对象**进行交互，代码更清晰。
*   利用 **Fixtures** (`poco`, `config`, `login_test_data`) 获取依赖和数据。
*   屏幕对象通过 `__init__` 接收 `poco` 和 `config`。
*   使用 `assert` 对屏幕状态和关键元素内容进行验证。
*   (可选) 使用 `pytest.raises` 验证预期的失败场景（如登录失败抛出异常）。
*   (可选) 使用 `@pytest.mark.parametrize` 实现**数据驱动**。

## 5. 处理特定挑战 (微信小程序/公众号)

这部分详细内容已在第 2.3 节 (`主要挑战总结`) 中阐述。核心思路是：

*   **封装启动逻辑**: 将复杂的微信内搜索、启动过程封装到 `src/wechat/utils/navigation.py` 或 `tests/wechat/conftest.py` 中的可重用函数或 Fixture。**示例见下方 5.1 节**。
*   **优先 Poco 定位**: 尽可能使用 Poco 基于文本、name 或层级关系定位微信内部的控件或 H5 元素。
*   **Airtest 图像识别补充**: 对于 Poco 无法识别的控件（特别是小程序自定义组件）或不稳定区域，使用 Airtest 图像识别作为备选。
*   **健壮的等待**: 结合 Poco 的元素等待 (`wait_for_appearance`) 和 Airtest 的图像等待 (`wait(Template(...))`) 处理异步加载和 UI 不稳定。
*   **减少对易变原生控件的依赖**: 尤其是在公众号场景，尽量操作 H5 内容，避免依赖微信自身可能变化的顶栏/底栏原生控件。

### 5.1 微信启动工具函数示例

以下是一个简化版的启动微信小程序/公众号的工具函数示例，可以放在 `src/wechat/utils/navigation.py` 中：

```python
# src/wechat/utils/navigation.py
import time
from airtest.core.api import stop_app, start_app, text, touch, wait, exists, snapshot
from airtest.core.error import TargetNotFoundError
from poco.proxy import UIObjectProxy
from typing import Dict, Any

from src.utils.log.manager import get_logger

logger = get_logger(__name__)

# 假设已定义搜索图标、搜索框、小程序/公众号结果的 Template 或 Poco 选择器
# 例如：
SEARCH_ICON_TPL = Template(r"data/wechat/images/search_icon.png")
SEARCH_INPUT_POCO = "搜索" # Poco(text="搜索") 或更精确的选择器
OFFICIAL_ACCOUNT_ENTRY_TPL = Template(r"data/wechat/images/official_account_entry.png") # 公众号入口标识
MINI_PROGRAM_ENTRY_TPL = Template(r"data/wechat/images/mini_program_entry.png") # 小程序入口标识

def launch_target_in_wechat(device, poco: UIObjectProxy, config: Dict[str, Any], target_name: str, target_type: str):
    """
    封装启动微信并导航到指定小程序或公众号的逻辑。

    Args:
        device: Airtest 设备对象.
        poco: Poco 实例.
        config: 项目配置字典.
        target_name: 目标小程序或公众号的名称.
        target_type: '小程序' 或 '公众号'.
    """
    wechat_package_name = config.get('app', {}).get('wechat', {}).get('package_name', 'com.tencent.mm')
    timeout = config.get('airtest', {}).get('timeouts', {}).get('default', 20)

    logger.info(f"开始启动微信并导航至 {target_type}: '{target_name}'...")
    try:
        logger.info(f"停止微信 {wechat_package_name} 以确保初始状态...")
        stop_app(wechat_package_name)
        time.sleep(2)
        logger.info(f"启动微信 {wechat_package_name}...")
        start_app(wechat_package_name)
        time.sleep(5) # 等待微信完全加载

        # 1. 点击搜索图标 (使用 Airtest 图像识别更稳定)
        logger.debug("等待并点击微信主界面的搜索图标...")
        wait(SEARCH_ICON_TPL, timeout=timeout * 1.5) # 微信启动可能慢，给更长超时
        touch(SEARCH_ICON_TPL)

        # 2. 输入目标名称 (Poco 输入可能更可靠)
        logger.debug(f"等待搜索框并输入 '{target_name}'...")
        search_input = poco(SEARCH_INPUT_POCO) # 假设可以通过文本"搜索"定位
        search_input.wait_for_appearance(timeout=timeout)
        # search_input.click() # 有时需要先点击才能输入
        text(target_name) # 使用 Airtest 的 text 输入
        time.sleep(1) # 等待搜索结果刷新

        # 3. 点击目标入口
        logger.debug(f"查找并点击 {target_type} '{target_name}' 的入口...")
        target_entry_tpl = MINI_PROGRAM_ENTRY_TPL if target_type == "小程序" else OFFICIAL_ACCOUNT_ENTRY_TPL
        
        # 尝试使用 Poco 基于文本定位入口，如果失败则回退到图像识别
        try:
            target_poco = poco(text=target_name) # 尝试直接通过名字定位
            if target_poco.exists():
                 target_poco.click()
                 logger.info(f"已通过 Poco 点击 '{target_name}' 入口。")
            else:
                 logger.warning(f"Poco 未直接找到文本为 '{target_name}' 的入口，尝试图像识别...")
                 wait(target_entry_tpl, timeout=timeout)
                 touch(target_entry_tpl)
                 logger.info(f"已通过 Airtest 图像识别点击 '{target_name}' 入口。")
        except Exception as poco_click_err:
            logger.warning(f"Poco 点击 '{target_name}' 入口失败: {poco_click_err}，尝试图像识别...")
            wait(target_entry_tpl, timeout=timeout)
            touch(target_entry_tpl)
            logger.info(f"已通过 Airtest 图像识别点击 '{target_name}' 入口。")

        logger.info(f"导航到 {target_type}: '{target_name}' 的操作已完成。")
        time.sleep(3) # 等待目标加载

    except TargetNotFoundError as tnf:
        error_msg = f"启动或导航至 {target_type} '{target_name}' 失败：未找到预期元素/图像: {tnf}"
        logger.error(error_msg)
        snapshot(filename=f"error_launch_{target_type}_{target_name}.png")
        raise RuntimeError(error_msg) from tnf
    except Exception as e:
        error_msg = f"启动或导航至 {target_type} '{target_name}' 时发生意外错误: {e}"
        logger.error(error_msg, exc_info=True)
        snapshot(filename=f"error_launch_{target_type}_{target_name}.png")
        raise RuntimeError(error_msg) from e

# 这个函数可以在 tests/wechat/conftest.py 的 fixture 中被调用和预配置
```
**注意**: 上述示例代码中的选择器 (`SEARCH_INPUT_POCO`) 和图像模板 (`SEARCH_ICON_TPL` 等) 需要根据你的实际情况进行调整和创建。

## 6. 执行测试与查看报告

(与 API 指南中的解释类似)

### 6.1 执行测试

使用 `pytest` 命令：

*   **执行所有测试**: `poetry run pytest` ( **注意**: 见下方关于并行执行的说明)
*   **仅执行移动 App 测试**: `poetry run pytest -m mobile`
*   **仅执行微信测试**: `poetry run pytest -m wechat`
*   **执行特定文件**: `poetry run pytest tests/mobile/test_login.py`
*   **生成 Allure 报告数据**: `poetry run pytest --alluredir=output/allure-results`
*   **并行执行**: `poetry run pytest -n <workers>` (例如 `-n 2` 同时跑两个测试。**重要**: 见下文)

**重要注意事项：关于 App 和 WeChat 测试的并行执行**

*   **问题描述**: 尝试使用 `pytest -n auto` 或 `pytest -n X` (X > 1) 同时并行执行多个 App (Mobile) 或 WeChat 测试用例**通常会导致测试冲突和失败**。
*   **根本原因**: 这些测试通常需要与**单个物理设备**或**同一个微信应用实例**进行交互。当多个测试并行运行时，它们会争抢设备控制权或干扰彼此的应用状态（例如，一个测试正在尝试登录，而另一个测试可能正在导航到其他页面或执行清理操作），导致不可预测的行为和断言失败。
*   **`xdist_group` 的局限性**: 虽然 `pytest-xdist` 提供了 `@pytest.mark.xdist_group` 标记试图将特定测试绑定到同一 worker，但在 `-n auto` 或 worker 数量较多的情况下，并**不能保证**这些测试被严格地、完全串行地执行。调度复杂性可能导致分组约束失效或不同 worker 处理同一分组的不同测试，依然引发冲突。
*   **最佳实践**: 为了确保 App 和 WeChat 测试的稳定性和可靠性，**强烈建议使用 `-n 1` 参数来串行执行这些测试**：
    *   执行 App 测试: `poetry run pytest -n 1 tests/mobile/`
    *   执行 WeChat 测试: `poetry run pytest -n 1 tests/wechat/`
*   **混合并行策略**: 如果你需要同时运行 Web/API 测试（可以并行）和 App/WeChat 测试（需要串行），请**不要**依赖单一的 `pytest -n auto` 命令和复杂的 `conftest.py` 钩子。**最佳实践是采用多阶段执行**，例如使用脚本：
    1.  先用 `pytest -n auto tests/web/ tests/api/` 执行 Web/API 测试。
    2.  再用 `pytest -n 1 tests/mobile/ --allure-no-capture` 执行 App 测试。
    3.  最后用 `pytest -n 1 tests/wechat/ --allure-no-capture` 执行 WeChat 测试。
    (详细脚本示例请参考相关讨论或项目中的 `run_tests.sh` 示例)
*   **提高 App/WeChat 测试效率**: 如果你需要提高 App 或 WeChat 测试的整体执行效率，唯一的可靠方法是**使用多台物理设备并行执行测试集**。例如，你可以将一部分测试用例分配给设备 A，另一部分分配给设备 B。关键在于，**在每一台设备上，测试用例仍需使用 `-n 1` 串行执行**，以避免单台设备上的状态冲突。这通常需要更复杂的测试分发和设备管理机制，可能需要借助 CI/CD 平台或专门的设备管理平台来实现。

### 6.2 查看 Allure 报告

1.  确保已安装 Allure 命令行工具。
2.  执行 `poetry run pytest --alluredir=output/allure-results`。
3.  运行 `allure generate output/allure-results --clean -o output/reports/allure-report`。
4.  运行 `allure open output/reports/allure-report`。

## 7. 遵循的最佳实践与项目规范

在开发 App 和微信自动化测试时，请务必牢记并遵守以下项目规范 (`.cursor/rules/` 目录) 和通用最佳实践：

*   **代码分析优先 (`code-analysis-first`)**: 检查是否已有类似屏幕对象或操作。
*   **代码风格一致性 (`code-consistency`)**: 使用 Black, Pylint, MyPy。
*   **强制业务代码实现 (`force-business-implementation`)**: 屏幕对象应反映真实业务。
*   **接口先行原则 (`interface-first-principle`)**: 复杂屏幕或可复用组件可考虑抽象接口。
*   **日志标准化 (`logging-standards`)**: 在屏幕对象和测试用例中记录关键信息。
*   **页面对象模式 (`page-object-pattern`)**: **核心实践**，必须遵循。
*   **平台特定标准 (`platform-specific-testing`)**: 将代码放在正确的平台目录下 (`mobile`, `wechat`)。
*   **项目文档优先 (`project-documentation-first`)**: 阅读本文档和架构文档。
*   **资源管理 (`resource-management`)**: Fixture 负责设备连接和 Poco 实例生命周期。
*   **安全数据处理 (`secure-data-handling`)**: 不硬编码密码等敏感信息。
*   **七层架构设计 (`seven-layer-architecture`)**: 代码放置在正确目录。
*   **智能等待策略 (`smart-wait-strategy`)**: **核心实践**，使用 Poco 等待，禁止 `time.sleep()`。
*   **异常专一性 (`specific-exceptions`)**: 定义和使用有意义的自定义异常。
*   **测试数据分离 (`test-data-separation`)**: 使用 `data/` 和参数化。
*   **类型注解强制 (`type-annotations`)**: 使用类型提示。
*   **版本控制 (`version-control`)**: 遵循提交规范。

*   **Poco 选择器最佳实践**:
    *   **优先级**: 
        1.  **唯一且稳定的标识符**: `name` (Android 的 resource-id, iOS 的 name/identifier/label) 是首选。
        2.  **固定且唯一的文本**: `text` 或 `label`。适用于按钮、标签等。
        3.  **组合属性**: 例如 `poco(text="确定", type="Button")` 增加唯一性。
        4.  **层级关系 (谨慎使用)**: `child()`, `parent()`, `sibling()`, `offspring()`。UI 结构变化容易导致失效。优先使用相对稳定的父节点结合子节点属性。
    *   **使用 `nameMatches`**: 对于部分动态变化的 ID 或文本，可以使用正则表达式进行匹配，例如 `poco(nameMatches=".*button_confirm_\\d+")`。
    *   **利用 Airtest IDE**: 充分利用 IDE 探索 UI 树，尝试不同的选择器组合。

*   **Airtest 图像模板管理**:
    *   **命名规范**: 图像文件名应清晰表达其所属页面/组件和代表的元素，例如 `login_screen_username_icon.png` 或 `wechat_search_result_mini_program.png`。
    *   **组织结构**: 在 `data/<platform>/images/` 目录下，按屏幕或功能模块创建子目录来组织图像文件，例如 `data/mobile/images/login/`, `data/wechat/images/search/`。
    *   **图像质量与区域**: 截取的图像应清晰、具有辨识度，尽量只包含目标元素的核心特征，避免包含过多易变的背景。
    *   **分辨率与设备差异**: Airtest 对分辨率有一定容忍度，但如果目标设备分辨率差异过大或 UI 风格不同，可能需要为特定设备准备单独的图像。优先尝试调整识别阈值 (`threshold`)。
    *   **更新机制**: 当 UI 发生变化导致图像识别失败时，需要及时更新对应的图像模板。建议在提交代码时检查相关图像是否需要同步更新。

*   **(可选) 高级特性参考**:
    *   **Poco `freeze()` 和 `thaw()`**: 在 UI 快速变化或需要操作特定瞬间状态的复杂场景下，可以使用 `freeze()` 冻结当前 UI 树进行分析和操作，完成后使用 `thaw()` 解冻。
    *   **Airtest 断言**: Airtest 提供了 `assert_exists(v)`, `assert_not_exists(v)`, `assert_equal(first, second)`, `assert_not_equal(first, second)` 等断言函数，可以在脚本中直接使用，尤其适合基于图像的断言。
    *   **复杂手势**: 除了 `swipe`，Airtest 还支持更复杂的手势如 `pinch` (缩放)。

## 8. 问题排查 (Troubleshooting)

(与之前文档内容类似，保持详细)

*   **测试失败且行为混乱 (尤其在并行运行时):**
    *   **症状**: App 或 WeChat 测试在单独运行时通过，但在使用 `pytest -n auto` 或 `pytest -n X` (X>1) 并行运行时，出现随机失败、状态相互干扰（如一个测试登录时另一个在退出）、断言失败、设备无响应等不可预测行为。
    *   **原因**: 这是因为多个测试用例试图同时控制**同一个物理设备**或**同一个微信应用实例**。`pytest-xdist` 的并行机制（即使结合 `@pytest.mark.xdist_group`）在 `-n auto` 或 worker 数量较多时，无法保证对共享物理资源的严格串行访问，导致冲突。
    *   **解决方案**: **不要**尝试通过复杂的 `conftest.py` 钩子解决此问题。**必须串行执行 App 和 WeChat 测试**。
        *   使用 `pytest -n 1 tests/mobile/` 执行 App 测试。
        *   使用 `pytest -n 1 tests/wechat/` 执行 WeChat 测试。
        *   对于混合执行场景（如 Web/API 并行 + App/WeChat 串行），请使用**多阶段脚本**（参见第 6.1 节）。
        *   **提高效率**: 如果你需要加速 App/WeChat 测试，不能依赖在单台设备上并行运行。正确的方法是**增加物理测试设备**，并将测试负载分散到多台设备上。在每台设备上，测试仍然必须使用 `-n 1` 串行执行。
*   **元素找不到 (Poco):**
    *   在 Airtest IDE 中检查 Poco UI 树，确认元素层级和属性。
    *   选择器是否准确？尝试不同的属性组合或相对定位（参考选择器最佳实践）。
    *   元素是否已加载？使用 `wait_for_appearance()`。
    *   是否在屏幕可见区域内？Poco 通常需要元素可见才能交互。使用 Poco 的 `scroll_to_find` 或 Airtest `swipe` 滚动。
    *   是否是自定义控件导致 Poco 无法识别？尝试 Airtest 图像识别。
    *   **iOS 特定**: 检查 `name`, `label`, `value` 等属性是否准确。
*   **Airtest 图像识别失败:**
    *   截图是否清晰、具有代表性？（参考图像管理策略）
    *   识别阈值 (`threshold`) 是否合适？尝试调整（0.7 到 0.9 之间常见）。
    *   屏幕分辨率或 UI 样式是否变化？
    *   是否有动画干扰？尝试等待动画结束或截取更稳定的区域。
*   **点击无效:**
    *   Poco: 元素是否可见、可点击 (`enabled`)？是否有遮挡？尝试 `poco_element.click([relative_x, relative_y])` 指定点击位置。
    *   Airtest: `touch` 的坐标是否准确？
*   **微信操作失败:**
    *   检查微信版本。
    *   检查控件 ID/文本是否因微信更新失效。优先使用文本或 `nameMatches`。
    *   确保前置条件满足（如已登录微信）。
    *   增加等待时间 (`timeout`) 或使用更精确的等待条件。
    *   Poco 识别微信 UI 可能不如原生 App 精确，需要更多耐心调试选择器或结合 Airtest。
*   **iOS 连接或 WDA 问题**:
    *   确认 WDA 服务是否在设备上正常运行 (`tidevice wdaproxy` 是否成功启动并连接)。
    *   Xcode Build WDA 是否成功？签名证书是否有效？
    *   设备是否已信任 Mac？
    *   尝试重启设备和 Mac。
    *   检查 `connect_device` 中的端口号是否与 `wdaproxy` 启动的端口一致。
*   **安全限制导致无法截图或定位元素:**
    *   **问题:** 某些高度安全的界面（如银行 App 的密码输入、微信支付页面等）可能同时禁止截屏**并且**阻止自动化工具获取其内部的 UI 元素结构（表现为 Poco UI 树为空或不完整）。
    *   **影响:** 基于元素定位的断言和基于图像的断言都无法执行。
    *   **应对策略:**
        *   **Android:** 在这种情况下，检查当前的 **Activity 名称** 可能是唯一可行的断言方式，用于判断是否已成功跳转到预期的安全页面。使用 `dev.get_top_activity_name()` 获取当前前台 Activity 的名称，并与预期值进行比较。
        *   **iOS:** iOS 没有 Activity 概念，也没有直接获取当前 View Controller 类名的简单标准 API。替代策略包括：
            *   **检查特定元素存在性:** 断言某个预期在该安全页面上唯一且可被 Poco 识别的元素 (`name`, `label` 等) 是否存在。
            *   **检查导航栏标题:** 如果导航栏及其标题可访问，检查标题文本是否符合预期。
            *   (如果适用) 依赖 Airtest 图像识别页面上的非敏感、固定区域。

---
*本文档遵循项目自动化测试框架规范编写，主要基于 Airtest 和 PocoUI 技术栈。*