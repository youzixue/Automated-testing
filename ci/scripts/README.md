# CI/CD 脚本说明 (`ci/scripts/`)

本目录包含用于支持 Jenkins CI/CD 流水线 (`Jenkinsfile`) 的辅助 Python 脚本。这些脚本主要负责测试结果的处理、报告元数据的生成以及通知发送。

## 活动脚本及其作用

以下是当前 Jenkins 流水线中**正在使用**的脚本：

1.  **`write_allure_metadata.py`**
    *   **用途**: 在测试执行完毕后，向 `allure-results` 目录写入 Allure 报告所需的元数据文件。
    *   **生成文件**:
        *   `environment.properties` / `.xml` / `.json`: 记录测试执行的环境信息（如操作系统、Python版本、测试环境APP_ENV等）。
        *   `executor.json`: 记录执行本次构建的 CI 系统信息（如 Jenkins 构建号、构建 URL 等）。
        *   `categories.json`: 定义 Allure 报告中的自定义测试结果分类（如产品缺陷、用例缺陷等）。
    *   **调用时机**: 在 `Jenkinsfile` 的 `post` 阶段，处理 `allure-results` 目录之前被调用。

2.  **`run_and_notify.py`**
    *   **用途**: 作为邮件通知流程的**入口脚本**，在 Jenkins Pipeline 的 `post` 阶段最后执行。
    *   **主要职责**:
        *   从环境变量中读取配置（如邮件服务器信息、收件人、Allure 报告 URL、构建状态等）。
        *   调用 `utils.py` 中的 `get_allure_summary()` 函数，尝试从一个临时生成的 Allure 报告目录中读取 `summary.json` 文件，以获取测试统计数据。
        *   调用 `notify.py` 中的 `send_report_email()` 函数，将收集到的信息传递给它，以完成邮件的组装和发送。
    *   **调用时机**: 在 `Jenkinsfile` 的 `post` 阶段，通常在 Allure 报告生成（或尝试生成）之后执行。

3.  **`notify.py`**
    *   **用途**: 包含发送测试报告**邮件的具体实现逻辑**。
    *   **主要职责**:
        *   接收来自 `run_and_notify.py` 的测试摘要信息和环境变量。
        *   使用这些信息组装邮件标题和 HTML 格式的邮件正文。
        *   调用项目工具层 `src/utils/email_notifier.py` 中的 `EmailNotifier` 类来实际发送邮件。
        *   处理邮件发送过程中的日志记录和异常。
    *   **调用方式**: 被 `run_and_notify.py` 导入并调用。

4.  **`utils.py`**
    *   **用途**: 提供 CI 脚本所需的**通用辅助函数**。
    *   **主要函数**:
        *   `get_allure_summary(report_dir_base)`: 读取指定 Allure 报告目录下的 `widgets/summary.json` 文件，并解析返回包含测试统计数据（如总数、通过、失败、持续时间等）的字典。
    *   **调用方式**: 被 `run_and_notify.py` 导入并调用。

## 可能已过时的脚本

以下脚本在当前的 `Jenkinsfile` 中似乎**未被直接调用**，可能已过时或用于其他已移除的流程：

*   `run_tests.py`: 当前 `Jenkinsfile` 直接在 `docker run` 命令中调用 `pytest`。
*   `generate_report.py`: 其元数据写入功能已被 `write_allure_metadata.py` 替代，报告生成主要由 Allure Jenkins 插件处理，上传逻辑已被移除。
*   `prepare_nginx_dir.sh`: 可能与已移除的 Nginx 部署报告的流程相关。

**建议**: 如果确认这些脚本不再需要，应考虑将其归档或删除，以保持目录整洁。

## 脚本交互流程 (简化)

```mermaid
graph TD
    JenkinsPost["Jenkins Post Stage"] -->|执行| WriteMeta(write_allure_metadata.py);
    WriteMeta --> AllureResults["allure-results/"];
    JenkinsPost -->|Allure插件/手动生成| AllureReport["临时 Allure 报告目录 (含 summary.json)"];
    JenkinsPost -->|执行| RunNotify(run_and_notify.py);
    RunNotify -->|调用| Utils(utils.py)::get_allure_summary;
    Utils -->|读取| AllureReport;
    RunNotify -->|调用| Notify(notify.py)::send_report_email;
    Notify -->|使用| EmailUtil("src.utils.email_notifier.py");
    EmailUtil -->|发送| EmailServer[SMTP 服务器];

    style AllureResults fill:#f9f,stroke:#333,stroke-width:2px
    style AllureReport fill:#ccf,stroke:#333,stroke-width:2px
```

**注意**: `Jenkinsfile` 是整个 CI 流程的编排者，它决定了这些脚本的调用顺序和传递给它们的参数（主要通过环境变量）。
