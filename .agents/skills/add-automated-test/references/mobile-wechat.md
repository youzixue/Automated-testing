# App 与微信端测试开发

以下路径相对仓库根目录。

## 按入口定位

| 平台 | 用例与入口 |
|---|---|
| App | `tests/mobile/test_jiyu_monthly_card.py`、`src/mobile/screens/jiyu_entry_screen.py` |
| 微信小程序 | `tests/wechat/test_mini_program_monthly_card.py`、`src/wechat/utils/navigation.py` |
| 微信公众号 | `tests/wechat/test_official_account_monthly_card.py`、`src/wechat/screens/official_account_entry.py` |

设备 fixture 位于 `tests/mobile/conftest.py` 和 `tests/wechat/conftest.py`，共同依赖根级 `tests/conftest.py` 的辅助逻辑。
共享流程位于 `src/common/components/monthly_card_flow.py`；图像素材位于 `data/common/images/` 和 `data/wechat/images/`。
详细背景：[微信与 App 开发指南](../../../../docs/微信&APP自动化测试开发指南.md)。

## 实施要点

- 确认设备 URI、平台、应用包名、微信目标和登录状态，再定位入口差异。
- 优先复用 `MonthlyCardWebViewFlow`；App、公众号和小程序的导航、提交支付步骤分别对照各自用例，不强制统一。
- 微信内 H5/WebView 当前通过 Airtest/Poco 和图像交互，不因为名称含 H5 就迁移到桌面 Playwright。
- 有稳定控件证据时使用 Poco；图像定位需核对模板、分辨率和当前页面，不能凭空编造截图或控件属性。
- 采用 Poco 状态等待或 Airtest 图像等待；记录具体等待目标和超时，避免用扩大固定延时掩盖错误页面。
- 同一设备串行执行，沿用 fixture 的设备/Poco 生命周期和现有失败截图附件机制。
- 当前月卡代表性链路断言支付 Activity 拉起；只有另有回调、订单状态等证据时才能新增支付成功结论。
- Android 上的 Activity 断言不代表 iOS 已验证；新增平台支持需使用对应的可观察结果。

## 验证入口

```bash
poetry run pytest tests/mobile --env=test -n 1 --alluredir=output/allure-results
poetry run pytest tests/wechat --env=test -n 1 --alluredir=output/allure-results
```

两条命令依次执行，并优先选择实际变更的文件。修改共享组件时，评估 App、小程序、公众号三个调用端；只验证了部分入口需明确其余未验证范围。
