# 🎓 Academic Dashboard (macOS & Telegram)

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![UI](https://img.shields.io/badge/UI-Flet_0.25.2_(Cupertino)-purple.svg)](https://flet.dev/)
[![Telegram Bot](https://img.shields.io/badge/Telegram_Bot-Aiogram_3-blue.svg)](https://docs.aiogram.dev/)
[![Database](https://img.shields.io/badge/Database-SQLite3_WAL-green.svg)](https://sqlite.org/)
[![Code Style](https://img.shields.io/badge/Code_Style-Ruff_0.9-black.svg)](https://github.com/astral-sh/ruff)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

> **A personal academic workload and grade analytics dashboard designed in native macOS Cupertino style.**  
> Features **3 interfaces** (macOS Desktop GUI with Kanban Board / Aiogram 3 Telegram Bot / Terminal CLI) with a unified domain core and real-time synchronization.

---

[ 🇷🇺 [Русская версия (Russian)](README.md) | 🇬🇧 **English Version** | 📚 [Code Documentation](CODE_DOCUMENTATION.md) | 💡 [Design Philosophy](DESIGN_PHILOSOPHY.md) ]

---

## 📑 Table of Contents

- [✨ Core Features](#-core-features)
- [🖥️ macOS Graphical Interface](#️-macos-graphical-interface)
- [🤖 Telegram Bot](#-telegram-bot)
- [🧮 Mathematical Models & Algorithms](#-mathematical-models--algorithms)
- [🗣️ Natural Language Task Parser](#️-natural-language-task-parser)
- [🏗️ System Architecture](#️-system-architecture)
- [🚀 Quick Start](#-quick-start)
  - [Requirements](#requirements)
  - [Installation](#installation)
  - [Configuring `.env`](#configuring-env)
- [⌨️ macOS Keyboard Shortcuts](#️-macos-keyboard-shortcuts)
- [🧪 Testing](#-testing)
- [🤝 Contributing](#-contributing)
- [📜 License](#-license)

---

## ✨ Core Features

- 📋 **Comprehensive Task & Deadline Management** — Full CRUD lifecycle, priorities, effort scores (1–10), tags (`#Exam`, `#Homework`), and statuses (`TODO`, `DOING`, `DONE`).
- 🗂️ **Dual View Modes** — Instant 1-click toggle between an urgency-grouped structured list and an interactive **3-column Kanban Board**.
- ⚡ **Dynamic Prioritization** — Real-time priority calculations: tasks with close deadlines, high effort, and exam tags surface to the top.
- 🍩 **Modern Analytics** — Donut chart of subject workload with center indicator, 7-day completion trend, and tag radar.
- 🎯 **GPA & Target Calculator** — Accurate GPA tracking and a closed-form $O(1)$ target grade calculator (*"How many A grades needed to reach a 4.75 GPA?"*).
- 🌓 **Dynamic Themes (Dark / Light)** — Deep Slate obsidian dark mode (`#0B0F19`) and clean light mode (`#FFFFFF`).
- 🤖 **Telegram Bot with Smart Task IDs** — Sequential task numbering (`1.`, `2.`), quick action buttons `[⚡ #1 In Progress]`, `[✅ #1 Done]`, and interactive `/done`.
- 🔄 **Reactive Synchronization** — Instant two-way synchronization between GUI and Telegram bot via SQLite WAL mode and file observers.
- 💻 **Terminal CLI Mode** — Full-featured interactive CLI for headless operation.

---

## 🖥️ macOS Graphical Interface

Designed following Apple Human Interface Guidelines:

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│  Academic Dashboard                                                      [—] [□] [✕]      │
├─────────────────┬────────────────────────────────────────────────────────────────────────┤
│ 🎓 Academic     │ ⚡ Daily Workload: 4 / 10 pts. [████████░░░░] 40%      [📥] [📤] [🌓]   │
│    Dashboard    ├────────────────────────────────────────────────────────────────────────┤
│                 │ [🔍 Search (Cmd+F)...] [Status ▼] [Tags ▼] [Sort ▼]    [📋] [🗂️] [🔄]│
│ ➕ New Task     │ [ All Tasks ] [ 🔥 Urgent ] [ 📅 Today ] [ 🚨 Overdue ]                │
│                 │                                                                        │
│ NAVIGATION      │ ┌─ To Do (2) ────────┐  ┌─ In Progress (1) ─┐  ┌─ Completed (4) ─────┐ │
│ 📝 Tasks    (3) │ │ 📕 Mathematics     │  │ 📘 Physics        │  │ 📗 History          │ │
│ 📊 Statistics   │ │    Lab Work 4      │  │    Exam Prep      │  │    Chapter Summary  │ │
│ 🎓 Grades (GPA) │ │ [⚡ Tomorrow] [⚡ 4]│  │ [🔥 Today!]       │  │ [Grade: 5 ▼]        │ │
│ 📅 Calendar     │ │ [⚡ Start]         │  │ [To Plan] [✅Done]│  │ [↩️ Return]         │ │
│                 │ └────────────────────┘  └───────────────────┘  └─────────────────────┘ │
│ ─────────────── │                                                                        │
│ 🟢 Bot Active   │                                                                        │
│ [ ⌨️ Cmd+/ ]    │                                                                        │
└─────────────────┴────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Telegram Bot

Powered by **Aiogram 3** for on-the-go mobile task management:

- **Humanized Sequential IDs**: Tasks are presented with priority order indices (`1.`, `2.`).
- **Interactive `/done` Command**:
  - `/done` — displays inline buttons for 1-tap task completion.
  - `/done 1` — completes the first task directly.
- **Bot Commands**:
  | Command | Description |
  | :--- | :--- |
  | `/start`, `/help` | Greeting and full command reference |
  | `/list` | Interactive active task list with action buttons |
  | `/done [N]` | Mark task as completed (1-tap or by number) |
  | `/load` | Inspect today's workload versus limit |
  | `/stats` | KPI summary, subject breakdown, and tag loads |
  | `/grades` | GPA score and grade breakdown (5/4/3/2) |
  | `/add [text]` | Natural language task addition or FSM dialog |
  | `/settings` | Configure daily morning digest delivery hour |
  | `/backup` | Export SQLite database backup (admin only) |
  | `/cancel` | Cancel active creation wizard |

---

## 🧮 Mathematical Models & Algorithms

### 1. Dynamic Priority Formula
$$\text{Priority} = \frac{\text{effort\_score}}{\max(0, \text{days\_left}) + 1} \times M_{\text{exam}}$$
- $\text{days\_left} = \text{deadline} - \text{today}$
- $M_{\text{exam}} = 1.5$ for exam tags (`ОГЭ`, `ЕГЭ`, `Exam`), otherwise $1.0$.

### 2. Analytical GPA Target Calculator ($O(1)$)
$$k = \max\left(0, \left\lceil \frac{T \cdot N - S}{5 - T} \right\rceil\right)$$
- $N$ — total existing grades count, $S$ — sum of all grades, $T$ — target GPA ($T < 5$).

---

## 🗣️ Natural Language Task Parser

Allows creating tasks with freeform natural language text:
> *"Record physics lab 3 due tomorrow effort 4 #Exam"*

Automatically extracts:
- 📚 **Subject**: `Physics`
- 📝 **Description**: `Lab 3`
- 📅 **Deadline**: Calculated date (`2026-08-15`)
- 💪 **Effort**: `4` (range 1–10)
- 🏷️ **Tags**: `["Exam"]`

---

## 🏗️ System Architecture

Detailed developer architecture available in [CODE_DOCUMENTATION.md](CODE_DOCUMENTATION.md).

```
┌───────────────────────────────────────────────────────────┐
│                          User                             │
└───────────────┬───────────────────────────┬───────────────┘
                │                           │
         [ Flet Desktop GUI ]      [ Aiogram 3 Telegram Bot ]
                │                           │
                └─────────────┬─────────────┘
                              │
                    [ DatabaseManager Facade ]
                              │
            ┌─────────────────┴─────────────────┐
            │   SQLite3 Database (WAL-mode)     │
            │   - tasks, tags, task_tags, users │
            └───────────────────────────────────┘
```

---

## 🚀 Quick Start

### Requirements
- Python **3.10+** (tested on 3.10, 3.11, 3.12)
- macOS, Linux, or Windows

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/m0rvey/academic-dashboard.git
   cd academic-dashboard
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Configuring `.env`

Copy the environment template:
```bash
cp .env.example .env
```

Edit credentials in `.env`:
```ini
# Telegram Bot Token (from @BotFather)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Allowed Telegram Chat IDs (comma-separated, from @userinfobot)
TELEGRAM_ALLOWED_USERS=123456789

# Telegram Admin IDs (optional)
TELEGRAM_ADMIN_USERS=123456789
```

4. **Run the application**:
   ```bash
   # Launch Desktop GUI (with background Telegram bot)
   python main.py

   # Or launch in interactive Terminal CLI mode
   python main.py --cli

   # Or run Telegram bot in standalone mode
   python bot.py
   ```

---

## ⌨️ macOS Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| <kbd>Cmd</kbd> + <kbd>N</kbd> | Open New Task dialog |
| <kbd>Cmd</kbd> + <kbd>F</kbd> | Focus search field |
| <kbd>Cmd</kbd> + <kbd>R</kbd> | Force reload data |
| <kbd>Cmd</kbd> + <kbd>T</kbd> | Toggle Dark / Light theme |
| <kbd>Cmd</kbd> + <kbd>B</kbd> | Start / restart Telegram bot |
| <kbd>Cmd</kbd> + <kbd>/</kbd> | Open keyboard shortcuts help modal |
| <kbd>1</kbd> .. <kbd>4</kbd> | Switch navigation tabs |

---

## 🧪 Testing

Run unit and integration test suite:
```bash
pytest -v
```

Code style check:
```bash
ruff check .
```

---

## 🤝 Contributing

Contributions are welcome! Please review [CONTRIBUTING.md](CONTRIBUTING.md) and adhere to our [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

---

## 📜 License

This project is licensed under the **MIT License**. See [LICENSE](LICENSE) for details.
