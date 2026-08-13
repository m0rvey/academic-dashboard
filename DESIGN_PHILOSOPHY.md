# 💡 Design Philosophy & Architecture Values: Academic Dashboard

This document outlines the core ideology, architectural principles, and design trade-offs behind Academic Dashboard.

---

## 🎯 1. Mission & Core Values

Academic Dashboard is built around **four foundational principles**:

1. **Student Workload & Mental Health Protection**:
   - Students often suffer from burnout due to hidden task stacking. The system explicitly quantifies effort (`effort_score`) and enforces a daily load limit ($10$ units max), warning students before overloading themselves.

2. **Cross-Interface Harmony Without Overhead**:
   - Students need to manage tasks both sitting at their Mac (Desktop GUI) and on-the-go (Telegram Bot).
   - Rather than deploying complex cloud web servers, Academic Dashboard uses a **Zero-Server Architecture**: SQLite WAL mode + file observer triggers (`.db_change`).

3. **Privacy & Data Ownership First**:
   - Student data stays 100% private on local storage. No third-party tracking, no external SaaS dependencies, and easy 1-click JSON backup/export.

4. **Zero-Friction Ergonomics**:
   - Support for natural spoken Russian input (NLP parser), 1-click interactive inline Telegram buttons (`[⚡ DOING]`, `[✅ DONE]`, `[🗑️ DELETE]`), and fast desktop hotkeys (`Cmd+N`, `Cmd+F`, `Cmd+R`, `Cmd+T`).

---

## 🏛️ 2. Architectural Decisions & Trade-Offs

### Single Source of Truth
- Both the Telegram Bot daemon and Flet GUI access the same local SQLite database file `data/planner.db`.
- SQLite WAL mode ensures non-blocking concurrent reads and writes.

### Reactive Watchdog vs Heavy Polling
- Polling databases drains MacBook battery and consumes CPU cycles.
- The `watchdog` file observer puts the application thread to sleep until the OS kernel fires an `FSEvents` / `kqueue` notification triggered by `.db_change`.

### Fail-Closed Security Model
- Access control checks `TELEGRAM_ALLOWED_USERS`. If `.env` is unconfigured or unauthorized users attempt access, the bot fails closed, refusing input.
