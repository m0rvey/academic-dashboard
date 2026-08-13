import re

# Спецсимволы Telegram Markdown v1, требующие экранирования
_MD_V1_ESCAPE_CHARS = r"_*`[]()~>#+-=|{}.!"


def escape_md(text: str) -> str:
    """Экранирует специальные символы Telegram Markdown v1."""
    if not text:
        return text
    return re.sub(rf"([{re.escape(_MD_V1_ESCAPE_CHARS)}])", r"\\\1", str(text))


def mask_url_credentials(url: str) -> str:
    """Маскирует пароль в строке подключения прокси или URL."""
    if not url:
        return ""
    return re.sub(r"://([^:/@]+):(.*)@", r"://\1:***@", str(url))

