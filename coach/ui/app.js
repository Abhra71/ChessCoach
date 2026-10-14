// Knightwise desktop app: one page, a few screens (#/home, #/games, #/practice, #/settings, #/welcome).
const $ = (sel, el = document) => el.querySelector(sel);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const api = (path, body) => fetch(path, body === undefined ? {} : {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
}).then(async r => { const j = await r.json().catch(() => ({})); if (!r.ok) throw Object.assign(new Error(j.message || r.status), j); return j; });
const wait = ms => new Promise(r => setTimeout(r, ms));
const cap = s => s ? s[0].toUpperCase() + s.slice(1) : "";

const ICON = {
  home: '<path d="M3 10.5 12 3l9 7.5V21h-6v-6H9v6H3z"/>',
  games: '<path d="M4 4h16v16H4z"/><path d="M4 12h16M12 4v16"/>',
  practice: '<circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="3"/>',
  progress: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
  medal: '<circle cx="12" cy="15" r="6"/><path d="m8.5 10.5-3-7.5h4l2.5 5M15.5 10.5l3-7.5h-4L12 8"/>',
  plan: '<path d="M5 4h11l3 3v13H5z"/><path d="M8 10h8M8 14h8M8 18h5"/>',
  settings: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/>',
  hang: '<path d="M12 3 2.5 20h19z"/><path d="M12 10v4"/><path d="M12 17h.01"/>',
  fork: '<path d="M12 21v-8"/><path d="m12 13-6-7"/><path d="m12 13 6-7"/><circle cx="6" cy="4.5" r="1.6"/><circle cx="18" cy="4.5" r="1.6"/>',
  capture: '<circle cx="12" cy="12" r="7.5"/><circle cx="12" cy="12" r="2.5"/><path d="M12 1.5v4M12 18.5v4M1.5 12h4M18.5 12h4"/>',
  mate: '<path d="M4 17 3 7l5 4 4-7 4 7 5-4-1 10z"/><path d="M4 21h16"/>',
  draw: '<circle cx="12" cy="12" r="8.5"/><path d="M8 10h8M8 14h8"/>',
  flame: '<path d="M12 22c4 0 7-2.7 7-7 0-3.5-2.2-5.6-3.6-7.5-.5 1.9-1.4 3-2.6 3.5.3-3.4-1-6.6-3.8-9-.3 3.4-2 5.7-3.6 7.6C4.2 11.3 5 13 5 15c0 4.3 3 7 7 7Z"/>',
  bolt: '<path d="M13 2 4 14h7l-1 8 9-12h-7z"/>',
  down: '<path d="M12 5v14M6 13l6 6 6-6"/>', up: '<path d="M12 19V5M6 11l6-6 6 6"/>',
  pawn: '<path fill="currentColor" stroke="none" d="M12 3a3 3 0 0 0-1.8 5.4C9 9.3 8.5 10.5 8.6 12h6.8c.1-1.5-.4-2.7-1.6-3.6A3 3 0 0 0 12 3Zm-3.3 10c-.4 2.3-1.4 4-2.9 5.3V21h12.4v-2.7c-1.5-1.3-2.5-3-2.9-5.3Z"/>',
};
const svg = (name, extra = "") => `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" ${extra}>${ICON[name]}</svg>`;

const PATTERN_TITLE = {  // the habit as a headline
  "left a piece hanging": "Stop leaving pieces hanging",
  "missed a free capture": "Take the free pieces",
  "walked into a fork or trick": "Watch for forks",
  "walked into checkmate": "Check their checks",
  "missed a checkmate": "Look for checkmate first",
  "stalemated a won game": "Finish won games",
};

const HABIT = {  // each habit as a tile: an icon and a few words
  "left a piece hanging": ["hang", "Pieces left hanging"],
  "walked into a fork or trick": ["fork", "Forks and tricks"],
  "missed a free capture": ["capture", "Free pieces missed"],
  "walked into checkmate": ["mate", "Walked into mate"],
  "missed a checkmate": ["mate", "Mates missed"],
  "stalemated a won game": ["draw", "Wins thrown to a draw"],
};

