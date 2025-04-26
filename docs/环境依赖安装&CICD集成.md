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
  - 敏感信息（如账号、密码、API密钥）用CI平台凭据管理。

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
- 下载并解压（支持两种格式：.tgz或.zip）：
  ```bash
  # 方法1：使用.tgz格式
  cd /opt
  wget https://github.com/allure-framework/allure2/releases/download/2.27.0/allure-2.27.0.tgz
  tar -zxvf allure-2.27.0.tgz
  sudo mv allure-2.27.0 /opt/allure
  sudo ln -s /opt/allure/bin/allure /usr/bin/allure
  
  # 方法2：使用.zip格式（与Dockerfile一致）
  cd /opt
  wget https://github.com/allure-framework/allure2/releases/download/2.27.0/allure-2.27.0.zip
  unzip allure-2.27.0.zip
  sudo mv allure-2.27.0 /opt/allure
  sudo ln -s /opt/allure/bin/allure /usr/bin/allure
  
  # 验证安装
  allure --version
  ```
- Allure依赖Java 8+，如未安装请执行：
  ```bash
  # CentOS/RHEL
  yum install java-1.8.0-openjdk -y
  
  # Ubuntu/Debian
  apt-get update && apt-get install -y openjdk-8-jre
  
  # 设置JAVA_HOME（所有系统）
  export JAVA_HOME=$(dirname $(dirname $(readlink -f $(which java))))
  export PATH=$JAVA_HOME/bin:$PATH
  ```
- `output/allure-results` 和 `output/reports/allure-report` 目录分别用于存放测试结果和最终生成的 HTML 报告。`output/` 目录已在 `.gitignore` 中全局忽略，避免提交临时文件和生成报告。

---

## 8. 运行自动化测试与报告生成
- 运行测试：
  ```bash
  poetry run pytest --alluredir=output/allure-results
  ```
- 推荐用`poetry run pytest`保证依赖环境一致，避免直接用`pytest`导致依赖找不到。
- 生成HTML报告：
  ```bash
  allure generate output/allure-results -o output/reports/allure-report --clean
  ```
- 本地预览报告：
  ```bash
  allure open output/reports/allure-report
  ```
- output目录下的allure-results、allure-report、logs、screenshots、coverage-data等均为临时/生成文件，已在.gitignore中全局忽略。

---

## 9. 测试数据分离与管理
- 所有测试数据应存放于data/目录，按业务/平台分子目录，推荐YAML/JSON格式。
- data/README.md中需说明各数据文件用途和字段含义。
- 新增/调整数据结构时，务必补充data/README.md。
- 测试数据与测试逻辑分离，便于维护和参数化。

---

