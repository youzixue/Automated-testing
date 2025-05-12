// Jenkinsfile
pipeline {
    agent any // Globale agent, viele Schritte überschreiben dies mit Docker-Agent

    parameters {
        choice(name: 'APP_ENV', choices: ['test', 'prod'], description: '选择测试环境')
        booleanParam(name: 'RUN_WEB_TESTS', defaultValue: true, description: '运行Web测试')
        booleanParam(name: 'RUN_API_TESTS', defaultValue: true, description: '运行API测试')
        booleanParam(name: 'RUN_APP_RELATED_TESTS', defaultValue: true, description: '运行App相关测试 (Mobile 和/或 WeChat)')

        string(name: 'PRIMARY_APP_DEVICE_SERIAL', 
               defaultValue: '20a2da8d', 
               description: '主App测试设备ID (序列号)。如果只用一台设备，请只配置这个。', 
               trim: true)
        string(name: 'SECONDARY_APP_DEVICE_SERIAL', 
               defaultValue: '', 
               description: '可选的第二台App测试设备ID。如果留空或与主设备相同，则App/WeChat测试会在主设备上串行。否则Mobile在主设备，WeChat在次设备并行。', 
               trim: true)
        string(name: 'JIYU_APP_PACKAGE', 
               defaultValue: 'com.zsck.yq', 
               description: '积余App的包名', 
               trim: true)
        string(name: 'WECHAT_APP_PACKAGE', 
               defaultValue: 'com.tencent.mm', 
               description: '微信App的包名', 
               trim: true)

        choice(name: 'TEST_SUITE', choices: ['全部', '冒烟测试', '回归测试'], description: '选择测试套件')
        booleanParam(name: 'SEND_EMAIL', defaultValue: true, description: '是否发送邮件通知')
    }

    environment {
        GIT_CREDENTIALS_ID = 'git-credentials'
        GIT_REPO_URL_CREDENTIAL_ID = 'git-repo-url'
        TEST_ENV_CREDENTIALS_ID = 'test-env-credentials'
        PROD_ENV_CREDENTIALS_ID = 'prod-env-credentials'
        TEST_WEB_URL_CREDENTIAL_ID = 'test-web-url'
        TEST_API_URL_CREDENTIAL_ID = 'test-api-url'
        PROD_WEB_URL_CREDENTIAL_ID = 'prod-web-url'
        PROD_API_URL_CREDENTIAL_ID = 'prod-api-url'

        TEST_PAYMENT_API_KEY_CREDENTIAL_ID = 'test-payment-api-key'
        TEST_PAYMENT_MCH_ID_CREDENTIAL_ID = 'test-payment-mch-id'
        TEST_PAYMENT_DEVICE_INFO_CREDENTIAL_ID = 'test-payment-device-info'
        PROD_PAYMENT_API_KEY_CREDENTIAL_ID = 'prod-payment-api-key'
        PROD_PAYMENT_MCH_ID_CREDENTIAL_ID = 'prod-payment-mch-id'
        PROD_PAYMENT_DEVICE_INFO_CREDENTIAL_ID = 'prod-payment-device-info'

        EMAIL_PASSWORD_CREDENTIALS_ID = 'email-password-credential'
        EMAIL_SMTP_SERVER_CREDENTIAL_ID = 'email-smtp-server'
        EMAIL_SMTP_PORT_CREDENTIAL_ID = 'email-smtp-port'
        EMAIL_SENDER_CREDENTIAL_ID = 'email-sender'
        EMAIL_RECIPIENTS_CREDENTIAL_ID = 'email-recipients'
        EMAIL_USE_SSL_CREDENTIAL_ID = 'email-use-ssl'

        HOST_ADB_KEYS_ANDROID_DIR = '/home/minipc/my_device_adb_keys/.android' 

        HOST_JENKINS_HOME_ON_HOST = '/var/lib/docker/volumes/jenkins_home/_data' 
        HOST_WORKSPACE_PATH = "${HOST_JENKINS_HOME_ON_HOST}/workspace/${env.JOB_NAME}" 
        HOST_ALLURE_RESULTS_PATH = "${HOST_WORKSPACE_PATH}/output/allure-results" 
        HOST_ALLURE_REPORT_PATH = "${HOST_WORKSPACE_PATH}/output/reports/temp-allure-report-for-summary"

        TEST_SUITE_VALUE = "${params.TEST_SUITE == '全部' ? 'all' : (params.TEST_SUITE == '冒烟测试' ? 'smoke' : 'regression')}"
        DOCKER_IMAGE = "automated-testing:dev" 
    }

    stages {
        stage('检出代码') {
            steps {
                withCredentials([
                    string(credentialsId: env.GIT_REPO_URL_CREDENTIAL_ID, variable: 'INJECTED_GIT_REPO_URL'),
                    usernamePassword(credentialsId: env.GIT_CREDENTIALS_ID, usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')
                ]) {
                    echo "从代码仓库拉取最新代码: ${INJECTED_GIT_REPO_URL}"
                    cleanWs()
                    checkout([
                        $class: 'GitSCM',
                        branches: [[name: '*/main']], 
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

        stage('检查脚本文件') {
            steps {
                echo "检查脚本文件是否存在于 Agent 路径: ${WORKSPACE}/ci/scripts/ ..."
                sh "ls -la ${WORKSPACE}/ci/scripts/ || echo '>>> ci/scripts/ 目录不存在或无法列出 <<<' "
                sh "test -f ${WORKSPACE}/ci/scripts/write_allure_metadata.py && echo '>>> write_allure_metadata.py 存在于 Agent <<< ' || echo '>>> write_allure_metadata.py 不存在于 Agent! <<<' "
                sh "test -f ${WORKSPACE}/ci/scripts/run_and_notify.py && echo '>>> run_and_notify.py 存在于 Agent <<< ' || echo '>>> run_and_notify.py 不存在于 Agent! <<<' "
            }
        }

        stage('执行测试') {
             steps {
                script {
                    def accountCredentialsId = (params.APP_ENV == 'prod') ? env.PROD_ENV_CREDENTIALS_ID : env.TEST_ENV_CREDENTIALS_ID
                    def webUrlCredentialId = (params.APP_ENV == 'prod') ? env.PROD_WEB_URL_CREDENTIAL_ID : env.TEST_WEB_URL_CREDENTIAL_ID
                    def apiUrlCredentialId = (params.APP_ENV == 'prod') ? env.PROD_API_URL_CREDENTIAL_ID : env.TEST_API_URL_CREDENTIAL_ID
                    def paymentApiKeyCredentialId = (params.APP_ENV == 'prod') ? env.PROD_PAYMENT_API_KEY_CREDENTIAL_ID : env.TEST_PAYMENT_API_KEY_CREDENTIAL_ID
                    def paymentMchIdCredentialId = (params.APP_ENV == 'prod') ? env.PROD_PAYMENT_MCH_ID_CREDENTIAL_ID : env.TEST_PAYMENT_MCH_ID_CREDENTIAL_ID
                    def paymentDeviceInfoCredentialId = (params.APP_ENV == 'prod') ? env.PROD_PAYMENT_DEVICE_INFO_CREDENTIAL_ID : env.TEST_PAYMENT_DEVICE_INFO_CREDENTIAL_ID

                    try {
                        withCredentials([
                            usernamePassword(credentialsId: accountCredentialsId, usernameVariable: 'ACCOUNT_USERNAME', passwordVariable: 'ACCOUNT_PASSWORD'),
                            string(credentialsId: webUrlCredentialId, variable: 'INJECTED_WEB_URL'),
                            string(credentialsId: apiUrlCredentialId, variable: 'INJECTED_API_URL')
                        ]) {
                            def parallelWebAndApiTests = [:] 

                            if (params.RUN_WEB_TESTS) {
                                parallelWebAndApiTests['Web测试'] = {
                                    echo "执行Web测试 (并发: auto, 重试: 2)"
                                    sh """
                                    docker run --rm --name pytest-web-${BUILD_NUMBER} \
                                      -e APP_ENV=${params.APP_ENV} \
                                      -e TEST_PLATFORM="web" \
                                      -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_USERNAME' : 'TEST_DEFAULT_USERNAME'}="${ACCOUNT_USERNAME}" \
                                      -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_PASSWORD' : 'TEST_DEFAULT_PASSWORD'}="${ACCOUNT_PASSWORD}" \
                                      -e TEST_SUITE="${env.TEST_SUITE_VALUE}" \
                                      -e WEB_BASE_URL="${INJECTED_WEB_URL}" \
                                      -e TZ="Asia/Shanghai" \
                                      -v ${env.HOST_WORKSPACE_PATH}:/workspace:rw \
                                      -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \
                                      --workdir /workspace \
                                      -v /etc/localtime:/etc/localtime:ro \
                                      --network host \
                                      ${env.DOCKER_IMAGE} \
                                      pytest tests/web -n auto --reruns 2 -v --alluredir=/results_out
                                    """
                                }
                            } else { echo "跳过Web测试" }

                            if (params.RUN_API_TESTS) {
                                parallelWebAndApiTests['API测试'] = {
                                    echo "执行API测试 (并发: auto, 重试: 2)"
                                    withCredentials([ 
                                        string(credentialsId: paymentApiKeyCredentialId, variable: 'INJECTED_PAYMENT_API_KEY'),
                                        string(credentialsId: paymentMchIdCredentialId, variable: 'INJECTED_PAYMENT_MCH_ID'),
                                        string(credentialsId: paymentDeviceInfoCredentialId, variable: 'INJECTED_PAYMENT_DEVICE_INFO')
                                    ]) {
                                        def paymentEnvVars = "-e ${params.APP_ENV == 'prod' ? 'PROD_PAYMENT_API_KEY' : 'PAYMENT_API_KEY'}='${INJECTED_PAYMENT_API_KEY}' " +
                                                             "-e ${params.APP_ENV == 'prod' ? 'PROD_MCH_ID' : 'PAYMENT_MCH_ID'}='${INJECTED_PAYMENT_MCH_ID}' "
                                        if (paymentDeviceInfoCredentialId) { 
                                           paymentEnvVars += "-e ${params.APP_ENV == 'prod' ? 'PROD_DEVICE_INFO' : 'PAYMENT_DEVICE_INFO'}='${INJECTED_PAYMENT_DEVICE_INFO}' "
                                        }
                                        sh """
                                        docker run --rm --name pytest-api-${BUILD_NUMBER} \
                                          -e APP_ENV=${params.APP_ENV} \
                                          -e TEST_PLATFORM="api" \
                                          -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_USERNAME' : 'TEST_DEFAULT_USERNAME'}="${ACCOUNT_USERNAME}" \
                                          -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_PASSWORD' : 'TEST_DEFAULT_PASSWORD'}="${ACCOUNT_PASSWORD}" \
                                          -e TEST_SUITE="${env.TEST_SUITE_VALUE}" \
                                          -e API_BASE_URL="${INJECTED_API_URL}" \
                                          ${paymentEnvVars} \
                                          -e TZ="Asia/Shanghai" \
                                          -v ${env.HOST_WORKSPACE_PATH}:/workspace:rw \
                                          -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \
                                          --workdir /workspace \
                                          -v /etc/localtime:/etc/localtime:ro \
                                          --network host \
                                          ${env.DOCKER_IMAGE} \
                                          pytest tests/api -n auto --reruns 2 -v --alluredir=/results_out
                                        """
                                    }
                                }
                            } else { echo "跳过API测试" }

                            if (!parallelWebAndApiTests.isEmpty()) {
                                 echo "开始并行执行Web和API测试..."
                                 parallel parallelWebAndApiTests
                            } else {
                                 echo "Web和API测试均未选择。"
                            }

                            if (params.RUN_APP_RELATED_TESTS) {
                                def primaryDeviceSerial = params.PRIMARY_APP_DEVICE_SERIAL.trim()
                                def secondaryDeviceSerial = params.SECONDARY_APP_DEVICE_SERIAL.trim()

                                boolean useTwoDevices = false
                                if (primaryDeviceSerial && !primaryDeviceSerial.isEmpty() && 
                                    secondaryDeviceSerial && !secondaryDeviceSerial.isEmpty() && 
                                    primaryDeviceSerial != secondaryDeviceSerial) {
                                    useTwoDevices = true
                                    echo "检测到两台不同设备，Mobile测试将在主设备(${primaryDeviceSerial})运行，WeChat测试将在次设备(${secondaryDeviceSerial})运行，两者并行。"
                                } else if (primaryDeviceSerial && !primaryDeviceSerial.isEmpty()) {
                                    echo "只使用一台主设备 (${primaryDeviceSerial})。Mobile和WeChat测试将在此设备上串行执行。"
                                } else {
                                    error "[错误]：未指定主App测试设备 (PRIMARY_APP_DEVICE_SERIAL 为空)。无法执行App相关测试。"
                                }
                                
                                if (primaryDeviceSerial && !primaryDeviceSerial.isEmpty()) {
                                    // 设备检查仍然保留，以确保在运行实际测试前设备仍然可见
                                    sh """
                                    echo "在容器内再次检查主设备 ${primaryDeviceSerial} ..."
                                    docker run --rm --name adb-recheck-main-${BUILD_NUMBER} \
                                      -v "${env.HOST_ADB_KEYS_ANDROID_DIR}":/root/.android \
                                      --privileged \
                                      --network host -e ANDROID_SERIAL="${primaryDeviceSerial}" \
                                      ${env.DOCKER_IMAGE} sh -c " \
                                        echo '--- ADB devices output (recheck main device) ---'; \
                                        adb devices; \
                                        echo '--- Grepping for ${primaryDeviceSerial}[[:space:]]device (recheck main device) ---'; \
                                        adb devices | grep '${primaryDeviceSerial}[[:space:]]device' && echo 'Grep SUCCESSFUL (recheck main device)' || (echo 'Grep FAILED (recheck main device), exiting...' && exit 1) \
                                      " || (echo "错误: 容器内再次检查主设备 ${primaryDeviceSerial} 的脚本执行失败或设备未找到/未授权!" && exit 1)
                                    echo "容器内主设备 ${primaryDeviceSerial} 再次检查通过。"
                                    """
                                    if (useTwoDevices) { 
                                         sh """
                                        echo "在容器内再次检查次设备 ${secondaryDeviceSerial} ..."
                                        docker run --rm --name adb-recheck-sec-${BUILD_NUMBER} \
                                          -v "${env.HOST_ADB_KEYS_ANDROID_DIR}":/root/.android \
                                          --privileged \
                                          --network host -e ANDROID_SERIAL="${secondaryDeviceSerial}" \
                                          ${env.DOCKER_IMAGE} sh -c " \
                                            echo '--- ADB devices output (recheck secondary device) ---'; \
                                            adb devices; \
                                            echo '--- Grepping for ${secondaryDeviceSerial}[[:space:]]device (recheck secondary device) ---'; \
                                            adb devices | grep '${secondaryDeviceSerial}[[:space:]]device' && echo 'Grep SUCCESSFUL (recheck secondary device)' || (echo 'Grep FAILED (recheck secondary device), exiting...' && exit 1) \
                                          " || (echo "错误: 容器内再次检查次设备 ${secondaryDeviceSerial} 的脚本执行失败或设备未找到/未授权!" && exit 1)
                                        echo "容器内次设备 ${secondaryDeviceSerial} 再次检查通过。"
                                        """
                                    }

                                    // 开始实际测试执行
                                    def runMobileTests = { String deviceSerial -> // 明确参数类型
                                        echo "在设备 ${deviceSerial} 上执行 tests/mobile"
                                        sh """
                                        docker run --rm --name pytest-mobile-${BUILD_NUMBER}-${deviceSerial} \\
                                          -e APP_ENV=${params.APP_ENV} \\
                                          -e TEST_PLATFORM="mobile" \\
                                          -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_USERNAME' : 'TEST_DEFAULT_USERNAME'}="${ACCOUNT_USERNAME}" \\
                                          -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_PASSWORD' : 'TEST_DEFAULT_PASSWORD'}="${ACCOUNT_PASSWORD}" \\
                                          -e TEST_SUITE="${env.TEST_SUITE_VALUE}" \\
                                          -e ANDROID_SERIAL="${deviceSerial}" \\
                                          -e DEVICE_URI="Android:///${deviceSerial}" \\
                                          -e JIYU_APP_PACKAGE_NAME="${params.JIYU_APP_PACKAGE}" \\
                                          -e TZ="Asia/Shanghai" \\
                                          -v ${env.HOST_WORKSPACE_PATH}:/workspace:rw \\
                                          -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \\
                                          -v "${env.HOST_ADB_KEYS_ANDROID_DIR}":/root/.android \\
                                          --privileged \\
                                          --network host \\
                                          --workdir /workspace \\
                                          -v /etc/localtime:/etc/localtime:ro \\
                                          ${env.DOCKER_IMAGE} \\
                                          pytest tests/mobile -v --alluredir=/results_out
                                        """
                                    }
                                    def runWechatTests = { String deviceSerial -> // 明确参数类型
                                        echo "在设备 ${deviceSerial} 上执行 tests/wechat"
                                        sh """
                                        docker run --rm --name pytest-wechat-${BUILD_NUMBER}-${deviceSerial} \\
                                          -e APP_ENV=${params.APP_ENV} \\
                                          -e TEST_PLATFORM="wechat" \\
                                          -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_USERNAME' : 'TEST_DEFAULT_USERNAME'}="${ACCOUNT_USERNAME}" \\
                                          -e ${params.APP_ENV == 'prod' ? 'PROD_DEFAULT_PASSWORD' : 'TEST_DEFAULT_PASSWORD'}="${ACCOUNT_PASSWORD}" \\
                                          -e TEST_SUITE="${env.TEST_SUITE_VALUE}" \\
                                          -e ANDROID_SERIAL="${deviceSerial}" \\
                                          -e DEVICE_URI="Android:///${deviceSerial}" \\
                                          -e WECHAT_PACKAGE_NAME="${params.WECHAT_APP_PACKAGE}" \\
                                          -e TZ="Asia/Shanghai" \\
                                          -v ${env.HOST_WORKSPACE_PATH}:/workspace:rw \\
                                          -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \\
                                          -v "${env.HOST_ADB_KEYS_ANDROID_DIR}":/root/.android \\
                                          --privileged \\
                                          --network host \\
                                          --workdir /workspace \\
                                          -v /etc/localtime:/etc/localtime:ro \\
                                          ${env.DOCKER_IMAGE} \\
                                          pytest tests/wechat -v --alluredir=/results_out
                                        """
                                    }

                                    if (useTwoDevices) {
                                        def appTestsInParallel = [:]
                                        appTestsInParallel['Mobile测试 (主设备)'] = { runMobileTests(primaryDeviceSerial) }
                                        appTestsInParallel['WeChat测试 (次设备)'] = { runWechatTests(secondaryDeviceSerial) }
                                        echo "使用两台设备并行执行 Mobile 和 WeChat 测试..."
                                        parallel appTestsInParallel
                                    } else { 
                                        echo "使用一台设备 (${primaryDeviceSerial}) 串行执行 Mobile 和 WeChat 测试..."
                                        runMobileTests(primaryDeviceSerial)
                                        runWechatTests(primaryDeviceSerial) 
                                    }
                                } 
                            } else { 
                                echo "跳过App相关测试 (Mobile 和 WeChat)"
                                if (parallelWebAndApiTests.isEmpty()) { 
                                     sh "mkdir -p ${WORKSPACE}/output/allure-results" 
                                }
                            }
                        } 
                    } catch (err) {
                        echo "测试阶段出现错误: ${err}."
                        currentBuild.result = 'UNSTABLE' 
                    }
                } 
            } 
        } 
    } 

    post {
        always {
            echo "Pipeline 完成. 开始执行报告生成和通知步骤..."
            script {
                def allureReportUrl = ""
                def allureStepSuccess = false
                def tempReportGenSuccess = false

                try {
                    withCredentials([
                        string(credentialsId: env.EMAIL_PASSWORD_CREDENTIALS_ID, variable: 'INJECTED_EMAIL_PASSWORD'),
                        string(credentialsId: env.EMAIL_SMTP_SERVER_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_SMTP_SERVER'),
                        string(credentialsId: env.EMAIL_SMTP_PORT_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_SMTP_PORT'),
                        string(credentialsId: env.EMAIL_SENDER_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_SENDER'),
                        string(credentialsId: env.EMAIL_RECIPIENTS_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_RECIPIENTS'),
                        string(credentialsId: env.EMAIL_USE_SSL_CREDENTIAL_ID, variable: 'INJECTED_EMAIL_USE_SSL')
                    ]) {

                        echo "写入 Allure 元数据文件到 ${env.HOST_ALLURE_RESULTS_PATH} (在宿主机上)..."
                        def jenkinsAllureReportUrl = "${env.BUILD_URL}allure/"
                        sh """
                        docker run --rm --name write-metadata-${BUILD_NUMBER} \
                          -e APP_ENV=${params.APP_ENV} \
                          -e BUILD_NUMBER=${BUILD_NUMBER} \
                          -e BUILD_URL=${env.BUILD_URL} \
                          -e JOB_NAME=${env.JOB_NAME} \
                          -e ALLURE_PUBLIC_URL='${jenkinsAllureReportUrl}' \
                          -v ${env.HOST_WORKSPACE_PATH}:/workspace:ro \
                          -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_out:rw \
                          -v /etc/localtime:/etc/localtime:ro \
                          --user root \
                          ${env.DOCKER_IMAGE} \
                          python /workspace/ci/scripts/write_allure_metadata.py /results_out
                        """
                        echo "Allure 元数据写入完成。"

                        echo "修正宿主机目录 ${env.HOST_ALLURE_RESULTS_PATH} 的权限 (使用 Docker)..."
                        sh """
                        docker run --rm --name chown-chmod-results-${BUILD_NUMBER} \
                          -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_to_fix:rw \
                          --user root \
                          ${env.DOCKER_IMAGE} \
                          sh -c 'chown -R 1000:1000 /results_to_fix || echo "chown to 1000:1000 failed, continuing..."; chmod -R a+r /results_to_fix || echo "chmod failed!"'
                        """
                        echo "权限修正尝试完成。"

                        echo "使用 Allure Jenkins 插件处理 ${WORKSPACE}/output/allure-results 中的结果..."
                        try {
                            allure([
                                properties: [],
                                reportBuildPolicy: 'ALWAYS',
                                results: [
                                    [path: 'output/allure-results'] 
                                ]
                            ])
                            allureStepSuccess = true
                            allureReportUrl = jenkinsAllureReportUrl
                            echo "Allure 插件报告处理完成。报告 URL: ${allureReportUrl}"
                        } catch (allurePluginError) {
                            echo "Allure 插件步骤失败: ${allurePluginError}"
                            allureStepSuccess = false
                            allureReportUrl = "(Allure 插件报告生成失败)"
                        }

                        echo "生成临时报告到 ${env.HOST_ALLURE_REPORT_PATH} 以获取 summary.json..."
                        echo "确保宿主机目录 ${env.HOST_ALLURE_REPORT_PATH}/widgets 存在 (使用 Docker)..."
                        sh """
                        docker run --rm --name mkdir-temp-report-${BUILD_NUMBER} \
                          -v ${env.HOST_WORKSPACE_PATH}:/host_workspace:rw \
                          --user root \
                          ${env.DOCKER_IMAGE} \
                          sh -c 'mkdir -p /host_workspace/output/reports/temp-allure-report-for-summary/widgets && echo "Host directory ensured."'
                        """
                        sh """
                        docker run --rm --name allure-gen-temp-${BUILD_NUMBER} \
                          -v ${env.HOST_ALLURE_RESULTS_PATH}:/results_in:ro \
                          -v ${env.HOST_ALLURE_REPORT_PATH}:/report_out:rw \
                          --user root \
                          ${env.DOCKER_IMAGE} \
                          sh -c 'allure generate /results_in --clean -o /report_out && echo "Temporary report generated to /report_out" || echo "Failed to generate temporary report!"'
                        """
                        def summaryCheckExitCode = sh script: "docker run --rm -v ${env.HOST_ALLURE_REPORT_PATH}:/report_check:ro ${env.DOCKER_IMAGE} test -f /report_check/widgets/summary.json", returnStatus: true
                        if (summaryCheckExitCode == 0) {
                            tempReportGenSuccess = true
                            echo "summary.json 已成功生成到宿主机路径: ${env.HOST_ALLURE_REPORT_PATH}/widgets/summary.json"
                        } else {
                            tempReportGenSuccess = false
                            echo "[警告] 未能在 ${env.HOST_ALLURE_REPORT_PATH}/widgets/ 中找到 summary.json。邮件可能缺少统计信息。"
                        }

                        if (params.SEND_EMAIL) {
                            echo "发送邮件通知 (尝试读取 ${env.HOST_ALLURE_REPORT_PATH}/widgets/summary.json)..."
                            sh """
                            echo "--- Sending notification email via run_and_notify.py ---"
                            docker run --rm --name notify-${BUILD_NUMBER} \
                              -e CI=true \
                              -e APP_ENV=${params.APP_ENV} \
                              -e EMAIL_ENABLED=${params.SEND_EMAIL} \
                              -e EMAIL_PASSWORD='${INJECTED_EMAIL_PASSWORD}' \
                              -e EMAIL_SMTP_SERVER="${INJECTED_EMAIL_SMTP_SERVER}" \
                              -e EMAIL_SMTP_PORT=${INJECTED_EMAIL_SMTP_PORT} \
                              -e EMAIL_SENDER="${INJECTED_EMAIL_SENDER}" \
                              -e EMAIL_RECIPIENTS="${INJECTED_EMAIL_RECIPIENTS}" \
                              -e EMAIL_USE_SSL=${INJECTED_EMAIL_USE_SSL} \
                              -e ALLURE_PUBLIC_URL="${allureReportUrl}" \
                              -e BUILD_STATUS="${currentBuild.result ?: 'SUCCESS'}" \
                              -e BUILD_URL="${env.BUILD_URL}" \
                              -e JOB_NAME="${env.JOB_NAME}" \
                              -e BUILD_NUMBER="${BUILD_NUMBER}" \
                              -e TZ="Asia/Shanghai" \
                              -v ${env.HOST_WORKSPACE_PATH}:/workspace:ro \
                              -v ${env.HOST_ALLURE_REPORT_PATH}:/report:ro \
                              -v /etc/localtime:/etc/localtime:ro \
                              --network host \
                              ${env.DOCKER_IMAGE} \
                              python /workspace/ci/scripts/run_and_notify.py
                            echo "通知脚本执行完毕。"
                            """
                        } else {
                            echo "邮件通知已禁用 (SEND_EMAIL=false)。"
                        }
                    } 
                } catch (err) {
                    echo "Post-build 阶段出现严重错误: ${err}"
                    if (!allureStepSuccess && !tempReportGenSuccess) {
                        currentBuild.result = 'FAILURE'
                    } else {
                        if (currentBuild.result == null || currentBuild.result == 'SUCCESS') {
                           currentBuild.result = 'UNSTABLE'
                        }
                    }
                } finally {
                    def testTypes = []
                    if (params.RUN_WEB_TESTS) testTypes.add("Web")
                    if (params.RUN_API_TESTS) testTypes.add("API")
                    if (params.RUN_APP_RELATED_TESTS) {
                        def primaryDesc = params.PRIMARY_APP_DEVICE_SERIAL.trim()
                        def secondaryDesc = params.SECONDARY_APP_DEVICE_SERIAL.trim()
                        if (primaryDesc && !primaryDesc.isEmpty()) { 
                            if (secondaryDesc && !secondaryDesc.isEmpty() && secondaryDesc != primaryDesc) {
                                testTypes.add("App (Mobile on ${primaryDesc}, WeChat on ${secondaryDesc})")
                            } else {
                                testTypes.add("App (Mobile & WeChat on ${primaryDesc})")
                            }
                        } else {
                            testTypes.add("App (未指定设备)")
                        }
                    }
                    if (testTypes.isEmpty()) testTypes.add("未选择")

                    def finalStatus = currentBuild.result ?: 'SUCCESS'
                    def reportLink = allureStepSuccess && allureReportUrl != null && allureReportUrl.startsWith("http") ? "<a href='${allureReportUrl}' target='_blank'>查看报告</a>" : allureReportUrl ?: "(报告链接不可用)"

                    currentBuild.description = "${params.APP_ENV.toUpperCase()} 环境 [${testTypes.join(', ')}] - ${finalStatus} - ${reportLink}"

                    echo "清理 Agent 工作空间 ${WORKSPACE} 和临时报告目录 ${env.HOST_ALLURE_REPORT_PATH} (在宿主机上)..."
                    sh """
                    docker run --rm --name cleanup-temp-report-${BUILD_NUMBER} \
                      -v ${env.HOST_WORKSPACE_PATH}:/host_workspace:rw \
                      --user root \
                      ${env.DOCKER_IMAGE} \
                      sh -c 'rm -rf /host_workspace/output/reports/temp-allure-report-for-summary && echo "Host temporary report directory removed."'
                    """
                    cleanWs()
                    echo "Agent 工作空间和临时报告目录已清理。"
                }
            }
        }
        success {
            echo "Pipeline 最终状态: 成功"
        }
        failure {
            echo "Pipeline 最终状态: 失败"
        }
        unstable {
            echo "Pipeline 最终状态: 不稳定"
        }
    }
}