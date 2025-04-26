import os
import json
import datetime
import sys
import platform # 导入 platform 获取系统信息

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

def main():
    # Get target directory from command line argument
    if len(sys.argv) < 2:
        print("错误：需要提供 Allure 结果目录作为参数！")
        sys.exit(1)
    allure_results_dir = sys.argv[1]

    # 从容器环境变量获取 APP_ENV
    app_env = os.environ.get('APP_ENV', 'unknown')
    # 不再需要 Jenkins 构建相关的环境变量

    print(f'为Allure报告生成元数据信息')
    print(f'环境: {app_env}')
    print(f'结果目录: {allure_results_dir}')

    try:
        os.makedirs(allure_results_dir, exist_ok=True)
    except Exception as e:
        print(f'创建结果目录失败: {e}')
        sys.exit(1) # 创建失败则退出

    # environment.properties - 构建期望的环境信息
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    os_info = get_os_info()

    environment = {
        'APP_ENV': app_env,
        'PYTHON_VERSION': python_version,
        'OS': os_info,
        'TEST_FRAMEWORK': 'pytest',
        'UI_AUTOMATION': 'Playwright',
        'API_AUTOMATION': 'httpx', # 假设API测试使用httpx
        'REPORT_TOOL': 'Allure 2.x'
    }
    try:
        env_file_path = os.path.join(allure_results_dir, 'environment.properties')
        # 确保使用 UTF-8 编码写入
        with open(env_file_path, 'w', encoding='utf-8') as f:
            for key, value in environment.items():
                # 替换换行符，避免多行值破坏格式
                value_str = str(value).replace('\\n', ' ').replace('\\r', '')
                f.write(f'{key}={value_str}\n') # 使用标准换行符
        print(f'环境信息写入成功: {env_file_path}')
    except Exception as e:
        print(f'写入环境信息失败: {e}')

    # executor.json - 可以保留，但使用固定名称或 APP_ENV
    # 不再需要 Jenkins 构建相关的环境变量
    build_url = os.environ.get('BUILD_URL', '#') # 保留 Build URL 以便追溯
    job_name = os.environ.get('JOB_NAME', 'Automation')
    build_number = os.environ.get('BUILD_NUMBER', 'N/A')

    executor = {
        'name': f'{app_env.upper()} Environment', # 使用环境名
        'type': 'ci', # 通用类型
        'url': build_url,
        'buildName': f'{job_name} #{build_number}',
        'buildUrl': build_url
    }
    try:
        exec_file_path = os.path.join(allure_results_dir, 'executor.json')
        with open(exec_file_path, 'w', encoding='utf-8') as f:
            json.dump(executor, f, ensure_ascii=False, indent=2)
        print(f'执行器信息写入成功: {exec_file_path}')
    except Exception as e:
        print(f'写入执行器信息失败: {e}')

    # categories.json (保持不变)
    categories = [
        {'name': '测试失败', 'matchedStatuses': ['failed'], 'messageRegex': '.*AssertionError.*'},
        {'name': '环境问题', 'matchedStatuses': ['broken', 'failed'], 'messageRegex': '.*(ConnectionError|TimeoutError|WebDriverException).*'},
        {'name': '产品缺陷', 'matchedStatuses': ['failed'], 'messageRegex': '.*预期结果与实际结果不符.*'}
    ]
    try:
        cat_file_path = os.path.join(allure_results_dir, 'categories.json')
        with open(cat_file_path, 'w', encoding='utf-8') as f:
            json.dump(categories, f, ensure_ascii=False, indent=2)
        print(f'分类信息写入成功: {cat_file_path}')
    except Exception as e:
        print(f'写入分类信息失败: {e}')

    print('元数据写入脚本执行完毕')

if __name__ == "__main__":
    main()