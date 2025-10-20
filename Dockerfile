# -----------------------------
# Stage 1: Builder
# -----------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

# Системные зависимости только для сборки
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Обновляем pip, setuptools, wheel
RUN python -m pip install --upgrade pip setuptools wheel

# Копируем requirements и устанавливаем зависимости в отдельную папку
COPY requirements.txt ./
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# -----------------------------
# Stage 2: Runtime
# -----------------------------
FROM python:3.11-slim

WORKDIR /app

# Копируем только зависимости из билд-стадии
COPY --from=builder /install /usr/local

# Копируем код приложения
COPY . .

# Отключаем буферизацию stdout/stderr
ENV PYTHONUNBUFFERED=1

# Точка входа
CMD ["python", "app.py"]
