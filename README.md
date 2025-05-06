# 自动化测试框架

本项目为企业级自动化测试框架，集成 Playwright、Airtest/PocoUI、httpx、OCR 验证码识别和 Allure 报告等，支持 Web、API、原生移动应用和微信小程序/公众号的多平台、多环境自动化测试。

## 项目架构与目录结构

本项目严格遵循七层架构设计，确保代码结构清晰、高度可维护：

- **`src/`**: 核心源代码目录，按七层架构划分：
    - `core/base/`: **核心抽象层** - 定义通用接口、基类、异常，是框架的基础。
    - `web/`, `api/`, `mobile/`, `wechat/`: **平台实现层** - 各测试平台具体实现和适配。
    - `utils/`: **工具层** - 通用工具（日志、配置、OCR、签名、智能等待、邮件等）。
    - `common/`: **通用组件** - 跨平台共享的功能组件和工具类。
    - *业务对象层封装在平台实现层内：*
        - `src/web/pages/`: Web 页面对象。
        - `src/api/services/`: API 服务对象。
        - `src/mobile/screens/`: 移动应用屏幕对象。
        - `src/wechat/screens/` / `src/wechat/components/`: 微信页面/组件对象。
- **`tests/`**: **测试用例层** - 存放按平台和功能划分的自动化测试脚本。
    - `tests/web/`: Web UI 测试用例。
    - `tests/api/`: API 接口测试用例。
    - `tests/mobile/`: 原生移动应用测试用例。
    - `tests/wechat/`: 微信小程序/公众号测试用例。
- **`data/`**: **测试数据目录** - 存放参数化所需的测试数据文件 (YAML, JSON等)。
- **`config/`**: **配置目录** - 存放 `settings.yaml` 及各环境配置 (`env/`)。
- **`docs/`**: **文档目录** - 存放项目架构、环境部署、规范等详细文档。
- **`ci/`**: **CI/CD 辅助目录** - 包含 Jenkins Pipeline (`Jenkinsfile`) 及相关脚本。
- **`output/`**: **输出目录** - 存放生成的报告、日志、截图等临时文件 (不提交到 Git)。
- **`.cursor/`**: Cursor AI 规则目录，包含项目代码规范和最佳实践。
- `pyproject.toml`: 项目元数据及依赖管理 (Poetry)。
- `Dockerfile`: 测试环境的 Docker 镜像定义。
- `.env.example`, `.env`: 环境变量配置模板和本地配置 (不提交 `.env`)。

详细架构说明请参见 `docs/enhanced_architecture.md`。移动与微信测试指南请参见 `docs/微信&APP自动化测试开发指南.md`。

## 技术栈与核心组件

