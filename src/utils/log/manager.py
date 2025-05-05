from __future__ import annotations
import logging
import logging.handlers
import os
import queue
import atexit
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
_listener: Optional[logging.handlers.QueueListener] = None # Keep track of the listener

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
        "filename": "app.log",
        "max_size": 10, # MB
        "backup_count": 5
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

def _get_log_dir_from_env() -> str:
    """
    优先从环境变量LOG_FILE_PATH获取日志目录，否则用默认值。
    支持.env、settings.yaml等配置联动。
    """
    log_dir = os.environ.get("LOG_FILE_PATH")
    if log_dir:
        app_env = os.environ.get("APP_ENV", "dev")
        log_dir = log_dir.replace("${APP_ENV}", app_env)
        log_dir = log_dir.replace("$APP_ENV", app_env)
        return log_dir
    # 如果没有环境变量，尝试从配置读取
    config = get_config()
    log_dir_config = config.get('log', {}).get('file', {}).get('path', _DEFAULT_LOG_DIR)
    # 确保目录存在
    abs_log_dir = os.path.abspath(log_dir_config)
    os.makedirs(os.path.dirname(abs_log_dir), exist_ok=True)
    return log_dir_config

def _get_today_str() -> str:
    """获取当天日期字符串，格式为YYYY-MM-DD。"""
    return datetime.now().strftime("%Y-%m-%d")

def get_logger(
    name: Optional[str] = None,
    level: Optional[int] = None,
) -> logging.Logger:
    """
    获取或创建标准化日志器。
    日志级别优先从配置读取。日志记录将通过根记录器的 QueueHandler 处理。
    """
    global _loggers
    logger_name = name or "root"

    if logger_name in _loggers:
        existing_logger = _loggers[logger_name]
        # 如果指定了新级别，则更新
        if level is not None and existing_logger.level != level:
             existing_logger.setLevel(level)
        # 否则，确保其级别与全局配置一致（如果它不是root）
        elif level is None and logger_name != "root":
             current_global_level = _get_level_from_config()
             if existing_logger.level != current_global_level:
                  existing_logger.setLevel(current_global_level)
        return existing_logger

    # 创建新的 logger
    logger = logging.getLogger(logger_name)
    determined_level = level if level is not None else _get_level_from_config()
    logger.setLevel(determined_level)

    # 确保 logger 传播到 root logger (默认行为，显式设置以防万一)
    logger.propagate = True

    # 不再直接添加 handler，所有处理由 QueueListener 负责
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
    # 如果 listener 存在，也更新其处理器的级别（如果需要更细粒度控制）
    # 但通常只控制根 logger 级别就够了

