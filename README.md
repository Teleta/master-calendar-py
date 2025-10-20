# MC - Master Calendar (MVP)

Минимально жизнеспособный Telegram-бот для составления недельного расписания.

## Требования

- Docker Desktop (Windows, Mac, Linux)
- Telegram-аккаунт для создания бота

---

## 1. Установка Docker Desktop (Windows)

1. Скачайте Docker Desktop с официального сайта:  
   [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Установите Docker Desktop и перезапустите компьютер, если потребуется.
3. Проверьте установку в PowerShell или CMD:

```powershell
docker --version
docker compose version
```

---

## 2. Создание Telegram-бота и получение токена

1. В Telegram найдите бота [BotFather](https://t.me/BotFather).
2. Отправьте команду `/newbot` и следуйте инструкциям.
3. После создания получите токен (строку вида `123456789:ABCDefGHIjklMNOpqRSTuvWXyz`).

---

## 3. Настройка окружения (Windows)

1. Создайте переменную окружения `BOT_TOKEN`:

```powershell
setx BOT_TOKEN "<YOUR_TELEGRAM_BOT_TOKEN>"
```

2. Перезапустите PowerShell/CMD, чтобы переменная вступила в силу:

```powershell
echo %BOT_TOKEN%
```
Должно вывести ваш токен.

---

## 4. Запуск бота через Docker

### Вариант 1: Сборка локального образа

```powershell
docker compose build
docker compose up -d
```

### Вариант 2: Использование готового образа из Docker Hub

```powershell
docker pull <YOUR_DOCKERHUB_USERNAME>/master-calendar-py-bot:latest
docker run --rm -e BOT_TOKEN="%BOT_TOKEN%" <YOUR_DOCKERHUB_USERNAME>/master-calendar-py-bot:latest
```

---

## 5. Проверка работы бота

1. Откройте Telegram и найдите своего бота по имени, которое вы указали при создании.
2. Отправьте команду `/start` — бот должен ответить приветственным сообщением с перечислением команд.
3. Попробуйте добавить событие через `/busy` или задачу через `/task` и убедитесь, что бот отвечает корректно.

---

## 6. Команды

- `/busy` — добавить событие (дата + время + подтверждение)
- `/task` — добавить задачу (название + длительность)
- `/schedule` — сгенерировать недельное расписание
- `/my_busy`, `/my_tasks` — просмотр ваших данных
- `/set_hours` — задать рабочие часы для планирования (например `8 17`)
- `/help` — вывести справку

---

## 7. Репозиторий

[https://github.com/Teleta/master-calendar-py](https://github.com/Teleta/master-calendar-py)