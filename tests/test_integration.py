from datetime import date
from unittest.mock import patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.advent_calendar.const import CONF_PIN_HASH, DOMAIN, EVENT_DOOR_OPENED
from custom_components.advent_calendar.manager import AdventManager, hash_pin
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

PIN = "1234"


@pytest.fixture(autouse=True)
def fake_today(request):
    """Pin the manager's notion of 'today' (freezing the clock would expire HA auth tokens)."""
    m = request.node.get_closest_marker("today")
    d = date.fromisoformat(m.args[0]) if m else date(2026, 12, 3)
    with patch.object(AdventManager, "today", lambda self: d):
        yield


@pytest.fixture
async def setup(hass: HomeAssistant, hass_client_no_auth):
    assert await async_setup_component(hass, "http", {})
    assert await async_setup_component(hass, "websocket_api", {})
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_PIN_HASH: hash_pin(PIN)}, unique_id=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


class Client:
    """Tiny helper that numbers websocket messages."""

    def __init__(self, ws):
        self.ws, self.i = ws, 0

    async def call(self, type_, **kw):
        self.i += 1
        await self.ws.send_json({"id": self.i, "type": f"{DOMAIN}/{type_}", **kw})
        return await self.ws.receive_json()


async def mk(hass, hass_ws_client, token):
    return Client(await hass_ws_client(hass, token))


@pytest.mark.today("2026-12-03")
async def test_open_door_rules_and_persistence(hass, setup, hass_ws_client, hass_read_only_access_token):
    events = []
    hass.bus.async_listen(EVENT_DOOR_OPENED, lambda e: events.append(e.data))
    c = await mk(hass, hass_ws_client, hass_read_only_access_token)  # any account works, even read-only
    r = await c.call("get_state")
    assert r["success"] and len(r["result"]["days"]) == 25 and not any(d["opened"] for d in r["result"]["days"])
    r = await c.call("open_door", day=10)
    assert not r["success"] and r["error"]["code"] == "not_yet"
    r = await c.call("open_door", day=3)
    assert r["success"] and r["result"]["newly_opened"] is True
    r = await c.call("open_door", day=3)
    assert r["success"] and r["result"]["newly_opened"] is False
    await hass.async_block_till_done()
    assert len(events) == 1 and events[0]["day"] == 3 and events[0]["finale"] is False
    assert (await c.call("open_door", day=1))["success"]  # catch-up
    st = (await c.call("get_state"))["result"]
    assert [d["day"] for d in st["days"] if d["opened"]] == [1, 3]
    assert hass.data[DOMAIN].data["opened"]["advent:2026"] == [1, 3]


@pytest.mark.today("2026-12-25")
async def test_finale_flag(hass, setup, hass_ws_client, hass_access_token):
    events = []
    hass.bus.async_listen(EVENT_DOOR_OPENED, lambda e: events.append(e.data))
    c = await mk(hass, hass_ws_client, hass_access_token)
    assert (await c.call("open_door", day=25))["success"]
    await hass.async_block_till_done()
    assert events[-1]["finale"] is True


@pytest.mark.today("2026-12-12")
async def test_menorah_family(hass, setup, hass_ws_client, hass_access_token):
    c = await mk(hass, hass_ws_client, hass_access_token)
    assert (await c.call("set_settings", pin=PIN, design="menorah"))["success"]
    st = (await c.call("get_state"))["result"]
    assert st["family"] == "menorah" and len(st["days"]) == 8 and st["days"][0]["date"] == "2026-12-04"
    assert (await c.call("open_door", day=8))["success"]
    assert not (await c.call("open_door", day=9))["success"]  # not a valid menorah day
    await c.call("set_settings", pin=PIN, design="winter")
    st = (await c.call("get_state"))["result"]
    assert not any(d["opened"] for d in st["days"])  # advent progress is separate


