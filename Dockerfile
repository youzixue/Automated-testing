FROM ubuntu:22.04

WORKDIR /app

# 配置APT源为清华源
RUN rm -rf /etc/apt/sources.list.d/* && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy main restricted universe multiverse" > /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-updates main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-backports main restricted universe multiverse" >> /etc/apt/sources.list && \
    echo "deb https://mirrors.tuna.tsinghua.edu.cn/ubuntu/ jammy-security main restricted universe multiverse" >> /etc/apt/sources.list && \
    apt-get clean && \
    apt-get update

# 安装Python及必要工具
RUN apt-get install -y --no-install-recommends \
    python3.11 python3.11-dev python3.11-venv python3-pip python3-wheel \
    build-essential wget openjdk-17-jre-headless unzip \
    libglib2.0-0 libnss3 libnspr4 \
    libdbus-1-3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libexpat1 \
    libx11-6 libxcomposite1 libxdamage1 libxext6 libxfixes3 libxrandr2 libgbm1 \
    libxcb1 libxkbcommon0 libpango-1.0-0 libcairo2 libasound2 libatspi2.0-0 \
    fonts-liberation libappindicator3-1 lsb-release \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# 创建软链接 python -> python3.11
RUN ln -sf /usr/bin/python3.11 /usr/bin/python && \
    ln -sf /usr/bin/pip3 /usr/bin/pip

# 先只复制依赖声明文件，利用缓存加速依赖安装
COPY pyproject.toml poetry.lock /app/

# 配置pip多源兜底（阿里云+清华）
RUN mkdir -p /root/.pip && \
    echo "[global]" > /root/.pip/pip.conf && \
    echo "index-url = https://mirrors.aliyun.com/pypi/simple/" >> /root/.pip/pip.conf && \
    echo "[global]" > /root/.pip/pip_tuna.conf && \
    echo "index-url = https://pypi.tuna.tsinghua.edu.cn/simple" >> /root/.pip/pip_tuna.conf

# 升级pip并安装poetry
RUN pip install --upgrade pip \
    && pip install "poetry==1.8.4"

# 配置poetry多源兜底（阿里云+清华）
RUN poetry config repositories.aliyun https://mirrors.aliyun.com/pypi/simple/ \
    && poetry config repositories.tuna https://pypi.tuna.tsinghua.edu.cn/simple

# 增加 Poetry 的网络超时时间（单位：秒）
ENV POETRY_REQUESTS_TIMEOUT=300

# 安装项目依赖（--no-root表示只安装依赖，不安装当前项目）
RUN poetry install --no-root

# playwright浏览器下载加速（可选）
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright

# 安装playwright及其浏览器（多源兜底）
RUN pip install playwright -i https://mirrors.aliyun.com/pypi/simple/ \
    || pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && playwright install

# 复制全部项目代码（依赖已装好，代码变动不会导致依赖重装）
COPY . /app

# 复制本地下载的Allure CLI安装包到镜像
COPY allure-2.27.0.zip /tmp/

RUN unzip /tmp/allure-2.27.0.zip -d /opt/ \
    && ln -s /opt/allure-2.27.0/bin/allure /usr/bin/allure \
    && rm /tmp/allure-2.27.0.zip

CMD ["bash", "-c", "poetry run pytest --alluredir=output/allure-results && allure generate output/allure-results -o output/allure-report --clean"] 