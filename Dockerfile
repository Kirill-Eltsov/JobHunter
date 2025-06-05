# Build stage
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .

# Установка зависимостей для psycopg2 (если нужно)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# venv для изоляции
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim

WORKDIR /app

# Копирование venv из builder
COPY --from=builder /opt/venv /opt/venv

# Копирование только нужных файлов
COPY . .

# Обновление PATH
ENV PATH=/opt/venv/bin:$PATH

# Запуск бота
CMD ["python", "main.py"]