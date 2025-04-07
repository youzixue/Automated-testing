"""
配置管理模块。

提供多级配置系统，支持从不同来源加载配置并按优先级合并。
支持环境变量覆盖，确保敏感信息安全处理。
"""

import os
import logging
import functools
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union, cast, Callable, TypeVar, Type, Generic
import yaml
import threading
from copy import deepcopy # 导入 deepcopy

from src.utils.config.loaders import YamlConfigLoader, JsonConfigLoader, EnvConfigLoader, ConfigLoader
from src.utils.patterns import Singleton
from src.utils.event import EventBus
from src.core.base.errors import ConfigTypeError, ConfigurationError

from src.core.base.config_defs import ConfigLevel, CONFIG_PRIORITY_ORDER, CONFIG_MERGE_ORDER

# 类型变量用于泛型转换
T = TypeVar('T')

# --- 全局变量和锁 ---
_config_manager: Optional["DefaultConfigManager"] = None # 使用字符串避免导入问题
_config_lock = threading.RLock()

# --- 定义 deep_merge 函数 ---
def deep_merge(source: Dict, destination: Dict) -> Dict:
    """递归地深度合并两个字典.

    Args:
        source: 源字典, 其值将合并到目标字典中.
        destination: 目标字典, 将被修改.

    Returns:
        合并后的目标字典.
    """
    destination = deepcopy(destination) # 创建目标字典的深拷贝以避免修改原始对象
    for key, value in source.items():
        if isinstance(value, dict):
            # 获取或初始化目标字典中的嵌套字典
            node = destination.setdefault(key, {})
            if isinstance(node, dict): # 确保目标也是字典
                 deep_merge(value, node)
            else:
                 # 如果目标中对应键的值不是字典, 源值将覆盖它
                 destination[key] = deepcopy(value)
        elif isinstance(value, list):
             # 如果源值是列表, 进行合并或替换 (这里选择替换)
             # 可以根据需要实现更复杂的列表合并逻辑
             destination[key] = deepcopy(value)
        else:
            # 对于非字典和非列表类型, 源值直接覆盖目标值
            destination[key] = value # 不需要 deepcopy, 因为源值是不可变或最终类型
    return destination

# --- 初始化函数 ---

def initialize_config_manager(
    config_dir: Optional[str] = None,
    default_config_file: str = "settings.yaml",
    env_dir: Optional[str] = "env",
    local_config_file: Optional[str] = "local.yaml",
    env_var_prefix: str = "APP_",
    loaders: Optional[Dict[str, Type[ConfigLoader]]] = None,
    load_order: Optional[List[ConfigLevel]] = None,
    merge_strategy: Callable[[Dict, Dict], Dict] = deep_merge,
    raise_on_missing_env: bool = False,
    debug: bool = False,
) -> "DefaultConfigManager":
    """初始化或重新初始化配置管理器单例.

    Args:
        config_dir: 配置文件的根目录.
        default_config_file: 默认配置文件名.
        env_dir: 环境特定配置文件的子目录.
        local_config_file: 本地覆盖文件名.
        env_var_prefix: 用于覆盖配置的环境变量前缀.
        loaders: 自定义加载器字典.
        load_order: 自定义配置加载顺序.
        merge_strategy: 自定义配置合并策略.
        raise_on_missing_env: 如果为 True, 当找不到环境文件时抛出异常.
        debug: 是否启用调试日志.

    Returns:
        初始化后的 DefaultConfigManager 实例.
    """
    global _config_manager
    with _config_lock:
        # 配置日志记录器, 确保在导入时可用
        log_level = logging.DEBUG if debug else logging.INFO
        logging.basicConfig(level=log_level, format='%(asctime)s [%(levelname)s] [%(name)s] [%(process)d] - %(message)s')
        logger = logging.getLogger(__name__) # 获取此模块的日志记录器

        if debug:
            logger.debug("Debug logging enabled for config manager initialization.")

        # 延迟导入以避免循环
        from .loaders import YamlConfigLoader, JsonConfigLoader, EnvConfigLoader # 确保导入正确

        default_loaders = {
            ".yaml": YamlConfigLoader,
            ".yml": YamlConfigLoader,
            ".json": JsonConfigLoader,
        }
        if loaders:
            default_loaders.update(loaders)

        env_loader = EnvConfigLoader(prefix=env_var_prefix)

        # 优先使用传入的 config_dir, 否则尝试从环境变量获取, 最后使用默认路径
        if config_dir is None:
            config_dir_env = os.getenv("CONFIG_DIR")
            if config_dir_env:
                config_dir = config_dir_env
            else:
                # 获取当前文件的路径
                current_file = Path(__file__).resolve()
                # 从当前文件位置向上查找项目根目录（包含 config 目录的位置）
                project_root = current_file.parent.parent.parent.parent
                config_dir = str(project_root / "config")
                logger.debug(f"使用默认配置目录路径: {config_dir}")

        # 实例化 DefaultConfigManager - 定义在文件末尾
        _config_manager = DefaultConfigManager(
            config_dir=config_dir,
            default_config_file=default_config_file,
            env_dir=env_dir,
            local_config_file=local_config_file,
            env_loader=env_loader,
            file_loaders=default_loaders,
            load_order=load_order,
            merge_strategy=merge_strategy,
            raise_on_missing_env=raise_on_missing_env,
        )
        _config_manager.load_config() # 加载配置
        logger.info(f"配置管理器已成功初始化, 配置目录: {config_dir}")
        return _config_manager