@pytest.mark.today("2026-12-03")
async def test_parent_pin_gates_everything_for_any_account(hass, setup, hass_ws_client, hass_read_only_access_token):
    kid = await mk(hass, hass_ws_client, hass_read_only_access_token)
    # No PIN / wrong PIN: every parent action refused
    r = await kid.call("set_custom", family="advent", day=4, message="x")  # pin missing -> schema error
    assert not r["success"]
    for t, kw in [("set_settings", {"design": "santa"}), ("set_custom", {"family": "advent", "day": 4, "message": "x"}),
                  ("delete_custom", {"family": "advent", "day": 4}), ("reset", {}), ("get_state", {}), ("verify_pin", {})]:
        r = await kid.call(t, pin="0000", **kw)
        assert not r["success"] and r["error"]["code"] == "invalid_pin", t
        hass.data[DOMAIN]._fails = 0  # keep this test clear of the lockout (tested separately)
    # Correct PIN works even for a read-only HA account
    kid2 = await mk(hass, hass_ws_client, hass_read_only_access_token)
    assert (await kid2.call("verify_pin", pin=PIN))["success"]
    assert (await kid2.call("set_custom", pin=PIN, family="advent", day=4, title="Lunch", message="Chipotle today!", emoji="🌮"))["success"]
    # Unopened custom content is visible only with the PIN
    public = (await kid2.call("get_state"))["result"]
    assert public["is_parent"] is False and public["days"][3]["has_custom"] is True and "custom" not in public["days"][3]
    parent = (await kid2.call("get_state", pin=PIN))["result"]
    assert parent["is_parent"] is True and parent["days"][3]["custom"]["message"] == "Chipotle today!"
    # Once opened, everyone sees the content
    await kid2.call("set_custom", pin=PIN, family="advent", day=3, message="Hello", emoji="")
    assert (await kid2.call("open_door", day=3))["success"]
    st = (await kid2.call("get_state"))["result"]
    assert st["days"][2]["custom"] == {"title": "", "message": "Hello", "emoji": "🎁"}


@pytest.mark.today("2026-12-03")
async def test_lockout_after_repeated_failures(hass, setup, hass_ws_client, hass_access_token):
    c = await mk(hass, hass_ws_client, hass_access_token)
    for _ in range(5):
        assert (await c.call("verify_pin", pin="9999"))["error"]["code"] == "invalid_pin"
    r = await c.call("verify_pin", pin=PIN)  # correct PIN is refused while locked
    assert not r["success"] and r["error"]["code"] == "locked"
    with patch("custom_components.advent_calendar.manager.time.monotonic", return_value=10**9):
        assert (await c.call("verify_pin", pin=PIN))["success"]


@pytest.mark.today("2026-12-03")
async def test_validation_and_reset(hass, setup, hass_ws_client, hass_access_token):
    c = await mk(hass, hass_ws_client, hass_access_token)
    assert not (await c.call("set_settings", pin=PIN, design="bogus"))["success"]
    assert not (await c.call("set_custom", pin=PIN, family="advent", day=3, message=""))["success"]
    assert not (await c.call("set_custom", pin=PIN, family="advent", day=3, message="x" * 281))["success"]
    s1 = (await c.call("get_state"))["result"]["settings"]["shuffle_seed"]
    await c.call("set_settings", pin=PIN, reshuffle=True)
    assert (await c.call("get_state"))["result"]["settings"]["shuffle_seed"] != s1
    await c.call("open_door", day=1)
    assert (await c.call("reset", pin=PIN))["success"]
    assert not any(d["opened"] for d in (await c.call("get_state"))["result"]["days"])


async def test_state_survives_restart(hass, setup):
    mgr = hass.data[DOMAIN]
    await mgr.async_open_door(2, today=date(2026, 12, 2))
    await mgr.async_set_custom("advent", 5, "t", "m", "e")
    await hass.async_block_till_done()
    m2 = AdventManager(hass, setup)
    await m2.async_load()
    assert m2.data["opened"]["advent:2026"] == [2] and "advent:5" in m2.data["custom"]


async def test_config_and_options_flow(hass):
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert r["type"] == "form"
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"pin": "12"})
    assert r["type"] == "form" and r["errors"] == {"pin": "invalid_pin"}
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"pin": "abcd"})
    assert r["errors"] == {"pin": "invalid_pin"}
    r = await hass.config_entries.flow.async_configure(r["flow_id"], {"pin": "4321"})
    assert r["type"] == "create_entry"
    entry = r["result"]
    assert "4321" not in str(entry.data) and entry.data[CONF_PIN_HASH].count("$") == 1  # stored hashed only
    r = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert r["type"] == "abort" and r["reason"] == "already_configured"
    # change the PIN via options
    await hass.async_block_till_done()
    r = await hass.config_entries.options.async_init(entry.entry_id)
    r = await hass.config_entries.options.async_configure(r["flow_id"], {"pin": "5555"})
    assert r["type"] == "create_entry"
    mgr = hass.data[DOMAIN]
    await mgr.async_verify_pin("5555")
    with pytest.raises(ValueError):
        await mgr.async_verify_pin("4321")


