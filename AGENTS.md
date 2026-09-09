# Agent 协作指南

## 项目背景

这是 Python + pytest 多端自动化测试框架，覆盖 Web、API、App、微信小程序及公众号代表性链路。
项目来自曾实际运行的业务测试实现；开源测试数据为作者编造的示例。
历史运行经历不代表当前机器、目标系统或所有平台已验证。报告本次实际执行结果。

## 代码与文档入口

- `tests/`：测试用例；根级和各平台 `conftest.py` 管理 fixture、配置及报告钩子。
- `src/api/services/`、`src/api/models/`：httpx 服务对象和 Pydantic 模型。
- `src/web/pages/`：页面对象；Web 用例使用 Playwright 异步接口。
- `src/mobile/screens/`、`src/wechat/`：App 屏幕对象、微信导航及入口。
- `src/common/components/monthly_card_flow.py`：App 和微信端共享月卡流程。
- `src/core/base/`、`src/utils/`：抽象接口、配置、日志、等待和其他工具。
- `data/`：场景数据和图像模板；`config/`：基础及环境配置。
- `ci/`、`Jenkinsfile`、`Dockerfile`：现有运行、报告和集成入口。

先阅读 [README](README.md) 中与任务有关的部分，再核对相关实现。
架构背景见 [架构文档](docs/enhanced_architecture.md)；平台细节按需阅读 `docs/` 中对应指南。
文档与代码不一致时，先确认实际调用和运行证据，不把历史文档直接当作重构要求。

## 环境与运行

以下命令在项目根目录执行，是现有入口，不代表当前环境已通过验证。
当前 `pyproject.toml` 的 Python 范围为 `>=3.11,<3.12`，主要依赖通过 Poetry 管理。

```bash
poetry install
poetry run playwright install chromium
poetry run pytest tests/api --env=test --alluredir=output/allure-results
poetry run pytest tests/web --env=test --alluredir=output/allure-results
poetry run pytest tests/mobile --env=test -n 1 --alluredir=output/allure-results
poetry run pytest tests/wechat --env=test -n 1 --alluredir=output/allure-results
```

Airtest/Poco 当前还有额外安装步骤，参见 README 的环境准备；不要假定 `poetry install` 包含设备端全部依赖。
根据 `.env.example` 准备运行配置。检查启动方式、环境选择、变量注入和实际读取位置，不输出凭据值。
Web/API 需要可访问的目标系统；设备端还需要设备连接、应用、账号和匹配的图像模板。
同一设备上的 App、小程序和公众号测试串行执行，也不要并发启动多个任务争用该设备。
优先运行相关文件或 node ID；直接选择平台目录可避免收集无关设备模块。
是否并行运行 Web/API 取决于账号、订单和测试数据是否隔离。

## 修改约定

- 优先复用现有页面、服务、屏幕对象及共享组件，保持平台职责清晰，避免循环依赖。
- 不机械要求逐层调用；仅在任务需要时新增抽象，不顺带重写架构或升级依赖。
- 保留虚构示例和必要教学说明；实际凭据通过环境配置提供，不提交 `.env`。
- 测试数据与逻辑按现有方式组织；普通断言常量不必全部改成环境变量。
- 优先使用 Playwright、Poco 或 Airtest 的条件等待；需要轮询时设置明确退出条件和超时。
- 由 fixture 或上下文管理器管理浏览器、客户端和设备资源；确认引用后再清理旧实现。
- 使用现有日志和异常机制，保留原始失败原因，避免新增完整凭据、签名或敏感请求输出。
- 公共接口补充必要类型和说明，遵循 `pyproject.toml` 的现有工具配置。
- 配置或实现疑点先结合调用路径验证；不要为了让测试通过而放宽断言、吞异常或随意增加跳过。

## 任务 Skills

- 新增或修改测试：使用 [多端测试开发](.agents/skills/add-automated-test/SKILL.md)，按平台读取参考指南。
- 诊断失败：使用 [测试排错](.agents/skills/debug-test-failure/SKILL.md)。
- 普通文档维护不需要加载测试开发流程。

## 验证与交付

执行与改动相关的检查。纯文档改动检查链接、路径和内容一致性即可。
运行测试前确认目标与任务范围一致；下单等会改变目标系统状态的步骤不要当作无副作用检查。
缺少设备、凭据或目标服务时，说明缺失条件和未执行范围，不把收集成功或跳过计为测试通过。
交付说明修改内容、实际执行命令、结果及未验证部分；不将拉起支付页面表述为支付成功闭环。
