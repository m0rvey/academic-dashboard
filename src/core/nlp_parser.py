import re
from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import Any, Dict, List, Optional, Tuple

from src.core.config import EXAM_TAGS, MAX_EFFORT, MIN_EFFORT

SUBJECTS_MAP: Dict[str, str] = {
    "однкнр": "ОДНКНР",
    "изо": "ИЗО",
    "англ": "Английский язык",
    "астр": "Астрономия",
    "алг": "Математика",
    "био": "Биология",
    "гео": "География",
    "черч": "Черчение",
    "труд": "Технология",
    "прог": "Программирование",
    "физр": "Физкультура",
    "общ": "Обществознание",
    "хим": "Химия",
    "инф": "Информатика",
    "ист": "История",
    "лит": "Литература",
    "мат": "Математика",
    "рус": "Русский язык",
    "физ": "Физика",
}

WEEKDAYS_MAP: Dict[str, int] = {
    "понедельник": 0,
    "вторник": 1,
    "сред": 2,
    "четверг": 3,
    "пятниц": 4,
    "суббот": 5,
    "воскресен": 6,
}


class BaseParser(ABC):
    @abstractmethod
    def parse(self, text: str) -> Tuple[str, Any]:
        """Parses the text, returns (remaining_text, extracted_value)."""
        pass


class EffortParser(BaseParser):
    def parse(self, text: str) -> Tuple[str, int]:
        text_lower = text.lower()
        effort = MIN_EFFORT
        effort_match = re.search(r"(?:сложность|нагрузка|сложностью)\s*(\d+)", text_lower)
        if not effort_match:
            effort_match = re.search(r"(\d+)\s*(?:сложность|нагрузка|сложностью)", text_lower)

        if effort_match:
            try:
                val = int(effort_match.group(1))
                if MIN_EFFORT <= val <= MAX_EFFORT:
                    effort = val
                text = text[: effort_match.start()] + text[effort_match.end() :]
            except ValueError:
                pass
        else:
            date_spans = [m.span() for m in re.finditer(r"\b\d{4}-\d{2}-\d{2}\b", text_lower)]
            nums = []
            for m in re.finditer(r"\b(\d+)\b", text_lower):
                start, end = m.span()
                if any(ds[0] <= start < ds[1] for ds in date_spans):
                    continue
                try:
                    v = int(m.group(1))
                    if MIN_EFFORT <= v <= MAX_EFFORT:
                        nums.append((v, start, end))
                except ValueError:
                    pass
            if nums:
                val, start_idx, end_idx = nums[-1]
                effort = val
                text = text[:start_idx] + text[end_idx:]

        return text.strip(), effort


class DeadlineParser(BaseParser):
    def parse(self, text: str) -> Tuple[str, str]:
        text_lower = text.lower()
        deadline = (date.today() + timedelta(days=1)).isoformat()

        in_days_match = re.search(r"\bчерез\s+(\d+)\s+(дн|нед)", text_lower)
        if in_days_match:
            count = int(in_days_match.group(1))
            unit = in_days_match.group(2)
            days_to_add = count * 7 if unit.startswith("нед") else count
            deadline = (date.today() + timedelta(days=days_to_add)).isoformat()
            text = text[: in_days_match.start()] + text[in_days_match.end() :]
            return text.strip(), deadline

        in_one_match = re.search(r"\bчерез\s+(день|неделю)\b", text_lower)
        if in_one_match:
            unit = in_one_match.group(1)
            days_to_add = 7 if unit == "неделю" else 1
            deadline = (date.today() + timedelta(days=days_to_add)).isoformat()
            text = text[: in_one_match.start()] + text[in_one_match.end() :]
            return text.strip(), deadline

        date_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", text_lower)
        if date_match:
            deadline = date_match.group(1)
            text = text[: date_match.start()] + text[date_match.end() :]
            return text.strip(), deadline

        replacements = [(r"\b(?:на\s+)?послезавтра\b", 2), (r"\b(?:на\s+)?завтра\b", 1), (r"\b(?:на\s+)?сегодня\b", 0)]
        for pattern, days in replacements:
            match = re.search(pattern, text_lower)
            if match:
                deadline = (date.today() + timedelta(days=days)).isoformat()
                text = text[: match.start()] + text[match.end() :]
                return text.strip(), deadline

        if re.search(r"\b(?:до|к)\s+концу\s+недели\b", text_lower):
            today = date.today()
            days_ahead = 6 - today.weekday()
            if days_ahead < 0:
                days_ahead += 7
            deadline = (today + timedelta(days=days_ahead)).isoformat()
            text = re.sub(r"\b(?:до|к)\s+концу\s+недели\b", "", text, flags=re.IGNORECASE)
            return text.strip(), deadline

        for day_name, weekday_num in WEEKDAYS_MAP.items():
            pattern = rf"\b(?:в\s+|во\s+|на\s+)?(?:следующ[а-яё]+\s+)?{day_name}\w*\b"
            match = re.search(pattern, text_lower)
            if match:
                today = date.today()
                days_ahead = weekday_num - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                if "следующ" in match.group(0):
                    days_ahead += 7
                deadline = (today + timedelta(days_ahead)).isoformat()
                text = text[: match.start()] + text[match.end() :]
                return text.strip(), deadline

        return text.strip(), deadline


