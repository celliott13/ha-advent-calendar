"""Pure calendar logic (no Home Assistant imports, so it is trivially testable)."""
from __future__ import annotations

from datetime import date, timedelta

from . import const
from .const import FAMILY_ADVENT, FAMILY_MENORAH

ADVENT_DAYS = 25
MENORAH_DAYS = 8


def family_for_design(design: str) -> str:
    """Return the calendar family used by a design."""
    return FAMILY_MENORAH if design == "menorah" else FAMILY_ADVENT


def days_in_family(family: str) -> int:
    return MENORAH_DAYS if family == FAMILY_MENORAH else ADVENT_DAYS


def hanukkah_first_day(gregorian_year: int) -> date:
    """Gregorian date of 25 Kislev (first full day of Hanukkah) in the given year.

    Hanukkah begins at sundown the evening before this date.
    """
    from pyluach import dates  # imported lazily; declared in manifest requirements

    hebrew_year = dates.HebrewDate.from_pydate(date(gregorian_year, 12, 15)).year
    # pyluach numbers months from Nisan = 1, so Kislev = 9.
    return dates.HebrewDate(hebrew_year, 9, 25).to_pydate()


def build_days(family: str, year: int) -> list[dict]:
    """Return [{day, date}] for a calendar family and year."""
    if family == FAMILY_MENORAH:
        # Door n = night n. Night 1 is the evening BEFORE 25 Kislev (Hanukkah begins at sundown),
        # so each door is dated by the civil date on which that night's candle is lit.
        start = date(year, const.TEST_MONTH, 5) if const.TEST_MONTH else hanukkah_first_day(year) - timedelta(days=1)
        return [
            {"day": n, "date": (start + timedelta(days=n - 1)).isoformat()}
            for n in range(1, MENORAH_DAYS + 1)
        ]
    return [
        {"day": n, "date": date(year, const.TEST_MONTH or 12, n).isoformat()}
        for n in range(1, ADVENT_DAYS + 1)
    ]


def door_available(door_date: str, today: date) -> bool:
    """A door can be opened on its date or any later date (catch-up allowed)."""
    return date.fromisoformat(door_date) <= today
