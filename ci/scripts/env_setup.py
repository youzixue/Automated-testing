"""
CI环境准备相关工具：
- .env加载（仅本地）
- 关键环境变量补全
- 目录准备
"""
import os

def ensure_env_variables():
    """确保关键环境变量存在，避免发送邮件时出错"""
    defaults = {
        "EMAIL_SMTP_SERVER": "smtp.qq.com",
        "EMAIL_SMTP_PORT": "465",
        "EMAIL_SENDER": "your-email@qq.com",
        "EMAIL_PASSWORD": "your-password-or-auth-code",
        "EMAIL_RECIPIENTS": "your-email@qq.com",
        "EMAIL_USE_SSL": "true"
    }
    for key, default_value in defaults.items():
        if key not in os.environ:
            os.environ[key] = default_value
            print(f"[WARNING] 环境变量 {key} 未设置，使用默认值: {default_value}")

def load_dotenv_if_local():
    """仅本地开发时加载.env文件"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # CI/CD 环境可忽略

def prepare_env():
    load_dotenv_if_local()
    ensure_env_variables()
