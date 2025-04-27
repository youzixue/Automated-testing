# notify.py
"""
邮件通知工具：
- 组装邮件参数和HTML正文
- 发送测试报告邮件
"""
import os
import time
import platform
import sys
from typing import Optional, Dict, List # 添加类型提示

# 将项目根目录添加到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.email_notifier import EmailNotifier
from src.utils.log.manager import get_logger # 导入项目的 get_logger 函数

# --- 使用项目标准日志工具获取 logger ---
logger = get_logger(__name__) # 使用 get_logger 获取实例

def send_report_email(summary: Optional[Dict]):
    """组装并发送HTML测试报告邮件。

    Args:
        summary: 包含测试统计信息的字典，或者在 CI 通知模式下可能只包含 {"status": "..."}。
                 如果为 None 或缺少 'total' 键，则不显示详细统计信息。
    """
    smtp_server = os.environ.get("EMAIL_SMTP_SERVER", "smtp.qq.com")
    try:
        smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", 465))
    except ValueError:
        logger.warning(f"无效的 EMAIL_SMTP_PORT 值，使用默认值 465。")
        smtp_port = 465
    username = os.environ.get("EMAIL_SENDER", "your-email@qq.com")
    password = os.environ.get("EMAIL_PASSWORD", "your-password")
    sender = os.environ.get("EMAIL_SENDER", username)
    use_ssl = os.environ.get("EMAIL_USE_SSL", "true").lower() == "true"
    recipients_str = os.environ.get("EMAIL_RECIPIENTS", username)
    recipients = [email.strip() for email in recipients_str.split(",") if email.strip()]
    
    # 从环境变量获取核心信息
    test_env = os.environ.get("APP_ENV", "N/A").upper()
    report_url = os.environ.get('ALLURE_PUBLIC_URL', '#') # Allure 报告链接
    build_url = os.environ.get('BUILD_URL', '#') # Jenkins 构建链接
    job_name = os.environ.get('JOB_NAME', 'N/A')
    build_number = os.environ.get('BUILD_NUMBER', 'N/A')
    build_status = os.environ.get("BUILD_STATUS", "UNKNOWN") # Jenkins 构建状态

    # 确定是否显示详细统计信息
    show_detailed_stats = summary is not None and 'total' in summary

    # 邮件标题
    subject = f"【自动化测试】{job_name} #{build_number} - {test_env} 环境 - {build_status}"

    # 获取操作系统和 Python 版本信息
    try:
        if platform.system() == "Windows":
            if hasattr(sys, 'getwindowsversion'):
                win_version = sys.getwindowsversion()
                build_number_os = win_version.build
                if build_number_os >= 22000:
                    os_info = f"Windows 11 ({platform.version()})"
                else:
                    os_info = f"Windows 10 ({platform.version()})"
            else:
                os_info = f"Windows {platform.release()} ({platform.version()})"
        elif platform.system() == "Darwin":
            os_info = f"macOS {platform.release()} ({platform.mac_ver()[0]})"
        else:
            os_info = f"{platform.system()} {platform.release()}"
    except Exception as e:
        logger.warning(f"无法确定操作系统信息: {e}", exc_info=True)
        os_info = "N/A"
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

    # 准备 HTML 内容
    report_generation_time = time.strftime("%Y-%m-%d %H:%M:%S")
    button_html = f'<a href="{report_url}" target="_blank" style="display: inline-block; padding: 10px 20px; font-size: 16px; color: #ffffff; background-color: #007bff; border-radius: 5px; text-decoration: none;">查看完整报告</a>' \
                  if report_url != '#' else '<span style="color: #888;">（报告链接无效）</span>'

    html_body = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
    body {{ font-family: sans-serif; line-height: 1.6; color: #333; }}
    .container {{ max-width: 700px; margin: 20px auto; padding: 20px; border: 1px solid #eee; border-radius: 8px; background-color: #f9f9f9; }}
    .header {{ text-align: center; margin-bottom: 20px; }}
    .header h1 {{ margin: 0; color: #333; }}
    .header p {{ color: #888; font-size: 0.9em; }}
    .status {{ text-align: center; margin-bottom: 20px; font-size: 1.2em; }}
    .status strong {{ padding: 5px 10px; border-radius: 4px; color: white; }}
    .status .success {{ background-color: #28a745; }}
    .status .failure {{ background-color: #dc3545; }}
    .status .unstable {{ background-color: #ffc107; color: #333; }}
    .status .unknown {{ background-color: #6c757d; }}
    .summary-block {{ display: flex; justify-content: space-around; text-align: center; margin-bottom: 20px; padding: 15px; background-color: #fff; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    .summary-item {{ flex: 1; padding: 0 5px; }}
    .summary-item h3 {{ margin: 0 0 5px 0; font-size: 1.8em; }}
    .summary-item span {{ font-size: 0.9em; color: #888; }}
    .details {{ margin-bottom: 20px; padding: 15px; background-color: #fff; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    .details p {{ margin: 5px 0; }}
    .environment {{ font-size: 0.9em; color: #555; border-top: 1px solid #eee; padding-top: 15px; margin-top: 20px; }}
    .environment h4 {{ margin-top: 0; margin-bottom: 10px; color: #333; }}
</style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>自动化测试报告</h1>
        <p>生成时间: {report_generation_time}</p>
        <p>构建任务: <a href="{build_url}" target="_blank">{job_name} #{build_number}</a></p>
    </div>

    <div class="status">
        <span>构建状态: </span>
        <strong class="{build_status.lower()}">{build_status}</strong>
    </div>

"""

    if show_detailed_stats:
        # 解析详细统计数据
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        broken = summary.get('broken', 0)
        skipped = summary.get('skipped', 0)
        total = summary.get('total', 0)
        # duration_ms = summary.get('duration', 0) # 持续时间信息不再可靠获取，从邮件中移除
        # exec_time_str = format_duration(duration_ms)
        pass_rate = f"{(passed / total * 100):.1f}%" if total > 0 else "N/A"
        
        pass_color = "#28a745" if passed > 0 else "#888"
        fail_color = "#dc3545" if failed > 0 else "#888"
        broken_color = "#ffc107" if broken > 0 else "#888"
        skipped_color = "#6c757d" if skipped > 0 else "#888"

        html_body += f"""
    <div class="summary-block">
        <div class="summary-item">
            <h3>{total}</h3>
            <span>总用例数</span>
        </div>
        <div class="summary-item" style="color: {pass_color};">
            <h3>{passed}</h3>
            <span>通过</span>
        </div>
        <div class="summary-item" style="color: {fail_color};">
            <h3>{failed}</h3>
            <span>失败</span>
        </div>
        <div class="summary-item" style="color: {broken_color};">
            <h3>{broken}</h3>
            <span>异常</span>
        </div>
        <div class="summary-item" style="color: {skipped_color};">
            <h3>{skipped}</h3>
            <span>跳过</span>
        </div>
    </div>
    <div class="details">
        <h4>测试结果详情</h4>
        <p><strong>通过率:</strong> {pass_rate}</p>
        <!-- <p><strong>执行时间:</strong> {exec_time_str}</p> --> <!-- 移除了执行时间 -->
    </div>
        """
    else:
        # 如果没有详细统计数据，显示提示信息
        html_body += '''
    <div class="details">
        <p style="text-align: center; color: #888;">详细测试统计信息请查看完整报告。</p>
    </div>
        '''

    # 添加报告链接按钮和环境信息
    html_body += f"""
    <div style="margin-top: 20px; text-align: center;">
        {button_html}
    </div>
    <div class="environment">
        <h4>执行环境信息</h4>
        <p><strong>测试环境:</strong> {test_env}</p>
        <p><strong>操作系统:</strong> {os_info}</p>
        <p><strong>Python版本:</strong> {python_version}</p>
    </div>
</div>
</body>
</html>
    """

    # --- 发送邮件 --- 
    logger.info(f"准备发送HTML邮件，参数: 服务器={smtp_server}:{smtp_port}, SSL={use_ssl}, 发件人={sender}, 收件人={recipients}")
    try:
        notifier = EmailNotifier(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            username=username,
            password=password,
            sender=sender,
            use_ssl=use_ssl,
            use_tls=False # 显式设置 use_tls
        )
        notifier.send_html(
            subject=subject,
            html_body=html_body,
            recipients=recipients
        )
        logger.info("HTML邮件发送成功")
    except Exception as e:
        logger.error(f"HTML邮件发送失败: {e}", exc_info=True)
        # 记录一些关键配置信息以便排查
        logger.error(f"SMTP服务器: {smtp_server}:{smtp_port}, SSL: {use_ssl}")
        logger.error(f"发件人: {sender}")
