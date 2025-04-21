FROM python:3.11-slim

WORKDIR /app
COPY . /app

# 配置pip国内源
RUN mkdir -p /root/.pip && \
    echo -e "[global]\nindex-url = https://pypi.tuna.tsinghua.edu.cn/simple" > /root/.pip/pip.conf

# 升级pip并安装poetry
RUN pip install --upgrade pip \
    && pip install "poetry>=1.5.0"

# 配置poetry国内源（可选）
RUN poetry config repositories.tuna https://pypi.tuna.tsinghua.edu.cn/simple

# 安装项目依赖和playwright
RUN poetry install \
    && pip install playwright -i https://pypi.tuna.tsinghua.edu.cn/simple \
    && playwright install

# playwright浏览器下载加速（可选）
ENV PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright

# 安装Allure CLI
RUN apt-get update && apt-get install -y wget openjdk-11-jre-headless unzip \
    && wget https://github.com/allure-framework/allure2/releases/download/2.27.0/allure-2.27.0.zip \
    && unzip allure-2.27.0.zip -d /opt/ \
    && ln -s /opt/allure-2.27.0/bin/allure /usr/bin/allure \
    && rm allure-2.27.0.zip

CMD ["bash", "-c", "pytest --alluredir=output/allure-results && allure generate output/allure-results -o output/allure-report --clean"]