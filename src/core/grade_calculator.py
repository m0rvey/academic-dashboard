import math
from typing import List, Optional


def calculate_needed_grades(current_grades: List[int], target: float, planned_grade: int = 5) -> Optional[int]:
    """Вычисляет количество оценок planned_grade, необходимых для достижения среднего балла target.

    Возвращает None, если достичь целевого балла невозможно.
    """
    if not current_grades:
        return 1 if planned_grade >= target else None

    current_sum = sum(current_grades)
    n = len(current_grades)
    current_avg = current_sum / n

    if current_avg >= target:
        return 0

    if planned_grade <= target:
        return None

    # Уравнение: (current_sum + k * planned_grade) / (n + k) >= target
    # k >= (target * n - current_sum) / (planned_grade - target)
    k = (target * n - current_sum) / (planned_grade - target)
    return int(math.ceil(k))