// numbers roll up when a screen opens
function countUp(root = document) {
  root.querySelectorAll("[data-to]").forEach(el => {
    const to = +el.dataset.to, dec = +(el.dataset.dec || 0), t0 = performance.now(), ms = 700;
    const step = t => { const k = Math.min(1, (t - t0) / ms), e = 1 - Math.pow(1 - k, 3);
      el.textContent = (to * e).toFixed(dec); if (k < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  });
}
const roll = (v, dec = 0) => `<span class="num" data-to="${v}" data-dec="${dec}">${(0).toFixed(dec)}</span>`;

let STATUS = {};

// ---------- theme ----------
function applyTheme(theme) {
  if (theme === "dark" || theme === "light") document.documentElement.dataset.theme = theme;
  else delete document.documentElement.dataset.theme;
}

// ---------- voice ----------
const Voice = (() => {  // the coach speaks sentence by sentence; the next one is made while this one plays
  let on = true, playing = null, token = 0;
  const PAUSE = 450;  // ms between sentences: back to back they sounded rushed, though the voice itself was right
  const talkers = [], tell = v => talkers.forEach(f => { try { f(v); } catch (e) {} });
  const split = t => String(t).replace(/\s+/g, " ").split(/(?<=[.!?])\s+/).filter(Boolean);
  const audio = (text, voice) => fetch("/api/say", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(voice ? { text, voice } : { text }) }).then(r => { if (!r.ok) throw new Error("voice"); return r.blob(); }).then(b => URL.createObjectURL(b));
  const play = url => new Promise(done => { const a = new Audio(url); playing = a; a.onended = a.onerror = done; a.play().catch(done); });
  function stop() { token++; if (playing) { playing.pause(); playing = null; } tell(false); }
  async function speak(text, force, voice) {
    stop();
    if ((!on && !force) || !text) return;
    const mine = ++token, parts = split(text);
    let next = audio(parts[0], voice);
    for (let i = 0; i < parts.length; i++) {
      let url;
      try { url = await next; } catch (e) { return; }
      if (mine !== token) return;
      if (i + 1 < parts.length) next = audio(parts[i + 1], voice);
      tell(true);
      await play(url);
      if (mine !== token) return;
      if (i + 1 < parts.length) await wait(PAUSE);  // a breath between sentences, like a person (13 Oct: "too fast")
      if (mine !== token) return;
    }
    tell(false);
  }
  return { speak, stop, set(v) { on = v; if (!v) stop(); }, get on() { return on; }, onTalk: f => talkers.push(f) };
})();

// ---------- sounds: the player's picks from Kenney's CC0 packs (coach/ui/sounds) ----------
const Sound = (() => {
  let on = true;
  const cache = {};
  function play(name, volume = 0.6) {
    if (!on) return;
    try {
      const a = (cache[name] = cache[name] || new Audio(`/ui/sounds/${name}.ogg`)).cloneNode();
      a.volume = volume; a.play().catch(() => {});
    } catch (e) {}
  }
  const move = san => play(/[+#]/.test(san || "") ? "check" : /x/.test(san || "") ? "capture" : "move", 0.8);
  return { play, move, set(v) { on = v; }, get on() { return on; } };
})();

// little bursts of colour when something is finished
function confetti(n = 70) {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const layer = document.createElement("div"); layer.className = "confetti"; document.body.appendChild(layer);
  const colours = ["#36c27a", "#ff4d42", "#f0a43a", "#ffffff", "#4da3ff"];
  for (let i = 0; i < n; i++) {
    const p = document.createElement("i");
    p.style.cssText = `left:${50 + (Math.random() - .5) * 30}%;background:${colours[i % colours.length]};` +
      `--dx:${(Math.random() - .5) * 900}px;--dy:${-250 - Math.random() * 400}px;--r:${Math.random() * 720}deg;animation-delay:${Math.random() * .15}s`;
    layer.appendChild(p);
  }
  setTimeout(() => layer.remove(), 2200);
}

// ---------- microphone ----------
const Mic = (() => {  // records 16 kHz mono in the window; the coach turns it into text on this computer
  let ctx = null, stream = null, node = null, chunks = [];
  async function start() {
    fetch("/api/listen/warm").catch(() => {});
    stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
    ctx = new AudioContext({ sampleRate: 16000 });
    const src = ctx.createMediaStreamSource(stream);
    node = ctx.createScriptProcessor(4096, 1, 1);
    chunks = [];
    node.onaudioprocess = e => chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));
    src.connect(node); node.connect(ctx.destination);
  }
  async function stop() {
    if (!ctx) return "";
    node.disconnect(); stream.getTracks().forEach(t => t.stop()); await ctx.close(); ctx = null;
    const n = chunks.reduce((a, c) => a + c.length, 0), pcm = new Int16Array(n);
    let i = 0;
    for (const c of chunks) for (const v of c) pcm[i++] = Math.max(-1, Math.min(1, v)) * 32767;
    const r = await fetch("/api/listen", { method: "POST", headers: { "Content-Type": "application/octet-stream" }, body: pcm.buffer });
    const j = await r.json();
    if (!r.ok) throw new Error(j.message || "Couldn't hear that.");
    return j.text;
  }
  return { start, stop, get on() { return !!ctx; } };
})();

// a question box with a microphone: onAsk(text) answers it
function askBox(el, { placeholder, enabled, listen, onAsk, coach }) {
  el.innerHTML = `<div class="row"><input class="field" data-q placeholder="${esc(enabled ? placeholder : "Add an AI key in Settings to ask the coach")}" ${enabled ? "" : "disabled"}>
    ${listen && enabled ? `<button class="btn mic" data-mic title="Hold to talk, or click to start and stop">Talk</button>` : ""}
    <button class="btn primary" data-ask ${enabled ? "" : "disabled"}>Ask</button></div><div data-a class="small" style="margin-top:8px"></div>`;
  if (!enabled) {  // the feature is never hidden: say what a free key gives, and where to add it
    el.innerHTML = `<p class="small" style="margin:0 0 10px">Talk with your coaches and get real replies with a free AI key.</p>
      <a class="btn" href="#/settings">Set up now</a>`;
    return;
  }
  const q = $("[data-q]", el), out = $("[data-a]", el), mic = $("[data-mic]", el);
  const go = async () => {
    const text = q.value.trim(); if (!text) return;
    out.innerHTML = `<span class="muted">Thinking…</span>`;
    try { const r = await onAsk(text); out.innerHTML = `<div class="coach-says">${esc(r.text)}</div>`; Voice.speak(r.text, false, (COACHES[coach] || {}).voice); }
    catch (e) { out.innerHTML = `<span class="err">${esc(e.message)}</span>`; }
  };
  $("[data-ask]", el).onclick = go;
  q.onkeydown = e => { if (e.key === "Enter") go(); };
  if (mic) mic.onclick = async () => {
    if (!Mic.on) {
      Voice.stop();
      try { await Mic.start(); } catch (e) { out.innerHTML = `<span class="err">The microphone isn't available.</span>`; return; }
      mic.textContent = "Stop"; mic.classList.add("rec"); out.innerHTML = `<span class="muted">Listening… click Stop when you're done.</span>`;
    } else {
      mic.textContent = "Talk"; mic.classList.remove("rec"); out.innerHTML = `<span class="muted">Writing down what you said…</span>`;
      try { const text = await Mic.stop(); if (!text) { out.innerHTML = `<span class="muted">I didn't catch that. Try again.</span>`; return; }
        q.value = text; go(); }
      catch (e) { out.innerHTML = `<span class="err">${esc(e.message)}</span>`; }
    }
  };
}

// ---------- shell ----------
function shell(active, body) {
  const item = (route, name, icon) =>
    `<a href="#/${route}" class="${active === route ? "on" : ""}">${svg(icon)}<span>${name}</span></a>`;
  $("#root").innerHTML = `
    <div class="shell">
      <aside class="side">
        <div class="brand"><div class="brand-mark" style="color:var(--on-invert)">${svg("pawn")}</div><span>Knightwise</span></div>
        <nav class="nav">${item("home", "Home", "home")}${item("games", "Games", "games")}${item("practice", "Practice", "practice")}${item("plan", "Your plan", "plan")}${item("progress", "Progress", "progress")}${item("settings", "Settings", "settings")}</nav>
        <button class="btn side-voice" id="mute" title="Voice on or off">${Voice.on ? "Voice on" : "Voice off"}</button>
        <div class="side-foot" id="status"><i class="dot"></i><span>Connecting…</span></div>
      </aside>
      <main><div class="page" id="page">${body}</div></main>
    </div>`;
  paintStatus();
  $("#mute").onclick = () => {
    Voice.set(!Voice.on);
    $("#mute").textContent = Voice.on ? "Voice on" : "Voice off";
    api("/api/settings", { voice: Voice.on }).catch(() => {});
  };
}

function paintStatus() {
  const el = $("#status");
  if (!el) return;
  const s = STATUS, busy = s.phase && !["ready", "waiting for your chess.com username", "starting"].includes(s.phase);
  const text = !s.phase ? "Coach not running" : busy ? `${cap(s.phase)}${s.total ? ` ${s.done}/${s.total}` : "…"}`
    : s.phase === "error" ? "Last check failed, retrying" : `Up to date${s.last_update ? " · " + s.last_update.slice(11) : ""}`;
  el.innerHTML = `<i class="dot ${!s.phase ? "" : busy ? "busy" : "ok"}"></i><span>${esc(text)}</span>`;
}

async function pollStatus() {
  try { STATUS = await api("/api/status"); } catch (e) { STATUS = {}; }
  paintStatus();
  setTimeout(pollStatus, STATUS.phase && STATUS.phase !== "ready" ? 1500 : 6000);
}

// ---------- home ----------
function spark(points) {  // a small line, no axes: is it going down?
  if (points.length < 2) return "";
  const W = 220, H = 56, max = Math.max(...points, 1) * 1.1;
  const x = i => 4 + i * (W - 8) / (points.length - 1), y = v => H - 6 - v / max * (H - 12);
  const d = points.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const n = points.length - 1;
  return `<svg class="spark" viewBox="0 0 ${W} ${H}"><path class="line draw" d="${d}" pathLength="1"/>
    <circle class="last" cx="${x(n)}" cy="${y(points[n])}" r="4"/></svg>`;
}

function ring(part, whole) {  // a progress ring that fills
  const k = whole ? part / whole : 0, C = 2 * Math.PI * 26;
  return `<svg class="ring" viewBox="0 0 64 64"><circle cx="32" cy="32" r="26" class="track"/>
    <circle cx="32" cy="32" r="26" class="fill" style="--to:${C * (1 - k)}" stroke-dasharray="${C}" stroke-dashoffset="${C}"/></svg>`;
}

function dailyCard(d) {  // five minutes a day; the streak forgives one missed day and never scolds
  const days = ["M", "T", "W", "T", "F", "S", "S"], today = (new Date().getDay() + 6) % 7;
  const dots = (d.week || []).map((on, i) => `<i class="${on ? "on" : ""} ${i === 6 ? "today" : ""}">${days[(today - 6 + i + 7) % 7]}</i>`).join("");
  return `<a class="box daily rise ${d.done_today ? "done" : ""}" href="#/daily">
    <div class="daily-icon">${svg(d.done_today ? "flame" : "bolt")}</div>
    <div class="daily-main"><div class="label">${d.done_today ? "Done today" : "Today's 5 minutes"}</div>
      <div class="daily-title">${d.done_today ? "Nice. Back tomorrow for a new one." : "Your position, a puzzle, your opening"}</div></div>
    <div class="daily-week">${dots}</div>
    ${d.streak ? `<div class="daily-streak"><b class="num">${d.streak}</b><span>day${d.streak > 1 ? "s" : ""}</span></div>` : ""}
    <span class="btn ${d.done_today ? "" : "primary"}">${d.done_today ? "Play again" : "Start"}</span></a>`;
}

function vsCard(v) {  // you now against you before: the only rival that is always fair
  if (!v) return "";
  const row = (name, a, b, lowerBetter, unit = "") => {
    const max = Math.max(a, b, 0.1), good = lowerBetter ? a <= b : a >= b;
    return `<div class="vs-row"><div class="vs-name">${name}</div>
      <div class="vs-bars"><div class="vs-bar now ${good ? "good" : "bad"}"><i style="width:${100 * a / max}%"></i><b class="num">${a}${unit}</b></div>
        <div class="vs-bar then"><i style="width:${100 * b / max}%"></i><b class="num">${b}${unit}</b></div></div></div>`;
  };
  return `<div class="box vs" style="grid-column: span 2"><div class="row spread"><h2 style="margin:0">You vs you</h2>
      <div class="vs-key small muted"><span><i class="now"></i>${esc(v.now.label)}</span><span><i class="then"></i>${esc(v.then.label)}</span></div></div>
    ${row("Pieces given away a game", v.now.pieces, v.then.pieces, true)}
    ${row("Games won", v.now.wins, v.then.wins, false, "%")}
    ${row("Big mistakes a game", v.now.moments, v.then.moments, true)}</div>`;
}

async function daily() {
  shell("practice", `<p class="muted">Loading…</p>`);
  const d = await api("/api/daily");
  if (!d.drills.length) { $("#page").innerHTML = `<div class="empty">Today's challenge appears once your games are checked.</div>`; return; }
  $("#page").innerHTML = trainerPage("Today's 5 minutes", { back: `<a href="#/home" class="small muted" style="text-decoration:none">← Home</a>`,
    text: `Today's idea: ${d.theme}.` });
  trainer(d.drills, { coach: "maya", record: true, onDone: async right => {
    const s = await api("/api/daily/done", {}).catch(() => ({}));
    setTimeout(() => Coach.react("maya", "celebrate",
      `Done for today: ${right} of ${d.drills.length} right first time.${s.streak > 1 ? ` That's ${s.streak} days in a row.` : ""} See you tomorrow.`,
      [{ label: "Back home", app: "home" }]), 2500);
  } });
}

// ---------- your opening tree: every branch of your first moves, with your results ----------
async function openingTree() {
  shell("games", `<p class="muted">Loading…</p>`);
  const t = (await api("/api/openings")).tree || {};
  if (!t.white && !t.black) { $("#page").innerHTML = `<div class="empty">Your opening tree appears once your games are checked.</div>`; return; }
  const label = n => `${Math.ceil(n.ply / 2)}${n.ply % 2 ? "." : "..."}${n.san}`;
  const node = (n, depth) => {
    const kids = n.children.filter(c => c.games >= 2);
    const good = n.score >= 55, bad = n.score <= 40;
    const row = `<div class="tree-row"><span class="tree-move num">${esc(label(n))}</span>
      <span class="tree-name">${esc(n.name || "")}</span>
      <span class="tree-games small muted num">${n.games} game${n.games > 1 ? "s" : ""}</span>
      <span class="tree-score ${good ? "good" : bad ? "bad" : ""}"><i style="width:${n.score}%"></i><b class="num">${n.score}%</b></span></div>
      ${n.note ? `<div class="tree-note ${bad ? "bad" : "good"}">${esc(n.note)}</div>` : ""}`;
    if (!kids.length) return `<div class="tree-leaf">${row}</div>`;
    return `<details class="tree-node" ${depth < 2 || n.note ? "open" : ""}><summary>${row}</summary>
      <div class="tree-kids">${kids.map(c => node(c, depth + 1)).join("")}</div></details>`;
  };
  const side = (name, root) => root ? `<div class="box rise"><div class="row spread"><h2 style="margin:0">As ${name}</h2>
      <span class="small muted">${root.games} games · you score ${root.score}%</span></div>
      <div class="tree">${root.children.filter(c => c.games >= 2).map(c => node(c, 0)).join("")}</div></div>` : "";
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/games" class="small muted" style="text-decoration:none">← Games</a>
      <h1 style="margin-top:6px">Your opening tree</h1><p class="sub">Your first three moves in every game, and how each branch went. Score: a win is 1, a draw is half.</p></div></div>
    <div class="grid">${side("White", t.white)}${side("Black", t.black)}</div>`;
  const worst = [t.white, t.black].filter(Boolean).flatMap(function all(n) { return [n, ...n.children.flatMap(all)]; })
    .filter(n => n.note && n.score <= 40).sort((a, b) => b.games - a.games)[0];
  if (worst) Coach.react("maya", "point", `Look at ${label(worst)}${worst.name ? `, the ${worst.name}` : ""}. ${worst.note} Your plan has an opening that fixes this.`,
    [{ label: "Your plan", app: "plan" }]);
}

// ---------- try it again: one key moment of your game, on the board, with Maya ----------
async function tryAgain(gid, ply) {
  shell("games", `<p class="muted">Loading…</p>`);
  const d = await api(`/api/try/${gid}/${ply}`);
  const back = `<a href="#/games/${gid}" class="small muted" style="text-decoration:none">← Back to the game</a>`;
  $("#page").innerHTML = trainerPage("Try it again", { back, text: "The moment before your mistake. Find a better move." });
  trainer([d], { coach: "maya", record: true, onDone: right => setTimeout(() => Coach.react("maya", right ? "celebrate" : "encourage",
    right ? "That's the move you'll play next time." : "Now you know it. It will come back in your practice.",
    [{ label: "Back to the game", app: `games/${gid}` }]), 2200) });
}

// ---------- progress: Viktor's story of your week, and badges from your real games ----------
// chess.com games and Knightwise practice counted apart, never blended (13 Oct test, point 16)
const BADGE_SOURCES = [["From your chess.com games", ["Habits", "Clean play", "Results"]], ["From your Knightwise practice", ["Practice"]]];
const TIERS = ["Bronze", "Silver", "Gold"];
function badgeCard(b) {  // what you have, what's next, and whether it's complete: one look
  const state = b.tier === 3 ? "Complete" : b.tier ? `${b.tier_name} · Gold at ${b.tiers[2]}` : `Not started · Bronze at ${b.tiers[0]}`;
  return `<div class="badge t${b.tier}">
    <div class="medal">${svg(b.icon)}</div><b>${esc(b.name)}</b><div class="tier-name">${b.tier === 3 ? "✓ " : ""}${esc(state)}</div>
    <div class="small muted">${b.next ? `${b.best} of ${b.next} ${esc(b.what)}, for ${TIERS[b.tier]}` : `${b.best} ${esc(b.what)}`}</div>
    <div class="bar"><div style="width:${b.next ? Math.min(100, 100 * b.best / b.next) : 100}%"></div></div></div>`;
}
async function progressView() {
  shell("progress", `<p class="muted">Loading…</p>`);
  const p = await api("/api/progress");
  if (!p.player) return go("welcome");
  const s = p.story, r = (s && s.results) || {};
  const complete = p.badges.filter(b => b.tier === 3).length, started = p.badges.filter(b => b.tier && b.tier < 3).length;
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>Progress</h1><p class="sub">From your real chess.com games, checked by Stockfish.</p></div></div>
    <div class="grid">
      ${s ? `<div class="box story rise" id="story">
        <div class="story-head"><div><div class="label">${esc(s.title)}</div><div class="small muted">${esc(s.from)} to ${esc(s.to)}</div></div>
          <button class="btn primary" id="sharepic">Share</button></div>
        <div class="story-grid">
          <div class="story-tile wide"><div class="wdl">
              <div><b class="big good-text">${roll(r.win || 0)}</b><span>won</span></div>
              <div><b class="big faint">${roll(r.draw || 0)}</b><span>drawn</span></div>
              <div><b class="big bad-text">${roll(r.loss || 0)}</b><span>lost</span></div></div>
            <div class="stat-label">of ${s.games} games</div></div>
          <div class="story-tile"><div class="big">${roll(s.pieces, 1)}</div><div class="stat-label">pieces given away a game</div>
            ${s.pieces_before !== null ? (s.pieces < s.pieces_before ? `<span class="trend good">${svg("down")}from ${s.pieces_before}</span>`
              : s.pieces > s.pieces_before ? `<span class="trend bad">${svg("up")}from ${s.pieces_before}</span>` : `<span class="small muted">same as before</span>`) : ""}</div>
          ${s.improved ? `<div class="story-tile good"><div class="habit-icon">${svg((HABIT[s.improved.pattern] || ["hang"])[0])}</div>
            <div class="stat-label">Most improved</div><b>${esc((HABIT[s.improved.pattern] || [s.improved.pattern])[1] || s.improved.pattern)}</b>
            <div class="small muted">${s.improved.before} → ${s.improved.now} a game</div></div>` : ""}
          ${s.best ? `<a class="story-tile click" href="#/games/${s.best.id}"><div class="stat-label">${esc(s.best.label)}</div>
            <b>vs ${esc(s.best.opponent)} <span class="chip ${s.best.result}">${s.best.result === "win" ? "W" : s.best.result === "loss" ? "L" : "D"}</span></b>
            <div class="small muted">${s.best.moments ? `${s.best.moments} big mistake${s.best.moments > 1 ? "s" : ""}` : "No big mistakes"} · ${esc(s.best.date)}</div></a>` : ""}
        </div>
        ${s.next ? `<div class="story-next"><span class="label">Next week's one thing</span><div>${esc(s.next.habit)}</div></div>` : ""}
      </div>` : `<div class="empty">Your story appears after your first checked games.</div>`}
      <div class="box rise"><div class="row spread"><h2 style="margin:0">Badges</h2>
          <div class="ring-legend"><span><i class="t1"></i>Bronze</span><span><i class="t2"></i>Silver</span><span><i class="t3"></i>Gold, complete</span></div></div>
        <p class="small muted" style="margin:6px 0 0">${complete} complete · ${started} on the way · ${p.badges.length - complete - started} not started. A badge is complete at Gold.</p>
        ${BADGE_SOURCES.map(([title, groups]) => `<h3 class="badge-source">${title}</h3>
        ${groups.filter(gr => p.badges.some(b => b.group === gr)).map(gr => `<div class="badge-group">${esc(gr)}</div>
        <div class="badges">${p.badges.filter(b => b.group === gr).map(badgeCard).join("")}</div>`).join("")}`).join("")}</div>
    </div>`;
  countUp($("#page"));
  if (s) $("#sharepic").onclick = () => sharePanel(p.player, s);
}

// Share the week's picture. From a PC, WhatsApp and X can't take a picture through a link, so the app puts it on
// the clipboard and opens them with a line ready: Ctrl+V adds it. Instagram can't be posted to from a link at all:
// the picture is copied and saved, and Instagram opens to make a post (13 Oct test, point 5.5).
const SHARE_ICON = {  // simple glyphs, drawn here (no brand files)
  whatsapp: `<svg viewBox="0 0 24 24"><path d="M12 3a9 9 0 0 0-7.8 13.5L3 21l4.6-1.2A9 9 0 1 0 12 3z" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M9 8.5c0 3.5 3 6.5 6.5 6.5l1-1.5-2-1-1 1c-1-.5-2.5-2-3-3l1-1-1-2-1.5 1z" fill="currentColor"/></svg>`,
  x: `<svg viewBox="0 0 24 24"><path d="M4 4l16 16M20 4L4 20" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"/></svg>`,
  instagram: `<svg viewBox="0 0 24 24"><rect x="3.5" y="3.5" width="17" height="17" rx="5" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.8"/><circle cx="17.2" cy="6.8" r="1.2" fill="currentColor"/></svg>`,
  copy: `<svg viewBox="0 0 24 24"><rect x="8" y="8" width="12" height="12" rx="2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3" fill="none" stroke="currentColor" stroke-width="1.8"/></svg>`,
  save: `<svg viewBox="0 0 24 24"><path d="M12 4v11m0 0l-4.5-4.5M12 15l4.5-4.5M5 19h14" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>`,
};
function sharePanel(player, s) {
  const r = s.results || {}, line = `${s.title === "Your week" ? "My chess this week" : "My last 10 chess games"}: ${r.win || 0} won, ${r.draw || 0} drawn, ${r.loss || 0} lost. Coached by Knightwise, free.`;
  const url = "https://github.com/Abhra71/ChessCoach";
  const old = $(".share-pop"); if (old) old.remove();
  const pop = document.createElement("div"); pop.className = "share-pop box";
  const btn = (to, label) => `<button class="btn share-btn" data-to="${to}">${SHARE_ICON[to]}<span>${label}</span></button>`;
  pop.innerHTML = `<div class="row spread"><b>Share your week</b><button class="btn ghost" data-x>×</button></div>
    <p class="small muted" style="margin:6px 0 12px">The picture is copied first: press Ctrl+V where it opens.</p>
    <div class="share-grid">${btn("whatsapp", "WhatsApp")}${btn("x", "X (Twitter)")}${btn("instagram", "Instagram")}${btn("copy", "Copy picture")}${btn("save", "Save as picture")}</div>
    <p class="small" id="sharemsg" style="margin:10px 0 0"></p>`;
  document.body.appendChild(pop);
  $("[data-x]", pop).onclick = () => pop.remove();
  const msg = t => { $("#sharemsg", pop).textContent = t; };
  const png = () => storyPicture(player, s);
  const copy = () => api("/api/copy-picture", { png: png() });  // the app copies it: Windows' clipboard
  pop.querySelectorAll("[data-to]").forEach(b => b.onclick = async () => {
    const to = b.dataset.to;
    if (to === "save") {  // into Pictures\Knightwise, and Explorer shows it: you asked for the file
      try { await api("/api/save-picture", { png: png(), show: true }); msg("Saved in Pictures, Knightwise."); }
      catch (e) { msg("Couldn't save the picture."); }
      return;
    }
    try { await copy(); } catch (e) { msg("Couldn't copy the picture: use Save as picture instead."); return; }
    if (to === "copy") { msg("Copied. Paste it anywhere with Ctrl+V."); return; }
    if (to === "instagram") {  // no link can post to Instagram: a copy saved quietly, and Instagram opens
      api("/api/save-picture", { png: png(), show: false }).catch(() => {});
      window.open("https://www.instagram.com/", "_blank", "noopener");
      msg("Picture copied, and saved in Pictures, Knightwise. In Instagram, press + to make a post with it.");
      return;
    }
    const link = to === "whatsapp" ? `https://wa.me/?text=${encodeURIComponent(`${line} ${url}`)}`
      : `https://x.com/intent/post?text=${encodeURIComponent(line)}&url=${encodeURIComponent(url)}`;
    window.open(link, "_blank", "noopener");
    msg(`Picture copied. In ${to === "x" ? "X" : "WhatsApp"}, press Ctrl+V to add it.`);
  });
}

function storyPicture(player, s) {  // the week as a 1080 x 1350 picture, drawn on a canvas
  const W = 1080, H = 1350, c = document.createElement("canvas"); c.width = W; c.height = H;
  const g = c.getContext("2d"), r = s.results || {};
  const grad = g.createLinearGradient(0, 0, W, H); grad.addColorStop(0, "#0d2a1a"); grad.addColorStop(1, "#0a0a0a");
  g.fillStyle = grad; g.fillRect(0, 0, W, H);
  const text = (t, x, y, size, colour = "#fff", weight = 700) => { g.font = `${weight} ${size}px Segoe UI, sans-serif`; g.fillStyle = colour; g.fillText(t, x, y); };
  text("KNIGHTWISE", 80, 120, 30, "#36c27a", 800);
  text(`${player}: ${s.title.toLowerCase()}`, 80, 200, 54);
  text(`${s.from} to ${s.to}`, 80, 255, 30, "#9a9a9a", 400);
  const tile = (x, y, big, label, colour = "#fff") => {
    g.fillStyle = "rgba(255,255,255,.06)"; g.beginPath(); g.roundRect(x, y, 440, 260, 28); g.fill();
    text(String(big), x + 40, y + 140, 110, colour); text(label, x + 40, y + 210, 30, "#bdbdbd", 500);
  };
  tile(80, 320, s.games, "games played");
  tile(560, 320, `${r.win || 0}`, "won", "#36c27a");
  tile(80, 620, s.pieces, "pieces given away a game", s.pieces_before !== null && s.pieces < s.pieces_before ? "#36c27a" : "#fff");
  if (s.best) tile(560, 620, s.best.moments || 0, s.best.result === "win" ? "big mistakes, best game" : "big mistakes, closest game");
  if (s.improved) {
    const name = (HABIT[s.improved.pattern] || [0, s.improved.pattern])[1];
    text("Most improved", 80, 1000, 30, "#36c27a", 600);
    text(`${name}: ${s.improved.before} → ${s.improved.now} a game`, 80, 1050, 40);
  }
  if (s.next) { text("Next week's one thing", 80, 1150, 30, "#f0a43a", 600); wrap(g, s.next.habit, 80, 1200, 920, 36); }
  text("Coached by Viktor · Knightwise", 80, 1300, 26, "#777", 500);
  return c.toDataURL("image/png");
}
function wrap(g, t, x, y, width, size) {
  g.font = `600 ${size}px Segoe UI, sans-serif`; g.fillStyle = "#fff";
  let line = "";
  for (const w of t.split(" ")) {
    if (g.measureText(line + w).width > width) { g.fillText(line, x, y); line = ""; y += size * 1.3; }
    line += w + " ";
  }
  g.fillText(line, x, y);
}

async function home() {
  shell("home", `<p class="muted">Loading…</p>`);
  const h = await api("/api/home");
  if (!h.player) return go("welcome");
  // the very first Home is for the player's own games: the AI card waits for the next visit (13 Oct test: the AI
  // card, a sudden coach and a console window all at once "ruined the first look")
  try {
    if (sessionStorage.getItem("kw-new")) { sessionStorage.removeItem("kw-new"); localStorage.setItem("kw-ai-next", "1"); }
    else if (localStorage.getItem("kw-ai-next")) { localStorage.removeItem("kw-ai-next"); setTimeout(() => AiCard.maybe("welcome"), 4000); }
    else AiCard.maybe("week");
  } catch (e) {}
  const hour = new Date().getHours(), hello = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const f = h.focus, last = h.last_game, r = h.results || {}, pr = h.practice || {};
  const better = h.pieces_last20 < h.pieces_per_game;
  const played = (r.win || 0) + (r.loss || 0) + (r.draw || 0) || 1, pct = n => (100 * (n || 0) / played).toFixed(1);
  const rc = h.rating_change;
  const arrow = (good, text) => `<span class="trend ${good ? "good" : "bad"}">${svg(good ? "down" : "up")}${text}</span>`;
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>${hello}, ${esc(h.player)}</h1>
      <p class="sub">${h.games} games checked by Stockfish</p></div>
      <div class="row"><button class="btn" id="brief">Hear your briefing</button><a class="btn primary" href="#/practice">Start practice</a></div></div>
    <div class="grid">
      ${dailyCard(h.daily || {})}
      ${f ? `<div class="box focus hero rise">
        <div class="hero-main"><div class="label">Your focus</div>
          <h3 class="hero-title">${esc(PATTERN_TITLE[f.pattern] || cap(f.pattern))}</h3>
          <p class="hero-habit">${esc(f.habit)}</p>
          <div class="row"><a class="btn primary" href="#/practice/${encodeURIComponent(f.pattern)}">Practise this</a>
            <span class="pill red">${f.times} times · ${f.games} games</span></div></div>
        <div class="hero-side">${spark(h.trend)}
          <div class="hero-num"><span class="faint num">${h.pieces_per_game.toFixed(1)}</span><span class="faint">→</span>${roll(h.pieces_last20, 1)}</div>
          <div class="stat-label">pieces given away a game, lately</div>${arrow(better, better ? "better" : "worse")}</div></div>` : ""}
      <div class="habits rise">${h.patterns.map(p => {
        const [icon, name] = HABIT[p.pattern] || ["hang", cap(p.pattern)], fewer = p.recent <= p.per_game;
        return `<a class="habit box ${p.pattern === (f && f.pattern) ? "top" : ""}" href="#/practice/${encodeURIComponent(p.pattern)}" title="Practise this">
          <div class="habit-icon">${svg(icon)}</div><div class="big">${roll(p.times)}</div><div class="habit-name">${esc(name)}</div>
          ${arrow(fewer, fewer ? "fewer lately" : "more lately")}</a>`; }).join("")}</div>
      <div class="grid cols-3 rise">
        ${vsCard(h.you_vs_you)}
        <div class="box"><div class="big">${h.rating ? roll(h.rating) : "–"}</div><div class="stat-label">${cap(h.rating_class || "")} rating</div>
          ${rc ? `<span class="trend ${rc > 0 ? "good" : "bad"}">${svg(rc > 0 ? "up" : "down")}${rc > 0 ? "+" : ""}${rc} this month</span>` : ""}
          <div class="wld"><i class="w" style="width:${pct(r.win)}%"></i><i class="d" style="width:${pct(r.draw)}%"></i><i class="l" style="width:${pct(r.loss)}%"></i></div>
          <div class="wld-key small muted"><span><i class="w"></i>${r.win || 0} won</span><span><i class="d"></i>${r.draw || 0} drawn</span><span><i class="l"></i>${r.loss || 0} lost</span></div></div>
      </div>
      ${last ? `<div class="box row spread rise"><div><div class="label muted-label">Your last game</div>
          <h3 style="margin:6px 0 4px">vs ${esc(last.opponent)} <span class="faint num">${last.opponent_rating}</span>
            <span class="chip ${last.result}">${last.result === "win" ? "W" : last.result === "loss" ? "L" : "D"}</span></h3>
          <p class="sub">${last.moments ? `Maya found ${last.moments} key moment${last.moments > 1 ? "s" : ""} to look at.` : "A clean game: nothing big to fix."}</p></div>
        <a class="btn" href="#/games/${last.id}">Review game</a></div>` : ""}
      <div class="box rise"><h2>Ask the coach</h2><div id="askbox"></div></div>
    </div>`;
  countUp($("#page"));
  const briefing = [`${hello}, ${h.player}.`,
    f ? `Your focus is: ${PATTERN_TITLE[f.pattern] || f.pattern}. It happened ${f.times} times, in ${f.games} of your ${h.games} games.` : "",
    f ? f.meaning : "", f ? f.habit : "",
    `You give away ${h.pieces_per_game.toFixed(1)} pieces per game, and ${h.pieces_last20.toFixed(1)} in your last 20 games${better ? ", which is better" : ""}.`,
    last ? `Your last game was a ${last.result} against ${last.opponent}, with ${last.moments} key moments to look at.` : ""].join(" ");
  $("#brief").onclick = () => Voice.speak(briefing, true, COACHES.maya.voice);  // Home is Maya's
  api("/api/settings").then(cfg => askBox($("#askbox"), { placeholder: "How do I stop leaving pieces hanging?", coach: "maya",
    enabled: Object.values(cfg.slots).some(x => x.set), listen: cfg.listen_ready,
    onAsk: q => api("/api/ask", { question: q }) }));
}

// ---------- games ----------
async function games() {
  shell("games", `<p class="muted">Loading…</p>`);
  const list = await api("/api/games");
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>Games</h1><p class="sub">${list.length} finished games from chess.com. Click one to see its key moments.</p></div>
      <a class="btn" href="#/openings">Your opening tree</a></div>
    <div class="box" style="padding:8px 8px 0"><table><thead><tr><th>Date</th><th>Opponent</th><th>Result</th><th>Type</th>
      <th class="num">Pieces given away</th><th class="num">Key moments</th></tr></thead><tbody>
      ${list.map(g => `<tr class="click" data-id="${g.id}"><td class="muted num">${esc(g.date)}</td>
        <td>${esc(g.opponent)} <span class="faint num">${g.opponent_rating}</span></td>
        <td><span class="chip ${g.result}">${g.result === "win" ? "W" : g.result === "loss" ? "L" : "D"}</span></td>
        <td class="muted">${esc(cap(g.time_class))} · ${g.color}</td>
        <td class="num">${g.checked ? g.pieces_lost : "–"}</td><td class="num">${g.checked ? g.moments : "–"}</td></tr>`).join("")}
    </tbody></table></div>`;
  document.querySelectorAll("tr.click").forEach(tr => tr.onclick = () => go(`games/${tr.dataset.id}`));
}

// Game review, one key moment at a time (debrief points 17, 18 and 42): You played, Better, They replied, Their
// better, one step at a time with Maya saying each one. All the moments are one click away, and so is every move.
async function gameView(id) {
  shell("games", `<p class="muted">Loading…</p>`);
  const [g, cfg] = await Promise.all([api(`/api/games/${id}`), api("/api/settings")]);
  const aiReady = Object.values(cfg.slots).some(x => x.set);
  const explained = {}, moments = g.key_moments, keyPly = new Set(moments.map(m => m.ply));
  const flip = g.color === "black";
  let mi = 0, si = 0, shown = 0, free = !moments.length, ply = moments.length ? moments[0].ply - 1 : g.positions.length - 1;
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/games" class="small muted" style="text-decoration:none">← Games</a>
      <h1 style="margin-top:6px">vs ${esc(g.opponent)} <span class="faint num">${g.opponent_rating}</span></h1>
      <p class="sub">${cap(g.result)} · ${esc(g.date)} · ${esc(g.time_class)} · you were ${g.color}${g.opening ? " · " + esc(g.opening) : ""}</p></div>
      <a class="btn" href="${esc(g.url)}" target="_blank" rel="noopener">Open on chess.com ↗</a></div>
    <div class="game-layout">
      <div><div class="board-wrap" id="board"></div>
        <div class="controls"><button class="btn" data-go="0">⏮</button><button class="btn" data-go="-1">◀</button>
          <button class="btn" data-go="1">▶</button><button class="btn" data-go="end">⏭</button></div>
        <div style="margin-top:12px">${Board.legend(["mine", "better", "real", "reply"])}</div></div>
      <div class="stack">
        <div class="box stack walk" id="walk"></div>
        <div class="box stack" style="padding:14px"><h2 style="margin:0">Ask the coach about this position</h2><div id="askbox"></div></div>
        <details class="box" style="padding:12px"><summary><b>All moves</b> <span class="small muted">click one to see the board there</span></summary>
          <div class="movelist" id="moves" style="margin-top:10px"></div></details>
      </div>
    </div>`;
  const stepPly = (k, st) => st.board === "before" ? k.ply - 1 : k.ply;
  function board() {
    const k = moments[mi], st = !free && k ? k.steps[si] : null, pos = g.positions[ply], hl = {};
    if (!st && pos.uci) { hl[pos.uci.slice(0, 2)] = "hl-last"; hl[pos.uci.slice(2, 4)] = "hl-last"; }
    const arrows = st ? st.arrows.map(([u, kind]) => ({ from: u.slice(0, 2), to: u.slice(2, 4), kind })) : [];
    Board.render($("#board"), { fen: pos.fen, flip, highlights: hl, arrows });
    let html = "";
    for (let i = 1; i < g.positions.length; i += 2) {
      html += `<span class="n">${(i + 1) / 2}.</span>`;
      for (const j of [i, i + 1]) html += g.positions[j]
        ? `<span data-p="${j}" class="${j === ply ? "cur" : ""} ${keyPly.has(j) ? "key" : ""}">${esc(g.positions[j].san)}</span>` : "<span></span>";
    }
    $("#moves").innerHTML = html;
    $("#moves").querySelectorAll("span[data-p]").forEach(el => el.onclick = () => { ply = Number(el.dataset.p); free = true; draw(); });
  }
  function draw() {
    board();
    const w = $("#walk");
    if (!moments.length) {
      w.innerHTML = `<h2 style="margin:0">No big mistakes in this game</h2><p class="muted">Every move kept your position. Step through it with the arrows under the board.</p>`;
      return;
    }
    const k = moments[mi];
    w.innerHTML = `
      <div class="row spread"><h2 style="margin:0">Key moment ${mi + 1} of ${moments.length}</h2>
        <div class="dots">${moments.map((m, i) => `<button class="dot ${i === mi ? "on" : ""}" data-m="${i}" title="Move ${m.move_number}" aria-label="Key moment ${i + 1}, move ${m.move_number}"></button>`).join("")}</div></div>
      <div class="row spread"><span class="what">Move ${k.move_number} · ${esc(cap(k.pattern))}</span>
        <span class="small faint" title="How much of your chance to win this move cost">−${Math.round(k.loss)}% win chance</span></div>
      <ol class="steps">${k.steps.slice(0, shown + 1).map((st, i) => `<li class="step ${!free && i === si ? "on" : ""}" data-s="${i}">
        <span class="tag"><i style="background:${Board.KIND[st.kind].color}"></i>${esc(st.title)}${st.san ? ` <b>${esc(st.san)}</b>` : ""}</span>
        <div class="small">${esc(st.text)}</div></li>`).join("")}</ol>
      ${shown < k.steps.length - 1 ? `<div class="row"><button class="btn primary" id="nextstep">Next: ${esc(k.steps[shown + 1].title)} ▶</button>
          <button class="btn" id="allsteps">Show all steps</button></div>`
        : `${k.habit ? `<div class="small"><b>Habit:</b> ${esc(k.habit)}</div>` : ""}
          ${explained[k.ply] ? `<div class="coach-says">${esc(explained[k.ply])}</div>` : ""}
          <div class="row"><a class="btn primary" href="#/try/${g.id}/${k.ply}">Try it again</a>
            ${mi < moments.length - 1 ? `<button class="btn" id="nextmoment">Next moment ▶</button>` : ""}
            ${aiReady && !explained[k.ply] ? `<button class="btn" data-explain="${k.ply}">Explain like a coach</button>` : ""}</div>`}`;
    w.querySelectorAll("[data-m]").forEach(b => b.onclick = () => open(Number(b.dataset.m)));
    w.querySelectorAll("[data-s]").forEach(li => li.onclick = () => pick(Number(li.dataset.s)));
    const ns = $("#nextstep"); if (ns) ns.onclick = () => { shown++; pick(shown); };
    const all = $("#allsteps"); if (all) all.onclick = () => { shown = k.steps.length - 1; pick(shown, false); };
    const nm = $("#nextmoment"); if (nm) nm.onclick = () => open(mi + 1);
    w.querySelectorAll("[data-explain]").forEach(b => b.onclick = async () => {
      b.disabled = true; b.textContent = "Thinking…";
      try {
        const r = await api("/api/explain", { game: g.id, ply: Number(b.dataset.explain) });
        explained[Number(b.dataset.explain)] = r.text; draw(); Coach.react("maya", "explain", r.text);
      } catch (err) { b.textContent = err.message.slice(0, 80); }
    });
  }
  // show one step: its board, its arrows, and Maya says it (worried when it went wrong for you)
  function pick(i, speak = true) {
    const k = moments[mi], st = k.steps[i];
    si = i; free = false; ply = stepPly(k, st);
    draw();
    const bad = st.kind === "mine" || (st.kind === "real" && !k.reply_missed && k.real_reply_san);
    if (speak) Coach.react("maya", bad ? "worried" : "explain", st.text);
  }
  function open(i) { mi = i; shown = 0; pick(0); }
  askBox($("#askbox"), { placeholder: "Why is my bishop in danger here?", coach: "maya", enabled: aiReady, listen: cfg.listen_ready,
    onAsk: q => { const k = moments[mi]; return api("/api/ask", { question: q, fen: g.positions[ply].fen, game: g.id, ply: !free && k ? k.ply : null }); } });
  document.querySelectorAll("[data-go]").forEach(b => b.onclick = () => {
    const v = b.dataset.go, was = ply;
    ply = v === "0" ? 0 : v === "end" ? g.positions.length - 1 : Math.max(0, Math.min(g.positions.length - 1, ply + Number(v)));
    free = true;
    if (ply === was + 1) Sound.move(g.positions[ply].san);
    draw();
  });
  draw();
  // Maya welcomes you at once (13 Oct test: she only came after a moment was clicked): how many, which cost most
  const worst = moments.reduce((a, b) => (b.loss > (a ? a.loss : -1) ? b : a), null);
  if (worst) Coach.react("maya", "explain",
    `${moments.length} key moment${moments.length === 1 ? "" : "s"} in this game, and we'll take them one at a time. ` +
    (moments.length < 2 ? `It's move ${worst.move_number}. ` : worst === moments[0] ? `The first one, move ${worst.move_number}, cost you the most. `
      : `First move ${moments[0].move_number}; move ${worst.move_number} cost you the most. `) + "Press Next when you're ready.",
    [{ label: `Start with move ${moments[0].move_number}`, run: () => pick(0) }]);
  else Coach.react("maya", "celebrate", "No big mistakes in this game. That's how it's done.");
}

