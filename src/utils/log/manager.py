from __future__ import annotations
import logging
import os
from typing import Optional, Dict
from datetime import datetime

LOG_LEVEL_DEBUG = logging.DEBUG
LOG_LEVEL_INFO = logging.INFO
LOG_LEVEL_WARNING = logging.WARNING
LOG_LEVEL_ERROR = logging.ERROR

_DEFAULT_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
_DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"
_DEFAULT_LOG_DIR = "output/logs"

_loggers: Dict[str, logging.Logger] = {}

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
    level: int = LOG_LEVEL_INFO,
    fmt: str = _DEFAULT_FORMAT,
    datefmt: str = _DEFAULT_DATEFMT,
) -> logging.Logger:
    """
    获取或创建标准化日志器，单例模式，自动支持控制台、分文件和全局聚合日志输出（全局日志按日期命名，带project前缀）。
    日志目录优先读取环境变量LOG_FILE_PATH。
    """
    global _loggers
    logger_name = name or "root"
    if logger_name in _loggers:
        return _loggers[logger_name]

    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    # 控制台输出
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    # 日志目录
    log_dir = _get_log_dir_from_env()
    os.makedirs(log_dir, exist_ok=True)

    # 分文件日志
    file_path = os.path.join(log_dir, f"{logger_name}.log")
    if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', None) == os.path.abspath(file_path) for h in logger.handlers):
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # 全局聚合日志（project_YYYY-MM-DD.log）
    today_str = _get_today_str()
    global_log_path = os.path.join(log_dir, f"run_{today_str}.log")
    if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', None) == os.path.abspath(global_log_path) for h in logger.handlers):
        global_file_handler = logging.FileHandler(global_log_path, encoding="utf-8")
        global_file_handler.setLevel(level)
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