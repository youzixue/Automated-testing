# src/web/pages 页面对象层说明

本目录用于封装Web端所有页面对象（Page Object），实现UI元素定位、页面操作和业务流程。

## 主要内容
- 每个页面/业务流程一个Page类，命名规范如 LoginPage、DashboardPage
- 页面对象封装定位符和重复交互；用例组织场景并断言业务结果。
- 优先通过现有页面对象复用交互；必要的场景验证可使用 fixture 提供的页面对象，不为单次操作强行增加封装。

## 设计原则
- 严格遵循页面对象模式
- 命名、注释、类型注解需与项目规范一致
- 新增页面对象时，务必补充本 README

## 参考

项目协作约定见 [AGENTS.md](../../../AGENTS.md)。

开发流程见 [Web 测试指南](../../../.agents/skills/add-automated-test/references/web.md)。
