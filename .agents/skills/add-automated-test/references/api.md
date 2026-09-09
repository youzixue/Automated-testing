# API 测试开发

以下路径相对仓库根目录。

## 当前实现入口

- `tests/api/test_payment_unified_order.py`：正常下单、缺字段、格式、长度和签名等场景。
- `tests/api/conftest.py`：模块级 YAML 数据加载、参数化 IDs、`payment_api_data` 和 `payment_service` fixture。
- `src/api/services/payment_service.py`：请求准备、签名、httpx 调用及响应解析。
- `src/api/models/payment_models.py`：请求相关数据和响应模型。
- `data/api/payment_data.yaml`：基础参数及场景数据。
- 详细背景：[API 开发指南](../../../../docs/API自动化测试开发指南.md)。

## 实施要点

- 先追踪配置值与用例参数的合成顺序；显式异常参数可覆盖默认值，不要无意中改变这种能力。
- 区分客户端 Pydantic 校验失败、HTTP 错误、响应结构错误和接口业务拒绝；测试应验证它实际经过的层次。
- 正常场景校验业务状态和关键字段；异常场景校验对应错误，不能仅以“存在响应”判断通过。
- 签名错误场景需确认 monkeypatch 命中了实际调用位置，并且请求到达预期验证环节。
- YAML 锚点及 session 数据可能共享对象；需要修改输入时在用例边界建立适当副本。
- 订单重复测试与正常订单的唯一性要求不同，按场景生成或复用订单号，不统一替换成随机值。
- 保持客户端由现有 fixture 关闭；请求日志和报告不要暴露运行环境凭据。

## 验证入口

```bash
poetry run pytest tests/api --env=test --alluredir=output/allure-results
```

优先缩小到新增文件或 node ID。下单会改变目标系统状态，复跑范围和次数应与任务匹配；仅在数据隔离后考虑并行。
