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

## Установка

```bash
git clone https://github.com/m0rvey/academic-dashboard.git
cd academic-dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Запуск

```bash
# GUI
python main.py

# CLI
python main.py --cli

# Telegram Bot (требуется .env с TELEGRAM_BOT_TOKEN)
python bot.py

# Тесты
PYTHONPATH=. python -m pytest tests/ -v
```

### Переменные окружения (.env)

```
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

- **Linting:** ruff (line-length=120)
- **Formatting:** ruff-format
- **Pre-commit hooks:** ruff + ruff-format автоматически перед коммитом
- **Типизация:** полная (Pydantic v2, type hints)
- **DI:** DependencyMiddleware для Aiogram (тестируемые хендлеры)

## Безопасность

| Риск | Статус |
|------|--------|
| SQL Injection | ✅ Параметризованные запросы |
| Auth | ✅ Fail-Closed middleware, whitelist |
| Rate Limiting | ✅ RateLimitMiddleware (1s, memory cleanup) |
| Markdown XSS | ✅ escape_md для всех спецсимволов v1 |

## Лицензия

MIT
