FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

COPY src/frontend/package*.json ./
RUN npm ci

COPY src/frontend/ ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libclang-dev \
    tesseract-ocr \
    poppler-utils \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
COPY src/backend/requirements.txt ./backend-requirements.txt

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r backend-requirements.txt

RUN apt-get update && apt-get install -y \
    texlive-latex-base \
    texlive-fonts-recommended \
    texlive-fonts-extra \
    texlive-latex-extra \
    && rm -rf /var/lib/apt/lists/*

COPY src/ ./src/
COPY setup.py ./

COPY --from=frontend-builder /frontend/dist ./src/frontend/dist

RUN mkdir -p /app/src/backend/uploads && \
    mkdir -p /app/analysis_results

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "-m", "uvicorn", "backend.api_server:app", "--host", "0.0.0.0", "--port", "8000"]
