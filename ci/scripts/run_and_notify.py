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
    from ci.scripts.utils import get_allure_summary # 重新导入
except ImportError as e:
    # 在 logger 初始化前可能无法记录，暂时保留 print
    print(f"[ERROR] Failed to import necessary modules: {e}. Ensure the script is run within the project structure or PYTHONPATH is set correctly.")
    sys.exit(1)

# --- 获取日志记录器实例 ---
logger = get_logger(__name__) # 使用项目的 get_logger

def _send_notification():
    """尝试读取摘要并发送邮件通知。"""
    logger.info("准备邮件通知...")

    # 在 CI 通知模式下，尝试从挂载的报告目录读取摘要
    # Jenkinsfile 中将 HOST_ALLURE_REPORT_PATH 挂载到了 /report
    # 并且在调用此脚本前，已将 summary.json 拷贝到 HOST_ALLURE_REPORT_PATH/widgets/ 下
    report_read_dir = "/report" # 容器内路径
    logger.info(f"尝试从挂载的报告目录读取摘要: {report_read_dir}")
    summary_for_email = get_allure_summary(report_dir_base=report_read_dir)

    if not summary_for_email:
        logger.warning(f"未能从 {report_read_dir}/widgets/summary.json 获取有效的摘要。邮件将不包含详细统计信息。")
        # 即使没有摘要，也要发送通知，包含状态和链接
        build_status = os.environ.get("BUILD_STATUS", "UNKNOWN")
        summary_for_email = {
            "status": build_status
            # 不包含 total, passed 等统计键
        }
    else:
         logger.info(f"成功获取摘要信息: {summary_for_email}")
         # 如果成功获取，添加 build_status (如果 notify.py 需要合并处理)
         if "status" not in summary_for_email:
              summary_for_email["status"] = os.environ.get("BUILD_STATUS", "UNKNOWN")


    email_enabled = os.environ.get("EMAIL_ENABLED", "false").lower() == "true"
    if email_enabled:
        logger.info(f"邮件通知已启用。发送邮件...")
        try:
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

    # 在 CI 通知模式下，脚本的退出码不应影响 Jenkins 构建状态
    logger.info("通知脚本执行完毕，退出状态为 0。")
    sys.exit(0)


if __name__ == "__main__":
    main()