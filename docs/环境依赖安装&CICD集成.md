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
- **强烈建议所有敏感信息和环境特定配置（如Git凭据、测试账号、API密钥、Web/API URL、Allure报告基础URL、邮件服务器配置等）都通过CI平台的凭据管理功能注入，避免写入代码、.env文件或镜像。**
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

**核心思路：** 利用Jenkins Pipeline和Docker插件（或直接调用宿主机Docker命令），实现拉取代码、构建/拉取环境镜像、在Docker容器中运行测试、生成报告并部署的全自动化流程。特别注意在Docker-outside-of-Docker (DooD) 模式下宿主机路径的正确映射。**所有敏感配置（账户、URL、邮件设置等）均通过 Jenkins 凭据管理，并动态注入到流水线中。报告生成和通知步骤被移至 `post { always { ... } }` 块，以确保无论测试成功与否都会执行。**

**Jenkinsfile关键部分示例 (参考项目根目录的 `Jenkinsfile`)**

```groovy
pipeline {
    agent any // 或指定特定的agent标签

    parameters { // 定义构建参数，增加灵活性
        choice(name: 'APP_ENV', choices: ['test', 'prod'], description: '选择测试环境')
        booleanParam(name: 'RUN_WEB_TESTS', defaultValue: true, description: '运行Web测试')
        booleanParam(name: 'RUN_API_TESTS', defaultValue: true, description: '运行API测试')
        booleanParam(name: 'RUN_WECHAT_TESTS', defaultValue: false, description: '运行微信公众号测试')
        booleanParam(name: 'RUN_APP_TESTS', defaultValue: false, description: '运行App测试')
        choice(name: 'TEST_SUITE', choices: ['全部', '冒烟测试', '回归测试'], description: '选择测试套件')
        booleanParam(name: 'SEND_EMAIL', defaultValue: true, description: '是否发送邮件通知')
    }

    environment {
        // --- 凭据 ID (在Jenkins中预先创建) ---
        GIT_CREDENTIALS_ID = 'git-credentials'          // Git 认证凭据 (Username/Password 或 SSH Key)
        GIT_REPO_URL_CREDENTIAL_ID = 'git-repo-url'     // Git 仓库 URL (Secret text)
        TEST_ENV_CREDENTIALS_ID = 'test-env-credentials'// 测试环境账户 (Username with password)
        PROD_ENV_CREDENTIALS_ID = 'prod-env-credentials'// 生产环境账户 (Username with password)
        TEST_WEB_URL_CREDENTIAL_ID = 'test-web-url'     // 测试环境 Web URL (Secret text)
        TEST_API_URL_CREDENTIAL_ID = 'test-api-url'     // 测试环境 API URL (Secret text)
        PROD_WEB_URL_CREDENTIAL_ID = 'prod-web-url'     // 生产环境 Web URL (Secret text)
        PROD_API_URL_CREDENTIAL_ID = 'prod-api-url'     // 生产环境 API URL (Secret text)
        ALLURE_BASE_URL_CREDENTIAL_ID = 'allure-base-url' // Allure 报告基础 URL (Secret text)
        EMAIL_PASSWORD_CREDENTIALS_ID = 'email-password-credential' // 邮件发件人密码/授权码 (Secret text)
        EMAIL_SMTP_SERVER_CREDENTIAL_ID = 'email-smtp-server'       // SMTP 服务器地址 (Secret text)
        EMAIL_SMTP_PORT_CREDENTIAL_ID = 'email-smtp-port'           // SMTP 端口 (Secret text)
        EMAIL_SENDER_CREDENTIAL_ID = 'email-sender'                 // 发件人邮箱地址 (Secret text)
        EMAIL_RECIPIENTS_CREDENTIAL_ID = 'email-recipients'         // 收件人列表 (Secret text, 逗号分隔)
        EMAIL_USE_SSL_CREDENTIAL_ID = 'email-use-ssl'               // 是否使用 SSL (Secret text, 'true' or 'false')

        // --- Allure 报告相关 (Nginx 宿主机路径) ---
        ALLURE_NGINX_DIR_NAME = "${params.APP_ENV == 'prod' ? 'allure-report-prod' : 'allure-report-test'}"
        // ALLURE_PUBLIC_URL 将在 post 块中动态构建
        ALLURE_NGINX_HOST_PATH = "/usr/share/nginx/html/${ALLURE_NGINX_DIR_NAME}" // Nginx 在宿主机上的路径

        // --- Docker Agent & 宿主机路径映射 (DooD模式关键) ---
        // !! 重要：此路径需要根据实际Jenkins Docker容器挂载情况确定 !!
        HOST_JENKINS_HOME_ON_HOST = '/var/lib/docker/volumes/jenkins_home/_data'
        // 基于宿主机Jenkins Home计算出宿主机上的工作区、结果、报告路径
        HOST_WORKSPACE_PATH = "${HOST_JENKINS_HOME_ON_HOST}/workspace/${env.JOB_NAME}"
        HOST_ALLURE_RESULTS_PATH = "${HOST_WORKSPACE_PATH}/output/allure-results"
        HOST_ALLURE_REPORT_PATH = "${HOST_WORKSPACE_PATH}/output/reports/allure-report"

        // --- 测试相关 ---
        TEST_SUITE_VALUE = "${params.TEST_SUITE == '全部' ? 'all' : (params.TEST_SUITE == '冒烟测试' ? 'smoke' : 'regression')}"
        DOCKER_IMAGE = "automated-testing:dev" // 使用的测试环境镜像
    }

    // --- Jenkins 凭据创建指南 (更新版) ---
    #### Jenkins 凭据创建指南

    为了让 Jenkinsfile 能够安全地访问 Git 仓库、测试环境账号、URL配置和邮箱服务，你需要在 Jenkins 系统中预先创建以下凭据。请确保凭据 ID 与 Jenkinsfile 中 `environment` 块定义的完全一致。

    **创建步骤（在 Jenkins UI 中操作）：**

    1.  登录 Jenkins。
    2.  导航到 "Manage Jenkins" -> "Credentials"。
    3.  在 "Stores scoped to Jenkins" 下，点击 "System" 域（或你选择的其他域）下的 "Global credentials (unrestricted)"。
    4.  点击左侧菜单的 "Add Credentials"。
    5.  根据下表创建凭据：

        | Jenkinsfile中的凭据ID             | 类型 (Kind)            | ID (必须与左侧一致)                | Scope  | Username (用户名)       | Password / Secret (密码/令牌/文本) | Description (描述)                   |
        | :-------------------------------- | :--------------------- | :------------------------------- | :----- | :---------------------- | :------------------------------- | :----------------------------------- |
        | `git-credentials`                 | Username with password | `git-credentials`                | Global | 你的 Git 用户名           | 你的 Git 密码/令牌             | Git 仓库访问凭据                     |
        | `git-repo-url`                    | Secret text            | `git-repo-url`                   | Global |                         | 你的 Git 仓库 URL (e.g., https://...) | Git 仓库 URL                       |
        | `test-env-credentials`            | Username with password | `test-env-credentials`           | Global | 测试环境用户名         | 测试环境密码                 | 测试环境账号密码                   |
        | `prod-env-credentials`            | Username with password | `prod-env-credentials`           | Global | 生产环境用户名         | 生产环境密码                 | 生产环境账号密码                   |
        | `test-web-url`                    | Secret text            | `test-web-url`                   | Global |                         | 测试环境 Web URL (完整路径)      | 测试环境 Web URL                    |
        | `test-api-url`                    | Secret text            | `test-api-url`                   | Global |                         | 测试环境 API URL (完整路径)      | 测试环境 API URL                    |
        | `prod-web-url`                    | Secret text            | `prod-web-url`                   | Global |                         | 生产环境 Web URL (完整路径)      | 生产环境 Web URL                    |
        | `prod-api-url`                    | Secret text            | `prod-api-url`                   | Global |                         | 生产环境 API URL (完整路径)      | 生产环境 API URL                    |
        | `allure-base-url`                 | Secret text            | `allure-base-url`                | Global |                         | Allure 报告基础 URL (e.g., http://ip:port) | Allure 报告基础 URL                  |
        | `email-password-credential`       | Secret text            | `email-password-credential`      | Global |                         | 你的发件邮箱密码或授权码          | 邮件通知发件人密码/授权码            |
        | `email-smtp-server`               | Secret text            | `email-smtp-server`              | Global |                         | 你的 SMTP 服务器地址              | 邮件 SMTP 服务器地址                 |
        | `email-smtp-port`                 | Secret text            | `email-smtp-port`                | Global |                         | 你的 SMTP 端口 (e.g., 465)       | 邮件 SMTP 端口                      |
        | `email-sender`                    | Secret text            | `email-sender`                   | Global |                         | 你的发件人邮箱地址             | 邮件发件人邮箱地址                  |
        | `email-recipients`                | Secret text            | `email-recipients`               | Global |                         | 收件人邮箱列表 (逗号分隔)        | 邮件收件人列表 (逗号分隔)          |
        | `email-use-ssl`                   | Secret text            | `email-use-ssl`                  | Global |                         | 'true' 或 'false'               | 邮件是否使用 SSL                    |

    **注意事项：**

    *   **ID 必须精确匹配** Jenkinsfile 中的定义。
    *   对于 `git-credentials`，如果使用 SSH 密钥，需创建 "SSH Username with private key" 类型。
    *   对于 `Secret text` 类型的凭据，将对应的值粘贴到 "Secret" 字段中。
    *   `email-recipients` 的值可以是单个邮箱，也可以是多个邮箱地址，用英文逗号 `,` 分隔。
    *   确保凭据的 Scope 设置为 Global 或 Jenkinsfile 可以访问的域。

    stages {
        stage('检出代码') {
            steps {
                // --- 使用 withCredentials 注入 Git URL 和认证凭据 ---
                withCredentials([
                    string(credentialsId: env.GIT_REPO_URL_CREDENTIAL_ID, variable: 'INJECTED_GIT_REPO_URL'),
                    usernamePassword(credentialsId: env.GIT_CREDENTIALS_ID, usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD') // 或者使用 SSH Key 凭据类型
                ]) {
                    echo "从代码仓库拉取最新代码: ${INJECTED_GIT_REPO_URL}"
                    cleanWs()
                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: '*/main']],
                        userRemoteConfigs: [[
                            url: INJECTED_GIT_REPO_URL, // <-- 使用注入的变量
                            credentialsId: env.GIT_CREDENTIALS_ID // <-- 认证凭据保持不变
                        ]]
                    ])
                }
                echo "代码检出完成到 Agent 路径: ${WORKSPACE}"
                echo "对应的宿主机路径是: ${env.HOST_WORKSPACE_PATH}"
                sh "echo '>>> Jenkins Agent Workspace Contents:' && ls -la ${WORKSPACE}"
            }
        }

        stage('准备环境') { // 创建必要的宿主机目录
            steps {
                echo "准备测试环境和目录 (在 Agent 上)..."
                sh """
                mkdir -p ${WORKSPACE}/output/allure-results
                mkdir -p ${WORKSPACE}/output/reports/allure-report
                echo "清空旧的 allure-results (在 Agent 上)..."
                rm -rf ${WORKSPACE}/output/allure-results/*

                echo "确保 Nginx 目录 ${env.ALLURE_NGINX_HOST_PATH} (在宿主机上) 存在并设置权限..."
                docker run --rm -v ${env.ALLURE_NGINX_HOST_PATH}:/nginx_dir_on_host --user root alpine:latest sh -c "mkdir -p /nginx_dir_on_host && chmod -R 777 /nginx_dir_on_host"

                echo "环境准备完成。"
                """
            }
        }

        stage('检查脚本文件') { // 验证CI脚本是否存在
            steps {
                echo "检查脚本文件是否存在于 Agent 路径: ${WORKSPACE}/ci/scripts/ ..."
                sh "ls -la ${WORKSPACE}/ci/scripts/ || echo '>>> ci/scripts/ 目录不存在或无法列出 <<<' "
                sh "test -f ${WORKSPACE}/ci/scripts/write_allure_metadata.py && echo '>>> write_allure_metadata.py 存在于 Agent <<< ' || echo '>>> write_allure_metadata.py 不存在于 Agent! <<<' "
                sh "test -f ${WORKSPACE}/ci/scripts/prepare_nginx_dir.sh && echo '>>> prepare_nginx_dir.sh 存在于 Agent <<< ' || echo '>>> prepare_nginx_dir.sh 不存在于 Agent! <<<' "
                sh "test -f ${WORKSPACE}/ci/scripts/deploy_allure_report.sh && echo '>>> deploy_allure_report.sh 存在于 Agent <<< ' || echo '>>> deploy_allure_report.sh 不存在于 Agent! <<<' "
            }
        }

        stage('并行执行测试') { // 根据参数并行运行不同平台的测试
             steps {
                script {
                    // --- 动态选择凭据 ID ---
                    def accountCredentialsId = (params.APP_ENV == 'prod') ? env.PROD_ENV_CREDENTIALS_ID : env.TEST_ENV_CREDENTIALS_ID
                    def webUrlCredentialId = (params.APP_ENV == 'prod') ? env.PROD_WEB_URL_CREDENTIAL_ID : env.TEST_WEB_URL_CREDENTIAL_ID
                    def apiUrlCredentialId = (params.APP_ENV == 'prod') ? env.PROD_API_URL_CREDENTIAL_ID : env.TEST_API_URL_CREDENTIAL_ID
                    echo "选择凭据 ID: 账户=${accountCredentialsId}, WebURL=${webUrlCredentialId}, APIURL=${apiUrlCredentialId}"

                    // --- 捕获测试阶段的错误，但不让它停止 Pipeline ---
                    try {
                        // --- 注入账户和 URL 凭据 ---
                        withCredentials([
                            usernamePassword(credentialsId: accountCredentialsId, usernameVariable: 'ACCOUNT_USERNAME', passwordVariable: 'ACCOUNT_PASSWORD'),
                            string(credentialsId: webUrlCredentialId, variable: 'INJECTED_WEB_URL'),
                            string(credentialsId: apiUrlCredentialId, variable: 'INJECTED_API_URL')
                        ]) {
                            def testsToRun = [:] // 定义并行任务

                            if (params.RUN_WEB_TESTS) {
                                testsToRun['Web测试'] = {
                                    echo "执行Web测试 (并发: auto, 重试: 2)"
                                    // --- 使用注入的 WEB_BASE_URL ---
                                    sh """
                                    docker run --rm --name pytest-web-${BUILD_NUMBER} \\
                                      -e APP_ENV=${params.APP_ENV} \\
                                      -e TEST_PLATFORM="web" \\
                                      -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_USERNAME' : 'TEST_DEFAULT_USERNAME'}="${ACCOUNT_USERNAME}" \\
                                      -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_PASSWORD' : 'TEST_DEFAULT_PASSWORD'}="${ACCOUNT_PASSWORD}" \\
                                      -e TEST_SUITE="${env.TEST_SUITE_VALUE}" \\
                                      -e WEB_BASE_URL="${INJECTED_WEB_URL}" \\
                                      -e TZ="Asia/Shanghai" \\
                                      -v ${env.HOST_WORKSPACE_PATH}:/workspace:rw \\
                                      -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \\
                                      --workdir /workspace \\
                                      -v /etc/localtime:/etc/localtime:ro \\
                                      --network host \\
                                      ${env.DOCKER_IMAGE} \\
                                      pytest tests/web -n auto --reruns 2 -v --alluredir=/results_out
                                    """
                                }
                            } else { echo "跳过Web测试" }

                            if (params.RUN_API_TESTS) {
                                testsToRun['API测试'] = {
                                    echo "执行API测试 (并发: auto, 重试: 2)"
                                    // --- 使用注入的 API_BASE_URL ---
                                    sh """
                                    docker run --rm --name pytest-api-${BUILD_NUMBER} \\
                                      -e APP_ENV=${params.APP_ENV} \\
                                      -e TEST_PLATFORM="api" \\
                                      -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_USERNAME' : 'TEST_DEFAULT_USERNAME'}="${ACCOUNT_USERNAME}" \\
                                      -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_PASSWORD' : 'TEST_DEFAULT_PASSWORD'}="${ACCOUNT_PASSWORD}" \\
                                      -e TEST_SUITE="${env.TEST_SUITE_VALUE}" \\
                                      -e API_BASE_URL="${INJECTED_API_URL}" \\
                                      -e TZ="Asia/Shanghai" \\
                                      -v ${env.HOST_WORKSPACE_PATH}:/workspace:rw \\
                                      -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \\
                                      --workdir /workspace \\
                                      -v /etc/localtime:/etc/localtime:ro \\
                                      --network host \\
                                      ${env.DOCKER_IMAGE} \\
                                      pytest tests/api -n auto --reruns 2 -v --alluredir=/results_out
                                    """
                                }
                            } else { echo "跳过API测试" }

                            // ... 其他平台的测试任务 (Wechat, App) 类似地使用注入的凭据 ...

                            if (!testsToRun.isEmpty()) {
                                 echo "开始并行执行选定的测试 (使用宿主机路径 ${env.HOST_WORKSPACE_PATH} 挂载到容器 /workspace)..."
                                 parallel testsToRun // 执行并行任务
                            } else {
                                 echo "没有选择任何测试平台，跳过测试执行。"
                                 // 确保宿主机上的结果目录存在，即使没有测试运行
                                 sh "mkdir -p ${env.HOST_ALLURE_RESULTS_PATH}"
                            }
                        } // End inner withCredentials
                    } catch (err) {
                        echo "测试阶段出现错误: ${err}. 将继续执行报告生成和通知。"
                        // 可以选择将构建标记为不稳定
                        // currentBuild.result = 'UNSTABLE'
                    }
                } // End script
            } // End steps
        } // End stage '并行执行测试'

       // --- '生成报告与通知' Stage 已被移动到 post 块 ---

   } // End stages

   post { // 流水线完成后执行
       always {
           // --- 将报告生成和通知逻辑移动到这里 ---
           echo "Pipeline 完成. 开始执行报告生成和通知步骤 (无论测试是否成功)..."
           script {
               // 定义将在内部使用的完整 Allure URL 变量
               def final_allure_public_url = ""
               // 使用 try/catch 块来捕获可能的错误，确保后续清理能执行
               try {
                   // --- 注入所有需要的凭据，包括邮件配置 ---
                   withCredentials([
                       string(credentialsId: env.EMAIL_PASSWORD_CREDENTIALS_ID, variable: 'INJECTED_EMAIL_PASSWORD'),
                       string(credentialsId: env.ALLURE_BASE_URL_CREDENTIAL_ID, variable: 'INJECTED_ALLURE_BASE_URL'),
                       string(credentialsId: env.EMAIL_SMTP_SERVER_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_SMTP_SERVER'),
                       string(credentialsId: env.EMAIL_SMTP_PORT_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_SMTP_PORT'),
                       string(credentialsId: env.EMAIL_SENDER_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_SENDER'),
                       string(credentialsId: env.EMAIL_RECIPIENTS_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_RECIPIENTS'),
                       string(credentialsId: env.EMAIL_USE_SSL_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_USE_SSL')
                   ]) {
                       // --- 动态构建完整的 Allure URL ---
                       // 确保基础 URL 后有斜杠
                       def baseUrl = INJECTED_ALLURE_BASE_URL.endsWith('/') ? INJECTED_ALLURE_BASE_URL : INJECTED_ALLURE_BASE_URL + '/'
                       final_allure_public_url = "${baseUrl}${env.ALLURE_NGINX_DIR_NAME}/"
                       echo "构建的 Allure 公共 URL: ${final_allure_public_url}"

                       echo "写入 Allure 元数据文件到 ${env.HOST_ALLURE_RESULTS_PATH} (在宿主机上)..."
                       sh """
                       docker run --rm --name write-metadata-${BUILD_NUMBER} -e APP_ENV=${params.APP_ENV} -e BUILD_NUMBER=${BUILD_NUMBER} -e BUILD_URL=${env.BUILD_URL} -e JOB_NAME=${env.JOB_NAME} -v ${env.HOST_WORKSPACE_PATH}:/workspace:ro -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw -v /etc/localtime:/etc/localtime:ro --user root ${env.DOCKER_IMAGE} python /workspace/ci/scripts/write_allure_metadata.py /results_out
                       """
                       echo "Allure 元数据写入完成。"

                       echo "开始生成 Allure 报告 (从宿主机路径 ${env.HOST_ALLURE_RESULTS_PATH} 生成到 ${env.HOST_ALLURE_REPORT_PATH})..."
                       sh """
                       docker run --rm --name allure-generate-${BUILD_NUMBER} \\
                         -v ${env.HOST_ALLURE_RESULTS_PATH}:/results:ro \\
                         -v ${env.HOST_ALLURE_REPORT_PATH}:/report:rw \\
                         -v /etc/localtime:/etc/localtime:ro \\
                         --user root \\
                         ${env.DOCKER_IMAGE} \\
                         /bin/bash -c "echo 'Generating report...'; ls -la /results || echo 'Results dir not found'; allure generate /results -o /report --clean || echo 'Allure generate command failed'"
                       echo "Allure 报告已生成到宿主机路径: ${env.HOST_ALLURE_REPORT_PATH}"
                       """

                       echo "准备 Nginx 目录 ${env.ALLURE_NGINX_HOST_PATH} (在宿主机上)..."
                       sh """
                       docker run --rm --name prep-nginx-dir-${BUILD_NUMBER} \\
                         -v ${env.ALLURE_NGINX_HOST_PATH}:/nginx_dir_on_host:rw \\
                         -v ${env.HOST_WORKSPACE_PATH}/ci/scripts:/scripts:ro \\
                         --user root \\
                         alpine:latest \\
                         sh /scripts/prepare_nginx_dir.sh /nginx_dir_on_host
                       """

                       echo "部署 Allure 报告 (从宿主机 ${env.HOST_ALLURE_REPORT_PATH} 到 Nginx 宿主机 ${env.ALLURE_NGINX_HOST_PATH})..."
                       sh """
                       docker run --rm --name deploy-report-${BUILD_NUMBER} \\
                         -v ${env.HOST_ALLURE_REPORT_PATH}:/src_report:ro \\
                         -v ${env.ALLURE_NGINX_HOST_PATH}:/dest_nginx:rw \\
                         -v ${env.HOST_WORKSPACE_PATH}/ci/scripts:/scripts:ro \\
                         --user root \\
                         alpine:latest \\
                         sh /scripts/deploy_allure_report.sh /src_report /dest_nginx
                       """
                       echo "报告已部署到 Nginx 目录。"

                       echo "发送邮件通知..."
                       // --- 使用注入的邮件配置变量 ---
                       sh """
                       echo "--- Sending notification email via run_and_notify.py --- (using host path ${env.HOST_WORKSPACE_PATH})"
                       docker run --rm --name notify-${BUILD_NUMBER} \\
                         -e CI=true \\
                         -e APP_ENV=${params.APP_ENV} \\
                         -e EMAIL_ENABLED=${params.SEND_EMAIL} \\
                         -e EMAIL_PASSWORD='${INJECTED_EMAIL_PASSWORD}' \\
                         -e EMAIL_SMTP_SERVER="${INJECTED_EMAIL_SMTP_SERVER}" \\
                         -e EMAIL_SMTP_PORT=${INJECTED_EMAIL_SMTP_PORT} \\
                         -e EMAIL_SENDER="${INJECTED_EMAIL_SENDER}" \\
                         -e EMAIL_RECIPIENTS="${INJECTED_EMAIL_RECIPIENTS}" \\
                         -e EMAIL_USE_SSL=${INJECTED_EMAIL_USE_SSL} \\
                         -e ALLURE_PUBLIC_URL="${final_allure_public_url}" \\
                         -e TZ="Asia/Shanghai" \\
                         -e ALLURE_RESULTS_DIR=/results \\
                         -e ALLURE_REPORT_DIR=/report \\
                         -e SKIP_REPORT_GENERATION=true \\
                         -e SKIP_TEST_EXECUTION=true \\
                         -v ${env.HOST_WORKSPACE_PATH}:/workspace:rw \\
                         -v ${env.HOST_ALLURE_RESULTS_PATH}:/results:ro \\
                         -v ${env.HOST_ALLURE_REPORT_PATH}:/report:ro \\
                         -v /etc/localtime:/etc/localtime:ro \\
                         --network host \\
                         ${env.DOCKER_IMAGE} \\
                         /bin/bash -c "cd /workspace && python ci/scripts/run_and_notify.py"
                       echo "通知脚本执行完毕。"
                       """
                   } // End withCredentials
               } catch (err) {
                   echo "报告生成或通知阶段出现错误: ${err}"
                   // 即使这里出错，我们仍然希望执行清理
               }

               // --- 设置构建描述 (使用动态构建的 URL) ---
               def testTypes = []
               if (params.RUN_WEB_TESTS) testTypes.add("Web")
               if (params.RUN_API_TESTS) testTypes.add("API")
               if (params.RUN_WECHAT_TESTS) testTypes.add("微信")
               if (params.RUN_APP_TESTS) testTypes.add("App")
               if (testTypes.isEmpty()) testTypes.add("未选择")
               // 根据 currentBuild.currentResult 判断最终状态
               def finalStatus = currentBuild.currentResult ?: 'SUCCESS' // 如果没有被明确设置失败/不稳定，则假定为成功
               // 使用 final_allure_public_url，如果为空则提供提示
               def reportLink = final_allure_public_url ? "<a href='${final_allure_public_url}' target='_blank'>查看报告</a>" : "(报告URL未生成)"
               currentBuild.description = "${params.APP_ENV.toUpperCase()} 环境 [${testTypes.join(', ')}] - ${finalStatus} - ${reportLink}"
           } // End script

           // --- 清理工作空间 ---
           echo "清理 Agent 工作空间 ${WORKSPACE}..."
           cleanWs()
           echo "Agent 工作空间已清理。"
       } // End always
       success {
           echo "Pipeline 最终状态: 成功 (即使测试阶段可能失败)"
       }
       failure {
           // 注意：如果测试失败，但报告生成成功，最终状态可能是FAILURE，
           // 这取决于测试阶段是否显式设置了 currentBuild.result
           echo "Pipeline 最终状态: 失败 (可能在测试阶段或报告/通知阶段失败)"
       }
       unstable {
           echo "Pipeline 最终状态: 不稳定 (可能在测试阶段标记为不稳定)"
       }
   } // End post
} // End pipeline
```

