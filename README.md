# 自动化测试框架

本项目为企业级自动化测试框架，集成 Playwright、OCR 验证码识别、Allure 报告等，支持多平台、多环境的高效自动化测试。

## 目录结构（七层架构）
1. **测试用例层（tests/）**：存放所有自动化测试用例，按平台/业务分目录。
2. **固件层（tests/conftest.py 等）**：pytest fixtures、全局前置后置、数据工厂。
3. **业务对象层（src/web/pages/、src/api/services/、src/mobile/screens/）**：页面对象、服务对象、业务流程封装。
4. **平台实现层（src/web/、src/api/、src/mobile/）**：平台相关实现与适配。
5. **核心抽象层（src/core/base/）**：接口定义、抽象基类。
6. **工具层（src/utils/）**：通用工具、OCR、日志、数据工厂等。
7. **外部集成层（pyproject.toml）**：依赖声明与管理。

## 环境变量配置说明

- 所有环境变量请参考 `.env.example`，复制为 `.env` 后补充实际值。
- **本地开发推荐配置：**
  - `UPLOAD_REPORT=true`  # 需要上传Allure报告到远程Web服务时设为true
  - `EMAIL_ENABLED=false` # 本地调试建议关闭邮件通知，避免骚扰
- **CI/CD环境推荐配置：**
  - `UPLOAD_REPORT=false` # CI执行机和Web服务同一台时设为false（默认即可）
  - `EMAIL_ENABLED=true`  # 自动发送测试报告邮件
- 详细注释已在 `.env.example` 中给出，团队成员请按需调整。

## 快速开始
1. 安装依赖：`poetry install`
2. 配置环境变量：复制 `.env.example` 为 `.env` 并补充实际值（见上文说明）
3. 运行测试：`pytest -n auto --alluredir=output/allure`
4. 查看报告：`allure serve output/allure`

## CI/CD集成与自动化
- 推荐CI/CD流水线仅调用主控脚本：
  ```bash
  python ci/scripts/run_and_notify.py
  # 或在Docker容器中：
  docker run ... automated-testing:latest bash -c "python ci/scripts/run_and_notify.py"
  ```
- 邮件通知、Allure报告上传等行为均可通过环境变量灵活控制，无需修改代码。
- 详细CI/CD集成方案见 docs/自动环境部署&CICD集成.md

## 主要特性
- Playwright 跨浏览器 UI 自动化
- ddddocr + Pillow 验证码识别
- Allure/HTML 测试报告
- 多环境配置（config/env/）
- 智能等待与异常处理
- 测试数据与逻辑分离
- CI/CD 集成与代码质量保障

## 参考文档
- docs/enhanced_architecture.md （架构设计）
- .cursor/rules/（项目规范）

## Allure命令动态配置

本项目支持本地和CI环境灵活调用Allure命令：
- 默认直接调用`allure`（需将allure加入PATH）
- 如需指定本地Allure路径，可设置环境变量`ALLURE_CMD`，如：
  - Windows本地：`ALLURE_CMD=D:\allure-2.33.0\bin\allure.bat`
  - Linux/Mac：`ALLURE_CMD=/usr/local/bin/allure`
- CI环境推荐全局安装allure并确保`allure`命令可用，无需设置ALLURE_CMD

脚本会自动优先读取`ALLURE_CMD`，未设置时回退为`allure`。

---
如需扩展新平台、业务或工具，请先查阅相关目录下 README。

## Docker环境下Allure CLI安装说明

- 由于国内网络环境限制，建议在构建Docker镜像前，手动下载 Allure CLI 安装包（allure-2.27.0.zip）并放置于项目根目录（与Dockerfile同级）。
- Dockerfile 会自动将该zip包COPY进镜像并完成解压与安装，无需外网下载。
- **注意：allure-2.27.0.zip 不建议提交到Git仓库，请在.gitignore中添加 `allure-*.zip` 进行忽略。**
- 下载地址（需科学上网）：https://github.com/allure-framework/allure2/releases/download/2.27.0/allure-2.27.0.zip
- 构建命令示例：
  ```bash
  docker build -t automated-testing:latest .
  ```
- 如需团队协作，请在文档或Wiki中明确说明此操作，确保所有成员一致。
