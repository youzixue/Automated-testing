# src/web/pages 页面对象层说明

本目录用于封装Web端所有页面对象（Page Object），实现UI元素定位、页面操作和业务流程。

## 主要内容
- 每个页面/业务流程一个Page类，命名规范如 LoginPage、DashboardPage
- 元素定位符、操作方法、断言逻辑均应封装在Page类中
- 测试用例只通过Page对象与UI交互，禁止直接操作底层driver

## 设计原则
- 严格遵循页面对象模式（见 page-object-pattern.mdc）
- 命名、注释、类型注解需与项目规范一致（见 code-consistency.mdc）
- 新增页面对象时，务必补充本 README

## 参考
- .cursor/rules/page-object-pattern.mdc
- .cursor/rules/code-consistency.mdc
