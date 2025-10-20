FROM python:3.11-slim

WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y git && \
    python -m pip install --upgrade pip setuptools wheel && \
    apt-get clean

# Обновляем pip, setuptools, wheel — чтобы избежать проблем с установкой последних пакетов
RUN python -m pip install --upgrade pip setuptools wheel

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get remove -y git && \
    apt-get autoremove -y && \
    apt-get clean

# Чистим кеш apt
RUN rm -rf /var/lib/apt/lists/*

# Копируем код приложения
COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["python", "app.py"]
