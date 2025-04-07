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
    # 注意: GLOBAL 级别已移除，settings.yaml 作为 DEFAULT

# 定义配置合并和优先级顺序
# 优先级高的层级会覆盖优先级低的层级
CONFIG_PRIORITY_ORDER = [
    ConfigLevel.ENV_VAR,
    ConfigLevel.LOCAL,
    ConfigLevel.TEST,
    ConfigLevel.ENVIRONMENT,
    ConfigLevel.DEFAULT, # GLOBAL 已被 DEFAULT 替代
]

# 合并顺序与优先级相反，确保高优先级最后合并
CONFIG_MERGE_ORDER = list(reversed(CONFIG_PRIORITY_ORDER)) 