// ---------- practice ----------
async function practice(pattern) {
  shell("practice", `<p class="muted">Loading…</p>`);
  const all = await api("/api/practice-set").catch(() => []);
  const only = pattern ? all.filter(d => d.pattern === pattern) : [], drills = only.length ? only : all;
  if (!drills.length) { $("#page").innerHTML = `<div class="empty">Practice appears once your games are checked.</div>`; return; }
  $("#page").innerHTML = trainerPage(only.length ? (HABIT[pattern] || [])[1] || "Practice" : "Practice",
    { text: "" });
  trainer(drills, { coach: "maya", record: true });
}

// Settings: the chess.com self-check (coach/health.py). All working, or what chess.com changed and what still works.
function healthRow(h) {
  if (!h || (!h.verified && !h.broken.length)) return `<span class="faint">Not run yet: it runs when you open chess.com.</span>`;
  const when = t => new Date(t * 1000).toLocaleString([], { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  if (!h.broken.length) return `<span class="ok-text">All working · last verified ${when(h.verified)}</span>`;
  return h.broken.map(b => `<div class="delta bad" style="font-size:13.5px">${esc(b.says)}</div>
    <div class="small faint">Since ${when(b.since)}${b.detail ? ` · ${esc(b.detail)}` : ""}</div>`).join("")
    + `<div class="small muted" style="margin-top:6px">Everything else keeps working. An update will fix it.</div>`;
}

// Settings: where the extension really is. "Set up" only while it isn't connected anywhere.
function connectedIn(st) {
  const names = { chrome: "Chrome", edge: "Edge", brave: "Brave", opera: "Opera" };
  const where = Object.keys(st.extension_in || {}).map(b => names[b] || "your browser");
  return where.length ? `<span class="ok-text">Connected in ${where.join(" and ")}</span>`
    : `<span class="faint">Not connected yet</span><a class="btn" href="#/extension">Set up</a>`;
}

// ---------- arrows on chess.com: the extension, step by step ----------
async function extensionView() {
  shell("settings", `<p class="muted">Loading…</p>`);
  const st = await api("/api/status");
  const browsers = st.browsers.length ? st.browsers : ["chrome"];
  let browser = browsers.includes("chrome") ? "chrome" : browsers[0];
  const NAME = { chrome: "Chrome", edge: "Edge" };
  const here = () => (st.extension_in || {})[browser];  // connected in the browser shown, not just anywhere
  const copyBtn = (id, text) => `<button class="btn" data-copy="${esc(text)}" id="${id}">Copy</button>`;
  // Chrome: real screenshots (personal details removed, the click spot circled in red); Edge: simple drawings
  const REAL = { open: "1-address", dev: "2-developer-mode", load: "3-load-unpacked", pick: "4-choose-folder", done: "5-done" };
  const pic = (step, alt) => browser === "chrome" ? `<img class="shot real" src="/ui/guide/${REAL[step]}.png" alt="${alt}">` : Guide.steps[step];
  function render() {
    const page = `${browser}://extensions`;
    $("#page").innerHTML = `
      <div class="page-head"><div><a href="#/settings" class="small muted" style="text-decoration:none">← Settings</a>
        <h1 style="margin-top:6px">Arrows on chess.com</h1>
        <p class="sub">A small browser extension shows the key moments of your finished games right on chess.com's board. One minute, once.</p></div>
        ${browsers.length > 1 ? `<div class="seg" id="browser">${browsers.map(b => `<button data-b="${b}" class="${b === browser ? "on" : ""}">${NAME[b] || b}</button>`).join("")}</div>` : ""}</div>
      <div class="box ext-status ${here() ? "ok" : ""}" id="extstatus">${here() ? `Connected in ${NAME[browser] || browser}. The extension is working.` : "Waiting for the extension… this turns green by itself."}</div>
      <p class="note" style="margin:10px 0 18px">Fair play: it only shows something on games that are already finished. During a live game it shows nothing, and it never moves pieces.</p>
      <div class="guide">
        <div class="gstep"><div class="gnum">1</div><div class="gtext"><h3>Open ${NAME[browser]}'s extensions page</h3>
          <p class="muted">Click the button, or copy the address and paste it into ${NAME[browser]}'s address bar.</p>
          <div class="row"><button class="btn primary" id="openext">Open it for me</button><code class="addr">${page}</code>${copyBtn("c1", page)}</div>
          <p class="small muted" id="openmsg"></p></div>${pic("open", "Chrome's address bar showing chrome://extensions")}</div>
        <div class="gstep"><div class="gnum">2</div><div class="gtext"><h3>Switch on "Developer mode"</h3>
          <p class="muted">The switch at the top right of that page. Leave it on: the extension only works while it is on.</p></div>${pic("dev", "The Developer mode switch, top right")}</div>
        <div class="gstep"><div class="gnum">3</div><div class="gtext"><h3>Click "Load unpacked"</h3>
          <p class="muted">It appears at the top left once Developer mode is on.</p></div>${pic("load", "The Load unpacked button, top left")}</div>
        <div class="gstep"><div class="gnum">4</div><div class="gtext"><h3>Choose the Knightwise folder</h3>
          <p class="muted">In the window that opens, click its address bar, paste this path with Ctrl+V, press Enter, then click <b>Select Folder</b>.</p>
          <div class="row"><code class="addr long">${esc(st.extension_path)}</code>${copyBtn("c2", st.extension_path)}</div>
          <p class="small muted" style="margin-top:8px">Easier: <button class="btn" id="showfolder" style="padding:4px 10px">Show the folder</button> and drag the <b>extension</b> folder onto the extensions page.</p></div>${pic("pick", "The folder window: path typed in its address bar, then Select Folder")}</div>
        <div class="gstep"><div class="gnum">5</div><div class="gtext"><h3>Done</h3>
          <p class="muted">"Knightwise" appears in the list, and the box at the top turns green. Then open any finished game of yours on chess.com.</p>
          <p class="small muted">${NAME[browser]} may later say the extension "may be unsafe" or "can't be verified": that is expected for any extension not from its web store. Keep it.</p>
          <a class="btn" href="https://www.chess.com/games/archive/${encodeURIComponent(st.player || "")}" target="_blank" rel="noopener">Your games on chess.com ↗</a></div>${pic("done", "Knightwise in the list of extensions")}</div>
      </div>`;
    document.querySelectorAll(".shot.real").forEach(i => i.onclick = () => i.closest(".gstep").classList.toggle("zoom"));
    document.querySelectorAll("[data-copy]").forEach(b => b.onclick = () => navigator.clipboard.writeText(b.dataset.copy).then(() => { b.textContent = "Copied"; }));
    if ($("#browser")) $("#browser").querySelectorAll("button").forEach(b => b.onclick = () => { browser = b.dataset.b; render(); });
    $("#openext").onclick = async () => {
      const r = await api("/api/open-extensions", { browser }).catch(() => ({}));
      $("#openmsg").textContent = r.opened ? `Opened in ${NAME[browser]}. It may be behind this window.` : `Couldn't open it: copy the address and paste it into ${NAME[browser]}.`;
    };
    $("#showfolder").onclick = () => api("/api/show-extension-folder", {}).catch(() => {});
  }
  render();
  (async function watch() {
    while (location.hash.startsWith("#/extension")) {
      const s2 = await api("/api/status").catch(() => ({}));
      st.extension_in = s2.extension_in || {};
      if (here()) { const box = $("#extstatus"); if (box) { box.classList.add("ok"); box.textContent = `Connected in ${NAME[browser] || browser}. The extension is working.`; } return; }
      await wait(1500);
    }
  })();
}

// ---------- settings ----------
async function settingsView() {
  shell("settings", `<p class="muted">Loading…</p>`);
  const [s, st] = await Promise.all([api("/api/settings"), api("/api/status")]);
  const aiSet = Object.values(s.slots).some(x => x.set);  // the real key state, never a stale flag
  const slot = (id, n) => {
    const x = s.slots[id], prov = s.providers[x.provider];
    return `<div class="box stack" data-slot="${id}"><div class="row spread"><h3>AI key ${n}</h3>
        <span class="small ${x.set ? "ok-text" : "faint"}">${x.set ? `Saved · ends with ••••${esc(x.ends)}` : "Not set"}</span></div>
      <select class="field" data-provider>${Object.entries(s.providers).map(([k, p]) =>
        `<option value="${k}" ${k === x.provider ? "selected" : ""}>${esc(p.name)}${p.free ? ", free" : ", paid"}</option>`).join("")}</select>
      <input class="field" type="password" autocomplete="off" spellcheck="false" placeholder="${x.set ? "Paste a new key to replace it" : "Paste your API key"}" data-key>
      <div class="row"><button class="btn primary" data-save>Save key</button>${x.set ? `<button class="btn" data-test>Test key</button><button class="btn danger" data-remove>Remove</button>` : ""}
        <a class="small muted" data-get href="${esc(prov.get_key)}" target="_blank" rel="noopener">Get a ${esc(prov.name)} key ↗</a></div>
      <div class="err" data-msg></div></div>`;
  };
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>Settings</h1><p class="sub">Everything here stays on this computer.</p></div></div>
    <div class="box">
      <div class="settings-row"><div><h3>chess.com account</h3><p class="note">Only public games are read. No password.</p></div>
        <div class="stack"><div class="row"><input class="field" id="user" value="${esc(st.player || "")}" spellcheck="false" style="max-width:280px">
          <button class="btn" id="saveuser">Change</button></div><div class="err" id="usermsg"></div></div></div>
      <div class="settings-row"><div><h3>Appearance</h3></div>
        <div><div class="seg" id="theme">${["system", "dark", "light"].map(t => `<button data-t="${t}" class="${s.theme === t ? "on" : ""}">${cap(t)}</button>`).join("")}</div></div></div>
      <div class="settings-row"><div><h3>Voice</h3><p class="note">Your coaches speak. It runs on this computer, no internet needed.</p></div>
        <div class="stack"><div class="row"><button class="switch ${s.voice ? "on" : ""}" id="voice" aria-label="Voice"></button>
          <span class="small muted">${s.voice_ready ? (s.voice ? "On" : "Off") : "Voice files not installed"}</span></div>
          <div class="voices">${Object.entries(COACHES).map(([id, c]) => `<button class="btn voice-chip" data-hear="${id}">
            ${KnightwiseFaces.svg(id, "pleased")}<span><b>${esc(c.name)}</b><small>${esc(c.role)}</small></span><i>▶</i></button>`).join("")}</div>
          <div class="row"><span class="small ${s.listen_ready && aiSet ? "ok-text" : "muted"}" id="listenstate">${!s.listen_ready ? "Ask by voice: a one-time 485 MB download."
            : aiSet ? "Listening is on: use Talk to ask by voice." : "Listening is installed. Asking needs an AI key: add one above."}</span>
            ${s.listen_ready ? "" : `<button class="btn" id="getlisten">Install listening</button>`}</div></div></div>
      <div class="settings-row"><div><h3>Sounds</h3><p class="note">Moves, right and wrong answers, a finished set. No background music.</p></div>
        <div class="row"><button class="switch ${s.sounds ? "on" : ""}" id="sounds" aria-label="Sounds"></button>
          <span class="small muted">${s.sounds ? "On" : "Off"}</span></div></div>
      <div class="settings-row"><div><h3>AI: talk with your coaches</h3><p class="note">Optional. With a key, the coach explains moves in its own words and answers your questions.
        Without one it uses the engine's built-in sentences. Keys are kept in Windows Credential Manager, encrypted for your Windows account,
        and are only sent to the provider you choose.</p>
        <button class="btn" id="aicompare" style="margin-top:8px">What AI adds</button></div>
        <div class="grid">${slot("slot1", 1)}${slot("slot2", 2)}<p class="note">Key 2 is used when key 1 fails or runs out.</p></div></div>
      <div class="settings-row"><div><h3>Arrows on chess.com</h3><p class="note">The browser extension.</p></div>
        <div class="row">${connectedIn(st)}</div></div>
      <div class="settings-row"><div><h3>chess.com check</h3><p class="note">chess.com changes its site now and then. Knightwise checks everything it uses there, each time.</p></div>
        <div>${healthRow(st.health)}</div></div>
      <div class="settings-row"><div><h3>Your data</h3><p class="note">Games, checks, practice and your logbook.</p></div>
        <div class="row"><button class="btn" id="folder">Open data folder</button></div></div>
      <div class="settings-row"><div><h3>About</h3></div>
        <div class="muted small">Knightwise · beta · open source, GPL-3.0 · <a href="https://github.com/Abhra71/ChessCoach" target="_blank" rel="noopener">GitHub ↗</a><br>
          Engine: Stockfish 19 · Puzzles: Lichess · Fair play: never active in games against real people.</div></div>
    </div>`;
  $("#theme").querySelectorAll("button").forEach(b => b.onclick = async () => {
    const r = await api("/api/settings", { theme: b.dataset.t }); applyTheme(r.theme); settingsView();
  });
  $("#sounds").onclick = async () => { await api("/api/settings", { sounds: !s.sounds }); Sound.set(!s.sounds); if (!s.sounds) Sound.play("right"); settingsView(); };
  $("#voice").onclick = async () => { await api("/api/settings", { voice: !s.voice }); Voice.set(!s.voice); settingsView(); };
  const HELLO = { maya: "Hi, I'm Maya. I'll walk you through your games, one moment at a time.",
    viktor: "Viktor. I keep an eye on your progress. Slowly, but surely." };
  document.querySelectorAll("[data-hear]").forEach(b => b.onclick = () => Voice.speak(HELLO[b.dataset.hear], true, COACHES[b.dataset.hear].voice));
  $("#aicompare").onclick = () => AiCard.open();
  if ($("#getlisten")) $("#getlisten").onclick = async () => {
    $("#getlisten").disabled = true;
    await api("/api/voice/install-listening", {});
    for (;;) {
      const st = await api("/api/status").catch(() => ({}));
      const x = st.listen_install;
      if (!x) { settingsView(); return; }
      if (x.error) { $("#listenstate").textContent = "Download failed: " + x.error; $("#getlisten").disabled = false; return; }
      $("#listenstate").textContent = x.total ? `Downloading… ${Math.round(100 * x.done / x.total)}%` : "Starting download…";
      await wait(1000);
    }
  };
  $("#folder").onclick = () => api("/api/open-folder", {}).catch(() => {});
  $("#saveuser").onclick = async () => {
    const name = $("#user").value.trim();
    if (!name || name === st.player) return;
    if (!confirm(`Switch to ${name}? The coach will check that player's games from the start.`)) return;
    $("#usermsg").textContent = "Checking on chess.com…";
    try { await api("/api/player", { username: name }); go("home"); } catch (e) { $("#usermsg").textContent = e.message; }
  };
  document.querySelectorAll("[data-slot]").forEach(box => {
    const id = box.dataset.slot, msg = $("[data-msg]", box);
    $("[data-provider]", box).onchange = e => { $("[data-get]", box).href = s.providers[e.target.value].get_key;
      $("[data-get]", box).textContent = `Get a ${s.providers[e.target.value].name} key ↗`; };
    $("[data-save]", box).onclick = async () => {
      msg.textContent = "";
      try { await api("/api/keys", { slot: id, provider: $("[data-provider]", box).value, key: $("[data-key]", box).value }); settingsView(); }
      catch (e) { msg.textContent = e.message; }
    };
    const test = $("[data-test]", box);
    if (test) test.onclick = async () => {
      msg.className = "err"; msg.textContent = "Testing…";
      const r = await api("/api/keys/test", { slot: id }).catch(e => ({ ok: false, message: e.message }));
      msg.className = r.ok ? "ok-text" : "err"; msg.textContent = r.message;
    };
    const rm = $("[data-remove]", box);
    if (rm) rm.onclick = async () => { if (confirm("Remove this key?")) { await api("/api/keys/remove", { slot: id }); settingsView(); } };
  });
}

// ---------- welcome ----------
const LINES = ["Every move you played, checked.", "Your habits, found.", "Silent when you play a real person.",
  "Trained on your own positions.", "A coach that never sleeps."];
const remember = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } };

