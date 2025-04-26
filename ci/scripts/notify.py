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
# import logging # 移除 logging 模块的导入

# 将项目根目录添加到系统路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.email_notifier import EmailNotifier
from src.utils.log.manager import get_logger # 导入项目的 get_logger 函数

# --- 使用项目标准日志工具获取 logger ---
logger = get_logger(__name__) # 使用 get_logger 获取实例

def send_report_email(summary, upload_success):
    """组装并发送HTML测试报告邮件"""
    smtp_server = os.environ.get("EMAIL_SMTP_SERVER", "smtp.qq.com")
    try:
        smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", 465))
    except ValueError: # 更具体的异常类型
        logger.warning(f"Invalid EMAIL_SMTP_PORT value, using default 465.")
        smtp_port = 465
    username = os.environ.get("EMAIL_SENDER", "your-email@qq.com")
    password = os.environ.get("EMAIL_PASSWORD", "your-password")
    sender = os.environ.get("EMAIL_SENDER", username)
    use_ssl = os.environ.get("EMAIL_USE_SSL", "true").lower() == "true"
    recipients_str = os.environ.get("EMAIL_RECIPIENTS", username)
    recipients = [email.strip() for email in recipients_str.split(",") if email.strip()]
    test_env = os.environ.get("APP_ENV", "test")
    try:
        if platform.system() == "Windows":
            if hasattr(sys, 'getwindowsversion'):
                win_version = sys.getwindowsversion()
                build_number = win_version.build
                if build_number >= 22000:
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
        logger.warning(f"Could not determine OS info: {e}", exc_info=True) # 添加 exc_info
        os_info = "N/A"
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    public_url = os.environ.get("ALLURE_PUBLIC_URL", "")
    total_count = summary.get("total", 0)
    pass_count = summary.get("passed", 0)
    fail_count = summary.get("failed", 0)
    broken_count = summary.get("broken", 0)
    skipped_count = summary.get("skipped", 0)
    
    # 处理执行时间，确保是数字才格式化
    duration_value = summary.get('duration')
    if isinstance(duration_value, (int, float)):
        exec_time = f"{duration_value:.1f}秒"
    else:
        exec_time = str(duration_value) if duration_value is not None else "N/A" # 如果不是数字，直接转字符串或显示N/A
        
    pass_rate = f"{(pass_count/total_count*100):.1f}%" if total_count and isinstance(total_count, int) and total_count > 0 and isinstance(pass_count, int) else "N/A" # 增加对total_count类型的检查
    report_generation_time = time.strftime("%Y-%m-%d %H:%M:%S")
    pass_rate_percent = f"{pass_count}/{total_count}" if isinstance(total_count, int) and isinstance(pass_count, int) else "N/A" # 确保是数字才拼接
    
    subject = f"【自动化测试】测试报告 [{report_generation_time}] - 通过率: {pass_rate_percent}"
    if public_url:
        report_link = public_url
        button_html = f'<a href="{report_link}" target="_blank" style="display: inline-block; padding: 10px 20px; font-size: 16px; color: #ffffff; background-color: #007bff; border-radius: 5px; text-decoration: none;">查看完整报告</a>'
    else:
        report_link = "N/A"
        button_html = '<span style="color: #888;">（报告未上传或链接无效）</span>'
    pass_color = "#28a745" if pass_count > 0 else "#888"
    fail_color = "#dc3545" if fail_count > 0 else "#888"
    broken_color = "#ffc107" if broken_count > 0 else "#888"
    skipped_color = "#6c757d" if skipped_count > 0 else "#888"
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
    .summary-block {{ display: flex; justify-content: space-around; text-align: center; margin-bottom: 20px; padding: 15px; background-color: #fff; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    .summary-item {{ flex: 1; }}
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
    </div>
    <div class="summary-block">
        <div class="summary-item">
            <h3>{total_count}</h3>
            <span>总用例数</span>
        </div>
        <div class="summary-item" style="color: {pass_color};">
            <h3>{pass_count}</h3>
            <span>通过</span>
        </div>
        <div class="summary-item" style="color: {fail_color};">
            <h3>{fail_count}</h3>
            <span>失败</span>
        </div>
        <div class="summary-item" style="color: {broken_color};">
            <h3>{broken_count}</h3>
            <span>异常</span>
        </div>
        <div class="summary-item" style="color: {skipped_color};">
            <h3>{skipped_count}</h3>
            <span>跳过</span>
        </div>
    </div>
    <div class="details">
        <h4>测试结果详情</h4>
        <p><strong>通过率:</strong> {pass_rate}</p>
        <p><strong>执行时间:</strong> {exec_time}</p>
        <div style="margin-top: 15px; text-align: center;">
            {button_html}
        </div>
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
    # --- 使用 logger 记录准备发送的信息 ---
    logger.info(f"准备发送HTML邮件，参数: 服务器={{smtp_server}}:{{smtp_port}}, SSL={{use_ssl}}, 发件人={{sender}}, 收件人={{recipients}}")
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
        # --- 使用 logger 记录发送成功信息 ---
        logger.info("HTML邮件发送成功")
    except Exception as e:
        # --- 使用 logger 记录错误信息，添加 exc_info=True 获取traceback ---
        logger.error(f"HTML邮件发送失败: {{e}}", exc_info=True)
        logger.error(f"SMTP服务器: {{smtp_server}}:{{smtp_port}}")
        logger.error(f"发件人: {{sender}}")
        logger.error(f"收件人: {{recipients}}")
        logger.error(f"SSL: {{use_ssl}}")