async def test_card_js_served_and_registered(hass, setup, hass_client):
    client = await hass_client()
    resp = await client.get("/advent_calendar_static/advent-calendar-card.js")
    assert resp.status == 200
    body = await resp.text()
    assert len(body) > 30000 and "advent-calendar-card" in body
    from homeassistant.components.frontend import DATA_EXTRA_MODULE_URL
    assert any("advent-calendar-card.js" in u for u in hass.data[DATA_EXTRA_MODULE_URL].urls)


@pytest.mark.today("2026-12-03")
async def test_activities_api(hass, setup, hass_ws_client, hass_read_only_access_token):
    c = await mk(hass, hass_ws_client, hass_read_only_access_token)
    assert (await c.call("get_state"))["result"]["activities"] == {"advent": None, "menorah": None}
    r = await c.call("set_activities", pin="0000", family="advent", activities=["x"])
    assert not r["success"] and r["error"]["code"] == "invalid_pin"
    hass.data[DOMAIN]._fails = 0
    r = await c.call("set_activities", pin=PIN, family="advent", activities=["Cocoa time", "  Dance party  ", ""])
    assert r["success"]
    assert (await c.call("get_state"))["result"]["activities"]["advent"] == ["Cocoa time", "Dance party"]
    assert (await c.call("set_activities", pin=PIN, family="advent", activities=[]))["success"]  # zero activities is allowed
    assert (await c.call("get_state"))["result"]["activities"]["advent"] == []
    assert (await c.call("set_activities", pin=PIN, family="advent", activities=None))["success"]  # restore defaults
    assert (await c.call("get_state"))["result"]["activities"]["advent"] is None
    # menorah only has 7 non-finale doors
    r = await c.call("set_activities", pin=PIN, family="menorah", activities=["a"] * 8)
    assert not r["success"] and r["error"]["code"] == "too_many_activities"
    assert not (await c.call("set_activities", pin=PIN, family="advent", activities=["a"] * 25))["success"]


@pytest.mark.today("2026-12-03")
async def test_device_and_entities(hass, setup, hass_ws_client, hass_access_token):
    from homeassistant.helpers import device_registry as dr, entity_registry as er
    dev = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, setup.entry_id)})
    assert dev is not None and dev.name == "Advent Calendar"
    ent = er.async_get(hass)
    sensor = ent.async_get_entity_id("sensor", DOMAIN, f"{setup.entry_id}_doors_opened")
    waiting = ent.async_get_entity_id("binary_sensor", DOMAIN, f"{setup.entry_id}_door_waiting")
    assert sensor and waiting
    assert hass.states.get(sensor).state == "0"
    assert hass.states.get(waiting).state == "on"  # doors 1-3 are available and unopened
    c = await mk(hass, hass_ws_client, hass_access_token)
    for d in (1, 2, 3):
        await c.call("open_door", day=d)
    await hass.async_block_till_done()
    assert hass.states.get(sensor).state == "3"
    assert hass.states.get(sensor).attributes["opened_days"] == [1, 2, 3]
    assert hass.states.get(waiting).state == "off"


