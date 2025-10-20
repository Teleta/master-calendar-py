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

# Копируем runtime-зависимости и устанавливаем их в отдельную папку
COPY requirements.txt ./
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Копируем код приложения
COPY . .

# -----------------------------
# Stage 2: Runtime (минифицированный)
# -----------------------------
FROM python:3.11-slim

WORKDIR /app

# Копируем только runtime-зависимости
COPY --from=builder /install /usr/local

# Копируем код приложения
COPY --from=builder /app /app

# Чистка кешей и временных файлов
RUN rm -rf /var/lib/apt/lists/* /root/.cache/pip /tmp/*

ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
