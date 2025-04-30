# src/utils 工具层说明

本目录为自动化测试框架的通用工具层（七层架构中的 **Utils** 层），包含与具体业务无关、可在框架内复用的各类辅助工具。

## 主要内容
- **日志工具** (`log/`): 统一日志管理，详见 `log/README.md`。
- **配置管理** (`config/`): 加载、解析、校验配置文件，详见 `config/README.md`。
- **OCR 工具** (`ocr/`, `ocr.py`): 验证码识别与预处理，详见 `ocr/README.md`。
- **截图工具** (`screenshot.py`): 统一截图保存与管理。
- **数据生成器** (`data_generator.py`): 生成各类随机测试数据。
- **文件操作** (`file_utils.py`): 封装常用的文件读写、路径操作。
- **时间处理** (`time.py`): 时间格式化、解析、等待等相关工具。
- **邮件通知** (`email_notifier.py`): 发送邮件通知。
- **事件总线** (`event.py`): 实现简单的事件发布/订阅机制。
- **正则表达式** (`patterns.py`): 集中管理常用正则表达式。
- **签名工具** (`signature.py`): 实现支付兼容的 MD5 签名算法。
- **初始化** (`__init__.py`): 导出工具类或函数。

## 目录结构说明
- `log/`: 日志管理子模块。包含 `manager.py`。
- `ocr/`: OCR 相关子模块。包含 `captcha.py`。
- `config/`: 配置管理子模块。包含 `manager.py`, `loaders.py`。
- 其它 `.py` 文件: 为独立的通用工具模块。

## 设计原则
- 工具层只放通用、可复用、无业务依赖的代码。
- 所有工具函数/类应有完善的类型注解和Google风格docstring。
- 关键分支和异常需加标准化日志，便于排查和维护。
- 推荐按功能拆分多个工具模块，便于团队协作和长期维护。
- 截图、日志、配置等目录均支持通过环境变量和配置文件灵活切换。

## 主要模块示例

### screenshot.py
- `save_screenshot(driver, file_name, report=False)`：调用driver的截图方法并保存到指定目录，支持原始和报告归档目录。
- `gen_screenshot_filename(test_name, ext="png")`：生成带时间戳的截图文件名。
- `get_screenshot_dir(report=False)`：获取截图存放目录，支持配置和环境变量切换。

**用法示例：**
```python
from src.utils.screenshot import save_screenshot, gen_screenshot_filename
file_name = gen_screenshot_filename("test_login_fail")
await save_screenshot(driver, file_name, report=False)
await save_screenshot(driver, file_name, report=True)
```

### log/
- `manager.py`：统一日志器获取、日志级别设置、文件与控制台输出、全局聚合日志等。

### ocr/ 与 ocr.py
- `ocr.py`：通用 OCR 工具，集成 ddddocr，支持图片验证码识别。
- `ocr/captcha.py`：专用验证码识别策略，支持多种验证码类型扩展。

### config/
- `manager.py`：统一加载、合并、校验多环境配置，支持环境变量覆盖。
- `loaders.py`：包含不同格式配置文件的加载器实现。

### data_generator.py
- `random_user()`：生成随机用户信息字典。
- `random_users(count: int)`：批量生成随机用户。

### file_utils.py
- `read_text(path: str)`：读取文本文件内容。
- `write_text(path: str, content: str)`：写入文本内容到文件。

### email_notifier.py
- `send_email(subject, body, recipients)`：发送邮件，支持文本和HTML。

### event.py
- 支持事件订阅、发布、取消订阅，便于模块间解耦。

### patterns.py
- 常用正则模式集中管理，统一接口，便于复用和维护。

### signature.py
- `calculate_md5_sign(params, secret_key)`: 根据支付规则计算参数字典的 MD5 签名。

---

如需扩展更多工具函数，请在本目录下新建对应模块，并补全README说明。  