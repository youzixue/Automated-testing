# API 测试平台实现层说明

本目录属于七层架构中的 **平台实现层 (Platform)**，负责封装与 API 交互的具体实现逻辑。

## 主要内容
- `services/`: 存放具体的 API 服务对象，每个服务对象封装对特定 API 端点的操作（如请求发送、响应解析）。
- `models/`: (可选) 定义用于 API 请求体或响应体的数据模型。
- `__init__.py`: 包初始化文件。

## 设计原则
- **服务封装**: 使用 `httpx` 库发送 HTTP 请求 (`platform-specific-testing.mdc`)。
- **模型定义**: 使用 Pydantic 或 dataclasses 定义清晰的数据模型，便于数据验证和序列化。
- **异常处理**: 抛出特定的 API 相关异常 (`specific-exceptions.mdc`)，例如 `ApiRequestError`, `ApiResponseError`。
- **日志记录**: 使用标准日志记录器记录关键请求和响应信息 (`logging-standards.mdc`)。
- **架构遵循**: 严格遵循七层架构规范 (`seven-layer-architecture.mdc`)，不直接被测试用例层调用，而是通过业务对象层 (`src/business/api/`) 间接调用。

## 参考
- `.cursor/rules/platform-specific-testing.mdc`
- `.cursor/rules/seven-layer-architecture.mdc`
- `.cursor/rules/specific-exceptions.mdc`
- `.cursor/rules/logging-standards.mdc` 