- **测试框架**: [pytest](https://docs.pytest.org/) - 强大的 Python 测试框架，支持参数化、Fixtures、插件扩展等。
- **多平台适配**:
    - **Web UI 测试**: [Playwright](https://playwright.dev/python/) - 现代跨浏览器自动化工具，支持 Chromium, Firefox, WebKit。
    - **API 测试**: [httpx](https://www.python-httpx.org/) - 现代化的 HTTP 客户端，支持同步/异步请求。
    - **移动应用测试**: [Airtest](https://airtest.netease.com/) + [PocoUI](https://poco.readthedocs.io/) - 跨平台 UI 自动化引擎，支持 Android/iOS 通过控件树和图像识别进行定位和交互。
    - **微信小程序/公众号测试**: Airtest/PocoUI - 支持原生控件和 WebView 的混合测试。
- **测试报告**: [Allure](https://docs.qameta.io/allure/) - 生成丰富、交互式的测试报告，包含截图、日志、测试步骤等。
- **OCR 识别**: [ddddocr](https://github.com/sml2h3/ddddocr) + [Pillow](https://pillow.readthedocs.io/) - 用于验证码识别。
- **依赖管理**: [Poetry](https://python-poetry.org/) - 现代化 Python 依赖和包管理工具。
- **容器化**: [Docker](https://www.docker.com/) - 确保环境一致性和 CI/CD 集成。
- **CI/CD**: Jenkins Pipeline - 自动化构建、测试、报告和通知。

## 环境准备

1.  **Python**: 需要 Python 3.11 或更高版本。
2.  **Git**: 用于代码版本控制。
3.  **Poetry**: 用于项目依赖管理。
    ```bash
    # 安装 Poetry (如果未安装)
    pip install poetry
    # 配置国内源加速 (可选)
    poetry config repositories.aliyun https://mirrors.aliyun.com/pypi/simple/
    poetry config repositories.tuna https://pypi.tuna.tsinghua.edu.cn/simple
    ```
4.  **Allure CLI**: 用于本地生成和查看 Allure HTML 报告。CI 环境的 Docker 镜像中已包含。
    ```bash
    # 本地安装 Allure CLI (参考官方文档，方法多样)
    # 例如：npm install -g allure-commandline 或下载解压
    allure --version # 验证安装
    ```
5.  **Playwright 浏览器**: 项目依赖安装后需要安装浏览器驱动。
    ```bash
    # 在项目根目录运行
    poetry install # 安装项目依赖
    poetry run playwright install # 安装默认浏览器驱动
    # 或 poetry run playwright install chromium firefox webkit
    ```
6.  **移动测试环境 (Airtest/PocoUI)**:
    - **Android**: 确保已安装 Android SDK 并配置好 `adb`。设备开启 USB 调试模式并授权。
    - **iOS**: 需要 macOS 环境、Xcode 和 WebDriverAgent 配置，详见 `docs/微信&APP自动化测试开发指南.md`。
    - **macOS 用户特别说明**: 由于 airtest 和 pocoui 包在 macOS 上可能尝试安装 pywin32 导致失败，项目已将这些依赖放入单独的分组。安装依赖时请使用:
      ```bash
      # 先安装除 airtest-group 外的所有依赖
      poetry install --without airtest-group
      # 然后根据需要手动安装 airtest 和 pocoui
      pip install airtest pocoui
      ```

详细的环境搭建步骤请参见 `docs/环境依赖安装&CICD集成.md`。

## 本地运行与调试

1.  **克隆代码**: `git clone <your-repo-url>`
2.  **安装依赖**: 在项目根目录运行 `poetry install`
3.  **配置环境变量**: 复制 `.env.example` 为 `.env` 文件，并根据需要修改其中的配置（如 `APP_ENV`, `TEST_DEFAULT_USERNAME`, `TEST_DEFAULT_PASSWORD`, `TEST_WEB_URL`, `TEST_API_URL` 等）。**请勿将包含敏感信息的 `.env` 文件提交到 Git。**
4.  **运行测试**: 在项目根目录运行 pytest，并将 Allure 结果输出到 `output/allure-results`：
    ```bash
    # 运行所有测试 (不推荐，特别是包含移动和微信测试时)
    poetry run pytest --alluredir=output/allure-results

    # Web 测试 (支持并行)
    poetry run pytest tests/web -n auto --alluredir=output/allure-results

    # API 测试 (支持并行)
    poetry run pytest tests/api -n auto --alluredir=output/allure-results
    
    # 移动应用测试 (严格串行执行，防止设备冲突)
    poetry run pytest tests/mobile -n 1 --alluredir=output/allure-results
    
    # 微信测试 (严格串行执行，防止设备冲突)
    poetry run pytest tests/wechat -n 1 --alluredir=output/allure-results

    # 使用标记运行特定套件
    poetry run pytest -m smoke --alluredir=output/allure-results
    
    # 指定测试环境
    APP_ENV=prod poetry run pytest tests/api -n auto --alluredir=output/allure-results
    ```
    
    **重要提示**: 移动和微信测试必须使用 `-n 1` 确保串行执行，否则会因多测试同时控制设备而导致冲突和失败。
    
5.  **生成并查看报告**: 使用本地安装的 Allure CLI：
    ```bash
    # 生成 HTML 报告到 output/reports/allure-report
    allure generate output/allure-results --clean -o output/reports/allure-report

    # 在浏览器中打开报告
    allure open output/reports/allure-report
    ```

## 多环境配置

本项目支持多环境配置管理，遵循以下配置加载和覆盖顺序：

1. **基础配置**: `config/settings.yaml` 中定义的默认值。
2. **环境特定配置**: 根据 `APP_ENV` 环境变量加载 `config/env/{env}.yaml`。
   - 当前支持的环境: `test`（测试环境，默认）和 `prod`（生产环境）。
3. **环境变量覆盖**: 特定形式的环境变量可以覆盖配置文件中的任何值，例如 `WEB_BASE_URL` 环境变量会覆盖配置中的 `web.base_url` 值。
4. **本地开发配置**: 如果存在 `config/local.yaml`，它将覆盖前面的所有配置（该文件不应提交到 Git）。

通过命令行指定环境：
```bash
# 使用生产环境配置运行测试
APP_ENV=prod poetry run pytest tests/api

# 使用测试环境配置运行测试（默认）
APP_ENV=test poetry run pytest tests/web
# 或省略环境变量（默认为 test）
poetry run pytest tests/web
```

在 CI/CD 中，通过 Jenkins 参数或环境变量设置 `APP_ENV` 来确定测试环境。敏感信息（如账号、密码、API 密钥等）通过 Jenkins 凭据（在 `withCredentials` 块中）安全注入，而不是硬编码在配置文件中。

配置项使用规范：
```python
# 在代码中使用配置项（示例）
from src.utils.config.manager import get_config

# 获取配置
config = get_config(env='prod')  # 或从环境变量获取 env=os.getenv('APP_ENV', 'test')

# 访问配置项
web_base_url = config.get('web', {}).get('base_url', 'http://default-url.com')
timeout = config.get('web', {}).get('timeouts', {}).get('default', 10)
```

有关更详细的配置管理说明，请参见 `docs/enhanced_architecture.md` 中的相关章节。

## Docker 使用

本项目提供 `Dockerfile` 用于构建包含所有依赖（Python, Poetry, Playwright 浏览器, Allure CLI 等）的测试环境镜像，推荐用于 CI/CD 和需要隔离环境的场景。

### 构建镜像

```bash
# 确保 allure-2.27.0.zip (或对应版本) 在项目根目录
docker build -t automated-testing:dev .
```
**注意**: Dockerfile 设计为从本地复制 Allure CLI 安装包进行安装，以应对网络问题。请在 `.gitignore` 中忽略 `allure-*.zip`。

### 本地开发 (使用 Docker 环境)

如果你希望在本地编码，但使用 Docker 容器作为运行时环境（例如确保与 CI 环境一致），可以挂载本地代码目录：

```bash
docker run --rm \
  -e APP_ENV=test \ # 设置必要的环境变量
  -e TEST_DEFAULT_USERNAME="your_test_user" \
  -e TEST_DEFAULT_PASSWORD="your_test_password" \
  -e TEST_WEB_URL="http://host.docker.internal:8080" \ # 示例: 访问宿主机服务
  -v $(pwd):/workspace:rw \ # 将本地项目目录挂载到容器 /workspace
  -v $(pwd)/output/allure-results:/results_out:rw \ # 挂载结果输出目录
  --workdir /workspace \ # 设置工作目录
  automated-testing:dev \ # 使用你构建的镜像
  poetry run pytest tests/web -n auto --alluredir=/results_out # 在容器内运行测试

# 测试完成后，可在本地使用 Allure CLI 生成和查看报告
# allure generate output/allure-results --clean -o output/reports/allure-report
# allure open output/reports/allure-report
```
*   `-v $(pwd):/workspace:rw`: 将当前宿主机目录（你的项目代码）挂载到容器的 `/workspace` 目录，实现代码修改后无需重建镜像即可运行。
*   `-v $(pwd)/output/allure-results:/results_out:rw`: 将 Allure 结果直接输出到宿主机的 `output/allure-results` 目录。

### CI/CD 集成 (Jenkins)

本项目使用 Jenkins 进行 CI/CD 编排，详细流程定义在项目根目录的 `Jenkinsfile` 中。核心流程如下：

1.  Jenkins Agent 检出最新代码。
2.  Jenkins 使用 Docker (通常是 Docker-outside-of-Docker 模式) 运行测试：
    *   启动基于 `automated-testing:dev` 镜像的容器。
    *   通过卷挂载将**宿主机**上的工作区路径 (`HOST_WORKSPACE_PATH`) 和结果路径 (`HOST_ALLURE_RESULTS_PATH`) 映射到容器内。
    *   在容器内执行 `poetry run pytest --alluredir=<挂载的结果路径>`。
    *   所有环境变量和敏感信息通过 Jenkins Credentials 注入。
3.  测试完成后，在 `post` 阶段执行：
    *   **写入元数据**: 在 Docker 容器内运行 `ci/scripts/write_allure_metadata.py` 脚本，向结果目录写入环境、执行者等信息。
    *   **权限修正**: 在 Docker 容器内修正结果目录权限，以便 Allure 插件读取。
    *   **Allure Jenkins 插件**: Jenkins 调用插件处理结果目录，生成并展示报告在 Jenkins UI 中（这是查看报告的主要方式）。
    *   **生成临时报告 (用于邮件)**: 在 Docker 容器内运行 `allure generate`，将报告输出到宿主机的临时目录 (`HOST_ALLURE_REPORT_PATH`)。
    *   **发送邮件通知**: 在 Docker 容器内运行 `ci/scripts/run_and_notify.py`，读取临时报告中的 `summary.json` 获取统计信息，并使用 Jenkins 注入的邮件凭据发送通知邮件。
    *   **清理**: 清理宿主机上的临时报告目录和 Jenkins Agent 工作区。

**要点**: CI 流程依赖 Docker 镜像中包含的 Allure CLI 来生成临时报告以支持邮件通知。

详细的 Jenkins 配置、凭据设置和 `Jenkinsfile` 解析，请参考 `docs/环境依赖安装&CICD集成.md`。

## Allure 测试报告

- **本地查看**: 使用 `allure generate` 和 `allure open` 命令（见上方本地运行部分）。
- **CI 环境**: 主要通过 **Allure Jenkins 插件** 在 Jenkins 构建页面查看交互式报告和历史趋势。
- **报告内容**: 包含测试结果、步骤、截图（如果失败）、环境信息、执行者信息、自定义分类等。
- **丰富的分析功能**:
  - **测试趋势**: 历史测试通过率和失败率变化趋势图。
  - **失败分析**: 根据 Allure 自动关联的失败原因分类。
  - **环境矩阵**: 不同环境和浏览器下的测试结果对比。
  - **挂件 (Widgets)**: 包括汇总、分类、严重性、持续时间分布等多种数据可视化。
- **自定义分类**: 使用 `@allure.feature`, `@allure.story`, `@allure.severity` 等注解组织测试用例，便于分析。
- **自动截图与日志**: 失败时自动截图附加到报告，使用 `allure.step()` 记录测试步骤。

关于 Allure 报告的完整使用指南，请参见各平台的测试开发指南文档。

## pytest 配置

本项目使用 `pyproject.toml` 文件中的 `[tool.pytest.ini_options]` 部分统一管理 pytest 配置，包括测试路径、命名约定、PYTHONPATH 设置、默认参数、日志级别和自定义标记 (markers)。这种方式确保了在不同环境下（本地、Docker、CI）测试行为的一致性，并简化了配置管理。

```toml
# pyproject.toml (部分)
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
pythonpath = ["."] # 确保 src 包可以被导入
addopts = "-ra --tb=short --strict-markers" # 常用选项
log_cli = true
log_cli_level = "INFO"
markers = [
    "web: web端自动化测试",
    "api: 接口自动化测试", 
    "mobile: 移动端自动化测试",
    "wechat: 微信小程序or公众号测试",
    "smoke: 冒烟测试",
    "regression: 回归测试",
    "slow: 慢速用例",
    "negative: 异常场景测试",
]
```

## 主要特性

- **多平台支持**:
  - Playwright 实现跨浏览器 Web UI 自动化，支持 Chromium, Firefox, WebKit。
  - httpx 实现异步/同步 API 测试，支持复杂请求和自定义签名验证。
  - Airtest/PocoUI 实现移动应用和微信小程序/公众号测试，结合控件树分析和图像识别实现稳定定位。

- **智能化测试**:
  - 内置智能等待策略，提高测试稳定性，避免使用固定等待。
  - ddddocr + Pillow 实现验证码识别，提高登录等场景的自动化程度。
  - 自定义异常处理机制，提供更精确的错误定位和诊断。

- **架构与设计**:
  - 严格遵循七层架构设计，代码结构清晰，易于维护和扩展。
  - 页面对象模式 (POM) 封装 UI 元素和交互操作，提高代码复用和维护性。
  - 业务驱动和数据驱动结合，支持参数化测试和多环境配置。

- **集成与工具**:
  - Allure 生成丰富、交互式的测试报告，支持测试步骤、截图、日志等。
  - 基于 Poetry 的标准化依赖管理，简化环境配置。
  - 多环境配置支持 (`config/settings.yaml`, `config/env/`)，使用环境变量灵活覆盖。
  - 统一的日志管理和级别控制 (`src/utils/log/`)。
  - 支付兼容的 MD5 签名工具 (`src/utils/signature.py`) 用于 API 签名验证。

- **工程化实践**:
  - 测试数据与测试逻辑分离 (`data/`)，支持 YAML/JSON 格式。
  - Docker 环境一致性与 CI/CD 集成，保证开发、测试和生产环境一致。
  - Jenkins Pipeline 自动化构建、测试、报告生成和邮件通知。
  - 使用 `.env` 进行本地环境配置管理，CI 环境通过凭据注入敏感信息。

## 常见问题

- **Q: 为什么移动和微信测试需要 `-n 1` 参数？**
  - A: 移动和微信测试需要与单个物理设备交互，并行运行会导致设备控制冲突和状态干扰，使测试失败。

- **Q: 如何解决移动/微信测试中的元素定位难题？**
  - A: 优先使用 Poco 选择器基于 UI 控件属性（如 `text`, `name`）定位；对于难以识别的元素，使用 Airtest 图像识别作为补充。详见 `docs/微信&APP自动化测试开发指南.md`。

- **Q: 使用 Docker 时如何访问宿主机上运行的服务？**
  - A: 可以使用 `host.docker.internal` 作为主机名，例如 `http://host.docker.internal:8080`。

- **Q: Jenkins 报告无法显示或数据不正确？**
  - A: 确保 Allure 结果目录权限正确，并正确设置了 `HOST_ALLURE_RESULTS_PATH` 和 `HOST_WORKSPACE_PATH` 变量。

- **Q: 如何实施数据驱动测试？**
  - A: 在 `data/` 目录中创建 YAML/JSON 数据文件，通过 pytest fixtures 加载，结合 `@pytest.mark.parametrize` 实现参数化测试。
  
  **示例代码（数据文件）**:
  ```yaml
  # data/api/user_data.yaml
  valid_users:
    - username: "test_user1"
      password: "valid_pass1"
      expected_status: 200
      
    - username: "test_user2"
      password: "valid_pass2"
      expected_status: 200
      
  invalid_users:
    - username: "bad_user"
      password: "wrong_pass"
      expected_status: 401
      expected_message: "Invalid credentials"
  ```
  
  **示例代码（fixture 加载数据）**:
  ```python
  # tests/conftest.py 或 tests/api/conftest.py
  import yaml
  import pytest
  from pathlib import Path
  
  @pytest.fixture
  def user_test_data():
      """加载用户测试数据"""
      data_path = Path(__file__).parent.parent / "data" / "api" / "user_data.yaml"
      with open(data_path, "r", encoding="utf-8") as file:
          return yaml.safe_load(file)
  ```
  
  **示例代码（参数化测试）**:
  ```python
  # tests/api/test_user_login.py
  import pytest
  import allure
  
  @allure.feature("用户管理")
  @allure.story("用户登录")
  @pytest.mark.api
  @pytest.mark.parametrize("user_index", [0, 1])
  def test_valid_login(api_client, user_test_data, user_index):
      """测试有效用户登录成功"""
      # 从测试数据中获取特定用户
      user = user_test_data["valid_users"][user_index]
      
      # 执行 API 调用
      response = api_client.post(
          "/api/login",
          json={"username": user["username"], "password": user["password"]}
      )
      
      # 断言
      assert response.status_code == user["expected_status"]
      
  @allure.feature("用户管理")
  @allure.story("用户登录")
  @pytest.mark.api
  @pytest.mark.negative
  def test_invalid_login(api_client, user_test_data):
      """测试无效用户登录失败"""
      # 获取失败测试数据
      user = user_test_data["invalid_users"][0]
      
      # 执行 API 调用
      response = api_client.post(
          "/api/login",
          json={"username": user["username"], "password": user["password"]}
      )
      
      # 断言
      assert response.status_code == user["expected_status"]
      assert user["expected_message"] in response.json().get("message", "")
  ```

## 参考文档

- `docs/环境依赖安装&CICD集成.md`: 最全面的环境搭建、Docker 使用和 Jenkins 集成指南。
- `docs/enhanced_architecture.md`: 详细的七层架构设计说明。
- `docs/Web自动化测试开发指南.md`: Web UI 测试的专项指南，包含 Playwright 的最佳实践。
- `docs/API自动化测试开发指南.md`: API 接口测试的专项指南，包含 httpx 的最佳实践。
- `docs/微信&APP自动化测试开发指南.md`: 移动应用和微信测试的专项指南，包含 Airtest/PocoUI 的最佳实践。
- `.cursor/rules/`: 项目编码规范和最佳实践规则。
- 各 `src` 和 `tests` 子目录下的 `README.md`: 提供模块的具体说明。

---

欢迎贡献！请遵循项目规范（见 `.cursor/rules/`）。
