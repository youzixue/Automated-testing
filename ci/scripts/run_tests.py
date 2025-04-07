#!/usr/bin/env python3
"""
测试执行脚本，用于运行自动化测试
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行自动化测试")
    parser.add_argument("--env", choices=["dev", "test", "prod"], default="dev",
                      help="要使用的环境配置")
    parser.add_argument("--browser", choices=["chromium", "firefox", "webkit"], default=None,
                      help="使用的浏览器")
    parser.add_argument("--headless", action="store_true",
                      help="是否使用无头模式")
    parser.add_argument("--parallel", type=int, default=1,
                      help="并行执行的进程数")
    parser.add_argument("--reruns", type=int, default=0,
                      help="失败重试次数")
    parser.add_argument("--report", action="store_true",
                      help="生成Allure报告")
    parser.add_argument("--tags", type=str, default="",
                      help="要运行的标记，例如: 'web and login'")
    parser.add_argument("--tests", type=str, default="",
                      help="要运行的测试路径，例如: tests/web/login/")
    args = parser.parse_args()
    
    # 获取项目根目录
    root_dir = Path(__file__).parent.parent.absolute()
    os.chdir(root_dir)
    
    # 设置环境变量
    os.environ["ENV"] = args.env
    
    # 构建pytest命令
    pytest_args = ["pytest"]
    
    # 添加标记
    if args.tags:
        pytest_args.extend(["-m", args.tags])
    
    # 添加并行执行参数
    if args.parallel > 1:
        pytest_args.extend(["-n", str(args.parallel)])
    
    # 添加失败重试参数
    if args.reruns > 0:
        pytest_args.extend(["--reruns", str(args.reruns)])
    
    # 添加报告参数
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if args.report:
        report_dir = os.path.join(root_dir, "reports", "allure", timestamp)
        os.makedirs(report_dir, exist_ok=True)
        pytest_args.extend(["--alluredir", report_dir])
    
    # 添加指定的测试路径
    if args.tests:
        pytest_args.append(args.tests)
    
    # 添加浏览器和无头模式参数
    if args.browser:
        os.environ["BROWSER"] = args.browser
    if args.headless:
        os.environ["HEADLESS"] = "true"
    
    # 运行测试
    print(f"开始执行测试 (环境: {args.env})")
    print(f"命令: {' '.join(pytest_args)}")
    
    start_time = time.time()
    result = subprocess.run(pytest_args, check=False)
    end_time = time.time()
    
    # 输出执行结果
    duration = end_time - start_time
    print(f"测试执行完成，耗时: {duration:.2f}秒")
    print(f"退出码: {result.returncode}")
    
    # 如果生成了报告，显示报告路径
    if args.report:
        print(f"Allure报告已生成: {report_dir}")
        print("运行以下命令查看报告:")
        print(f"  allure serve {report_dir}")
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main()) 