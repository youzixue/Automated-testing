from __future__ import annotations
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from src.utils.log.manager import get_logger

class EmailNotifier:
    """
    邮件通知工具类，支持发送文本和HTML邮件。
    """

    def __init__(
        self,
        smtp_server: str,
        smtp_port: int,
        username: str,
        password: str,
        use_tls: bool = True,
        use_ssl: bool = False,
        sender: Optional[str] = None
    ):
        """
        初始化邮件通知器。
        Args:
            smtp_server: SMTP服务器地址
            smtp_port: SMTP端口
            username: 登录用户名
            password: 登录密码
            use_tls: 是否使用TLS
            use_ssl: 是否使用SSL
            sender: 发件人邮箱（默认与用户名一致）
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.use_ssl = use_ssl
        self.sender = sender or username
        self.logger = get_logger(self.__class__.__name__)

    def send_email(
        self,
        subject: str,
        body: str,
        recipients: List[str],
        html: bool = False
    ) -> None:
        """
        发送邮件。
        Args:
            subject: 邮件主题
            body: 邮件正文
            recipients: 收件人列表
            html: 是否为HTML邮件
        Raises:
            smtplib.SMTPException: 发送失败
        """
        msg = MIMEMultipart()
        msg['From'] = self.sender
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = subject

        if html:
            msg.attach(MIMEText(body, 'html', 'utf-8'))
        else:
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

        try:
            self.logger.info(f"准备发送邮件: {subject} -> {recipients}")
            if self.use_ssl:
                # SSL方式（如465端口）
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.login(self.username, self.password)
                    server.sendmail(self.sender, recipients, msg.as_string())
            else:
                # 非SSL方式（如25/587端口），可选TLS
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                    if self.use_tls:
                        server.starttls()
                    server.login(self.username, self.password)
                    server.sendmail(self.sender, recipients, msg.as_string())
            self.logger.info(f"邮件发送成功: {subject} -> {recipients}")
        except smtplib.SMTPException as e:
            self.logger.error(f"邮件发送失败: {e}")
            raise

    def send_text(
        self,
        subject: str,
        body: str,
        recipients: List[str]
    ) -> None:
        """
        发送纯文本邮件。
        Args:
            subject: 邮件主题
            body: 邮件正文
            recipients: 收件人列表
        """
        self.send_email(subject, body, recipients, html=False)

    def send_html(
        self,
        subject: str,
        html_body: str,
        recipients: List[str]
    ) -> None:
        """
        发送HTML格式邮件。
        Args:
            subject: 邮件主题
            html_body: HTML正文
            recipients: 收件人列表
        """
        self.send_email(subject, html_body, recipients, html=True)