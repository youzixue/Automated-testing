#!/usr/bin/env python
# run_and_notify.py
"""
主控入口脚本：CI/CD自动化测试全流程调度
- 环境准备
- 测试执行
- 报告生成
- 报告上传与权限修正
- 邮件通知
"""
import os
import sys
import json
import subprocess
import time
from env_setup import prepare_env
from run_tests import run_tests
from generate_report import (
    write_allure_categories, write_allure_environment, write_allure_executor,
    generate_allure_report, upload_report_to_ecs, fix_permissions
)
from utils import get_allure_summary, copy_history_to_results
from notify import send_report_email

# 将项目根目录添加到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

def fix_local_permissions(local_report_dir, nginx_user="nginx"):
    """本地修正Allure报告目录权限"""
    try:
        subprocess.run([
            "chown", "-R", f"{nginx_user}:{nginx_user}", local_report_dir
        ], check=True)
        subprocess.run([
            "find", local_report_dir, "-type", "d", "-exec", "chmod", "755", "{}", "+"
        ], check=True)
        subprocess.run([
            "find", local_report_dir, "-type", "f", "-exec", "chmod", "644", "{}", "+"
        ], check=True)
        print("[INFO] 本地Allure报告权限修正成功")
        return True
    except Exception as e:
        print(f"[WARNING] 本地Allure报告权限修正失败: {e}")
        return False

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
    # 5. 上传报告与修正权限（本地/CI自动切换）
    upload_success = False
    upload_report = os.environ.get("UPLOAD_REPORT", "false").lower() == "true"
    local_report_dir = "output/reports/allure-report"
    if report_success:
        if upload_report:
            # 本地开发：上传到远程Web服务
            remote_user = os.environ.get("ECS_USER", "root")
            remote_host = os.environ.get("ECS_HOST")
            remote_dir = os.environ.get("ECS_TARGET_DIR", "/usr/share/nginx/html/")
            if remote_host:
                upload_success = upload_report_to_ecs(
                    local_report_dir, remote_user, remote_host, remote_dir
                )
                if upload_success:
                    fix_permissions(remote_user, remote_host, remote_dir, nginx_user="nginx")
        elif os.environ.get("CI", "false").lower() == "true":
            # CI环境：修正本地权限（非本地开发环境）
            nginx_user = os.environ.get("WEB_SERVER_USER", "nginx")
            upload_success = fix_local_permissions(local_report_dir, nginx_user=nginx_user)
        else:
            # 本地开发环境：跳过权限修正
            print("[INFO] 本地开发环境，跳过权限修正")
            upload_success = True
    # 6. 邮件通知
    summary = get_allure_summary() or {}
    email_enabled = os.environ.get("EMAIL_ENABLED", "false").lower() == "true"
    if email_enabled:
        send_report_email(summary, upload_success)
    else:
        print("[INFO] 邮件通知已关闭（EMAIL_ENABLED!=true）")

if __name__ == "__main__":
    main()