**关键说明与最佳实践：**

*   **DooD 宿主机路径映射**：`HOST_JENKINS_HOME_ON_HOST` 的正确设置至关重要，确保 Jenkinsfile 中 `-v` 挂载的是宿主机上的真实路径。
*   **凭据管理**：所有敏感信息和环境特定配置（Git、账户、URL、邮件设置）都通过 Jenkins 凭据管理注入，提高安全性和灵活性。
*   **动态配置**：Web/API URL 根据 `APP_ENV` 参数动态选择；Allure 公共 URL 根据注入的基础 URL 动态构建。
*   **强制执行报告/通知**：通过将逻辑移至 `post { always { ... } }` 并捕获测试阶段的错误，确保报告和通知总会尝试执行。
*   **辅助脚本**：利用 `ci/scripts/` 下的脚本封装复杂逻辑，保持 Jenkinsfile 清晰。

---

## 15. 常见问题FAQ

*   **Q: 没有Dockerfile怎么办？**
    *   A: 请在项目根目录新建Dockerfile，内容见本手册第11节。确保 `allure-2.27.0.zip` 文件存在。
*   **Q: 如何保证本地和CI环境一致？**
    *   A: 所有成员和CI都用同一个Dockerfile构建或拉取同一个镜像标签，避免本地依赖污染。
