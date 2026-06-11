import re

# Спецсимволы Telegram Markdown v1, требующие экранирования
_MD_V1_ESCAPE_CHARS = r"_*`[]()~>#+-=|{}.!"


def escape_md(text: str) -> str:
    """Экранирует специальные символы Telegram Markdown v1."""
    if not text:
        return text
    return re.sub(rf"([{re.escape(_MD_V1_ESCAPE_CHARS)}])", r"\\\1", str(text))
