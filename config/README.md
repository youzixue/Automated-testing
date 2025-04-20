# config 配置层说明

本目录用于存放所有环境相关的配置文件，支持多环境（dev/test/prod）切换和外部化配置。

## 主要内容
- 通用基础配置：config/settings.yaml
- 各环境专用配置：config/env/test.yaml、config/env/prod.yaml
- 本地开发配置：config/.env（不提交到版本库）

## 设计原则
- 所有可变配置均应外部化，不允许硬编码（见 external-configuration.mdc）
- 配置项需有详细注释，便于理解和维护
- 新增/调整配置项时，务必补充本 README

## 参考
- .cursor/rules/external-configuration.mdc
