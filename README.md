# Academic Dashboard

Персональный планировщик учебной нагрузки для школьника. Три интерфейса (GUI / CLI / Telegram Bot) с единым ядром бизнес-логики.

## Возможности

- **CRUD задач** — предмет, описание, дедлайн, сложность 1-10, теги, статус
- **Smart Priority** — `P = effort_score / (days_left + 1) × exam_multiplier` (1.5 для ОГЭ/ЕГЭ/Экзамен)
- **Контроль нагрузки** — дневной лимит 10 ед. с предупреждениями
- **GPA калькулятор** — аналитическая формула O(1) без итераций
- **NLP-парсер** — ввод задач естественным языком на русском (`"домашка по физике лаба 3 на завтра сложность 4"`)
- **4 вкладки GUI** — Задачи, Статистика, Успеваемость, Календарь
- **Telegram-бот** — `/list`, `/load`, `/done`, `/add`, `/stats`, `/grades`, `/backup`, ежедневные напоминания
- **CLI-режим** — `python main.py --cli`
- Тёмная/светлая тема, импорт/экспорт JSON, ротация бэкапов, macOS-уведомления

## Стек

Python ≥3.10 / Flet 0.25.2 / Aiogram 3 / SQLite3 (WAL) / Pydantic v2

## Готовое приложение для macOS (Быстрый запуск)

Вы можете скачать и запустить скомпилированное приложение напрямую, без необходимости настраивать окружение Python:

1. Скачайте образ диска с готовым приложением: **[AcademicDashboard_macos_universal.dmg](releases/AcademicDashboard_macos_universal.dmg)**.
2. Откройте скачанный DMG-файл двойным кликом.
3. Перетащите приложение `Academic Dashboard.app` в папку **Программы** (`/Applications`).

> [!IMPORTANT]
> **Важно при первом запуске (macOS Gatekeeper):**
> Так как приложение собрано локально и не имеет коммерческой цифровой подписи Apple, при первом открытии macOS покажет предупреждение о том, что разработчика невозможно проверить.
> Чтобы разрешить запуск:
> 1. Откройте **Системные настройки** -> **Конфиденциальность и безопасность** (Privacy & Security).
> 2. Прокрутите вниз до раздела «Безопасность» и нажмите кнопку **Подтвердить вход** (Open Anyway) напротив «Academic Dashboard».
> 3. Или кликните правой кнопкой мыши по приложению в папке «Программы», выберите **Открыть**, а затем подтвердите запуск кнопкой **Открыть** в диалоговом окне.