class SubjectParser(BaseParser):
    def parse(self, text: str) -> Tuple[str, Optional[str]]:
        text_lower = text.lower()
        subject = None

        sub_match = re.search(r"\bпо\s+([а-яё]+)\b", text_lower)
        if sub_match:
            candidate = sub_match.group(1)
            for prefix, subj_name in SUBJECTS_MAP.items():
                if candidate.startswith(prefix):
                    subject = subj_name
                    text = text[: sub_match.start()] + text[sub_match.end() :]
                    break
            if not subject:
                subject = candidate.capitalize()
                text = text[: sub_match.start()] + text[sub_match.end() :]
            return text.strip(), subject

        words = re.finditer(r"\b[а-яё]+\b", text_lower)
        for match in words:
            w = match.group(0)
            for prefix, subj_name in SUBJECTS_MAP.items():
                if w.startswith(prefix):
                    subject = subj_name
                    text = text[: match.start()] + text[match.end() :]
                    return text.strip(), subject

        return text.strip(), subject


class TagsParser(BaseParser):
    def parse(self, text: str) -> Tuple[str, List[str]]:
        tags = []

        hashtag_matches = list(re.finditer(r"#([a-zA-Zа-яА-ЯёЁ0-9_]+)", text))
        for match in reversed(hashtag_matches):
            tag_val = match.group(1)
            tags.append(tag_val.capitalize())
            text = text[: match.start()] + text[match.end() :]

        explicit_tag_matches = list(
            re.finditer(r"\b(?:тег|хэштег)\s+([a-zA-Zа-яА-ЯёЁ0-9_]+)\b", text, flags=re.IGNORECASE)
        )
        for match in reversed(explicit_tag_matches):
            tag_val = match.group(1)
            tags.append(tag_val.capitalize())
            text = text[: match.start()] + text[match.end() :]

        words = re.findall(r"\b[a-zA-Zа-яА-ЯёЁ0-9]+\b", text.lower())
        for tag in EXAM_TAGS:
            tag_lower = tag.lower()
            if tag_lower == "экзамен":
                if any(w.startswith("экзамен") for w in words) and "Экзамен" not in tags:
                    tags.append("Экзамен")
            elif tag_lower in words and tag not in tags:
                tags.append(tag)

        # Reverse to keep original order if needed, but append is fine
        return text.strip(), tags


class DescriptionCleaner(BaseParser):
    def parse(self, text: str) -> Tuple[str, str]:
        stop_patterns = [
            r"^надо\b",
            r"^нужно\b",
            r"^необходимо\b",
            r"\bзапиши\b",
            r"\bдобавь\b",
            r"\bдомашка\b",
            r"\bдомашнюю\s+работу\b",
            r"\bдомашнее\s+задание\b",
            r"\bдомашк[ау]\b",
            r"\bзадач[ау]\b",
            r"\bпожалуйста\b",
        ]
        for pattern in stop_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        text = re.sub(r"\s+", " ", text).strip()
        text = re.sub(r"^[:,\-\s]+|[:,\-\s]+$", "", text).strip()
        return text, text


def parse_natural_language_task(text: str) -> Optional[Dict[str, Any]]:
    if not text.strip():
        return None

    orig_text = text
    text, effort = EffortParser().parse(text)
    text, deadline = DeadlineParser().parse(text)
    text, subject = SubjectParser().parse(text)
    text, tags = TagsParser().parse(text)
    text, _ = DescriptionCleaner().parse(text)

    if not subject:
        words = re.findall(r"\b[a-zA-Zа-яА-ЯёЁ]+\b", orig_text)
        cleaned_words = [
            w for w in words if w.lower() not in ("запиши", "добавь", "домашка", "задача", "задачу", "на", "в", "во")
        ]
        if cleaned_words:
            first_w = cleaned_words[0]
            for prefix, subj_name in SUBJECTS_MAP.items():
                if first_w.lower().startswith(prefix):
                    subject = subj_name
                    break
            if not subject:
                subject = first_w.capitalize()
                text = re.sub(rf"\b{first_w}\b", "", text, count=1, flags=re.IGNORECASE).strip()
        else:
            subject = "Другое"

    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"^[:,\-\s]+|[:,\-\s]+$", "", text).strip()

    description = text if text else "Выполнить задание"

    return {
        "subject": subject,
        "description": description.capitalize(),
        "deadline": deadline,
        "effort_score": effort,
        "tags": tags,
    }
