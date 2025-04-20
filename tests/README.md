# tests 测试用例层说明

本目录用于组织所有自动化测试用例，按平台和业务分目录，支持参数化、分层和多环境执行。

## 目录结构
- `tests/web/`：Web UI自动化测试用例
- `tests/api/`：API自动化测试用例
- `tests/mobile/`：移动端自动化测试用例
- `tests/unit/`：单元测试
- `tests/integration/`：集成测试
- `conftest.py`：全局pytest fixture与数据工厂

## 设计原则
- 测试用例与测试数据分离，数据统一存放于 `data/` 目录
- 用例应参数化，支持多账号、多场景、多浏览器测试
- 命名、注释、分层结构需与项目规范一致
- 推荐使用Allure/HTML报告，便于结果追踪

## 多浏览器测试操作方法
本项目已支持多浏览器自动化测试（chromium/firefox/webkit），无需修改业务代码。

### 1. 通过环境变量切换浏览器类型
在运行pytest前设置 `BROWSER` 环境变量即可：

#### Windows PowerShell
```powershell
$env:BROWSER="chromium"; pytest
$env:BROWSER="firefox"; pytest
$env:BROWSER="webkit"; pytest
```

#### Windows CMD
```cmd
set BROWSER=chromium && pytest
set BROWSER=firefox && pytest
set BROWSER=webkit && pytest
```

#### Linux/Mac Bash
```bash
BROWSER=chromium pytest
BROWSER=firefox pytest
BROWSER=webkit pytest
```

### 2. 一次性批量执行三种浏览器
可编写批处理脚本批量执行：

#### PowerShell 脚本
```powershell
$env:BROWSER="chromium"; pytest
$env:BROWSER="firefox"; pytest
$env:BROWSER="webkit"; pytest
```

#### CMD 批处理
```bat
set BROWSER=chromium && pytest
set BROWSER=firefox && pytest
set BROWSER=webkit && pytest
```

#### Bash 脚本
```bash
for b in chromium firefox webkit; do
  BROWSER=$b pytest
done
```

### 3. 结果区分建议
建议在测试日志或Allure报告中打印当前浏览器类型（如 `os.environ.get("BROWSER")`），便于区分不同浏览器下的测试结果。

---
如需扩展新平台、业务或参数化场景，请补充本README并同步更新相关目录文档。
