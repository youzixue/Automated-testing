"""
CI流程通用工具函数：
- 获取Allure报告统计信息
- 检查suites.json引用完整性 (保留此函数，可能用于调试或验证)
"""
import os
import json

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
    # 从 summary.json 获取持续时间 (毫秒)
    duration_ms = time_info.get("duration", 0)
    # 返回毫秒值，让调用者决定如何格式化
    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "broken": broken,
        "skipped": skipped,
        "unknown": unknown,
        "duration": duration_ms # 返回毫秒
    }

def check_suites_uids_integrity():
    """检查suites.json中引用的所有UID是否在data目录中存在对应文件。
    
    此函数当前未被 CI 脚本调用，但可能用于本地调试或报告验证。
    """
    # ... (函数实现保持不变) ...
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