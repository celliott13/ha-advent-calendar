# Advent Calendar for Home Assistant

A family-dashboard **Advent calendar** (Dec 1-25) and **Hanukkah calendar** (8 nights, dates computed from the Hebrew calendar). Each day a door can be opened, and opened doors stay open for every device and every family member.

## Features
- **Three designs:** Winter scene, Santa, Hanukkah menorah
- **Door order:** in order, or randomized (stable layout, with a Reshuffle button)
- **Door sizes:** all the same, or some larger
- **Your own doors:** a parent writes a message (and emoji) for any day, e.g. *"You're going to Chipotle for lunch today!"*
- **Customizable activities:** edit the family activities (hot cocoa, dance party, thank-you notes...), add your own, or remove some. A full day-by-day plan is shown to parents so nothing is a surprise
- **Every door does something:** jokes, facts, family activities, an elf loading Santa's sack, a shakeable snow globe, a gift to unwrap, a flying sleigh, twinkling lights, a tree that gains an ornament per door, a menorah that lights one more candle each night
- **Finales:** Christmas Day (door 25) and the 8th night of Hanukkah get confetti, fireworks and a celebration
- **Parent mode (PIN):** preview any door and change settings. Previews are never saved; leaving parent mode restores the real state
- **A real Home Assistant Device** with sensors and device triggers, so building automations is point-and-click
- Doors open on their date or later (missed days can be caught up)
- All artwork is original SVG/CSS/canvas. No external assets, no cloud calls. Sound is off by default.

## Install (HACS)
1. HACS > three-dot menu > **Custom repositories** > add `https://github.com/celliott13/ha-advent-calendar`, category **Integration**.
2. Install **Advent Calendar**, then **restart Home Assistant**.
3. Go to Settings > Devices & services > **Add integration**, choose **Advent Calendar**, and choose a **parent PIN** (4-8 digits).
4. **Refresh your browser once** (Ctrl+F5, or fully reopen the Companion app / wall-panel browser). Home Assistant only loads a new card's file when a page loads, so until you do, the editor says "Custom element doesn't exist". This is only needed after the first install.
5. Add the card (see below).

## Add it to a dashboard (recommended: a Panel view)
For a big, fit-to-screen calendar (great for a wall tablet):

1. Open your dashboard > **Edit** (pencil) > the **+** next to the view tabs to add a new view.
2. Give it a name such as *Advent*, set **View type** to **Panel (single card)**, and save.
3. Add a card > search **Advent Calendar** (or choose **Manual** and enter `type: custom:advent-calendar-card`).

In a Panel view the card automatically sizes itself to the visible screen, so all the doors fit without scrolling. In other view types it uses a natural square-door layout. You can force either behavior:

```yaml
type: custom:advent-calendar-card
fit: true     # always fit to the screen height; false = never; omit = automatic (fits in Panel views)
```

## Parent mode and the PIN
The calendar works for **every Home Assistant account**, including read-only users and shared wall tablets. Opening doors needs no PIN.

Anything parental needs the PIN you chose at setup: tap 🔒, enter the PIN, and you get the options panel (design, order, sizes, title, custom doors, activities, full plan, reset) and can preview any door. Previews are never saved, and leaving parent mode restores the real state. Parent mode also exits by itself after 5 minutes of inactivity.

The PIN is checked on the server for every parental action, not just hidden in the card. It is stored only as a salted hash, and 5 wrong attempts lock parent mode for 5 minutes. A custom door's text stays on the server until that door is opened. (The activities list is not secret; for a real surprise use a custom door.) To change the PIN, use **Settings > Devices & services > Advent Calendar > Configure**.

## Activities
In parent mode, the **Activities** section lists the family activities, pre-filled with the built-in examples. Edit them, add more, or delete some, then **Save activities**.

- Activities are spread evenly across the calendar. With the built-in 8 they land on days 3, 6, 9 ... 24.
- **More** activities replace jokes and facts to make room.
- **Fewer** activities free up doors, which are filled with extra jokes and fun things like shaking the snow globe, unwrapping a gift or watching the sleigh fly by (the dreidel on the Hanukkah calendar).
- A custom door for a specific day always wins over everything else.
- **Full plan (spoilers!)** shows exactly what every day will do.

