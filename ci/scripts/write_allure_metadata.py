"""
为 Allure 报告生成元数据文件：
- environment.properties: 包含测试环境信息
- executor.json: 包含构建执行器信息（如 Jenkins 构建号、URL）
- categories.json: 定义测试结果分类规则
"""

import os
import json
import sys
import platform # 导入 platform 获取系统信息
from datetime import datetime # 导入 datetime 模块

def get_os_info():
    """获取操作系统信息"""
    try:
        if platform.system() == "Windows":
            if hasattr(sys, 'getwindowsversion'):
                win_version = sys.getwindowsversion()
                build_number = win_version.build
                if build_number >= 22000:
                    return f"Windows 11 ({platform.version()})"
                else:
                    return f"Windows 10 ({platform.version()})"
            else:
                return f"Windows {platform.release()} ({platform.version()})"
        elif platform.system() == "Darwin":
            return f"macOS {platform.release()} ({platform.mac_ver()[0]})"
        else:
            # 尝试获取更友好的Linux发行版名称
            try:
                with open('/etc/os-release') as f:
                    for line in f:
                        if line.startswith('PRETTY_NAME='):
                            return line.split('=')[1].strip().strip('"')
            except FileNotFoundError:
                 pass # 如果文件不存在，回退到基本信息
            return f"{platform.system()} {platform.release()}"
    except Exception:
        return "N/A"

def write_allure_environment(results_dir, app_env):
    """写入 environment.properties 文件，包含环境信息。"""
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    os_info = get_os_info()

    environment = {
        'APP_ENV': app_env,
        'PYTHON_VERSION': python_version,
        'OS': os_info,
        'TEST_FRAMEWORK': 'pytest',
        'UI_AUTOMATION': 'Playwright',
        'API_AUTOMATION': 'httpx',
        'REPORT_TOOL': 'Allure 2.x'
    }
    env_file_path = os.path.join(results_dir, 'environment.properties')
    try:
        # 确保使用 UTF-8 编码写入
        with open(env_file_path, 'w', encoding='utf-8') as f:
            for key, value in environment.items():
                # 替换换行符，避免多行值破坏格式
                value_str = str(value).replace('\n', ' ').replace('\r', '')
                f.write(f'{key}={value_str}\n')
        print(f'环境信息写入成功: {env_file_path}')
    except IOError as e:
        print(f'错误：无法写入环境信息到 {env_file_path}: {e}', file=sys.stderr)

def write_allure_executor(results_dir):
    """写入 executor.json 文件，包含构建信息。"""
    # 从环境变量获取构建信息
    build_number = os.environ.get('BUILD_NUMBER', 'N/A') # 仍然获取构建号，可用于其他字段
    job_name = os.environ.get('JOB_NAME', 'Local Run')
    build_url = os.environ.get('BUILD_URL', '#')
    # 尝试获取 Jenkinsfile 中定义的公共报告 URL
    # 如果 Jenkinsfile 没有设置 ALLURE_PUBLIC_URL，则回退到 build_url
    report_url = os.environ.get('ALLURE_PUBLIC_URL', build_url)

    # 获取当前时间
    now = datetime.now()
    # 格式化为 MMDDHHMM (用于 buildOrder 和趋势图)
    timestamp_build_order = now.strftime('%m%d%H%M')
    # 修改：格式化为 YYYY-MM-DD HH:MM (用于 buildName 显示)
    timestamp_build_name = now.strftime('%Y-%m-%d %H:%M')

    executor_info = {
        "name": "Jenkins", # 执行器名称
        "type": "jenkins", # 执行器类型
        "url": os.environ.get('JENKINS_URL', '#'), # Jenkins 主 URL
        "buildOrder": timestamp_build_order, # <-- 保持 MMDDHHMM 用于趋势图
        "buildName": timestamp_build_name,  # <-- 修改为 YYYY-MM-DD HH:MM 用于显示
        "buildUrl": build_url, # Jenkins 构建 URL (链接保持不变)
        "reportName": "自动化测试报告", # Allure 报告名称
        "reportUrl": report_url # Allure 报告的公共访问 URL
    }

    executor_file = os.path.join(results_dir, 'executor.json')
    try:
        with open(executor_file, 'w', encoding='utf-8') as f:
            json.dump(executor_info, f, ensure_ascii=False, indent=4)
        print(f"执行器信息写入成功: {executor_file}")
    except IOError as e:
        print(f"错误：无法写入执行器信息到 {executor_file}: {e}", file=sys.stderr)

def write_allure_categories(results_dir):
    """写入 categories.json 文件，定义结果分类规则。"""
    categories = [
        {'name': '断言失败', 'matchedStatuses': ['failed'], 'messageRegex': '.*AssertionError.*'},
        {'name': '环境或元素问题', 'matchedStatuses': ['broken', 'failed'], 'messageRegex': '.*(TimeoutError|NoSuchElementError|ElementNotInteractableError|WebDriverException|ConnectionError).*'},
        {'name': '已知产品缺陷', 'matchedStatuses': ['failed'], 'messageRegex': '.*BUG_ID:.*'}, # 示例：通过特定标记区分已知缺陷
        {'name': '跳过测试', 'matchedStatuses': ['skipped']}
    ]
    cat_file_path = os.path.join(results_dir, 'categories.json')
    try:
        with open(cat_file_path, 'w', encoding='utf-8') as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)
        print(f'分类信息写入成功: {cat_file_path}')
    except IOError as e:
        print(f'错误：无法写入分类信息到 {cat_file_path}: {e}', file=sys.stderr)


def main():
    """主函数：解析参数并调用写入函数。"""
    if len(sys.argv) < 2:
        print("错误：需要提供 Allure 结果目录作为第一个参数！", file=sys.stderr)
        sys.exit(1)
    allure_results_dir = sys.argv[1]

    app_env = os.environ.get('APP_ENV', 'unknown')

    print(f'为Allure报告生成元数据信息')
    print(f'环境: {app_env}')
    print(f'结果目录: {allure_results_dir}')

    try:
        os.makedirs(allure_results_dir, exist_ok=True)
    except OSError as e:
        print(f'错误：创建结果目录失败: {allure_results_dir}: {e}', file=sys.stderr)
        sys.exit(1) # 创建失败则退出

    # 调用各个写入函数
    write_allure_environment(allure_results_dir, app_env)
    write_allure_executor(allure_results_dir)
    write_allure_categories(allure_results_dir)

    print('元数据写入脚本执行完毕')

if __name__ == "__main__":
    main()