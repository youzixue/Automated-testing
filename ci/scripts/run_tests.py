"""
测试执行工具：
- 负责pytest并发执行和重试
- 返回退出码，供主控流程判断
"""
import subprocess

def run_tests():
    """执行pytest并返回退出码"""
    result = subprocess.run([
        "pytest", "-n", "auto", "--reruns", "2", "--alluredir=output/reports/allure-results"
    ], check=False)
    return result.returncode
