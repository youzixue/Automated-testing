# CI/CD 脚本目录说明

本目录下为自动化测试平台的CI/CD流程专用脚本，已按单一职责原则进行模块化拆分，便于维护和扩展。

## 目录结构

```
ci/scripts/
├── env_setup.py         # 环境准备：加载.env、补全关键环境变量
├── run_tests.py         # 测试执行：并发运行pytest，自动重试
├── generate_report.py   # 报告生成与上传：Allure报告生成、环境信息写入、上传与权限修正
├── notify.py            # 邮件通知：组装并发送HTML测试报告邮件
├── utils.py             # 通用工具：历史数据复制、报告统计、完整性检查等
├── run_and_notify.py    # 主控入口：调度各子模块，CI流程唯一入口
└── README.md            # 本说明文档
```

## 各模块职责

- **env_setup.py**
  - 仅负责环境变量准备和本地.env加载。
  - 提供 `prepare_env()` 统一入口。

- **run_tests.py**
  - 仅负责pytest测试执行，支持并发与失败重试。
  - 提供 `run_tests()` 统一入口。

- **generate_report.py**
  - 负责Allure报告生成、环境/分类/执行器信息写入、.nojekyll创建、远端上传与权限修正。
  - 提供 `generate_allure_report()`、`upload_report_to_ecs()` 等函数。

- **notify.py**
  - 负责组装HTML邮件内容并发送测试报告。
  - 提供 `send_report_email(summary, upload_success)` 统一入口。

- **utils.py**
  - 提供CI流程通用工具函数，如历史数据复制、报告统计、完整性检查等。

- **run_and_notify.py**
  - CI流程唯一主控入口，按顺序调度各子模块。
  - 推荐CI/CD流水线仅调用本脚本。

## 使用方法

1. **本地调试/开发**
   - 可直接运行 `python run_and_notify.py`，自动完成环境准备、测试、报告、通知全流程。
   - 支持本地.env自动加载。

2. **CI/CD集成**
   - 在CI流程（如GitHub Actions、Jenkins等）中仅需调用 `python ci/scripts/run_and_notify.py`。
   - 其余脚本均为子模块，不建议单独调用。

## 设计原则与最佳实践

- 严格遵循单一职责、解耦与可维护性优先。
- 配置与敏感信息全部外部化，禁止硬编码。
- 所有异常均有日志输出，便于问题定位。
- 便于团队协作和后续扩展。

---
如需扩展新功能，请优先在本目录下新建独立模块，保持主控入口简洁明了。