// The welcome film's music: Satie's Gymnopedie No. 1 (public domain), quiet; the mute is remembered.
// The recording opens very softly (its first ~9 s are about a third as loud as the rest), so it starts a little louder
// and settles back to quiet once the melody fills out. The app window lets it start by itself (app.py); in a plain
// browser the first click or key starts it.
function welcomeMusic(button) {
  // 13 Oct test: "late, with a lull and long silences". The piece opens with quiet chords before the melody, the
  // volume used to drop 9 s in, and the file ends with 3 s of silence before looping. So: start 3 s in, one steady
  // volume, and loop before the silent end.
  const audio = new Audio("/ui/vendor/music/gymnopedie-1.flac"), VOLUME = 0.26, FROM = 3, TAIL = 168.5;
  audio.preload = "auto"; audio.volume = 0;
  let muted = remember("kw-music-muted") === "1", fader = null;
  const fade = (to, secs) => {
    clearInterval(fader);
    const step = (to - audio.volume) / Math.max(1, secs * 20);
    fader = setInterval(() => {
      const v = audio.volume + step;
      if ((step >= 0 && v >= to) || (step < 0 && v <= to)) { audio.volume = to; clearInterval(fader); if (!to) audio.pause(); }
      else audio.volume = Math.min(1, Math.max(0, v));
    }, 50);
  };
  audio.addEventListener("loadedmetadata", () => { if (audio.currentTime < FROM) audio.currentTime = FROM; }, { once: true });
  audio.addEventListener("timeupdate", () => { if (audio.currentTime >= TAIL) audio.currentTime = FROM; });  // no silent tail
  const start = () => {
    if (muted || !audio.paused) return;
    if (audio.readyState >= 1 && audio.currentTime < FROM) audio.currentTime = FROM;
    audio.play().then(() => fade(VOLUME, 0.5)).catch(() => {});
  };
  const paint = () => { button.innerHTML = muted ? "Music off" : "Music on"; button.setAttribute("aria-pressed", String(!muted)); };
  button.onclick = () => { muted = !muted; remember("kw-music-muted", muted ? "1" : "0"); paint(); if (muted) fade(0, 0.6); else start(); };
  paint(); start();
  const kick = () => { if (audio.paused) start(); };
  const EVENTS = ["pointerdown", "keydown"];
  EVENTS.forEach(e => addEventListener(e, kick));
  return () => { EVENTS.forEach(e => removeEventListener(e, kick)); fade(0, 0.8); };
}

