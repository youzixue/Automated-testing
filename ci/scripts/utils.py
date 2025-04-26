"""
CI流程通用工具函数：
- 获取Allure报告统计信息
- 复制历史数据到结果目录
- 检查suites.json引用完整性
"""
import os
import json
import shutil

def get_allure_summary(report_dir_base: str = "output/reports/allure-report"):
    """获取Allure报告的统计摘要。
    
    Args:
        report_dir_base: Allure报告所在的根目录。
        
    Returns:
        dict or None: 包含统计信息的字典，或在找不到文件时返回None。
    """
    summary_path = os.path.join(report_dir_base, "widgets", "summary.json")
    print(f"[DEBUG] Trying to read summary from: {summary_path}") # 添加调试日志
    if not os.path.exists(summary_path):
        print(f"[WARNING] Summary file not found at: {summary_path}") # 添加警告日志
        return None
    try: # 增加try-except确保文件读取或JSON解析错误能被捕获
        with open(summary_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] Failed to read or parse summary file {summary_path}: {e}")
        return None
        
    statistic = data.get("statistic", {})
    total = statistic.get("total", 0)
    passed = statistic.get("passed", 0)
    failed = statistic.get("failed", 0)
    broken = statistic.get("broken", 0)
    skipped = statistic.get("skipped", 0)
    unknown = statistic.get("unknown", 0)
    time_info = data.get("time", {})
    duration = time_info.get("duration", 0) / 1000  # ms转秒
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "broken": broken,
        "skipped": skipped,
        "unknown": unknown,
        "duration": duration
    }

def copy_history_to_results():
    """复制历史数据到结果目录"""
    allure_results = "output/reports/allure-results"
    allure_report = "output/reports/allure-report"
    history_src = os.path.join(allure_report, "history")
    history_dst = os.path.join(allure_results, "history")
    os.makedirs(allure_results, exist_ok=True)
    os.makedirs(history_dst, exist_ok=True)
    if os.path.exists(history_src):
        print(f"[INFO] 正在复制历史数据: {history_src} -> {history_dst}")
        try:
            for item in os.listdir(history_src):
                src_path = os.path.join(history_src, item)
                dst_path = os.path.join(history_dst, item)
                if os.path.isfile(src_path):
                    shutil.copy2(src_path, dst_path)
                else:
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        except Exception as e:
            print(f"[WARNING] 复制历史数据时出错: {e}")
    else:
        print(f"[INFO] 历史数据目录不存在: {history_src}")

def check_suites_uids_integrity():
    """检查suites.json中引用的所有UID是否在data目录中存在对应文件"""
    data_dir = "output/reports/allure-report/data"
    suites_json = os.path.join(data_dir, "suites.json")
    if not os.path.exists(suites_json):
        print("[WARNING] suites.json文件不存在，无法检查引用完整性")
        return []
    try:
        with open(suites_json, "r", encoding="utf-8") as f:
            suites_data = json.load(f)
    except Exception as e:
        print(f"[ERROR] 读取suites.json失败: {e}")
        return []
    referenced_uids = set()
    def extract_uids(item):
        if isinstance(item, dict):
            if "uid" in item:
                referenced_uids.add(item["uid"])
            for value in item.values():
                extract_uids(value)
        elif isinstance(item, list):
            for element in item:
                extract_uids(element)
    extract_uids(suites_data)
    print(f"[INFO] 在suites.json中找到 {len(referenced_uids)} 个引用的UID")
    missing_uids = []
    for uid in referenced_uids:
        uid_file = os.path.join(data_dir, f"{uid}.json")
        if not os.path.exists(uid_file):
            missing_uids.append(uid)
            print(f"[WARNING] 缺少UID文件: {uid}.json")
    return missing_uids
