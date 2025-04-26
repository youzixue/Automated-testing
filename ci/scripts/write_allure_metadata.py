import os
import json
import datetime
import sys

def main():
    # Get target directory from command line argument
    if len(sys.argv) < 2:
        print("错误：需要提供 Allure 结果目录作为参数！")
        sys.exit(1)
    allure_results_dir = sys.argv[1]

    # 从容器环境变量获取信息
    app_env = os.environ.get('APP_ENV', 'unknown')
    ci_name = os.environ.get('CI_NAME', 'Jenkins')
    build_number = os.environ.get('BUILD_NUMBER', 'unknown')
    build_url = os.environ.get('BUILD_URL', 'unknown')
    job_name = os.environ.get('JOB_NAME', 'unknown')

    print(f'为Allure报告生成元数据信息')
    print(f'环境: {app_env}')
    print(f'CI名称: {ci_name}')
    print(f'构建号: {build_number}')
    print(f'结果目录: {allure_results_dir}')

    try:
        os.makedirs(allure_results_dir, exist_ok=True)
    except Exception as e:
        print(f'创建结果目录失败: {e}')
        sys.exit(1) # 创建失败则退出

    # environment.properties
    environment = {
        'APP_ENV': app_env,
        'Build Number': build_number,
        'Build URL': build_url,
        'Job Name': job_name,
        'CI': ci_name,
        'Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    try:
        env_file_path = os.path.join(allure_results_dir, 'environment.properties')
        with open(env_file_path, 'w', encoding='utf-8') as f:
            for key, value in environment.items():
                f.write(f'{key}={value}\n') # Standard newline
        print(f'环境信息写入成功: {env_file_path}')
    except Exception as e:
        print(f'写入环境信息失败: {e}')

    # executor.json
    executor = {
        'name': ci_name,
        'type': 'jenkins',
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

    # categories.json
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