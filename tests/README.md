# tests 测试用例层说明

本目录是自动化测试框架七层架构中的 **测试用例层 (Tests)**，用于组织所有自动化测试用例，按平台和业务分目录，支持参数化、分层和多环境执行。

## 目录结构

```
tests/
├── web/               # Web UI 自动化测试用例
│   ├── conftest.py    # Web 平台特定的 Fixtures
│   └── omp/           # OMP 后台相关测试用例
│       └── test_login.py     # 登录测试
│
├── api/               # API 自动化测试用例
│   ├── conftest.py    # API 平台特定的 Fixtures
│   └── test_payment_unified_order.py  # 支付统一下单接口测试
│
├── mobile/            # 移动端自动化测试用例
│   ├── conftest.py    # 移动平台特定的 Fixtures
│   └── test_jiyu_monthly_card.py  # 积玉月卡测试
│
├── wechat/            # 微信平台自动化测试用例
│   ├── conftest.py    # 微信平台特定的 Fixtures
│   ├── test_mini_program_monthly_card.py  # 微信小程序月卡测试
│   └── test_official_account_monthly_card.py  # 微信公众号月卡测试
│
├── data/              # 测试数据目录 (建议迁移到项目根目录的 data/ 中)
│   └── web/           # Web测试相关数据
│
├── conftest.py        # 全局 pytest Fixtures 与配置
└── README.md          # 本说明文件
```

## 平台测试说明

### Web 测试 (tests/web/)
- **技术栈**: Playwright + pytest + Allure
- **页面对象**: 在 `src/web/pages/` 目录中定义，遵循页面对象模式 (POM)
- **主要测试**: OMP后台登录功能 (`test_login.py`)

### API 测试 (tests/api/)
- **技术栈**: httpx + pytest + Allure
- **服务对象**: 在 `src/api/services/` 目录中定义
- **主要测试**: 支付统一下单接口 (`test_payment_unified_order.py`)

### 移动应用测试 (tests/mobile/)
- **技术栈**: Airtest + PocoUI + pytest + Allure
- **屏幕对象**: 在 `src/mobile/screens/` 目录中定义
- **主要测试**: 积玉App月卡功能 (`test_jiyu_monthly_card.py`)
- **注意事项**: 移动测试必须使用 `-n 1` 参数串行执行，避免设备冲突

### 微信测试 (tests/wechat/)
- **技术栈**: Airtest + PocoUI + pytest + Allure
- **页面/组件对象**: 在 `src/wechat/screens/` 或 `src/wechat/components/` 目录中定义
- **主要测试**: 
  - 微信小程序月卡功能 (`test_mini_program_monthly_card.py`)
  - 微信公众号月卡功能 (`test_official_account_monthly_card.py`)
- **注意事项**: 微信测试必须使用 `-n 1` 参数串行执行，避免设备冲突

## 设计原则
- 测试用例与测试数据分离，数据统一存放于项目根目录的 `data/` 目录
- 用例应参数化，支持多账号、多场景、多浏览器测试
- 命名、注释、分层结构需与项目规范一致
- 使用Allure报告，便于结果追踪

## 多浏览器测试操作方法
本项目已支持多浏览器自动化测试（chromium/firefox/webkit），无需修改业务代码。

### 1. 通过环境变量切换浏览器类型
在运行pytest前设置 `BROWSER` 环境变量即可：

#### Windows PowerShell
```powershell
$env:BROWSER="chromium"; pytest tests/web
$env:BROWSER="firefox"; pytest tests/web
$env:BROWSER="webkit"; pytest tests/web
```

#### Windows CMD
```cmd
set BROWSER=chromium && pytest tests/web
set BROWSER=firefox && pytest tests/web
set BROWSER=webkit && pytest tests/web
```

#### Linux/Mac Bash
```bash
BROWSER=chromium pytest tests/web
BROWSER=firefox pytest tests/web
BROWSER=webkit pytest tests/web
```

### 2. 一次性批量执行三种浏览器
可编写批处理脚本批量执行：

#### PowerShell 脚本
```powershell
$env:BROWSER="chromium"; pytest tests/web
$env:BROWSER="firefox"; pytest tests/web
$env:BROWSER="webkit"; pytest tests/web
```

#### CMD 批处理
```bat
set BROWSER=chromium && pytest tests/web
set BROWSER=firefox && pytest tests/web
set BROWSER=webkit && pytest tests/web
```

#### Bash 脚本
```bash
for b in chromium firefox webkit; do
  BROWSER=$b pytest tests/web
done
```

### 3. 结果区分建议
建议在测试日志或Allure报告中打印当前浏览器类型（如 `os.environ.get("BROWSER")`），便于区分不同浏览器下的测试结果。

## 执行测试
```bash
# 执行所有平台测试 (不推荐，特别是包含移动和微信测试时)
poetry run pytest

# Web测试 (支持并行)
poetry run pytest tests/web -n auto --alluredir=output/allure-results

# API测试 (支持并行)
poetry run pytest tests/api -n auto --alluredir=output/allure-results

# 移动端测试 (必须串行执行)
poetry run pytest tests/mobile -n 1 --alluredir=output/allure-results

# 微信测试 (必须串行执行)
poetry run pytest tests/wechat -n 1 --alluredir=output/allure-results

# 使用标记过滤测试
poetry run pytest -m web
poetry run pytest -m api
poetry run pytest -m mobile
poetry run pytest -m wechat
poetry run pytest -m smoke
```

---
如需扩展新平台、业务或参数化场景，请补充本README并同步更新相关目录文档。遵循项目规范（见 `.cursor/rules/`）。
