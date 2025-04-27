pipeline {
    agent any // 或者指定你的 Docker Agent: agent { label 'docker' } 或 agent { docker { image 'your-agent-image' ... } }

    parameters {
        choice(name: 'APP_ENV', choices: ['test', 'prod'], description: '选择测试环境')
        booleanParam(name: 'RUN_WEB_TESTS', defaultValue: true, description: '运行Web测试')
        booleanParam(name: 'RUN_API_TESTS', defaultValue: true, description: '运行API测试')
        booleanParam(name: 'RUN_WECHAT_TESTS', defaultValue: false, description: '运行微信公众号测试')
        booleanParam(name: 'RUN_APP_TESTS', defaultValue: false, description: '运行App测试')
        choice(name: 'TEST_SUITE', choices: ['全部', '冒烟测试', '回归测试'], description: '选择测试套件')
        booleanParam(name: 'SEND_EMAIL', defaultValue: true, description: '是否发送邮件通知')
    }

    environment {
        // --- 凭据 ID ---
        GIT_CREDENTIALS_ID = 'git-credentials'
        GIT_REPO_URL_CREDENTIAL_ID = 'git-repo-url'
        TEST_ENV_CREDENTIALS_ID = 'test-env-credentials'
        PROD_ENV_CREDENTIALS_ID = 'prod-env-credentials'
        TEST_WEB_URL_CREDENTIAL_ID = 'test-web-url'
        TEST_API_URL_CREDENTIAL_ID = 'test-api-url'
        PROD_WEB_URL_CREDENTIAL_ID = 'prod-web-url'
        PROD_API_URL_CREDENTIAL_ID = 'prod-api-url'
        // ALLURE_BASE_URL_CREDENTIAL_ID = 'allure-base-url' // 使用 Jenkins 插件后，这个可能不再需要，除非邮件中仍想放 Nginx 最新链接
        // --- 邮件相关凭据 ID ---
        EMAIL_PASSWORD_CREDENTIALS_ID = 'email-password-credential'
        EMAIL_SMTP_SERVER_CREDENTIAL_ID = 'email-smtp-server'
        EMAIL_SMTP_PORT_CREDENTIAL_ID = 'email-smtp-port'
        EMAIL_SENDER_CREDENTIAL_ID = 'email-sender'
        EMAIL_RECIPIENTS_CREDENTIAL_ID = 'email-recipients'
        EMAIL_USE_SSL_CREDENTIAL_ID = 'email-use-ssl'

        // --- Nginx 部署相关 (如果仍想保留最新报告部署到 Nginx) ---
        // ALLURE_NGINX_DIR_NAME = "${params.APP_ENV == 'prod' ? 'allure-report-prod' : 'allure-report-test'}"
        // ALLURE_NGINX_HOST_PATH = "/usr/share/nginx/html/${ALLURE_NGINX_DIR_NAME}"

        // --- Docker Agent & 宿主机路径映射 (关键) ---
        // !!! 重要：根据你的实际 Docker 卷配置修改 HOST_JENKINS_HOME_ON_HOST !!!
        // 这个路径是 Jenkins Master/Controller 上 Jenkins Home 卷映射到宿主机的路径
        HOST_JENKINS_HOME_ON_HOST = '/var/lib/docker/volumes/jenkins_home/_data' // <-- !!! 示例路径，请务必检查 !!!
        HOST_WORKSPACE_PATH = "${HOST_JENKINS_HOME_ON_HOST}/workspace/${env.JOB_NAME}" // <-- 宿主机上的 Jenkins 工作区路径
        // 这些路径指向工作区内部，Allure 插件会读取这里的结果
        HOST_ALLURE_RESULTS_PATH = "${HOST_WORKSPACE_PATH}/output/allure-results" // <-- 宿主机上的 Allure 结果路径 (用于写入元数据)
        HOST_ALLURE_REPORT_PATH = "${HOST_WORKSPACE_PATH}/output/reports/allure-report" // <-- 宿主机上的临时报告路径 (用于邮件通知脚本读取摘要)

        // --- 测试相关 ---
        TEST_SUITE_VALUE = "${params.TEST_SUITE == '全部' ? 'all' : (params.TEST_SUITE == '冒烟测试' ? 'smoke' : 'regression')}"
        DOCKER_IMAGE = "automated-testing:dev" // 你的测试执行 Docker 镜像
    }

    stages {
        stage('检出代码') {
            steps {
                withCredentials([
                    string(credentialsId: env.GIT_REPO_URL_CREDENTIAL_ID, variable: 'INJECTED_GIT_REPO_URL'),
                    usernamePassword(credentialsId: env.GIT_CREDENTIALS_ID, usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')
                ]) {
                    echo "从代码仓库拉取最新代码: ${INJECTED_GIT_REPO_URL}"
                    cleanWs() // 清理 Agent 工作区
                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: '*/main']], // 或者你的开发分支
                        userRemoteConfigs: [[
                            url: INJECTED_GIT_REPO_URL,
                            credentialsId: env.GIT_CREDENTIALS_ID
                        ]]
                    ])
                }
                echo "代码检出完成到 Agent 路径: ${WORKSPACE}"
                echo "对应的宿主机路径是: ${env.HOST_WORKSPACE_PATH}"
                sh "echo '>>> Jenkins Agent Workspace Contents:' && ls -la ${WORKSPACE}"
            }
        }

        stage('准备环境 (Agent)') {
            steps {
                echo "准备测试环境和目录 (在 Agent ${WORKSPACE} 上)..."
                // 在 Agent 上创建目录，插件会读取这里的 allure-results
                sh """
                mkdir -p ${WORKSPACE}/output/allure-results
                mkdir -p ${WORKSPACE}/output/reports/allure-report
                echo "清空旧的 allure-results (在 Agent ${WORKSPACE} 上)..."
                rm -rf ${WORKSPACE}/output/allure-results/*
                """
                // 不再需要准备 Nginx 目录
                // echo "确保 Nginx 目录 ${env.ALLURE_NGINX_HOST_PATH} (在宿主机上) 存在并设置权限..."
                // sh """
                // docker run --rm -v ${env.ALLURE_NGINX_HOST_PATH}:${env.ALLURE_NGINX_HOST_PATH}:rw --user root alpine:latest sh -c "mkdir -p ${env.ALLURE_NGINX_HOST_PATH} && chmod -R 777 ${env.ALLURE_NGINX_HOST_PATH}" || echo 'Failed to prepare Nginx host directory, permissions might be an issue.'
                // """
                echo "环境准备完成。"
            }
        }

        stage('检查脚本文件') {
             // (可选) 保留此阶段用于调试
            steps {
                echo "检查脚本文件是否存在于 Agent 路径: ${WORKSPACE}/ci/scripts/ ..."
                sh "ls -la ${WORKSPACE}/ci/scripts/ || echo '>>> ci/scripts/ 目录不存在或无法列出 <<<' "
                sh "test -f ${WORKSPACE}/ci/scripts/write_allure_metadata.py && echo '>>> write_allure_metadata.py 存在于 Agent <<< ' || echo '>>> write_allure_metadata.py 不存在于 Agent! <<<' "
                // 不再需要检查部署脚本
                // sh "test -f ${WORKSPACE}/ci/scripts/prepare_nginx_dir.sh && echo '>>> prepare_nginx_dir.sh 存在于 Agent <<< ' || echo '>>> prepare_nginx_dir.sh 不存在于 Agent! <<<' "
                // sh "test -f ${WORKSPACE}/ci/scripts/deploy_allure_report.sh && echo '>>> deploy_allure_report.sh 存在于 Agent <<< ' || echo '>>> deploy_allure_report.sh 不存在于 Agent! <<<' "
            }
        }

        stage('并行执行测试') {
             steps {
                script {
                    // --- 动态选择凭据 ID ---
                    def accountCredentialsId = (params.APP_ENV == 'prod') ? env.PROD_ENV_CREDENTIALS_ID : env.TEST_ENV_CREDENTIALS_ID
                    def webUrlCredentialId = (params.APP_ENV == 'prod') ? env.PROD_WEB_URL_CREDENTIAL_ID : env.TEST_WEB_URL_CREDENTIAL_ID
                    def apiUrlCredentialId = (params.APP_ENV == 'prod') ? env.PROD_API_URL_CREDENTIAL_ID : env.TEST_API_URL_CREDENTIAL_ID
                    echo "选择凭据 ID: 账户=${accountCredentialsId}, WebURL=${webUrlCredentialId}, APIURL=${apiUrlCredentialId}"

                    // 捕获测试阶段的错误，但不让它停止 Pipeline
                    try {
                        // --- 注入账户和 URL 凭据 ---
                        withCredentials([
                            usernamePassword(credentialsId: accountCredentialsId, usernameVariable: 'ACCOUNT_USERNAME', passwordVariable: 'ACCOUNT_PASSWORD'),
                            string(credentialsId: webUrlCredentialId, variable: 'INJECTED_WEB_URL'),
                            string(credentialsId: apiUrlCredentialId, variable: 'INJECTED_API_URL')
                        ]) {
                            def testsToRun = [:]

                            if (params.RUN_WEB_TESTS) {
                                testsToRun['Web测试'] = {
                                    echo "执行Web测试 (并发: auto, 重试: 2)"
                                    // 注意：仍然需要将宿主机的 allure-results 路径挂载到容器，以便 pytest 写入结果
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

                            if (params.RUN_WECHAT_TESTS) {
                               testsToRun['微信公众号测试'] = {
                                    echo "执行微信公众号测试 (并发: auto, 重试: 2)"
                                    sh """
                                    docker run --rm --name pytest-wechat-${BUILD_NUMBER} \\
                                      -e APP_ENV=${params.APP_ENV} \\
                                      -e TEST_PLATFORM="wechat" \\
                                      -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_USERNAME' : 'TEST_DEFAULT_USERNAME'}="${ACCOUNT_USERNAME}" \\
                                      -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_PASSWORD' : 'TEST_DEFAULT_PASSWORD'}="${ACCOUNT_PASSWORD}" \\
                                      -e TEST_SUITE="${env.TEST_SUITE_VALUE}" \\
                                      -e TZ="Asia/Shanghai" \\
                                      -v ${env.HOST_WORKSPACE_PATH}:/workspace:rw \\
                                      -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \\
                                      --workdir /workspace \\
                                      -v /etc/localtime:/etc/localtime:ro \\
                                      --network host \\
                                      ${env.DOCKER_IMAGE} \\
                                      pytest tests/wechat -n auto --reruns 2 -v --alluredir=/results_out
                                    """
                               }
                            } else { echo "跳过微信公众号测试" }

                            if (params.RUN_APP_TESTS) {
                                testsToRun['App测试'] = {
                                    echo "执行App测试 (并发: auto, 重试: 2)"
                                    sh """
                                    docker run --rm --name pytest-app-${BUILD_NUMBER} \\
                                      -e APP_ENV=${params.APP_ENV} \\
                                      -e TEST_PLATFORM="app" \\
                                      -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_USERNAME' : 'TEST_DEFAULT_USERNAME'}="${ACCOUNT_USERNAME}" \\
                                      -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_PASSWORD' : 'TEST_DEFAULT_PASSWORD'}="${ACCOUNT_PASSWORD}" \\
                                      -e TEST_SUITE="${env.TEST_SUITE_VALUE}" \\
                                      -e TZ="Asia/Shanghai" \\
                                      -v ${env.HOST_WORKSPACE_PATH}:/workspace:rw \\
                                      -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \\
                                      --workdir /workspace \\
                                      -v /etc/localtime:/etc/localtime:ro \\
                                      --network host \\
                                      ${env.DOCKER_IMAGE} \\
                                      pytest tests/app -n auto --reruns 2 -v --alluredir=/results_out
                                    """
                                }
                            } else { echo "跳过App测试" }

                            if (!testsToRun.isEmpty()) {
                                 echo "开始并行执行选定的测试 (结果写入宿主机 ${env.HOST_ALLURE_RESULTS_PATH})..."
                                 parallel testsToRun
                            } else {
                                 echo "没有选择任何测试平台，跳过测试执行。"
                                 // 即使跳过测试，也要确保 Agent 上的结果目录存在
                                 sh "mkdir -p ${WORKSPACE}/output/allure-results"
                            }
                        } // End withCredentials
                    } catch (err) {
                        echo "测试阶段出现错误: ${err}. 将继续执行报告生成和通知。"
                        // currentBuild.result = 'UNSTABLE'
                    }
                } // End script
            } // End steps
        } // End stage '并行执行测试'

       } // End stages

       // --- Post Build Actions ---
       post {
           always {
               echo "Pipeline 完成. 开始执行报告生成和通知步骤..."
               script {
                   // 定义报告链接变量，初始为空
                   def allureReportUrl = ""
                   // 定义一个标志，表示 Allure 插件步骤是否成功
                   def allureStepSuccess = false

                   try {
                       // --- 注入邮件凭据 ---
                       withCredentials([
                           string(credentialsId: env.EMAIL_PASSWORD_CREDENTIALS_ID, variable: 'INJECTED_EMAIL_PASSWORD'),
                           // string(credentialsId: env.ALLURE_BASE_URL_CREDENTIAL_ID, variable: 'INJECTED_ALLURE_BASE_URL'), // 可能不再需要
                           string(credentialsId: env.EMAIL_SMTP_SERVER_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_SMTP_SERVER'),
                           string(credentialsId: env.EMAIL_SMTP_PORT_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_SMTP_PORT'),
                           string(credentialsId: env.EMAIL_SENDER_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_SENDER'),
                           string(credentialsId: env.EMAIL_RECIPIENTS_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_RECIPIENTS'),
                           string(credentialsId: env.EMAIL_USE_SSL_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_USE_SSL')
                       ]) {

                           // --- 1. 写入 Allure 元数据 (插件会使用) ---
                           echo "写入 Allure 元数据文件到 ${env.HOST_ALLURE_RESULTS_PATH} (在宿主机上)..."
                           // 传递 Jenkins 插件报告 URL 给元数据脚本
                           def jenkinsAllureReportUrl = "${env.BUILD_URL}allure/"
                           sh """
                           docker run --rm --name write-metadata-${BUILD_NUMBER} \\
                             -e APP_ENV=${params.APP_ENV} \\
                             -e BUILD_NUMBER=${BUILD_NUMBER} \\
                             -e BUILD_URL=${env.BUILD_URL} \\
                             -e JOB_NAME=${env.JOB_NAME} \\
                             -e ALLURE_PUBLIC_URL='${jenkinsAllureReportUrl}' \\
                             -v ${env.HOST_WORKSPACE_PATH}:/workspace:ro \\
                             -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \\
                             -v /etc/localtime:/etc/localtime:ro \\
                             --user root \\
                             ${env.DOCKER_IMAGE} \\
                             python /workspace/ci/scripts/write_allure_metadata.py /results_out
                           """
                           echo "Allure 元数据写入完成。"

                           // --- 2. 使用 Allure Jenkins 插件生成和归档报告 ---
                           echo "使用 Allure Jenkins 插件处理 ${WORKSPACE}/output/allure-results 中的结果..."
                           // 使用 allure 步骤，它会查找全局配置的 Allure Commandline
                           allure([
                               // includeProperties: false, // 是否包含Java属性，通常不需要
                               // jdk: '', // 如果需要指定特定JDK
                               properties: [], // 可以添加额外的环境属性
                               reportBuildPolicy: 'ALWAYS', // 每次构建都生成报告 (其他选项: NEVER, UNSTABLE, FAILED)
                               results: [
                                   // 指定 Allure 结果文件在 Agent 工作区中的路径
                                   [path: 'output/allure-results']
                               ]
                           ])
                           // 如果插件步骤成功，设置标志和URL
                           allureStepSuccess = true
                           allureReportUrl = jenkinsAllureReportUrl // 使用上面定义的插件 URL
                           echo "Allure 插件报告处理完成。报告 URL: ${allureReportUrl}"

                           // --- 3. 发送邮件通知 (更新链接) ---
                           if (params.SEND_EMAIL) {
                               echo "发送邮件通知..."
                               // 邮件通知脚本现在需要读取 Agent 上的 allure-report 目录来获取摘要
                               // 注意：allure 插件生成的报告存储在 Jenkins Master/Controller，Agent 上可能没有完整的报告文件
                               // run_and_notify.py 需要调整以适应这种情况，或者邮件只发送基本信息和链接
                               // 临时方案：让 run_and_notify.py 尝试读取结果目录
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
                                 -e ALLURE_PUBLIC_URL="${allureReportUrl}" \\
                                 -e TZ="Asia/Shanghai" \\
                                 -e ALLURE_RESULTS_DIR=/results \\
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
                           } else {
                               echo "邮件通知已禁用 (SEND_EMAIL=false)。"
                           }

                       } // End withCredentials
                   } catch (err) {
                       echo "Post-build 阶段出现错误: ${err}"
                       // 如果 allure 步骤失败，标记构建失败
                       if (!allureStepSuccess) {
                           currentBuild.result = 'FAILURE'
                       }
                   } finally {
                       // --- 4. 设置构建描述 ---
                       def testTypes = []
                       if (params.RUN_WEB_TESTS) testTypes.add("Web")
                       if (params.RUN_API_TESTS) testTypes.add("API")
                       if (params.RUN_WECHAT_TESTS) testTypes.add("微信")
                       if (params.RUN_APP_TESTS) testTypes.add("App")
                       if (testTypes.isEmpty()) testTypes.add("未选择")
                       def finalStatus = currentBuild.result ?: 'SUCCESS'
                       // 使用 Jenkins 插件的报告 URL
                       def reportLink = allureReportUrl ? "<a href='${allureReportUrl}' target='_blank'>查看报告</a>" : "(报告未生成)"
                       currentBuild.description = "${params.APP_ENV.toUpperCase()} 环境 [${testTypes.join(', ')}] - ${finalStatus} - ${reportLink}"

                       // --- 5. 清理工作空间 ---
                       echo "清理 Agent 工作空间 ${WORKSPACE}..."
                       cleanWs()
                       echo "Agent 工作空间已清理。"
                   } // End finally
               } // End script
           } // End always
           success {
               echo "Pipeline 最终状态: 成功"
           }
           failure {
               echo "Pipeline 最终状态: 失败"
           }
           unstable {
               echo "Pipeline 最终状态: 不稳定"
           }
       } // End post
   } // End pipeline