# Helper function to get the singleton instance
def get_config() -> Dict[str, Any]:
    """获取最终合并后的配置字典."""
    global _config_manager
    with _config_lock:
        if _config_manager is None:
            # 获取此模块的日志记录器
            logger = logging.getLogger(__name__)
            logger.warning("Config Manager accessed before explicit initialization. Initializing with default settings.")
            # 调用现在已定义的初始化函数
            initialize_config_manager()

        # 确保 _config_manager 已被初始化
        if _config_manager is None:
            # This case should ideally not happen after initialization
            raise ConfigurationError("配置管理器未能初始化")

        # 返回加载后的配置字典, 而不是管理器实例
        return _config_manager.get_all()


# --- 配置管理器类 (确保定义在 initialize_config_manager 和 get_config 之后) ---
class DefaultConfigManager(Singleton):
    """默认配置管理器实现.

    处理配置文件的加载、合并和访问.
    """

    def __init__(self,
                 config_dir: str,
                 default_config_file: str = "settings.yaml",
                 env_dir: Optional[str] = "env",
                 local_config_file: Optional[str] = "local.yaml",
                 env_loader: Optional[EnvConfigLoader] = None,
                 file_loaders: Optional[Dict[str, Type[ConfigLoader]]] = None,
                 load_order: Optional[List[ConfigLevel]] = None,
                 merge_strategy: Callable[[Dict, Dict], Dict] = deep_merge,
                 raise_on_missing_env: bool = False):
        """初始化配置管理器.
        
        Args:
            config_dir: 配置文件的根目录.
            default_config_file: 默认配置文件名 (相对于config_dir).
            env_dir: 环境特定配置子目录 (相对于config_dir).
            local_config_file: 本地覆盖配置文件名 (相对于config_dir).
            env_loader: 用于加载环境变量的加载器实例.
            file_loaders: 文件扩展名到加载器类的映射.
            load_order: 配置加载和合并的顺序.
            merge_strategy: 用于合并配置字典的函数.
            raise_on_missing_env: 如果找不到环境配置文件是否引发错误.
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config_dir = Path(config_dir)
        self._default_config_file = default_config_file
        self._env_dir = env_dir
        self._local_config_file = local_config_file
        self._env_loader = env_loader or EnvConfigLoader()
        self._file_loaders = file_loaders or {}
        self._load_order = load_order or CONFIG_MERGE_ORDER
        self._merge_strategy = merge_strategy
        self._raise_on_missing_env = raise_on_missing_env

        self._config_layers: Dict[ConfigLevel, Dict[str, Any]] = {level: {} for level in ConfigLevel}
        self._merged_config: Dict[str, Any] = {}
        self._initialized = False

        self._logger.info(f"配置管理器使用的配置目录: {self._config_dir}")
        if not self._config_dir.is_dir():
            self._logger.warning(f"指定的配置目录不存在: {self._config_dir}")
            # Consider raising an error or trying to create it?
            # For now, just log a warning. Loading will likely fail.

    def _get_loader(self, file_path: Path) -> Optional[ConfigLoader]:
        """根据文件扩展名获取合适的加载器."""
        ext = file_path.suffix.lower()
        loader_cls = self._file_loaders.get(ext)
        return loader_cls() if loader_cls else None

    def _load_file(self, file_path: Path, level: ConfigLevel) -> None:
        """加载单个配置文件."""
        if not file_path.is_file():
            msg = f"配置文件不存在或不是文件: {file_path}, 跳过加载"
            if level == ConfigLevel.ENVIRONMENT and self._raise_on_missing_env:
                self._logger.error(msg)
                raise FileNotFoundError(msg)
            elif level != ConfigLevel.LOCAL: # Don't warn for missing optional local file
                 self._logger.warning(msg)
            else:
                 self._logger.debug(msg) # Debug level for missing local file
            return

        loader = self._get_loader(file_path)
        if not loader:
            self._logger.warning(f"没有找到适用于 '{file_path.suffix}' 的加载器, 跳过文件: {file_path}")
            return

        try:
            config_data = loader.load(file_path)
            if config_data:
                self._config_layers[level] = self._merge_strategy(self._config_layers.get(level, {}), config_data)
                self._logger.info(f"加载配置文件: {file_path} 到级别 {level.name}")
            else:
                self._logger.debug(f"配置文件为空或加载失败 (返回None): {file_path}")
        except Exception as e:
            self._logger.error(f"加载配置文件 '{file_path}' 时出错: {e}", exc_info=True)
            # Decide if we should raise, or just log and continue
            # raise ConfigurationError(f"Failed to load config file: {file_path}") from e

    def _merge_configs(self) -> None:
        """按照指定顺序合并所有配置层."""
        self._merged_config = {}
        self._logger.debug(f"开始合并配置层, 顺序: {[level.name for level in self._load_order]}")
        for level in self._load_order:
            layer_data = self._config_layers.get(level, {})
            if layer_data:
                self._logger.debug(f"合并层级: {level.name}, 数据键: {list(layer_data.keys())}")
                self._merged_config = self._merge_strategy(self._merged_config, layer_data)
            else:
                 self._logger.debug(f"层级 {level.name} 为空, 跳过合并")
        self._logger.debug("配置合并完成")
        # self._logger.debug(f"最终合并配置: {self._merged_config}") # May log sensitive data

    def load_config(self) -> None:
        """加载所有配置文件并合并."""
        self._logger.info("开始加载默认配置文件...")

        # 1. 加载默认配置
        default_path = self._config_dir / self._default_config_file
        self._load_file(default_path, ConfigLevel.DEFAULT)

        # 2. 加载环境特定配置 (如果 env_dir 提供)
        if self._env_dir:
            app_env = os.getenv("APP_ENV", "dev").lower()
            env_file_name = f"{app_env}.yaml" # Or infer extension?
            env_path = self._config_dir / self._env_dir / env_file_name
            self._load_file(env_path, ConfigLevel.ENVIRONMENT)
        else:
            self._logger.debug("未配置环境特定配置目录 (env_dir), 跳过加载环境配置")

        # 3. 加载本地配置 (如果 local_config_file 提供)
        if self._local_config_file:
            local_path = self._config_dir / self._local_config_file
            self._load_file(local_path, ConfigLevel.LOCAL)
        else:
            self._logger.debug("未配置本地覆盖配置文件名 (local_config_file), 跳过加载本地配置")

        # 4. 加载环境变量
        try:
            env_data = self._env_loader.load()
            if env_data:
                self._config_layers[ConfigLevel.ENV_VAR] = env_data
                self._logger.info("已加载环境变量覆盖配置")
            else:
                 self._logger.debug("未找到匹配的环境变量覆盖")
        except Exception as e:
            self._logger.error(f"加载环境变量时出错: {e}", exc_info=True)

        # 5. 合并所有配置
        self._merge_configs()
        self._initialized = True
        self._logger.info("默认配置文件加载完成")

    def reload_config(self) -> None:
        """重新加载所有配置."""
        self._logger.info("重新加载配置...")
        self._config_layers = {level: {} for level in ConfigLevel}
        self._merged_config = {}
        self._initialized = False
        self.load_config()

    def get(self, key: str, default: Optional[T] = None) -> Union[Any, T]:
        """获取指定键的配置值.

        使用点表示法访问嵌套值 (例如, 'database.host').
        
        Args:
            key: 配置键 (可以使用点表示法).
            default: 如果键不存在时返回的默认值.
            
        Returns:
            配置值或默认值.
        """
        if not self._initialized:
            self._logger.warning("配置尚未初始化, 尝试加载默认配置")
            self.load_config()

        keys = key.split('.')
        value = self._merged_config
        try:
            for k in keys:
                if isinstance(value, dict):
                     value = value[k]
                # Allow accessing list elements by index string
                elif isinstance(value, list) and k.isdigit():
                     idx = int(k)
                     if 0 <= idx < len(value):
                          value = value[idx]
                     else:
                          raise KeyError(f"索引 {k} 超出列表范围")
                else:
                    raise KeyError(f"键 '{k}' 在非字典或列表的路径中: {key}")
            return value
        except (KeyError, IndexError):
            self._logger.debug(f"配置键 '{key}' 未找到, 返回默认值: {default}")
            return default
        except Exception as e:
             self._logger.error(f"获取配置键 '{key}' 时出错: {e}")
             return default

    def get_all(self) -> Dict[str, Any]:
        """获取所有合并后的配置."""
        if not self._initialized:
            self._logger.warning("配置尚未初始化, 尝试加载默认配置")
            self.load_config()
        return self._merged_config.copy() # 返回副本以防止外部修改

    def get_dict(self, key: str, default: Optional[Dict] = None) -> Dict[str, Any]:
        """获取字典类型的配置值."""
        value = self.get(key, default)
        if not isinstance(value, dict):
            self._logger.warning(f"配置键 '{key}' 的值不是字典类型 (实际类型: {type(value)}), 返回默认值")
            return default if default is not None else {}
        return value

    def get_list(self, key: str, default: Optional[List] = None) -> List[Any]:
        """获取列表类型的配置值."""
        value = self.get(key, default)
        if not isinstance(value, list):
            self._logger.warning(f"配置键 '{key}' 的值不是列表类型 (实际类型: {type(value)}), 返回默认值")
            return default if default is not None else []
        return value

    def get_str(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取字符串类型的配置值."""
        value = self.get(key, default)
        if value is None:
             return default
        if not isinstance(value, str):
            self._logger.warning(f"配置键 '{key}' 的值不是字符串类型 (实际类型: {type(value)}), 尝试转换为字符串")
            try:
                 return str(value)
            except Exception:
                 self._logger.error(f"无法将配置键 '{key}' 的值转换为字符串")
                 return default
        return value

    def get_int(self, key: str, default: Optional[int] = None) -> Optional[int]:
        """获取整数类型的配置值."""
        value = self.get(key, default)
        if value is None:
             return default
        if isinstance(value, int):
             return value
        if isinstance(value, str) and value.isdigit():
             try:
                  return int(value)
             except ValueError:
                 pass # Fall through to warning
        self._logger.warning(f"配置键 '{key}' 的值不是有效的整数 (值: {value}), 返回默认值")
        return default

    def get_float(self, key: str, default: Optional[float] = None) -> Optional[float]:
        """获取浮点数类型的配置值."""
        value = self.get(key, default)
        if value is None:
            return default
        if isinstance(value, (int, float)): # Allow int to be converted
             return float(value)
        if isinstance(value, str):
             try:
                  return float(value)
             except ValueError:
                 pass # Fall through to warning
        self._logger.warning(f"配置键 '{key}' 的值不是有效的浮点数 (值: {value}), 返回默认值")
        return default
    
    def get_bool(self, key: str, default: Optional[bool] = None) -> Optional[bool]:
        """获取布尔类型的配置值.

        识别 'true', 'yes', '1' 为 True (不区分大小写),
        'false', 'no', '0' 为 False (不区分大小写).
        其他值会记录警告并返回默认值.
        """
        value = self.get(key, default)
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            val_lower = value.lower()
            if val_lower in ('true', 'yes', '1'):
                return True
            if val_lower in ('false', 'no', '0'):
                return False
        if isinstance(value, int):
             if value == 1:
                  return True
             if value == 0:
                 return False
    
        self._logger.warning(f"配置键 '{key}' 的值不是有效的布尔值 (值: {value}), 返回默认值")
        return default

    def is_set(self, key: str) -> bool:
        """检查配置键是否存在."""
        return self.get(key, _SENTINEL) is not _SENTINEL

    def clear_level(self, level: ConfigLevel) -> None:
        """清除指定配置层级的数据."""
        if level in self._config_layers:
            self._config_layers[level] = {}
            self._merge_configs() # 清除后重新合并
            self._logger.debug(f"已清除配置层级: {level.name}")
    
_SENTINEL = object() # 用于区分None和未设置

# --- 配置管理器类 --- 