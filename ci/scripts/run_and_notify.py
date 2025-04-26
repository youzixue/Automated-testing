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
    skip_report_generation = os.environ.get('SKIP_REPORT', 'false').lower() == 'true'
    skip_notify = os.environ.get('SKIP_NOTIFY', 'false').lower() == 'true'
    
    # 1. 环境准备
    prepare_env()
    
    # 决定是否应该运行测试 (只有在提供了平台且不跳过报告生成时)
    platform = os.environ.get('TEST_PLATFORM')
    should_run_tests = platform and not skip_report_generation
    
    # 2. 执行测试 (如果需要)
    test_result = True # 假设成功，除非测试运行并失败
    if should_run_tests:
        print(f"[INFO] 从环境变量检测到测试平台: {platform}")
        test_result = run_tests_with_platform(platform)
    else:
        print("[INFO] 跳过测试执行 (TEST_PLATFORM 未设置或 SKIP_REPORT=true)")

    # 3. 报告相关操作 (仅在不跳过报告生成时)
    report_success = False
    upload_success = False
    if not skip_report_generation:
        print("[INFO] 开始执行报告相关操作...")
        # a. 复制历史记录和写入元数据 (在生成报告前)
        copy_history_to_results()
        write_allure_categories()
        write_allure_environment()
        write_allure_executor()
        
        # b. 生成Allure报告
        report_success = generate_allure_report()
        
        # c. 上传报告与修正权限
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
        # 如果报告生成成功，就认为上传/权限修正是成功的（或根据实际情况设置upload_success）
        upload_success = report_success
    else:
        print("[INFO] 跳过报告生成、上传和权限修正。")
        # 当跳过报告时，根据需要决定 upload_success 的状态
        upload_success = False # 或者 True，取决于邮件内容需要如何展示

    # 4. 邮件通知 (除非显式跳过)
    if not skip_notify:
        print("[INFO] 准备发送邮件通知...")
        # 如果报告未生成，get_allure_summary 可能失败或返回空
        summary = {}
        if report_success:
            summary = get_allure_summary() or {}
            print(f"[INFO] 获取到报告摘要: {summary}")
        else:
            print("[WARNING] 报告未生成或生成失败，无法获取详细摘要。")
            # 可以创建一个默认摘要
            summary = {"total": "N/A", "passed": "N/A", "failed": "N/A", "broken": "N/A", "skipped": "N/A", "unknown": "N/A", "duration": "N/A"}
            if not test_result:
                 summary["status"] = "测试执行失败" # 添加一个状态
            elif not should_run_tests:
                 summary["status"] = "测试未执行" 
                 
        email_enabled = os.environ.get("EMAIL_ENABLED", "false").lower() == "true"
        if email_enabled:
            print("[INFO] 调用邮件发送函数...")
            # 注意：send_report_email 需要能处理 summary 为空或默认值的情况
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