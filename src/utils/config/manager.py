import os
import re
from .loaders import YamlConfigLoader

def _replace_env_vars(obj):
    """递归替换${env:KEY:-default}为os.environ['KEY']或默认值"""
    pattern = re.compile(r"\$\{env:([A-Z0-9_]+)(:-(.*?))?\}")
    if isinstance(obj, dict):
        return {k: _replace_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_env_vars(i) for i in obj]
    elif isinstance(obj, str):
        def repl(match):
            key = match.group(1)
            default = match.group(3) if match.group(3) is not None else ""
            env_value = os.environ.get(key)
            # 如果环境变量存在，则使用它，否则使用默认值
            final_value = env_value if env_value is not None else default
            return final_value
            
        replaced_string = pattern.sub(repl, obj)
        return replaced_string
    else:
        return obj

def get_config(env=None):
    """统一加载配置，优先级：settings.yaml < env/{env}.yaml < 环境变量"""
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
    settings_path = os.path.join(base, 'config/settings.yaml')
    
    determined_env = env or os.environ.get("APP_ENV", "dev")
    
    env_path = os.path.join(base, f'config/env/{determined_env}.yaml')

    loader = YamlConfigLoader()
    config = loader.load(settings_path)
    if os.path.exists(env_path):
        env_config = loader.load(env_path)
        config.update(env_config) # 浅层更新
        
    config = _replace_env_vars(config)
    
    return config
