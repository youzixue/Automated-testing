# 自动化测试环境依赖与CI/CD集成操作手册

## 目录（TOC）
- [目录结构与分层说明](#目录结构与分层说明)
- [1. 环境选择与准备](#1-环境选择与准备)
- [2. 安装基础依赖](#2-安装基础依赖)
- [3. 克隆项目代码](#3-克隆项目代码)
- [4. 安装项目依赖](#4-安装项目依赖)
- [5. 配置环境变量与测试数据分离](#5-配置环境变量与测试数据分离)
- [6. Playwright浏览器驱动安装](#6-playwright浏览器驱动安装)
- [7. Allure CLI（测试报告工具）](#7-allure-cli测试报告工具)
- [8. 运行自动化测试与报告生成](#8-运行自动化测试与报告生成)
- [9. 测试数据分离与管理](#9-测试数据分离与管理)
- [10. CI/CD集成与敏感信息管理](#10-cicd集成与敏感信息管理)
- [11. Docker环境一键部署与CI/CD集成](#11-docker环境一键部署与cicd集成)
- [12. Docker最佳实践](#12-docker最佳实践)
- [13. 参考与扩展](#13-参考与扩展)
- [14. 主流CI平台Docker集成示例](#14-主流ci平台docker集成示例)
- [15. 常见问题FAQ](#15-常见问题faq)
- [16. 邮件通知集成](#16-邮件通知集成)
- [变更记录](#变更记录)

> **如有环境/流程变更，请同步更新本手册，确保团队成员操作一致。**

## 目录结构与分层说明
本项目严格遵循七层架构设计，目录结构如下：

1. **测试用例层（tests/）**：自动化测试用例，按平台/业务分目录
2. **固件层（tests/conftest.py 等）**：pytest fixtures、全局前置后置、数据工厂
3. **业务对象层（src/web/pages/、src/api/services/、src/mobile/screens/）**：页面对象、服务对象、业务流程封装
4. **平台实现层（src/web/、src/api/、src/mobile/）**：平台相关实现与适配
5. **核心抽象层（src/core/base/）**：接口定义、抽象基类
6. **工具层（src/utils/）**：通用工具、OCR、日志、数据工厂等
7. **外部集成层（pyproject.toml）**：依赖声明与管理

> 详细分层与依赖关系请参见 docs/enhanced_architecture.md

---

## 1. 环境选择与准备
- 支持三种主流部署方式：
  1. 本地直装（适合个人开发/调试）
  2. Poetry虚拟环境（推荐，自动管理依赖）
  3. Docker容器化（推荐团队协作/CI/CD）
- 推荐使用华为云、阿里云、腾讯云等主流云厂商的Linux服务器（CentOS 7/8、Rocky Linux、Ubuntu 20.04+）。
- 建议选择最小化安装，避免多余软件干扰。
- 用Xshell、MobaXterm、FinalShell等工具，或直接用Windows/Linux自带的ssh命令连接服务器。

---

## 2. 安装基础依赖

### 2.1 安装Python 3.11+
- 检查Python版本：
  ```bash
  python3 --version
  ```
- 如未安装，推荐用源码安装或参考云厂商文档。
- 多版本共存建议用pyenv或指定python3.11执行后续命令。
- 激活正确版本：
  ```bash
  alias python=python3.11
  alias pip=pip3.11
  ```

### 2.2 安装Git（推荐用SSH方式拉代码）
- 检查是否已安装：
  ```bash
  git --version
  ```
- 推荐用SSH方式克隆代码，避免频繁输入用户名密码。
- 生成SSH密钥：
  ```bash
  ssh-keygen -t rsa -b 4096 -C "your_email@example.com"
  cat ~/.ssh/id_rsa.pub
  ```
- 将公钥添加到Git服务器个人设置的SSH Key管理页面。

### 2.3 安装Poetry（依赖管理工具）
- 切换pip源为国内镜像（加速下载）：
  ```bash
  mkdir -p ~/.pip
  echo -e "[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple" > ~/.pip/pip.conf
  ```
- 安装Poetry：
  ```bash
  pip install poetry
  ```
- 安装后可用`poetry --version`验证。
- **所有依赖必须通过`poetry add`/`poetry remove`管理，禁止直接修改pyproject.toml。依赖变更后需提交pyproject.toml和poetry.lock，并在PR描述中说明原因。**
- 如有多个Python版本，建议用如下命令指定虚拟环境Python版本：
  ```bash
  poetry env use python3.11
  ```

---

## 3. 克隆项目代码
- 选择存放目录，建议在/opt、~/workspace等目录下操作：
  ```bash
  cd /opt
  git clone git@<git服务器地址>:<group>/<repo>.git
  cd automated-testing
  ```

---

## 4. 安装项目依赖
- **必须在项目根目录下执行**：
  ```bash
  poetry install
  ```
- 安装完成后可用`poetry show`或`pip list`检查依赖包是否完整。
- 进入虚拟环境：
  ```bash
  poetry shell
  ```
- 也可用`poetry run pytest`等命令直接运行。

---

## 5. 配置环境变量与测试数据分离
- 本地开发：
  ```bash
  cp .env.example .env
  vim .env
  ```
  按需修改APP_ENV、WEB_BASE_URL等变量。
- **所有敏感信息全部用.env管理，实际值不得提交代码库。新增环境变量时，必须同步更新.env.example并补充注释说明。**
- **测试数据与测试逻辑分离，所有测试数据建议放在data/目录，结构和命名规范详见data/README.md，推荐YAML/JSON格式。**
- CI环境（Jenkins/GitHub Actions等）：
  - 不要直接用.env，推荐在流水线或"构建参数"中设置环境变量。
  - **强烈建议所有敏感信息和环境特定配置（如Git凭据、测试账号、API密钥、Web/API URL、邮件服务器配置等）都通过CI平台的凭据管理功能注入，避免写入代码、.env文件或镜像。**

---

## 6. Playwright浏览器驱动安装
- 进入虚拟环境并安装：
  ```bash
  poetry shell
  playwright install
  exit
  ```
- 如需安装特定浏览器：
  ```bash
  playwright install chromium
  playwright install firefox
  playwright install webkit
  ```
- 安装后可用`playwright --version`验证。
- 如遇playwright install下载慢，可设置代理或用国内镜像，详见Playwright官方文档。
- 如需无头模式，可在pytest参数中加`--headless`。

---

## 7. Allure CLI（测试报告工具）
- **重要性**: Allure CLI (Command Line Interface) 是生成最终 HTML 报告和本地预览报告的**必备工具**。虽然 Jenkins 流水线主要使用 Allure Jenkins 插件来展示报告，但为了支持邮件通知中的测试统计信息，CI 流程仍然需要在 Docker 容器内部**手动执行 `allure generate`** 来生成一个临时报告以提取 `summary.json`。因此，Allure CLI **必须被安装**：
    1.  **对于本地开发/调试**: 你需要在本地机器上安装 Allure CLI。
    2.  **对于 CI/CD 环境**: Allure CLI **必须包含在项目使用的 Docker 镜像 (`Dockerfile`) 中**。
- 下载与安装 (以 Linux 为例):
    ```bash
    # 方法1：使用.tgz格式
    cd /opt
    wget https://github.com/allure-framework/allure2/releases/download/2.27.0/allure-2.27.0.tgz
    tar -zxvf allure-2.27.0.tgz
    sudo mv allure-2.27.0 /opt/allure
    sudo ln -s /opt/allure/bin/allure /usr/bin/allure

    # 方法2：使用.zip格式（与项目 Dockerfile 一致）
    cd /opt
    wget https://github.com/allure-framework/allure2/releases/download/2.27.0/allure-2.27.0.zip
    unzip allure-2.27.0.zip
    sudo mv allure-2.27.0 /opt/allure
    sudo ln -s /opt/allure/bin/allure /usr/bin/allure

    # 验证安装
    allure --version
    ```
- Allure 依赖 Java 8+，请确保已正确安装并配置 `JAVA_HOME`。
- `output/allure-results` 目录用于存放原始测试结果 JSON 文件，`output/reports/allure-report` (本地) 或 `output/reports/temp-allure-report-for-summary` (CI 临时) 目录用于存放生成的 HTML 报告。`output/` 目录已在 `.gitignore` 中全局忽略。

---

## 8. 运行自动化测试与报告生成
- **本地运行测试** (确保已配置好 .env 或环境变量)：
  ```bash
  # 运行测试并将原始结果输出到 allure-results
  poetry run pytest --alluredir=output/allure-results

  # (可选) 运行指定平台的测试
  # poetry run pytest tests/web --alluredir=output/allure-results
  ```
- 推荐用 `poetry run pytest` 保证依赖环境一致。
- **本地生成 HTML 报告**：
  ```bash
  # 从 allure-results 生成报告到 allure-report 目录
  allure generate output/allure-results -o output/reports/allure-report --clean
  ```
- **本地预览报告**：
  ```bash
  # 在浏览器中打开本地报告
  allure open output/reports/allure-report
  ```
- output 目录下的 allure-results、allure-report、logs、screenshots、coverage-data 等均为临时/生成文件，已在 `.gitignore` 中全局忽略。

---

## 9. 测试数据分离与管理
- 所有测试数据应存放于data/目录，按业务/平台分子目录，推荐YAML/JSON格式。
- data/README.md中需说明各数据文件用途和字段含义。
- 新增/调整数据结构时，务必补充data/README.md。
- 测试数据与测试逻辑分离，便于维护和参数化。

---

## 10. CI/CD集成与敏感信息管理
- 所有代码变更必须通过CI/CD流程验证，确保代码质量和自动化测试执行。
- 推荐使用 Jenkins，参考项目根目录的 `Jenkinsfile`。
- CI 环境必须用 poetry 安装依赖，使用缓存加速。
- 测试环境与开发环境保持一致，Python 版本 3.11+。
- **强烈建议所有敏感信息和环境特定配置（如 Git 凭据、测试账号、API 密钥、Web/API URL、邮件服务器配置等）都通过 CI 平台的凭据管理功能注入，避免写入代码、.env 文件或镜像。**
- 当前 CI 流程主要依赖 `ci/scripts/` 目录下的以下脚本：
    - `write_allure_metadata.py`: 写入报告元数据。
    - `run_and_notify.py`: 邮件通知入口，调用 `utils.py` 获取摘要，调用 `notify.py` 发送邮件。
    - `notify.py`: 邮件发送具体实现。
    - `utils.py`: 提供辅助函数，如 `get_allure_summary`。
- 参考 Jenkinsfile 示例，了解如何通过 `withCredentials` 块安全地使用这些凭据。

---

## 11. Docker环境一键部署与CI/CD集成
- 推荐主机或CI流水线先拉取代码，再用Docker构建和运行测试环境。
- 不建议在Dockerfile中直接git clone代码，便于版本可控和CI集成。
- **推荐的Dockerfile写法（项目根目录，用于构建环境镜像）：**
  ```dockerfile
  # 使用官方Python 3.11 Slim镜像
  FROM python:3.11.9-slim

  # 设置容器内工作目录
  WORKDIR /app

  # 先只复制依赖声明文件，利用缓存加速依赖安装
  COPY pyproject.toml poetry.lock /app/

  # 配置国内APT源加速系统依赖安装 (以清华为例)
  RUN rm -rf /etc/apt/sources.list.d/* && \
      echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
      echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
      echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
      apt-get clean && \
      apt-get update && apt-get install -y --no-install-recommends apt-transport-https ca-certificates && \
      apt-get update

  # 安装 Playwright 浏览器依赖和常用工具 (openjdk用于Allure, unzip解压Allure)
  RUN apt-get install -y --no-install-recommends \
      wget openjdk-17-jre-headless unzip \
      libglib2.0-0 libnss3 libnspr4 \
      libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libexpat1 \
      libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 \
      libxcb1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 \
      fonts-liberation libappindicator3-1 lsb-release \
      && apt-get clean && rm -rf /var/lib/apt/lists/*

  # 配置pip和Poetry国内源 (以阿里云和清华为例，提供兜底)
  RUN mkdir -p /root/.pip && \
      echo "[global]" > /root/.pip/pip.conf && \
      echo "index-url = https://mirrors.aliyun.com/pypi/simple/" >> /root/.pip/pip.conf
  RUN pip install --upgrade pip \
      && pip install "poetry>=1.5.0"
  RUN poetry config repositories.aliyun https://mirrors.aliyun.com/pypi/simple/ \
      && poetry config repositories.tuna https://pypi.tuna.tsinghua.edu.cn/simple

  # 全局禁用 Poetry 的虚拟环境创建，直接安装到系统Python环境
  ENV POETRY_VIRTUALENVS_CREATE=false
  # 增加 Poetry 网络超时时间
  ENV POETRY_REQUESTS_TIMEOUT=300

  # 安装项目依赖（核心步骤，不安装项目本身，只安装依赖）
  RUN poetry install --no-root

  # playwright浏览器下载加速（可选，使用国内镜像）
  ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright

  # 安装playwright及其浏览器（使用国内源兜底）
  RUN pip install playwright -i https://mirrors.aliyun.com/pypi/simple/ \
      || pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple \
      && playwright install

  # 安装Allure CLI (从本地复制zip包) - CI流程需要用它生成临时报告以获取邮件摘要
  COPY allure-2.27.0.zip /tmp/
  RUN unzip /tmp/allure-2.27.0.zip -d /opt/ \
      && ln -s /opt/allure-2.27.0/bin/allure /usr/bin/allure \
      && rm /tmp/allure-2.27.0.zip

  # 注意：这个Dockerfile不包含项目代码(没有COPY . /app)，代码将在运行时挂载
  # 也不包含 CMD 或 ENTRYPOINT，因为命令将在 docker run 时指定
  ```
- **本地构建与运行（使用卷挂载最新代码）：**
  ```bash
  # 1. 拉取/更新最新代码
  # git clone <项目仓库URL> or git pull
  cd automated-testing

  # 2. 构建环境镜像 (如果镜像不存在或Dockerfile/依赖更新)
  # 确保 allure-2.27.0.zip 文件在构建上下文中（项目根目录）
  docker build -t automated-testing:dev . 

  # 3. 运行测试 (挂载代码和Allure结果目录)
  # 确保本地 output/allure-results 目录存在: mkdir -p output/allure-results
  # 注意：$(pwd) 获取的是当前宿主机路径
  docker run --rm \
    -v $(pwd):/workspace:rw \
    -v $(pwd)/output/allure-results:/results_out:rw \
    --workdir /workspace \
    automated-testing:dev \
    poetry run pytest --alluredir=/results_out

  # 4. 本地生成和预览报告 (如果需要)
  allure generate output/allure-results -o output/reports/allure-report --clean
  allure open output/reports/allure-report
  ```
- **CI脚本思路（以Jenkins Pipeline为例，演示卷挂载和当前流程）：**
  ```groovy
  // Jenkinsfile (部分示例 - 重点展示测试和报告处理流程)
  environment {
      // ... 其他环境变量和凭据ID ...
      HOST_JENKINS_HOME_ON_HOST = '/var/lib/docker/volumes/jenkins_home/_data' // !!宿主机Jenkins Home路径!!
      HOST_WORKSPACE_PATH = "${HOST_JENKINS_HOME_ON_HOST}/workspace/${env.JOB_NAME}" // 宿主机工作区路径
      HOST_ALLURE_RESULTS_PATH = "${HOST_WORKSPACE_PATH}/output/allure-results" // 宿主机结果路径
      // HOST_ALLURE_REPORT_PATH 用于临时报告，用于获取 summary.json
      HOST_ALLURE_REPORT_PATH = "${HOST_WORKSPACE_PATH}/output/reports/temp-allure-report-for-summary" // <-- 宿主机临时报告路径
      DOCKER_IMAGE = "automated-testing:dev" // 定义使用的镜像
  }
  stages {
      // ... checkout ...
      stage('准备环境 (Agent)') {
          steps {
              echo "准备测试环境和目录 (在 Agent ${WORKSPACE} 上)..."
              // 确保结果和临时报告目录在 Agent 上存在对应的目录结构
              sh """
              mkdir -p ${WORKSPACE}/output/allure-results
              mkdir -p ${WORKSPACE}/output/reports/temp-allure-report-for-summary/widgets
              echo "清空旧的 allure-results 和 temp report (在 Agent ${WORKSPACE} 上)..."
              rm -rf ${WORKSPACE}/output/allure-results/*
              rm -rf ${WORKSPACE}/output/reports/temp-allure-report-for-summary/*
              """
              echo "环境准备完成。"
          }
      }
      // ... 检查脚本文件 ...
      stage('并行执行测试') {
          steps {
              script {
                  // ... (选择和注入凭据) ...
                  try {
                      // ... (运行 docker run pytest，挂载 HOST_WORKSPACE_PATH 和 HOST_ALLURE_RESULTS_PATH) ...
                  } catch (err) {
                      echo "测试阶段出现错误: ${err}."
                      currentBuild.result = 'UNSTABLE'
                  }
              } // End script
          } // End steps
      } // End stage '并行执行测试'

   } // End stages

   post { // 流水线完成后执行
       always {
           echo "Pipeline 完成. 开始执行报告生成和通知步骤..."
           script {
               def allureReportUrl = "" // 用于存储 Jenkins 插件生成的报告 URL
               def allureStepSuccess = false
               def tempReportGenSuccess = false

               try {
                   // --- 注入邮件等凭据 ---
                   withCredentials([
                       string(credentialsId: env.EMAIL_PASSWORD_CREDENTIALS_ID, variable: 'INJECTED_EMAIL_PASSWORD'),
                       string(credentialsId: env.EMAIL_SMTP_SERVER_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_SMTP_SERVER'),
                       // ... 其他邮件凭据 ...
                   ]) {

                       // --- 1. 写入 Allure 元数据 ---
                       echo "写入 Allure 元数据文件到 ${env.HOST_ALLURE_RESULTS_PATH} (在宿主机上)..."
                       sh """
                       docker run --rm --name write-metadata-${BUILD_NUMBER} \\
                         /* ... env vars ... */ \\
                         -v ${env.HOST_WORKSPACE_PATH}:/workspace:ro \\
                         -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \\
                         ${env.DOCKER_IMAGE} \\
                         python /workspace/ci/scripts/write_allure_metadata.py /results_out
                       """
                       echo "Allure 元数据写入完成。"

                       // --- 2. 修正 allure-results 目录权限 ---
                       echo "修正宿主机目录 ${env.HOST_ALLURE_RESULTS_PATH} 的权限..."
                       sh """
                       docker run --rm --name chown-chmod-results-${BUILD_NUMBER} \\
                         -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_to_fix:rw \\
                         ${env.DOCKER_IMAGE} \\
                         sh -c 'chown -R 1000:1000 /results_to_fix || echo "chown failed"; chmod -R a+r /results_to_fix || echo "chmod failed!"'
                       """
                       echo "权限修正尝试完成。"

                       // --- 3. 使用 Allure Jenkins 插件生成和归档报告 ---
                       echo "使用 Allure Jenkins 插件处理 ${WORKSPACE}/output/allure-results 中的结果..."
                       try {
                           allure([
                               properties: [],
                               reportBuildPolicy: 'ALWAYS',
                               results: [
                                   [path: 'output/allure-results'] // 相对于 WORKSPACE
                               ]
                           ])
                           allureStepSuccess = true
                           allureReportUrl = "${env.BUILD_URL}allure/" // Jenkins 插件报告 URL
                           echo "Allure 插件报告处理完成。报告 URL: ${allureReportUrl}"
                       } catch (allurePluginError) {
                           echo "Allure 插件步骤失败: ${allurePluginError}"
                           allureStepSuccess = false
                           allureReportUrl = "(Allure 插件报告生成失败)"
                       }

                       // --- 4. 手动生成报告到临时目录 (获取 summary.json) ---
                       echo "生成临时报告到 ${env.HOST_ALLURE_REPORT_PATH} 以获取 summary.json..."
                       // 确保宿主机目录存在
                       sh """
                       docker run --rm --name mkdir-temp-report-${BUILD_NUMBER} \\
                         -v ${env.HOST_WORKSPACE_PATH}:/host_workspace:rw \\
                         ${env.DOCKER_IMAGE} \\
                         sh -c 'mkdir -p /host_workspace/output/reports/temp-allure-report-for-summary/widgets'
                       """
                       // 运行 allure generate
                       sh """
                       docker run --rm --name allure-gen-temp-${BUILD_NUMBER} \\
                         -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_in:ro \\
                         -v ${env.HOST_ALLURE_REPORT_PATH}:/report_out:rw \\
                         ${env.DOCKER_IMAGE} \\
                         sh -c 'allure generate /results_in --clean -o /report_out'
                       """
                       // 检查 summary.json 是否成功生成
                       def summaryCheckExitCode = sh script: "docker run --rm -v ${env.HOST_ALLURE_REPORT_PATH}:/report_check:ro ${env.DOCKER_IMAGE} test -f /report_check/widgets/summary.json", returnStatus: true
                       if (summaryCheckExitCode == 0) {
                           tempReportGenSuccess = true
                           echo "summary.json 已成功生成到宿主机路径: ${env.HOST_ALLURE_REPORT_PATH}/widgets/summary.json"
                       } else {
                           tempReportGenSuccess = false
                           echo "[警告] 未能在 ${env.HOST_ALLURE_REPORT_PATH}/widgets/ 中找到 summary.json。"
                       }

                       // --- 5. 发送邮件通知 ---
                       if (params.SEND_EMAIL) {
                           echo "发送邮件通知 (尝试读取 ${env.HOST_ALLURE_REPORT_PATH}/widgets/summary.json)..."
                           sh """
                           docker run --rm --name notify-${BUILD_NUMBER} \\
                             -e CI=true \\
                             -e APP_ENV=${params.APP_ENV} \\
                             -e EMAIL_ENABLED=${params.SEND_EMAIL} \\
                             -e EMAIL_PASSWORD='${INJECTED_EMAIL_PASSWORD}' \\
                             // ... 其他邮件环境变量 ...
                             -e ALLURE_PUBLIC_URL="${allureReportUrl}" \\ // 使用插件生成的 URL
                             -e BUILD_STATUS="${currentBuild.result ?: 'SUCCESS'}" \\
                             // ... 其他构建信息环境变量 ...
                             -v ${env.HOST_WORKSPACE_PATH}:/workspace:ro \\
                             -v ${env.HOST_ALLURE_REPORT_PATH}:/report:ro \\ // 只读挂载临时报告
                             ${env.DOCKER_IMAGE} \\
                             python /workspace/ci/scripts/run_and_notify.py
                           """
                       } else {
                           echo "邮件通知已禁用。"
                       }

                   } // End withCredentials
               } catch (err) {
                   echo "Post-build 阶段出现严重错误: ${err}"
                   // ... 处理错误 ...
               } finally {
                   // --- 6. 设置构建描述 ---
                   // ... (使用 allureReportUrl 设置描述) ...
                   def finalStatus = currentBuild.result ?: 'SUCCESS'
                   def reportLink = allureStepSuccess && allureReportUrl.startsWith("http") ? "<a href='${allureReportUrl}' target='_blank'>查看报告</a>" : allureReportUrl ?: "(报告链接不可用)"
                   currentBuild.description = "${params.APP_ENV.toUpperCase()} 环境 [...] - ${finalStatus} - ${reportLink}"

                   // --- 7. 清理临时报告目录和 Agent 工作区 ---
                   echo "清理临时报告目录 ${env.HOST_ALLURE_REPORT_PATH} (在宿主机上)..."
                   sh """
                   docker run --rm --name cleanup-temp-report-${BUILD_NUMBER} \\
                     -v ${env.HOST_WORKSPACE_PATH}:/host_workspace:rw \\
                     ${env.DOCKER_IMAGE} \\
                     sh -c 'rm -rf /host_workspace/output/reports/temp-allure-report-for-summary'
                   """
                   cleanWs()
                   echo "Agent 工作空间和临时报告目录已清理。"
               } // End finally
           } // End script
       } // End always
       // ... success, failure, unstable blocks ...
   } // End post
} // End pipeline
```
- output目录建议定期清理，节省磁盘空间。

---

## 12. Docker最佳实践

### 12.1 为什么推荐Docker？
- **环境一致性**：Docker镜像中包含了所有依赖、Python版本、工具链，团队每个人/CI/CD环境/生产环境都能100%复现同样的运行环境，彻底避免"在我电脑上没问题"的情况。
- **CI/CD无缝集成**：主流CI平台（GitHub Actions、Jenkins、GitLab CI等）都原生支持Docker，流水线脚本更简洁，环境更可控。
- **依赖冲突和污染风险低**：不会污染本地环境，也不会被本地已有的Python包、系统库影响。
- **易于迁移和扩展**：迁移到新服务器、云平台、甚至本地开发机都极其方便。

### 12.2 Dockerfile版本选择建议
- 推荐写法：`FROM python:3.11-slim`，可自动获得3.11系列的最新小版本（如3.11.9）。
- 如需锁定小版本（如3.11.9），可写为：`FROM python:3.11.9-slim`。
- **为什么这样做？**
  - `python:3.11-slim`保证大版本一致，自动获得安全更新，适合大多数团队和CI/CD场景。
  - `python:3.11.9-slim`适合对小版本有极端严格要求的场景。

### 12.3 output目录挂载与Allure报告目录对接
- **推荐策略**：在 CI/CD 流水线中，将宿主机的工作区目录和 Allure 原始结果目录挂载到测试容器。报告生成现在分为两部分：
    1.  **主要报告 (Jenkins UI)**: Allure Jenkins 插件直接处理挂载的 `allure-results` 目录 (通过 Agent 上的 `${WORKSPACE}/output/allure-results` 路径访问，该路径映射自宿主机的 `HOST_ALLURE_RESULTS_PATH`)。
    2.  **临时报告 (用于邮件摘要)**: 手动在 Docker 容器内运行 `allure generate`，将结果输出到挂载的宿主机临时目录 (`HOST_ALLURE_REPORT_PATH`)，供邮件脚本读取 `summary.json`，之后该临时目录会被清理。
- **示例命令 (Jenkinsfile 风格，使用宿主机路径变量)**：
  ```groovy
  # 1. 运行测试，将结果输出到挂载的 /results_out (映射到 HOST_ALLURE_RESULTS_PATH)
  docker run --rm \
    -v ${env.HOST_WORKSPACE_PATH}:/workspace:rw \
    -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \
    # ... 其他参数 ...
    ${env.DOCKER_IMAGE} \
    poetry run pytest --alluredir=/results_out

  # 2. (在 post 阶段) 生成临时报告，从 /results_in 读取，输出到挂载的 /report_out (映射到 HOST_ALLURE_REPORT_PATH)
  docker run --rm \
    -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_in:ro \
    -v ${env.HOST_ALLURE_REPORT_PATH}:/report_out:rw \
    # ... 其他参数 ...
    ${env.DOCKER_IMAGE} \
    allure generate /results_in -o /report_out --clean

  # 3. (在 post 阶段) 运行通知脚本，挂载临时报告目录以读取摘要
  docker run --rm \
    # ... 其他参数和挂载 ...
    -v ${env.HOST_ALLURE_REPORT_PATH}:/report:ro \ # 只读挂载临时报告
    ${env.DOCKER_IMAGE} \
    python /workspace/ci/scripts/run_and_notify.py

  # 4. (在 post 阶段) 清理临时报告目录
  docker run --rm \
    -v ${env.HOST_WORKSPACE_PATH}:/host_workspace:rw \
    # ... 其他参数 ...
    ${env.DOCKER_IMAGE} \
    sh -c 'rm -rf /host_workspace/output/reports/temp-allure-report-for-summary'
  ```
- **为什么这样做？**
  - 清晰分离代码和原始结果的路径。
  - 利用 Allure Jenkins 插件进行主要的报告展示和历史追踪。
  - 按需生成临时报告以支持邮件通知中的摘要信息，避免不必要的持久化存储。
  - CI/CD 流程更清晰，每一步职责单一。

### 12.4 环境变量传递最佳实践
- 推荐用`-e`参数在docker run时传递非敏感配置（如`APP_ENV`）和通过`withCredentials`注入的敏感信息（如账号、密码、URL等）。
- **避免**使用`--env-file`传递包含敏感信息的文件。
- **为什么这样做？**
  - 保证敏感信息不写进镜像或代码，安全性高，灵活适配多环境。CI 平台凭据管理是最佳实践。

### 12.5 典型docker run命令模板及参数解释 (结合卷挂载 - CI 流程)
- **场景：在 CI/CD 中运行测试**
  ```bash
  docker run --rm \
    -e APP_ENV=<环境> \
    -e WEB_BASE_URL=<URL> \
    -e TEST_DEFAULT_USERNAME=<用户名> \
    -e TEST_DEFAULT_PASSWORD=<密码> \
    -v <宿主机工作区路径>:/workspace:rw \
    -v <宿主机Allure结果路径>:/results_out:rw \
    --workdir /workspace \
    <环境镜像名:标签> \
    poetry run pytest --alluredir=/results_out # <命令>
  ```
- **场景：在 CI/CD Post 阶段生成临时报告 (用于邮件摘要)**
  ```bash
  docker run --rm \
    -v <宿主机Allure结果路径>:/results_in:ro \
    -v <宿主机临时报告路径>:/report_out:rw \
    <环境镜像名:标签> \
    allure generate /results_in -o /report_out --clean # <命令>
  ```
- **场景：在 CI/CD Post 阶段运行通知脚本**
  ```bash
  docker run --rm \
    -e <邮件相关环境变量由Jenkins注入> \
    -e ALLURE_PUBLIC_URL=<Jenkins插件报告URL> \
    -v <宿主机工作区路径>:/workspace:ro \
    -v <宿主机临时报告路径>:/report:ro \
    <环境镜像名:标签> \
    python /workspace/ci/scripts/run_and_notify.py # <命令>
  ```
- **参数说明：**
  - `--rm`：容器运行结束后自动删除。
  - `-e`：传递环境变量 (大量使用 Jenkins 注入的凭据)。
  - `-v <宿主机路径>:<容器路径>:<模式>`：挂载卷。
    - `<宿主机工作区路径>:/workspace:rw`：挂载最新的代码。
    - `<宿主机Allure结果路径>:/results_out:rw` (测试时) 或 `/results_in:ro` (生成报告时)：挂载原始测试结果目录。
    - `<宿主机临时报告路径>:/report_out:rw` (生成报告时) 或 `/report:ro` (通知时)：挂载用于临时存放报告以提取摘要的目录。
  - `--workdir /workspace`：设置容器的工作目录。
  - `<环境镜像名:标签>`：指定包含所有依赖的环境镜像。
  - `<命令>`：在容器内执行的命令。

### 12.6 团队协作和CI/CD流水线下的推荐用法
- 推荐所有团队成员和CI/CD流水线都用同一个Dockerfile和镜像标签，保证环境一致。
- CI平台（如 Jenkins）必须使用凭据机制安全注入敏感变量。
- 主要的报告查看通过 Allure Jenkins 插件进行。

### 12.7 常见问题与解答
- **Q: 没有Dockerfile怎么办？**
  - A: 请在项目根目录新建Dockerfile，内容见本手册第11节。
- **Q: 如何保证本地和CI环境一致？**
  - A: 所有成员和CI都用同一个Dockerfile和镜像，避免本地依赖污染。
- **Q: 环境变量优先级如何？**
  - A: `docker run -e` > 容器内.env文件。CI 中优先使用 `-e` 注入 Jenkins 凭据。
- **Q: Jenkins Allure 报告无法访问或内容不正确？**
  - A: 检查：
    1.  `HOST_ALLURE_RESULTS_PATH` 变量是否正确指向宿主机上的 Allure 结果目录。
    2.  该目录的权限是否允许 Jenkins Agent (或运行 Docker 的用户) 读取。
    3.  Allure Jenkins 插件配置是否正确指向了 Agent 上的结果路径 (`output/allure-results`)。
    4.  `write_allure_metadata.py` 是否成功执行并写入了元数据。
- **Q: Jenkins邮件通知缺少统计信息？**
  - A: 检查：
    1.  `post` 阶段手动运行 `allure generate` 的步骤是否成功执行 (检查 Jenkins 日志)。
    2.  `HOST_ALLURE_REPORT_PATH` 挂载是否正确。
    3.  `summary.json` 是否确实生成在了 `HOST_ALLURE_REPORT_PATH/widgets/` 目录下。
    4.  `run_and_notify.py` 脚本是否正确读取和解析了 `summary.json`。
- **Q: Jenkins环境变量/凭据如何安全注入？**
  - A: 强烈推荐使用 Jenkins 的 "Credentials" 功能，并在 Jenkinsfile 中通过 `withCredentials` 块注入。
- **Q: Playwright/Allure安装慢或报错？**
  - A: 检查 Dockerfile 中是否已配置国内镜像源。网络不稳定时可尝试增加 `POETRY_REQUESTS_TIMEOUT`。
- **Q: Playwright依赖库缺失如何解决？**
  - A: 仔细核对 Dockerfile 中 `apt-get install` 命令是否包含了所有 Playwright 官方文档要求的系统依赖。
- **Q: output目录产物如何归档？**
  - A: 可以归档 `HOST_ALLURE_RESULTS_PATH` 作为原始数据备份。最终报告由 Jenkins 插件管理。
- **Q: 为什么要使用 poetry run pytest 而不是直接 pytest？**
  - A: 确保在 Poetry 管理的环境中运行，避免依赖问题。
- **Q: Docker 拉取镜像或构建时网络超时/无法连接？**
  - A: 核心是解决 Docker daemon 访问仓库的网络问题。首选方案是配置并验证有效的国内镜像加速器。
- **Q: Jenkins流水线在Docker容器(DooD模式)中挂载卷找不到文件/内容不正确？**
  - A: 关键在于区分 Jenkins Agent 容器内的路径 (`${WORKSPACE}`) 和宿主机上的真实路径。必须在 Jenkinsfile 的 `docker run` 命令中使用 `-v` 挂载宿主机上的路径。

---

## 13. 参考与扩展
- [Allure官方文档](https://docs.qameta.io/allure/)
- [Playwright官方文档](https://playwright.dev/python/)
- [Poetry官方文档](https://python-poetry.org/docs/)
- 团队内部Wiki/知识库（如有），持续收集最佳实践与常见问题，便于团队协作和持续改进。

---

## 14. 主流CI平台Docker集成示例

本节详细说明如何在 Jenkins 中集成 Docker 自动化测试，**关键步骤均有解释**，适合团队成员参考。由于本项目当前主要使用 Jenkins 作为 CI/CD 工具，这里仅提供 Jenkins 的集成示例。

### 14.1 Jenkins流水线（Pipeline）集成

**核心思路：** 利用 Jenkins Pipeline 和 Docker 命令，实现拉取代码、构建/拉取环境镜像、在 Docker 容器中运行测试、通过 Allure Jenkins 插件展示报告、手动生成临时报告获取摘要、发送邮件通知的全自动化流程。特别注意在 Docker-outside-of-Docker (DooD) 模式下宿主机路径的正确映射。**所有敏感配置均通过 Jenkins 凭据管理，并动态注入。报告生成和通知步骤移至 `post { always { ... } }` 块。**

**Jenkinsfile关键部分示例 (参考项目根目录的 `Jenkinsfile`，已根据最新流程调整)**

```groovy
pipeline {
    agent any // 或指定特定的agent标签

    parameters { // 定义构建参数
        choice(name: 'APP_ENV', choices: ['test', 'prod'], description: '选择测试环境')
        booleanParam(name: 'RUN_WEB_TESTS', defaultValue: true, description: '运行Web测试')
        // ... 其他测试平台参数 ...
        booleanParam(name: 'SEND_EMAIL', defaultValue: true, description: '是否发送邮件通知')
    }

    environment {
        // --- 凭据 ID (在Jenkins中预先创建) ---
        GIT_CREDENTIALS_ID = 'git-credentials'
        GIT_REPO_URL_CREDENTIAL_ID = 'git-repo-url'
        TEST_ENV_CREDENTIALS_ID = 'test-env-credentials'
        PROD_ENV_CREDENTIALS_ID = 'prod-env-credentials'
        TEST_WEB_URL_CREDENTIAL_ID = 'test-web-url'
        TEST_API_URL_CREDENTIAL_ID = 'test-api-url'
        PROD_WEB_URL_CREDENTIAL_ID = 'prod-web-url'
        PROD_API_URL_CREDENTIAL_ID = 'prod-api-url'
        EMAIL_PASSWORD_CREDENTIALS_ID = 'email-password-credential'
        EMAIL_SMTP_SERVER_CREDENTIAL_ID = 'email-smtp-server'
        EMAIL_SMTP_PORT_CREDENTIAL_ID = 'email-smtp-port'
        EMAIL_SENDER_CREDENTIAL_ID = 'email-sender'
        EMAIL_RECIPIENTS_CREDENTIAL_ID = 'email-recipients'
        EMAIL_USE_SSL_CREDENTIAL_ID = 'email-use-ssl'

        // --- Docker Agent & 宿主机路径映射 (DooD模式关键) ---
        HOST_JENKINS_HOME_ON_HOST = '/var/lib/docker/volumes/jenkins_home/_data' // !!根据实际情况修改!!
        HOST_WORKSPACE_PATH = "${HOST_JENKINS_HOME_ON_HOST}/workspace/${env.JOB_NAME}"
        HOST_ALLURE_RESULTS_PATH = "${HOST_WORKSPACE_PATH}/output/allure-results"
        HOST_ALLURE_REPORT_PATH = "${HOST_WORKSPACE_PATH}/output/reports/temp-allure-report-for-summary" // 临时报告路径

        // --- 测试相关 ---
        TEST_SUITE_VALUE = "${params.TEST_SUITE == '全部' ? 'all' : (params.TEST_SUITE == '冒烟测试' ? 'smoke' : 'regression')}"
        DOCKER_IMAGE = "automated-testing:dev" // 使用的测试环境镜像
    }

    // --- Jenkins 凭据创建指南 ---
    #### Jenkins 凭据创建指南 (已移除 allure-base-url)

    请在 Jenkins 系统中预先创建以下凭据，确保凭据 ID 与 Jenkinsfile 中 `environment` 块定义的完全一致。

    **创建步骤（在 Jenkins UI 中操作）：** (与之前一致，省略重复表格)

    *   移除 `allure-base-url` 凭据，因为报告 URL 现在由 Allure Jenkins 插件生成。

    stages {
        stage('检出代码') {
            steps {
                // ... (使用 withCredentials 检出代码) ...
            }
        }

        stage('准备环境 (Agent)') {
            steps {
                // ... (在 Agent 上创建和清理 allure-results 和 temp-allure-report-for-summary 目录) ...
            }
        }

        stage('检查脚本文件') {
            steps {
                // ... (检查 write_allure_metadata.py, run_and_notify.py 等是否存在) ...
                // !!移除对 prepare_nginx_dir.sh 和 deploy_allure_report.sh 的检查!!
            }
        }

        stage('并行执行测试') {
             steps {
                script {
                    // ... (选择和注入凭据) ...
                    try {
                        // ... (运行 docker run pytest，挂载 HOST_WORKSPACE_PATH 和 HOST_ALLURE_RESULTS_PATH) ...
                    } catch (err) {
                        echo "测试阶段出现错误: ${err}."
                        currentBuild.result = 'UNSTABLE'
                    }
                } // End script
            } // End steps
        } // End stage '并行执行测试'

   } // End stages

   post { // 流水线完成后执行
       always {
           echo "Pipeline 完成. 开始执行报告生成和通知步骤..."
           script {
               def allureReportUrl = "" // 用于存储 Jenkins 插件生成的报告 URL
               def allureStepSuccess = false
               def tempReportGenSuccess = false

               try {
                   // --- 注入邮件等凭据 ---
                   withCredentials([
                       string(credentialsId: env.EMAIL_PASSWORD_CREDENTIALS_ID, variable: 'INJECTED_EMAIL_PASSWORD'),
                       string(credentialsId: env.EMAIL_SMTP_SERVER_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_SMTP_SERVER'),
                       // ... 其他邮件凭据 ...
                   ]) {

                       // --- 1. 写入 Allure 元数据 ---
                       echo "写入 Allure 元数据文件到 ${env.HOST_ALLURE_RESULTS_PATH} (在宿主机上)..."
                       sh """
                       docker run --rm --name write-metadata-${BUILD_NUMBER} \\
                         /* ... env vars ... */ \\
                         -v ${env.HOST_WORKSPACE_PATH}:/workspace:ro \\
                         -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \\
                         ${env.DOCKER_IMAGE} \\
                         python /workspace/ci/scripts/write_allure_metadata.py /results_out
                       """
                       echo "Allure 元数据写入完成。"

                       // --- 2. 修正 allure-results 目录权限 ---
                       echo "修正宿主机目录 ${env.HOST_ALLURE_RESULTS_PATH} 的权限..."
                       sh """
                       docker run --rm --name chown-chmod-results-${BUILD_NUMBER} \\
                         -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_to_fix:rw \\
                         ${env.DOCKER_IMAGE} \\
                         sh -c 'chown -R 1000:1000 /results_to_fix || echo "chown failed"; chmod -R a+r /results_to_fix || echo "chmod failed!"'
                       """
                       echo "权限修正尝试完成。"

                       // --- 3. 使用 Allure Jenkins 插件生成和归档报告 ---
                       echo "使用 Allure Jenkins 插件处理 ${WORKSPACE}/output/allure-results 中的结果..."
                       try {
                           allure([
                               properties: [],
                               reportBuildPolicy: 'ALWAYS',
                               results: [
                                   [path: 'output/allure-results'] // 相对于 WORKSPACE
                               ]
                           ])
                           allureStepSuccess = true
                           allureReportUrl = "${env.BUILD_URL}allure/" // Jenkins 插件报告 URL
                           echo "Allure 插件报告处理完成。报告 URL: ${allureReportUrl}"
                       } catch (allurePluginError) {
                           echo "Allure 插件步骤失败: ${allurePluginError}"
                           allureStepSuccess = false
                           allureReportUrl = "(Allure 插件报告生成失败)"
                       }

                       // --- 4. 手动生成报告到临时目录 (获取 summary.json) ---
                       echo "生成临时报告到 ${env.HOST_ALLURE_REPORT_PATH} 以获取 summary.json..."
                       // 确保宿主机目录存在
                       sh """
                       docker run --rm --name mkdir-temp-report-${BUILD_NUMBER} \\
                         -v ${env.HOST_WORKSPACE_PATH}:/host_workspace:rw \\
                         ${env.DOCKER_IMAGE} \\
                         sh -c 'mkdir -p /host_workspace/output/reports/temp-allure-report-for-summary/widgets'
                       """
                       // 运行 allure generate
                       sh """
                       docker run --rm --name allure-gen-temp-${BUILD_NUMBER} \\
                         -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_in:ro \\
                         -v ${env.HOST_ALLURE_REPORT_PATH}:/report_out:rw \\
                         ${env.DOCKER_IMAGE} \\
                         sh -c 'allure generate /results_in --clean -o /report_out'
                       """
                       // 检查 summary.json 是否成功生成
                       def summaryCheckExitCode = sh script: "docker run --rm -v ${env.HOST_ALLURE_REPORT_PATH}:/report_check:ro ${env.DOCKER_IMAGE} test -f /report_check/widgets/summary.json", returnStatus: true
                       if (summaryCheckExitCode == 0) {
                           tempReportGenSuccess = true
                           echo "summary.json 已成功生成到宿主机路径: ${env.HOST_ALLURE_REPORT_PATH}/widgets/summary.json"
                       } else {
                           tempReportGenSuccess = false
                           echo "[警告] 未能在 ${env.HOST_ALLURE_REPORT_PATH}/widgets/ 中找到 summary.json。"
                       }

                       // --- 5. 发送邮件通知 ---
                       if (params.SEND_EMAIL) {
                           echo "发送邮件通知 (尝试读取 ${env.HOST_ALLURE_REPORT_PATH}/widgets/summary.json)..."
                           sh """
                           docker run --rm --name notify-${BUILD_NUMBER} \\
                             -e CI=true \\
                             -e APP_ENV=${params.APP_ENV} \\
                             -e EMAIL_ENABLED=${params.SEND_EMAIL} \\
                             -e EMAIL_PASSWORD='${INJECTED_EMAIL_PASSWORD}' \\
                             // ... 其他邮件环境变量 ...
                             -e ALLURE_PUBLIC_URL="${allureReportUrl}" \\ // 使用插件生成的 URL
                             -e BUILD_STATUS="${currentBuild.result ?: 'SUCCESS'}" \\
                             // ... 其他构建信息环境变量 ...
                             -v ${env.HOST_WORKSPACE_PATH}:/workspace:ro \\
                             -v ${env.HOST_ALLURE_REPORT_PATH}:/report:ro \\ // 只读挂载临时报告
                             ${env.DOCKER_IMAGE} \\
                             python /workspace/ci/scripts/run_and_notify.py
                           """
                       } else {
                           echo "邮件通知已禁用。"
                       }

                   } // End withCredentials
               } catch (err) {
                   echo "Post-build 阶段出现严重错误: ${err}"
                   // ... 处理错误 ...
               } finally {
                   // --- 6. 设置构建描述 ---
                   // ... (使用 allureReportUrl 设置描述) ...
                   def finalStatus = currentBuild.result ?: 'SUCCESS'
                   def reportLink = allureStepSuccess && allureReportUrl.startsWith("http") ? "<a href='${allureReportUrl}' target='_blank'>查看报告</a>" : allureReportUrl ?: "(报告链接不可用)"
                   currentBuild.description = "${params.APP_ENV.toUpperCase()} 环境 [...] - ${finalStatus} - ${reportLink}"

                   // --- 7. 清理临时报告目录和 Agent 工作区 ---
                   echo "清理临时报告目录 ${env.HOST_ALLURE_REPORT_PATH} (在宿主机上)..."
                   sh """
                   docker run --rm --name cleanup-temp-report-${BUILD_NUMBER} \\
                     -v ${env.HOST_WORKSPACE_PATH}:/host_workspace:rw \\
                     ${env.DOCKER_IMAGE} \\
                     sh -c 'rm -rf /host_workspace/output/reports/temp-allure-report-for-summary'
                   """
                   cleanWs()
                   echo "Agent 工作空间和临时报告目录已清理。"
               } // End finally
           } // End script
       } // End always
       // ... success, failure, unstable blocks ...
   } // End post
} // End pipeline
```
- output目录建议定期清理，节省磁盘空间。

---

## 15. 常见问题FAQ

*   **Q: 没有Dockerfile怎么办？**
    *   A: 请在项目根目录新建Dockerfile，内容见本手册第11节。确保 `allure-2.27.0.zip` 文件存在。
*   **Q: 如何保证本地和CI环境一致？**
    *   A: 所有成员和CI都用同一个Dockerfile构建或拉取同一个镜像标签。
*   **Q: 环境变量优先级如何？**
    *   A: `docker run -e` > 容器内.env文件。CI 中优先使用 `-e` 注入 Jenkins 凭据。
*   **Q: Jenkins Allure 报告无法访问或内容不正确？**
    *   A: 检查：
        1.  `HOST_ALLURE_RESULTS_PATH` 变量是否正确指向宿主机上的 Allure 结果目录。
        2.  该目录的权限是否允许 Jenkins Agent (或运行 Docker 的用户) 读取。
        3.  Allure Jenkins 插件配置是否正确指向了 Agent 上的结果路径 (`output/allure-results`)。
        4.  `write_allure_metadata.py` 是否成功执行并写入了元数据。
*   **Q: Jenkins邮件通知缺少统计信息？**
    *   A: 检查：
        1.  `post` 阶段手动运行 `allure generate` 的步骤是否成功执行 (检查 Jenkins 日志)。
        2.  `HOST_ALLURE_REPORT_PATH` 挂载是否正确。
        3.  `summary.json` 是否确实生成在了 `HOST_ALLURE_REPORT_PATH/widgets/` 目录下。
        4.  `run_and_notify.py` 脚本是否正确读取和解析了 `summary.json`。
*   **Q: Jenkins环境变量/凭据如何安全注入？**
    *   A: 强烈推荐使用 Jenkins 的 "Credentials" 功能，并在 Jenkinsfile 中通过 `withCredentials` 块注入。
*   **Q: Playwright/Allure安装慢或报错？**
    *   A: 检查 Dockerfile 中是否已配置国内镜像源。网络不稳定时可尝试增加 `POETRY_REQUESTS_TIMEOUT`。
*   **Q: Playwright依赖库缺失如何解决？**
    *   A: 仔细核对 Dockerfile 中 `apt-get install` 命令是否包含了所有 Playwright 官方文档要求的系统依赖。
*   **Q: output目录产物如何归档？**
    *   A: 可以归档 `HOST_ALLURE_RESULTS_PATH` 作为原始数据备份。最终报告由 Jenkins 插件管理。
*   **Q: 为什么要使用 poetry run pytest 而不是直接 pytest？**
    *   A: 确保在 Poetry 管理的环境中运行，避免依赖问题。
*   **Q: Docker 拉取镜像或构建时网络超时/无法连接？**
    *   A: 核心是解决 Docker daemon 访问仓库的网络问题。首选方案是配置并验证有效的国内镜像加速器。
*   **Q: Jenkins流水线在Docker容器(DooD模式)中挂载卷找不到文件/内容不正确？**
    *   A: 关键在于区分 Jenkins Agent 容器内的路径 (`${WORKSPACE}`) 和宿主机上的真实路径。必须在 Jenkinsfile 的 `docker run` 命令中使用 `-v` 挂载宿主机上的路径。

---

## 16. 邮件通知集成

测试完成后自动发送邮件通知是CI/CD自动化的重要环节。本项目当前通过在 Jenkins 流水线中调用 Python 脚本来实现邮件发送。

### 16.1 Python脚本发送邮件 (当前项目使用方式)

项目中 `ci/scripts/run_and_notify.py` 负责在测试执行后收集结果，并根据环境变量配置调用邮件发送逻辑。**关键在于**: 该脚本会尝试读取**手动生成的临时 Allure 报告**中的 `summary.json` 文件来获取详细的测试统计数据。

**强烈推荐**将所有邮件配置（SMTP服务器、端口、发件人、密码/授权码、收件人、SSL设置）通过 Jenkins 凭据管理，并在 Jenkinsfile 中使用 `withCredentials` 将这些凭据注入到运行该脚本的容器的环境变量中。

```python
# ci/scripts/run_and_notify.py 逻辑示意
import os
# from src.utils.email_notifier import EmailNotifier
from ci.scripts.utils import get_allure_summary # 导入获取摘要的函数

def send_notification(allure_plugin_url): # URL 来自 Jenkins 插件
    # --- 从环境变量获取邮件配置 (由 Jenkinsfile 通过凭据注入) ---
    enabled = os.environ.get("EMAIL_ENABLED", "false").lower() == "true"
    # ... 获取其他邮件配置 sender, password, recipients_str, smtp_server, etc. ...

    if not enabled: # or other checks fail
        print("邮件通知未启用或配置缺失，跳过。")
        return

    # --- 尝试从临时报告目录获取摘要 ---
    # Jenkinsfile 中将 HOST_ALLURE_REPORT_PATH 挂载到了 /report
    summary = get_allure_summary(report_dir_base="/report")

    if not summary:
        print("警告: 未能获取 Allure 摘要信息，邮件将不包含详细统计。")
        # 可以选择发送一个不含统计的简化邮件，或直接返回
        # return

    # 解析收件人等配置
    # ...

    # 准备邮件内容
    subject = f"【自动化测试】..."
    # 构建 HTML 正文，如果 summary 存在则包含统计信息，否则提示
    html_body = f"<html><body>"
    if summary and 'total' in summary:
         # ... 使用 summary 构建包含统计的 HTML ...
         pass
    else:
         html_body += "<p>未能获取详细统计信息。</p>"
    html_body += f"<br/> 报告链接: <a href='{allure_plugin_url}'>点击查看 (Jenkins)</a></body></html>"

    # 发送邮件
    try:
        # ... 调用邮件发送逻辑 ...
        print(f"邮件通知已尝试发送给: ...")
    except Exception as e:
        print(f"发送邮件失败: {e}")

# 在 run_and_notify.py 的主逻辑中调用
# if __name__ == "__main__":
#     allure_public_url = os.environ.get("ALLURE_PUBLIC_URL", "#") # 获取插件生成的 URL
#     send_notification(allure_public_url)
```

**确保 Jenkinsfile 中在 `post { always { ... } }` 块的 `withCredentials` 中注入了所有必要的邮件环境变量，并且在调用 `run_and_notify.py` 的 `docker run` 命令中正确挂载了临时报告目录 (`-v ${env.HOST_ALLURE_REPORT_PATH}:/report:ro`)。**

### 16.2 Jenkins Email Extension Plugin (备选方案)
如果可以接受邮件中不包含详细的 Allure 测试统计信息（只有构建状态和报告链接），可以考虑使用 Jenkins 的 Email Extension Plugin (`emailext`)。这样可以移除自定义的邮件脚本 (`run_and_notify.py`, `notify.py`, `utils.py`)，移除手动生成临时报告的步骤，并移除 Dockerfile 中的 Allure CLI 依赖，从而简化流程。但会牺牲邮件内容的丰富度。

### 16.3 邮件通知最佳实践
- **使用凭据管理**：绝不硬编码密码或 API 密钥。
- **清晰的标题**：包含项目、环境、构建号、状态等关键信息。
- **简洁的正文**：突出显示关键结果（状态、通过率等）和报告链接。
- **区分收件人**：根据构建状态或失败类型发送给不同的人员/群组。
- **错误处理**：邮件发送失败不应导致整个 CI 流程失败。

---

## 变更记录
- YYYY-MM-DD: **重大更新**: 根据最新的 Jenkinsfile 和 CI 脚本重构，更新了文档。主要变更包括：明确 Allure CLI 仍然需要；更新了 CI 脚本说明；修正了 Jenkinsfile 示例，移除了 Nginx 部署逻辑，准确反映了 Allure 插件 + 手动临时报告生成（用于邮件摘要）+ 清理的流程；澄清了报告访问方式；调整了 FAQ 和邮件通知章节。
- YYYY-MM-DD: **重大更新**: 将 Web/API URL、Allure 基础 URL、Git 仓库 URL 及所有邮件配置参数化到 Jenkins 凭据。更新了 Jenkins 凭据创建指南和 Jenkinsfile 示例以反映这些变化。将报告生成和通知逻辑移至 `post { always }` 块以强制执行。
- YYYY-MM-DD: 新增 Jenkins 凭据创建指南，调整邮件通知说明以匹配项目实践，移除 emailext 示例强调 Python 脚本方式。
- YYYY-MM-DD: 更新 Dockerfile 和 Jenkinsfile 相关描述，移除 GitLab CI 示例，强化 Jenkins 集成说明和 DooD 模式下的路径映射解释。