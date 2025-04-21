FROM python:3.11-slim

WORKDIR /app
COPY . /app

# 配置pip国内源
RUN mkdir -p /root/.pip && \
    echo "[global]" > /root/.pip/pip.conf && \
    echo "index-url = https://pypi.tuna.tsinghua.edu.cn/simple" >> /root/.pip/pip.conf

# 升级pip并安装poetry
RUN pip install --upgrade pip \
    && pip install "poetry>=1.5.0"

# 配置poetry国内源（加速，保险起见）
RUN poetry config repositories.tuna https://pypi.tuna.tsinghua.edu.cn/simple

# 安装项目依赖（会自动走pyproject.toml里配置的tuna源）
RUN poetry install

# playwright浏览器下载加速（可选）
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright

# 安装playwright及其浏览器
RUN pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple \
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