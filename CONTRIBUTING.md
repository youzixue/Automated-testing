# 贡献指南

感谢您对本项目的关注！我们欢迎各种形式的贡献，包括但不限于bug修复、功能增强、文档改进等。

## 开发流程

1. Fork本仓库
2. 创建你的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交你的修改 (`git commit -m 'feat: add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 提交Pull Request

## 提交规范

本项目使用约定式提交(Conventional Commits)规范，所有commit消息必须遵循以下格式：

```
<类型>[可选作用域]: <描述>
```

类型必须是以下之一:
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 仅文档变更
- `style`: 不影响代码含义的变化(空白、格式化等)
- `refactor`: 既不修复错误也不添加功能的代码变更
- `perf`: 提高性能的代码变更
- `test`: 添加或修正测试
- `chore`: 对构建过程或辅助工具和库的更改

## 代码规范

- 所有Python代码必须遵循PEP 8规范
- 所有公共API必须有完整的文档字符串
- 所有公共方法必须有类型注解
- 单元测试覆盖率必须达到80%以上

## 分支管理

- `main`: 主分支，保持稳定可用
- `develop`: 开发分支，新功能合并到这里
- `feature/*`: 特性分支，用于开发新功能
- `fix/*`: 修复分支，用于修复bug
- `release/*`: 发布分支，用于版本发布准备

## 开发环境设置

```bash
# 安装开发依赖
poetry install --with dev

# 运行代码检查
poetry run pylint src tests
poetry run mypy src tests

# 运行测试
poetry run pytest
```

## 代码审查

所有Pull Request必须通过以下检查：
- 代码风格检查 (pylint)
- 类型检查 (mypy)
- 单元测试通过
- 代码审查（至少一个维护者批准）

## 文档

- 新功能必须有相应文档
- 文档位于`docs/`目录
- API文档通过docstring自动生成

感谢您的贡献！ 