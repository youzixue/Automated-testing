# Web 测试开发

以下路径相对仓库根目录。

## 当前实现入口

- `tests/web/omp/test_login.py`：异步登录及异常场景。
- `tests/web/conftest.py`：异步 `browser`、`page` fixture、`test_users` 数据合成及失败截图钩子。
- `src/web/pages/omp/login_page.py`：当前 OMP 登录页面对象。
- `data/web/login/login_data.yaml`：登录场景及验证码配置。
- 详细背景：[Web 开发指南](../../../../docs/Web自动化测试开发指南.md)。

## 实施要点

- 跟随实际 import 选择页面对象；仓库中存在多个登录相关文件，不因名字相似就合并或替换。
- 保持异步调用和 fixture 生命周期一致，避免混入同步 Playwright 操作或独立创建未释放的浏览器。
- 选择器来自页面证据或已有实现；封装交互，使用定位器等待和可观察状态断言。
- 登录结果按场景校验错误提示或页面状态；OCR 识别失败和账号密码错误是不同原因，不互相替代。
- 正常登录凭据由配置注入；虚构的无效输入可继续留在场景 YAML 中。
- 检查现有截图钩子后再增加取证逻辑，避免重复附件；共享账号状态未隔离时不直接增加并行。

## 验证入口

```bash
poetry run pytest tests/web --env=test --alluredir=output/allure-results
```

需要浏览器及目标系统。优先运行指定场景，确认断言描述与实际页面证据一致。
