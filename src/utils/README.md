# src/utils 工具层说明

本目录为自动化测试框架的通用工具层，主要包含以下内容：

- **日志工具**（log/）：统一日志管理，支持多级别日志、控制台与文件输出、全局聚合日志。
- **OCR工具**（ocr/、ocr.py）：验证码识别与预处理，集成 ddddocr + Pillow，支持多种验证码场景。
- **配置管理工具**（config/）：统一加载、解析、校验YAML/JSON等配置文件，支持多环境配置、环境变量覆盖、配置校验等。
- **截图工具**（screenshot.py）：统一截图保存、目录管理，支持原始与报告归档目录，详见下方用法示例。
- **数据生成器**（data_generator.py）：生成随机用户名、邮箱、密码、用户信息等，支持批量生成测试数据。
- **文件操作工具**（file_utils.py）：支持文本文件的读写、追加、删除、遍历等常用操作。
- **邮件通知工具**（email_notifier.py）：支持SMTP邮件发送，支持文本和HTML格式，带详细日志和异常处理。
- **时间工具**（time_utils.py）：时间格式化、解析、时间差计算、智能sleep等。
- **正则表达式工具**（patterns.py）：常用正则模式集中管理，统一接口，便于复用和维护。
- **事件总线**（event.py）：支持事件订阅、发布、取消订阅，便于模块间解耦。
- **错误处理与重试机制**（error_handling.py）：统一异常捕获、日志记录、重试装饰器等。

## 目录结构说明

- `log/`：日志管理子模块，详见`log/README.md`。
- `ocr/`：OCR相关子模块，详见`ocr/README.md`。
- `config/`：配置管理子模块，详见`config/README.md`。
- 其它py文件：为通用工具类，适用于全局或多业务场景。

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
await save_screenshot(driver, file_name, report=False)  # 保存到原始截图目录
await save_screenshot(driver, file_name, report=True)   # 保存到报告归档目录
```

### log/
- `manager.py`：统一日志器获取、日志级别设置、文件与控制台输出、全局聚合日志等。

### ocr/ 与 ocr.py
- `ocr.py`：通用OCR工具，集成ddddocr，支持图片验证码识别。
- `ocr/captcha.py`：专用验证码识别策略，支持多种验证码类型扩展。

### config/
- `manager.py`：统一加载、合并、校验多环境配置，支持环境变量覆盖。
- `validators.py`：配置项校验、类型检查等。
- `README.md`：详细说明配置模块的扩展和使用方法。

### data_generator.py
- `random_user()`：生成随机用户信息字典。
- `random_users(count: int)`：批量生成随机用户。

### file_utils.py
- `read_text(path: str)`：读取文本文件内容。
- `write_text(path: str, content: str)`：写入文本内容到文件。

### email_notifier.py
- `send_email(subject, body, recipients)`：发送邮件，支持文本和HTML。

### allure_report_tools.py
- **用途**：
  提供Allure报告产物的自动校验与补传工具函数，确保Allure静态报告在分布式/静态服务器环境下用例详情不404。适用于CI/CD流程和本地上传前的自动检查。

- **主要函数**：
  - `get_uid_files(data_dir: str) -> Set[str]`  
    获取data目录下所有UID .json文件名（不含扩展名）。
  - `get_allure_test_uids(report_dir: str) -> Set[str]`  
    从suites.json中递归提取所有用例的UID。
  - `upload_files(files: List[str], data_dir: str, remote_user: str, remote_host: str, remote_dir: str) -> List[str]`  
    上传指定UID .json文件到服务器，返回失败文件列表。
  - `upload_key_files(data_dir: str, remote_user: str, remote_host: str, remote_dir: str) -> List[str]`  
    上传history.json、categories.json、summary.json等关键文件，返回失败文件列表。

- **用法示例**：

  ```python
  from src.utils.allure_report_tools import (
      get_uid_files, get_allure_test_uids, upload_files, upload_key_files
  )

  data_dir = "output/reports/allure-report/data"
  report_dir = "output/reports/allure-report"
  remote_user = "root"
  remote_host = "1.2.3.4"
  remote_dir = "/usr/share/nginx/html/allure-report/data/"

  uids_in_data = get_uid_files(data_dir)
  uids_in_suites = get_allure_test_uids(report_dir)
  missing = uids_in_suites - uids_in_data

  if missing:
      failed = upload_files(list(missing), data_dir, remote_user, remote_host, remote_dir)
      if failed:
          print("部分UID .json文件补传失败：", failed)
  upload_key_files(data_dir, remote_user, remote_host, remote_dir)
  ```

- **注意事项**：
  - 需保证本地和服务器均已安装`scp`命令。
  - 适用于Allure报告已生成后、上传到静态服务器前的校验和补传。
  - 建议集成到CI/CD流程，自动保障报告完整性。

---

如需扩展更多工具函数，请在本目录下新建对应模块，并补全README说明。  