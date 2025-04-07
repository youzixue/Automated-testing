"""
邮件通知工具。

提供测试执行后的邮件通知功能，支持通过环境变量获取敏感信息，
使用安全连接发送邮件，并包含完整的测试结果信息。
"""

import os
import sys
import smtplib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formataddr
from email.header import Header
from contextlib import contextmanager

from src.utils.patterns import Singleton
from src.utils.config.manager import DefaultConfigManager


class EmailConfigError(Exception):
    """邮件配置错误异常。"""
    pass


class EmailSendError(Exception):
    """邮件发送错误异常。"""
    pass


class EmailNotifier(Singleton):
    """邮件通知器。
    
    单例模式实现的邮件通知器，用于发送测试结果通知邮件。
    
    支持:
    1. 从配置文件和环境变量读取配置
    2. 使用安全连接(SSL/TLS)
    3. 附加测试报告
    4. 自定义邮件模板
    5. 失败时立即通知(可配置)
    
    Attributes:
        enabled: 是否启用邮件通知
        smtp_server: SMTP服务器地址
        smtp_port: SMTP服务器端口
        sender: 发件人地址
        recipients: 收件人列表
        use_ssl: 是否使用SSL连接
        use_tls: 是否使用TLS连接
        subject_template: 邮件主题模板
        body_template: 邮件正文模板
        attach_report: 是否附加测试报告
        notify_on_failure: 是否在失败时立即通知
    """
    
    def __init__(self) -> None:
        """初始化邮件通知器。
        
        从配置文件和环境变量加载配置信息。
        """
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config_manager = DefaultConfigManager()
        self._load_config()
    
    def _load_config(self) -> None:
        """加载邮件配置。
        
        从配置文件和环境变量加载邮件配置。
        
        Raises:
            EmailConfigError: 配置加载错误
        """
        try:
            config = self._config_manager.get_all()
            email_config = config.get("notification", {}).get("email", {})
            
            # 加载基本配置
            self.enabled = email_config.get("enabled", False)
            self.smtp_server = email_config.get("smtp_server", "")
            self.smtp_port = email_config.get("smtp_port", 0)
            self.sender = email_config.get("sender_email", "")
            self.recipients = email_config.get("recipients", [])
            self.use_ssl = email_config.get("use_ssl", False)
            self.use_tls = email_config.get("use_tls", False)
            self.subject_template = email_config.get("subject_template", "测试报告: {status}")
            self.body_template = email_config.get("body_template", "测试执行结果")
            self.attach_report = email_config.get("attach_report", True)
            self.notify_on_failure = email_config.get("notify_on_failure", False)
            
            # 从环境变量覆盖配置
            if os.environ.get("EMAIL_ENABLED") is not None:
                self.enabled = os.environ.get("EMAIL_ENABLED").lower() in ("true", "1", "yes")
            
            self.smtp_server = os.environ.get("EMAIL_SMTP_SERVER", self.smtp_server)
            
            if os.environ.get("EMAIL_SMTP_PORT"):
                try:
                    self.smtp_port = int(os.environ.get("EMAIL_SMTP_PORT", "0"))
                except ValueError:
                    self._logger.warning("无效的SMTP端口环境变量，使用配置文件中的值")
            
            self.sender = os.environ.get("EMAIL_SENDER", self.sender)
            
            if os.environ.get("EMAIL_RECIPIENTS"):
                self.recipients = [r.strip() for r in os.environ.get("EMAIL_RECIPIENTS", "").split(",")]
            
            if os.environ.get("EMAIL_USE_SSL") is not None:
                self.use_ssl = os.environ.get("EMAIL_USE_SSL").lower() in ("true", "1", "yes")
                
            if os.environ.get("EMAIL_USE_TLS") is not None:
                self.use_tls = os.environ.get("EMAIL_USE_TLS").lower() in ("true", "1", "yes")
            
            # 检查配置有效性
            self._validate_config()
                
        except Exception as e:
            self._logger.error(f"加载邮件配置失败: {e}")
            raise EmailConfigError(f"加载邮件配置失败: {e}")
    
    def _validate_config(self) -> None:
        """验证邮件配置有效性。
        
        Raises:
            EmailConfigError: 配置无效
        """
        if not self.enabled:
            return
            
        if not self.smtp_server:
            raise EmailConfigError("SMTP服务器地址未配置")
            
        if not self.smtp_port:
            raise EmailConfigError("SMTP服务器端口未配置")
            
        if not self.sender:
            raise EmailConfigError("发件人地址未配置")
            
        if not self.recipients:
            raise EmailConfigError("收件人列表为空")
    
    @contextmanager
    def _get_smtp_connection(self) -> smtplib.SMTP:
        """获取SMTP连接。
        
        使用上下文管理器确保连接正确关闭。
        
        Yields:
            smtplib.SMTP: SMTP连接对象
            
        Raises:
            EmailSendError: 连接错误
        """
        smtp = None
        try:
            if self.use_ssl:
                self._logger.debug(f"使用SSL连接到SMTP服务器: {self.smtp_server}:{self.smtp_port}")
                smtp = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                self._logger.debug(f"连接到SMTP服务器: {self.smtp_server}:{self.smtp_port}")
                smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
                
                if self.use_tls:
                    self._logger.debug("启用TLS加密")
                    smtp.starttls()
            
            # 获取SMTP密码
            smtp_password = os.environ.get("EMAIL_PASSWORD", "")
            
            if smtp_password:
                self._logger.debug(f"以用户 {self.sender} 登录")
                smtp.login(self.sender, smtp_password)
            else:
                self._logger.warning("未提供SMTP密码，尝试匿名登录")
                
            yield smtp
        
        except Exception as e:
            self._logger.error(f"SMTP连接错误: {e}")
            raise EmailSendError(f"SMTP连接错误: {e}")
        
        finally:
            if smtp:
                try:
                    smtp.quit()
                    self._logger.debug("SMTP连接已关闭")
                except Exception as e:
                    self._logger.warning(f"关闭SMTP连接时出错: {e}")
    
    def send_test_results(self, 
                         test_summary: Dict[str, int], 
                         report_path: Optional[str] = None,
                         failed_tests: Optional[List[Dict[str, Any]]] = None) -> bool:
        """发送测试结果邮件。
        
        Args:
            test_summary: 测试结果摘要，包含通过/失败/跳过/总计数量
            report_path: 报告路径，用于附加到邮件
            failed_tests: 失败测试用例的详细信息列表
            
        Returns:
            bool: 是否发送成功
            
        Raises:
            EmailSendError: 邮件发送失败
        """
        if not self.enabled:
            self._logger.info("邮件通知未启用")
            return False
            
        try:
            # 准备邮件内容
            msg = MIMEMultipart()
            
            # 设置邮件主题
            status = "通过" if test_summary.get("failed", 0) == 0 else "失败"
            subject = self.subject_template.format(
                status=status,
                datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                passed=test_summary.get("passed", 0),
                failed=test_summary.get("failed", 0),
                skipped=test_summary.get("skipped", 0),
                total=test_summary.get("total", 0)
            )
            msg["Subject"] = Header(subject, "utf-8")
            
            # 设置发件人和收件人
            msg["From"] = formataddr(("自动化测试框架", self.sender))
            msg["To"] = ", ".join(self.recipients)
            
            # 准备邮件正文
            body = self._generate_email_body(test_summary, failed_tests)
            msg.attach(MIMEText(body, "html", "utf-8"))
            
            # 附加报告
            if self.attach_report and report_path and os.path.exists(report_path):
                self._logger.debug(f"附加报告: {report_path}")
                with open(report_path, "rb") as file:
                    attachment = MIMEApplication(file.read(), Name=os.path.basename(report_path))
                attachment["Content-Disposition"] = f'attachment; filename="{os.path.basename(report_path)}"'
                msg.attach(attachment)
            
            # 发送邮件
            with self._get_smtp_connection() as smtp:
                self._logger.info(f"发送邮件至: {', '.join(self.recipients)}")
                smtp.send_message(msg)
                
            self._logger.info("邮件发送成功")
            return True
            
        except Exception as e:
            self._logger.error(f"发送邮件失败: {e}")
            raise EmailSendError(f"发送邮件失败: {e}")
    
    def _generate_email_body(self, 
                            test_summary: Dict[str, int], 
                            failed_tests: Optional[List[Dict[str, Any]]] = None) -> str:
        """生成邮件正文。
        
        Args:
            test_summary: 测试结果摘要
            failed_tests: 失败测试用例的详细信息列表
            
        Returns:
            str: 邮件正文HTML内容
        """
        # 使用HTML格式美化邮件
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h2 {{ color: #333; }}
                .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
                .skipped {{ color: orange; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .error-details {{ background-color: #fff8f8; border-left: 3px solid #d9534f; padding: 10px; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <h2>自动化测试执行结果</h2>
            <div class="summary">
                <p>
                    <span class="passed">通过: {test_summary.get('passed', 0)}</span> | 
                    <span class="failed">失败: {test_summary.get('failed', 0)}</span> | 
                    <span class="skipped">跳过: {test_summary.get('skipped', 0)}</span> | 
                    总计: {test_summary.get('total', 0)}
                </p>
                <p>执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        """
        
        # 如果有失败的测试用例，添加详情
        if failed_tests and test_summary.get('failed', 0) > 0:
            html += """
            <h3>失败测试用例详情</h3>
            <table>
                <tr>
                    <th>测试名称</th>
                    <th>失败原因</th>
                </tr>
            """
            
            for test in failed_tests:
                html += f"""
                <tr>
                    <td>{test.get('name', 'Unknown')}</td>
                    <td>
                        {test.get('error_message', 'Unknown error')}
                        <div class="error-details">
                            <pre>{test.get('error_trace', '')}</pre>
                        </div>
                    </td>
                </tr>
                """
            
            html += "</table>"
        
        # 添加环境信息
        env = os.environ.get("ENV", "dev")
        python_version = sys.version.split()[0]
        platform_info = sys.platform
        
        html += f"""
            <h3>环境信息</h3>
            <ul>
                <li>测试环境: {env}</li>
                <li>Python版本: {python_version}</li>
                <li>平台: {platform_info}</li>
            </ul>
        """
        
        html += """
        </body>
        </html>
        """
        
        return html


def get_email_notifier() -> EmailNotifier:
    """获取邮件通知器实例。
    
    Returns:
        EmailNotifier: 邮件通知器单例实例
    """
    try:
        # 正确获取单例实例
        return EmailNotifier()
    except Exception as e:
        logging.getLogger("email_notifier").error(f"获取邮件通知器失败: {e}")
        # 返回一个空实现，避免程序崩溃
        class NullEmailNotifier:
            def send_test_results(self, *args, **kwargs):
                return False
        return NullEmailNotifier()


def send_test_results(test_summary: Dict[str, int], 
                     report_path: Optional[str] = None,
                     failed_tests: Optional[List[Dict[str, Any]]] = None) -> bool:
    """发送测试结果邮件。
    
    便捷函数，内部使用EmailNotifier单例发送邮件。
    
    Args:
        test_summary: 测试结果摘要，包含通过/失败/跳过/总计数量
        report_path: 报告路径，用于附加到邮件
        failed_tests: 失败测试用例的详细信息列表
        
    Returns:
        bool: 是否发送成功
    """
    return get_email_notifier().send_test_results(test_summary, report_path, failed_tests)