def setup_logging(
    level: Optional[str] = None,
    log_to_file: Optional[bool] = None,
    log_to_console: Optional[bool] = None,
    log_path: Optional[str] = None,
    fmt: str = _DEFAULT_FORMAT,
    datefmt: str = _DEFAULT_DATEFMT
) -> None:
    """
    设置全局日志配置，使用 QueueHandler 和 QueueListener 实现异步日志记录。

    Args:
        level: 日志级别字符串 ("DEBUG", "INFO", "WARNING", "ERROR")。None 则从配置读取。
        log_to_file: 是否输出到文件。None 则从配置读取。
        log_to_console: 是否输出到控制台。None 则从配置读取。
        log_path: 日志文件目录。None 则从环境变量或配置读取。
        fmt: 日志格式。
        datefmt: 日期格式。
    """
    global _listener
    # 如果已经设置过 listener，则直接返回或根据需要更新
    if _listener is not None:
        print("Logging system already initialized.")
        # 可以选择在这里添加更新 listener 配置的逻辑，但通常初始化一次即可
        return

    # --- 获取配置 ---
    config = get_config()
    log_config = config.get('log', {})
    # --- 增加调试日志，打印读取到的 log_config --- 
    try:
        log_config_str = json.dumps(log_config, indent=2)
    except TypeError:
        log_config_str = str(log_config) # 如果无法序列化，直接转字符串
    print(f"[DEBUG] setup_logging: 读取到的 log 配置: \n{log_config_str}")
    # --- 调试日志结束 ---

    final_level_str = level or log_config.get('level', 'INFO')
    final_level_int = _LEVEL_MAP.get(final_level_str.upper(), LOG_LEVEL_INFO)

    # 优先使用传入参数，否则从配置读取
    console_config_value = log_config.get('console', True) # 默认True
    print(f"[DEBUG] setup_logging: 读取到的 console 配置值: {console_config_value} (类型: {type(console_config_value)})")
    if log_to_console is None:
        if isinstance(console_config_value, dict):
            final_log_to_console = console_config_value.get('enabled', True)
        elif isinstance(console_config_value, str):
            final_log_to_console = console_config_value.lower() == 'true'
        elif isinstance(console_config_value, bool):
            final_log_to_console = console_config_value # 直接使用布尔值
        else: # 默认启用
            print("[WARNING] setup_logging: console 配置值类型无法识别，默认启用")
            final_log_to_console = True 
    else:
        final_log_to_console = log_to_console
    print(f"[DEBUG] setup_logging: 最终 console 启用状态: {final_log_to_console}")

    file_config_value = log_config.get('file', True) # 默认True
    print(f"[DEBUG] setup_logging: 读取到的 file 配置值: {file_config_value} (类型: {type(file_config_value)})")
    if log_to_file is None:
        if isinstance(file_config_value, dict):
            final_log_to_file = file_config_value.get('enabled', True)
        elif isinstance(file_config_value, str):
            final_log_to_file = file_config_value.lower() == 'true'
        elif isinstance(file_config_value, bool):
            final_log_to_file = file_config_value # 直接使用布尔值
        else: # 默认启用
            print("[WARNING] setup_logging: file 配置值类型无法识别，默认启用")
            final_log_to_file = True
    else:
        final_log_to_file = log_to_file
    print(f"[DEBUG] setup_logging: 最终 file 启用状态: {final_log_to_file}")

    # log_path 的处理保持不变，因为它本身预期就是字符串路径
    final_log_path = log_path or _get_log_dir_from_env()


    # --- 配置 Queue 和 Handler ---
    log_queue = queue.Queue(-1) # 创建无限大小的队列
    queue_handler = logging.handlers.QueueHandler(log_queue)

    # 获取根 logger，并只添加 QueueHandler
    root_logger = logging.getLogger()
    # 清理可能存在的旧 handler (重要，防止重复添加)
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close() # 关闭旧 handler
    root_logger.addHandler(queue_handler)
    root_logger.setLevel(final_level_int)

    # --- 配置实际处理日志的 Handlers ---
    handlers: List[logging.Handler] = []
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    if final_log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        # 通常让根 logger 控制级别，但如果需要，可以单独设置 handler 级别
        # console_handler.setLevel(final_level_int)
        handlers.append(console_handler)

    if final_log_to_file and final_log_path:
        # 确保日志目录存在
        # 路径可能包含文件名模式，取其目录部分
        log_dir = os.path.dirname(final_log_path) if '.' in os.path.basename(final_log_path) else final_log_path
        os.makedirs(log_dir, exist_ok=True)

        today_str = _get_today_str()
        # 默认使用 run_YYYY-MM-DD.log 作为聚合日志文件名
        file_path = os.path.join(log_dir, f"run_{today_str}.log")
        try:
            # 使用 RotatingFileHandler 或 TimedRotatingFileHandler 更好，但 FileHandler 也可以
            file_handler = logging.FileHandler(file_path, encoding="utf-8", mode='a')
            file_handler.setFormatter(formatter)
            # file_handler.setLevel(final_level_int)
            handlers.append(file_handler)
        except Exception as e:
            print(f"无法创建日志文件处理器 at {file_path}: {e}")

    # --- 创建并启动 Listener ---
    # respect_handler_level=True 意味着如果 handler 上设置了级别，会覆盖根 logger 级别
    # 这里我们没在 handler 上设置级别，所以它会使用 root_logger 的级别
    _listener = logging.handlers.QueueListener(log_queue, *handlers, respect_handler_level=True)
    _listener.start()

    # --- 注册退出处理器 ---
    # 确保 Python 退出时停止 listener，处理剩余日志
    atexit.register(_listener.stop)

    # --- 配置其他库的日志级别（可选） ---
    # 减少 Airtest 和 Poco 的冗余日志
    for noisy_logger_name in ["airtest.core.api", "airtest.core.device", "poco.drivers", "airtest.core.android.adb"]:
        noisy_logger = logging.getLogger(noisy_logger_name)
        noisy_logger.setLevel(logging.ERROR) # <-- Change to ERROR

    # --- 记录配置完成信息 ---
    startup_message = (
        f"异步日志系统已配置: 级别={final_level_str}, "
        f"文件输出={final_log_to_file} (路径模式: {final_log_path}), "
        f"控制台输出={final_log_to_console}"
    )
    root_logger.info(startup_message) # 这条日志会通过队列处理

    # --- 配置 Airtest 日志目录 (如果需要 Airtest 的截图等输出) ---
    from airtest.core.helper import set_logdir
    airtest_log_dir = os.path.join(final_log_path, "airtest_logs") if final_log_path else _DEFAULT_LOG_DIR
    os.makedirs(airtest_log_dir, exist_ok=True)
    set_logdir(airtest_log_dir)
    root_logger.info(f"Airtest 日志目录设置为: {airtest_log_dir}")