## 10. CI/CD集成与敏感信息管理
- 所有代码变更必须通过CI/CD流程验证，确保代码质量和自动化测试执行。
- 推荐使用Jenkins、GitHub Actions等平台，参考@.github/workflows/test.yml。
- CI环境必须用poetry安装依赖，使用缓存加速。
- 测试环境与开发环境保持一致，Python版本3.11+。
- 敏感环境变量建议用CI平台凭据管理功能注入，避免写入代码或镜像。
- 参考Jenkinsfile和GitHub Actions示例，敏感信息不要明文写入流水线脚本。

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
  RUN rm -rf /etc/apt/sources.list.d/* && \\
      echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \\
      echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \\
      echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \\
      apt-get clean && \\
      apt-get update && apt-get install -y --no-install-recommends apt-transport-https ca-certificates && \\
      apt-get update

  # 安装 Playwright 浏览器依赖和常用工具 (openjdk用于Allure, unzip解压Allure)
  RUN apt-get install -y --no-install-recommends \\
      wget openjdk-17-jre-headless unzip \\
      libglib2.0-0 libnss3 libnspr4 \\
      libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libexpat1 \\
      libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 \\
      libxcb1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 \\
      fonts-liberation libappindicator3-1 lsb-release \\
      && apt-get clean && rm -rf /var/lib/apt/lists/*

  # 配置pip和Poetry国内源 (以阿里云和清华为例，提供兜底)
  RUN mkdir -p /root/.pip && \\
      echo "[global]" > /root/.pip/pip.conf && \\
      echo "index-url = https://mirrors.aliyun.com/pypi/simple/" >> /root/.pip/pip.conf
  RUN pip install --upgrade pip \\
      && pip install "poetry>=1.5.0"
  RUN poetry config repositories.aliyun https://mirrors.aliyun.com/pypi/simple/ \\
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
  RUN pip install playwright -i https://mirrors.aliyun.com/pypi/simple/ \\
      || pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple \\
      && playwright install

  # 安装Allure CLI (从本地复制zip包)
  COPY allure-2.27.0.zip /tmp/
  RUN unzip /tmp/allure-2.27.0.zip -d /opt/ \\
      && ln -s /opt/allure-2.27.0/bin/allure /usr/bin/allure \\
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
  docker build -t automated-testing:dev . # 使用优化后的Dockerfile

  # 3. 运行测试 (挂载代码和输出目录)
  # 确保本地 output 目录存在: mkdir -p output/allure-results output/reports/allure-report
  # 注意：$(pwd) 获取的是当前宿主机路径
  docker run --rm \\
    -v $(pwd):/workspace:rw \\
    -v $(pwd)/output/allure-results:/results_out:rw \\
    -v $(pwd)/output/reports/allure-report:/report_out:rw \\
    --workdir /workspace \\
    automated-testing:dev \\
    bash -c "poetry run pytest --alluredir=/results_out && allure generate /results_out -o /report_out --clean"

  # 4. 本地预览报告 (如果需要)
  allure open output/reports/allure-report
  ```
- **CI脚本思路（以Jenkins Pipeline为例，演示卷挂载）：**
  ```groovy
  // Jenkinsfile (部分示例)
  environment {
      // ... 其他环境变量 ...
      HOST_JENKINS_HOME_ON_HOST = '/var/lib/docker/volumes/jenkins_home/_data' // !!宿主机Jenkins Home路径!!
      HOST_WORKSPACE_PATH = "${HOST_JENKINS_HOME_ON_HOST}/workspace/${env.JOB_NAME}" // 宿主机工作区路径
      HOST_ALLURE_RESULTS_PATH = "${HOST_WORKSPACE_PATH}/output/allure-results" // 宿主机结果路径
      HOST_ALLURE_REPORT_PATH = "${HOST_WORKSPACE_PATH}/output/reports/allure-report" // 宿主机报告路径
      DOCKER_IMAGE = "automated-testing:dev" // 定义使用的镜像
  }
  stages {
      // ... checkout ...
      stage('Run Tests in Docker') {
          steps {
              script {
                  // 确保宿主机上的目录存在
                  sh "mkdir -p ${env.HOST_ALLURE_RESULTS_PATH} ${env.HOST_ALLURE_REPORT_PATH}"

                  // 运行测试容器，注意使用宿主机路径进行卷挂载
                  sh """
                  docker run --rm \\
                    -e APP_ENV=\${params.APP_ENV} \\
                    -e TEST_DEFAULT_USERNAME=\${ACCOUNT_USERNAME} \\
                    -e TEST_DEFAULT_PASSWORD=\${ACCOUNT_PASSWORD} \\
                    -v ${env.HOST_WORKSPACE_PATH}:/workspace:rw \\
                    -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \\
                    --workdir /workspace \\
                    ${env.DOCKER_IMAGE} \\
                    poetry run pytest --alluredir=/results_out
                  """

                  // 生成报告容器，同样使用宿主机路径
                  sh """
                  docker run --rm \\
                    -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:ro \\
                    -v ${env.HOST_ALLURE_REPORT_PATH}:/report_out:rw \\
                    ${env.DOCKER_IMAGE} \\
                    allure generate /results_out -o /report_out --clean
                  """
              }
          }
      }
      // ... report deployment and notification ...
  }
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
- **推荐策略**：在 CI/CD 流水线中，将宿主机的工作区目录、Allure 原始结果目录、最终报告目录分别挂载到容器内不同的路径。
- **示例命令 (Jenkinsfile 风格，使用宿主机路径变量)**：
  ```bash
  # 假设 env.HOST_WORKSPACE_PATH, env.HOST_ALLURE_RESULTS_PATH, env.HOST_ALLURE_REPORT_PATH 已定义
  # 假设 env.ALLURE_NGINX_HOST_PATH 指向 Nginx 的宿主机报告目录
  
  # 1. 运行测试，将结果输出到挂载的 /results_out
  docker run --rm \
    -v ${env.HOST_WORKSPACE_PATH}:/workspace:rw \
    -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \
    --workdir /workspace \
    automated-testing-env:latest \
    poetry run pytest --alluredir=/results_out
    
  # 2. 生成报告，从 /results_out 读取，输出到挂载的 /report_out
  docker run --rm \
    -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:ro \
    -v ${env.HOST_ALLURE_REPORT_PATH}:/report_out:rw \
    automated-testing-env:latest \
    allure generate /results_out -o /report_out --clean
    
  # 3. (可选) 将生成的报告部署到 Nginx 目录
  #    注意：此步骤通常使用辅助脚本，直接操作宿主机上的报告和 Nginx 目录
  #    docker run ... alpine:latest sh deploy_script.sh ${env.HOST_ALLURE_REPORT_PATH} ${env.ALLURE_NGINX_HOST_PATH}
  ```
- **为什么这样做？**
  - 清晰分离代码、原始结果和最终报告的路径，避免冲突。
  - 报告直接生成在宿主机指定路径，方便后续部署或归档。
  - CI/CD 流程更清晰，每一步职责单一。

### 12.4 环境变量传递最佳实践
- 推荐用`-e`参数在docker run时传递敏感信息和环境配置（如账号、密码、URL等），如：
  ```bash
  docker run --rm \
    -e APP_ENV=prod \
    -e WEB_BASE_URL=https://xxx.com \
    -e TEST_DEFAULT_USERNAME=xxx \
    -e TEST_DEFAULT_PASSWORD=xxx \
    ...
  ```
- 也可用`--env-file`参数批量传递.env文件内容：
  ```bash
  docker run --rm --env-file .env ...
  ```
- **优先级说明**：`-e`参数 > `--env-file` > 容器内的.env文件。
- **为什么这样做？**
  - 保证敏感信息不写进镜像或代码，安全性高，灵活适配多环境。

### 12.5 典型docker run命令模板及参数解释 (结合卷挂载)
- **场景：在 CI/CD 中运行测试并生成报告**
  ```bash
  # --- 运行测试 ---
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

  # --- 生成报告 ---
  docker run --rm \
    -v <宿主机Allure结果路径>:/results_out:ro \
    -v <宿主机Allure报告路径>:/report_out:rw \
    <环境镜像名:标签> \
    allure generate /results_out -o /report_out --clean # <命令>
  ```
- **参数说明：**
  - `--rm`：容器运行结束后自动删除。
  - `-e`：传递环境变量。
  - `-v <宿主机路径>:<容器路径>:<模式>`：挂载卷。
    - `<宿主机工作区路径>:/workspace:rw`：将最新的代码挂载到容器 `/workspace`。
    - `<宿主机Allure结果路径>:/results_out:rw`：挂载用于存放原始测试结果的目录。
    - `<宿主机Allure报告路径>:/report_out:rw`：挂载用于存放生成的HTML报告的目录。
  - `--workdir /workspace`：设置容器的工作目录为挂载的代码目录。
  - `<环境镜像名:标签>`：指定包含所有依赖的环境镜像。
  - `<命令>`：在容器内执行的命令，如 `poetry run pytest ...` 或 `allure generate ...`。

### 12.6 团队协作和CI/CD流水线下的推荐用法
- 推荐所有团队成员和CI/CD流水线都用同一个Dockerfile和docker run命令，保证环境和产物一致。
- CI平台（如Jenkins、GitHub Actions）可用secrets机制安全注入敏感变量。
- output目录建议统一挂载到Web服务或CI产物归档目录，便于报告自动发布和追溯。

### 12.7 常见问题与解答
- **Q: 没有Dockerfile怎么办？**
  - A: 请在项目根目录新建Dockerfile，内容见本手册Docker章节。
- **Q: 如何保证本地和CI环境一致？**
  - A: 所有成员和CI都用同一个Dockerfile和镜像，避免本地依赖污染。
- **Q: 环境变量优先级如何？**
  - A: `docker run -e` > `--env-file` > 容器内.env文件。
- **Q: 报告生成后Web服务无法访问？**
  - A: 检查-v挂载路径是否与Web服务配置一致，权限是否正确。
- **Q: Jenkins/GitLab CI环境变量如何安全注入？**
  - A: 推荐用凭据/变量机制，不要明文写在脚本里，详见各平台示例。
- **Q: Playwright/Allure安装慢或报错？**
  - A: 优先切换国内镜像源，或参考官方FAQ。
- **Q: Playwright依赖库缺失如何解决？**
  - A: 确保Dockerfile中安装了所有必要的依赖，libglib2.0-0、libnss3等。
- **Q: output目录产物如何归档？**
  - A: 推荐用CI平台的产物归档功能，便于追溯和发布。
- **Q: 产物目录与Web服务目录不一致怎么办？**
  - A: 建议统一挂载，或在测试后用脚本同步到Web服务目录。
- **Q: 为什么要使用poetry run pytest而不是直接pytest？**
  - A: 确保在正确的虚拟环境中运行，避免依赖问题。
- **Q: Docker 拉取镜像（如 `docker pull` 或 `docker build` 时）失败，报错 `Connection timed out`、`Network is unreachable` 或 `context deadline exceeded`，如何解决？**
  - A: 这通常是由于本地网络环境无法稳定连接到 Docker Hub (registry-1.docker.io) 或其他 Docker 仓库（包括配置的加速器）的网络问题。排查步骤如下：
    1.  **基础网络检查**：确认本机能 `ping` 通外部地址（如 `baidu.com`, `8.8.8.8`）和网关。
    2.  **DNS 检查**：使用 `nslookup <仓库域名>` 确认域名能正确解析。
    3.  **端口连通性检查**：使用 `telnet <仓库域名> 443` 或 `nc -zv <仓库域名> 443` 检查 HTTPS 端口是否可达。即使 `ping` 通，端口也可能被防火墙阻止。
    4.  **强烈推荐配置镜像加速器**：这是解决国内访问 Docker Hub 不稳定问题的最有效方法。编辑 `/etc/docker/daemon.json` 文件（如不存在则创建，需要 sudo 权限），添加 `registry-mirrors` 列表，例如：
        ```json
        {
          "registry-mirrors": [
            "https://docker.m.daocloud.io", // 示例，选择可用加速器
            "https://hub-mirror.c.163.com"
            // ... 其他可用加速器
          ]
        }
        ```
    5.  **验证并筛选加速器**：配置后，务必 `ping <加速器域名>` 并用 `nslookup <加速器域名>` 确认**所有**配置的加速器都能被解析和访问。如果某个加速器域名无法解析（报错"名称或服务未知"），**必须将其从 `daemon.json` 中移除**，否则 Docker 尝试失败后会回退到直连官方仓库，导致问题依旧。
    6.  **重启 Docker 服务**：修改 `/etc/docker/daemon.json` 后，必须执行 `sudo systemctl daemon-reload && sudo systemctl restart docker` 使配置生效。
    7.  **防火墙检查**：检查本地防火墙 (`ufw`, `firewalld`) 和路由器防火墙规则。

- **Q: Jenkins流水线在Docker容器(DooD模式)中运行测试时，通过 `-v ${WORKSPACE}:/some/path` 挂载工作区，但容器内找不到文件或目录内容不正确，怎么办？**
  - A: 这是典型的Docker-outside-of-Docker (DooD) 问题。Jenkins容器内部的`${WORKSPACE}`路径（如`/var/jenkins_home/workspace/...`）对于宿主机的Docker服务是无效的。宿主机Docker会尝试在自己的文件系统上查找这个路径，导致挂载错误。
    **解决方案：**
    1.  **确定宿主机映射路径：** 通过 `docker inspect <jenkins容器ID或名称>` 命令查看Jenkins容器的`Mounts`部分，找到`Destination`为`/var/jenkins_home`（或Jenkins数据目录）对应的`Source`路径（宿主机上的真实路径，例如`/var/lib/docker/volumes/jenkins_home/_data`）。
    2.  **修改Jenkinsfile：** 
        - 在`environment`块定义新的环境变量，存储这个宿主机路径以及基于它计算出的宿主机工作区路径、结果路径等 (例如：`HOST_JENKINS_HOME_ON_HOST`, `HOST_WORKSPACE_PATH`, `HOST_ALLURE_RESULTS_PATH`)。
        - 在所有需要挂载工作区或其子目录的`docker run`命令中，修改`-v`参数，**使用这些基于宿主机的路径变量**，而不是`${WORKSPACE}`。例如：`-v ${env.HOST_WORKSPACE_PATH}:/workspace:rw`。

---

## 13. 参考与扩展
- [Allure官方文档](https://docs.qameta.io/allure/)
- [Playwright官方文档](https://playwright.dev/python/)
- [Poetry官方文档](https://python-poetry.org/docs/)
- 团队内部Wiki/知识库（如有），持续收集最佳实践与常见问题，便于团队协作和持续改进。

---

## 14. 主流CI平台Docker集成示例

本节详细说明如何在Jenkins中集成Docker自动化测试，**关键步骤均有解释**，适合团队成员参考。由于本项目当前主要使用Jenkins作为CI/CD工具，这里仅提供Jenkins的集成示例。

### 14.1 Jenkins流水线（Pipeline）集成

**核心思路：** 利用Jenkins Pipeline和Docker插件（或直接调用宿主机Docker命令），实现拉取代码、构建/拉取环境镜像、在Docker容器中运行测试、生成报告并部署的全自动化流程。特别注意在Docker-outside-of-Docker (DooD) 模式下宿主机路径的正确映射。

**Jenkinsfile关键部分示例 (参考项目根目录的 `Jenkinsfile`)**

```groovy
pipeline {
    agent any // 或指定特定的agent标签

    parameters { // 定义构建参数，增加灵活性
        choice(name: 'APP_ENV', choices: ['test', 'prod'], description: '选择测试环境')
        // ... 其他参数，如运行哪些测试、是否发邮件等 ...
    }

    environment {
        // --- 凭据 ID (在Jenkins中管理) ---
        GIT_CREDENTIALS_ID = 'git-credentials'
        TEST_ENV_CREDENTIALS_ID = 'test-env-credentials'
        PROD_ENV_CREDENTIALS_ID = 'prod-env-credentials'
        EMAIL_PASSWORD_CREDENTIALS_ID = 'email-password-credential'

        // --- Allure 报告相关 (Nginx 宿主机路径) ---
        // 定义报告在Nginx上的部署路径和URL
        ALLURE_NGINX_DIR_NAME = "${params.APP_ENV == 'prod' ? 'allure-report-prod' : 'allure-report-test'}"
        ALLURE_PUBLIC_URL = "http://<nginx服务器IP或域名>:<端口>/${ALLURE_NGINX_DIR_NAME}/" // 需要替换
        ALLURE_NGINX_HOST_PATH = "/usr/share/nginx/html/${ALLURE_NGINX_DIR_NAME}" // Nginx在宿主机上的路径

        // --- Docker Agent & 宿主机路径映射 (DooD模式关键) ---
        // !! 重要：此路径需要根据实际Jenkins Docker容器挂载情况确定 !!
        HOST_JENKINS_HOME_ON_HOST = '/var/lib/docker/volumes/jenkins_home/_data'
        // 基于宿主机Jenkins Home计算出宿主机上的工作区、结果、报告路径
        HOST_WORKSPACE_PATH = "${HOST_JENKINS_HOME_ON_HOST}/workspace/${env.JOB_NAME}"
        HOST_ALLURE_RESULTS_PATH = "${HOST_WORKSPACE_PATH}/output/allure-results"
        HOST_ALLURE_REPORT_PATH = "${HOST_WORKSPACE_PATH}/output/reports/allure-report"

        // --- 测试相关 ---
        DOCKER_IMAGE = "automated-testing:dev" // 使用的测试环境镜像
        // ... 其他测试所需的环境变量 ...
    }

    // 新增：Jenkins凭据创建步骤
    #### Jenkins 凭据创建指南

    为了让 Jenkinsfile 能够安全地访问 Git 仓库、测试环境账号和邮箱服务，你需要在 Jenkins 系统中预先创建以下凭据。请确保凭据 ID 与 Jenkinsfile 中 `environment` 块定义的完全一致。

    **创建步骤（在 Jenkins UI 中操作）：**

    1.  登录 Jenkins。
    2.  导航到 "Manage Jenkins" -> "Credentials"。
    3.  在 "Stores scoped to Jenkins" 下，点击 "System" 域（或你选择的其他域）下的 "Global credentials (unrestricted)"。
    4.  点击左侧菜单的 "Add Credentials"。
    5.  根据下表创建凭据：

        | Jenkinsfile中的凭据ID          | 类型 (Kind)        | ID (必须与左侧一致)           | Scope  | Username (用户名)       | Password (密码/令牌/Secret)  | Description (描述)                   |
        | :----------------------------- | :----------------- | :---------------------------- | :----- | :---------------------- | :-------------------------- | :----------------------------------- |
        | `git-credentials`              | Username with password | `git-credentials`             | Global | 你的 Git 仓库用户名       | 你的 Git 仓库密码或访问令牌 | Git 仓库访问凭据                     |
        | `test-env-credentials`         | Username with password | `test-env-credentials`        | Global | 测试环境默认登录用户名 | 测试环境默认登录密码        | 测试环境账号密码                   |
        | `prod-env-credentials`         | Username with password | `prod-env-credentials`        | Global | 生产环境默认登录用户名 | 生产环境默认登录密码        | 生产环境账号密码                   |
        | `email-password-credential`    | Secret text        | `email-password-credential`   | Global |                         | 你的发件邮箱密码或授权码     | 邮件通知发件人密码/授权码         |

    **注意事项：**

    *   **ID 必须精确匹配** Jenkinsfile 中的定义。
    *   对于 `git-credentials`，如果你的 Git 仓库使用 SSH 密钥认证，你需要创建 "SSH Username with private key" 类型的凭据。
    *   对于 `email-password-credential`，选择 "Secret text" 类型，并将邮箱密码或生成的应用授权码粘贴到 "Secret" 字段中。
    *   确保凭据的 Scope 设置为 Global 或 Jenkinsfile 可以访问的域。

    stages {
        stage('检出代码') {
            steps {
                cleanWs() // 清理工作空间
                checkout([ // 使用Git插件和凭据检出代码
                    $class: 'GitSCM',
                    branches: [[name: '*/main']], // 或其他分支
                    userRemoteConfigs: [[
                        url: 'https://gittest.ylmo2o.com:8099/yzx/Automated-testing.git', // Git仓库URL
                        credentialsId: env.GIT_CREDENTIALS_ID // 使用Jenkins凭据
                    ]]
                ])
                echo "代码检出到 Agent 路径: ${WORKSPACE}"
                echo "对应的宿主机路径 (用于Docker挂载): ${env.HOST_WORKSPACE_PATH}"
            }
        }

        stage('准备环境') { // 创建必要的宿主机目录
            steps {
                sh """
                echo "确保宿主机上的结果和报告目录存在..."
                # 注意：这里通过运行一个临时容器来操作宿主机目录
                docker run --rm -v ${env.HOST_ALLURE_RESULTS_PATH}:/results -v ${env.HOST_ALLURE_REPORT_PATH}:/report alpine:latest sh -c 'mkdir -p /results /report && chmod -R 777 /results /report'
                echo "确保Nginx宿主机目录 ${env.ALLURE_NGINX_HOST_PATH} 存在并有权限..."
                docker run --rm -v ${env.ALLURE_NGINX_HOST_PATH}:/nginx_dir alpine:latest sh -c 'mkdir -p /nginx_dir && chmod -R 777 /nginx_dir'
                """
            }
        }
        
        stage('检查脚本文件') { // 验证CI脚本是否存在
            steps {
                sh "test -f ${WORKSPACE}/ci/scripts/run_and_notify.py && echo 'run_and_notify.py 存在' || echo 'run_and_notify.py 不存在!'"
                // ... 检查其他需要的脚本 ...
            }
        }

        stage('并行执行测试') { // 根据参数并行运行不同平台的测试
             steps {
                script {
                    def accountCredentialsId = (params.APP_ENV == 'prod') ? env.PROD_ENV_CREDENTIALS_ID : env.TEST_ENV_CREDENTIALS_ID
                    withCredentials([usernamePassword(credentialsId: accountCredentialsId, // 注入测试账号密码
                                                     usernameVariable: 'ACCOUNT_USERNAME',
                                                     passwordVariable: 'ACCOUNT_PASSWORD')]) {
                        def testsToRun = [:] // 定义并行任务

                        if (params.RUN_WEB_TESTS) {
                            testsToRun['Web测试'] = {
                                sh """
                                echo "启动Web测试容器..."
                                docker run --rm --name pytest-web-${BUILD_NUMBER} \\
                                  -e APP_ENV=${params.APP_ENV} \\
                                  -e TEST_PLATFORM="web" \\
                                  -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_USERNAME' : 'TEST_DEFAULT_USERNAME'}="\${ACCOUNT_USERNAME}" \\
                                  -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_PASSWORD' : 'TEST_DEFAULT_PASSWORD'}="\${ACCOUNT_PASSWORD}" \\
                                  # ... 其他环境变量 ...
                                  -v ${env.HOST_WORKSPACE_PATH}:/workspace:rw \\
                                  -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \\
                                  --workdir /workspace \\
                                  --network host \\
                                  ${env.DOCKER_IMAGE} \\
                                  python /workspace/ci/scripts/run_and_notify.py # 假设用脚本封装 pytest 调用
                                """
                            }
                        }
                        // ... 其他平台的测试任务 (API, Wechat, App) ...

                        if (!testsToRun.isEmpty()) {
                             parallel testsToRun // 执行并行任务
                        } else {
                             echo "没有选择任何测试平台，跳过测试执行。"
                        }
                    }
                }
            }
        }

       stage('生成报告与通知') { // 生成Allure报告、部署到Nginx、发送邮件
           steps {
                script {
                   withCredentials([string(credentialsId: env.EMAIL_PASSWORD_CREDENTIALS_ID, variable: 'EMAIL_PASSWORD')]) { // 注入邮箱密码
                       echo "写入 Allure 元数据..."
                       sh """
                       docker run --rm --name write-metadata-${BUILD_NUMBER} \\
                         # ... 环境变量 ...
                         -v ${env.HOST_WORKSPACE_PATH}:/workspace:ro \\
                         -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \\
                         ${env.DOCKER_IMAGE} \\
                         python /workspace/ci/scripts/write_allure_metadata.py /results_out
                       """

                       echo "生成 Allure 报告..."
                       sh """
                       docker run --rm --name allure-generate-${BUILD_NUMBER} \\
                         -v ${env.HOST_ALLURE_RESULTS_PATH}:/results:ro \\
                         -v ${env.HOST_ALLURE_REPORT_PATH}:/report:rw \\
                         ${env.DOCKER_IMAGE} \\
                         allure generate /results -o /report --clean
                       """

                       echo "准备并部署报告到 Nginx..."
                       # 使用辅助脚本处理历史记录、权限等
                       sh """
                       docker run --rm --name prep-nginx-${BUILD_NUMBER} \\
                         -v ${env.ALLURE_NGINX_HOST_PATH}:/nginx_dir \\
                         -v ${env.HOST_WORKSPACE_PATH}/ci/scripts:/scripts \\
                         alpine:latest sh /scripts/prepare_nginx_dir.sh /nginx_dir
                       """
                       sh """
                       docker run --rm --name deploy-report-${BUILD_NUMBER} \\
                         -v ${env.HOST_ALLURE_REPORT_PATH}:/src_report \\
                         -v ${env.ALLURE_NGINX_HOST_PATH}:/dest_nginx \\
                         -v ${env.HOST_WORKSPACE_PATH}/ci/scripts:/scripts \\
                         alpine:latest sh /scripts/deploy_allure_report.sh /src_report /dest_nginx
                       """

                       echo "发送邮件通知..."
                       sh """
                       docker run --rm --name notify-${BUILD_NUMBER} \\
                         # ... 环境变量 (包括 EMAIL_PASSWORD) ...
                         -e ALLURE_PUBLIC_URL="${env.ALLURE_PUBLIC_URL}" \\
                         -v ${env.HOST_WORKSPACE_PATH}:/workspace:ro \\
                         -v ${env.HOST_ALLURE_RESULTS_PATH}:/results:ro \\
                         -v ${env.HOST_ALLURE_REPORT_PATH}:/report:ro \\
                         ${env.DOCKER_IMAGE} \\
                         python /workspace/ci/scripts/run_and_notify.py # 假设也处理通知
                       """
                   }
                }
           }
       }
   } // End stages

   post { // 流水线完成后执行
       always {
           echo "Pipeline 完成. 清理 Agent 工作空间..."
           # 设置构建描述，包含报告链接
           script {
               # ... (代码同原 Jenkinsfile) ...
               currentBuild.description = "${params.APP_ENV.toUpperCase()} 环境 [...] - <a href='${env.ALLURE_PUBLIC_URL}' target='_blank'>查看报告</a>"
           }
           cleanWs() // 清理Agent工作区
           echo "Agent 工作空间已清理。"
       }
       // ... success / failure blocks ...
   }
}

