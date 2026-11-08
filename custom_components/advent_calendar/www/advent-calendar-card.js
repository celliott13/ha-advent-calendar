/*
 * Advent Calendar card for Home Assistant  (served by the advent_calendar integration)
 * Usage:   type: custom:advent-calendar-card
 * Parent mode is protected by the PIN chosen when the integration was set up (enforced server-side).
 * All artwork and animation is original, drawn with SVG/CSS/canvas. No external assets.
 */
const AC_VERSION = "2026.11.1";

/* ------------------------------------------------------------------ content */
const KIND_ICON = { joke: "🎭", fact: "💡", activity: "✨", fun: "🎉" };

/* Built-in content. Activities are customisable by the parent; jokes/facts/fun fill the remaining doors. */
const ADVENT_ACTIVITIES = [
  "Hot cocoa break! Make a mug of cocoa and add extra marshmallows.",
  "Sing a holiday song together. Silly voices are encouraged.",
  "Draw a snowman, then give him the silliest hat you can imagine.",
  "Do a good deed today. Say something kind to someone who isn't expecting it.",
  "Dance party! Pick one song, turn it up, and everyone moves.",
  "Write a thank-you note to someone who helped you this year.",
  "Long, dark night: turn off the big lights, turn on the string lights, and read a story.",
  "Christmas Eve: set out cookies and carrots, then get to bed early.",
];
const ADVENT_SEQ = [
  { k: "fact", t: "Every snowflake has six sides (or arms), because of the way water molecules lock together as they freeze." },
  { k: "joke", t: "What do elves learn in school?", p: "The elf-abet!" },
  { k: "fact", t: "Reindeer are the only kind of deer where both the males and the females grow antlers." },
  { k: "joke", t: "What do snowmen eat for breakfast?", p: "Frosted flakes!" },
  { k: "fact", t: "'Jingle Bells' was the first song broadcast from space, played by the Gemini 6 astronauts in 1965." },
  { k: "joke", t: "What do you call a snowman in July?", p: "A puddle!" },
  { k: "fact", t: "Poinsettias, the red holiday plants, are native to Mexico." },
  { k: "joke", t: "Why did Santa go to music school?", p: "To improve his wrapping skills!" },
  { k: "fact", t: "Rudolph the Red-Nosed Reindeer first appeared in a storybook in 1939." },
  { k: "joke", t: "Why did the gingerbread man go to the doctor?", p: "He was feeling crummy!" },
  { k: "fact", t: "The first electric Christmas tree lights were made in 1882." },
  { k: "joke", t: "What do you get when you cross a snowman with a vampire?", p: "Frostbite!" },
  { k: "fact", t: "In Iceland, thirteen 'Yule Lads' visit during the thirteen nights before Christmas." },
  { k: "joke", t: "What did one snowman say to the other?", p: "Do you smell carrots?" },
  { k: "fact", t: "Tinsel was originally made from real silver." },
  { k: "joke", t: "What do you call Santa's helpers?", p: "Subordinate Clauses!" },
];
/* Used when the parent has fewer activities than the built-in set: extra jokes and interactive fun. */
const ADVENT_EXTRA = [
  { k: "fun", fx: "globe", t: "Shake the snow globe and watch the snow swirl!" },
  { k: "joke", t: "What do you call a reindeer with no eyes?", p: "No-eye-deer!" },
  { k: "fun", fx: "gift", t: "A present just for you. Tap it to unwrap!" },
  { k: "joke", t: "Why was the Christmas tree bad at sewing?", p: "It kept dropping its needles!" },
  { k: "fact", t: "Mistletoe is a plant that grows on the branches of trees." },
  { k: "fun", fx: "sleigh", t: "Santa's sleigh is zooming past. Can you spot the reindeer?" },
  { k: "joke", t: "What do snowmen wear on their heads?", p: "Ice caps!" },
  { k: "fact", t: "The Christmas tree tradition at Rockefeller Center began in 1931." },
];
const ADVENT_FINALE = { k: "fact", t: "Look at all those doors you opened! Enjoy the day together." };

const MENORAH_ACTIVITIES = ["Family dreidel game! Spin, and see who collects the most gelt."];
const MENORAH_SEQ = [
  { k: "fact", t: "Hanukkah means 'dedication' in Hebrew. It remembers the rededication of the Temple in Jerusalem." },
  { k: "fact", t: "A Hanukkah menorah has nine branches: one for each of the eight nights, plus the shamash, the 'helper' candle that lights the others." },
  { k: "joke", t: "What did one dreidel say to the other?", p: "Let's spin out!" },
  { k: "fact", t: "The four letters on a dreidel stand for 'Nes gadol hayah sham': a great miracle happened there." },
  { k: "fact", t: "Foods fried in oil, like latkes and sufganiyot (jelly doughnuts), remember the miracle of the oil." },
  { k: "fact", t: "'Gelt' means money in Yiddish. Chocolate gelt is a Hanukkah favorite." },
];
const MENORAH_EXTRA = [
  { k: "fun", fx: "dreidel", t: "Spin the dreidel! Which letter will it land on?" },
  { k: "joke", t: "What did the dreidel say when it got dizzy?", p: "I'm going around in circles!" },
  { k: "fact", t: "Candles are added from right to left, but lit from left to right, so the newest candle is lit first." },
  { k: "fact", t: "A menorah is traditionally placed in a window or doorway so its light can be seen from outside." },
  { k: "joke", t: "What's the best thing to put in a latke?", p: "Your teeth!" },
];
const MENORAH_FINALE = { k: "fact", t: "Eight nights, eight lights! Chag Urim Sameach: Happy Festival of Lights!" };

const PLAN_DAYS = { advent: 24, menorah: 7 };       // doors before the finale
const MAX_ACTIVITIES = PLAN_DAYS;                      // at most one activity per door
function defaultActivities(family) { return (family === "menorah" ? MENORAH_ACTIVITIES : ADVENT_ACTIVITIES).slice(); }

/* Day -> content. Activities are spread evenly (the built-in 8 land on days 3, 6, ... 24, exactly as before).
 * More activities replace jokes/facts; fewer free up doors that are filled with extra jokes and fun. */
function buildPlan(family, acts) {
  const men = family === "menorah", N = PLAN_DAYS[family];
  const list = (acts == null ? defaultActivities(family) : acts).slice(0, N), a = list.length, pos = new Map();
  for (let i = 0; i < a; i++) pos.set(Math.floor(((i + 1) * N) / a), { k: "activity", t: list[i] });
  const seq = (men ? MENORAH_SEQ : ADVENT_SEQ).concat(men ? MENORAH_EXTRA : ADVENT_EXTRA), plan = {};
  let si = 0;
  for (let d = 1; d <= N; d++) plan[d] = pos.get(d) || seq[si++ % seq.length];
  plan[N + 1] = men ? MENORAH_FINALE : ADVENT_FINALE;
  return plan;
}
const FX_CYCLE = ["snow", "sack", "tree", "globe", "gift", "sleigh", "lights"];
const FX_HINT = { globe: "Tap the snow globe to shake it!", tree: "Another ornament for the tree!", gift: "Tap the gift!" };

const DESIGN_LABEL = { winter: "Winter scene", santa: "Santa", menorah: "Hanukkah menorah" };
const FAMILY_DAYS = { advent: 25, menorah: 8 };

