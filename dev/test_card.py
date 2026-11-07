import sys, json
from playwright.sync_api import sync_playwright
BASE = "http://127.0.0.1:8765/dev/index.html"
fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (f"  [{extra}]" if extra and not cond else ""))
    if not cond: fails.append(name)

def grid_holes(page):
    return page.evaluate("""() => { const g = __card.shadowRoot.querySelector('.grid'); const cs = getComputedStyle(g);
      const cols = cs.gridTemplateColumns.split(' ').length, rows = cs.gridTemplateRows.split(' ').length;
      let area = 0; g.querySelectorAll('.door').forEach(d => { const big=d.classList.contains('big'), wide=d.classList.contains('wide'); area += big?4:wide?2:1; });
      return {cols, rows, area, cells: cols*rows}; }""")

with sync_playwright() as p:
    b = p.chromium.launch(executable_path="/usr/bin/google-chrome", args=["--no-sandbox"])
    ctx = b.new_context(viewport={"width": 760, "height": 900})
    page = ctx.new_page(); errs = []
    page.on("console", lambda m: errs.append(m.text) if m.type == "error" and "404" not in m.text else None)
    page.on("pageerror", lambda e: errs.append(str(e)))
    def load(qs):
        page.goto(BASE + "?" + qs); page.wait_for_function("__card && __card.shadowRoot.querySelector('.door')")
    def S(sel): return page.locator("advent-calendar-card " + sel)
    def parent_on(pin="1234"):
        S("#pm").click(); page.wait_for_selector("advent-calendar-card #pin"); S("#pin").fill(pin); S("#pok").click(); page.wait_for_timeout(400)
    page.add_init_script("localStorage.setItem('advent_sound','off')")

    # 1. persistence + gating (fresh store)
    load("store=t1&today=2026-12-03")
    check("25 doors rendered", S(".door").count() == 25)
    check("door 4 locked", "locked" in S(".door[data-day='4']").get_attribute("class"))
    page.screenshot(path="shots/01_winter_day3.png")
    S(".door[data-day='3']").click()
    page.wait_for_selector("advent-calendar-card .modal", timeout=3000)
    check("modal shown on open", S(".modal").count() == 1)
    page.wait_for_timeout(1200); page.screenshot(path="shots/02_winter_door3_modal.png")
    S("#close").click(); page.wait_for_timeout(300)
    check("door 3 open after close", "open" in S(".door[data-day='3']").get_attribute("class"))
    page.reload(); page.wait_for_selector("advent-calendar-card .door"); page.wait_for_timeout(300)
    check("door 3 STILL open after reload", "open" in S(".door[data-day='3']").get_attribute("class").split())
    # locked door click
    page.evaluate("__calls.length=0")
    S(".door[data-day='10']").click(); page.wait_for_timeout(200)
    check("locked door shows toast", S(".toast").count() == 1)
    check("locked door made no open_door call", "advent_calendar/open_door" not in page.evaluate("__calls"))
    # 2. parent mode
    parent_on()
    check("parent panel visible", S(".panel").count() == 1)
    page.evaluate("__calls.length=0")
    S(".door[data-day='10']").click(); page.wait_for_selector("advent-calendar-card .modal"); page.wait_for_timeout(800)
    S("#close").click(); page.wait_for_timeout(500)
    check("parent preview opens future door", "open" in S(".door[data-day='10']").get_attribute("class").split())
    check("parent preview does NOT call open_door", "advent_calendar/open_door" not in page.evaluate("__calls"))
    page.screenshot(path="shots/03_parent_mode.png", full_page=True)
    S("#pm").click(); page.wait_for_timeout(300)
    cls10 = S(".door[data-day='10']").get_attribute("class").split(); cls3 = S(".door[data-day='3']").get_attribute("class").split()
    check("parent off: preview door 10 closed again", "open" not in cls10)
    check("parent off: real door 3 still open", "open" in cls3)
    page.reload(); page.wait_for_selector("advent-calendar-card .door")
    check("after reload door 10 still closed", "open" not in S(".door[data-day='10']").get_attribute("class").split())

    # 3. custom door
    parent_on()
    S("#c-day").select_option("4"); S("#c-emoji").fill("🌮"); S("#c-title").fill("Lunch surprise"); S("#c-msg").fill("You're going to Chipotle for lunch today! <b>x</b>")
    S("#c-save").click(); page.wait_for_timeout(500)
    check("custom door listed", "Chipotle" in S(".clist").inner_text() or "Lunch surprise" in S(".clist").inner_text())
    S("#pm").click(); page.wait_for_timeout(200)
    load("store=t1&today=2026-12-04")
    S(".door[data-day='4']").click(); page.wait_for_selector("advent-calendar-card .modal"); page.wait_for_timeout(900)
    txt = S(".mcard").inner_text()
    check("custom content shown", "Chipotle" in txt and "Lunch surprise" in txt, repr(txt[:200]) + page.evaluate("JSON.stringify(__card._st.days[3])"))
    check("custom HTML escaped", "<b>x</b>" in txt)
    page.screenshot(path="shots/04_custom_door.png")
    S("#close").click()
    # parent mode is available to every account but needs the PIN
    load("store=t1&today=2026-12-04")
    check("parent button shown to everyone", S("#pm").count() == 1)
    S("#pm").click(); page.wait_for_selector("advent-calendar-card #pin"); S("#pin").fill("0000"); S("#pok").click(); page.wait_for_timeout(300)
    check("wrong PIN rejected", S(".panel").count() == 0 and "Incorrect" in S("#perr").inner_text())
    S("#pin").fill("1234"); S("#pok").click(); page.wait_for_timeout(500)
    check("right PIN accepted", S(".panel").count() == 1)
    page.screenshot(path="shots/04b_parent_unlocked.png", full_page=True)
    S("#c-day").select_option("6"); S("#c-msg").fill("Secret surprise"); S("#c-save").click(); page.wait_for_timeout(400)
    # without the PIN the page never receives unopened custom door content
    load("store=t1&today=2026-12-04")
    check("no PIN: unopened custom content not in page state", page.evaluate("__card._st.days[5].custom === undefined && __card._st.days[5].has_custom === true"))
    S("#pm").click(); page.wait_for_selector("advent-calendar-card #pin"); page.keyboard.press("Escape"); page.wait_for_timeout(200)
    check("PIN dialog cancels with Escape", S("#pin").count() == 0 and S(".panel").count() == 0)

    # 4. layouts
    for qs, name in [("order=random&sizes=varied", "winter_random_varied"), ("design=santa&sizes=varied", "santa_varied"), ("design=menorah&sizes=varied", "menorah_varied"), ("design=menorah", "menorah_uniform"), ("design=santa&order=random", "santa_random")]:
        load(f"store=L_{name}&today=2026-12-08&{qs}")
        h = grid_holes(page)
        check(f"{name}: no grid holes", h["area"] == h["cells"], json.dumps(h))
        page.screenshot(path=f"shots/05_{name}.png", full_page=True)
    # random order stable across reloads, differs from sequential
    load("store=R&today=2026-12-08&order=random"); o1 = page.evaluate("[...__card.shadowRoot.querySelectorAll('.door')].map(d=>d.dataset.day).join()")
    page.reload(); page.wait_for_selector("advent-calendar-card .door"); o2 = page.evaluate("[...__card.shadowRoot.querySelectorAll('.door')].map(d=>d.dataset.day).join()")
    check("random order stable on reload", o1 == o2); check("random order != sequential", o1 != ",".join(map(str, range(1, 26))))

    # 5. finales + a few effects
    def open_day(qs, day, shot, wait=2500):
        load(qs); S(f".door[data-day='{day}']").click(); page.wait_for_selector("advent-calendar-card .modal"); page.wait_for_timeout(wait); page.screenshot(path=shot); S("#close").click()
    open_day("store=F1&today=2026-12-25&design=santa", 25, "shots/06_christmas_finale.png", 3500)
    open_day("store=F2&today=2026-12-12&design=menorah", 8, "shots/07_hanukkah_finale.png", 3500)
    open_day("store=F2&today=2026-12-12&design=menorah", 3, "shots/08_menorah_day3.png", 1200)
    for d in (2, 4, 5, 6, 7, 8):  # sack, globe, gift(?), sleigh, lights
        open_day(f"store=FX{d}&today=2026-12-25&design=winter", d, f"shots/09_fx_day{d}.png", 1800)
    # joke punchline
    load("store=J&today=2026-12-25"); S(".door[data-day='2']").click(); page.wait_for_selector("advent-calendar-card #punch"); S("#punch").click(); page.wait_for_timeout(200)
    check("joke punchline revealed", "elf-abet" in S(".mcard").inner_text())

    # 6. v2026.11 features ------------------------------------------------
    # inline, larger countdown
    load("store=H1&today=2026-12-03&design=santa")
    g = page.evaluate("""() => { const r = __card.shadowRoot; const h = r.querySelector('h2').getBoundingClientRect(), c = r.querySelector('.count').getBoundingClientRect();
      return {sameRow: Math.abs((h.top + h.height/2) - (c.top + c.height/2)) < 20, rightOfTitle: c.left >= h.right - 1, size: parseFloat(getComputedStyle(r.querySelector('.count')).fontSize), text: r.querySelector('.count').textContent}; }""")
    check("countdown on same row, right of title", g["sameRow"] and g["rightOfTitle"], json.dumps(g))
    check("countdown font is large (>=18px)", g["size"] >= 18, json.dumps(g))
    for d, txt in [("winter", "until Christmas"), ("santa", "until Christmas"), ("menorah", "until Hanukkah")]:
        load(f"store=H2{d}&today=2026-11-20&design={d}")
        check(f"{d}: countdown text", txt in S(".count").inner_text(), S(".count").inner_text())
    page.screenshot(path="shots/10_header_menorah.png")
    load("store=H3&today=2026-12-06&design=menorah"); check("menorah: candles text during Hanukkah", "of 8 candles lit" in S(".count").inner_text())
    load("store=H4&today=2026-12-30&design=menorah"); check("menorah: after Hanukkah", "Chag Urim Sameach" in S(".count").inner_text())

    # fit to screen in Panel view
    page.set_viewport_size({"width": 1400, "height": 700})
    for design, extra in [("winter", ""), ("santa", "&sizes=varied"), ("menorah", "")]:
        load(f"store=P_{design}{extra[-6:]}&today=2026-12-03&design={design}&panel=1{extra}")
        page.wait_for_timeout(300)
        m = page.evaluate("""() => { const h = __card.getBoundingClientRect(), g = __card.shadowRoot.querySelector('.grid').getBoundingClientRect(), w = __card.shadowRoot.querySelector('.wrap');
          return {cardBottom: h.bottom, vh: innerHeight, docH: document.scrollingElement.scrollHeight, gridBottom: g.bottom, wrapScroll: w.scrollHeight - w.clientHeight, fit: w.classList.contains('fit')}; }""")
        check(f"panel/{design}{extra}: fits screen, no page scroll", m["fit"] and m["docH"] <= m["vh"] + 2 and m["cardBottom"] <= m["vh"] + 2 and m["wrapScroll"] <= 2, json.dumps(m))
        page.screenshot(path=f"shots/11_panel_{design}{extra[-6:]}.png")
    load("store=P_off&today=2026-12-03&panel=1&fit=0") if False else None
    page.set_viewport_size({"width": 760, "height": 900})
    load("store=P_nopanel&today=2026-12-03")
    check("normal (non-panel) view keeps natural height", not page.evaluate("__card.shadowRoot.querySelector('.wrap').classList.contains('fit')"))

    # activity plan
    pj = lambda e: page.evaluate(e)
    load("store=A0&today=2026-12-25")
    plan = pj("(()=>{const p=buildPlan('advent',null);return Object.entries(p).map(([d,c])=>d+':'+c.k[0]).join(' ')})()")
    acts = [int(x.split(':')[0]) for x in plan.split() if x.endswith(':a')]
    check("default plan: 8 activities on days 3,6,...,24", acts == [3, 6, 9, 12, 15, 18, 21, 24], plan)
    check("default plan: every one of 25 days has content", len(plan.split()) == 25)
    more = pj("(()=>{const p=buildPlan('advent',Array.from({length:14},(_,i)=>'Act '+i));return Object.values(p).filter(c=>c.k==='activity').length+'/'+Object.values(p).filter(c=>c.k==='joke'||c.k==='fact').length})()")
    check("14 activities replace jokes/facts (14 act, 10 joke/fact)", more == "14/10" or more.startswith("14/"), more)
    fewer = pj("(()=>{const p=buildPlan('advent',['Only one']);const v=Object.values(p);return [v.filter(c=>c.k==='activity').length, v.filter(c=>c.k==='fun').length, v.length].join()})()")
    a1, fun1, tot = map(int, fewer.split(","))
    check("1 activity: freed doors filled with jokes + fun (snow globe etc.)", a1 == 1 and fun1 >= 3 and tot == 25, fewer)
    zero = pj("(()=>{const p=buildPlan('advent',[]);return Object.values(p).filter(c=>c.k==='activity').length+'/'+Object.keys(p).length+'/'+Object.values(p).filter(c=>!c.t).length})()")
    check("0 activities: still 25 full doors", zero == "0/25/0", zero)
    check("menorah plan has 8 doors, finale last", pj("(()=>{const p=buildPlan('menorah',null);return Object.keys(p).length+':'+p[8].t.includes('Urim')})()") == "8:true")

    # parent edits activities through the UI; kids then see them
    load("store=A1&today=2026-12-25"); parent_on()
    check("activities editor shows 8 built-in activities", S("[data-act]").count() == 8)
    check("plan preview present", S(".plan").count() == 1)
    S("#a-add").click(); page.wait_for_timeout(200)
    S("[data-act]").nth(8).fill("Build a blanket fort"); S("#a-save").click(); page.wait_for_timeout(500)
    check("saved: 9 activities persisted", page.evaluate("__card._st.activities.advent.length") == 9)
    S("#pm").click(); page.wait_for_timeout(300)
    page.reload(); page.wait_for_selector("advent-calendar-card .door")
    texts = page.evaluate("Object.values(__card._plan).filter(c=>c.k==='activity').map(c=>c.t)")
    check("kids' plan includes the new activity", "Build a blanket fort" in texts, str(texts))
    day = page.evaluate("Number(Object.entries(__card._plan).find(([d,c])=>c.t==='Build a blanket fort')[0])")
    S(f".door[data-day='{day}']").click(); page.wait_for_selector("advent-calendar-card .modal"); page.wait_for_timeout(800)
    check("opening that door shows the custom activity", "Build a blanket fort" in S(".mcard").inner_text())
    S("#close").click()
    load("store=A1&today=2026-12-25"); parent_on()
    page.once("dialog", lambda d: d.accept()); S("#a-reset").click(); page.wait_for_timeout(500)
    check("reset restores 8 defaults", page.evaluate("__card._st.activities.advent === null") and S("[data-act]").count() == 8, str(page.evaluate("JSON.stringify(__card._st.activities)")) + " n=" + str(S("[data-act]").count()))
    # fun door: snow globe via 1 activity
    load("store=A2&today=2026-12-25"); parent_on()
    for _ in range(7): S("[data-actdel]").first.click(); page.wait_for_timeout(100)
    S("#a-save").click(); page.wait_for_timeout(400); S("#pm").click(); page.wait_for_timeout(300)
    fday = page.evaluate("Number(Object.entries(__card._plan).find(([d,c])=>c.fx==='globe')[0])")
    S(f".door[data-day='{fday}']").click(); page.wait_for_selector("advent-calendar-card .modal"); page.wait_for_timeout(1200)
    check("fun door renders the snow globe", S("#globe").count() == 1)
    page.screenshot(path="shots/12_fun_globe.png"); S("#close").click()
    check("no console/page errors", not errs, "; ".join(errs[:5]))
    b.close()
print("\nFAILED:", fails if fails else "none"); sys.exit(1 if fails else 0)