*   **Q: 环境变量优先级如何？**
    *   A: `docker run -e` > `--env-file` > 容器内.env文件。CI中通常用 `-e` 注入，但现在推荐通过 `withCredentials` 注入敏感信息。
*   **Q: 报告生成后Web服务无法访问？**
    *   A: 检查：
        1.  `ALLURE_NGINX_HOST_PATH` 是否正确指向 Nginx 宿主机上的 Web 根目录或其子目录。
        2.  `deploy_allure_report.sh` 脚本是否成功将报告文件从 `HOST_ALLURE_REPORT_PATH` 复制到 `ALLURE_NGINX_HOST_PATH`。
        3.  Nginx 服务器配置是否正确，以及相关目录权限是否允许 Nginx 进程读取。
        4.  防火墙是否阻止了对 Nginx 端口的访问。
*   **Q: Jenkins环境变量/凭据如何安全注入？**
    *   A: **强烈推荐**使用 Jenkins 的 "Credentials" 功能管理所有密码、密钥、URL、邮件服务器等配置信息，并在 Jenkinsfile 中通过 `withCredentials` 块按需注入。避免在 `environment` 块中硬编码任何敏感或易变信息。
*   **Q: Playwright/Allure安装慢或报错？**
    *   A: 检查 Dockerfile 中是否已配置国内镜像源 (APT, pip, Poetry, Playwright download host)。网络不稳定时可尝试增加 `POETRY_REQUESTS_TIMEOUT`。