```

**关键说明与最佳实践：**
- **DooD 宿主机路径映射**：`HOST_JENKINS_HOME_ON_HOST` 的正确设置至关重要，确保 Jenkinsfile 中 `-v` 挂载的是宿主机上的真实路径，而不是 Jenkins Agent 容器内的路径。
- **环境变量与凭据**：所有敏感信息（Git、测试账号、邮箱密码）都应通过 Jenkins 凭据管理注入，增加安全性。环境特定配置（如 URL）通过环境变量传递。
- **目录准备**：在运行测试前，通过临时 Docker 容器确保宿主机上用于存放结果、报告和 Nginx 部署的目录已创建并具有正确权限。
- **辅助脚本**：利用 `ci/scripts/` 下的脚本（如 `write_allure_metadata.py`, `prepare_nginx_dir.sh`, `deploy_allure_report.sh`, `run_and_notify.py`)封装复杂的逻辑，使 Jenkinsfile 更清晰。这些脚本在容器内执行，通过卷挂载访问所需的文件和目录。
- **Allure 报告部署**：报告生成在宿主机路径 (`HOST_ALLURE_REPORT_PATH`)，然后通过辅助脚本部署到 Nginx 的宿主机路径 (`ALLURE_NGINX_HOST_PATH`)，实现外部访问。
- **错误处理与日志**：Jenkinsfile 应包含适当的 `try/catch` 或利用 `post` 块处理失败情况，并提供清晰的日志输出 (`echo`) 帮助调试。
- **镜像复用**：构建好的 `automated-testing:dev` 镜像被多个 `docker run` 命令复用，执行不同的任务（测试、元数据写入、报告生成、通知）。

---

## 15. 常见问题FAQ

- **Q: 没有Dockerfile怎么办？**
  - A: 请在项目根目录新建Dockerfile，内容见本手册第11节。确保 `allure-2.27.0.zip` 文件存在。
- **Q: 如何保证本地和CI环境一致？**
  - A: 所有成员和CI都用同一个Dockerfile构建或拉取同一个镜像标签，避免本地依赖污染。
- **Q: 环境变量优先级如何？**
  - A: `docker run -e` > `--env-file` > 容器内.env文件。CI中通常用 `-e` 注入。
- **Q: 报告生成后Web服务无法访问？**
  - A: 检查：
    1.  `ALLURE_NGINX_HOST_PATH` 是否正确指向 Nginx 宿主机上的 Web 根目录或其子目录。
    2.  `deploy_allure_report.sh` 脚本是否成功将报告文件从 `HOST_ALLURE_REPORT_PATH` 复制到 `ALLURE_NGINX_HOST_PATH`。
    3.  Nginx 服务器配置是否正确，以及相关目录权限是否允许 Nginx 进程读取。
    4.  防火墙是否阻止了对 Nginx 端口的访问。
- **Q: Jenkins环境变量如何安全注入？**
  - A: 强烈推荐使用 Jenkins 的 "Credentials" 功能管理密码、密钥等敏感信息，并在 Jenkinsfile 中通过 `credentials()` 或 `withCredentials` 块引用。非敏感配置可通过 "Parameters" 或直接在 `environment` 块定义。
- **Q: Playwright/Allure安装慢或报错？**
  - A: 检查 Dockerfile 中是否已配置国内镜像源 (APT, pip, Poetry, Playwright download host)。网络不稳定时可尝试增加 `POETRY_REQUESTS_TIMEOUT`。
- **Q: Playwright依赖库缺失如何解决？**
  - A: 仔细核对 Dockerfile 中 `apt-get install` 命令是否包含了所有 Playwright 官方文档要求的系统依赖。
- **Q: output目录产物如何归档？**
  - A: Jenkinsfile 中可以使用 `archiveArtifacts` 步骤归档 `HOST_ALLURE_REPORT_PATH` 目录。部署到 Nginx 后通常无需再归档。
- **Q: 为什么要使用poetry run pytest而不是直接pytest？**
  - A: 确保使用的是 Poetry 管理的依赖环境，尤其是在 Dockerfile 中 `POETRY_VIRTUALENVS_CREATE=false` 时，`poetry run` 能正确找到安装的包。
- **Q: Docker 拉取镜像或构建时网络超时/无法连接？**
  - A: 核心是解决 Docker daemon 访问仓库的网络问题。**首选方案是配置并验证有效的国内镜像加速器**（详见上一版本FAQ中的详细步骤，包括 `daemon.json` 配置、验证和重启 Docker 服务）。
- **Q: Jenkins流水线在Docker容器(DooD模式)中挂载卷找不到文件/内容不正确？**
  - A: 关键在于区分 Jenkins Agent 容器内的路径 (`${WORKSPACE}`) 和宿主机上的真实路径。**必须**在 Jenkinsfile 的 `docker run` 命令中使用 `-v` 挂载**宿主机**上的路径。通过 `docker inspect <jenkins容器>` 找到宿主机路径，并在 `environment` 块中定义变量（如 `HOST_WORKSPACE_PATH`）来引用它。


---

## 16. 邮件通知集成

测试完成后自动发送邮件通知是CI/CD自动化的重要环节。本项目当前主要通过在 Jenkins 流水线中调用 Python 脚本来实现邮件发送。

### 16.1 Python脚本发送邮件 (当前项目使用方式)

项目中 `ci/scripts/run_and_notify.py` (或类似脚本) 负责在测试执行后收集结果，并根据环境变量配置调用邮件发送逻辑。通常会使用如 `yagmail` 或 `smtplib` 等库。

```python
# ci/scripts/run_and_notify.py (或相关邮件发送模块) 逻辑示意
import os
import yagmail # 假设使用 yagmail

