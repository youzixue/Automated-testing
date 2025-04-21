FROM python:3.11-slim

WORKDIR /app
COPY . /app

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

# 增加 Poetry 的网络超时时间（单位：秒）
ENV POETRY_REQUESTS_TIMEOUT=300

# 安装项目依赖（pyproject.toml里配置多源）
RUN poetry install

# playwright浏览器下载加速（可选）
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright

# 安装playwright及其浏览器（多源兜底）
RUN pip install playwright -i https://mirrors.aliyun.com/pypi/simple/ \
    || pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && playwright install

# 安装Playwright和Allure CLI所需的全部系统依赖
RUN apt-get update && apt-get install -y \
    wget openjdk-11-jre-headless unzip \
    libglib2.0-0 libgobject-2.0-0 libnss3 libnssutil3 libsmime3 libnspr4 \
    libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libgio-2.0-0 libexpat1 \
    libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 \
    libxcb1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 libatspi0 \
    fonts-liberation libappindicator3-1 lsb-release \
    && wget https://github.com/allure-framework/allure2/releases/download/2.27.0/allure-2.27.0.zip \
    && unzip allure-2.27.0.zip -d /opt/ \
    && ln -s /opt/allure-2.27.0/bin/allure /usr/bin/allure \
    && rm allure-2.27.0.zip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

CMD ["bash", "-c", "pytest --alluredir=output/allure-results && allure generate output/allure-results -o output/allure-report --clean"]