# data 测试数据层说明

本目录用于存放所有自动化测试所需的参数化数据文件，支持 YAML/JSON/CSV 等格式。

## 主要内容
- Web端登录数据：data/web/login/login_data.yaml
- 其他业务测试数据按业务/平台分目录存放

## 设计原则
- 测试数据与测试逻辑分离，便于维护和复用（见 test-data-separation.mdc）
- 数据文件需有详细注释，字段含义清晰
- 新增/调整数据结构时，务必补充本 README

## 参考
- .cursor/rules/test-data-separation.mdc
