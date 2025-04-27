#!/usr/bin/env python
# run_and_notify.py
"""
CI/CD 通知脚本入口 (Jenkins Post-Build专用)

负责根据环境变量组装信息并调用邮件发送模块。
假定在 Jenkins Pipeline 的 Post-Build 阶段被调用，
且测试执行和 Allure 报告生成已由 Pipeline 其他阶段或插件完成。
"""
import os
import sys
import time

# --- 将项目根目录添加到 sys.path ---
# 确保 notify 模块能被正确导入
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- 导入项目模块 ---
try:
    # 只需要导入日志和通知模块
    from src.utils.log.manager import get_logger
    from ci.scripts.notify import send_report_email # 直接从 ci.scripts 导入
except ImportError as e:
    # 在 logger 初始化前可能无法记录，暂时保留 print
    print(f"[ERROR] Failed to import necessary modules: {e}. Ensure the script is run within the project structure or PYTHONPATH is set correctly.")
    sys.exit(1)

# --- 获取日志记录器实例 ---
logger = get_logger(__name__) # 使用项目的 get_logger

def _send_notification():
    """组装参数并发送邮件通知。"""
    logger.info("准备邮件通知...")

    # 在 CI 通知模式下，我们不尝试读取本地摘要文件。
    # 邮件内容将依赖环境变量中的构建状态和报告URL。
    # 创建一个空的 summary 或只包含状态信息的 dict 传递给发送函数。
    build_status = os.environ.get("BUILD_STATUS", "UNKNOWN") # 从 Jenkinsfile 获取
    summary_for_email = {
        "status": build_status, # 传递构建状态
        # 不包含 total, passed, failed 等统计信息
    }
    logger.info(f"CI 通知模式: 使用构建状态 '{build_status}' 进行通知。")

    email_enabled = os.environ.get("EMAIL_ENABLED", "false").lower() == "true"
    if email_enabled:
        logger.info(f"邮件通知已启用。发送邮件...")
        # 注意：send_report_email 需要能够处理只包含 status 的 summary
        try:
            # upload_successful 参数已移除
            send_report_email(summary_for_email)
        except Exception as e:
             logger.error(f"调用 send_report_email 时出错: {e}", exc_info=True)
    else:
        logger.info("邮件通知已禁用 (EMAIL_ENABLED != true)。")


def main():
    """主执行函数，仅负责触发邮件通知。"""
    logger.info("启动 run_and_notify 通知脚本...")

    # --- 直接发送通知 ---
    _send_notification()

    # 不再需要计算和记录时长
    # end_time = time.time()
    # total_duration = format_duration(int((end_time - start_time) * 1000))
    # logger.info(f"run_and_notify 通知脚本在 {total_duration} 内完成。")

    # 在 CI 通知模式下，脚本的退出码不应影响 Jenkins 构建状态
    logger.info("通知脚本执行完毕，退出状态为 0。")
    sys.exit(0)


if __name__ == "__main__":
    main()