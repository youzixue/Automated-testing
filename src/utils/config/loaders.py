"""
配置加载器模块。

提供不同类型配置文件和环境变量的加载功能。
"""

import os
import json
from typing import Any, Dict, Type, Optional
from abc import ABC, abstractmethod

from src.utils.patterns import Singleton
from src.core.base.errors import ConfigurationError


class ConfigLoader(ABC):
    """配置加载器接口。
    
    定义配置加载的标准接口。
    """
    
    @abstractmethod
    def load(self, path: str) -> Dict[str, Any]:
        """加载配置文件。
        
        Args:
            path: 配置文件路径
            
        Returns:
            配置字典
            
        Raises:
            FileNotFoundError: 配置文件不存在
            ValueError: 配置文件格式错误
        """
        pass
    
    @abstractmethod
    def supports(self, path: str) -> bool:
        """检查是否支持加载指定路径的配置文件。
        
        Args:
            path: 配置文件路径
            
        Returns:
            是否支持加载指定路径的配置文件
        """
        pass


class YamlConfigLoader(ConfigLoader):
    """YAML配置加载器。
    
    从YAML文件加载配置。
    """
    
    def __init__(self):
        """初始化YAML配置加载器。"""
        pass
    
    def load(self, path: str) -> Dict[str, Any]:
        """从YAML文件加载配置。
        
        Args:
            path: 配置文件路径
            
        Returns:
            配置字典
            
        Raises:
            ImportError: 未安装PyYAML
            FileNotFoundError: 配置文件不存在
            yaml.YAMLError: YAML解析错误
        """
        try:
            import yaml
        except ImportError:
            raise ImportError("未安装PyYAML，请使用 pip install pyyaml 安装")
        
        if not os.path.exists(path):
            raise FileNotFoundError(f"配置文件不存在: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                if config is None:  # 空文件
                    config = {}
                return config
        except yaml.YAMLError as e:
            raise
    
    def supports(self, path: str) -> bool:
        """检查是否支持加载指定路径的YAML配置文件。
        
        Args:
            path: 配置文件路径
            
        Returns:
            是否支持加载
        """
        return path.lower().endswith(('.yaml', '.yml'))


class JsonConfigLoader(ConfigLoader):
    """JSON配置加载器。
    
    从JSON文件加载配置。
    """
    
    def __init__(self):
        """初始化JSON配置加载器。"""
        pass
    
    def load(self, path: str) -> Dict[str, Any]:
        """从JSON文件加载配置。
        
        Args:
            path: 配置文件路径
            
        Returns:
            配置字典
            
        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: JSON解析错误
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"配置文件不存在: {path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            raise
    
    def supports(self, path: str) -> bool:
        """检查是否支持加载指定路径的JSON配置文件。
        
        Args:
            path: 配置文件路径
            
        Returns:
            是否支持加载
        """
        return path.lower().endswith('.json')


class EnvConfigLoader(ConfigLoader):
    """环境变量配置加载器。
    
    从环境变量加载配置。
    """
    
    def __init__(self, prefix: str = "APP_"):
        """初始化环境变量配置加载器。
        
        Args:
            prefix: 环境变量前缀，默认为"APP_"
        """
        self._prefix = prefix
    
    def load(self, path: str = None) -> Dict[str, Any]:
        """从环境变量加载配置。
        
        实现ConfigLoader接口，path参数在此处不使用但保留以兼容接口。
        
        环境变量命名规则：
        - 前缀_分隔的大写变量名，例如 APP_LOG_LEVEL
        - 转换为小写下划线格式的配置项，例如 log.level
        
        Args:
            path: 配置文件路径（在环境变量加载器中不使用，但保留以兼容接口）
            
        Returns:
            配置字典
        """
        config = {}
        
        for key, value in os.environ.items():

            if not key.startswith(self._prefix):
                continue

            config_key = key[len(self._prefix):].lower() 
            config_key = config_key.replace("__", ".")
            config_value = self._convert_value(value)

            config[config_key] = config_value
        
        return config
    
    def supports(self, path: str) -> bool:
        """检查是否支持加载指定路径的配置。
        
        实现ConfigLoader接口。对于环境变量加载器，该方法始终返回True，
        因为它不依赖于特定的文件路径。
        
        Args:
            path: 配置文件路径
            
        Returns:
            是否支持加载
        """
        return True
    
    def _convert_value(self, value: str) -> Any:
        """转换环境变量值类型。
        
        尝试转换为布尔值、整数、浮点数，如果都不行则保持字符串。
        
        Args:
            value: 环境变量值
            
        Returns:
            转换后的值
        """

        if value.lower() in ['true', 'yes', '1', 'on']:
            return True
        if value.lower() in ['false', 'no', '0', 'off']:
            return False
        
        try:
            return int(value)
        except ValueError:
            pass
        
        try:
            return float(value)
        except ValueError:
            pass
        
        if (value.startswith('{') and value.endswith('}')) or \
           (value.startswith('[') and value.endswith(']')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        return value