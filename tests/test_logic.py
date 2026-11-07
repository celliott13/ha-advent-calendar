from datetime import date

from custom_components.advent_calendar.calendar_logic import (
    build_days, door_available, family_for_design, hanukkah_first_day,
)


def test_family():
    assert family_for_design("winter") == family_for_design("santa") == "advent"
    assert family_for_design("menorah") == "menorah"


def test_hanukkah_dates():
    # 25 Kislev (first full day; Hanukkah begins the evening before). 2026 matches the published date; later years come from pyluach.
    assert hanukkah_first_day(2026) == date(2026, 12, 5)
    assert hanukkah_first_day(2027) == date(2027, 12, 25)
    assert hanukkah_first_day(2028) == date(2028, 12, 13)


def test_build_days():
    adv = build_days("advent", 2026)
    assert len(adv) == 25 and adv[0]["date"] == "2026-12-01" and adv[-1]["date"] == "2026-12-25"
    men = build_days("menorah", 2026)
    assert len(men) == 8 and men[0]["date"] == "2026-12-04" and men[-1]["date"] == "2026-12-11"  # dated by night: lit the evening before each day


def test_availability_allows_catch_up():
    assert door_available("2026-12-03", date(2026, 12, 3))
    assert door_available("2026-12-03", date(2026, 12, 20))
    assert not door_available("2026-12-04", date(2026, 12, 3))


def test_test_month_shifts_dates(monkeypatch):
    from custom_components.advent_calendar import const
    monkeypatch.setattr(const, "TEST_MONTH", 11)
    adv = build_days("advent", 2026); men = build_days("menorah", 2026)
    assert adv[0]["date"] == "2026-11-01" and adv[-1]["date"] == "2026-11-25"
    assert men[0]["date"] == "2026-11-05" and men[-1]["date"] == "2026-11-12"
