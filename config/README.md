# config 配置层说明

本目录用于存放所有环境相关的配置文件，支持多环境（dev/test/prod）切换和外部化配置。配置系统采用分层设计，允许环境特定配置覆盖基础配置。

## 目录结构
```
config/
├── settings.yaml     # 基础配置文件（所有环境通用的默认配置）
├── env/              # 环境特定配置目录
│   ├── test.yaml     # 测试环境特定配置
│   └── prod.yaml     # 生产环境特定配置
└── .env              # 本地开发环境变量（不提交到版本库）
```

## 配置文件说明

### 基础配置（settings.yaml）
包含所有环境共享的默认配置项：
- Web测试配置：浏览器设置、超时时间、截图配置等
- API测试配置：请求超时、重试策略等
- 通知配置：邮件通知、报告生成等
- 日志配置：日志级别、格式、存储位置等
- 移动测试配置：设备URI、APP包名等
- 微信测试配置：小程序和公众号相关设置

### 环境特定配置（env/*.yaml）
为特定环境（测试/生产）提供的专用配置，可覆盖基础配置中的值：
- 环境特定的URL和端点
- 环境专用的超时和重试策略
- 环境相关的凭据和密钥（通过环境变量引用）
- 环境特定的日志级别和通知模板

## 配置加载机制
1. 首先加载 `settings.yaml` 中的基础配置
2. 根据当前环境加载对应的环境配置文件（如 `env/test.yaml`）
3. 环境配置会覆盖基础配置中的同名项
4. 环境变量引用（`${env:VARIABLE_NAME}`）会在运行时解析

## 环境变量使用
配置系统支持从环境变量中读取值，推荐用法：
- 敏感信息（密码、API密钥）应通过环境变量传入
- 使用 `${env:VARIABLE_NAME}` 语法引用环境变量
- 可设置默认值：`${env:VARIABLE_NAME:-default_value}`

示例：
```yaml
api:
  timeout: ${env:API_TIMEOUT:-30}  # 如未设置环境变量，使用默认值30
  base_url: "${env:API_BASE_URL}"  # 必须从环境变量获取，无默认值
```

## 设计原则
- 所有可变配置均应外部化，不允许硬编码（见 external-configuration.mdc）
- 配置项需有详细注释，便于理解和维护
- 新增/调整配置项时，务必同步更新本 README
- 敏感信息不应直接存储在配置文件中，应通过环境变量注入
- 配置项应分门别类，结构清晰，便于维护和扩展
- 尽量提供默认值，减少配置错误导致的问题

## 本地开发配置
开发者可在本地创建 `.env` 文件（已在 .gitignore 中排除）用于存储本地开发所需的环境变量：
```
# 本地开发环境变量示例
WEB_BASE_URL=http://localhost:8080
API_BASE_URL=http://localhost:8000/api
DEFAULT_TIMEOUT=60
TEST_ADMIN_USERNAME=admin
TEST_ADMIN_PASSWORD=admin123
```

## 参考
- `.cursor/rules/external-configuration.mdc`
