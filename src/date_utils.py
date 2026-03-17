import re
from typing import Optional


def resolve_meal_date(meal_date_hint: Optional[str], eaten_at: Optional[str]) -> Optional[str]:
    if eaten_at and len(eaten_at) >= 10:
        return eaten_at[:10]

    if not meal_date_hint:
        return None

    if re.match(r"^\d{4}-\d{2}-\d{2}$", meal_date_hint):
        return meal_date_hint

    return None
