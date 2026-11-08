"""Constants for Advent Calendar."""

DOMAIN = "advent_calendar"
VERSION = "2026.11.1"

STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1

URL_BASE = "/advent_calendar_static"
CARD_FILE = "advent-calendar-card.js"

EVENT_DOOR_OPENED = f"{DOMAIN}_door_opened"
EVENT_UPDATED = f"{DOMAIN}_updated"

DESIGNS = ("winter", "santa", "menorah")
ORDERS = ("sequential", "random")
SIZES = ("uniform", "varied")

# Calendar "families": winter + santa are Advent (Dec 1-25); menorah is Hanukkah (8 days)
FAMILY_ADVENT = "advent"
FAMILY_MENORAH = "menorah"
FAMILIES = (FAMILY_ADVENT, FAMILY_MENORAH)

DEFAULT_SETTINGS = {
    "design": "winter",
    "order": "sequential",
    "sizes": "uniform",
    "shuffle_seed": 1,
    "title": "",
}

MAX_TITLE = 60
MAX_MESSAGE = 280
MAX_EMOJI = 8

CONF_PIN_HASH = "pin_hash"
PIN_MIN, PIN_MAX = 4, 8
PIN_MAX_FAILS = 5
PIN_LOCKOUT_SECONDS = 300

MAX_ACTIVITIES = 24

# TEST BUILD ONLY: when set to a month number, the Advent doors are dated in that month (1-25) and the
# Hanukkah doors start on the 5th of it, so the calendar can be exercised before December.
# Set to None for release.
TEST_MONTH = None