def send_notification(allure_url):
    # 从环境变量获取邮件配置 (由 Jenkinsfile 注入)
    enabled = os.environ.get("EMAIL_ENABLED", "false").lower() == "true"
    sender = os.environ.get("EMAIL_SENDER")
    password = os.environ.get("EMAIL_PASSWORD") # 从 Jenkins 凭据注入
    recipients = os.environ.get("EMAIL_RECIPIENTS", "").split(",")
    smtp_server = os.environ.get("EMAIL_SMTP_SERVER")
    smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", 465))
    use_ssl = os.environ.get("EMAIL_USE_SSL", "true").lower() == "true"
    ci_name = os.environ.get("CI_NAME", "自动化测试")

    if not enabled or not all(sender, password, recipients, smtp_server):
        print("邮件通知未启用或配置不完整，跳过发送。")
        return

    subject = f"{ci_name} 报告"
    content = f"测试已完成，Allure 报告地址：{allure_url}"

    try:
        yag = yagmail.SMTP(user=sender, password=password, host=smtp_server, port=smtp_port, smtp_ssl=use_ssl)
        yag.send(to=[r for r in recipients if r], subject=subject, contents=content)
        print("邮件通知已发送。")
    except Exception as e:
        print(f"发送邮件失败: {e}")

# 在 run_and_notify.py 的主逻辑中调用
if __name__ == "__main__":
    # ... 执行测试 ...
    # ... 生成报告 ...
    allure_public_url = os.environ.get("ALLURE_PUBLIC_URL", "#")
    if not os.environ.get("SKIP_NOTIFY", "false").lower() == "true":
         send_notification(allure_public_url)
