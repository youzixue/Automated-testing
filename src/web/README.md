# src/web Web平台实现层说明

本目录为Web自动化测试平台实现层，负责Web端自动化相关的所有平台适配、页面对象、工具类等实现。

## 目录结构
- `pages/`：页面对象层，封装所有Web端业务页面对象（Page Object），详见`pages/README.md`
- `utils/`：Web专用工具层，包含表单校验、条件处理、驱动适配、智能等待等通用工具
- 其它py文件：平台适配器、全局配置、特殊业务实现等

## 设计原则
- 严格遵循七层架构分层思想，禁止跨层依赖
- 页面对象、工具类、适配器等均需加类型注解和Google风格docstring
- 关键业务流程和异常分支必须加标准化日志，日志器命名为类名或模块名
- 所有异常需精确捕获并记录日志，禁止捕获通用Exception后无日志输出
- 目录结构和命名需与项目规范一致，便于团队协作和长期维护

## 扩展建议
- 新增页面对象请放在`pages/`目录，并补充`pages/README.md`
- 新增Web工具请放在`utils/`目录，并补充`utils/README.md`
- 平台适配器、全局配置等建议单独成文件并加详细注释

## 参考
- .cursor/rules/seven-layer-architecture.mdc
- .cursor/rules/page-object-pattern.mdc
- .cursor/rules/code-consistency.mdc
- .cursor/rules/type-annotations.mdc
- .cursor/rules/logging-standards.mdc
- .cursor/rules/specific-exceptions.mdc 