*   **Q: Playwright依赖库缺失如何解决？**
    *   A: 仔细核对 Dockerfile 中 `apt-get install` 命令是否包含了所有 Playwright 官方文档要求的系统依赖。
*   **Q: output目录产物如何归档？**
    *   A: Jenkinsfile 中可以使用 `archiveArtifacts` 步骤归档 `HOST_ALLURE_REPORT_PATH` 目录。部署到 Nginx 后通常无需再归档。
*   **Q: 为什么要使用pytest而不是直接pytest？** (原文如此，应为 `poetry run pytest`)
    *   A: 确保使用的是 Poetry 管理的依赖环境，尤其是在 Dockerfile 中 `POETRY_VIRTUALENVS_CREATE=false` 时，`poetry run` 能正确找到安装的包。
*   **Q: Docker 拉取镜像或构建时网络超时/无法连接？**
    *   A: 核心是解决 Docker daemon 访问仓库的网络问题。**首选方案是配置并验证有效的国内镜像加速器**（详见本手册FAQ中的详细步骤，包括 `daemon.json` 配置、验证和重启 Docker 服务）。
*   **Q: Jenkins流水线在Docker容器(DooD模式)中挂载卷找不到文件/内容不正确？**
    *   A: 关键在于区分 Jenkins Agent 容器内的路径 (`${WORKSPACE}`) 和宿主机上的真实路径。**必须**在 Jenkinsfile 的 `docker run` 命令中使用 `-v` 挂载**宿主机**上的路径。通过 `docker inspect <jenkins容器>` 找到宿主机路径，并在 `environment` 块中定义变量（如 `HOST_WORKSPACE_PATH`）来引用它。

