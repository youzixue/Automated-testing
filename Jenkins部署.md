# Jenkins流水线配置指南：多平台自动化测试

本文档详细介绍如何在同一台机器上使用Docker部署的Jenkins（版本2.492.3）中配置流水线，实现Web自动化、接口自动化、微信公众号和App自动化测试，并在同一个Allure报告中展示所有测试结果。

## 目录

1. [环境准备](#环境准备)
2. [目录结构创建](#目录结构创建)
3. [创建Pipeline项目](#创建pipeline项目)
4. [配置Pipeline脚本](#配置pipeline脚本)
5. [配置定时构建](#配置定时构建)
6. [执行与查看结果](#执行与查看结果)
7. [常见问题与解决方案](#常见问题与解决方案)

## 环境准备

### 前提条件

- 已安装Docker并正常运行
- Jenkins已通过Docker方式部署并可以访问 (版本2.492.3或更高)
- 已安装必要的Jenkins插件：
  - Pipeline插件
  - Git插件
  - Parameterized Trigger插件
- 已准备好Nginx服务器用于展示Allure报告
- CI环境和Jenkins位于同一台机器上

### Docker-in-Docker配置

由于Jenkins本身运行在Docker容器中，需要确保它能够执行Docker命令：

1. 检查Jenkins容器是否已挂载Docker套接字：
   ```bash
   docker inspect jenkins | grep docker.sock
   ```

2. 如果没有挂载，需要重新创建Jenkins容器：
   ```bash
   docker stop jenkins
   docker rm jenkins
   docker run -d --name jenkins \
     -p 8080:8080 -p 50000:50000 \
     -v jenkins_home:/var/jenkins_home \
     -v /var/run/docker.sock:/var/run/docker.sock \
     -v /usr/bin/docker:/usr/bin/docker \
     --group-add $(getent group docker | cut -d: -f3) \
     jenkins/jenkins:2.492.3
   ```

3. 进入Jenkins容器，确认Docker命令可用：
   ```bash
   docker exec -it jenkins bash
   docker --version
   ```

### 安装项目依赖

1. 创建自动化测试的Docker镜像：

   a. 准备Dockerfile（保存为`/path/to/Dockerfile`）：
   ```dockerfile
   FROM python:3.11-slim
   
   # 安装基础依赖
   RUN apt-get update && apt-get install -y \
       wget \
       gnupg \
       curl \
       unzip \
       && rm -rf /var/lib/apt/lists/*
   
   # 安装Poetry
   RUN curl -sSL https://install.python-poetry.org | python3 -
   ENV PATH="/root/.local/bin:$PATH"
   
   # 设置工作目录
   WORKDIR /app
   
   # 复制项目文件
   COPY . .
   
   # 安装项目依赖
   RUN poetry config virtualenvs.create false \
       && poetry install --no-dev
   
   # 设置时区
   ENV TZ=Asia/Shanghai
   
   # 设置入口点
   ENTRYPOINT ["/bin/bash"]
   ```

   b. 构建Docker镜像：
   ```bash
   cd /path/to/project
   docker build -t automated-testing:dev -f Dockerfile .
   ```

## 目录结构创建

### 创建必要的目录结构

1. 创建Nginx目录用于Allure报告：
   ```bash
   sudo mkdir -p /usr/share/nginx/html/allure-report-test
   sudo mkdir -p /usr/share/nginx/html/allure-report-prod
   ```

2. 设置目录权限（确保Jenkins可以写入）：
   ```bash
   sudo chmod -R 777 /usr/share/nginx/html/allure-report-test
   sudo chmod -R 777 /usr/share/nginx/html/allure-report-prod
   ```

3. 创建项目目录结构：
   ```bash
   mkdir -p /path/to/project/tests/{web,api,wechat,app}
   mkdir -p /path/to/project/ci/scripts
   mkdir -p /path/to/project/output/{logs,screenshots,reports,allure-results}
   ```

### 配置Nginx服务器

1. 创建Nginx配置文件（保存为`/etc/nginx/conf.d/allure.conf`）：
   ```nginx
   server {
       listen 8000;
       server_name localhost;
   
       # 测试环境Allure报告
       location /allure-report-test/ {
           alias /usr/share/nginx/html/allure-report-test/;
           index index.html;
           try_files $uri $uri/ /index.html;
       }
   
       # 生产环境Allure报告
       location /allure-report-prod/ {
           alias /usr/share/nginx/html/allure-report-prod/;
           index index.html;
           try_files $uri $uri/ /index.html;
       }
   }
   ```

2. 重新加载Nginx配置：
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

## 创建Pipeline项目

1. 访问Jenkins服务器（如：http://your-server:8080）
2. 点击左上角的"**新建任务**"（或"**New Item**"）
3. 输入项目名称，如"**Automated-testing**"
4. 选择"**流水线**"（或"**Pipeline**"）项目类型
5. 点击"**确定**"（或"**OK**"）按钮创建项目

## 配置Pipeline脚本

### 步骤1：配置项目参数

1. 在项目配置页面，找到"**参数化构建过程**"（或"**This project is parameterized**"）选项并勾选
2. 添加以下参数：

   a. 添加"**选项参数**"（Choice Parameter）：
      - 名称：`APP_ENV`
      - 选项（每行一个）：
        ```
        test
        prod
        ```
      - 描述：选择测试环境

   b. 添加多个"**布尔值参数**"（Boolean Parameter）：
      - 名称：`RUN_WEB_TESTS`（默认值：true，描述：运行Web测试）
      - 名称：`RUN_API_TESTS`（默认值：true，描述：运行API测试）
      - 名称：`RUN_WECHAT_TESTS`（默认值：false，描述：运行微信公众号测试）
      - 名称：`RUN_APP_TESTS`（默认值：false，描述：运行App测试）

   c. 添加"**选项参数**"（Choice Parameter）：
      - 名称：`TEST_SUITE`
      - 选项（每行一个）：
        ```
        全部
        冒烟测试
        回归测试
        ```
      - 描述：选择测试套件

   d. 添加"**布尔值参数**"（Boolean Parameter）：
      - 名称：`SEND_EMAIL`
      - 默认值：true
      - 描述：是否发送邮件通知

### 步骤2：配置Pipeline脚本

1. 在"**流水线**"（Pipeline）部分，选择"**Pipeline script**"
2. 将以下脚本粘贴到文本框中：

```groovy
pipeline {
    agent any 

    environment {
        // PROJECT_PATH 变量不再需要用来挂载源代码了
        // ALLURE 目录和 URL 配置 (保持不变)
        ALLURE_RESULTS_DIR = "${params.APP_ENV == 'prod' ? 'allure-report-prod' : 'allure-report-test'}"
        ALLURE_PUBLIC_URL = "${params.APP_ENV == 'prod' ? 
                          'http://192.168.10.67:8000/allure-report-prod/' : 
                          'http://192.168.10.67:8000/allure-report-test/'}"
        // URL 变量 (保持不变)
        WEB_URL = "${params.APP_ENV == 'prod' ? 'https://cmpark.cmpo1914.com/' : 'https://test.cmpo1914.com:3006/omp/'}"
        API_URL = "${params.APP_ENV == 'prod' ? 'https://cmpark.cmpo1914.com/api/' : 'https://test.cmpo1914.com:3006/api/'}"
        // 测试套件转换 (保持不变)
        TEST_SUITE_VALUE = "${params.TEST_SUITE == '全部' ? 'all' : (params.TEST_SUITE == '冒烟测试' ? 'smoke' : 'regression')}"

        // 凭据 ID (保持不变)
        GIT_CREDENTIALS_ID = 'git-credentials' 
        TEST_ENV_CREDENTIALS_ID = 'test-env-credentials'
        PROD_ENV_CREDENTIALS_ID = 'prod-env-credentials'
        EMAIL_PASSWORD_CREDENTIALS_ID = 'email-password-credential' 
    }

    stages {
        stage('检出代码') { // 这个阶段确保每次都拉取最新代码
            steps {
                echo "从代码仓库拉取最新代码: https://gittest.ylmo2o.com:8099/yzx/Automated-testing.git"
                cleanWs() 
                checkout([
                    $class: 'GitSCM', 
                    branches: [[name: '*/main']], 
                    userRemoteConfigs: [[
                        url: 'https://gittest.ylmo2o.com:8099/yzx/Automated-testing.git', 
                        credentialsId: env.GIT_CREDENTIALS_ID
                    ]]
                ])
                // (可选) 验证代码是否已检出到工作空间
                // sh 'ls -la ${WORKSPACE}' 
            }
        }

        stage('准备环境') { // 这个阶段现在准备工作空间内的目录
            steps {
                echo "准备 ${params.APP_ENV} 环境的测试执行 (在工作空间: ${WORKSPACE})..."
                sh """
                mkdir -p ${WORKSPACE}/output/allure-results
                mkdir -p ${WORKSPACE}/output/reports
                """
                sh "rm -rf ${WORKSPACE}/output/allure-results/*"
            }
        }
        
        stage('并行执行测试') {
            steps {
                 script {
                    def accountCredentialsId = (params.APP_ENV == 'prod') ? env.PROD_ENV_CREDENTIALS_ID : env.TEST_ENV_CREDENTIALS_ID
                    echo "Using credentials ID: ${accountCredentialsId}"
                    
                    withCredentials([usernamePassword(credentialsId: accountCredentialsId, 
                                                    usernameVariable: 'ACCOUNT_USERNAME', 
                                                    passwordVariable: 'ACCOUNT_PASSWORD')]) {
                        parallel {
                            stage('Web测试') {
                                when { expression { params.RUN_WEB_TESTS } }
                                steps {
                                    echo "执行Web测试 (代码来自 ${WORKSPACE})..."
                                    // **改动点**: 挂载 ${WORKSPACE} 而不是 PROJECT_PATH
                                    runTest('web', env.ACCOUNT_USERNAME, env.ACCOUNT_PASSWORD) 
                                }
                            }
                            
                            stage('API测试') {
                                when { expression { params.RUN_API_TESTS } }
                                steps {
                                    echo "执行API测试 (代码来自 ${WORKSPACE})..."
                                    // **改动点**: 挂载 ${WORKSPACE} 而不是 PROJECT_PATH
                                    runTest('api', env.ACCOUNT_USERNAME, env.ACCOUNT_PASSWORD)
                                }
                            }
                            
                            stage('微信公众号测试') {
                                when { expression { params.RUN_WECHAT_TESTS } }
                                steps {
                                    echo "执行微信公众号测试 (代码来自 ${WORKSPACE})..."
                                     // **改动点**: 挂载 ${WORKSPACE} 而不是 PROJECT_PATH
                                    runTest('wechat', env.ACCOUNT_USERNAME, env.ACCOUNT_PASSWORD)
                                }
                            }
                            
                            stage('App测试') {
                                when { expression { params.RUN_APP_TESTS } }
                                steps {
                                    echo "执行App测试 (代码来自 ${WORKSPACE})..."
                                     // **改动点**: 挂载 ${WORKSPACE} 而不是 PROJECT_PATH
                                    runTest('app', env.ACCOUNT_USERNAME, env.ACCOUNT_PASSWORD)
                                }
                            }
                        }
                     }
                 }
            }
        }
        
        stage('生成聚合报告') {
            steps {
                withCredentials([string(credentialsId: env.EMAIL_PASSWORD_CREDENTIALS_ID, variable: 'EMAIL_PASSWORD_SECRET')]) {
                    echo "生成统一Allure报告并发送邮件 (结果来自 ${WORKSPACE}/output)..."
                    
                    // **改动点**: 挂载 ${WORKSPACE} 而不是 PROJECT_PATH
                    sh """
                    docker run --rm \\
                      -e CI=true \\
                      -e CI_NAME="${params.APP_ENV == 'prod' ? '生产环境自动化' : '测试环境自动化'}" \\
                      -e APP_ENV=${params.APP_ENV} \\
                      -e EMAIL_ENABLED=${params.SEND_EMAIL} \\
                      -e EMAIL_SMTP_SERVER="smtp.qiye.aliyun.com" \\
                      -e EMAIL_SMTP_PORT=465 \\
                      -e EMAIL_SENDER="yzx@ylmt2b.com" \\
                      -e EMAIL_PASSWORD="${EMAIL_PASSWORD_SECRET}" \\
                      -e EMAIL_USE_SSL=true \\
                      -e EMAIL_RECIPIENTS="yzx@ylmt2b.com" \\
                      -e ALLURE_PUBLIC_URL="${ALLURE_PUBLIC_URL}" \\
                      -e TZ="Asia/Shanghai" \\
                      -v ${WORKSPACE}/output:/app/output \\
                      -v /usr/share/nginx/html/${ALLURE_RESULTS_DIR}:/app/output/reports/allure-report \\
                      -v /etc/localtime:/etc/localtime:ro \\
                      -v ${WORKSPACE}:/app \\  
                      --network host \\
                      automated-testing:dev \\
                      /bin/bash -c "cd /app && poetry run python ci/scripts/run_and_notify.py" 
                    """
                    
                    sh """
                    sudo chmod -R 755 /usr/share/nginx/html/${ALLURE_RESULTS_DIR} 
                    """
                }
            }
        }
    }
    
    post { // (保持不变)
        always {
            echo "测试已完成，集成Allure报告已生成: ${ALLURE_PUBLIC_URL}"
            script {
                def testTypes = []
                if (params.RUN_WEB_TESTS) testTypes.add("Web")
                if (params.RUN_API_TESTS) testTypes.add("API")
                if (params.RUN_WECHAT_TESTS) testTypes.add("微信")
                if (params.RUN_APP_TESTS) testTypes.add("App")
                currentBuild.description = "${params.APP_ENV.toUpperCase()} 环境 [${testTypes.join(', ')}] - <a href='${ALLURE_PUBLIC_URL}'>查看报告</a>"
            }
            cleanWs() 
        }
    }
}

// 公共函数：运行特定平台的测试 (接收从凭据获取的 username 和 password)
def runTest(String platform, String username, String password) {
    def usernameVar = "${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_USERNAME' : 'TEST_DEFAULT_USERNAME'}"
    def passwordVar = "${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_PASSWORD' : 'TEST_DEFAULT_PASSWORD'}"

    // **改动点**: 挂载 ${WORKSPACE} 而不是 PROJECT_PATH
    sh """
    docker run --rm \\
      -e CI=true \\
      -e CI_NAME="${params.APP_ENV}环境${platform}测试" \\
      -e APP_ENV=${params.APP_ENV} \\
      -e TEST_PLATFORM="${platform}" \\
      -e WEB_BASE_URL="${WEB_URL}" \\
      -e API_BASE_URL="${API_URL}" \\
      -e ${usernameVar}="${username}" \\
      -e ${passwordVar}="${password}" \\
      -e DEFAULT_TIMEOUT=30 \\
      -e TZ="Asia/Shanghai" \\
      -e TEST_SUITE="${TEST_SUITE_VALUE}" \\
      -v ${WORKSPACE}/output:/app/output \\
      -v /etc/localtime:/etc/localtime:ro \\
      -v ${WORKSPACE}:/app \\  
      --network host \\
      automated-testing:dev \\
      /bin/bash -c "cd /app && poetry run pytest tests/${platform} -v --alluredir=output/allure-results --allure-features=${platform.toUpperCase()}"
    """
}
   ```

2. 确保脚本有执行权限：
   ```bash
   chmod +x /path/to/project/ci/scripts/run_and_notify.py
   ```

## 配置定时构建

如果需要定期自动执行测试，可以配置定时构建：

1. 在项目配置页面，找到"**构建触发器**"（或"**Build Triggers**"）部分
2. 勾选"**定时构建**"（或"**Build periodically**"）选项
3. 在"**日程表**"（或"**Schedule**"）文本框中输入Cron表达式：
   - 测试环境每日构建：`H 9 * * 1-5`（工作日每天上午9点）
   - 生产环境每周构建：`H 22 * * 6`（每周六晚上10点）
4. 点击"**保存**"按钮

## 执行与查看结果

### 手动执行测试

1. 在Jenkins项目页面，点击左侧的"**立即构建**"（或"**Build Now**"）按钮
2. 在参数化构建页面上：
   - 选择`APP_ENV`（test或prod）
   - 勾选需要运行的测试类型
   - 选择测试套件（全部、冒烟测试或回归测试）
   - 设置是否发送邮件通知
3. 点击"**开始构建**"（或"**Build**"）按钮开始执行

### 查看执行过程

1. 点击正在运行的构建编号，进入构建详情页面
2. 点击"**控制台输出**"（或"**Console Output**"）查看实时日志
3. 可以在"**阶段视图**"（或"**Stage View**"）中查看各个阶段的执行情况

### 查看测试报告

1. 测试执行完成后，点击构建描述中的报告链接
2. 或直接访问Allure报告URL：
   - 测试环境：`http://localhost:8000/allure-report-test/`
   - 生产环境：`http://localhost:8000/allure-report-prod/`
3. 在Allure报告中：
   - 使用"**Features**"视图按测试类型查看结果
   - 使用"**Suites**"视图查看测试套件结果
   - 查看测试统计信息和失败详情

## 常见问题与解决方案

### 1. Docker命令执行权限问题

**问题**: Jenkins无法执行Docker命令
**解决方案**:
- 确认Jenkins容器已挂载Docker套接字和二进制文件：
  ```bash
  docker exec -it jenkins bash -c "ls -la /var/run/docker.sock && which docker"
  ```
- 确认Jenkins用户有权限访问Docker：
  ```bash
  docker exec -it jenkins bash -c "id && docker ps"
  ```
- 如果存在权限问题，添加Jenkins用户到docker组：
  ```bash
  docker exec -it jenkins bash -c "usermod -aG docker jenkins && id"
  ```

### 2. 目录挂载问题

**问题**: Docker容器无法访问宿主机目录
**解决方案**:
- 确认挂载目录存在且有正确权限：
  ```bash
  ls -la /usr/share/nginx/html/
  ls -la ${PROJECT_PATH}
  ```
- 对Nginx目录授予完全权限：
  ```bash
  chmod -R 777 /usr/share/nginx/html/allure-report-test
  chmod -R 777 /usr/share/nginx/html/allure-report-prod
  ```
- 确保PROJECT_PATH变量指向正确的项目路径

### 3. Allure报告生成问题

**问题**: 测试执行完成但无法生成Allure报告
**解决方案**:
- 确认Allure命令行工具已安装在Docker镜像中：
  ```bash
  docker run --rm automated-testing:dev -c "allure --version"
  ```
- 如果未安装，更新Dockerfile添加Allure安装：
  ```dockerfile
  # 安装Allure命令行工具
  RUN wget https://github.com/allure-framework/allure2/releases/download/2.24.0/allure-2.24.0.zip \
      && unzip allure-2.24.0.zip -d /opt \
      && ln -s /opt/allure-2.24.0/bin/allure /usr/local/bin/allure
  ```
- 检查Nginx配置是否正确：
  ```bash
  nginx -t
  ```

### 4. 网络连接问题

**问题**: 容器无法连接到外部URL或服务
**解决方案**:
- 使用host网络模式：
  ```bash
  # 在Docker命令中添加参数
  --network host
  ```
- 测试网络连接：
  ```bash
  docker run --rm --network host alpine ping -c 3 cmpark.cmpo1914.com
  ```
- 检查防火墙规则：
  ```bash
  sudo iptables -L
  ```

### 5. 邮件通知未发送

**问题**: 测试执行完成但未收到邮件通知
**解决方案**:
- 检查邮件服务器配置是否正确
- 确认`EMAIL_ENABLED`环境变量设置为`true`
- 测试邮件发送：
  ```bash
  docker run --rm \
    -e EMAIL_SMTP_SERVER="smtp.qiye.aliyun.com" \
    -e EMAIL_SMTP_PORT=465 \
    -e EMAIL_SENDER="yzx@ylmt2b.com" \
    -e EMAIL_PASSWORD="5nu2c9ErnAd747Sh" \
    -e EMAIL_USE_SSL=true \
    -e EMAIL_RECIPIENTS="test@example.com" \
    --network host \
    automated-testing:dev \
    -c "python -c \"
    import smtplib
    from email.mime.text import MIMEText
    server = smtplib.SMTP_SSL('smtp.qiye.aliyun.com', 465)
    server.login('yzx@ylmt2b.com', '5nu2c9ErnAd747Sh')
    msg = MIMEText('测试邮件')
    msg['Subject'] = '测试邮件'
    msg['From'] = 'yzx@ylmt2b.com'
    msg['To'] = 'test@example.com'
    server.send_message(msg)
    server.quit()
    print('邮件已发送')
    \""
  ```

## 附录：完整目录结构

同一台机器上的目录结构应如下所示：

```
/usr/share/nginx/html/
  ├── allure-report-test/  # 测试环境报告目录
  └── allure-report-prod/  # 生产环境报告目录

/path/to/project/         # 项目根目录
  ├── tests/
  │   ├── web/            # Web测试用例
  │   ├── api/            # API测试用例  
  │   ├── wechat/         # 微信公众号测试用例
  │   └── app/            # App测试用例
  ├── ci/
  │   └── scripts/
  │       ├── run_and_notify.py  # 报告生成和通知脚本
  │       └── run_tests.py       # 测试执行脚本
  ├── output/
  │   ├── allure-results/ # 测试结果输出目录
  │   ├── reports/        # 报告生成目录
  │   ├── logs/           # 日志目录
  │   └── screenshots/    # 截图目录
  ├── Dockerfile          # Docker镜像定义
  ├── pyproject.toml      # Poetry项目配置
  └── README.md           # 项目说明文档
```

Jenkins工作区目录（构建时创建）：
```
${JENKINS_HOME}/workspace/Automated-testing/
  ├── output/
  │   ├── allure-results/  # 存放测试结果
  │   └── reports/         # 临时报告目录
  └── ...
```
