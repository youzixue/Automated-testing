"""
主控入口脚本：CI/CD自动化测试全流程调度
- 环境准备
- 测试执行
- 报告生成
- 报告上传与权限修正
- 邮件通知
"""
from env_setup import prepare_env
from run_tests import run_tests
from generate_report import (
    write_allure_categories, write_allure_environment, write_allure_executor,
    generate_allure_report, upload_report_to_ecs, fix_permissions
)
from utils import get_allure_summary, copy_history_to_results
from notify import send_report_email
import os

def main():
    # 1. 环境准备
    prepare_env()
    copy_history_to_results()
    # 2. 写入Allure环境/分类/执行器信息
    write_allure_categories()
    write_allure_environment()
    write_allure_executor()
    # 3. 执行测试
    test_result = run_tests()
    # 4. 生成Allure报告
    report_success = generate_allure_report()
    # 5. 上传报告与修正权限
    upload_success = False
    if report_success:
        remote_user = os.environ.get("ECS_USER", "root")
        remote_host = os.environ.get("ECS_HOST")
        remote_dir = os.environ.get("ECS_TARGET_DIR", "/usr/share/nginx/html/")
        if remote_host:
            upload_success = upload_report_to_ecs(
                "output/reports/allure-report", remote_user, remote_host, remote_dir
            )
            if upload_success:
                fix_permissions(remote_user, remote_host, remote_dir, nginx_user="nginx")
    # 6. 邮件通知
    summary = get_allure_summary() or {}
    send_report_email(summary, upload_success)

if __name__ == "__main__":
    main()