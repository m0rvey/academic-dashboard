# 🎓 Academic Dashboard

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flet](https://img.shields.io/badge/UI-Flet_0.25.2-purple.svg)](https://flet.dev/)
[![Aiogram](https://img.shields.io/badge/Telegram_Bot-Aiogram_3-blue.svg)](https://docs.aiogram.dev/)
[![SQLite](https://img.shields.io/badge/Database-SQLite3_WAL-green.svg)](https://sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-96_passed_100%25-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **Personal academic workload planner and grade analytics system for students.**  
> Features **three seamless interfaces** (Cross-Platform GUI / Interactive CLI / Telegram Bot) driven by a unified, highly modular core.

---

[ **English** | [Русский](README_RU.md) ]

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [System Architecture](#-system-architecture)
- [Mathematical Formulas & Logic](#-mathematical-formulas--logic)
  - [Smart Task Priority](#smart-task-priority)
  - [GPA & Target Grade Analytics](#gpa--target-grade-analytics)
- [Natural Language Processing (NLP)](#-natural-language-processing-nlp)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables (`.env`)](#environment-variables-env)
- [Usage Modes](#-usage-modes)
  - [Graphical User Interface (GUI)](#1-graphical-user-interface-gui)
  - [Interactive Command Line (CLI)](#2-interactive-command-line-cli)
  - [Telegram Bot](#3-telegram-bot)
- [Testing & Quality Assurance](#-testing--quality-assurance)
- [Documentation & Architecture](#-documentation--architecture)
- [License](#-license)

---

## ✨ Key Features

- 📝 **Task Management (CRUD)** — Subject, description, deadline, effort score (1–10 scale), tags, and status tracking (TODO / DOING / DONE).
- ⚡ **Smart Priority Scoring** — Dynamic priority calculation prioritizing urgent deadlines, heavy workloads, and crucial exam subjects (OGE / EGE / Final Exams).
- 📊 **Workload Balance Control** — Daily recommended workload limit (10 units max) with visual progress indicators and overflow warnings.
- 🎯 **GPA & Grade Target Analytics** — Constant-time \(O(1)\) analytical calculator predicting exact required grades to reach target GPAs.
- 🗣️ **Russian Natural Language Parser** — Add tasks effortlessly in natural spoken Russian (e.g., `"домашка по физике лаба 3 на завтра сложность 4"`).
- 🖥️ **4-Tab Desktop Interface & Hotkeys** — Built with Flet featuring Dark/Light themes, JSON import/export, macOS system notifications (`osascript`), and hotkeys (`Cmd+N`, `Cmd+F`, `Cmd+R`, `Cmd+T`).
- 🤖 **Interactive Telegram Bot** — Aiogram 3 bot with FSM task creation, inline task action buttons (`[⚡ DOING]`, `[✅ DONE]`, `[🗑️ DELETE]`), custom `/settings` reminder hours, role authorization (fail-closed), daily automated reminders, and database backups.
- 🔄 **Real-Time APFS Observer** — Reactive file-system watcher (`watchdog`) with timestamp triggers (`.db_change`), syncing GUI instantly when bot tasks change.
- 💻 **Standalone CLI Mode** — Fully functional terminal user interface for server environments or low-resource systems.


---

## 🏗️ System Architecture

The codebase enforces a clean separation of concerns, decoupling storage, logic, and interface layers:

```
academic-dashboard/
├── main.py                  # Primary application entry point (GUI / CLI launcher)
├── bot.py                   # Telegram bot process launcher & thread runner
├── pyproject.toml           # Project metadata & linter configuration (Ruff)
├── requirements.txt         # Production dependencies
├── data/                    # SQLite database and app runtime log directory
├── src/
│   ├── core/                # Business logic, algorithms, models, and DB layer
│   │   ├── config.py        # Central configuration constants
│   │   ├── interfaces.py    # Abstract base interfaces (IDatabaseManager)
│   │   ├── logic.py         # Priority calculations & GPA algorithms
│   │   ├── models.py        # Pydantic Task model validation & Enums
│   │   ├── nlp_parser.py    # Natural language parsing engine
│   │   ├── migrations.py    # SQLite schema migrations
│   │   └── database/        # Modular Repository Pattern Layer
│   │       ├── connection.py        # SQLite connection manager (WAL mode, Foreign Keys)
│   │       ├── task_repository.py   # Task CRUD, filtering, tags & SQL priority sorting
│   │       ├── grade_repository.py  # Grade statistics & subject GPA aggregations
│   │       ├── stats_repository.py  # KPI metrics & 7-day workload distributions
│   │       ├── backup_manager.py    # JSON export/import & local backup rotation
│   │       ├── user_repository.py   # Telegram bot user authorization storage
│   │       └── manager.py           # Unified DatabaseManager facade
│   ├── ui/                  # Flet Desktop GUI Layer
│   │   ├── constants.py     # Theme color tokens & styling constants
│   │   ├── state.py         # Reactive AppState cache
│   │   ├── components/      # UI components (KPI cards, Task cards, Desktop notifications)
│   │   ├── dialogs/         # Modals (Add/Edit task, Delete confirmation)
│   │   ├── tabs/            # Tab views (Tasks, Analytics, Grades, Calendar)
│   │   └── views/           # Modular view screens (Main Dashboard, Log Console)

│   └── bot/                 # Aiogram 3 Telegram Bot Layer
│       ├── dependencies.py  # Bot instance & configuration loader
│       ├── scheduler.py     # Async daily reminder scheduler
│       ├── state.py         # In-memory bot cache
│       ├── middlewares/     # RateLimit throttling, Auth, Dependency injection
│       └── handlers/        # Command routers (/start, /add, /list, /stats, /grades, /backup)
└── tests/                   # Pytest test suite (92 tests covering DB, Bot, Logic, UI)
```

---

## 🧮 Mathematical Formulas & Logic

### Smart Task Priority

Each task's priority \(P\) is dynamically evaluated using the formula:

$$P = \frac{\text{effort\_score}}{\text{days\_left} + 1} \times \text{exam\_multiplier}$$

Where:
- **`effort_score`**: Task difficulty rating on a scale of $1$ (Very Easy) to $10$ (Extreme).
- **`days_left`**: Days remaining until the deadline ($\max(0, \text{deadline} - \text{today})$).
- **`exam_multiplier`**: Set to $1.5$ if the task contains exam tags (`ОГЭ`, `ЕГЭ`, `Экзамен`), otherwise $1.0$.

### GPA & Target Grade Analytics

To achieve a desired average grade $G_{\text{target}}$ given $N$ existing grades with sum $S$, the system computes the exact minimum number of additional straight 5s ($K_5$) needed in constant time $O(1)$:

$$K_5 = \left\lceil \frac{G_{\text{target}} \cdot N - S}{5 - G_{\text{target}}} \right\rceil$$

---

## 🗣️ Natural Language Processing (NLP)

The built-in Russian NLP parser converts free-form sentences into validated structured `Task` objects:

```text
Input:  "домашка по физике лаба 3 на завтра сложность 4 ОГЭ"
Parsed: Subject = "Физика"
        Description = "Лаба 3"
        Deadline = tomorrow's date (YYYY-MM-DD)
        Effort Score = 4
        Tags = ["ОГЭ"]
```

Key capabilities:
- **Relative Date Recognition**: `"сегодня"`, `"завтра"`, `"послезавтра"`, `"через 3 дня"`.
- **Subject Extraction**: Recognizes school subjects and common abbreviations (`маша`/`математика`, `физра`, `обж`, `лит-ра`).
- **Difficulty Inference**: Extracts numbers following keywords like `"сложность"`, `"сложность:"`, `"уровень"`.

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** installed on your system.
- **Git** for repository cloning.

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/m0rvey/academic-dashboard.git
   cd academic-dashboard
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt pytest pytest-asyncio ruff
   ```

### Environment Variables (`.env`)

Create a `.env` file in the root directory:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_ALLOWED_USERS=123456789
TELEGRAM_ADMIN_USERS=123456789
# Optional Proxy settings for Russia/constrained environments:
# TELEGRAM_PROXY=socks5://username:password@ip:port
# TELEGRAM_API_SERVER=https://tg-proxy-worker.username.workers.dev
```

---

## 💻 Usage Modes

### 1. Graphical User Interface (GUI)

Launch the interactive desktop interface:

```bash
.venv/bin/python main.py
```

Features:
- **Tasks Tab**: Filter by status/tag, search, sort by priority/deadline/effort, inline edit & completion.
- **Analytics Tab**: Visual charts for subject workload, 7-day completion velocity, and KPI summaries.
- **Grades Tab**: GPA distribution, subject grade tracker, target grade forecasting.
- **Calendar Tab**: Month grid view showing scheduled task deadlines.
- **Debug Console**: Click the Telegram Bot status badge to view live system logs and diagnostics.

### 2. Interactive Command Line (CLI)

Launch terminal mode:

```bash
.venv/bin/python main.py --cli
```

Provides an interactive console menu to add tasks, list items sorted by priority, inspect daily workload, and manage task statuses.

### 3. Telegram Bot

Launch the Telegram bot independently:

```bash
.venv/bin/python bot.py
```

Available Bot Commands:
- `/start` — Register user & view welcome instructions.
- `/add` — Start interactive multi-step FSM task creation.
- `/list` — View active tasks sorted by priority with inline quick-completion buttons.
- `/stats` — Show KPI statistics dashboard.
- `/grades` — View GPA summary & performance overview.
- `/load` — Inspect current daily workload vs recommended limit.
- `/backup` — Generate & receive database JSON backup (Admin only).
- `/cancel` — Cancel current bot operation.

---

## 🧪 Testing & Quality Assurance

The project includes a comprehensive suite of **92 automated unit and integration tests** covering all modules:

Run the full test suite:
```bash
PYTHONPATH=. .venv/bin/pytest tests/ -v
```

Run static code analysis and linting:
```bash
.venv/bin/ruff check .
```

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

Copyright (c) 2026 **m0rvey**
