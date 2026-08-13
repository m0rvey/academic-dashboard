import importlib
import subprocess
import sys

import flet as ft
from dotenv import load_dotenv

from src.core.config import ENV_PATH
from src.ui.constants import BG_CARD


def render_setup_view(page: ft.Page, on_complete) -> None:
    """Отображает экран первоначальной настройки токена и Chat ID бота."""
    page.clean()
    page.title = "Academic Dashboard - Настройка"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    token_input = ft.TextField(
        label="Токен Telegram-бота",
        hint_text="123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
        password=True,
        can_reveal_password=True,
        border_color=ft.Colors.LIGHT_BLUE_400,
        border_radius=10,
        width=450,
        helper_text="Получите токен у @BotFather",
    )
    chat_id_input = ft.TextField(
        label="Ваш Telegram Chat ID",
        hint_text="123456789",
        border_color=ft.Colors.LIGHT_BLUE_400,
        border_radius=10,
        width=450,
        helper_text="Только цифры. ID вашего аккаунта (можно узнать у @userinfobot)",
    )
    proxy_input = ft.TextField(
        label="Прокси-сервер (Опционально)",
        hint_text="http://username:password@ip:port или socks5://...",
        border_color=ft.Colors.LIGHT_BLUE_400,
        border_radius=10,
        width=450,
        helper_text="Для обхода блокировок Telegram (HTTP/SOCKS5)",
    )
    api_server_input = ft.TextField(
        label="Кастомный API сервер (Опционально)",
        hint_text="https://tg-proxy-worker.username.workers.dev",
        border_color=ft.Colors.LIGHT_BLUE_400,
        border_radius=10,
        width=450,
        helper_text="Адрес прокси/воркера",
    )

    def save_credentials(e):
        token_val = token_input.value.strip()
        chat_id_val = chat_id_input.value.strip()
        proxy_val = proxy_input.value.strip()
        api_server_val = api_server_input.value.strip()

        if api_server_val:
            if not (api_server_val.startswith("http://") or api_server_val.startswith("https://")):
                api_server_val = "https://" + api_server_val

        if not token_val or not chat_id_val:
            page.open(ft.SnackBar(ft.Text("❌ Пожалуйста, заполните оба обязательных поля!")))
            return

        try:
            ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(ENV_PATH, "w", encoding="utf-8") as f:
                f.write(f"TELEGRAM_BOT_TOKEN={token_val}\n")
                f.write(f"TELEGRAM_ALLOWED_USERS={chat_id_val}\n")
                f.write(f"TELEGRAM_ADMIN_USERS={chat_id_val}\n")
                if proxy_val:
                    f.write(f"TELEGRAM_PROXY={proxy_val}\n")
                if api_server_val:
                    f.write(f"TELEGRAM_API_SERVER={api_server_val}\n")

            load_dotenv(dotenv_path=ENV_PATH, override=True)

            modules_to_reload = [
                "src.bot.dependencies",
                "src.bot.middlewares.auth",
                "src.bot.middlewares.dependencies",
                "src.bot.middlewares.throttling",
                "src.bot.handlers.commands",
                "src.bot.handlers.dashboards",
                "src.bot.handlers.files",
                "src.bot.handlers.tasks",
                "src.bot.scheduler",
                "bot",
            ]

            for mod_name in modules_to_reload:
                if mod_name in sys.modules:
                    importlib.reload(sys.modules[mod_name])

            try:
                from bot import start_bot_in_thread
                start_bot_in_thread()
            except Exception:
                pass

            try:
                subprocess.Popen(["afplay", "/System/Library/Sounds/Glass.aiff"])
            except Exception:
                pass

            page.open(ft.SnackBar(ft.Text("✅ Настройки успешно сохранены! Запуск бота...")))
            on_complete()
        except Exception as ex:
            page.open(ft.SnackBar(ft.Text(f"❌ Ошибка сохранения: {ex}")))

    setup_card = ft.Container(
        content=ft.Column(
            [
                ft.Icon(ft.Icons.AUTO_STORIES_ROUNDED, size=60, color=ft.Colors.LIGHT_BLUE_200),
                ft.Text(
                    "Academic Dashboard",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.LIGHT_BLUE_200,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Text(
                    "Добро пожаловать! Пожалуйста, укажите токен Telegram-бота и ваш Telegram Chat ID, чтобы начать работу с приложением.",
                    size=14,
                    color=ft.Colors.GREY_400,
                    text_align=ft.TextAlign.CENTER,
                ),
                ft.Divider(color=ft.Colors.GREY_800, height=20),
                token_input,
                chat_id_input,
                proxy_input,
                api_server_input,
                ft.Text(
                    "💡 Проблемы с работой бота? Настройте прокси или кастомный API сервер. Инструкции см. в README.md.",
                    size=11,
                    color=ft.Colors.GREY_500,
                    text_align=ft.TextAlign.CENTER,
                    width=450,
                ),
                ft.Container(height=5),
                ft.ElevatedButton(
                    text="Сохранить и запустить",
                    on_click=save_credentials,
                    bgcolor=ft.Colors.LIGHT_BLUE_600,
                    color=ft.Colors.WHITE,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=10),
                    ),
                    width=450,
                    height=45,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=15,
        ),
        bgcolor=BG_CARD,
        padding=40,
        border_radius=16,
        border=ft.border.all(1, ft.Colors.GREY_800),
        width=500,
    )

    page.add(
        ft.Container(
            content=setup_card,
            alignment=ft.alignment.center,
            expand=True,
        )
    )
    page.update()
