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
- output/allure-results和output/allure-report目录分别用于存放测试结果和HTML报告，output目录已在.gitignore中全局忽略，避免无用文件提交。

---

## 8. 运行自动化测试与报告生成
- 运行测试：
  ```bash
  poetry run pytest --alluredir=output/allure-results
  ```
- 推荐用`poetry run pytest`保证依赖环境一致，避免直接用`pytest`导致依赖找不到。
- 生成HTML报告：
  ```bash
  allure generate output/allure-results -o output/allure-report --clean
  ```
- 本地预览报告：
  ```bash
  allure open output/allure-report
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
- Dockerfile标准写法（项目根目录）：
  ```dockerfile
  FROM python:3.11-slim

  WORKDIR /app
  COPY . /app

  # 切换为国内阿里云APT源，加速依赖安装（确保文件存在）
  RUN if [ -f /etc/apt/sources.list ]; then \
        sed -i 's@http://deb.debian.org@https://mirrors.aliyun.com/debian@g' /etc/apt/sources.list && \
        sed -i 's@http://security.debian.org@https://mirrors.aliyun.com/debian-security@g' /etc/apt/sources.list; \
      fi

  # 安装 Playwright 依赖库和常用工具
  RUN apt-get update && apt-get install -y --no-install-recommends \
      wget openjdk-17-jre-headless unzip \
      libglib2.0-0 libnss3 libnspr4 \
      libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libexpat1 \
      libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 \
      libxcb1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 \
      fonts-liberation libappindicator3-1 lsb-release \
      && apt-get clean && rm -rf /var/lib/apt/lists/*

  # 配置pip多源兜底
  RUN mkdir -p /root/.pip && \
      echo "[global]" > /root/.pip/pip.conf && \
      echo "index-url = https://mirrors.aliyun.com/pypi/simple/" >> /root/.pip/pip.conf

  # 升级pip并安装poetry
  RUN pip install --upgrade pip \
      && pip install "poetry>=1.5.0"

  # 安装项目依赖
  RUN poetry install

  # playwright浏览器下载加速
  ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright

  # 安装playwright及其浏览器
  RUN pip install playwright && playwright install

  CMD ["bash", "-c", "poetry run pytest --alluredir=output/allure-results && allure generate output/allure-results -o output/allure-report --clean"]
  ```
- 本地构建与运行：
  ```bash
  git clone <项目仓库URL>
  cd automated-testing
  docker build -t automated-testing:latest .
  docker run --rm -v $(pwd)/output:/app/output automated-testing:latest
  allure open output/allure-report
  ```
- CI脚本伪代码（以GitHub Actions为例）：
  ```yaml
  steps:
    - name: Checkout code
      uses: actions/checkout@v2
    - name: Build Docker image
      run: docker build -t automated-testing:latest .
    - name: Run tests
      run: docker run --rm -v ${{ github.workspace }}/output:/app/output automated-testing:latest
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
- 推荐将宿主机（CI服务器）上的Allure Web服务目录（如`/usr/share/nginx/html/allure-report`）挂载到容器内的`/app/output/allure-report`。
- 示例命令：
  ```bash
  docker run --rm \
    -v /usr/share/nginx/html/allure-report:/app/output/allure-report \
    automated-testing:latest \
    bash -c "poetry run pytest --alluredir=/app/output/allure-report && allure generate /app/output/allure-report -o /app/output/allure-report --clean"
  ```
- **为什么这样做？**
  - 这样pytest和allure生成的报告会直接写到Web服务目录，报告生成后Web服务立刻可访问，无需手动拷贝。

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

### 12.5 典型docker run命令模板及参数解释
- 基本模板：
  ```bash
  docker run --rm \
    -e APP_ENV=prod \
    -e WEB_BASE_URL=https://xxx.com \
    -v /usr/share/nginx/html/allure-report:/app/output/allure-report \
    automated-testing:latest \
    bash -c "poetry run pytest --alluredir=/app/output/allure-report && allure generate /app/output/allure-report -o /app/output/allure-report --clean"
  ```
- 参数说明：
  - `--rm`：容器运行结束后自动删除，保持环境整洁。
  - `-e`：传递环境变量，适配不同环境和敏感信息。
  - `-v`：挂载宿主机目录到容器内，实现报告/日志/产物同步。
  - `bash -c "..."`：一次性执行多条命令，先运行pytest再生成Allure报告。

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

---

## 13. 参考与扩展
- [Allure官方文档](https://docs.qameta.io/allure/)
- [Playwright官方文档](https://playwright.dev/python/)
- [Poetry官方文档](https://python-poetry.org/docs/)
- 团队内部Wiki/知识库（如有），持续收集最佳实践与常见问题，便于团队协作和持续改进。

---

## 14. 主流CI平台Docker集成示例

本节详细说明如何在Jenkins和GitLab CI中集成Docker自动化测试，**每个参数和关键步骤均有详细解释**，适合新手和团队成员直接参考。

### 14.1 Jenkins流水线（Pipeline）集成

**Jenkinsfile示例：**

```groovy
pipeline {
    agent any
    environment {
        // 推荐用Jenkins凭据安全注入敏感变量（可在Jenkins凭据管理中配置）
        APP_ENV = 'prod' // 运行环境
        WEB_BASE_URL = credentials('web_base_url') // 系统基础URL（凭据ID）
        TEST_DEFAULT_USERNAME = credentials('test_user') // 测试账号
        TEST_DEFAULT_PASSWORD = credentials('test_pass') // 测试密码
    }
    stages {
        stage('Checkout') {
            steps {
                checkout scm // 拉取代码
            }
        }
        stage('Build Docker Image') {
            steps {
                sh 'docker build -t automated-testing:latest .' // 构建镜像
            }
        }
        stage('Run Tests in Docker') {
            steps {
                sh '''
                docker run --rm \
                  -e APP_ENV=$APP_ENV \
                  -e WEB_BASE_URL=$WEB_BASE_URL \
                  -e TEST_DEFAULT_USERNAME=$TEST_DEFAULT_USERNAME \
                  -e TEST_DEFAULT_PASSWORD=$TEST_DEFAULT_PASSWORD \
                  -v /usr/share/nginx/html/allure-report:/app/output/allure-report \
                  automated-testing:latest \
                  bash -c "poetry run pytest --alluredir=/app/output/allure-report && allure generate /app/output/allure-report -o /app/output/allure-report --clean"
                '''
            }
        }
    }
    post {
        always {
            archiveArtifacts artifacts: 'output/allure-report/**', allowEmptyArchive: true // 归档Allure报告
        }
    }
}
```

**参数与步骤说明：**
- `agent any`：流水线可在任意可用节点上运行。
- `environment`：定义全局环境变量，推荐用Jenkins凭据安全注入敏感信息。
- `checkout scm`：拉取当前分支代码。
- `docker build -t automated-testing:latest .`：构建自动化测试镜像。
- `docker run --rm ...`：运行测试容器，参数详解：
  - `--rm`：测试完成后自动删除容器，保持环境整洁。
  - `-e ...`：传递环境变量，适配不同环境和敏感信息。
  - `-v /usr/share/nginx/html/allure-report:/app/output/allure-report`：将宿主机Web服务报告目录挂载到容器内，报告生成后Web服务可直接访问。
  - `automated-testing:latest`：指定要运行的镜像。
  - `bash -c "poetry run pytest ... && allure generate ..."`：先运行pytest生成Allure原始结果，再生成HTML报告。
- `archiveArtifacts`：将Allure报告归档为Jenkins产物，便于后续下载和发布。

---

### 14.2 GitLab CI 集成

**.gitlab-ci.yml示例：**

```yaml
stages:
  - test

variables:
  APP_ENV: "prod" # 运行环境

test:
  stage: test
  image: docker:latest # 使用官方Docker镜像
  services:
    - docker:dind # 启用Docker-in-Docker服务
  script:
    - docker build -t automated-testing:latest . # 构建镜像
    - >
      docker run --rm \
      -e APP_ENV=$APP_ENV \
      -e WEB_BASE_URL=$WEB_BASE_URL \
      -e TEST_DEFAULT_USERNAME=$TEST_DEFAULT_USERNAME \
      -e TEST_DEFAULT_PASSWORD=$TEST_DEFAULT_PASSWORD \
      -v /usr/share/nginx/html/allure-report:/app/output/allure-report \
      automated-testing:latest \
      bash -c "poetry run pytest --alluredir=/app/output/allure-report && allure generate /app/output/allure-report -o /app/output/allure-report --clean"
  artifacts:
    paths:
      - output/allure-report
    expire_in: 1 week
```

**参数与步骤说明：**
- `stages`：定义流水线阶段。
- `variables`：定义全局环境变量，可在GitLab CI/CD设置中配置敏感变量（如WEB_BASE_URL等）。
- `image: docker:latest`：使用官方Docker镜像，支持docker命令。
- `services: docker:dind`：启用Docker-in-Docker服务，允许流水线内构建和运行容器。
- `script`：
  - `docker build ...`：构建自动化测试镜像。
  - `docker run --rm ...`：运行测试容器，参数同Jenkins说明。
- `artifacts`：归档Allure报告，便于团队成员下载和查看。
- `expire_in`：产物保存时长。

---

### 14.3 关键说明与最佳实践
- **环境变量注入**：推荐用CI平台的变量/凭据机制，安全、灵活。
- **output挂载**：直接挂载Web服务目录或CI产物目录，报告自动同步。
- **产物归档**：Allure报告等测试产物建议用CI平台的归档功能，便于追溯和发布。
- **流水线全自动**：从拉代码、构建镜像、运行测试、生成报告到归档产物，全流程自动化，极大提升效率和一致性。

---

## 15. 常见问题FAQ

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

---

## 16. 邮件通知集成

测试完成后自动发送邮件通知是CI/CD自动化的重要环节，下面提供几种实现方式。

### 16.1 Python脚本发送邮件

推荐使用Python的yagmail库发送邮件，简单易用：

```python
# ci/scripts/send_report_email.py
import yagmail
import os

# 邮件配置（建议通过环境变量注入）
user = os.environ.get("EMAIL_SENDER")
password = os.environ.get("EMAIL_PASSWORD")
to = os.environ.get("EMAIL_RECIPIENTS").split(",")
allure_url = os.environ.get("ALLURE_PUBLIC_URL")

subject = "自动化测试报告"
content = f"本次自动化测试已完成，Allure报告地址：{allure_url}"

yag = yagmail.SMTP(user=user, password=password, host='smtp.qiye.aliyun.com')
yag.send(to=to, subject=subject, contents=content)
print("邮件已发送")
```

### 16.2 Jenkins集成邮件通知

在Jenkinsfile中添加邮件通知：

```groovy
post {
    always {
        archiveArtifacts artifacts: 'output/allure-report/**', allowEmptyArchive: true
        
        script {
            def testSummary = sh(script: 'cat output/allure-report/widgets/summary.json || echo "{}"', returnStdout: true).trim()
            def allureUrl = "http://your-jenkins-server/allure-report/${env.BUILD_NUMBER}/"
            
            emailext (
                subject: "测试结果: ${currentBuild.currentResult} - ${env.JOB_NAME} #${env.BUILD_NUMBER}",
                body: """
                    <p>测试结果: ${currentBuild.currentResult}</p>
                    <p>任务: ${env.JOB_NAME} #${env.BUILD_NUMBER}</p>
                    <p>Allure报告: <a href="${allureUrl}">${allureUrl}</a></p>
                    <p>变更详情: ${env.CHANGE_URL ?: '无'}</p>
                """,
                to: '$DEFAULT_RECIPIENTS',
                mimeType: 'text/html'
            )
        }
    }
}
```

### 16.3 GitLab CI邮件通知

使用GitLab CI/CD内置的邮件通知或自定义脚本：

```yaml
stages:
  - test
  - notify

test:
  # ... 上面的测试步骤 ...

notify:
  stage: notify
  image: python:3.11
  script:
    - pip install yagmail
    - python ci/scripts/send_report_email.py
  dependencies:
    - test
  only:
    - main
```

### 16.4 邮件通知最佳实践

- **只发送必要信息**：邮件内容简洁，关键测试指标和报告链接即可
- **区分通知级别**：成功和失败用不同主题，便于接收者快速识别
- **HTML格式增强可读性**：使用HTML格式，关键数据用表格呈现
- **安全保障**：邮箱账号密码通过CI平台变量/凭据管理注入
- **防止邮件轰炸**：仅在重要分支（如main、develop）构建后发送
- **便于跟踪分析**：在邮件中包含构建编号、分支/提交信息、报告链接等

---

### 变更记录
- 2024-06-XX：结构化重构，补充目录结构、环境变量、依赖管理、测试数据分离、CI/CD与Docker集成、主流CI平台集成示例、常见问题FAQ等内容，优化章节编号和格式。
- 2024-06-XX：更新Dockerfile示例，增加Playwright依赖安装说明，统一使用poetry run命令执行测试，补充FAQ内容。
- 2024-06-XX：新增邮件通知集成章节，提供Python脚本、Jenkins和GitLab CI的邮件通知实现方式。
