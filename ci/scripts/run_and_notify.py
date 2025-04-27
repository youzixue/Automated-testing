#!/usr/bin/env python
# run_and_notify.py
"""
主控入口脚本：CI/CD自动化测试全流程调度

负责协调环境准备、测试执行、报告生成、上传与权限修正、邮件通知等步骤。
通过环境变量控制各步骤的执行。
"""
import os
import sys
import json
import subprocess
import time
import logging # 保留导入，因为 get_logger 可能需要它或配置它

# --- 日志配置 ---
# logging.basicConfig(
#     level=logging.INFO,
#     format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
#     datefmt='%Y-%m-%d %H:%M:%S'
# ) # 注释掉，因为 get_logger 会处理


# --- 将项目根目录添加到 sys.path ---
# 确保本地导入在脚本从不同位置运行时能正常工作。
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if project_root not in sys.path:
    # 使用 get_logger 前可能需要先配置基础日志，如果 get_logger 内部没处理
    # 但通常 get_logger 应该能处理，先尝试直接用
    # logging.info(f"Added project root to sys.path: {project_root}") # 改用 logger
    sys.path.insert(0, project_root)

# --- 导入项目模块 ---
# 这些导入依赖于项目根目录在 sys.path 中
try:
    from src.utils.log.manager import get_logger # 使用项目标准日志工具
    from env_setup import prepare_env
    from run_tests import run_tests
    from generate_report import (
        write_allure_categories, write_allure_environment, write_allure_executor,
        generate_allure_report, upload_report_to_ecs, fix_permissions
    )
    from utils import get_allure_summary, copy_history_to_results
    from notify import send_report_email
except ImportError as e:
    # 在 logger 初始化前可能无法记录，暂时保留 print
    print(f"[ERROR] Failed to import necessary modules: {e}. Ensure the script is run within the project structure or PYTHONPATH is set correctly.")
    sys.exit(1)

# --- 获取日志记录器实例 ---
logger = get_logger(__name__) # 使用项目的 get_logger
logger.debug(f"项目根目录已添加到 sys.path: {project_root}") # 在获取 logger 后记录

def format_duration(duration_ms: int) -> str:
    """将毫秒持续时间转换为更易读的 'Xm Ys Zms' 格式字符串。

    Args:
        duration_ms: 持续时间（毫秒）。

    Returns:
        格式化后的持续时间字符串，如果输入为负数则返回 "N/A"。
    """
    if duration_ms < 0:
        return "N/A"
    seconds = duration_ms // 1000
    milliseconds = duration_ms % 1000
    minutes = seconds // 60
    seconds %= 60

    parts = []
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0:
        parts.append(f"{seconds}s")
    # 如果分钟和秒都为零，或者毫秒数大于0，则总是显示毫秒
    if milliseconds > 0 or not parts:
        parts.append(f"{milliseconds}ms")

    return " ".join(parts) if parts else "0ms"


def fix_local_permissions(local_report_dir: str, nginx_user: str = "nginx") -> bool:
    """在本地（Linux/MacOS）修正Allure报告目录及其内容的权限。

    Args:
        local_report_dir: 本地Allure报告目录的路径。
        nginx_user: Web服务器运行的用户（用于chown）。

    Returns:
        如果权限修正成功或不需要（非Linux环境），则返回True；否则返回False。

    Raises:
        FileNotFoundError: 如果指定的目录不存在（由subprocess.run内部触发）。
        PermissionError: 如果当前用户没有足够权限执行chown/chmod（由subprocess.run内部触发）。
    """
    logger.info(f"尝试修正本地目录权限: {local_report_dir}")
    try:
        if sys.platform.startswith('linux') or sys.platform.startswith('darwin'):
            # 修改所有权
            subprocess.run(
                ["chown", "-R", f"{nginx_user}:{nginx_user}", local_report_dir],
                check=True, capture_output=True, text=True
            )
            # 设置目录权限
            subprocess.run(
                ["find", local_report_dir, "-type", "d", "-exec", "chmod", "755", "{}", "+"],
                check=True, capture_output=True, text=True
            )
            # 设置文件权限
            subprocess.run(
                ["find", local_report_dir, "-type", "f", "-exec", "chmod", "644", "{}", "+"],
                check=True, capture_output=True, text=True
            )
            logger.info(f"本地权限成功修正于 {local_report_dir} (Linux/MacOS)")
            return True
        else:
            logger.info("检测到非Linux/MacOS环境，跳过本地权限修正。")
            return True # 非Linux/MacOS视为成功，因为无需操作
    except subprocess.CalledProcessError as e:
        logger.warning(f"修正本地权限失败于 {local_report_dir} (命令失败: {e.cmd})", exc_info=False)
        logger.warning(f"命令标准错误输出: {e.stderr.strip()}") # 记录 stderr 以便调试
        return False
    except FileNotFoundError:
        logger.error(f"修正本地权限失败: 目录 {local_report_dir} 未找到", exc_info=False)
        return False
    except PermissionError:
         logger.error(f"修正本地权限失败: 权限不足。请使用足够权限运行脚本。", exc_info=False)
         return False
    except Exception as e:
        # 捕获其他潜在错误 (例如，无效的 nginx_user)
        logger.error(f"本地权限修正过程中发生意外错误于 {local_report_dir}", exc_info=True)
        return False


