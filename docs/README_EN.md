<div align="center">

# 🎓 Academic Dashboard

**Personal workload planner, deadline tracker, and academic GPA manager in macOS Cupertino style with Telegram bot integration.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![UI](https://img.shields.io/badge/UI-Flet%20(Cupertino)-7928CA?style=flat-square)](https://flet.dev/)
[![Telegram Bot](https://img.shields.io/badge/Telegram_Bot-Aiogram_3-2CA5E0?style=flat-square&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![Database](https://img.shields.io/badge/Database-SQLite3_WAL-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Linter](https://img.shields.io/badge/Linter-Ruff-black?style=flat-square&logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](../LICENSE)

[Features](#-key-features) • [Architecture](#-architecture) • [Quick Start](#-quick-start) • [Shortcuts](#-macos-keyboard-shortcuts) • [Русская версия (Основная)](README.md)

</div>

---

## 📌 Overview

**Academic Dashboard** bridges a native macOS desktop interface with an asynchronous Telegram assistant for comprehensive academic workload management. Built with a shared core domain layer and synchronized in real time via SQLite in WAL mode.

---

## ✨ Key Features

<table>
  <tr>
    <td width="50%" valign="top">
      <h4>🖥️ macOS GUI & Kanban Board</h4>
      <ul>
        <li>1-click toggle between structured task lists and a 3-column Kanban board.</li>
        <li>Adaptive Donut chart showing workload distribution across subjects.</li>
        <li>Obsidian Deep Slate dark theme (<code>#0B0F19</code>) and clean light mode.</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h4>🤖 Telegram Assistant (Aiogram 3)</h4>
      <ul>
        <li>Sequential task numbering with inline quick actions (<code>[⚡ #1 Doing]</code>, <code>[✅ #1 Done]</code>).</li>
        <li>Smart <code>/done</code> command and proactive deadline reminders.</li>
        <li>Thread-safe real-time synchronization with desktop client.</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h4>🧮 Mathematical Prioritization</h4>
      <ul>
        <li>Dynamic priority scoring combining deadline proximity, subject weight, and complexity.</li>
        <li>Automatic surfacing of high-stakes exam and assignment tags.</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h4>🎯 Analytical GPA Calculator</h4>
      <ul>
        <li>Real-time grade point average tracking.</li>
        <li>Analytical <code>O(1)</code> target grade calculator without brute-force loops ("How many 5s needed to hit 4.75").</li>
      </ul>
    </td>
  </tr>
</table>

---

## 🗣️ Russian NLP Task Parser

Built-in NLP engine extracts date, time, subject, and assignment type from natural language input:
- *"Сдать расчетку по матану в пятницу в 18:00"* $\rightarrow$ Subject: `Math`, Type: `Assignment`, Deadline: `This Friday 18:00`.
- *"Завтра лаба по физике сложность 8"* $\rightarrow$ Subject: `Physics`, Type: `Lab`, Complexity: `8/10`.

---

## 🏛️ Architecture

- **Storage:** SQLite3 with **Write-Ahead Logging (WAL)** for concurrent read/write access.
- **Data Modeling:** Strict type contracts via Python dataclasses and Pydantic.
- **Interfaces:** macOS Desktop GUI (Flet Cupertino), Mobile Bot (Aiogram 3), and autonomous CLI.
- **Privacy:** 100% local persistence with zero external telemetry.

---

## 🚀 Quick Start

### Requirements
- Python 3.10+

```bash
# 1. Clone repository
git clone https://github.com/m0rvey/academic-dashboard.git
cd academic-dashboard

# 2. Setup virtual environment & dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Set TELEGRAM_BOT_TOKEN in .env (if running the bot)

# 4. Launch applications
python3 main.py        # Launch desktop GUI
python3 bot.py         # Launch Telegram bot
```

---

## ⌨️ macOS Keyboard Shortcuts

| Shortcut | Action |
| :--- | :--- |
| `⌘ + N` | Create new task |
| `⌘ + K` | Toggle view mode (List / Kanban) |
| `⌘ + F` | Focus search and filter input |
| `⌘ + T` | Toggle theme (Dark / Light) |

---

## 🧪 Testing & Quality

```bash
# Run pytest suite
pytest

# Run Ruff linter
ruff check .
```

---

## 📄 License

Distributed under the **MIT License**. See [LICENSE](../LICENSE) for details.  
Crafted by [m0rvey](https://github.com/m0rvey).
