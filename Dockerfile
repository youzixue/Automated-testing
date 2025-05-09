FROM python:3.11.9-slim

WORKDIR /app

# 先只复制依赖声明文件，利用缓存加速依赖安装
COPY pyproject.toml poetry.lock /app/

# 彻底清理和重置APT源为清华源
RUN rm -rf /etc/apt/sources.list.d/* && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm main contrib non-free non-free-firmware" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian bookworm-updates main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian-security bookworm-security main contrib non-free non-free-firmware" >> /etc/apt/sources.list && \
    apt-get clean && \
    apt-get update && apt-get install -y --no-install-recommends apt-transport-https ca-certificates && \
    apt-get update

# 安装系统依赖
RUN echo "Installing system dependencies..." && \
    apt-get install -y --no-install-recommends \
    wget openjdk-17-jre-headless unzip \
    libglib2.0-0 libnss3 libnspr4 \
    libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libexpat1 \
    libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 \
    libxcb1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 \
    fonts-liberation fonts-noto-cjk \
    libappindicator3-1 lsb-release \
    && apt-get clean && rm -rf /var/lib/apt/lists/* \
    && echo "System dependencies installed."

# 安装 Android SDK Platform Tools
COPY platform-tools-latest-linux.zip /tmp/platform-tools.zip
RUN echo "Installing Android SDK Platform Tools..." && \
    unzip /tmp/platform-tools.zip -d /opt && \
    rm /tmp/platform-tools.zip && \
    mv /opt/platform-tools /opt/android-sdk-platform-tools && \
    echo "Android SDK Platform Tools installed."
ENV PATH="/opt/android-sdk-platform-tools:${PATH}"

# 配置pip国内镜像源
RUN echo "Configuring pip mirror..." && \
    mkdir -p /root/.pip && \
    echo "[global]" > /root/.pip/pip.conf && \
    echo "index-url = https://mirrors.aliyun.com/pypi/simple/" >> /root/.pip/pip.conf && \
    echo "Pip mirror configured."

# 升级pip并安装poetry
RUN echo "Upgrading pip and installing poetry..." && \
    pip install --upgrade pip \
    && pip install "poetry>=1.5.0" \
    && echo "Poetry installed." \
    && echo "Attempting to find Poetry command right after pip install..." \
    && POETRY_PATH=$(command -v poetry) \
    && if [ -z "$POETRY_PATH" ]; then echo "Poetry command NOT FOUND immediately after pip install!"; else echo "Poetry command found at: $POETRY_PATH"; fi

# 尝试将常见的Python脚本路径添加到PATH (防御性措施)
ENV PATH="/root/.local/bin:/usr/local/bin:${PATH}"

# 强制验证 poetry 命令是否真的可用，如果不可用则构建失败
RUN echo "Verifying poetry command availability in PATH..." && \
    poetry --version \
    || (echo "CRITICAL ERROR: 'poetry --version' failed. Poetry command is not found or not executable. Check PATH and installation." && exit 1)
RUN echo "Poetry command verified successfully."

# 配置poetry国内镜像源
RUN echo "Configuring Poetry mirrors..." && \
    poetry config repositories.aliyun https://mirrors.aliyun.com/pypi/simple/ \
    && poetry config repositories.tuna https://pypi.tuna.tsinghua.edu.cn/simple \
    && echo "Poetry mirrors configured."

ENV POETRY_VIRTUALENVS_CREATE=false
ENV POETRY_REQUESTS_TIMEOUT=300

RUN echo "Clearing Poetry cache..." && \
    poetry cache clear . --all || echo "Poetry cache clear failed or no cache to clear, continuing..." && \
    echo "Poetry cache cleared."

# 1. 安装主项目依赖 (此步骤成功的前提是 pyproject.toml/poetry.lock 已正确处理 airtest/pocoui)
RUN echo "Starting Poetry core dependencies installation (pytest, pyyaml, playwright-lib, etc.)..." && \
    poetry install --no-root --sync \
    # 如果你将 airtest/pocoui 放在了名为 'mobile-tools' 的可选组中，请取消下一行的注释
    # --without mobile-tools \
    && echo "Poetry core dependencies installation step completed."

# 2. 验证核心依赖是否已通过 Poetry 成功安装
RUN echo "Verifying core dependencies installed by Poetry..." && \
    poetry run pytest --version && \
    python -c "import yaml; print('PyYAML imported successfully by Poetry.')" && \
    poetry run playwright --version && \
    echo "Core dependencies (pytest, PyYAML, Playwright lib) verified successfully." \
    || (echo "CRITICAL ERROR: One or more core dependencies (pytest, PyYAML, Playwright lib) NOT found after poetry install! Check poetry install logs." && exit 1)

# 3. 单独使用 pip 安装 airtest 和 pocoui (使用国内镜像源)
RUN echo "Attempting to install airtest and pocoui via pip..." && \
    pip install airtest pocoui -i https://mirrors.aliyun.com/pypi/simple/ \
    || pip install airtest pocoui -i https://pypi.tuna.tsinghua.edu.cn/simple \
    || pip install airtest pocoui \
    && echo "Airtest and Pocoui pip installation step completed."

# 4. 安装 Playwright 浏览器驱动
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright
RUN echo "Installing Playwright browsers..." && \
    playwright install \
    && echo "Playwright browsers installation step completed."

# 安装 Allure CLI
COPY allure-2.27.0.zip /tmp/
RUN echo "Installing Allure CLI..." && \
    unzip /tmp/allure-2.27.0.zip -d /opt/ \
    && ln -s /opt/allure-2.27.0/bin/allure /usr/bin/allure \
    && rm /tmp/allure-2.27.0.zip \
    && echo "Allure CLI installed."

# CMD ["python"]