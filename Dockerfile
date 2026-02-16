FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

RUN apt-get update && apt-get install -y cron && rm -rf /var/lib/apt/lists/*

RUN crontab /app/crontab

CMD ["cron", "-f"]
