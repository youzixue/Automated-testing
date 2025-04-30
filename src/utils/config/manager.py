import os
import re
from .loaders import YamlConfigLoader

def _replace_env_vars(obj):
    """递归替换${env:KEY}为os.environ['KEY']"""
    pattern = re.compile(r"\$\{env:([A-Z0-9_]+)(:-[^}]*)?\}")
    if isinstance(obj, dict):
        return {k: _replace_env_vars(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_replace_env_vars(i) for i in obj]
    elif isinstance(obj, str):
        def repl(match):
            key = match.group(1)
            default = match.group(2)[2:] if match.group(2) else ""
            return os.environ.get(key, default)
        return pattern.sub(repl, obj)
    else:
        return obj

def get_config(env=None):
    """统一加载配置，优先级：settings.yaml < env/{env}.yaml < 环境变量"""
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../'))
    settings_path = os.path.join(base, 'config/settings.yaml')
    
    # --- 确定环境 --- 
    determined_env = env or os.environ.get("APP_ENV", "dev")
    # --- !!! 添加调试打印 !!! ---
    print(f"[DEBUG] get_config: Determined environment to load: {determined_env} (from parameter: {env}, from os.environ['APP_ENV']: {os.environ.get('APP_ENV')}, default: dev)")
    # ---------------------------
    
    env_path = os.path.join(base, f'config/env/{determined_env}.yaml') # 使用 determined_env

    loader = YamlConfigLoader()
    config = loader.load(settings_path)
    if os.path.exists(env_path):
        env_config = loader.load(env_path)
        config.update(env_config)
    config = _replace_env_vars(config)
    return config