```

**确保 Jenkinsfile 中正确传递了以下环境变量给运行 `run_and_notify.py` 的容器：**
`EMAIL_ENABLED`, `EMAIL_SENDER`, `EMAIL_PASSWORD` (通过 `withCredentials`), `EMAIL_RECIPIENTS`, `EMAIL_SMTP_SERVER`, `EMAIL_SMTP_PORT`, `EMAIL_USE_SSL`, `ALLURE_PUBLIC_URL`, `CI_NAME`, `SKIP_NOTIFY` (可选)。


### 16.2 Jenkins Email Extension Plugin (备选方案)

Jenkins 也提供了强大的 Email Extension Plugin (`emailext`)，可以直接在 Jenkinsfile (Groovy 脚本) 中配置和发送邮件。如果你不希望通过 Python 脚本发送，可以考虑使用此插件。

```groovy
// Jenkinsfile post 块中的示例 (如果使用 emailext)
// post {
//     always {
//         script {
//             # ... 获取测试结果摘要 ...
//             def recipient_list = "user1@example.com,user2@example.com"
//             def email_subject = "测试结果: ${currentBuild.currentResult} - ${env.JOB_NAME} #${env.BUILD_NUMBER}"
//             def email_body = """
//                 <p>测试结果: ${currentBuild.currentResult}</p>
//                 <p>任务: ${env.JOB_NAME} #${env.BUILD_NUMBER}</p>
//                 <p>Allure报告: <a href="${env.ALLURE_PUBLIC_URL}">${env.ALLURE_PUBLIC_URL}</a></p>
//                 // ... 可添加更多构建信息和测试摘要 ...
//             """
//             emailext (
//                 subject: email_subject,
//                 body: email_body,
//                 to: recipient_list,
//                 mimeType: 'text/html'
//                 // ... 其他 emailext 参数，如附件、触发条件等
//             )
//         }
//     }
// }
```
**注意：** 使用 `emailext` 需要在 Jenkins 系统管理中配置好 SMTP 服务器信息，并且安装 Email Extension Plugin。

### 16.3 邮件通知最佳实践

- **只发送必要信息**：邮件内容简洁，关键测试指标和报告链接即可
- **区分通知级别**：成功和失败用不同主题，便于接收者快速识别
- **HTML格式增强可读性**：使用HTML格式，关键数据用表格呈现
- **安全保障**：邮箱账号密码通过CI平台变量/凭据管理注入
- **防止邮件轰炸**：仅在重要分支（如main、develop）构建后发送
- **便于跟踪分析**：在邮件中包含构建编号、分支/提交信息、报告链接等

---

## 变更记录
- YYYY-MM-DD: 新增 Jenkins 凭据创建指南，调整邮件通知说明以匹配项目实践，移除 emailext 示例强调 Python 脚本方式。
- YYYY-MM-DD: 更新 Dockerfile 和 Jenkinsfile 相关描述，移除 GitLab CI 示例，强化 Jenkins 集成说明和 DooD 模式下的路径映射解释。