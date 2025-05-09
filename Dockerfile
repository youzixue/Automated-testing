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
    mv /opt/platform-tools /opt/android-sdk-platform-tools && \
    echo "Android SDK Platform Tools installed."
ENV PATH="/opt/android-sdk-platform-tools:$PATH"

# 配置pip多源兜底（阿里云+清华）
RUN mkdir -p /root/.pip && \
    echo "[global]" > /root/.pip/pip.conf && \
    echo "index-url = https://mirrors.aliyun.com/pypi/simple/" >> /root/.pip/pip.conf && \
    echo "[global]" > /root/.pip/pip_tuna.conf && \
    echo "index-url = https://pypi.tuna.tsinghua.edu.cn/simple" >> /root/.pip/pip_tuna.conf

# 升级pip并安装poetry
RUN pip install --upgrade pip \
    && pip install "poetry>=1.5.0" \
    && echo "Poetry installed."

# 确保 poetry (以及其他 pip 安装的脚本) 的路径在 PATH 中
ENV PATH="/root/.local/bin:/usr/local/bin:${PATH}"

# 配置poetry多源兜底（阿里云+清华）
RUN poetry config repositories.aliyun https://mirrors.aliyun.com/pypi/simple/ \
    && poetry config repositories.tuna https://pypi.tuna.tsinghua.edu.cn/simple

# 全局禁用 Poetry 的虚拟环境创建
ENV POETRY_VIRTUALENVS_CREATE=false

# 增加 Poetry 的网络超时时间（单位：秒）
ENV POETRY_REQUESTS_TIMEOUT=300

# 清理 Poetry 缓存，以防旧缓存导致问题
RUN poetry cache clear . --all || echo "Poetry cache clear failed or no cache to clear, continuing..."

# 1. 安装主项目依赖（不包括 airtest 和 pocoui，它们应已从主依赖移除或通过 --without 排除）
#    使用 --sync 确保环境与 lock 文件一致
RUN echo "Starting Poetry core dependencies installation..." && \
    poetry install --no-root --sync \
    # 如果 airtest 和 pocoui 被定义在一个可选组（例如 'mobile-tools'）中,
    # 并且你不想让 poetry 尝试安装它们, 请取消下面一行的注释并修改组名:
    # --without mobile-tools \
    && echo "Poetry core dependencies installation step completed."

# 2. 验证核心依赖是否已成功安装
RUN echo "Verifying core dependencies..." && \
    poetry run pytest --version && \
    python -c "import yaml; print('PyYAML imported successfully by Poetry.')" && \
    poetry run playwright --version && \
    echo "Core dependencies verified successfully." \
    || (echo "CRITICAL ERROR: pytest, PyYAML, or Playwright library not found after poetry install!" && exit 1)

# 3. 单独使用 pip 安装 airtest 和 pocoui (使用国内镜像源)
RUN echo "Attempting to install airtest and pocoui via pip..." && \
    pip install airtest pocoui -i https://mirrors.aliyun.com/pypi/simple/ \
    || pip install airtest pocoui -i https://pypi.tuna.tsinghua.edu.cn/simple \
    || pip install airtest pocoui \
    && echo "Airtest and Pocoui pip installation step completed."

# 4. 安装 Playwright 浏览器驱动 (playwright 库本身应已由 poetry install 安装)
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
RUN echo "Installing Playwright browsers..." && \
    playwright install \
    && echo "Playwright browsers installation step completed."

# 复制本地下载的Allure CLI安装包到镜像
# 请确保 allure-2.27.0.zip 与 Dockerfile 在同一目录
COPY allure-2.27.0.zip /tmp/

RUN unzip /tmp/allure-2.27.0.zip -d /opt/ \
    && ln -s /opt/allure-2.27.0/bin/allure /usr/bin/allure \
    && rm /tmp/allure-2.27.0.zip \
    && echo "Allure CLI installed."

# 通常 Jenkinsfile 中的 docker run 命令会覆盖 CMD 或 ENTRYPOINT
# CMD ["python"]