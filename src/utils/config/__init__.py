"""
配置子模块。

提供配置加载、管理和访问功能，实现框架统一的配置管理机制。
"""

# 移除对 ConfigManager 的导入
# from src.utils.config.manager import ConfigManager
# 导入 DefaultConfigManager 和 get_config 函数
from src.utils.config.manager import get_config
from src.utils.config.loaders import YamlConfigLoader as YamlLoader, JsonConfigLoader as JsonLoader, EnvConfigLoader as EnvLoader

__all__ = [
    # 移除 ConfigManager
    # 'ConfigManager',
    'get_config', # 只导出获取实例的函数
    'YamlLoader',
    'JsonLoader',
    'EnvLoader'
] 