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
        // **新增:** 定义 CI_NAME 环境变量，方便后续步骤使用
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
                docker run --rm \\
                  -v /usr/share/nginx/html:/nginx_html \\
                  --user root \\
                  alpine:latest \\
                  sh -c "mkdir -p /nginx_html/${ALLURE_NGINX_DIR_NAME} && chmod -R 777 /nginx_html/${ALLURE_NGINX_DIR_NAME}"

                echo "环境准备完成。"
                """
            }
        }

        stage('并行执行测试') {
             steps {
                script {
                    def accountCredentialsId = (params.APP_ENV == 'prod') ? env.PROD_ENV_CREDENTIALS_ID : env.TEST_ENV_CREDENTIALS_ID
                    echo "选择凭据 ID: ${accountCredentialsId} 用于测试账户"

                    withCredentials([usernamePassword(credentialsId: accountCredentialsId,
                                                     usernameVariable: 'ACCOUNT_USERNAME',
                                                     passwordVariable: 'ACCOUNT_PASSWORD')]) {
                        def testsToRun = [:]
                        def allureResultsHostPath = "${WORKSPACE}/output/allure-results" // 定义宿主机结果路径

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
                                  -v ${WORKSPACE}:/workspace_host:ro \\
                                  -v ${allureResultsHostPath}:/results_out:rw \\
                                  --workdir /app \\
                                  -v /etc/localtime:/etc/localtime:ro \\
                                  --network host \\
                                  ${env.DOCKER_IMAGE} \\
                                  /bin/bash -c " \\
                                    echo '--- Running tests via run_and_notify.py ---'; \\
                                    echo 'Copying project files from /workspace_host to /app...'; \\
                                    cp -r /workspace_host/. /app/; \\
                                    echo 'Files copied. Running tests...'; \\
                                    cd /app && python ci/scripts/run_and_notify.py \\
                                  "
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
                                  -v ${WORKSPACE}:/workspace_host:ro \\
                                  -v ${allureResultsHostPath}:/results_out:rw \\
                                  --workdir /app \\
                                  -v /etc/localtime:/etc/localtime:ro \\
                                  --network host \\
                                  ${env.DOCKER_IMAGE} \\
                                  /bin/bash -c " \\
                                    echo '--- Running tests via run_and_notify.py ---' && \\
                                    echo 'Copying project files from /workspace_host to /app...' && cp -r /workspace_host/. /app/ && \\
                                    echo 'Files copied. Running tests...' && \\
                                    cd /app && python ci/scripts/run_and_notify.py \\
                                  "
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
                                  -v ${WORKSPACE}:/workspace_host:ro \\
                                  -v ${allureResultsHostPath}:/results_out:rw \\
                                  --workdir /app \\
                                  -v /etc/localtime:/etc/localtime:ro \\
                                  --network host \\
                                  ${env.DOCKER_IMAGE} \\
                                  /bin/bash -c " \\
                                    echo '--- Running tests via run_and_notify.py ---' && \\
                                    echo 'Copying project files from /workspace_host to /app...' && cp -r /workspace_host/. /app/ && \\
                                    echo 'Files copied. Running tests...' && \\
                                    cd /app && python ci/scripts/run_and_notify.py \\
                                  "
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
                                  -v ${WORKSPACE}:/workspace_host:ro \\
                                  -v ${allureResultsHostPath}:/results_out:rw \\
                                  --workdir /app \\
                                  -v /etc/localtime:/etc/localtime:ro \\
                                  --network host \\
                                  ${env.DOCKER_IMAGE} \\
                                  /bin/bash -c " \\
                                    echo '--- Running tests via run_and_notify.py ---' && \\
                                    echo 'Copying project files from /workspace_host to /app...' && cp -r /workspace_host/. /app/ && \\
                                    echo 'Files copied. Running tests...' && \\
                                    cd /app && python ci/scripts/run_and_notify.py \\
                                  "
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

                        echo "写入 Allure 元数据文件到 ${allureResultsHostPath} (在容器内执行)..."
                        // **修改点:** 使用 docker run 执行 Python 脚本
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
                          /bin/bash -c " \\
                            echo '--- Writing Allure metadata inside container (Target: /results_out) ---' && \\
                            python - << EOF
import os
import json
import datetime

# Python 脚本现在写入到容器内挂载的 /results_out 目录
allure_results_dir = '/results_out'

# 从容器环境变量获取信息
app_env = os.environ.get('APP_ENV', 'unknown')
ci_name = os.environ.get('CI_NAME', 'Jenkins')
build_number = os.environ.get('BUILD_NUMBER', 'unknown')
build_url = os.environ.get('BUILD_URL', 'unknown')
job_name = os.environ.get('JOB_NAME', 'unknown')

print(f'为Allure报告生成元数据信息')
print(f'环境: {app_env}')
print(f'CI名称: {ci_name}')
print(f'构建号: {build_number}')
print(f'结果目录: {allure_results_dir}')

try:
    os.makedirs(allure_results_dir, exist_ok=True)
except Exception as e:
    print(f'创建结果目录失败: {e}')
    exit(1) # 创建失败则退出

environment = {
    'APP_ENV': app_env,
    'Build Number': build_number,
    'Build URL': build_url,
    'Job Name': job_name,
    'CI': ci_name,
    'Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}
try:
    env_file_path = os.path.join(allure_results_dir, 'environment.properties')
    with open(env_file_path, 'w', encoding='utf-8') as f:
        for key, value in environment.items():
            f.write(f'{key}={value}\\n') # Python heredoc 不需要额外转义 \n
    print(f'环境信息写入成功: {env_file_path}')
except Exception as e:
    print(f'写入环境信息失败: {e}')

executor = {
    'name': ci_name,
    'type': 'jenkins',
    'url': build_url,
    'buildName': f'{job_name} #{build_number}',
    'buildUrl': build_url
}
try:
    exec_file_path = os.path.join(allure_results_dir, 'executor.json')
    with open(exec_file_path, 'w', encoding='utf-8') as f:
        json.dump(executor, f, ensure_ascii=False, indent=2)
    print(f'执行器信息写入成功: {exec_file_path}')
except Exception as e:
    print(f'写入执行器信息失败: {e}')

categories = [
    {
        'name': '测试失败',
        'matchedStatuses': ['failed'],
        'messageRegex': '.*AssertionError.*'
    },
    {
        'name': '环境问题',
        'matchedStatuses': ['broken', 'failed'],
        'messageRegex': '.*(ConnectionError|TimeoutError|WebDriverException).*'
    },
    {
        'name': '产品缺陷',
        'matchedStatuses': ['failed'],
        'messageRegex': '.*预期结果与实际结果不符.*'
    }
]
try:
    cat_file_path = os.path.join(allure_results_dir, 'categories.json')
    with open(cat_file_path, 'w', encoding='utf-8') as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)
    print(f'分类信息写入成功: {cat_file_path}')
except Exception as e:
    print(f'写入分类信息失败: {e}')

print('元数据写入脚本执行完毕')
EOF
                          " # End of bash -c command
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

                        echo "复制报告到 Nginx 目录并修正权限..."
                        sh """
                        echo "--- Copying generated report from host path ${allureReportHostPath} to Nginx directory ${env.ALLURE_NGINX_HOST_PATH} and fixing permissions ---"
                        # 首先确保目标目录存在，并处理历史数据目录
                        docker run --rm --name prep-nginx-dir-${BUILD_NUMBER} \
                          -v ${env.ALLURE_NGINX_HOST_PATH}:/nginx_dir:rw \
                          --user root \
                          alpine:latest \
                          sh -c "\
                            echo 'Preparing Nginx directory...' && \
                            mkdir -p /nginx_dir && \
                            mkdir -p /nginx_dir/history && \
                            find /nginx_dir -type d -exec chmod 755 {} \\; && \
                            find /nginx_dir -type f -exec chmod 644 {} \\; && \
                            echo 'Nginx directory prepared.'\
                          "
                          
                        # 确保历史目录存在并保持不变
                        docker run --rm --name preserve-history-${BUILD_NUMBER} \
                          -v ${env.ALLURE_NGINX_HOST_PATH}:/dest:rw \
                          -v ${allureReportHostPath}:/src:ro \
                          --user root \
                          alpine:latest \
                          sh -c "\
                            echo 'Preserving history directory...' && \
                            if [ -d '/dest/history' ]; then \
                              echo 'History directory exists, backing up...' && \
                              mkdir -p /tmp/history_backup && \
                              cp -rp /dest/history/* /tmp/history_backup/ || echo 'No files to copy' && \
                              echo 'Ensuring UTF-8 encoding for JSON files...' && \
                              find /tmp/history_backup -name '*.json' -type f -exec sh -c '\
                                FILE={} && \
                                TEMP_FILE=\$(mktemp) && \
                                cat \$FILE > \$TEMP_FILE && \
                                mv \$TEMP_FILE \$FILE\
                              ' \\; || echo 'No JSON files found' \
                            else \
                              echo 'No history directory found, will create empty one' && \
                              mkdir -p /dest/history && \
                              echo '{}' > /dest/history/history.json && \
                              echo '[]' > /dest/history/history-trend.json && \
                              echo '[]' > /dest/history/duration-trend.json && \
                              echo '[]' > /dest/history/categories-trend.json && \
                              echo '[]' > /dest/history/retry-trend.json \
                            fi && \
                            echo 'History directory preserved.'\
                          "

                        # 复制报告并保持历史数据
                        docker run --rm --name report-copy-perm-${BUILD_NUMBER} \
                          -v ${allureReportHostPath}:/src:ro \
                          -v ${env.ALLURE_NGINX_HOST_PATH}:/dest:rw \
                          --user root \
                          alpine:latest \
                          sh -c "\
                            echo 'Copying files...' && \
                            if [ -d '/dest/history' ]; then \
                              echo 'Backing up history directory...' && \
                              mkdir -p /tmp/history && \
                              cp -rp /dest/history/* /tmp/history/ || echo 'No history files to backup' \
                            fi && \
                            echo 'Copying report files...' && \
                            cp -rf /src/* /dest/ && \
                            if [ -d '/tmp/history' ]; then \
                              echo 'Restoring history directory...' && \
                              mkdir -p /dest/history && \
                              cp -rf /tmp/history/* /dest/history/ || echo 'No history files to restore' \
                            fi && \
                            echo 'Setting UTF-8 encoding for JSON files...' && \
                            find /dest -name '*.json' -type f -exec sh -c '\
                              FILE={} && \
                              if [ -s \"\$FILE\" ]; then \
                                mv \"\$FILE\" \"\$FILE.bak\" && \
                                cat \"\$FILE.bak\" > \"\$FILE\" && \
                                rm \"\$FILE.bak\" \
                              fi\
                            ' \\; || echo 'No JSON files to process' && \
                            echo 'Fixing permissions...' && \
                            chmod -R 755 /dest/\
                          "
                        echo "报告已复制到 Nginx 目录并修正权限。"
                        """

                        echo "发送邮件通知..."
                        // 直接复用 run_and_notify.py 脚本
                        sh """
                        echo "--- Sending notification email via run_and_notify.py ---"
                        docker run --rm --name notify-${BUILD_NUMBER} \
                          -e CI=true \
                          -e CI_NAME="${env.CI_NAME}" \
                          -e APP_ENV=${params.APP_ENV} \
                          -e EMAIL_ENABLED=${params.SEND_EMAIL} \
                          -e EMAIL_PASSWORD='${EMAIL_PASSWORD}' \
                          -e EMAIL_SMTP_SERVER="smtp.qiye.aliyun.com" \
                          -e EMAIL_SMTP_PORT=465 \
                          -e EMAIL_SENDER="yzx@ylmt2b.com" \
                          -e EMAIL_RECIPIENTS="yzx@ylmt2b.com" \
                          -e EMAIL_USE_SSL=true \
                          -e ALLURE_PUBLIC_URL="${env.ALLURE_PUBLIC_URL}" \
                          -e TZ="Asia/Shanghai" \
                          -e ALLURE_RESULTS_DIR=/results \
                          -e ALLURE_REPORT_DIR=/report \
                          -v ${allureResultsHostPath}:/results:ro \
                          -v ${allureReportHostPath}:/report:ro \
                          -v /etc/localtime:/etc/localtime:ro \
                          -v ${WORKSPACE}:/workspace_host:ro \
                          --network host \
                          ${env.DOCKER_IMAGE} \
                          /bin/bash -c "\
                            echo '--- 复制项目文件到容器内 ---'; \
                            cp -r /workspace_host/. /app/; \
                            echo '检查通知脚本是否存在...'; \
                            ls -la /app/ci/scripts/; \
                            echo '执行邮件通知脚本...'; \
                            cd /app && python ci/scripts/run_and_notify.py \
                          "
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