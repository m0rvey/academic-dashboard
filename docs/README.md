<div align="center">

# 🎓 Academic Dashboard

**Персональный планировщик учебной нагрузки, трекер дедлайнов и успеваемости в стиле macOS Cupertino с ассистентом в Telegram.**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![UI](https://img.shields.io/badge/UI-Flet%20(Cupertino)-7928CA?style=flat-square)](https://flet.dev/)
[![Telegram Bot](https://img.shields.io/badge/Telegram_Bot-Aiogram_3-2CA5E0?style=flat-square&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![Database](https://img.shields.io/badge/Database-SQLite3_WAL-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://sqlite.org/)
[![Linter](https://img.shields.io/badge/Linter-Ruff-black?style=flat-square&logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](../LICENSE)

[Возможности](#-ключевые-возможности) • [Архитектура](#-архитектура-системы) • [Быстрый запуск](#-быстрый-запуск) • [Shortcuts](#-горячие-клавиши-macos) • [English Version](README_EN.md)

</div>

---

## 📌 Обзор

**Academic Dashboard** объединяет десктопное приложение с нативным интерфейсом macOS Cupertino и интеллектуального Telegram-бота для управления академическими задачами. Проект использует единое ядро бизнес-логики и реактивную синхронизацию данных в реальном времени через SQLite в режиме WAL.

---

## ✨ Ключевые возможности

<table>
  <tr>
    <td width="50%" valign="top">
      <h4>🖥️ macOS GUI & Канбан-доска</h4>
      <ul>
        <li>Переключение между списком задач и интерактивной 3-колоночной Канбан-доской.</li>
        <li>Адаптивная Donut-диаграмма распределения нагрузки по дисциплинам.</li>
        <li>Темная обсидиановая тема Deep Slate (<code>#0B0F19</code>) и светлый режим.</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h4>🤖 Telegram-бот Ассистент (Aiogram 3)</h4>
      <ul>
        <li>Порядковая нумерация задач с инлайн-кнопками быстрых действий (<code>[⚡ #1 В процесс]</code>, <code>[✅ #1 Готово]</code>).</li>
        <li>Команда <code>/done</code> и мгновенные уведомления о дедлайнах.</li>
        <li>Реактивная синхронизация с десктопом без блокировки потоков.</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td width="50%" valign="top">
      <h4>🧮 Математическая приоритизация</h4>
      <ul>
        <li>Динамический скоринг приоритета на основе близости дедлайна, веса предмета и сложности.</li>
        <li>Автоматический подъем критических задач и экзаменационных тегов (<code>#ОГЭ</code>, <code>#ЕГЭ</code>, <code>#КР</code>).</li>
      </ul>
    </td>
    <td width="50%" valign="top">
      <h4>🎯 Аналитический калькулятор GPA</h4>
      <ul>
        <li>Точный расчет среднего балла в реальном времени.</li>
        <li>Аналитический расчет необходимого числа отличных оценок за <code>O(1)</code> без перебора («Сколько 5 нужно до балла 4.75»).</li>
      </ul>
    </td>
  </tr>
</table>

---

## 🗣️ NLP-парсер русского языка

Встроенный NLP-движок автоматически извлекает дату, время, предмет и тип задания из текста на естественном языке:
- *"Сдать расчетку по матану в пятницу в 18:00"* $\rightarrow$ Предмет: `Матан`, Тип: `Расчетка`, Дедлайн: `Ближайшая пятница 18:00`.
- *"Завтра лаба по физике сложность 8"* $\rightarrow$ Предмет: `Физика`, Тип: `Лабораторная`, Сложность: `8/10`.

---

## 🏛️ Архитектура системы

- **БД:** SQLite3 с включенным **WAL (Write-Ahead Logging)** для параллельного чтения и записи из бота и GUI.
- **Модель данных:** Строгая типизация через Python dataclasses / Pydantic.
- **Интерфейсы:** Десктопный GUI (Flet Cupertino), мобильный бот (Aiogram 3) и автономный CLI-режим.
- **Безопасность:** Нулевая облачная телеметрия, локальное хранение данных.

---

## 🚀 Быстрый запуск

### Требования
- Python 3.10+

```bash
# 1. Клонировать репозиторий
git clone https://github.com/m0rvey/academic-dashboard.git
cd academic-dashboard

# 2. Создать виртуальное окружение и установить зависимости
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Настроить окружение
cp .env.example .env
# Заполните TELEGRAM_BOT_TOKEN в .env (если используете бота)

# 4. Запустить приложение
python3 main.py        # Запуск десктопного GUI
python3 bot.py         # Запуск Telegram-бота
```

---

## ⌨️ Горячие клавиши (macOS)

| Шорткат | Действие |
| :--- | :--- |
| `⌘ + N` | Создать новую задачу |
| `⌘ + K` | Переключить режим (Список / Канбан) |
| `⌘ + F` | Фокус на строке поиска / фильтрации |
| `⌘ + T` | Сменить тему оформления (Dark / Light) |

---

## 🧪 Тестирование и Качество

```bash
# Запуск тестов
pytest

# Линтинг и проверка стиля
ruff check .
```

---

## 📄 Лицензия

Распространяется под лицензией **MIT**. См. [LICENSE](../LICENSE).  
Автор: [m0rvey](https://github.com/m0rvey).