// Short lines typed over the film, letter by letter, held, then erased.
function typeLines(el) {
  let alive = true, i = 0;
  (async () => {
    while (alive) {
      const line = LINES[i++ % LINES.length];
      for (let n = 1; n <= line.length && alive; n++) { el.textContent = line.slice(0, n); await wait(45 + Math.random() * 40); }
      await wait(2600);
      for (let n = line.length; n >= 0 && alive; n--) { el.textContent = line.slice(0, n); await wait(18); }
      await wait(500);
    }
  })();
  return () => { alive = false; };
}

async function welcome() {
  $("#root").innerHTML = `<div class="onboard"><div class="scene"><div class="backdrop" id="backdrop"></div>
      <div class="typed"><span id="typed"></span><i class="caret"></i></div></div>
    <aside class="panel"><div class="brand"><span class="mark">${svg("pawn")}</span>Knightwise
      <button class="music" id="music" title="Music"></button></div><div class="card" id="card"></div>
      <p class="credit">Music: Satie, Gymnopédie No. 1, played by Michael Laucke, public domain</p></aside></div>`;
  const stops = [typeLines($("#typed")), welcomeMusic($("#music"))];
  const mountBackdrop = () => { try { stops.push(window.Backdrop.mount($("#backdrop"))); } catch (e) { console.warn("3D scene", e); } };
  if (window.Backdrop) mountBackdrop(); else window.addEventListener("backdrop-ready", mountBackdrop, { once: true });
  addEventListener("hashchange", () => stops.forEach(f => f && f()), { once: true });
  const card = $("#card");
  const dots = n => `<div class="steps-dots">${[0, 1, 2].map(i => `<i class="${i <= n ? "on" : ""}"></i>`).join("")}</div>`;
  function intro() {
    card.innerHTML = `${dots(0)}<h1>Your personal chess coach.</h1>
      <p class="lead">Knightwise studies your finished chess.com games with Stockfish, finds the one or two habits that cost you the most, and trains you out of them.</p>
      <div class="does"><div><b>It does</b><ul><li>Check every move of your finished games</li>
        <li>Show the key moments, with arrows</li><li>Train you on your own positions</li><li>Run quietly and check each new game</li></ul></div>
        <div class="no"><b>It never</b><ul><li>Helps during a game against a real person</li><li>Moves pieces for you</li>
        <li>Needs your password</li><li>Sells or shares your data</li></ul></div></div>
      <button class="btn primary" id="next1">Get started</button>`;
    $("#next1").onclick = name;
  }
  function name() {
    card.innerHTML = `${dots(1)}<h1>Who are you on chess.com?</h1>
      <p class="muted" style="margin:8px 0 18px">Your username. Only your public games are read.</p>
      <div class="row"><input class="field" id="name" placeholder="chess.com username" spellcheck="false" autocomplete="off">
        <button class="btn primary" id="go">Continue</button></div><div class="err" id="err" style="margin-top:8px"></div>`;
    $("#name").focus();
    const start = async () => {
      const v = $("#name").value.trim(); if (!v) return;
      $("#go").disabled = true; $("#err").textContent = "Checking on chess.com…";
      try { await api("/api/player", { username: v }); work(); }
      catch (e) { $("#err").textContent = e.message || "The coach isn't answering."; $("#go").disabled = false; }
    };
    $("#go").onclick = start; $("#name").onkeydown = e => { if (e.key === "Enter") start(); };
  }
  async function work() {
    card.innerHTML = `${dots(2)}<h1>Studying your games</h1><p class="muted" id="phase" style="margin:8px 0 16px">Starting…</p>
      <div class="bar"><div id="fill" style="width:3%;transition:width .4s"></div></div><p class="small muted num" id="cnt" style="margin-top:8px"></p>
      <p class="small muted" style="margin-top:16px">The first time takes a couple of minutes. You can close this window: a notification tells you when it's ready.</p>`;
    for (;;) {
      const s = await api("/api/status").catch(() => ({}));
      if (s.phase === "ready" && s.review_ready) { try { sessionStorage.setItem("kw-new", "1"); } catch (e) {} return go("home"); }
      $("#phase").textContent = s.phase === "error" ? "Something went wrong. Retrying by itself." : cap(s.phase || "working") + "…";
      $("#fill").style.width = (s.total ? Math.max(3, 100 * s.done / s.total) : s.phase === "building your pages" ? 100 : 3) + "%";
      $("#cnt").textContent = s.total ? `Game ${s.done} of ${s.total}` : "";
      await wait(1000);
    }
  }
  const s = await api("/api/status").catch(() => ({}));
  if (s.player && !s.review_ready) work(); else intro();
}

