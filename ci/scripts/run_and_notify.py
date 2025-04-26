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
    # 检查是否跳过报告生成和通知
    skip_report = os.environ.get('SKIP_REPORT', 'false').lower() == 'true'
    skip_notify = os.environ.get('SKIP_NOTIFY', 'false').lower() == 'true'
    
    # 1. 环境准备
    prepare_env()
    
    if not skip_report:
        copy_history_to_results()
        # 2. 写入Allure环境/分类/执行器信息
        write_allure_categories()
        write_allure_environment()
        write_allure_executor()
    
    # 3. 执行测试
    # 检查是否指定了测试平台
    platform = os.environ.get('TEST_PLATFORM')
    if platform:
        print(f"[INFO] 从环境变量检测到测试平台: {platform}")
        # 修改 run_tests 的调用，如果 run_tests 函数支持平台参数，则传入
        test_result = run_tests_with_platform(platform)
    else:
        # 使用原始调用
        test_result = run_tests()
    
    if skip_report:
        print("[INFO] 已完成测试执行，跳过报告生成和通知")
        return
    
    # 4. 生成Allure报告
    report_success = generate_allure_report()
    
    # 5. 上传报告与修正权限（本地/CI自动切换）
    upload_success = False
    upload_report = os.environ.get("UPLOAD_REPORT", "false").lower() == "true"
    local_report_dir = os.environ.get("ALLURE_REPORT_DIR", "output/reports/allure-report")
    
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
            # 检查是否在Docker中运行
            in_docker = os.path.exists('/.dockerenv') or os.environ.get('DOCKER_CONTAINER', '') == 'true'
            if in_docker and not upload_report:
                # Docker环境且不上传报告：修正本地权限
                print("[INFO] 检测到Docker环境，修正报告目录权限")
                nginx_user = os.environ.get("WEB_SERVER_USER", "nginx")
                upload_success = fix_local_permissions(local_report_dir, nginx_user=nginx_user)
            else:
                # 本地开发环境：跳过权限修正
                print("[INFO] 本地开发环境，跳过权限修正")
                upload_success = True
    
    # 6. 邮件通知
    if not skip_notify:
        summary = get_allure_summary() or {}
        email_enabled = os.environ.get("EMAIL_ENABLED", "false").lower() == "true"
        if email_enabled:
            send_report_email(summary, upload_success)
        else:
            print("[INFO] 邮件通知已关闭（EMAIL_ENABLED!=true）")
    else:
        print("[INFO] 跳过邮件通知")

def run_tests_with_platform(platform):
    """
    根据指定的平台执行测试
    
    Args:
        platform: 测试平台名称 (web, api, app, wechat)
        
    Returns:
        bool: 测试是否成功
    """
    print(f"[INFO] 执行特定平台测试: {platform}")
    
    # 构建pytest命令
    cmd = ["pytest", f"tests/{platform}"]
    
    # 添加并行参数
    parallel = os.environ.get("PYTEST_PARALLEL", "auto")
    if parallel and parallel != "0":
        cmd.extend(["-n", parallel])
    
    # 添加重试参数
    reruns = os.environ.get("PYTEST_RERUNS", "2")
    if reruns and int(reruns) > 0:
        cmd.extend(["--reruns", reruns])
    
    # 添加详细输出参数
    cmd.append("-v")
    
    # 添加Allure结果目录
    allure_dir = os.environ.get("ALLUREDIR", "output/allure-results")
    cmd.extend(["--alluredir", allure_dir])
    
    # 执行命令
    print(f"[INFO] 执行命令: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd)
        success = result.returncode == 0
        
        if success:
            print(f"[INFO] {platform}测试执行成功")
        else:
            print(f"[WARNING] {platform}测试执行完成，但存在失败用例 (返回码: {result.returncode})")
        
        return success
    except Exception as e:
        print(f"[ERROR] 执行测试时发生错误: {e}")
        return False

if __name__ == "__main__":
    main()