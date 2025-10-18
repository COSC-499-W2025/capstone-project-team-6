FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y curl build-essential \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY src/backend/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

WORKDIR /app/src/frontend
RUN npm install && npm rebuild rollup --force

RUN npm install -g concurrently wait-on cross-env

WORKDIR /app

CMD ["bash", "-c", "concurrently 'uvicorn src.backend.main:app --host 0.0.0.0 --port 8000' 'npm --prefix src/frontend run dev'"]
