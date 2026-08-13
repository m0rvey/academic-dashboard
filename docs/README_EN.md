# 🎓 Academic Dashboard — Full Documentation

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![UI](https://img.shields.io/badge/UI-Flet_0.25.2_(Cupertino)-purple.svg)](https://flet.dev/)
[![Telegram Bot](https://img.shields.io/badge/Telegram_Bot-Aiogram_3-blue.svg)](https://docs.aiogram.dev/)
[![Database](https://img.shields.io/badge/Database-SQLite3_WAL-green.svg)](https://sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-99_passed_100%25-brightgreen.svg)](../tests/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](../LICENSE)

> **A personal academic workload and grade analytics dashboard designed in native macOS Cupertino style.**  
> Features 3 seamless interfaces: macOS Desktop GUI with Kanban Board, Aiogram 3 Telegram Bot, and Terminal CLI.

---

[ 🇷🇺 [Русская версия](README.md) | 🇬🇧 **English** ]

---

## 📑 Table of Contents

1. [Overview & Core Capabilities](#1-overview--core-capabilities)
2. [macOS Graphical User Interface](#2-macos-graphical-user-interface)
3. [Kanban Board & Quick Filters](#3-kanban-board--quick-filters)
4. [Telegram Bot & Smart Task IDs](#4-telegram-bot--smart-task-ids)
5. [Mathematical Models & Algorithms](#5-mathematical-models--algorithms)
6. [Natural Language Parser (NLP)](#6-natural-language-parser-nlp)
7. [Architecture & Modules](#7-architecture--modules)
8. [Installation & Setup](#8-installation--setup)
9. [macOS Keyboard Shortcuts](#9-macos-keyboard-shortcuts)
10. [Roadmap & Ideas](#10-roadmap--ideas)

---

## 1. Overview & Core Capabilities

- **Task CRUD**: Create, read, update, and delete tasks with subjects, descriptions, deadlines, effort scores (1–10), tags, and grades (2–5).
- **Dynamic Prioritization**: Automated priority scoring balancing urgency, complexity, and exam relevance (`ОГЭ`, `ЕГЭ`, `Exam`).
- **Workload Management**: Daily effort meter with customizable limits (default: 10 units) and overload alerts.
- **Academic Performance**: GPA calculation, grade distribution charts, and an analytical \(O(1)\) target grade calculator.
- **Dynamic Themes**: Deep Space Obsidian dark theme (`#0B0F19`) and clean light theme (`#FFFFFF`).
- **Real-Time Synchronization**: `watchdog` SQLite observer providing immediate data sync between GUI and Telegram bot.

---

## 2. macOS Graphical User Interface

Designed following macOS Cupertino design tokens:

- **Left Navigation Sidebar**:
  - Brand header and icon.
  - Quick action "New Task" button (`Cmd+N`).
  - Navigation destinations with dynamic active task badges.
  - Telegram bot status indicator (`🟢 Active` / `🔴 Inactive`) with 1-click auto-restart.
  - Keyboard shortcuts helper trigger (`Cmd+/`).
- **Topbar Action Bar**:
  - Daily workload progress bar.
  - JSON Backup Export and Import buttons.
  - Dynamic theme toggle (`Cmd+T`).

---

## 3. Kanban Board & Quick Filters

The **Tasks** tab features two viewing modes:

### Quick Filter Chips:
`[All Tasks]` | `[🔥 Urgent]` | `[📅 Today]` | `[🚨 Overdue]` | `[🎓 Exams]` | `[✅ Completed]`

### View Modes:
1. **List Mode**: Organized by urgency sections ("Overdue", "Today", "Upcoming", "Completed") with humanized countdown capsules.
2. **Kanban Board**: 3 interactive vertical columns:
   - **To Do (TODO)**: 1-click `[⚡ Start]` button.
   - **In Progress (DOING)**: `[To Plan]` and `[✅ Done]` buttons.
   - **Done (DONE)**: `[Return]` button and quick grade selection dropdown (`5`, `4`, `3`, `2`).

---

## 4. Telegram Bot & Smart Task IDs

Powered by **Aiogram 3** for streamlined mobile task management:

- **Sequential Numbering**: Tasks in `/list` and reminder digests are numbered `1.`, `2.`, `3.` instead of database IDs.
- **Smart `/done` Command**:
  - `/done` (no arguments) — displays an interactive inline keyboard for 1-tap completion.
  - `/done 1` — completes the first task directly.
- **Command List**:
  - `/start`, `/help` — Help and registration.
  - `/list` — Active task list with action buttons.
  - `/done [N]` — Complete a task.
  - `/load` — Inspect today's workload.
  - `/stats` — KPI analytics dashboard.
  - `/grades` — GPA score and grade breakdown.
  - `/add` — Task creation (NLP or FSM wizard).
  - `/settings` — Reminder notification schedule.
  - `/backup` — SQLite database dump.
  - `/cancel` — Abort active operations.

---

## 5. Mathematical Models & Algorithms

### Smart Priority Formula

$$P = \frac{\text{effort\_score}}{\text{days\_left} + 1} \times \text{exam\_multiplier}$$

- $\text{effort\_score} \in [1, 10]$
- $\text{days\_left} = \max(0, \text{deadline} - \text{today})$
- $\text{exam\_multiplier} = 1.5$ for exam tags, otherwise $1.0$.

### Analytical GPA Simulator ($O(1)$)

Minimum count of grade 5 marks ($K_5$) needed to reach target GPA $G_{\text{target}}$:

$$K_5 = \left\lceil \frac{G_{\text{target}} \cdot N - S}{5 - G_{\text{target}}} \right\rceil$$

Where $N$ is the total count of existing grades and $S$ is their sum.

---

## 6. Natural Language Parser (NLP)

The `src/core/nlp_parser.py` module converts freeform text into structured `Task` models:

```text
Input:  "math homework lab 3 due friday effort 4 exam"
Output: Subject: "Math"
        Description: "Lab 3"
        Deadline: "YYYY-MM-DD (next Friday)"
        Effort: 4
        Tags: ["Exam"]
```

---

## 7. Architecture & Modules

```
src/
├── core/
│   ├── config.py           # Configuration and .env validation
│   ├── models.py           # Pydantic Task and TaskStatus models
│   ├── logic.py            # Priority, workload, and GPA algorithms
│   ├── nlp_parser.py       # Natural language parsing engine
│   └── database/           # SQLite repositories (Repository Pattern)
├── ui/
│   ├── constants.py        # Design tokens and theme palettes
│   ├── state.py            # AppState cache with dirty tracking
│   ├── components/         # TaskCard, KanbanCard, KPICard
│   ├── dialogs/            # AddEditDialog, DeleteDialog, ShortcutsDialog
│   ├── tabs/               # TasksTab, StatsTab, GradesTab, CalendarTab
│   └── views/              # MainView and DebugConsole
└── bot/
    ├── dependencies.py     # Bot instance initialization
    ├── scheduler.py        # Daily reminder digest scheduler
    ├── middlewares/        # Rate limiting and authentication
    └── handlers/           # Command and callback handlers
```

---

## 8. Installation & Setup

```bash
# 1. Clone repository
git clone https://github.com/m0rvey/academic-dashboard.git
cd academic-dashboard

# 2. Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt pytest pytest-asyncio ruff

# 4. Run GUI
.venv/bin/python main.py

# 5. Run CLI
.venv/bin/python main.py --cli
```

---

## 9. macOS Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `Cmd + N` | Open New Task dialog |
| `Cmd + F` | Focus search input |
| `Cmd + R` | Refresh data |
| `Cmd + T` | Toggle Light / Dark theme |
| `Cmd + 1..4` | Switch navigation tabs |
| `Cmd + /` | Open shortcuts help modal |

---

## 10. Roadmap & Ideas

1. **🌐 WebDAV / iCloud Sync** — Serverless cloud database synchronization.
2. **🎙️ Voice Task Creation** — Transcribe voice messages in Telegram bot using Whisper.
3. **📅 Apple / Google Calendar (.ics) Export** — Sync exams and deadlines with native calendars.
4. **🤖 AI Study Plan Generator** — Automated project decomposition.
5. **📲 Telegram WebApp Dashboard** — Interactive mini-app inside Telegram.

---

## 📜 License
MIT License (c) 2026 **m0rvey**
