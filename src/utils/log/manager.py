from __future__ import annotations
import logging
import os
from typing import Optional, Dict
from datetime import datetime

from src.utils.config.manager import get_config

LOG_LEVEL_DEBUG = logging.DEBUG
LOG_LEVEL_INFO = logging.INFO
LOG_LEVEL_WARNING = logging.WARNING
LOG_LEVEL_ERROR = logging.ERROR

_DEFAULT_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
_DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"
_DEFAULT_LOG_DIR = "output/logs"

_loggers: Dict[str, logging.Logger] = {}

_LEVEL_MAP = {
    'DEBUG': LOG_LEVEL_DEBUG,
    'INFO': LOG_LEVEL_INFO,
    'WARNING': LOG_LEVEL_WARNING,
    'ERROR': LOG_LEVEL_ERROR
}

def _get_level_from_config() -> int:
    """从配置中读取日志级别字符串并转换为 logging 常量。"""
    config = get_config()
    level_str = config.get('log', {}).get('level', 'INFO').upper()
    return _LEVEL_MAP.get(level_str, LOG_LEVEL_INFO)

def _get_log_dir_from_env() -> str:
    """
    优先从环境变量LOG_FILE_PATH获取日志目录，否则用默认值。
    支持.env、settings.yaml等配置联动。
    """
    log_dir = os.environ.get("LOG_FILE_PATH")
    if log_dir:
        # 变量替换，如 output/logs/${APP_ENV}
        app_env = os.environ.get("APP_ENV", "dev")
        log_dir = log_dir.replace("${APP_ENV}", app_env)
        log_dir = log_dir.replace("$APP_ENV", app_env)
        return log_dir
    return _DEFAULT_LOG_DIR

def _get_today_str() -> str:
    """获取当天日期字符串，格式为YYYY-MM-DD。"""
    return datetime.now().strftime("%Y-%m-%d")

def get_logger(
    name: Optional[str] = None,
    level: Optional[int] = None,
    fmt: str = _DEFAULT_FORMAT,
    datefmt: str = _DEFAULT_DATEFMT,
) -> logging.Logger:
    """
    获取或创建标准化日志器，单例模式，自动支持控制台、分文件和全局聚合日志输出。
    日志级别和目录优先从配置和环境变量读取。
    """
    global _loggers
    logger_name = name or "root"
    if logger_name in _loggers:
        existing_logger = _loggers[logger_name]
        determined_level = level if level is not None else _get_level_from_config()
        if existing_logger.level != determined_level:
            existing_logger.setLevel(determined_level)
            for handler in existing_logger.handlers:
                handler.setLevel(determined_level)
        return existing_logger

    determined_level = level if level is not None else _get_level_from_config()
    logger = logging.getLogger(logger_name)
    logger.setLevel(determined_level)
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(determined_level)
        logger.addHandler(stream_handler)

    log_dir = _get_log_dir_from_env()
    os.makedirs(log_dir, exist_ok=True)

    file_path = os.path.join(log_dir, f"{logger_name}.log")
    if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', None) == os.path.abspath(file_path) for h in logger.handlers):
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(determined_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    today_str = _get_today_str()
    global_log_path = os.path.join(log_dir, f"run_{today_str}.log")
    if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', None) == os.path.abspath(global_log_path) for h in logger.handlers):
        global_file_handler = logging.FileHandler(global_log_path, encoding="utf-8")
        global_file_handler.setLevel(determined_level)
        global_file_handler.setFormatter(formatter)
        logger.addHandler(global_file_handler)

    _loggers[logger_name] = logger
    return logger

def set_global_log_level(level: int) -> None:
    """
    设置所有已创建日志器的日志级别。
    """
    for logger in _loggers.values():
        logger.setLevel(level)

def add_file_handler(name: str, file_path: str, level: int = LOG_LEVEL_INFO, fmt: str = _DEFAULT_FORMAT, datefmt: str = _DEFAULT_DATEFMT) -> None:
    """
    为指定日志器添加文件输出（如需自定义路径）。
    """
    logger = get_logger(name)
    file_handler = logging.FileHandler(file_path, encoding="utf-8")
    file_handler.setLevel(level)
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)