// ---------- router ----------
function go(route) { location.hash = "#/" + route; }
async function route() {
  const [name, arg] = location.hash.replace(/^#\/?/, "").split("/");
  try {
    if (name === "welcome") { Coach.hide(); return await welcome(); }
    if (["settings", "extension"].includes(name)) Coach.hide();
    else if (!(name === "games" && arg)) {  // one game: Maya welcomes you there herself
      let first = false; try { first = !!sessionStorage.getItem("kw-new"); } catch (e) {}
      if (first) setTimeout(() => Coach.arrive("home"), 2500);  // the first Home: the coach comes once the cards have settled
      else Coach.arrive(name || "home");
    }
    if (name === "plan") return await planView(arg);
    if (name === "games" && arg) return await gameView(arg);
    if (name === "games") return await games();
    if (name === "practice") return await practice(arg && decodeURIComponent(arg));
    if (name === "daily") return await daily();
    if (name === "progress") return await progressView();
    if (name === "openings") return await openingTree();
    if (name === "try") return await tryAgain(arg, location.hash.split("/")[3]);
    if (name === "extension") return await extensionView();
    if (name === "settings") return await settingsView();
    return await home();
  } catch (e) {
    console.error(e);
    if ($("#page")) $("#page").innerHTML = `<div class="empty">Couldn't load this screen: ${esc(e.message)}</div>`;
  }
}
window.addEventListener("hashchange", () => { Voice.stop(); route(); });
api("/api/settings").then(s => { applyTheme(s.theme); Voice.set(s.voice && s.voice_ready); Sound.set(s.sounds !== false); }).catch(() => {});
api("/api/status").then(s => { STATUS = s; if (!s.player && !location.hash.includes("welcome")) go("welcome"); else route(); })
  .catch(() => route());
pollStatus();
