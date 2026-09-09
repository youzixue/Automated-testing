# API 测试平台实现层说明

本目录属于七层架构中的 **平台实现层 (Platform)**，负责封装与 API 交互的具体实现逻辑。

## 主要内容
- `services/`: 存放具体的 API 服务对象，每个服务对象封装对特定 API 端点的操作（如请求发送、响应解析）。
- `models/`: (可选) 定义用于 API 请求体或响应体的数据模型。
- `__init__.py`: 包初始化文件。

## 设计原则
- **服务封装**: 使用 `httpx` 库发送 HTTP 请求。
- **模型定义**: 使用 Pydantic 或 dataclasses 定义清晰的数据模型，便于数据验证和序列化。
- **异常处理**: 抛出特定的 API 相关异常，例如 `ApiRequestError`, `ApiResponseError`。
- **日志记录**: 使用标准日志记录器记录关键请求和响应信息。
- **职责划分**: 测试通过 fixture 获取 `services/` 中的服务对象，由服务对象组织请求和响应处理；保持职责清晰，避免循环依赖。

## 参考

项目协作约定见 [AGENTS.md](../../AGENTS.md)。

开发流程见 [API 测试指南](../../.agents/skills/add-automated-test/references/api.md)。