---

## 16. 邮件通知集成

测试完成后自动发送邮件通知是CI/CD自动化的重要环节。本项目当前主要通过在 Jenkins 流水线中调用 Python 脚本来实现邮件发送。

### 16.1 Python脚本发送邮件 (当前项目使用方式)

项目中 `ci/scripts/run_and_notify.py` 负责在测试执行后收集结果，并根据环境变量配置调用邮件发送逻辑。**强烈推荐**将所有邮件配置（SMTP服务器、端口、发件人、密码/授权码、收件人、SSL设置）通过 Jenkins 凭据管理，并在 Jenkinsfile 中使用 `withCredentials` 将这些凭据注入到运行该脚本的容器的环境变量中。

```python
# ci/scripts/run_and_notify.py (或相关邮件发送模块) 逻辑示意
import os
# 假设使用 yagmail 或类似库，或者项目内封装的 src.utils.email_notifier
# from src.utils.email_notifier import EmailNotifier

def send_notification(allure_url, summary): # 假设 summary 也被传入
    # --- 从环境变量获取邮件配置 (由 Jenkinsfile 通过凭据注入) ---
    enabled = os.environ.get("EMAIL_ENABLED", "false").lower() == "true"
    sender = os.environ.get("EMAIL_SENDER")          # 从凭据注入
    password = os.environ.get("EMAIL_PASSWORD")        # 从凭据注入
    recipients_str = os.environ.get("EMAIL_RECIPIENTS", "") # 从凭据注入
    smtp_server = os.environ.get("EMAIL_SMTP_SERVER")  # 从凭据注入
    smtp_port_str = os.environ.get("EMAIL_SMTP_PORT")    # 从凭据注入
    use_ssl_str = os.environ.get("EMAIL_USE_SSL")      # 从凭据注入

    # 检查必要配置是否存在
    if not all([enabled, sender, password, recipients_str, smtp_server, smtp_port_str, use_ssl_str]):
        print("邮件通知未启用或必要配置缺失 (来自凭据)，跳过发送。")
        return

    # 解析配置
    recipients = [email.strip() for email in recipients_str.split(",") if email.strip()]
    try:
        smtp_port = int(smtp_port_str)
    except ValueError:
        print(f"无效的 SMTP 端口号: {smtp_port_str}，跳过邮件发送。")
        return
    use_ssl = use_ssl_str.lower() == 'true'

    if not recipients:
        print("收件人列表为空，跳过邮件发送。")
        return

    # 准备邮件内容 (使用传入的 summary 和 allure_url)
    subject = f"【自动化测试】{os.environ.get('APP_ENV', '未知').upper()} 环境报告 [{time.strftime('%Y-%m-%d %H:%M:%S')}]"
    # ... 构建 HTML 正文 (如之前示例) ...
    html_body = f"<html><body>测试摘要: {summary} <br/> 报告链接: <a href='{allure_url}'>点击查看</a></body></html>" # 简化示例

    # 发送邮件 (使用项目工具或库)
    try:
        # 假设使用项目中的 EmailNotifier
        # notifier = EmailNotifier(smtp_server, smtp_port, sender, password, use_ssl=use_ssl)
        # notifier.send_html(subject, html_body, recipients)

        # 或者使用 yagmail
        # import yagmail
        # yag = yagmail.SMTP(user=sender, password=password, host=smtp_server, port=smtp_port, smtp_ssl=use_ssl)
        # yag.send(to=recipients, subject=subject, contents=html_body)

        print(f"邮件通知已尝试发送给: {', '.join(recipients)}")
    except Exception as e:
        print(f"发送邮件失败: {e}")

# 在 run_and_notify.py 的主逻辑中调用
# if __name__ == "__main__":
#     # ... 获取测试摘要 summary ...
#     allure_public_url = os.environ.get("ALLURE_PUBLIC_URL", "#")
#     # 确保 SKIP_TEST_EXECUTION=true 时也能获取到 summary
#     send_notification(allure_public_url, summary)

```

