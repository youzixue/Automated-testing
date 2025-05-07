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

# 安装 Playwright 依赖库、常用工具、unzip (用于解压platform-tools和allure) 以及中文字体
RUN apt-get install -y --no-install-recommends \
    wget openjdk-17-jre-headless unzip \
    libglib2.0-0 libnss3 libnspr4 \
    libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libexpat1 \
    libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 \
    libxcb1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 \
    fonts-liberation fonts-noto-cjk \
    libappindicator3-1 lsb-release \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 复制本地下载的 platform-tools 到镜像中
# !!! 请确保 platform-tools-latest-linux.zip 与 Dockerfile 在同一目录 !!!
COPY platform-tools-latest-linux.zip /tmp/platform-tools.zip

# 解压 platform-tools 并设置环境变量
RUN unzip /tmp/platform-tools.zip -d /opt && \
    rm /tmp/platform-tools.zip && \
    mv /opt/platform-tools /opt/android-sdk-platform-tools # 重命名为更清晰的路径
ENV PATH="/opt/android-sdk-platform-tools:$PATH"

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

# 全局禁用 Poetry 的虚拟环境创建
ENV POETRY_VIRTUALENVS_CREATE=false

# 增加 Poetry 的网络超时时间（单位：秒）
ENV POETRY_REQUESTS_TIMEOUT=300

# 安装项目依赖（--no-root表示只安装依赖，不安装当前项目）
# 这里我们先不运行 poetry install，因为通常会在 Jenkinsfile 的一个单独阶段进行，
# 以便更好地利用 Docker 层缓存。如果您的 pyproject.toml 和 poetry.lock 不经常变动，
# 而代码经常变动，将 poetry install 放在 Dockerfile 靠后的位置，
# 或者在 Jenkinsfile 中执行，可以避免每次代码变动都重新安装所有依赖。
# 如果您希望在镜像中直接包含所有依赖，可以取消下面一行的注释：
# RUN poetry install --no-root

# playwright浏览器下载加速（可选）
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright

# 安装playwright及其浏览器（多源兜底）
# 注意：如果 poetry install 已经安装了 playwright，这里的 pip install playwright 可能会冗余，
# 但 playwright install (浏览器驱动) 仍然是需要的。
# 为确保 playwright 命令可用，这里保留。
RUN pip install playwright -i https://mirrors.aliyun.com/pypi/simple/ \
    || pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && playwright install

# 复制本地下载的Allure CLI安装包到镜像
# !!! 请确保 allure-2.27.0.zip 与 Dockerfile 在同一目录 !!!
COPY allure-2.27.0.zip /tmp/

RUN unzip /tmp/allure-2.27.0.zip -d /opt/ \
    && ln -s /opt/allure-2.27.0/bin/allure /usr/bin/allure \
    && rm /tmp/allure-2.27.0.zip

# 可以添加一个CMD或ENTRYPOINT，但通常Jenkinsfile中docker run会覆盖它
# CMD ["python"]