def _execute_pre_run_steps(skip_report_generation: bool):
    """执行测试运行或报告生成之前的准备步骤。"""
    logger.info("执行测试运行/报告生成前的准备步骤...")
    prepare_env()
    if not skip_report_generation:
        logger.info("复制 Allure 历史记录并写入元数据...")
        copy_history_to_results()
        write_allure_categories()
        write_allure_environment()
        write_allure_executor()
    else:
        logger.info("由于跳过报告生成，故跳过写入 Allure 元数据。")

def _execute_tests() -> bool:
    """执行自动化测试并返回是否成功。"""
    logger.info("执行测试...")
    exit_code = run_tests() # 获取 pytest 的退出码
    if exit_code != 0:      # 检查退出码是否不为 0
        logger.error(f"测试执行失败！(Pytest 退出码: {exit_code})")
        return False        # 返回 False 表示失败
    else:
        logger.info(f"测试执行成功。(Pytest 退出码: {exit_code})")
        return True         # 返回 True 表示成功

def _generate_report() -> bool:
    """生成 Allure 报告。"""
    logger.info("生成 Allure 报告...")
    report_success = generate_allure_report()
    if not report_success:
        logger.error("Allure 报告生成失败！")
    else:
        logger.info("Allure 报告生成成功。")
    return report_success

def _handle_report_deployment(report_generated_successfully: bool) -> bool:
    """处理报告上传（如果配置）和/或本地权限修复（CI环境）。"""
    logger.info("执行报告生成后的步骤 (上传/权限修正)...")
    deployment_successful = report_generated_successfully # 初始假设部署成功取决于报告生成成功
    upload_report_flag = os.environ.get("UPLOAD_REPORT", "false").lower() == "true"
    local_report_dir_relative = "output/reports/allure-report"
    is_ci = os.environ.get("CI", "false").lower() == "true"

    if upload_report_flag:
        logger.info("UPLOAD_REPORT 设置为 true, 尝试远程上传...")
        remote_user = os.environ.get("ECS_USER", "root")
        remote_host = os.environ.get("ECS_HOST")
        remote_dir_base = os.environ.get("ECS_TARGET_DIR", "/usr/share/nginx/html/")

        if remote_host:
            upload_result = upload_report_to_ecs(
                local_report_dir_relative, remote_user, remote_host, remote_dir_base
            )
            deployment_successful = upload_result # 部署成功现在取决于上传结果

            if upload_result:
                logger.info(f"尝试在远程主机 {remote_host} 的基础目录 {remote_dir_base} 内修正权限")
                fix_permissions(remote_user, remote_host, remote_dir_base, nginx_user="nginx")
            else:
                 logger.error("远程报告上传失败。") # 记录具体的失败信息
        else:
            logger.warning("UPLOAD_REPORT 设置为 true, 但未设置 ECS_HOST。跳过远程上传。")
            deployment_successful = False # 没有主机无法成功上传

    elif is_ci:
        logger.info("检测到 CI 环境 (且不上传), 尝试修正本地权限...")
        nginx_user = os.environ.get("WEB_SERVER_USER", "nginx")
        deployment_successful = fix_local_permissions(local_report_dir_relative, nginx_user=nginx_user)
        if not deployment_successful:
             logger.error("在 CI 环境中修正本地权限失败。")

    else:
        logger.info("本地环境且未设置上传标志，跳过权限修正。")
        deployment_successful = True # 无需操作，视为成功

    return deployment_successful