**确保 Jenkinsfile 中在 `post { always { ... } }` 块的 `withCredentials` 中注入了所有必要的邮件环境变量给运行 `run_and_notify.py` 的容器：**
`EMAIL_ENABLED`, `EMAIL_PASSWORD`, `EMAIL_SMTP_SERVER`, `EMAIL_SMTP_PORT`, `EMAIL_SENDER`, `EMAIL_RECIPIENTS`, `EMAIL_USE_SSL`, `ALLURE_PUBLIC_URL`。

### 16.2 Jenkins Email Extension Plugin (备选方案)
// ... 这部分保持不变 ...

### 16.3 邮件通知最佳实践
// ... 这部分保持不变 ...

---

## 变更记录
- YYYY-MM-DD: **重大更新**: 将 Web/API URL、Allure 基础 URL、Git 仓库 URL 及所有邮件配置参数化到 Jenkins 凭据。更新了 Jenkins 凭据创建指南和 Jenkinsfile 示例以反映这些变化。将报告生成和通知逻辑移至 `post { always }` 块以强制执行。
- YYYY-MM-DD: 新增 Jenkins 凭据创建指南，调整邮件通知说明以匹配项目实践，移除 emailext 示例强调 Python 脚本方式。
- YYYY-MM-DD: 更新 Dockerfile 和 Jenkinsfile 相关描述，移除 GitLab CI 示例，强化 Jenkins 集成说明和 DooD 模式下的路径映射解释。