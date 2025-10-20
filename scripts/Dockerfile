FROM python:3.12-slim


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


WORKDIR /app


COPY src/backend/requirements.txt ./src/backend/requirements.txt
RUN pip install --upgrade pip && pip install -r src/backend/requirements.txt


COPY . .


CMD ["uvicorn", "src.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

