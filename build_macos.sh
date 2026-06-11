#!/bin/bash

# Скрипт для сборки Academic Dashboard в macOS .app
# Для запуска используйте команду: bash build_macos.sh

echo "📦 Начинаем сборку приложения для macOS..."

# Активируем виртуальное окружение
source .venv/bin/activate

# Проверяем, установлен ли flet
if ! command -v flet &> /dev/null; then
    echo "⚠️ flet не найден! Выполняю pip install -r requirements.txt..."
    pip install -r requirements.txt
fi

echo "🚀 Упаковка приложения с помощью flet pack..."
# --name "Academic Dashboard" задаст имя приложению
# --icon "assets/icon.icns" можно добавить позже, если появится иконка
# Добавляем --add-data "src:src" и т.д., если flet pack их сам не захватит. 
# Но обычно Flet pack работает через PyInstaller, который сканирует импорты. 

flet pack main.py --name "Academic Dashboard" --product-name "Academic Dashboard" --bundle-id "com.student.academicdashboard" -y

echo "✅ Сборка завершена!"
echo "📂 Приложение находится в директории: dist/"
echo "Вы можете найти файл 'Academic Dashboard.app' там и переместить его в папку Applications (Программы)."