@pytest.mark.today("2026-12-25")
async def test_device_triggers(hass, setup, hass_ws_client, hass_access_token):
    from homeassistant.components import automation
    from homeassistant.components.device_automation import async_get_device_automations, DeviceAutomationType
    from homeassistant.helpers import device_registry as dr
    from pytest_homeassistant_custom_component.common import async_mock_service

    dev = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, setup.entry_id)})
    triggers = await async_get_device_automations(hass, DeviceAutomationType.TRIGGER, [dev.id])
    types = {t["type"] for t in triggers[dev.id] if t["domain"] == DOMAIN}
    assert types == {"door_opened", "door_opened_day", "finale_opened", "custom_door_opened", "door_opened_on_date", "door_waiting_on_date"}

    calls = async_mock_service(hass, "test", "automation")
    def trig(**kw):
        return {"platform": "device", "domain": DOMAIN, "device_id": dev.id, **kw}
    def auto(i, trigger):
        return {"alias": i, "trigger": trigger, "action": {"service": "test.automation", "data": {"which": i}}}
    assert await async_setup_component(hass, "automation", {"automation": [
        auto("any", trig(type="door_opened")),
        auto("day7", trig(type="door_opened_day", day=7)),
        auto("finale", trig(type="finale_opened")),
        auto("custom", trig(type="custom_door_opened")),
        auto("date8", trig(type="door_opened_on_date", date="2026-12-08")),
    ]})
    await hass.async_block_till_done()
    c = await mk(hass, hass_ws_client, hass_access_token)
    await c.call("set_custom", pin=PIN, family="advent", day=7, message="Surprise!")
    await c.call("open_door", day=7); await hass.async_block_till_done()
    assert sorted(x.data["which"] for x in calls) == ["any", "custom", "day7"]
    calls.clear()
    await c.call("open_door", day=8); await hass.async_block_till_done()
    assert sorted(x.data["which"] for x in calls) == ["any", "date8"]
    calls.clear()
    await c.call("open_door", day=25); await hass.async_block_till_done()
    assert sorted(x.data["which"] for x in calls) == ["any", "finale"]


@pytest.mark.today("2026-12-09")
async def test_waiting_date_trigger(hass, setup):
    from datetime import datetime, timezone
    from homeassistant.helpers import device_registry as dr
    from pytest_homeassistant_custom_component.common import async_fire_time_changed, async_mock_service
    import homeassistant.util.dt as dt_util

    dev = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, setup.entry_id)})
    calls = async_mock_service(hass, "test", "automation")
    trig = lambda d: {"platform": "device", "domain": DOMAIN, "device_id": dev.id, "type": "door_waiting_on_date", "date": d}
    assert await async_setup_component(hass, "automation", {"automation": [
        {"alias": "w", "trigger": trig("2026-12-10"), "action": {"service": "test.automation", "data": {"day": "{{ trigger.day }}", "date": "{{ trigger.date }}"}}},
        {"alias": "other", "trigger": trig("2026-12-20"), "action": {"service": "test.automation", "data": {"which": "other"}}},
    ]})
    await hass.async_block_till_done()
    tz = dt_util.get_default_time_zone()
    async_fire_time_changed(hass, datetime(2026, 12, 10, 0, 0, 1, tzinfo=tz))
    await hass.async_block_till_done()
    assert len(calls) == 1 and calls[0].data == {"day": 10, "date": "2026-12-10"}
    calls.clear()
    async_fire_time_changed(hass, datetime(2026, 12, 11, 0, 0, 1, tzinfo=tz))
    await hass.async_block_till_done()
    assert calls == []   # other date, and the first date has passed


@pytest.mark.today("2026-12-09")
async def test_target_triggers(hass, setup, hass_ws_client, hass_access_token):
    from homeassistant.helpers import entity_registry as er
    from pytest_homeassistant_custom_component.common import async_mock_service

    sensor = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{setup.entry_id}_doors_opened")
    calls = async_mock_service(hass, "test", "automation")
    tgt = {"entity_id": [sensor]}
    def auto(i, key, **opts):
        t = {"trigger": f"{DOMAIN}.{key}", "target": tgt}
        if opts:
            t["options"] = opts
        return {"alias": i, "triggers": t, "actions": {"action": "test.automation", "data": {"which": i, "day": "{{ trigger.day }}"}}}
    assert await async_setup_component(hass, "automation", {"automation": [
        auto("any", "door_opened"),
        auto("day4", "door_opened_day", day=4),
        auto("date5", "door_opened_on_date", date="2026-12-05"),
        auto("date6", "door_opened_on_date", date="2026-12-06"),
        auto("finale", "finale_opened"),
    ]})
    await hass.async_block_till_done()
    c = await mk(hass, hass_ws_client, hass_access_token)
    await c.call("open_door", day=4); await hass.async_block_till_done()
    assert sorted(x.data["which"] for x in calls) == ["any", "day4"]
    calls.clear()
    await c.call("open_door", day=5); await hass.async_block_till_done()   # opened later than its date still counts
    assert sorted(x.data["which"] for x in calls) == ["any", "date5"]
    assert all(x.data["day"] == 5 for x in calls)
