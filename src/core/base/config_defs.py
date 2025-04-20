"""
配置相关的定义，如配置层级枚举。
"""
from enum import Enum, auto

class ConfigLevel(Enum):
    """配置层级枚举。"""
    DEFAULT = auto()     # 默认基础配置 (e.g., config/settings.yaml)
    ENVIRONMENT = auto() # 环境特定配置文件 (e.g., config/env/dev.yaml)
    TEST = auto()        # 测试特定配置 (通常通过 fixture 或测试代码动态加载/覆盖)
    LOCAL = auto()       # 本地覆盖文件 (e.g., config/local.yaml, 不提交到版本控制)
    ENV_VAR = auto()     # 环境变量覆盖 (最高优先级)
    # 注意:settings.yaml 作为 DEFAULT

# 配置优先级顺序（高优先级会覆盖低优先级）
CONFIG_PRIORITY_ORDER = [
    ConfigLevel.ENV_VAR,      # 环境变量，最高优先级
    ConfigLevel.LOCAL,        # 本地覆盖
    ConfigLevel.TEST,         # 测试特定
    ConfigLevel.ENVIRONMENT,  # 环境特定
    ConfigLevel.DEFAULT,      # 默认基础配置
]

# 配置合并顺序（应先加载低优先级，最后加载高优先级，保证高优先级覆盖低优先级）
# 实际合并时，先加载DEFAULT，依次叠加，最后加载ENV_VAR
CONFIG_MERGE_ORDER = list(reversed(CONFIG_PRIORITY_ORDER)) 