4. Запустите приложение. При первом запуске появится приветственное окно настройки, где вам нужно будет указать:
   - **Токен Telegram-бота** (можно получить у [@BotFather](https://t.me/BotFather))
   - **Ваш Telegram Chat ID** (можно узнать через [@userinfobot](https://t.me/userinfobot))
5. Нажмите «Сохранить и запустить». Данные запишутся в безопасное хранилище `~/Library/Application Support/AcademicDashboard/.env`, Telegram-бот автоматически запустится в фоновом режиме, и откроется основной интерфейс дашборда.

### Удаление приложения

Если вам потребуется удалить приложение с вашего MacBook:
1. Перетащите `Academic Dashboard.app` из папки **Программы** в **Корзину** (Trash) и очистите её.
2. Чтобы стереть все пользовательские данные (базу данных с задачами, бэкапы и файлы конфигурации бота), удалите системную папку приложения с помощью Терминала:
   ```bash
   rm -rf ~/Library/Application\ Support/AcademicDashboard
   ```

## Установка из исходного кода

```bash
git clone https://github.com/m0rvey/academic-dashboard.git
cd academic-dashboard
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt pytest pytest-asyncio
```

## Запуск

```bash
# GUI
.venv/bin/python main.py

# CLI
.venv/bin/python main.py --cli

# Telegram Bot (требуется .env с TELEGRAM_BOT_TOKEN)
.venv/bin/python bot.py

# Тесты
TELEGRAM_BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz" PYTHONPATH=. .venv/bin/pytest tests/ -v
```

### Переменные окружения (.env)

Создайте файл `.env` в корневой директории:
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ALLOWED_USERS=123456789
TELEGRAM_ADMIN_USERS=123456789
```

## Архитектура

```
┌─────────────────────────────────────────────┐
│           Presentation Layer                │
│  CLI (main.py) │ Flet GUI │ Aiogram 3 Bot  │
├─────────────────────────────────────────────┤
│             Core Layer                      │
│  database.py │ logic.py │ models.py         │
│  nlp_parser.py │ grade_calculator.py        │
├─────────────────────────────────────────────┤
│         SQLite3 (WAL)  planner.db           │
└─────────────────────────────────────────────┘
```

## Структура проекта

```
academic-dashboard/
├── main.py                          # Точка входа GUI/CLI
├── bot.py                           # Точка входа Telegram-бота
├── src/
│   ├── bot/                         # Telegram Bot
│   │   ├── handlers/                # Команды (commands, tasks, dashboards, files)
│   │   ├── middlewares/             # Auth, RateLimit, Dependency Injection
│   │   ├── state.py                 # BotState — кэш для бота
│   │   ├── dependencies.py          # Синглтоны (bot, db, state)
│   │   └── scheduler.py            # Ежедневные напоминания
│   ├── core/                        # Ядро бизнес-логики
│   │   ├── database.py             # DatabaseManager (CRUD, N+1 prevention)
│   │   ├── logic.py                # Smart Priority, Daily Load
│   │   ├── models.py               # Pydantic Task + TaskStatus
│   │   ├── nlp_parser.py           # Regex NLP (русский, ООП)
│   │   ├── grade_calculator.py     # GPA target calculator O(1)
│   │   ├── migrations.py           # Schema v0 → v4
│   │   ├── config.py               # Константы
│   │   └── logger.py               # Logging
│   └── ui/                          # Flet GUI
│       ├── state.py                 # AppState — in-memory кэш
│       ├── views.py                 # Оркестратор GUI
│       ├── components/              # KPI-карточки, уведомления
│       ├── dialogs/                 # Диалоги добавления/удаления
│       └── tabs/                    # Задачи, Статистика, Успеваемость, Календарь
└── tests/                           # 86 тестов (pytest)
```

## Тесты

```bash
PYTHONPATH=. python -m pytest tests/ -v
```

| Модуль | Тестов | Покрытие |
|--------|--------|----------|
| `test_database.py` | 16 | CRUD, теги, JSON, ротация, агрегация |
| `test_logic.py` | 21 | Приоритет, нагрузка, NLP, GPA, валидация |
| `test_bot_auth.py` | 5 | AuthMiddleware |
| `test_bot_handlers.py` | 2 | Backup handler |
| `test_bot_handlers_extended.py` | 12 | /start, /load, /list, /done, /add, /stats, /grades |
| `test_bot_state.py` | 7 | Кэширование BotState |
| `test_throttling.py` | 7 | Rate limiting |
| `test_escape_md.py` | 16 | Markdown escaping |

## Качество кода

- **Linting & Formatting:** ruff (line-length=120)
- **Типизация:** полная (Pydantic v2, type hints)
- **DI:** DependencyMiddleware для Aiogram (тестируемые хендлеры)

## Безопасность

| Риск | Статус |
|------|--------|
| SQL Injection | ✅ Параметризованные запросы |
| Auth | ✅ Fail-Closed middleware, whitelist |
| Rate Limiting | ✅ RateLimitMiddleware (1s, memory cleanup) |
| Markdown XSS | ✅ escape_md для всех спецсимволов v1 |

## Обход блокировок Telegram в РФ

Если у вас возникают проблемы с подключением бота из-за ограничений Telegram в РФ, вы можете настроить прокси или кастомный API-сервер в настройках приложения (или в файле `~/Library/Application Support/AcademicDashboard/.env`).

### 1. Кастомный API-сервер (Реверс-прокси) — Рекомендуемый способ
Вместо прямого обращения к `api.telegram.org` приложение будет отправлять запросы через промежуточный сервер-прокси.

- **Публичные прокси** (использовать на свой страх и риск, могут быть нестабильны):
  Введите в поле **Кастомный API сервер**:
  `https://api.telegram-proxy.org/bot`
  или
  `https://tgproxy.uz/bot`

- **Собственный приватный прокси через Cloudflare Workers** (Рекомендуется: бесплатно, приватно, быстро):
  1. Зарегистрируйтесь на [Cloudflare](https://dash.cloudflare.com/) (это бесплатно).
  2. Перейдите в **Workers & Pages** -> **Create Application** -> **Create Worker**.
  3. Назовите воркер (например, `tg-proxy-worker`) и нажмите **Deploy**.
  4. Нажмите **Edit Code** и замените код в файле `worker.js` на следующий:
     ```javascript
     addEventListener('fetch', event => {
       event.respondWith(handleRequest(event.request))
     })

     async function handleRequest(request) {
       const url = new URL(request.url)
       url.hostname = 'api.telegram.org'
       // Если в начале пути дублируется /bot/bot, обрезаем один из них
       if (url.pathname.startsWith('/bot/bot')) {
         url.pathname = url.pathname.replace('/bot/bot', '/bot')
       }
       return fetch(url, request)
     }
     ```
  5. Нажмите **Deploy** в правом верхнем углу.
  6. Скопируйте адрес вашего воркера (например, `https://tg-proxy-worker.your-subdomain.workers.dev`).
  7. Вставьте этот URL в поле **Кастомный API сервер** в приложении (можно указывать как с `/bot` на конце, так и просто домен `https://tg-proxy-worker.your-subdomain.workers.dev` — бот поймет оба формата).

### 2. Использование HTTP / SOCKS5 прокси
В поле **Прокси-сервер** вы можете указать ваш собственный прокси-сервер:
- **HTTP/HTTPS прокси**: `http://ip:port` или `http://user:password@ip:port`
- **SOCKS5 прокси**: `socks5://ip:port` или `socks5://user:password@ip:port`

Благодаря библиотеке `aiohttp-socks`, приложение нативно поддерживает SOCKS4/5 прокси для Telegram бота.

## Лицензия

MIT

