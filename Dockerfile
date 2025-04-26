FROM python:3.11.9-slim

WORKDIR /app

# 先只复制依赖声明文件，利用缓存加速依赖安装
COPY pyproject.toml poetry.lock /app/

# 彻底清理和重置APT源为清华源，确保不会使用官方源
RUN rm -rf /etc/apt/sources.list.d/* && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    apt-get clean && \
    apt-get update && apt-get install -y --no-install-recommends apt-transport-https ca-certificates && \
    apt-get update

# 安装 Playwright 依赖库和常用工具
RUN apt-get install -y --no-install-recommends \
    wget openjdk-17-jre-headless unzip \
    libglib2.0-0 libnss3 libnspr4 \
    libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libexpat1 \
    libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 \
    libxcb1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 \
    fonts-liberation libappindicator3-1 lsb-release \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 配置pip多源兜底（阿里云+清华）
RUN mkdir -p /root/.pip && \
    echo "[global]" > /root/.pip/pip.conf && \
    echo "index-url = https://mirrors.aliyun.com/pypi/simple/" >> /root/.pip/pip.conf && \
    echo "[global]" > /root/.pip/pip_tuna.conf && \
    echo "index-url = https://pypi.tuna.tsinghua.edu.cn/simple" >> /root/.pip/pip_tuna.conf

# 升级pip并安装poetry
RUN pip install --upgrade pip \
    && pip install "poetry>=1.5.0"

# 配置poetry多源兜底（阿里云+清华）
RUN poetry config repositories.aliyun https://mirrors.aliyun.com/pypi/simple/ \
    && poetry config repositories.tuna https://pypi.tuna.tsinghua.edu.cn/simple

# 复制全部项目代码到工作目录
COPY . /app

# 全局禁用 Poetry 的虚拟环境创建
ENV POETRY_VIRTUALENVS_CREATE=false

# 增加 Poetry 的网络超时时间（单位：秒）
ENV POETRY_REQUESTS_TIMEOUT=300

# 紧急修复 - 直接编辑CI脚本避免权限问题
RUN echo "# 紧急修复权限问题" >> /app/ci/scripts/hotfix.log && \
    sed -i 's/chown -R.*output\/reports\/allure-report/find "output\/reports\/allure-report" -type d -exec chmod 755 {} \\; \&\& find "output\/reports\/allure-report" -type f -exec chmod 644 {} \\;/g' /app/ci/scripts/run_and_notify.py && \
    sed -i 's/sudo chown -R.*nginx:nginx/find/g' /app/ci/scripts/generate_report.py && \
    sed -i 's/f"sudo find {remote_report_dir}/f"find {remote_report_dir}/g' /app/ci/scripts/generate_report.py && \
    sed -i 's/subprocess.run(\["chown"/# subprocess.run(["chown"/g' /app/ci/scripts/run_and_notify.py && \
    sed -i 's/"Attempting to fix local permissions"/"修正本地权限"/g' /app/ci/scripts/run_and_notify.py && \
    echo "# 修复完成" >> /app/ci/scripts/hotfix.log && \
    echo "# 设置UTF-8编码处理" >> /app/ci/scripts/hotfix.log && \
    # 修复JSON处理代码，确保使用UTF-8编码
    sed -i 's/json.load(f)/json.loads(f.read())/g' /app/ci/scripts/utils.py && \
    # 增加更多调试输出
    sed -i '/def get_allure_summary/a \    print(f"[DEBUG] 环境变量: ALLURE_REPORT_DIR={os.environ.get(\\"ALLURE_REPORT_DIR\\", \\"未设置\\")}")' /app/ci/scripts/utils.py && \
    echo "# 编码修复完成" >> /app/ci/scripts/hotfix.log

# 安装项目依赖（--no-root表示只安装依赖，不安装当前项目）
RUN poetry install --no-root -vvv

# playwright浏览器下载加速（可选）
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright

# 安装playwright及其浏览器（多源兜底）
RUN pip install playwright -i https://mirrors.aliyun.com/pypi/simple/ \
    || pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && playwright install

# 复制本地下载的Allure CLI安装包到镜像
COPY allure-2.27.0.zip /tmp/

RUN unzip /tmp/allure-2.27.0.zip -d /opt/ \
    && ln -s /opt/allure-2.27.0/bin/allure /usr/bin/allure \
    && rm /tmp/allure-2.27.0.zip