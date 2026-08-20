# 🛡️ Security & Privacy Policy — Academic Dashboard

## 🔒 Security Posture

**Academic Dashboard** adheres to local-first privacy principles:
- **Local Database:** All task, grade, and schedule data resides in a local SQLite database file in WAL mode.
- **Bot Token Protection:** Telegram bot tokens are strictly isolated in `.env` and never committed or logged.
- **Access Control:** The Telegram bot supports whitelist authorization (`ALLOWED_USERS`) to prevent unauthorized access.

---

## 🚨 Reporting a Vulnerability

If you discover a security issue or vulnerability in **Academic Dashboard**:
- Report privately via the GitHub repository's **Security > Report a vulnerability** page, or
- Open an issue tagged `[Security]`.

All reports are reviewed promptly and confidentially.