# --- 可选：添加一个明确的关闭函数 ---
def shutdown_logging():
    """显式停止日志监听器并关闭 handlers。"""
    global _listener
    if _listener:
        print("Shutting down logging listener...")
        _listener.stop()
        _listener = None
    # 清理 root logger 的 handlers (可选，atexit 也会做)
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        if isinstance(handler, logging.handlers.QueueHandler): # 只移除 QueueHandler
             root_logger.removeHandler(handler)
        # 不要关闭 listener 管理的 handlers，listener.stop() 会处理
    print("Logging shutdown complete.")

# 可以在 pytest_sessionfinish 中调用 shutdown_logging()
# import logging
# def pytest_sessionfinish(session, exitstatus):
#     shutdown_logging()

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
    配置全局日志系统。

    根据提供的配置字典设置日志格式、级别、输出目标（控制台、文件）。
    支持为特定的 logger 设置不同的级别。
    该函数应该在应用程序启动时或测试会话开始时调用一次。

    Args:
        config: 日志配置字典，结构应类似 DEFAULT_LOG_CONFIG。如果为 None，则使用默认配置。
    """
    global _logging_configured
    if _logging_configured:
        # print("Warning: Logging already configured. Skipping reconfiguration.")
        return

    # 合并配置，确保所有键都存在
    effective_config = _merge_configs(DEFAULT_LOG_CONFIG, config or {})
    log_config = effective_config.get('log', effective_config) # 兼容旧的配置结构

    # print(f"[DEBUG] setup_logging: 使用的日志配置: {log_config}")

    # --- 清理现有的 handlers --- #
    # 防止在某些场景（如测试框架多次调用）下重复添加 handlers
    for handler in _root_logger.handlers[:]:
        _root_logger.removeHandler(handler)
        handler.close()

    # --- 设置根 Logger 级别 --- #
    # Determine the final log level (Root logger level)
    # 优先级: 环境变量 > 配置文件 > 默认值
    level_from_env = os.environ.get("LOG_LEVEL")
    level_from_config = log_config.get("level", DEFAULT_LOG_CONFIG["level"]) # 从合并后的配置获取
    
    # 修复 AttributeError: 检查 final_level_str 是否为字符串
    final_level_str = level_from_env or level_from_config
    if not isinstance(final_level_str, str):
        print(f"[ERROR] [Logging Setup] Invalid log level configuration. Expected string but got {type(final_level_str)}: {final_level_str}. Falling back to INFO.")
        final_level_str = "INFO" # Fallback to INFO

    final_level_int = _LEVEL_MAP.get(final_level_str.upper(), LOG_LEVEL_INFO)
    _root_logger.setLevel(final_level_int)
    # print(f"[DEBUG] setup_logging: 根 Logger 级别设置为 {final_level_str} ({final_level_int})")

    # --- 设置日志格式 --- #
    log_format_str = log_config.get("format", DEFAULT_LOG_CONFIG["format"])
    formatter = logging.Formatter(log_format_str)

    # --- 配置控制台 Handler --- #
    console_config = log_config.get("console", DEFAULT_LOG_CONFIG["console"])
    if console_config.get("enabled", DEFAULT_LOG_CONFIG["console"]["enabled"]):
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        # 控制台 handler 通常使用根 logger 的级别，或者可以单独配置
        # console_handler.setLevel(final_level_int) # 通常不需要单独设置，继承 root
        _root_logger.addHandler(console_handler)
        # print(f"[DEBUG] setup_logging: 控制台 Handler 已添加")
    # else:
        # print(f"[DEBUG] setup_logging: 控制台 Handler 已禁用")

    # --- 配置 Rotating File Handler --- #
    file_config = log_config.get("file", DEFAULT_LOG_CONFIG["file"])
    if file_config.get("enabled", DEFAULT_LOG_CONFIG["file"]["enabled"]):
        log_dir_path = file_config.get("path", DEFAULT_LOG_CONFIG["file"]["path"])
        filename = file_config.get("filename", DEFAULT_LOG_CONFIG["file"]["filename"])
        
        # 处理相对路径和绝对路径
        log_dir = Path(log_dir_path)
        if not log_dir.is_absolute():
             # 假设相对路径是相对于项目根目录 (manager.py 向上两级)
             project_root = Path(__file__).parent.parent.parent
             log_dir = project_root / log_dir_path
             # print(f"[DEBUG] setup_logging: 日志文件相对路径转换为: {log_dir}")
        
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file_path = log_dir / filename
            # print(f"[DEBUG] setup_logging: 最终日志文件路径: {log_file_path}")

            max_bytes = int(file_config.get("max_size", DEFAULT_LOG_CONFIG["file"]["max_size"])) * 1024 * 1024
            backup_count = int(file_config.get("backup_count", DEFAULT_LOG_CONFIG["file"]["backup_count"]))
            
            file_handler = logging.handlers.RotatingFileHandler(
                log_file_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            # 文件 handler 通常也使用根 logger 的级别
            # file_handler.setLevel(final_level_int) # 通常不需要单独设置
            _root_logger.addHandler(file_handler)
            # print(f"[DEBUG] setup_logging: 文件 Handler 已添加，路径: {log_file_path}")

        except OSError as e:
            print(f"[ERROR] [Logging Setup] 创建日志目录或文件失败: {e}")
        except Exception as e:
            print(f"[ERROR] [Logging Setup] 配置日志文件处理器时出错: {e}")
    # else:
        # print(f"[DEBUG] setup_logging: 文件 Handler 已禁用")

    # --- 配置特定 Logger 的级别 --- #
    loggers_config = log_config.get("loggers", DEFAULT_LOG_CONFIG["loggers"])
    if isinstance(loggers_config, dict):
        for logger_name, logger_opts in loggers_config.items():
            if isinstance(logger_opts, dict):
                level_str = logger_opts.get("level")
                if level_str and isinstance(level_str, str):
                    level_int = _LEVEL_MAP.get(level_str.upper())
                    if level_int is not None:
                        logging.getLogger(logger_name).setLevel(level_int)
                        # print(f"[DEBUG] setup_logging: Logger '{logger_name}' 级别设置为 {level_str} ({level_int})")
                    else:
                        print(f"[WARNING] [Logging Setup] Logger '{logger_name}' 的配置级别 '{level_str}' 无效")
                # 可以扩展支持 propagate 等其他属性
            else:
                 print(f"[WARNING] [Logging Setup] Logger '{logger_name}' 的配置格式无效 (应为字典)")
    # else:
        # print(f"[DEBUG] setup_logging: 未找到特定 Logger 配置或格式无效")

    _logging_configured = True
    # print("[INFO] [Logging Setup] 日志系统配置完成.")

# --- 方便使用的函数 --- #
def log_exception(logger: logging.Logger, msg: str = "发生未处理的异常", *args, **kwargs):
    """记录异常信息，自动包含 traceback。"""
    logger.exception(msg, *args, **kwargs)