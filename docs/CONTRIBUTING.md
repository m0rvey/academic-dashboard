# 🤝 Руководство по Участию в Разработке (Contributing Guide)

Мы приветствуем любые идеи, исправления ошибок и улучшения для **Academic Dashboard**!  
Пожалуйста, ознакомьтесь с данным руководством перед началом работы над проектом.

---

## 📌 Как внести свой вклад

### 1. Сообщение об ошибках (Bug Reports)
Если вы обнаружили баг:
- Убедитесь, что проблема воспроизводится на последней версии ветки `main`.
- Проверьте [список открытых Issues](https://github.com/m0rvey/academic-dashboard/issues), чтобы избежать дубликатов.
- Создайте новый Issue, используя шаблон [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md).
- Укажите версию ОС, версию Python, подробные шаги воспроизведения и логи из `data/app.log`.

### 2. Предложение новых функций (Feature Requests)
- Создайте Issue с описанием предлагаемой функциональности через шаблон [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md).
- Опишите проблему, предлагаемое решение и возможные альтернативы.

---

## 🛠️ Настройка локального окружения

1. **Форкните и клонируйте репозиторий**:
   ```bash
   git clone https://github.com/<YOUR_GITHUB_USERNAME>/academic-dashboard.git
   cd academic-dashboard
   ```

2. **Создайте ветку для ваших изменений**:
   ```bash
   git checkout -b feature/my-awesome-feature
   # или для багфикса:
   git checkout -b fix/issue-description
   ```

3. **Создайте виртуальное окружение**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # На Windows: .venv\Scripts\activate
   ```

4. **Установите основные и dev-зависимости**:
   ```bash
   pip install -r requirements.txt
   pip install pytest pytest-asyncio ruff
   ```

5. **Настройте файл `.env` для тестирования**:
   ```bash
   cp .env.example .env
   # Укажите тестовые параметры TELEGRAM_BOT_TOKEN и TELEGRAM_ALLOWED_USERS
   ```

---

## 📐 Стандарты кода

- **Стиль и форматирование**:
  Проект использует [Ruff](https://github.com/astral-sh/ruff) с максимальной длиной строки 120 символов.
  ```bash
  # Проверка линтером
  ruff check .

  # Автоматическое форматирование
  ruff format .
  ```
- **Типизация**: Все новые функции и методы должны иметь аннотации типов аргументов и возвращаемых значений (`typing`, `Optional`, `List`, `Dict`).
- **Модели данных**: Для структурированных сущностей используйте модели `Pydantic v2`.
- **Безопасность**:
  - Никогда не используйте интерполяцию строк (f-строки) в SQL-запросах; используйте параметризацию `?`.
  - Все пользовательские строки, отправляемые в Telegram с `parse_mode="Markdown"`, должны экранироваться через `escape_md()`.

---

## 🧪 Запуск тестов

Перед отправкой изменений обязательно запустите тестовый набор:
```bash
# Запуск всех тестов
pytest -v

# Запуск конкретного тестового файла
pytest tests/test_logic.py -v
```

---

## 🚀 Процесс создания Pull Request

1. Убедитесь, что все тесты проходят без ошибок.
2. Проверьте отсутствие замечаний от `ruff check .`.
3. Сделайте коммит с понятным сообщением в формате [Conventional Commits](https://www.conventionalcommits.org/):
   ```bash
   git commit -m "feat(kanban): add drag-and-drop task reordering"
   # или
   git commit -m "fix(scheduler): prevent duplicate daily reminders"
   ```
4. Запушьте изменения в ваш форк:
   ```bash
   git push origin feature/my-awesome-feature
   ```
5. Откройте Pull Request в ветку `main` основного репозитория, заполнив форму по [шаблону PR](.github/pull_request_template.md).

---

## 📋 Чек-лист перед отправкой PR

- [ ] Код соответствует PEP 8 / Ruff.
- [ ] Добавлены юнит-тесты для нового функционала или багфикса.
- [ ] Все существующие тесты проходят успешно (`pytest`).
- [ ] Обновлена документация (`README.md`, `CODE_DOCUMENTATION.md`), если изменился API или интерфейс.
- [ ] В коммитах отсутствуют конфиденциальные данные (токены, реальные ID, дампы БД).
