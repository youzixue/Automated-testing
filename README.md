# 自动化测试框架

本项目为企业级自动化测试框架，集成 Playwright、OCR 验证码识别、Allure 报告等，支持多平台、多环境的高效自动化测试。

## 目录结构概览
本项目遵循清晰的分层和模块化设计，主要目录结构如下：

- **`src/`**: 核心源代码目录，遵循七层架构思想：
    - `core/base/`: **核心抽象层** - 定义通用接口、基类、异常。
    - `web/`, `api/`, `mobile/`, `wechat/`, `security/`: **平台实现层** - 各测试平台具体实现。
    - `utils/`: **工具层** - 通用工具（日志、配置、OCR、签名、邮件等）。
    - (*业务对象层在平台实现层内，如 `src/web/pages/`*)
- **`tests/`**: **测试用例层** - 存放所有自动化测试脚本，按平台划分。
- **`data/`**: **测试数据目录** - 存放参数化所需的测试数据文件 (YAML, JSON等)。
- **`config/`**: **配置目录** - 存放 `settings.yaml` 及各环境配置 (`env/`)。
- **`docs/`**: **文档目录** - 存放项目架构、环境部署、规范等详细文档。
- **`ci/`**: **CI/CD 辅助目录** - 包含 Jenkins Pipeline (`Jenkinsfile`) 及相关脚本 (`ci/scripts/`)。
- **`output/`**: **输出目录** - 存放 Allure 测试结果、报告、日志、截图等运行时生成的文件 (不提交到 Git)。
- **`.cursor/`**: Cursor AI 规则目录。
- `pyproject.toml`: 项目元数据及依赖管理 (Poetry)。
- `poetry.lock`: 锁定项目依赖的具体版本。
- `Dockerfile`: 用于构建测试环境的 Docker 镜像定义。
- `.env.example`, `.env`: 环境变量配置模板和本地配置 (不提交 `.env`)。
- `.gitignore`: 指定 Git 忽略的文件和目录。
- `README.md`: 本项目说明文件。

详细架构说明请参见 `docs/enhanced_architecture.md`。

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

详细的环境搭建步骤（包括 Linux/Docker）请参见 `docs/环境依赖安装&CICD集成.md`。

## 本地运行与调试

1.  **克隆代码**: `git clone <your-repo-url>`
2.  **安装依赖**: 在项目根目录运行 `poetry install`
3.  **配置环境变量**: 复制 `.env.example` 为 `.env` 文件，并根据需要修改其中的配置（如 `APP_ENV`, `TEST_DEFAULT_USERNAME`, `TEST_DEFAULT_PASSWORD`, `TEST_WEB_URL`, `TEST_API_URL` 等）。**请勿将包含敏感信息的 `.env` 文件提交到 Git。**
4.  **运行测试**: 在项目根目录运行 pytest，并将 Allure 结果输出到 `output/allure-results`：
    ```bash
    # 运行所有测试
    poetry run pytest --alluredir=output/allure-results

    # (可选) 仅运行 Web 测试
    # poetry run pytest tests/web --alluredir=output/allure-results

    # (可选) 使用标记运行特定套件 (需在 pyproject.toml 中定义 marker)
    # poetry run pytest -m smoke --alluredir=output/allure-results
    ```
5.  **生成并查看报告**: 使用本地安装的 Allure CLI：
    ```bash
    # 生成 HTML 报告到 output/reports/allure-report
    allure generate output/allure-results --clean -o output/reports/allure-report

    # 在浏览器中打开报告
    allure open output/reports/allure-report
    ```

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
  poetry run pytest --alluredir=/results_out # 在容器内运行测试

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
    "web: web端自动化用例",
    "api: 接口自动化用例",
    "mobile: 移动端自动化用例",
    "smoke: 冒烟测试",
    "regression: 回归测试",
    "slow: 慢速用例"
]
```

## 主要特性

- Playwright 实现跨浏览器 UI 自动化。
- httpx 实现异步/同步 API 测试。
- ddddocr + Pillow 实现验证码识别。
- Allure 生成丰富、交互式的测试报告。
- 基于 `pyproject.toml` 和 Poetry 的标准化依赖管理。
- 使用 `.env` 进行本地环境配置管理，CI 环境使用凭据注入。
- 支持多环境配置加载 (`config/`, `src/utils/config/`)。
- 统一日志管理 (`src/utils/log/`)。
- 智能等待策略和自定义异常处理 (`src/core/base/`, `src/web/` 等)。
- 实现支付兼容的 MD5 签名工具 (`src/utils/signature.py`)。
- 测试数据与测试逻辑分离 (`data/`)。
- 遵循七层架构设计，代码结构清晰。
- 通过 Docker 实现环境一致性与 CI/CD 集成。
- 集成 Jenkins Pipeline 实现自动化构建、测试、报告和通知。

## 参考文档

- `docs/环境依赖安装&CICD集成.md`: 最全面的环境搭建、Docker 使用和 Jenkins 集成指南。
- `docs/enhanced_architecture.md`: 详细的七层架构设计说明。
- `.cursor/rules/`: 项目编码规范和最佳实践规则。
- 各 `src` 和 `tests` 子目录下的 `README.md`: 提供模块的具体说明。

---

欢迎贡献！请遵循项目规范（见 `.cursor/rules/`）。
