FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install poetry \
    && poetry install \
    && pip install playwright \
    && playwright install

CMD ["pytest", "--alluredir=output/allure-results"]