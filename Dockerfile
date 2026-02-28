# AI News Publisher Dockerfile

FROM python:3.11-slim

LABEL maintainer="AI News Publisher"
LABEL description="AI News Aggregator and Auto-Publisher"

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p output cache

ENV PYTHONUNBUFFERED=1

EXPOSE 5000

CMD ["python", "main.py", "dashboard"]
