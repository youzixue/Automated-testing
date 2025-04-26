pipeline {
    agent any

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
        TEST_ENV_CREDENTIALS_ID = 'test-env-credentials'
        PROD_ENV_CREDENTIALS_ID = 'prod-env-credentials'
        EMAIL_PASSWORD_CREDENTIALS_ID = 'email-password-credential'

        // --- Allure 报告相关 ---
        ALLURE_NGINX_DIR_NAME = "${params.APP_ENV == 'prod' ? 'allure-report-prod' : 'allure-report-test'}"
        ALLURE_PUBLIC_URL = "${params.APP_ENV == 'prod' ? 'http://192.168.10.67:8000/allure-report-prod/' : 'http://192.168.10.67:8000/allure-report-test/'}"
        ALLURE_NGINX_HOST_PATH = "/usr/share/nginx/html/${ALLURE_NGINX_DIR_NAME}"

        // --- 测试相关 ---
        TEST_SUITE_VALUE = "${params.TEST_SUITE == '全部' ? 'all' : (params.TEST_SUITE == '冒烟测试' ? 'smoke' : 'regression')}"
        WEB_URL = "${params.APP_ENV == 'prod' ? 'https://cmpark.cmpo1914.com/' : 'https://test.cmpo1914.com:3006/omp/'}"
        API_URL = "${params.APP_ENV == 'prod' ? 'https://cmpark.cmpo1914.com/api/' : 'https://test.cmpo1914.com:3006/api/'}"
        DOCKER_IMAGE = "automated-testing:dev"
        CI_NAME = "${params.APP_ENV == 'prod' ? '生产环境自动化' : '测试环境自动化'}"
    }

    stages {
        stage('检出代码') {
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
                echo "代码检出完成到 ${WORKSPACE}"
                sh "echo '>>> Jenkins Workspace Contents:' && ls -la ${WORKSPACE}"
            }
        }

        stage('准备环境') {
            steps {
                echo "准备测试环境和目录..."
                sh """
                mkdir -p ${WORKSPACE}/output/allure-results
                mkdir -p ${WORKSPACE}/output/reports/allure-report
                echo "清空旧的 allure-results..."
                rm -rf ${WORKSPACE}/output/allure-results/*

                echo "确保 Nginx 目录 ${env.ALLURE_NGINX_HOST_PATH} 存在并设置权限..."
                docker run --rm -v /usr/share/nginx/html:/nginx_html --user root alpine:latest sh -c "mkdir -p /nginx_html/${ALLURE_NGINX_DIR_NAME} && chmod -R 777 /nginx_html/${ALLURE_NGINX_DIR_NAME}"

                echo "环境准备完成。"
                """
            }
        }

        // --- 新增的检查阶段 ---
        stage('检查脚本文件') {
            steps {
                echo "检查脚本文件是否存在于 ${WORKSPACE}/ci/scripts/ ..."
                // 列出 ci/scripts 目录内容
                sh "ls -la ${WORKSPACE}/ci/scripts/ || echo '>>> ci/scripts/ 目录不存在或无法列出 <<<' "
                // 检查具体文件是否存在
                sh "test -f ${WORKSPACE}/ci/scripts/write_allure_metadata.py && echo '>>> write_allure_metadata.py 存在 <<< ' || echo '>>> write_allure_metadata.py 不存在! <<<' "
                sh "test -f ${WORKSPACE}/ci/scripts/prepare_nginx_dir.sh && echo '>>> prepare_nginx_dir.sh 存在 <<< ' || echo '>>> prepare_nginx_dir.sh 不存在! <<<' "
                sh "test -f ${WORKSPACE}/ci/scripts/deploy_allure_report.sh && echo '>>> deploy_allure_report.sh 存在 <<< ' || echo '>>> deploy_allure_report.sh 不存在! <<<' "
            }
        }
        // --- 检查阶段结束 ---

        stage('并行执行测试') {
             steps {
                script {
                    def accountCredentialsId = (params.APP_ENV == 'prod') ? env.PROD_ENV_CREDENTIALS_ID : env.TEST_ENV_CREDENTIALS_ID
                    echo "选择凭据 ID: ${accountCredentialsId} 用于测试账户"

                    withCredentials([usernamePassword(credentialsId: accountCredentialsId,
                                                     usernameVariable: 'ACCOUNT_USERNAME',
                                                     passwordVariable: 'ACCOUNT_PASSWORD')]) {
                        def testsToRun = [:]
                        def allureResultsHostPath = "${WORKSPACE}/output/allure-results"

                        if (params.RUN_WEB_TESTS) {
                            testsToRun['Web测试'] = {
                                echo "执行Web测试 (并发: auto, 重试: 2)"
                                sh """
                                docker run --rm --name pytest-web-${BUILD_NUMBER} \\
                                  -e APP_ENV=${params.APP_ENV} \\
                                  -e TEST_PLATFORM="web" \\
                                  -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_USERNAME' : 'TEST_DEFAULT_USERNAME'}="${ACCOUNT_USERNAME}" \\
                                  -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_PASSWORD' : 'TEST_DEFAULT_PASSWORD'}="${ACCOUNT_PASSWORD}" \\
                                  -e TEST_SUITE="${env.TEST_SUITE_VALUE}" \\
                                  -e WEB_BASE_URL="${env.WEB_URL}" \\
                                  -e TZ="Asia/Shanghai" \\
                                  -e ALLUREDIR="/results_out" \\
                                  -e PYTEST_PARALLEL="auto" \\
                                  -e PYTEST_RERUNS="2" \\
                                  -e SKIP_REPORT="true" \\
                                  -e SKIP_NOTIFY="true" \\
                                  -v ${allureResultsHostPath}:/results_out:rw \\
                                  --workdir /app \\
                                  -v /etc/localtime:/etc/localtime:ro \\
                                  --network host \\
                                  ${env.DOCKER_IMAGE} \\
                                  python ci/scripts/run_and_notify.py
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
                                  -e API_BASE_URL="${env.API_URL}" \\
                                  -e TZ="Asia/Shanghai" \\
                                  -e ALLUREDIR="/results_out" \\
                                  -e PYTEST_PARALLEL="auto" \\
                                  -e PYTEST_RERUNS="2" \\
                                  -e SKIP_REPORT="true" \\
                                  -e SKIP_NOTIFY="true" \\
                                  -v ${allureResultsHostPath}:/results_out:rw \\
                                  --workdir /app \\
                                  -v /etc/localtime:/etc/localtime:ro \\
                                  --network host \\
                                  ${env.DOCKER_IMAGE} \\
                                  python ci/scripts/run_and_notify.py
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
                                  -e ALLUREDIR="/results_out" \\
                                  -e PYTEST_PARALLEL="auto" \\
                                  -e PYTEST_RERUNS="2" \\
                                  -e SKIP_REPORT="true" \\
                                  -e SKIP_NOTIFY="true" \\
                                  -v ${allureResultsHostPath}:/results_out:rw \\
                                  --workdir /app \\
                                  -v /etc/localtime:/etc/localtime:ro \\
                                  --network host \\
                                  ${env.DOCKER_IMAGE} \\
                                  python ci/scripts/run_and_notify.py
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
                                  -e ALLUREDIR="/results_out" \\
                                  -e PYTEST_PARALLEL="auto" \\
                                  -e PYTEST_RERUNS="2" \\
                                  -e SKIP_REPORT="true" \\
                                  -e SKIP_NOTIFY="true" \\
                                  -v ${allureResultsHostPath}:/results_out:rw \\
                                  --workdir /app \\
                                  -v /etc/localtime:/etc/localtime:ro \\
                                  --network host \\
                                  ${env.DOCKER_IMAGE} \\
                                  python ci/scripts/run_and_notify.py
                                """
                            }
                        } else { echo "跳过App测试" }

                        if (!testsToRun.isEmpty()) {
                             echo "开始并行执行选定的测试..."
                             parallel testsToRun
                        } else {
                             echo "没有选择任何测试平台，跳过测试执行。"
                             sh "mkdir -p ${allureResultsHostPath}"
                        }
                    } // End withCredentials
                } // End script
            } // End steps
        } // End stage '并行执行测试'

           stage('生成报告与通知') {
               steps {
                    script {
                       withCredentials([string(credentialsId: env.EMAIL_PASSWORD_CREDENTIALS_ID, variable: 'EMAIL_PASSWORD')]) {
                           // 定义宿主机路径变量
                           def allureResultsHostPath = "${WORKSPACE}/output/allure-results"
                           def allureReportHostPath = "${WORKSPACE}/output/reports/allure-report"
                           def scriptsHostPath = "${WORKSPACE}/ci/scripts" // 脚本在宿主机的路径

                           echo "检查 Docker 镜像内部的 /app/ci/scripts/ 目录内容..."
                           sh "docker run --rm --name check-scripts-${BUILD_NUMBER} ${env.DOCKER_IMAGE} ls -la /app/ci/scripts/ || echo '>>> 无法列出镜像内 /app/ci/scripts/ 目录 <<<'"

                           echo "写入 Allure 元数据文件到 ${allureResultsHostPath} (在容器内执行)..."
                           // 执行外部 Python 脚本
                           sh """
                           docker run --rm --name write-metadata-${BUILD_NUMBER} \\
                             -e APP_ENV=${params.APP_ENV} \\
                             -e CI_NAME="${env.CI_NAME}" \\
                             -e BUILD_NUMBER=${BUILD_NUMBER} \\
                             -e BUILD_URL=${env.BUILD_URL} \\
                             -e JOB_NAME=${env.JOB_NAME} \\
                             -v ${allureResultsHostPath}:/results_out:rw \\
                             -v /etc/localtime:/etc/localtime:ro \\
                             --user root \\
                             ${env.DOCKER_IMAGE} \\
                             python /app/ci/scripts/write_allure_metadata.py /results_out
                           """
                           echo "Allure 元数据写入完成。"

                           echo "开始生成 Allure 报告..."
                           sh """
                           echo "--- Generating Allure report from host results in ${allureResultsHostPath} ---"
                           docker run --rm --name allure-generate-${BUILD_NUMBER} \\
                             -v ${allureResultsHostPath}:/results:ro \\
                             -v ${allureReportHostPath}:/report:rw \\
                             -v /etc/localtime:/etc/localtime:ro \\
                             --user root \\
                             ${env.DOCKER_IMAGE} \\
                             /bin/bash -c "echo 'Generating report...'; ls -la /results; allure generate /results -o /report --clean"

                           echo "Allure 报告已生成到 ${allureReportHostPath}"
                           """

                           echo "准备 Nginx 目录..."
                           sh """
                           docker run --rm --name prep-nginx-dir-${BUILD_NUMBER} \\
                             -v ${env.ALLURE_NGINX_HOST_PATH}:/nginx_dir:rw \\
                             -v ${scriptsHostPath}:/scripts:ro \\
                             --user root \\
                             alpine:latest \\
                             sh /scripts/prepare_nginx_dir.sh /nginx_dir
                           """

                           echo "部署 Allure 报告 (处理历史记录、复制文件、修正权限)..."
                           sh """
                           docker run --rm --name deploy-report-${BUILD_NUMBER} \\
                             -v ${allureReportHostPath}:/src_report:ro \\
                             -v ${env.ALLURE_NGINX_HOST_PATH}:/dest_nginx:rw \\
                             -v ${scriptsHostPath}:/scripts:ro \\
                             --user root \\
                             alpine:latest \\
                             sh /scripts/deploy_allure_report.sh /src_report /dest_nginx
                           """
                           echo "报告已部署到 Nginx 目录。"


                           echo "发送邮件通知..."
                           sh """
                           echo "--- Sending notification email via run_and_notify.py ---"
                           docker run --rm --name notify-${BUILD_NUMBER} \\
                             -e CI=true \\
                             -e CI_NAME="${env.CI_NAME}" \\
                             -e APP_ENV=${params.APP_ENV} \\
                             -e EMAIL_ENABLED=${params.SEND_EMAIL} \\
                             -e EMAIL_PASSWORD='${EMAIL_PASSWORD}' \\
                             -e EMAIL_SMTP_SERVER="smtp.qiye.aliyun.com" \\
                             -e EMAIL_SMTP_PORT=465 \\
                             -e EMAIL_SENDER="yzx@ylmt2b.com" \\
                             -e EMAIL_RECIPIENTS="yzx@ylmt2b.com" \\
                             -e EMAIL_USE_SSL=true \\
                             -e ALLURE_PUBLIC_URL="${env.ALLURE_PUBLIC_URL}" \\
                             -e TZ="Asia/Shanghai" \\
                             -e ALLURE_RESULTS_DIR=/results \\
                             -e ALLURE_REPORT_DIR=/report \\
                             -v ${allureResultsHostPath}:/results:ro \\
                             -v ${allureReportHostPath}:/report:ro \\
                             -v /etc/localtime:/etc/localtime:ro \\
                             --network host \\
                             ${env.DOCKER_IMAGE} \\
                             cd /app && python ci/scripts/run_and_notify.py
                           echo "通知脚本执行完毕。"
                           """

                       } // End withCredentials
                    } // End script
               } // End steps
           } // End stage '生成报告与通知'
       } // End stages

       post {
           always {
               echo "Pipeline 完成. 清理工作空间..."
               script {
                   def testTypes = []
                   if (params.RUN_WEB_TESTS) testTypes.add("Web")
                   if (params.RUN_API_TESTS) testTypes.add("API")
                   if (params.RUN_WECHAT_TESTS) testTypes.add("微信")
                   if (params.RUN_APP_TESTS) testTypes.add("App")
                   if (testTypes.isEmpty()) testTypes.add("未选择")
                   currentBuild.description = "${params.APP_ENV.toUpperCase()} 环境 [${testTypes.join(', ')}] - <a href='${env.ALLURE_PUBLIC_URL}' target='_blank'>查看报告</a>"
               }
               cleanWs()
               echo "工作空间已清理。"
               // 注意：下面这行清理可能无效或多余，因为脚本似乎并未在 WORKSPACE 创建此文件
               sh "rm -f ${WORKSPACE}/tmp_write_metadata.py || true"
               echo "临时脚本文件已清理。"
           }
           success {
               echo "Pipeline 成功完成！"
           }
           failure {
               echo "Pipeline 执行失败，请检查控制台输出获取详细信息。"
           }
       } // End post
   } // End pipeline