def _send_notification(upload_successful: bool):
    """获取摘要并发送邮件通知。"""
    logger.info("准备邮件通知...")
    report_read_dir = "output/reports/allure-report" # 本地运行的默认路径
    is_ci = os.environ.get("CI", "false").lower() == "true"
    skip_report_generation = os.environ.get('SKIP_REPORT_GENERATION', 'false').lower() == 'true'

    # 在 CI 的通知阶段 (跳过了报告生成), 从挂载的目录读取
    if is_ci and skip_report_generation:
        report_read_dir = os.environ.get("ALLURE_REPORT_DIR", "/report") # 默认挂载路径
        logger.info(f"CI 通知模式: 从挂载的报告目录读取摘要: {report_read_dir}")
    else:
        logger.info(f"从本地生成的目录读取摘要: {report_read_dir}")

    summary = get_allure_summary(report_dir_base=report_read_dir)

    if not summary:
        logger.warning(f"未能从 {report_read_dir} 获取有效的摘要。使用默认零值。")
        summary = {
            "total": 0, "passed": 0, "failed": 0, "broken": 0,
            "skipped": 0, "unknown": 0, "duration": "N/A",
            "status": "摘要获取失败"
        }
    else:
        # 确保成功获取摘要时不包含 status 字段
        summary.pop("status", None)
        logger.info(f"获取到的摘要: {summary}")

    email_enabled = os.environ.get("EMAIL_ENABLED", "false").lower() == "true"
    if email_enabled:
        logger.info(f"邮件通知已启用。发送邮件 (上传/部署成功: {upload_successful})...")
        send_report_email(summary, upload_successful)
    else:
        logger.info("邮件通知已禁用 (EMAIL_ENABLED != true)。")


def main():
    """主执行函数，协调测试和报告流程。"""
    start_time = time.time()
    logger.info("启动 run_and_notify 进程...")

    # --- 从环境变量读取配置 ---
    skip_test_execution = os.environ.get('SKIP_TEST_EXECUTION', 'false').lower() == 'true'
    skip_report_generation = os.environ.get('SKIP_REPORT_GENERATION', 'false').lower() == 'true'
    logger.info(f"配置: 跳过测试={skip_test_execution}, 跳过报告生成={skip_report_generation}")

    test_run_successful = True # 初始假设成功
    report_generation_successful = False
    deployment_successful = False # 涵盖上传/权限修正步骤

    # --- 步骤 1: 运行前/报告前准备 --- (Conditional)
    if not skip_test_execution or not skip_report_generation:
        _execute_pre_run_steps(skip_report_generation)
    else:
        logger.info("跳过运行前/报告前准备步骤。")

    # --- 步骤 2: 执行测试 --- (Conditional)
    if not skip_test_execution:
        test_run_successful = _execute_tests() # 正确接收 True/False
    else:
        logger.info("跳过测试执行 (SKIP_TEST_EXECUTION=true)。")
        test_run_successful = True # 如果跳过，则认为是成功的

    # --- 步骤 3: 生成报告 --- (Conditional)
    # 如果测试执行失败，可以选择跳过报告生成或继续生成包含失败信息的报告
    # 当前逻辑：无论测试是否成功，只要不跳过就生成报告
    if not skip_report_generation:
        # 可以在这里添加逻辑：如果 test_run_successful 为 False，是否仍要生成报告？
        # if not test_run_successful:
        #     logger.warning("测试执行失败，但仍尝试生成报告...")
        report_generation_successful = _generate_report()
        # 如果报告生成成功，才进行部署/权限处理
        if report_generation_successful:
            # --- 步骤 4: 处理报告部署/权限 --- (Conditional on Generation)
            deployment_successful = _handle_report_deployment(report_generation_successful)
        else:
            deployment_successful = False # 如果生成失败，部署也隐式失败
    else:
        logger.info("跳过 Allure 报告生成。")
        # 如果跳过生成，部署状态取决于测试是否上传了已存在的报告
        # 这里的逻辑可能需要根据具体 CI 流程调整
        # 暂时假设跳过生成时部署状态与测试成功与否无关，依赖后续通知步骤判断
        report_generation_successful = True 
        deployment_successful = True 

    # --- 步骤 5: 发送通知 ---
    # 通知应能反映测试是否运行、报告是否生成、部署是否成功
    # 当前 _send_notification 只接收 deployment_successful
    # 可能需要传递 test_run_successful 和 report_generation_successful 给通知函数
    _send_notification(deployment_successful)

    end_time = time.time()
    total_duration = format_duration(int((end_time - start_time) * 1000))
    logger.info(f"run_and_notify 进程在 {total_duration} 内完成。")

    # 最终退出状态应反映整体流程是否成功
    # 例如，如果测试失败或报告生成失败或部署失败，则应以非零状态退出
    if not test_run_successful or not report_generation_successful or not deployment_successful:
        logger.error("run_and_notify 进程检测到错误。")
        sys.exit(1) # 以非零状态退出表示失败
    else:
        logger.info("run_and_notify 进程成功完成。")
        sys.exit(0) # 以零状态退出表示成功


if __name__ == "__main__":
    main()