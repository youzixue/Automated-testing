"""
Allure报告生成与上传工具：
- 生成Allure HTML报告
- 写入环境信息、executor、categories
- 创建.nojekyll文件
- 上传报告到远端服务器
- 修正远端权限
"""
import os
import subprocess
import json
import time
import shutil
import platform
import sys

def write_allure_environment():
    """生成Allure环境信息文件，供报告展示。"""
    env_dir = "output/reports/allure-results"
    os.makedirs(env_dir, exist_ok=True)
    try:
        win_ver = platform.win32_ver() if hasattr(platform, "win32_ver") else ("", "", "")
        if platform.system() == "Windows":
            try:
                if hasattr(sys, 'getwindowsversion'):
                    win_version = sys.getwindowsversion()
                    build_number = win_version.build
                    if build_number >= 22000:
                        os_info = f"Windows 11 ({platform.version()})"
                    else:
                        os_info = f"Windows 10 ({platform.version()})"
                else:
                    os_info = f"Windows {platform.release()} ({platform.version()})"
            except Exception as e:
                os_info = f"Windows {platform.release()}"
        elif platform.system() == "Darwin":
            os_info = f"macOS {platform.release()} ({platform.mac_ver()[0]})"
        else:
            os_info = f"{platform.system()} {platform.release()}"
    except Exception as e:
        os_info = platform.system()
    env_vars = {
        "APP_ENV": os.environ.get('APP_ENV', 'test'),
        "PYTHON_VERSION": f"{sys.version}",
        "OS": os_info,
        "TEST_FRAMEWORK": "pytest",
        "UI_AUTOMATION": "Playwright",
        "API_AUTOMATION": "httpx",
        "REPORT_TOOL": f"Allure {os.environ.get('ALLURE_VERSION', '2.x')}"
    }
    env_file = os.path.join(env_dir, "environment.properties")
    with open(env_file, "w", encoding="utf-8") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    env_xml = os.path.join(env_dir, "environment.xml")
    xml_content = f"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<environment>\n"""
    for key, value in env_vars.items():
        xml_content += f"    <parameter>\n        <key>{key}</key>\n        <value>{value}</value>\n    </parameter>\n"
    xml_content += "</environment>"
    with open(env_xml, "w", encoding="utf-8") as f:
        f.write(xml_content)
    env_json = os.path.join(env_dir, "environment.json")
    env_data = [{"name": key, "values": [value]} for key, value in env_vars.items()]
    with open(env_json, "w", encoding="utf-8") as f:
        json.dump(env_data, f, ensure_ascii=False, indent=2)

def write_allure_executor():
    """生成Allure运行器信息，供报告展示。"""
    env_dir = "output/reports/allure-results"
    os.makedirs(env_dir, exist_ok=True)
    ci_name = os.environ.get("CI_NAME", "本地执行")
    ci_build = os.environ.get("CI_BUILD_NUMBER")
    readable_time = time.strftime("%Y%m%d-%H:%M:%S")
    if not ci_build or not ci_build.isdigit():
        ci_build = readable_time
    ci_url = os.environ.get("CI_BUILD_URL", "")
    report_url = os.environ.get("ALLURE_PUBLIC_URL", "")
    build_order = int(time.strftime('%m%d%H%M'))
    executor_info = {
        "name": ci_name,
        "type": "jenkins",
        "buildName": f"{ci_build}",
        "buildOrder": build_order,
        "reportUrl": report_url,
        "buildUrl": ci_url
    }
    executor_file = os.path.join(env_dir, "executor.json")
    with open(executor_file, "w", encoding="utf-8") as f:
        json.dump(executor_info, f, ensure_ascii=False, indent=2)

def write_allure_categories():
    """生成Allure 2.33.0兼容的categories.json到allure-results目录，类别名称为中文"""
    env_dir = "output/reports/allure-results"
    os.makedirs(env_dir, exist_ok=True)
    categories = [
        {
            "name": "产品缺陷",
            "matchedStatuses": ["failed"],
            "messageRegex": ".*",
            "traceRegex": ".*",
            "flaky": False
        },
        {
            "name": "用例缺陷",
            "matchedStatuses": ["broken"],
            "messageRegex": ".*",
            "traceRegex": ".*",
            "flaky": False
        },
        {
            "name": "跳过用例",
            "matchedStatuses": ["skipped"],
            "flaky": False
        }
    ]
    categories_file = os.path.join(env_dir, "categories.json")
    with open(categories_file, "w", encoding="utf-8") as f:
        json.dump(categories, f, ensure_ascii=False, indent=2)

def create_nojekyll_file(path):
    """在指定目录创建.nojekyll文件"""
    if os.path.exists(path):
        no_jekyll_file = os.path.join(path, ".nojekyll")
        if not os.path.exists(no_jekyll_file):
            with open(no_jekyll_file, "w") as f:
                f.write("")

def generate_allure_report():
    allure_cmd = os.environ.get("ALLURE_CMD", "allure")
    report_dir = "output/reports/allure-report"
    try:
        allure_gen_cmd = [
            allure_cmd, "generate", "output/reports/allure-results",
            "--clean", "-o", report_dir
        ]
        print(f"[INFO] 执行Allure报告生成命令: {' '.join(allure_gen_cmd)}")
        subprocess.run(allure_gen_cmd, check=True)
        print("[INFO] Allure报告生成成功")
        static_dirs = [
            "output/reports/allure-report",
            "output/reports/allure-report/data",
            "output/reports/allure-report/history"
        ]
        for static_dir in static_dirs:
            create_nojekyll_file(static_dir)
        return True
    except Exception as e:
        print(f"[ERROR] Allure报告生成出错: {e}")
        return False

def upload_report_to_ecs(local_report_dir, remote_user, remote_host, remote_dir):
    remote_report_dir = f"{remote_dir}/allure-report"
    print(f"[INFO] 清空远端allure-report目录: {remote_report_dir}")
    subprocess.run([
        "ssh", f"{remote_user}@{remote_host}", f"rm -rf {remote_report_dir}"
    ], check=True)
    print(f"[INFO] 上传本地allure-report目录: {local_report_dir} -> {remote_dir}")
    subprocess.run([
        "scp", "-r", "-o", "StrictHostKeyChecking=no",
        local_report_dir,
        f"{remote_user}@{remote_host}:{remote_dir}"
    ], check=True)
    print("[INFO] Allure报告全量上传成功")
    return True

def fix_permissions(remote_user, remote_host, remote_dir, nginx_user="nginx"):
    remote_report_dir = f"{remote_dir}/allure-report"
    print(f"[INFO] 修正远端allure-report目录权限: {remote_report_dir} -> {nginx_user}")
    subprocess.run([
        "ssh", f"{remote_user}@{remote_host}",
        f"sudo chown -R {nginx_user}:{nginx_user} {remote_report_dir} && "
        f"sudo find {remote_report_dir} -type d -exec chmod 755 {{}} \\; && "
        f"sudo find {remote_report_dir} -type f -exec chmod 644 {{}} \\;"
    ], check=True)
    print("[INFO] 权限修正成功")
