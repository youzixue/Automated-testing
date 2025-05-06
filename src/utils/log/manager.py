from __future__ import annotations
import logging
import os
from typing import Optional, Dict, List, Any
from datetime import datetime
import json
from pathlib import Path

from src.utils.config.manager import get_config

LOG_LEVEL_DEBUG = logging.DEBUG
LOG_LEVEL_INFO = logging.INFO
LOG_LEVEL_WARNING = logging.WARNING
LOG_LEVEL_ERROR = logging.ERROR
LOG_LEVEL_CRITICAL = logging.CRITICAL

_DEFAULT_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
_DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"
_DEFAULT_LOG_DIR = "output/logs"

_loggers: Dict[str, logging.Logger] = {}

_LEVEL_MAP = {
    'DEBUG': LOG_LEVEL_DEBUG,
    'INFO': LOG_LEVEL_INFO,
    'WARNING': LOG_LEVEL_WARNING,
    'ERROR': LOG_LEVEL_ERROR,
    'CRITICAL': LOG_LEVEL_CRITICAL
}

# --- 默认配置 --- (会被配置文件和环境变量覆盖)
DEFAULT_LOG_CONFIG: Dict[str, Any] = {
    "format": '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    "level": "INFO", # 默认根日志级别
    "file": {
        "enabled": True,
        "path": "output/logs/default", # 默认日志目录
        "filename": "app.log", # Default fixed filename if date is not used
        "max_size": 10, # MB (Only relevant for RotatingFileHandler)
        "backup_count": 5 # (Only relevant for RotatingFileHandler/TimedRotatingFileHandler)
    },
    "console": {
        "enabled": True,
        "color": False # 默认不使用颜色
    },
    "loggers": {} # 特定 logger 的配置
}

# --- 全局日志状态标记 --- #
_logging_configured = False
_root_logger = logging.getLogger() # 获取根 logger

def _get_level_from_config() -> int:
    """从配置中读取日志级别字符串并转换为 logging 常量。"""
    config = get_config()
    level_str = config.get('log', {}).get('level', 'INFO').upper()
    return _LEVEL_MAP.get(level_str, LOG_LEVEL_INFO)

def get_logger(
    name: Optional[str] = None,
    level: Optional[int] = None,
) -> logging.Logger:
    """
    获取或创建标准化日志器。
    日志级别优先从配置读取。
    """
    global _loggers
    logger_name = name or "root"

    if logger_name in _loggers:
        existing_logger = _loggers[logger_name]
        if level is not None and existing_logger.level != level:
             existing_logger.setLevel(level)
        elif level is None and logger_name != "root":
             current_global_level = _get_level_from_config()
             if existing_logger.level != current_global_level:
                  existing_logger.setLevel(current_global_level)
        return existing_logger

    logger = logging.getLogger(logger_name)
    determined_level = level if level is not None else _get_level_from_config()
    logger.setLevel(determined_level)
    logger.propagate = True
    _loggers[logger_name] = logger
    return logger

def set_global_log_level(level: int) -> None:
    """
    设置所有已创建日志器的日志级别以及根日志器的级别。
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    for logger in _loggers.values():
        logger.setLevel(level)

def _merge_configs(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """递归合并两个字典，override 中的值会覆盖 base 中的值。"""
    merged = base.copy()
    for key, value in override.items():
        if isinstance(value, dict) and key in merged and isinstance(merged[key], dict):
            merged[key] = _merge_configs(merged[key], value)
        else:
            merged[key] = value
    return merged

def setup_logging(config: Optional[Dict[str, Any]] = None):
    """
    配置全局日志系统 (当前活动版本)。

    根据提供的配置字典设置日志格式、级别、输出目标（控制台、文件）。
    支持为特定的 logger 设置不同的级别。
    该函数应该在应用程序启动时或测试会话开始时调用一次。
    使用 FileHandler 并动态生成每日日志文件名 (run_YYYY-MM-DD.log)。

    Args:
        config: 日志配置字典，结构应类似 DEFAULT_LOG_CONFIG。如果为 None，则使用默认配置。
    """
    global _logging_configured
    if _logging_configured:
        return

    effective_config = _merge_configs(DEFAULT_LOG_CONFIG, config or {})
    log_config = effective_config.get('log', effective_config)

    for handler in _root_logger.handlers[:]:
        _root_logger.removeHandler(handler)
        handler.close()

    level_from_env = os.environ.get("LOG_LEVEL")
    level_from_config = log_config.get("level", DEFAULT_LOG_CONFIG["level"])
    final_level_str = level_from_env or level_from_config
    if not isinstance(final_level_str, str):
        print(f"[ERROR] [Logging Setup] Invalid log level configuration. Expected string but got {type(final_level_str)}: {final_level_str}. Falling back to INFO.")
        final_level_str = "INFO"
    final_level_int = _LEVEL_MAP.get(final_level_str.upper(), LOG_LEVEL_INFO)
    _root_logger.setLevel(final_level_int)

    log_format_str = log_config.get("format", DEFAULT_LOG_CONFIG["format"])
    formatter = logging.Formatter(log_format_str)

    console_config = log_config.get("console", DEFAULT_LOG_CONFIG["console"])
    if console_config.get("enabled", DEFAULT_LOG_CONFIG["console"]["enabled"]):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        _root_logger.addHandler(console_handler)

    # --- 配置 File Handler with Date in Filename --- #
    file_config = log_config.get("file", DEFAULT_LOG_CONFIG["file"])
    if file_config.get("enabled", DEFAULT_LOG_CONFIG["file"]["enabled"]):
        log_dir_path = file_config.get("path", DEFAULT_LOG_CONFIG["file"]["path"])
        
        log_dir = Path(log_dir_path)
        if not log_dir.is_absolute():
             project_root = Path(__file__).parent.parent.parent.parent
             log_dir = project_root / log_dir_path
        
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_filename = f"run_{datetime.now().strftime('%Y-%m-%d')}.log"
            log_file_path = log_dir / log_filename
            
            file_handler = logging.FileHandler(
                filename=str(log_file_path),
                encoding='utf-8',
                mode='a'
            )

            file_handler.setFormatter(formatter)
            _root_logger.addHandler(file_handler)

        except OSError as e:
            print(f"[ERROR] [Logging Setup] 创建日志目录或文件失败: {e}")
        except Exception as e:
            print(f"[ERROR] [Logging Setup] 配置日志文件处理器时出错 (路径: {log_file_path if 'log_file_path' in locals() else '未知'}): {e}")

    loggers_config = log_config.get("loggers", DEFAULT_LOG_CONFIG["loggers"])
    if isinstance(loggers_config, dict):
        for logger_name, logger_opts in loggers_config.items():
            if isinstance(logger_opts, dict):
                level_str = logger_opts.get("level")
                if level_str and isinstance(level_str, str):
                    level_int = _LEVEL_MAP.get(level_str.upper())
                    if level_int is not None:
                        logging.getLogger(logger_name).setLevel(level_int)
                    else:
                        print(f"[WARNING] [Logging Setup] Logger '{logger_name}' 的配置级别 '{level_str}' 无效")
            else:
                 print(f"[WARNING] [Logging Setup] Logger '{logger_name}' 的配置格式无效 (应为字典)")

    _logging_configured = True

def log_exception(logger: logging.Logger, msg: str = "发生未处理的异常", *args, **kwargs):
    """记录异常信息，自动包含 traceback。"""
    logger.exception(msg, *args, **kwargs)