## Automations
Open the automation editor, choose **Add trigger**, and type **Advent** in the search box (or expand the Advent Calendar device under *By target*). Pick one of these triggers, then choose the **Advent Calendar Doors opened** sensor (or the device) as the target:

| Trigger | When it fires | Option |
|---|---|---|
| Advent Calendar door opened | any door is opened | none |
| Advent Calendar door for a day opened | the door with that number is opened | day number (e.g. 7, or 25 for Christmas) |
| Advent Calendar door for a date opened | the door dated that day is opened, **on that date or any later day** (catch-up opens count) | date picker |
| Advent Calendar door for a date is waiting | just after midnight, when that date's door becomes available | date picker |
| Advent Calendar finale opened | Christmas Day / the 8th night of Hanukkah door is opened | none |
| Advent Calendar parent-written door opened | one of your own surprise doors is opened | none |

Every trigger provides these variables to your actions: `trigger.day`, `trigger.date`, `trigger.family` (`advent` or `menorah`), and, for the "opened" triggers, `trigger.design`, `trigger.custom`, `trigger.title` and `trigger.finale`.

### Examples
**Run something when the child opens a particular date's door** (even if they open it a few days late):

```yaml
alias: Advent - Dec 12 surprise
triggers:
  - trigger: advent_calendar.door_opened_on_date
    target:
      entity_id: sensor.advent_calendar_doors_opened
    options:
      date: "2026-12-12"
actions:
  - action: light.turn_on
    target:
      entity_id: light.living_room_tree
    data:
      color_name: red
      brightness_pct: 100
```

**Tell the family when a new door is ready** (fires at 12:00:01 am on that date):

```yaml
alias: Advent - Dec 5 door is ready
triggers:
  - trigger: advent_calendar.door_waiting_on_date
    target:
      entity_id: sensor.advent_calendar_doors_opened
    options:
      date: "2026-12-05"
actions:
  - action: notify.mobile_app_parents_phone
    data:
      message: "Door {{ trigger.day }} is ready to open!"
```

**A big finale** (Christmas morning lights and music):

```yaml
alias: Advent - finale
triggers:
  - trigger: advent_calendar.finale_opened
    target:
      entity_id: sensor.advent_calendar_doors_opened
actions:
  - action: scene.turn_on
    target:
      entity_id: scene.christmas_lights
  - action: media_player.play_media
    target:
      entity_id: media_player.family_room
    data:
      media_content_type: music
      media_content_id: "media-source://media_source/local/jingle.mp3"
```

**React to a specific door, or to any door:** use *door for a day opened* with `day: 7`, or *door opened* and branch on `{{ trigger.day }}` in your actions.

**Reminder if today's door is still closed.** The *Door waiting* binary sensor is on while an available door has not been opened:

```yaml
alias: Advent - nag at breakfast
triggers:
  - trigger: time
    at: "07:30:00"
conditions:
  - condition: state
    entity_id: binary_sensor.advent_calendar_door_waiting
    state: "on"
actions:
  - action: tts.speak
    target:
      entity_id: tts.home_assistant_cloud
    data:
      media_player_entity_id: media_player.kitchen
      message: "A new advent door is waiting to be opened!"
```

Entity IDs above assume the default names; adjust them to match yours. The same six triggers are also available under *Device* in the editor (older style), and you can use the `advent_calendar_door_opened` event directly (data: `day`, `family`, `design`, `date`, `custom`, `title`, `finale`).

The integration also provides a **Doors opened** sensor (count, with the list of opened days as attributes) and the **Door waiting** binary sensor.

## Hanukkah dates
Each door is dated by **night**: door 1 opens on the evening before the first full day of Hanukkah (when the first candle is lit), and door 8 on the 8th night. Dates are computed from the Hebrew calendar for the current year.

## Versioning
Versions follow Home Assistant's scheme: `YEAR.MONTH.ITERATION` (this release: **2026.11.1**). Tag releases with the same string, e.g. `2026.11.1`.

## Development
```
pip install pytest-homeassistant-custom-component home-assistant-frontend pyluach
pytest                      # backend tests
python -m http.server 8765  # then open http://127.0.0.1:8765/dev/index.html?today=2026-12-03
```
The dev page mocks Home Assistant. Query options: `today=YYYY-MM-DD`, `design=winter|santa|menorah`, `order=random`, `sizes=varied`, `panel=1` (Panel-view fit), `store=<name>`. The mock parent PIN is `1234`.
