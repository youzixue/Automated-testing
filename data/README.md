# data 测试数据层说明

本目录用于存放所有自动化测试所需的参数化数据文件，支持 YAML/JSON/CSV 等格式。

## 主要内容
- API测试数据：`data/api/payment_data.yaml`
- Web端测试数据：
    - 登录数据：`data/web/login/login_data.yaml`
- 移动端测试数据 (按平台划分):
    - Android: `data/mobile/android/` (目前为空)
    - iOS: `data/mobile/ios/` (目前为空)
- 微信测试数据 (按类型划分):
    - 小程序: `data/wechat/miniprogram/` (目前为空)
    - 公众号: `data/wechat/official/` (目前为空)

## 设计原则
- 测试数据与测试逻辑分离，便于维护和复用（见 test-data-separation.mdc）
- 数据文件需有详细注释，字段含义清晰
- 新增/调整数据结构时，务必补充本 README

## 参考
- .cursor/rules/test-data-separation.mdc