/* ------------------------------------------------------------------ utils */
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
function mulberry32(a) {
  return function () {
    a |= 0; a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
function seededOrder(n, seed) {
  const rnd = mulberry32(seed), a = Array.from({ length: n }, (_, i) => i + 1);
  for (let i = n - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; }
  return a;
}
function bigDoors(family, seed, attempt = 0) {
  // advent: 5 large (2x2) doors, always incl. day 25; menorah: 4 wide (2x1) doors
  const n = FAMILY_DAYS[family], rnd = mulberry32(seed + 7 + attempt * 101);
  const want = family === "advent" ? 5 : 4, set = new Set();
  if (family === "advent" && attempt < 200) set.add(25);   // prefer a big finale door; relax if no gap-free layout exists
  const pool = seededOrder(family === "advent" ? 24 : n, Math.floor(rnd() * 1e9));
  for (const d of pool) { if (set.size >= want) break; set.add(d); }
  return set;
}
// Simulates CSS "grid-auto-flow: dense" placement; returns rows used.
function packRows(order, bigSet, cols, w, h) {
  const used = []; let rows = 0;
  const free = (r, c, ww, hh) => { for (let i = 0; i < hh; i++) for (let j = 0; j < ww; j++) if (used[r + i] && used[r + i][c + j]) return false; return true; };
  for (const day of order) {
    const ww = bigSet.has(day) ? w : 1, hh = bigSet.has(day) ? h : 1; let placed = false;
    for (let r = 0; !placed; r++) for (let c = 0; c + ww <= cols && !placed; c++) if (free(r, c, ww, hh)) {
      for (let i = 0; i < hh; i++) { used[r + i] = used[r + i] || []; for (let j = 0; j < ww; j++) used[r + i][c + j] = true; }
      rows = Math.max(rows, r + hh); placed = true;
    }
  }
  return rows;
}
// Pick a set of large doors that tiles the grid with no gaps for the current door order.
function layoutBigDoors(family, seed, order, cols) {
  const w = 2, h = family === "menorah" ? 1 : 2, area = order.length + (family === "advent" ? 5 : 4) * (w * h - 1);
  let best = null;
  for (let a = 0; a < 400; a++) {
    const set = bigDoors(family, seed, a), rows = packRows(order, set, cols, w, h);
    best = best || { set, rows };
    if (rows * cols === area) return { set, rows };
  }
  return best;
}
function inPanel(el) {   // is the card the single card of a Panel-view dashboard?
  let n = el;
  for (let i = 0; i < 40 && n; i++) { if (n.localName === "hui-panel-view") return true; n = n.parentElement || (n.getRootNode && n.getRootNode().host) || null; }
  return false;
}
function countdownText(st) {
  const [y, m, d] = st.today.split("-").map(Number), today = new Date(y, m - 1, d), days = st.days;
  const dt = (iso) => { const [a, b, c] = iso.split("-").map(Number); return new Date(a, b - 1, c); };
  const diff = (to) => Math.round((to - today) / 864e5);
  if (st.family === "menorah") {
    const left = diff(dt(days[0].date)), end = diff(dt(days[days.length - 1].date));
    if (left > 0) return `${left} day${left === 1 ? "" : "s"} until Hanukkah`;
    if (end >= 0) return `${days.filter((x) => x.opened).length} of 8 candles lit`;
    return "Chag Urim Sameach!";
  }
  const left = diff(dt(days[days.length - 1].date));
  return left > 0 ? `${left} day${left === 1 ? "" : "s"} until Christmas` : left === 0 ? "Merry Christmas! 🎄" : "Hope it was a wonderful Christmas";
}
function prettyDate(iso) {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

/* ------------------------------------------------------------------ canvas effects */
class FxCanvas {
  constructor(canvas) { this.c = canvas; this.ctx = canvas.getContext("2d"); this.parts = []; this.mode = null; this.raf = 0; this.t = 0; }
  resize() { const r = this.c.getBoundingClientRect(); this.c.width = r.width * devicePixelRatio; this.c.height = r.height * devicePixelRatio; this.w = r.width; this.h = r.height; this.ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0); }
  start() { this.resize(); this.last = performance.now(); const loop = (now) => { const dt = Math.min(0.05, (now - this.last) / 1000); this.last = now; this.step(dt); this.raf = requestAnimationFrame(loop); }; this.raf = requestAnimationFrame(loop); }
  stop() { cancelAnimationFrame(this.raf); }
  snow(on = true) { this.snowOn = on; }
  confetti(n = 140) {
    const colors = ["#ff4d4d", "#ffd23f", "#3ddc97", "#4da3ff", "#ff7bd5", "#ffffff"];
    for (let i = 0; i < n; i++) this.parts.push({ k: "c", x: Math.random() * this.w, y: -10 - Math.random() * this.h * 0.4, vx: (Math.random() - 0.5) * 80, vy: 80 + Math.random() * 160, r: Math.random() * 6.28, vr: (Math.random() - 0.5) * 10, s: 5 + Math.random() * 6, col: colors[i % colors.length], life: 6 });
  }
  burst(x, y, hue) {
    const n = 70;
    for (let i = 0; i < n; i++) { const a = (i / n) * 6.283 + Math.random() * 0.2, sp = 80 + Math.random() * 190; this.parts.push({ k: "f", x, y, vx: Math.cos(a) * sp, vy: Math.sin(a) * sp, life: 1.4 + Math.random() * 0.6, max: 2, hue }); }
  }
  fireworks(ms = 9000) {
    const t0 = performance.now(); const tick = () => { if (performance.now() - t0 > ms || !this.raf) return; this.burst(this.w * (0.15 + Math.random() * 0.7), this.h * (0.12 + Math.random() * 0.4), Math.floor(Math.random() * 360)); setTimeout(tick, 350 + Math.random() * 450); }; tick();
  }
  step(dt) {
    const g = this.ctx; g.clearRect(0, 0, this.w, this.h); this.t += dt;
    if (this.snowOn) {
      while (this.parts.filter((p) => p.k === "s").length < 90) this.parts.push({ k: "s", x: Math.random() * this.w, y: -5, vx: (Math.random() - 0.5) * 20, vy: 25 + Math.random() * 45, s: 1.5 + Math.random() * 3.5, ph: Math.random() * 6, life: 99 });
    }
    this.parts = this.parts.filter((p) => p.life > 0 && p.y < this.h + 20);
    for (const p of this.parts) {
      p.life -= dt;
      if (p.k === "s") { p.x += (p.vx + Math.sin(this.t + p.ph) * 15) * dt; p.y += p.vy * dt; g.fillStyle = "rgba(255,255,255,.85)"; g.beginPath(); g.arc(p.x, p.y, p.s, 0, 6.283); g.fill(); }
      else if (p.k === "c") { p.x += p.vx * dt; p.y += p.vy * dt; p.r += p.vr * dt; g.save(); g.translate(p.x, p.y); g.rotate(p.r); g.fillStyle = p.col; g.fillRect(-p.s / 2, -p.s / 4, p.s, p.s / 2); g.restore(); }
      else { p.vy += 120 * dt; p.x += p.vx * dt; p.y += p.vy * dt; p.vx *= 0.985; g.fillStyle = `hsla(${p.hue},100%,65%,${Math.max(0, p.life / p.max)})`; g.beginPath(); g.arc(p.x, p.y, 2.2, 0, 6.283); g.fill(); }
    }
  }
}

/* ------------------------------------------------------------------ sound (muted by default) */
const Sound = {
  muted: (() => { try { return localStorage.getItem("advent_sound") !== "on"; } catch (e) { return true; } })(),
  toggle() { this.muted = !this.muted; try { localStorage.setItem("advent_sound", this.muted ? "off" : "on"); } catch (e) {} return !this.muted; },
  play(notes) {
    if (this.muted) return;
    try {
      this.ctx = this.ctx || new (window.AudioContext || window.webkitAudioContext)();
      const t0 = this.ctx.currentTime;
      notes.forEach((f, i) => {
        const o = this.ctx.createOscillator(), g = this.ctx.createGain();
        o.type = "triangle"; o.frequency.value = f; o.connect(g); g.connect(this.ctx.destination);
        const s = t0 + i * 0.18; g.gain.setValueAtTime(0.0001, s); g.gain.exponentialRampToValueAtTime(0.18, s + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, s + 0.5);
        o.start(s); o.stop(s + 0.55);
      });
    } catch (e) { /* audio not available */ }
  },
};
const JINGLE = [659, 659, 659, 659, 659, 659, 659, 784, 523, 587, 659];
const CHIME = [784, 988, 1175];

/* ------------------------------------------------------------------ SVG scenes */
const SVG = {
  sack: () => `
<svg viewBox="0 0 320 200" class="scene">
  <ellipse cx="215" cy="185" rx="80" ry="10" fill="rgba(0,0,0,.25)"/>
  <path d="M160 180 C150 120 175 95 205 90 L245 90 C275 95 290 125 280 180 Z" fill="#c8963e" stroke="#8a6320" stroke-width="3"/>
  <path d="M200 92 q22 -14 50 0" fill="none" stroke="#8a6320" stroke-width="5" stroke-linecap="round"/>
  <path d="M205 90 q20 12 40 0" fill="#a77b2c"/>
  <g class="elf">
    <path d="M60 186 L72 120 L100 120 L112 186 Z" fill="#2e9a4d"/>
    <circle cx="86" cy="103" r="19" fill="#f6cfa1"/>
    <path d="M66 98 L86 42 L106 98 Z" fill="#d93a3a"/>
    <circle cx="86" cy="40" r="6" fill="#fff"/>
    <rect x="64" y="94" width="44" height="7" rx="3" fill="#fff"/>
    <path d="M67 105 l-10 -4 l10 10 z M105 105 l10 -4 l-10 10 z" fill="#f6cfa1"/>
    <circle cx="80" cy="106" r="2" fill="#333"/><circle cx="92" cy="106" r="2" fill="#333"/>
    <path d="M80 113 q6 5 12 0" fill="none" stroke="#a34" stroke-width="2"/>
    <g class="arm"><rect x="98" y="124" width="46" height="9" rx="4" fill="#2e9a4d" transform="rotate(-18 98 128)"/></g>
  </g>
</svg>
<div class="toys"><span style="--i:0">🧸</span><span style="--i:1">🚂</span><span style="--i:2">🎨</span><span style="--i:3">🪀</span><span style="--i:4">🎁</span><span style="--i:5">🪁</span></div>`,
  globe: () => `
<svg viewBox="0 0 220 240" class="scene globe" id="globe">
  <defs><clipPath id="gc"><circle cx="110" cy="100" r="84"/></clipPath><radialGradient id="gg" cx=".35" cy=".3"><stop offset="0" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient></defs>
  <circle cx="110" cy="100" r="84" fill="#173a6b"/>
  <g clip-path="url(#gc)">
    <path d="M10 170 q50 -40 100 -15 t100 -10 V200 H10z" fill="#f4f8ff"/>
    <path d="M85 150 l22 -52 l22 52z" fill="#1d6b3f"/><path d="M92 125 l15 -38 l15 38z" fill="#238a50"/>
    <g id="flakes"></g>
  </g>
  <circle cx="110" cy="100" r="84" fill="url(#gg)" stroke="#cfe6ff" stroke-width="3"/>
  <path d="M50 190 h120 l12 38 h-144z" fill="#8c2a2a" stroke="#5a1717" stroke-width="3"/>
</svg>`,
  gift: () => `
<svg viewBox="0 0 220 220" class="scene gift" id="giftsvg">
  <rect x="50" y="100" width="120" height="90" rx="6" fill="#c92d3a"/>
  <rect x="100" y="100" width="20" height="90" fill="#ffd23f"/>
  <g class="lid"><rect x="42" y="78" width="136" height="28" rx="6" fill="#e0414f"/><rect x="100" y="78" width="20" height="28" fill="#ffd23f"/>
  <path d="M110 78 c-30 -34 -52 -2 -8 0 z M110 78 c30 -34 52 -2 8 0 z" fill="#ffd23f"/></g>
</svg><div class="giftpop" id="giftpop"></div>`,
  sleigh: () => `
<svg viewBox="0 0 400 160" class="scene sleigh">
  <g class="fly">
    <path d="M150 105 q40 10 90 0 l12 -26 h-70 q-20 0 -32 26z" fill="#b8272f" stroke="#7c161c" stroke-width="3"/>
    <path d="M140 118 q60 20 120 0" fill="none" stroke="#e8c15a" stroke-width="5" stroke-linecap="round"/>
    <circle cx="205" cy="62" r="13" fill="#f6cfa1"/><path d="M190 58 q15 -30 32 0z" fill="#d93a3a"/><circle cx="224" cy="52" r="5" fill="#fff"/>
    <rect x="215" y="68" width="22" height="22" rx="8" fill="#d93a3a"/>
    <path d="M60 96 h80" stroke="#c9a15a" stroke-width="3"/>
    <text x="40" y="100" font-size="34">🦌</text><text x="8" y="106" font-size="34">🦌</text>
  </g>
</svg>`,
  tree: (n) => {
    const cols = ["#ff4d4d", "#ffd23f", "#4da3ff", "#ff7bd5", "#ffffff", "#3ddc97"];
    const rnd = mulberry32(42); let balls = "";
    for (let i = 0; i < Math.min(n, 24); i++) { const row = Math.floor(rnd() * 4), w = 30 + row * 28, y = 62 + row * 34 + rnd() * 18, x = 110 + (rnd() - 0.5) * w * 1.5; balls += `<circle class="orn" style="animation-delay:${i * 40}ms" cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="5.5" fill="${cols[i % 6]}"/>`; }
    return `<svg viewBox="0 0 220 230" class="scene"><rect x="100" y="190" width="20" height="30" fill="#6b4423"/>
<path d="M110 14 L152 82 H68Z" fill="#1d6b3f"/><path d="M110 48 L168 124 H52Z" fill="#238a50"/><path d="M110 88 L184 172 H36Z" fill="#2aa05d"/><path d="M110 130 L196 196 H24Z" fill="#2fb36a" opacity=".0"/>
<path d="M110 8 l4 10 11 1 -9 7 3 11 -9 -6 -9 6 3 -11 -9 -7 11 -1z" fill="#ffd23f"/>${balls}</svg>`;
  },
  menorah: (lit) => {
    // 8 candles (index 0..7 left->right) + shamash (center, higher). Newest candle is added on the right.
    const xs = [30, 62, 94, 126, 194, 226, 258, 290];
    let c = "";
    xs.forEach((x, i) => {
      const on = i >= 8 - lit;
      c += `<rect x="${x - 6}" y="86" width="12" height="46" rx="2" fill="#e9f1ff"/>` + (on ? `<g class="flame" style="animation-delay:${i * 90}ms"><path d="M${x} 62 q-9 14 0 24 q9 -10 0 -24z" fill="#ffb627"/><path d="M${x} 72 q-4 8 0 14 q4 -6 0 -14z" fill="#fff3b0"/></g>` : "");
    });
    c += `<rect x="154" y="52" width="12" height="46" rx="2" fill="#e9f1ff"/><g class="flame"><path d="M160 28 q-9 14 0 24 q9 -10 0 -24z" fill="#ffb627"/><path d="M160 38 q-4 8 0 14 q4 -6 0 -14z" fill="#fff3b0"/></g>`;
    return `<svg viewBox="0 0 320 210" class="scene">${c}
<path d="M24 132 h272 M30 132 q0 36 130 36 q130 0 130 -36" fill="none" stroke="#f1c75a" stroke-width="6" stroke-linecap="round"/>
<rect x="156" y="98" width="8" height="70" fill="#f1c75a"/><path d="M110 188 h100 l-12 -20 h-76z" fill="#f1c75a"/></svg>`;
  },
  dreidel: () => `<svg viewBox="0 0 100 120" class="scene dreidel"><g class="spin"><path d="M50 4 v14" stroke="#c9a15a" stroke-width="6" stroke-linecap="round"/><rect x="24" y="20" width="52" height="46" rx="6" fill="#2f6bd9" stroke="#1a3f8a" stroke-width="3"/><path d="M24 66 L50 112 L76 66z" fill="#2457b8" stroke="#1a3f8a" stroke-width="3"/><text x="50" y="54" font-size="26" fill="#fff" text-anchor="middle" font-family="serif">נ</text></g></svg>`,
};

/* ------------------------------------------------------------------ styles */
const STYLE = `
:host{display:block;--cols:5;--acc:#ffd23f;container-type:inline-size}
*{box-sizing:border-box}
.wrap{position:relative;overflow:hidden;border-radius:18px;padding:16px;color:var(--text);background:var(--bg);min-height:320px;font-family:var(--ha-card-font-family,Roboto,system-ui,sans-serif)}
.d-winter{--bg:linear-gradient(#0b1b3d,#17306b 55%,#27498f);--text:#eef5ff;--d1:#e8f2ff;--d2:#bcd7f5;--dt:#1b3a73;--acc:#8fd0ff;--back:#0e2554}
.d-santa{--bg:linear-gradient(#8f1d22,#b3262c 60%,#7a161b);--text:#fff6e5;--d1:#1f7a45;--d2:#f4ead2;--dt:#fff;--acc:#ffd23f;--back:#5b0f13}
.d-menorah{--bg:linear-gradient(#0a1f5c,#133a99 60%,#0d2a73);--text:#f2f6ff;--d1:#f4f8ff;--d2:#c8d9fa;--dt:#133a99;--acc:#f1c75a;--back:#0a1d52}
.scenery{position:absolute;left:0;bottom:0;width:100%;height:90px;pointer-events:none;opacity:.9}
header{position:relative;display:flex;align-items:center;gap:10px;margin-bottom:12px;z-index:2}
.titlebar{flex:1;display:flex;align-items:center;flex-wrap:wrap;gap:6px 18px;min-width:0}
h2{margin:0;font-size:clamp(1.3rem,3.6cqw,2.2rem);text-shadow:0 2px 6px rgba(0,0,0,.35)}
.count{font-size:clamp(1.15rem,3.3cqw,1.95rem);font-weight:700;color:var(--acc);padding:2px 16px;border-radius:999px;background:rgba(255,255,255,.14);text-shadow:0 1px 4px rgba(0,0,0,.4);white-space:nowrap}
#main{height:100%}
.wrap.fit{height:100%;display:flex;flex-direction:column;overflow:auto}
.fit header{flex:0 0 auto}
.fit .grid{flex:1 1 auto;min-height:360px;grid-auto-rows:unset;grid-template-rows:repeat(var(--rows),minmax(0,1fr))}
.alist{margin:8px 0 0;padding:0;list-style:none}.alist li{display:flex;gap:8px;align-items:flex-start;margin-bottom:6px}.alist textarea{flex:1;min-height:48px}
.plan summary{cursor:pointer;margin:12px 0 4px;font-weight:600}.plan ol{margin:6px 0 0;padding-left:0;list-style:none;font-size:.82rem}
.plan li{padding:3px 0;border-top:1px solid rgba(255,255,255,.12);display:flex;gap:8px}.plan li b{flex:0 0 5.5em;opacity:.85;font-weight:600}.plan li i{opacity:.7;font-style:normal}
.sub{font-size:.85rem;opacity:.85}
.iconbtn{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.25);color:inherit;border-radius:10px;padding:6px 10px;cursor:pointer;font-size:1rem}
.iconbtn.on{background:var(--acc);color:#222}
.grid{position:relative;z-index:2;display:grid;gap:10px;grid-template-columns:repeat(var(--cols),1fr);grid-auto-flow:dense;grid-auto-rows:calc((100cqw - 32px - (var(--cols) - 1) * 10px)/var(--cols))}
.door{position:relative;perspective:700px;border:0;padding:0;background:none;cursor:pointer;font:inherit;color:inherit;min-width:0;min-height:0}
.door.big{grid-column:span 2;grid-row:span 2}.door.wide{grid-column:span 2}
.door .back{position:absolute;inset:0;border-radius:10px;background:var(--back);box-shadow:inset 0 0 14px rgba(0,0,0,.6);display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;overflow:hidden}
.door .back .ico{font-size:clamp(1.2rem,6cqw,2.4rem)}.door.big .back .ico{font-size:clamp(2rem,12cqw,4.2rem)}
.door .back .dn{font-size:.7rem;opacity:.7}
.door .front{position:absolute;inset:0;border-radius:10px;transform-origin:left center;transition:transform .7s cubic-bezier(.3,.7,.2,1);display:flex;align-items:center;justify-content:center;flex-direction:column;
  background:linear-gradient(135deg,var(--d1),var(--d2));color:var(--dt);box-shadow:0 3px 8px rgba(0,0,0,.35),inset 0 0 0 3px rgba(255,255,255,.35);backface-visibility:hidden}
.d-santa .door:nth-child(even) .front{background:linear-gradient(135deg,#f4ead2,#e5d7b4);color:#a31e25}
.door .front .num{font-weight:800;font-size:clamp(1.1rem,6cqw,2rem)}.door.big .front .num{font-size:clamp(2rem,13cqw,4.5rem)}
.door .front .deco{position:absolute;top:5px;right:7px;font-size:.8rem;opacity:.7}
.door .front .knob{position:absolute;right:9px;top:50%;width:9px;height:9px;border-radius:50%;background:var(--acc);box-shadow:0 0 0 2px rgba(0,0,0,.25)}
.door .front .date{font-size:.62rem;opacity:.75;margin-top:2px}
.door.open .front{transform:rotateY(-112deg)}
.door.locked .front{filter:saturate(.55) brightness(.9)}
.door.locked:active{animation:shake .35s}
.door:not(.open):not(.locked):hover .front{transform:rotateY(-14deg)}
.door.pending .front{box-shadow:0 0 0 3px var(--acc),0 0 18px var(--acc),0 3px 8px rgba(0,0,0,.35)}
.door.todo .front{animation:pulse 1.8s ease-in-out infinite}
@keyframes shake{25%{transform:translateX(-4px)}75%{transform:translateX(4px)}}
@keyframes pulse{50%{box-shadow:0 0 0 3px var(--acc),0 0 16px var(--acc),0 3px 8px rgba(0,0,0,.35)}}
.banner{position:relative;z-index:2;margin:0 0 10px;padding:8px 12px;border-radius:10px;background:rgba(255,210,63,.18);border:1px dashed var(--acc);font-size:.85rem}
.panel{position:relative;z-index:2;margin-top:14px;padding:14px;border-radius:12px;background:rgba(0,0,0,.35);backdrop-filter:blur(4px);font-size:.9rem}
.panel h3{margin:.2em 0 .6em;font-size:1rem}.panel label{display:block;margin:8px 0 3px;font-size:.78rem;opacity:.85}
.panel select,.panel input,.panel textarea{width:100%;padding:7px 9px;border-radius:8px;border:1px solid rgba(255,255,255,.3);background:rgba(255,255,255,.92);color:#111;font:inherit}
.panel textarea{min-height:60px;resize:vertical}
.row{display:flex;gap:8px;flex-wrap:wrap;align-items:flex-end}.row>*{flex:1;min-width:110px}
.btn{cursor:pointer;border:0;border-radius:9px;padding:8px 14px;font:inherit;font-weight:600;background:var(--acc);color:#1a1a1a}
.btn.ghost{background:rgba(255,255,255,.15);color:inherit}.btn.danger{background:#d9534f;color:#fff}
.clist{margin:10px 0 0;padding:0;list-style:none}.clist li{display:flex;gap:8px;align-items:center;padding:5px 0;border-top:1px solid rgba(255,255,255,.15)}
.clist li span{flex:1}
.toast{position:absolute;left:50%;bottom:14px;transform:translateX(-50%);z-index:20;background:rgba(0,0,0,.8);color:#fff;padding:8px 14px;border-radius:20px;font-size:.85rem;pointer-events:none}
/* modal */
.modal{position:fixed;inset:0;z-index:99999;background:rgba(5,10,30,.82);display:flex;align-items:center;justify-content:center;animation:fade .3s}
.modal.finale{background:radial-gradient(circle at 50% 40%,rgba(20,20,70,.96),rgba(0,0,10,.98))}
@keyframes fade{from{opacity:0}}
.mcard{position:relative;z-index:2;width:min(92vw,520px);max-height:92vh;overflow:auto;text-align:center;color:#fff;padding:18px 18px 16px;border-radius:20px;background:rgba(15,25,60,.55);border:1px solid rgba(255,255,255,.2);animation:pop .5s cubic-bezier(.2,1.4,.4,1)}
@keyframes pop{from{transform:scale(.6);opacity:0}}
.mcard .stage{position:relative;height:210px;display:flex;align-items:center;justify-content:center}
.mcard .kind{font-size:.8rem;letter-spacing:.12em;text-transform:uppercase;opacity:.75;margin-top:6px}
.mcard .txt{font-size:1.15rem;line-height:1.4;margin:8px 0}.mcard .txt b{color:#ffd23f}
.mcard.big .txt{font-size:1.5rem}
.mcard h1{margin:4px 0;font-size:2.1rem;color:#ffd23f;text-shadow:0 0 18px rgba(255,210,63,.6)}
.mcard .emoji{font-size:5rem;animation:bounce 1.2s infinite}
@keyframes bounce{50%{transform:translateY(-10px) scale(1.06)}}
.mfx{position:absolute;inset:0;width:100%;height:100%;z-index:1;pointer-events:none}
.mbtns{display:flex;gap:8px;justify-content:center;margin-top:10px}
.scene{width:100%;height:100%;max-height:210px;overflow:visible}
.elf{animation:rock 1.1s ease-in-out infinite;transform-origin:86px 186px}.elf .arm{animation:swing 1.1s ease-in-out infinite;transform-origin:98px 128px}
@keyframes rock{50%{transform:rotate(3deg)}}@keyframes swing{50%{transform:rotate(-24deg)}}
.stage:has(.toys) .scene{position:absolute}
.toys{position:absolute;inset:0;pointer-events:none}.toys span{position:absolute;left:calc(26% + var(--i)*3%);top:30%;font-size:1.6rem;animation:toss 3.2s ease-in infinite;animation-delay:calc(var(--i)*.5s);opacity:0}
@keyframes toss{0%{opacity:1;transform:translate(0,0) scale(1)}55%{opacity:1;transform:translate(70px,-48px) rotate(180deg) scale(1.1)}100%{opacity:0;transform:translate(150px,30px) rotate(360deg) scale(.5)}}
.sleigh .fly{animation:glide 5s ease-in-out infinite alternate}@keyframes glide{from{transform:translate(-30px,6px)}to{transform:translate(70px,-8px)}}
.globe{cursor:pointer;max-width:200px}.gift{cursor:pointer;max-width:200px}
.gift .lid{transition:transform .5s cubic-bezier(.3,1.5,.5,1)}.gift.opened .lid{transform:translate(18px,-70px) rotate(24deg)}
.giftpop{position:absolute;left:50%;top:40%;transform:translate(-50%,0) scale(0);font-size:3.4rem;transition:.6s .15s cubic-bezier(.3,1.6,.5,1)}.giftpop.show{transform:translate(-50%,-70px) scale(1)}
.orn{animation:ornpop .5s both}@keyframes ornpop{from{r:0;opacity:0}}
.flame{transform-box:fill-box;transform-origin:50% 100%;animation:flick .5s ease-in-out infinite alternate}@keyframes flick{from{transform:scale(1,1)}to{transform:scale(.88,1.1) rotate(2deg)}}
.dreidel{max-width:90px}.spin{transform-box:fill-box;transform-origin:50% 50%;animation:dspin 2s ease-out infinite}@keyframes dspin{from{transform:rotateY(0)}to{transform:rotateY(1440deg)}}
.lights{width:100%;display:flex;justify-content:space-around;align-items:flex-start}
.bulb{width:16px;height:22px;border-radius:50% 50% 50% 50%/40% 40% 60% 60%;animation:twinkle 1.2s infinite alternate;box-shadow:0 0 12px currentColor;background:currentColor;margin-top:calc(var(--i)%2*14px)}
@keyframes twinkle{from{opacity:.35}to{opacity:1}}
.dayno{font-size:.8rem;opacity:.7}
@media (prefers-reduced-motion:reduce){.elf,.elf .arm,.sleigh .fly,.bulb,.flame,.spin,.toys span,.door.todo .front{animation:none!important}}
`;

/* ------------------------------------------------------------------ the card */
class AdventCalendarCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._st = null; this._parent = false; this._pin = null; this._idle = 0; this._preview = new Set(); this._modal = null; this._sig = "";
    this._loaded = false; this._busy = false; this._hold = false;
  }
  setConfig(config) { this._config = config || {}; }
  getCardSize() { return 8; }
  static getStubConfig() { return {}; }

  set hass(hass) {
    this._hass = hass;
    if (!this._loaded) { this._loaded = true; this._init(); }
  }
  get hass() { return this._hass; }

  async _init() {
    this.shadowRoot.addEventListener("pointerdown", () => this._armIdle());
    this._onResize = () => this._applyFit(); window.addEventListener("resize", this._onResize);
    await this._refresh();
    try { this._unsub = await this._hass.connection.subscribeEvents(() => { if (!this._hold) this._refresh(); }, "advent_calendar_updated"); } catch (e) {}
    this._timer = setInterval(() => { if (!this._hold && !document.hidden) this._refresh(); }, 5 * 60 * 1000);
  }
  disconnectedCallback() { try { this._unsub && this._unsub(); } catch (e) {} clearInterval(this._timer); clearTimeout(this._idleT); window.removeEventListener("resize", this._onResize); this._pin = null; this._parent = false; this._closeModal(); this._loaded = false; }

  async _refresh() {
    try { this._st = await this._hass.callWS({ type: "advent_calendar/get_state", ...(this._parent && this._pin ? { pin: this._pin } : {}) }); this._err = null; }
    catch (e) {
      if (this._parent && e && (e.code === "invalid_pin" || e.code === "locked")) { this._exitParent(e.message); return this._refresh(); }
      this._err = e && e.message ? e.message : "Advent Calendar integration is not set up. Add it under Settings → Devices & services.";
    }
    this._render();
  }

  /* ---------- derived ---------- */
  _isOpen(d) { return d.opened || this._preview.has(d.day); }
  _content(day) {
    const st = this._st, d = st.days.find((x) => x.day === day);
    if (d && d.custom) return { custom: true, ...d.custom };
    return { custom: false, ...(this._plan || buildPlan(st.family, null))[day] };
  }
  _icon(day) {
    const c = this._content(day), st = this._st;
    if (c.custom) return c.emoji || "🎁";
    if (day === FAMILY_DAYS[st.family]) return st.family === "menorah" ? "🕎" : "🎄";
    return KIND_ICON[c.k] || "🎁";
  }

  /* ---------- render ---------- */
  _render() {
    const st = this._st;
    // Render into a dedicated container so an open modal (a sibling) survives re-renders.
    if (!this._main) { this.shadowRoot.innerHTML = `<style>${STYLE}</style><div id="main"></div>`; this._main = this.shadowRoot.getElementById("main"); }
    const root = this._main;
    if (this._err || !st) { root.innerHTML = `<div class="wrap d-winter"><b>Advent Calendar</b><div class="sub">${esc(this._err || "Loading…")}</div></div>`; return; }
    const sig = JSON.stringify([st.settings, st.days.map((d) => [d.opened, d.available, d.has_custom, d.custom]), st.today, this._parent, [...this._preview], st.is_parent, st.activities]);
    if (sig === this._sig && root.querySelector(".wrap.d-" + st.settings.design)) return;
    this._sig = sig;
    const s = st.settings, fam = st.family, n = FAMILY_DAYS[fam];
    const active = this._parent ? null : st.days.find((d) => d.available && !d.opened);
    const order = s.order === "random" ? seededOrder(n, s.shuffle_seed) : Array.from({ length: n }, (_, i) => i + 1);
    const cols = fam === "menorah" ? 4 : 5;
    let big = new Set(), rows = Math.ceil(n / cols);
    if (s.sizes === "varied") { const r = layoutBigDoors(fam, s.shuffle_seed, order, cols); big = r.set; rows = r.rows; }
    this._plan = buildPlan(fam, st.activities && st.activities[fam]);
    this._fit = this._config.fit === true || (this._config.fit !== false && inPanel(this));
    const openCount = st.days.filter((d) => d.opened).length;
    const title = s.title || (s.design === "menorah" ? "Hanukkah Calendar" : s.design === "santa" ? "Santa's Advent Calendar" : "Advent Calendar");
    const sub = countdownText(st);
    const doors = order.map((day) => {
      const d = st.days.find((x) => x.day === day), open = this._isOpen(d), locked = !d.available && !this._parent;
      const cls = ["door", open ? "open" : "", locked ? "locked" : "", big.has(day) ? (fam === "menorah" ? "wide" : "big") : "", this._preview.has(day) ? "pending" : "", active && active.day === day ? "todo" : ""].join(" ");
      const label = `Door ${day}` + (open ? ", opened" : locked ? `, opens ${prettyDate(d.date)}` : "");
      return `<button class="${cls}" data-day="${day}" aria-label="${esc(label)}">
        <div class="back"><div class="ico">${esc(open ? this._icon(day) : "")}</div><div class="dn">${open ? "Day " + day : ""}</div></div>
        <div class="front"><span class="deco">${s.design === "menorah" ? "✡" : s.design === "santa" ? "★" : "❄"}</span><span class="num">${day}</span>${locked || fam === "menorah" ? `<span class="date">${prettyDate(d.date)}</span>` : ""}<span class="knob"></span></div></button>`;
    }).join("");
    const hills = `<svg class="scenery" viewBox="0 0 400 90" preserveAspectRatio="none"><path d="M0 90 V50 q60 -30 120 -8 t130 -4 t150 -10 V90z" fill="rgba(255,255,255,.88)"/>${s.design === "menorah" ? "" : '<path d="M30 56 l12 -26 l12 26z M60 58 l9 -20 l9 20z M330 50 l11 -24 l11 24z" fill="#14522f"/>'}</svg>`;
    root.innerHTML = `<div class="wrap d-${esc(s.design)}${this._fit ? " fit" : ""}" style="--cols:${cols};--rows:${rows}">
      <header><div class="titlebar"><h2>${esc(title)}</h2><span class="count">${esc(sub)}</span></div>
        <button class="iconbtn ${this._parent ? "on" : ""}" id="pm" title="Parent mode" aria-label="Parent mode">${this._parent ? "🔓 Parent" : "🔒"}</button></header>
      ${this._parent ? `<div class="banner">Parent mode: tap any door to preview it. Previews are <b>not saved</b> and disappear when you turn parent mode off.</div>` : ""}
      <div class="grid">${doors}</div>
      ${this._parent ? this._panelHtml() : ""}
      ${hills}
    </div>`;
    this._bind();
    this._applyFit();
  }

  /* Panel view: size the card to the visible screen so the whole calendar fits without scrolling. */
  _applyFit() {
    if (!this._fit) { this.style.height = ""; return; }
    requestAnimationFrame(() => {
      const top = Math.max(0, this.getBoundingClientRect().top);
      this.style.height = Math.max(320, window.innerHeight - top - 4) + "px";
    });
  }

  _panelHtml() {
    const st = this._st, s = st.settings, fam = st.family, n = FAMILY_DAYS[fam];
    const opt = (v, cur, label) => `<option value="${v}" ${v === cur ? "selected" : ""}>${label}</option>`;
    const customs = st.days.filter((d) => d.custom);
    const dayOpts = st.days.map((d) => `<option value="${d.day}">Day ${d.day} (${prettyDate(d.date)})</option>`).join("");
    return `<div class="panel">
      <h3>Calendar options</h3>
      <div class="row">
        <div><label>Design</label><select id="s-design">${["winter", "santa", "menorah"].map((v) => opt(v, s.design, DESIGN_LABEL[v])).join("")}</select></div>
        <div><label>Door order</label><select id="s-order">${opt("sequential", s.order, "In order")}${opt("random", s.order, "Randomized")}</select></div>
        <div><label>Door sizes</label><select id="s-sizes">${opt("uniform", s.sizes, "All the same")}${opt("varied", s.sizes, "Some larger")}</select></div>
      </div>
      <div class="row" style="margin-top:8px"><div><label>Title (optional)</label><input id="s-title" maxlength="60" value="${esc(s.title)}" placeholder="e.g. The Elliott Family Advent"></div>
        <button class="btn ghost" id="reshuffle" style="flex:0 0 auto">🔀 Reshuffle</button></div>
      <h3 style="margin-top:16px">Your own door</h3>
      <div class="row"><div><label>Day</label><select id="c-day">${dayOpts}</select></div>
        <div style="flex:0 0 90px;min-width:80px"><label>Emoji</label><input id="c-emoji" maxlength="8" placeholder="🌮"></div>
        <div><label>Title</label><input id="c-title" maxlength="60" placeholder="Lunch surprise"></div></div>
      <label>Message</label><textarea id="c-msg" maxlength="280" placeholder="You're going to Chipotle for lunch today!"></textarea>
      <div class="mbtns" style="justify-content:flex-start"><button class="btn" id="c-save">Save door</button><button class="btn ghost" id="c-preview">Preview</button></div>
      ${customs.length ? `<ul class="clist">${customs.map((d) => `<li><span>Day ${d.day}: ${esc(d.custom.emoji)} ${esc(d.custom.title || d.custom.message.slice(0, 30))}</span><button class="btn ghost" data-edit="${d.day}">Edit</button><button class="btn danger" data-del="${d.day}">Delete</button></li>`).join("")}</ul>` : ""}
      ${this._activitiesHtml()}
      <div class="mbtns" style="justify-content:flex-start;margin-top:14px"><button class="btn danger" id="reset">Reset all opened doors</button></div>
    </div>`;
  }

  _activitiesHtml() {
    const st = this._st, fam = st.family, max = MAX_ACTIVITIES[fam];
    if (!this._draft || this._draftFam !== fam) { this._draft = (st.activities && st.activities[fam] != null ? st.activities[fam] : defaultActivities(fam)).slice(); this._draftFam = fam; }
    const plan = this._plan || buildPlan(fam, null), n = FAMILY_DAYS[fam];
    const rows = st.days.map((d) => {
      const c = d.custom ? { k: "custom", t: `${d.custom.emoji} ${d.custom.title ? d.custom.title + ": " : ""}${d.custom.message}` } : plan[d.day];
      const t = c.t.length > 110 ? c.t.slice(0, 107) + "…" : c.t;
      return `<li><b>Day ${d.day}</b><span><i>${esc(c.k)}${c.fx ? " · " + esc(c.fx) : ""}</i> ${esc(t)}${c.p ? ` <i>(${esc(c.p)})</i>` : ""}</span></li>`;
    }).join("");
    return `<h3 style="margin-top:16px">Activities <span class="sub">(${this._draft.length} of ${max} max)</span></h3>
      <div class="sub">Edit, add or remove the family activities. They are spread evenly across the calendar. More activities replace jokes and facts; fewer are filled in with extra jokes and fun things like the snow globe. Your own day-specific doors above always win.</div>
      <ul class="alist">${this._draft.map((t, i) => `<li><textarea data-act="${i}" maxlength="280" aria-label="Activity ${i + 1}">${esc(t)}</textarea><button class="btn danger" data-actdel="${i}" aria-label="Remove activity ${i + 1}">✕</button></li>`).join("")}</ul>
      <div class="mbtns" style="justify-content:flex-start"><button class="btn ghost" id="a-add" ${this._draft.length >= max ? "disabled" : ""}>+ Add activity</button><button class="btn" id="a-save">Save activities</button><button class="btn ghost" id="a-reset">Reset to defaults</button></div>
      <details class="plan" ${this._planOpen ? "open" : ""}><summary>Full ${n}-day plan (spoilers!)</summary><ol>${rows}</ol></details>`;
  }

  _bind() {
    const $ = (sel) => this._main.querySelector(sel), $$ = (sel) => this._main.querySelectorAll(sel);
    $$(".door").forEach((b) => b.addEventListener("click", () => this._clickDoor(Number(b.dataset.day), b)));
    const pm = $("#pm"); if (pm) pm.addEventListener("click", () => this._toggleParent());
    if (!this._parent) return;
    const set = async (changes) => { try { await this._p("set_settings", changes); await this._refresh(); } catch (e) { this._parentErr(e); } };
    $("#s-design").onchange = (e) => { this._preview.clear(); set({ design: e.target.value }); };
    $("#s-order").onchange = (e) => set({ order: e.target.value });
    $("#s-sizes").onchange = (e) => set({ sizes: e.target.value });
    $("#s-title").onchange = (e) => set({ title: e.target.value });
    $("#reshuffle").onclick = () => set({ reshuffle: true });
    const form = () => ({ day: Number($("#c-day").value), emoji: $("#c-emoji").value, title: $("#c-title").value, message: $("#c-msg").value });
    const fill = (day) => { const d = this._st.days.find((x) => x.day === day); $("#c-day").value = day; if (d && d.custom) { $("#c-emoji").value = d.custom.emoji; $("#c-title").value = d.custom.title; $("#c-msg").value = d.custom.message; } else { $("#c-emoji").value = ""; $("#c-title").value = ""; $("#c-msg").value = ""; } };
    $("#c-day").onchange = (e) => fill(Number(e.target.value));
    $("#c-save").onclick = async () => { const f = form(); if (!f.message.trim()) return this._toast("Add a message first"); try { await this._p("set_custom", { family: this._st.family, ...f }); this._toast("Saved"); await this._refresh(); } catch (e) { this._parentErr(e); } };
    $("#c-preview").onclick = () => { const f = form(); this._showModal(f.day, { custom: true, title: f.title, message: f.message, emoji: f.emoji || "🎁" }); };
    $$("[data-edit]").forEach((b) => b.onclick = () => { fill(Number(b.dataset.edit)); $("#c-msg").scrollIntoView({ block: "center" }); });
    $$("[data-del]").forEach((b) => b.onclick = async () => { if (!confirm(`Delete the custom door for day ${b.dataset.del}?`)) return; try { await this._p("delete_custom", { family: this._st.family, day: Number(b.dataset.del) }); await this._refresh(); } catch (e) { this._parentErr(e); } });
    const rerender = () => { this._sig = ""; this._render(); };
    $$("[data-act]").forEach((t) => t.addEventListener("input", () => { this._draft[Number(t.dataset.act)] = t.value; }));
    $$("[data-actdel]").forEach((b) => b.onclick = () => { this._draft.splice(Number(b.dataset.actdel), 1); rerender(); });
    $("#a-add").onclick = () => { this._draft.push(""); rerender(); const all = this._main.querySelectorAll("[data-act]"); all[all.length - 1] && all[all.length - 1].focus(); };
    const saveActs = async (acts) => { try { await this._p("set_activities", { family: this._st.family, activities: acts }); this._draft = null; this._sig = ""; this._toast(acts === null ? "Activities reset" : "Activities saved"); await this._refresh(); } catch (e) { this._parentErr(e); } };
    $("#a-save").onclick = () => saveActs(this._draft.map((x) => x.trim()).filter(Boolean));
    $("#a-reset").onclick = () => { if (confirm("Restore the built-in activities?")) saveActs(null); };
    const pl = $(".plan"); if (pl) pl.addEventListener("toggle", () => { this._planOpen = pl.open; });
    $("#reset").onclick = async () => { if (!confirm("Close ALL opened doors for this year? This cannot be undone.")) return; try { await this._p("reset"); this._preview.clear(); await this._refresh(); } catch (e) { this._parentErr(e); } };
  }

  /* ---------- parent mode (PIN verified server-side; the PIN lives only in memory while unlocked) ---------- */
  _p(type, extra = {}) { return this._hass.callWS({ type: `advent_calendar/${type}`, pin: this._pin, ...extra }); }
  _parentErr(e) {
    if (e && (e.code === "invalid_pin" || e.code === "locked")) { this._exitParent(e.message); this._refresh(); }
    else this._toast((e && e.message) || "Failed");
  }
  _exitParent(msg) {
    this._parent = false; this._pin = null; this._draft = null; this._preview.clear(); this._closeModal(); clearTimeout(this._idleT);
    this._sig = ""; if (msg) this._toast(msg);
  }
  _armIdle() { clearTimeout(this._idleT); if (this._parent) this._idleT = setTimeout(() => { this._exitParent("Parent mode timed out"); this._refresh(); }, 5 * 60 * 1000); }
  _toggleParent() {
    if (this._parent) { this._exitParent(); this._render(); } else this._askPin();
  }
  _askPin() {
    this._closeModal();
    const el = document.createElement("div"); el.className = "modal";
    el.innerHTML = `<div class="mcard" style="width:min(88vw,340px)"><h1 style="font-size:1.4rem">Parent PIN</h1>
      <div class="txt" style="font-size:.95rem">Enter the PIN to open parent mode.</div>
      <input id="pin" type="password" inputmode="numeric" autocomplete="off" maxlength="8" aria-label="Parent PIN" style="width:100%;font-size:1.6rem;text-align:center;letter-spacing:.4em;padding:8px;border-radius:10px;border:0">
      <div id="perr" class="sub" style="min-height:1.4em;color:#ffb3b3;margin-top:6px"></div>
      <div class="mbtns"><button class="btn ghost" id="pcancel">Cancel</button><button class="btn" id="pok">Unlock</button></div></div>`;
    this.shadowRoot.appendChild(el); this._modal = { el, fx: null };
    const input = el.querySelector("#pin"), err = el.querySelector("#perr"); input.focus();
    const submit = async () => {
      const pin = input.value.trim(); if (!pin) return;
      try { await this._hass.callWS({ type: "advent_calendar/verify_pin", pin }); }
      catch (e) { err.textContent = (e && e.message) || "Incorrect PIN"; input.value = ""; input.focus(); return; }
      this._pin = pin; this._parent = true; this._closeModal(); this._armIdle(); await this._refresh();
    };
    el.querySelector("#pok").onclick = submit; el.querySelector("#pcancel").onclick = () => this._closeModal();
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); if (e.key === "Escape") this._closeModal(); });
    el.addEventListener("click", (e) => { if (e.target === el) this._closeModal(); });
  }

  _toast(msg) {
    const w = this._main && this._main.querySelector(".wrap"); if (!w) return;
    const t = document.createElement("div"); t.className = "toast"; t.textContent = msg; w.appendChild(t); setTimeout(() => t.remove(), 2200);
  }

  async _clickDoor(day, el) {
    if (this._busy) return;
    const st = this._st, d = st.days.find((x) => x.day === day);
    if (this._isOpen(d)) return this._showModal(day);           // replay an already-open door
    if (!d.available && !this._parent) return this._toast(`Not yet! This door opens on ${prettyDate(d.date)}.`);
    this._busy = true; this._hold = true;
    try {
      if (this._parent) { this._preview.add(day); el.classList.add("open", "pending"); }   // preview only, never saved
      else {
        await this._hass.callWS({ type: "advent_calendar/open_door", day }); el.classList.add("open");
        // The server only reveals a custom door's content once it is opened, so re-read state (without re-rendering the grid mid-animation).
        try { this._st = await this._hass.callWS({ type: "advent_calendar/get_state" }); } catch (e) { /* fall back to built-in content */ }
      }
      await sleep(650);
      this._showModal(day);
    } catch (e) { this._toast(e.message === "not_yet" ? "Not yet!" : "Couldn't open that door"); }
    finally { this._busy = false; this._hold = false; this._sig = ""; await this._refresh(); }
  }

  /* ---------- modal & effects ---------- */
  _closeModal() { if (this._modal) { this._modal.fx && this._modal.fx.stop(); this._modal.el.remove(); this._modal = null; } }

  _showModal(day, override) {
    this._closeModal();
    const st = this._st, fam = st.family, finale = day === FAMILY_DAYS[fam];
    const c = override || this._content(day);
    const fx = c.fx || FX_CYCLE[day % FX_CYCLE.length];
    const openN = st.days.filter((d) => d.opened || this._preview.has(d.day)).length;
    const el = document.createElement("div"); el.className = "modal" + (finale && !override ? " finale" : "");
    let stage = "", head = "", body = "";
    if (c.custom) {
      stage = `<div class="emoji">${esc(c.emoji || "🎁")}</div>`; head = c.title ? `<h1 style="font-size:1.6rem">${esc(c.title)}</h1>` : "";
      body = `<div class="txt">${esc(c.message)}</div><div class="kind">A special surprise for day ${day}</div>`;
    } else if (finale) {
      const m = fam === "menorah";
      stage = m ? SVG.menorah(8) : SVG.tree(24);
      head = `<h1>${m ? "Chag Urim Sameach!" : "Merry Christmas!"}</h1>`;
      body = `<div class="txt">${esc(c.t)}</div>`;
    } else {
      if (c.fx === "dreidel") stage = `<div style="width:130px;height:190px">${SVG.dreidel()}</div>`;
      else if (fam === "menorah") stage = SVG.menorah(day) + (day % 2 === 1 ? `<div style="position:absolute;right:6%;bottom:4%;width:60px">${SVG.dreidel()}</div>` : "");
      else if (fx === "sack") stage = SVG.sack(); else if (fx === "globe") stage = SVG.globe(); else if (fx === "gift") stage = SVG.gift();
      else if (fx === "sleigh") stage = SVG.sleigh(); else if (fx === "tree") stage = SVG.tree(openN);
      else if (fx === "lights") stage = `<div class="lights">${Array.from({ length: 9 }, (_, i) => `<span class="bulb" style="--i:${i};color:${["#ff4d4d", "#ffd23f", "#3ddc97", "#4da3ff", "#ff7bd5"][i % 5]};animation-delay:${i * 130}ms"></span>`).join("")}</div>`;
      else stage = `<div class="emoji">❄️</div>`;
      head = `<div class="dayno">Day ${day}</div>`;
      const hint = FX_HINT[fx] && fam !== "menorah" && c.k !== "fun" ? `<div class="kind">${FX_HINT[fx]}</div>` : "";
      body = `<div class="kind">${KIND_ICON[c.k] || ""} ${esc(c.k)}</div><div class="txt">${esc(c.t)}${c.p ? `<br><br><span class="punch" hidden><b>${esc(c.p)}</b></span><button class="btn" id="punch">Tap for the answer</button>` : ""}</div>${hint}`;
    }
    el.innerHTML = `<canvas class="mfx"></canvas><div class="mcard ${finale ? "big" : ""}"><div class="stage">${stage}</div>${head}${body}
      <div class="mbtns"><button class="btn ghost" id="snd">${Sound.muted ? "🔇 Sound off" : "🔊 Sound on"}</button><button class="btn" id="close">${finale ? "Hooray!" : "Close"}</button></div></div>`;
    el.addEventListener("click", (e) => { if (e.target === el) this._closeModal(); });
    this.shadowRoot.appendChild(el);
    const canvas = el.querySelector("canvas"), fxc = new FxCanvas(canvas); fxc.start();
    this._modal = { el, fx: fxc };
    const q = (s) => el.querySelector(s);
    q("#close").onclick = () => this._closeModal();
    q("#snd").onclick = (e) => { const on = Sound.toggle(); e.target.textContent = on ? "🔊 Sound on" : "🔇 Sound off"; if (on) Sound.play(CHIME); };
    const punch = q("#punch"); if (punch) punch.onclick = () => { q(".punch").hidden = false; punch.remove(); fxc.confetti(40); Sound.play(CHIME); };

    if (finale && !override) { fxc.confetti(220); fxc.fireworks(12000); Sound.play(JINGLE); setTimeout(() => fxc.confetti(160), 3500); }
    else if (c.custom) { fxc.confetti(90); Sound.play(CHIME); }
    else {
      if (fx === "snow" || fam === "menorah") fxc.snow(true);
      if (fx === "lights" || fx === "sleigh") fxc.snow(true);
      Sound.play(CHIME);
      if (fx === "globe") this._wireGlobe(el);
      if (fx === "gift") { const g = q("#giftsvg"), pop = q("#giftpop"); const go = () => { g.classList.add("opened"); pop.textContent = ["🧸", "🎨", "🚂", "🍪", "⭐"][day % 5]; pop.classList.add("show"); fxc.confetti(60); Sound.play(CHIME); }; g.onclick = go; setTimeout(go, 1400); }
    }
  }

  _wireGlobe(el) {
    const g = el.querySelector("#flakes"), svg = el.querySelector("#globe"); let flakes = [];
    const ns = "http://www.w3.org/2000/svg";
    for (let i = 0; i < 40; i++) { const c = document.createElementNS(ns, "circle"); c.setAttribute("r", (1.2 + Math.random() * 2).toFixed(1)); c.setAttribute("fill", "#fff"); g.appendChild(c); flakes.push({ c, x: 30 + Math.random() * 160, y: 150 + Math.random() * 30, vx: 0, vy: 0, live: false }); }
    const shake = () => flakes.forEach((f) => { f.live = true; f.x = 40 + Math.random() * 140; f.y = 60 + Math.random() * 80; f.vx = (Math.random() - 0.5) * 120; f.vy = -40 - Math.random() * 120; });
    let last = performance.now();
    const loop = (now) => { if (!el.isConnected) return; const dt = Math.min(0.05, (now - last) / 1000); last = now;
      flakes.forEach((f) => { if (f.live) { f.vy += 90 * dt; f.vx *= 0.97; f.vy = Math.min(f.vy, 40); f.x += f.vx * dt; f.y += f.vy * dt; if (f.y > 165) { f.y = 165; f.live = false; } } f.c.setAttribute("cx", f.x.toFixed(1)); f.c.setAttribute("cy", f.y.toFixed(1)); });
      requestAnimationFrame(loop); };
    flakes.forEach((f) => { f.c.setAttribute("cx", f.x); f.c.setAttribute("cy", f.y); });
    svg.onclick = shake; setTimeout(shake, 500); requestAnimationFrame(loop);
  }
}

if (!customElements.get("advent-calendar-card")) customElements.define("advent-calendar-card", AdventCalendarCard);
window.customCards = window.customCards || [];
if (!window.customCards.some((c) => c.type === "advent-calendar-card")) {
  window.customCards.push({ type: "advent-calendar-card", name: "Advent Calendar", description: "Advent / Hanukkah calendar with doors to open each day.", preview: false });
}
console.info(`%c ADVENT-CALENDAR %c v${AC_VERSION} `, "background:#b3262c;color:#fff", "background:#1f7a45;color:#fff");
