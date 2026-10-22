// Knightwise desktop app: one page, a few screens (#/home, #/games, #/practice, #/settings, #/welcome).
const $ = (sel, el = document) => el.querySelector(sel);
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const api = (path, body) => fetch(path, body === undefined ? {} : {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
}).then(async r => { const j = await r.json().catch(() => ({})); if (!r.ok) throw Object.assign(new Error(j.message || r.status), j); return j; });
const wait = ms => new Promise(r => setTimeout(r, ms));
let TALK = false;  // a key that can hear is set: the coaches show Talk (0.6)
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
  book: '<path d="M4 5.5C4 4.7 4.7 4 5.5 4H11v16H5.5c-.8 0-1.5-.7-1.5-1.5z"/><path d="M20 5.5c0-.8-.7-1.5-1.5-1.5H13v16h5.5c.8 0 1.5-.7 1.5-1.5z"/>',
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
const Mic = (() => {  // records 16 kHz mono in the window; the coach's key turns it into text (Groq, then Gemini)
  let ctx = null, stream = null, node = null, chunks = [], level = 0, sound = false;
  // 19 Oct: Bluetooth headphones switched off mid-test and the microphone sent only zeros: say so, not "I'll be here"
  const DEAD = "Your microphone sends no sound. Check which one Windows is using (Settings, System, Sound), then try again.";
  async function start() {
    stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
    ctx = new AudioContext({ sampleRate: 16000 });
    const src = ctx.createMediaStreamSource(stream);
    node = ctx.createScriptProcessor(4096, 1, 1);
    chunks = []; level = 0; sound = false;
    node.onaudioprocess = e => {
      const d = new Float32Array(e.inputBuffer.getChannelData(0));
      chunks.push(d);
      let sum = 0; for (const v of d) { sum += v * v; if (v) sound = true; }
      level = Math.sqrt(sum / d.length);  // how loud, for knowing when the player has finished
    };
    src.connect(node); node.connect(ctx.destination);
  }
  async function close() {
    if (!ctx) return;
    node.disconnect(); stream.getTracks().forEach(t => t.stop()); await ctx.close(); ctx = null;
  }
  async function stop() {
    if (!ctx) return "";
    await close();
    const n = chunks.reduce((a, c) => a + c.length, 0), pcm = new Int16Array(n);
    let i = 0;
    for (const c of chunks) for (const v of c) pcm[i++] = Math.max(-1, Math.min(1, v)) * 32767;
    const r = await fetch("/api/listen", { method: "POST", headers: { "Content-Type": "application/octet-stream" }, body: pcm.buffer });
    const j = await r.json();
    if (!r.ok) throw new Error(j.message || "Couldn't hear that.");
    if (j.silent) throw new Error(DEAD);
    return j.text;
  }
  // hands-free: listen until the player has spoken and then been quiet for a moment. "" if they said nothing.
  async function listen({ wait = 8000, quiet = 1300, longest = 25000, loud = 0.02, cancelled = () => false } = {}) {
    await start();
    const began = Date.now();
    let heard = false, lastLoud = 0;
    while (true) {
      await new Promise(r => setTimeout(r, 100));
      const now = Date.now();
      if (cancelled()) { await close(); return ""; }
      if (level > loud) { heard = true; lastLoud = now; }
      if (!heard && now - began > wait) { await close(); if (!sound) throw new Error(DEAD); return ""; }
      if ((heard && now - lastLoud > quiet) || now - began > longest) return stop();
    }
  }
  return { start, stop, listen, close, get on() { return !!ctx; }, get level() { return level; } };
})();

// a question box with a microphone: onAsk(text) answers it
function askBox(el, { placeholder, enabled, listen, onAsk, coach }) {
  el.innerHTML = `<div class="row"><input class="field" data-q placeholder="${esc(enabled ? placeholder : "Add an AI key in Settings to ask the coach")}" ${enabled ? "" : "disabled"}>
    ${listen && enabled ? `<button class="btn mic" data-mic title="Click to talk, click again to stop">Talk</button>` : ""}
    <button class="btn" data-ask ${enabled ? "" : "disabled"}>Ask</button></div><div data-a class="small" style="margin-top:8px"></div>`;
  if (!enabled) {  // the feature is never hidden: say what a free key gives, and where to add it
    el.innerHTML = `<p class="small" style="margin:0 0 10px">Talk with your coaches and get real replies with a free AI key.</p>
      <a class="btn" href="#/settings">Set up now</a>`;
    return;
  }
  const q = $("[data-q]", el), out = $("[data-a]", el), mic = $("[data-mic]", el);
  const go = async () => {
    const text = q.value.trim(); if (!text) return;
    out.innerHTML = `<span class="muted">Thinking…</span>`;
    try { const r = await onAsk(text); out.innerHTML = `<div class="coach-says">${esc(r.text)}</div>` +
      (r.ai !== false ? `<p class="kw-ai-note">AI can make mistakes. <button class="kw-report">Report it</button></p>` : "");
      const rep = $(".kw-report", out); if (rep) rep.onclick = feedbackBox; Voice.speak(r.text, false, (COACHES[coach] || {}).voice); }
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

// ---------- feedback from beta testers: three short questions, saved with the app version ----------
function feedbackBox() {
  if ($(".feedback-pop")) return;
  const page = location.hash.replace(/^#\/?/, "") || "home";
  const box = document.createElement("div");
  box.className = "box feedback-pop stack";
  box.innerHTML = `<div class="row spread"><h2 style="margin:0">Send feedback</h2><button class="btn small-btn" data-close>✕</button></div>
    <label class="small">What were you doing?<textarea class="field" data-doing rows="2" maxlength="1500" placeholder="For example: going through my last game's review"></textarea></label>
    <label class="small">What went wrong, or was confusing?<textarea class="field" data-wrong rows="3" maxlength="1500" placeholder="For example: the arrow pointed at the wrong square"></textarea></label>
    <label class="small">Your email, only if you'd like a reply (optional)<input class="field" type="email" data-reply maxlength="120" placeholder="you@example.com" style="width:100%;margin-top:4px"></label>
    <div class="small">How much did Knightwise help today? <span class="stars">${[1, 2, 3, 4, 5].map(n => `<button class="btn small-btn" data-n="${n}">${n}</button>`).join("")}</span></div>
    <div class="row"><button class="btn primary" data-send>Send</button></div>
    <span class="small muted" data-msg>It goes to ${FEEDBACK_TO}, with the app version and this page (${esc(page)}). Nothing else about you, and your email only if you add it.</span>`;
  document.body.appendChild(box);
  let helped = 0;
  box.querySelector("[data-close]").onclick = () => box.remove();
  box.querySelectorAll("[data-n]").forEach(b => b.onclick = () => {
    helped = Number(b.dataset.n); box.querySelectorAll("[data-n]").forEach(x => x.classList.toggle("primary", Number(x.dataset.n) <= helped));
  });
  // by email (19 Oct: not a GitHub form, most people don't use GitHub); Copy text for those without a mail app
  const send = async email => {
    const wrong = box.querySelector("[data-wrong]").value.trim(), doing = box.querySelector("[data-doing]").value.trim();
    const replyTo = box.querySelector("[data-reply]").value.trim();  // optional: so the maker can press Reply (22 Oct)
    if (!wrong && !doing && !helped) return;
    const r = await api("/api/feedback", { doing, wrong, helped, page, email, reply: replyTo });
    const msg = box.querySelector("[data-msg]");
    if (email && r.limit) {  // four sent from this PC today: copy instead (22 Oct)
      try { await navigator.clipboard.writeText(r.text); } catch (e) {}
      msg.textContent = `You've sent ${r.limit} today, thank you! It's copied: paste it into an email to ${FEEDBACK_TO}.`; return;
    }
    if (email && r.key) {  // one click: straight to the builder's inbox through Web3Forms (22 Oct)
      msg.textContent = "Sending…";
      try {
        const sent = await fetch("https://api.web3forms.com/submit", { method: "POST",
          headers: { "Content-Type": "application/json", Accept: "application/json" },
          body: JSON.stringify({ access_key: r.key, subject: `Knightwise feedback (${r.version})`, from_name: "Knightwise", message: r.text,
            ...(r.reply ? { email: r.reply, replyto: r.reply } : {}) }) })
          .then(x => x.json());
        if (!sent.success) throw new Error(sent.message || "not sent");
        msg.textContent = "Sent. Thank you!"; setTimeout(() => box.remove(), 2500); return;
      } catch (e) { email = false; }  // offline or the service is down: copy it instead, so nothing is lost
    }
    if (email) { msg.textContent = "Your email app is opening with it. Press Send there. Thank you!"; setTimeout(() => box.remove(), 4000); return; }
    try { await navigator.clipboard.writeText(r.text); msg.textContent = `Copied. Paste it into an email to ${FEEDBACK_TO}. Thank you!`; }
    catch (e) { msg.textContent = `Couldn't copy here. Please write to ${FEEDBACK_TO}.`; }
  };
  box.querySelector("[data-send]").onclick = () => send(true);
}
const FEEDBACK_TO = "nanotech.mark.robots@gmail.com";

// One tap at a natural ending (the end of a review, a finished set): never a pop-up, at most once a day, easy to
// ignore. 👎 opens the feedback form; 👍 is kept on this PC. (19 Oct: "in the user's mind, never in the way")
function helpful(el, where) {
  if (!el) return;
  const today = new Date().toISOString().slice(0, 10);
  try { if (localStorage.getItem("kw-helpful") === today) return; localStorage.setItem("kw-helpful", today); } catch (e) { return; }
  el.className = "row helpful small muted";
  el.innerHTML = `<span>Was this helpful?</span><button class="btn small-btn" data-up title="Yes">👍</button><button class="btn small-btn" data-down title="Not really: tell us why">👎</button>`;
  el.querySelector("[data-up]").onclick = () => { api("/api/feedback", { doing: where, wrong: "", helped: 5, page: where }).catch(() => {}); el.textContent = "Thanks!"; };
  el.querySelector("[data-down]").onclick = () => { el.textContent = ""; feedbackBox(); };
}

// ---------- shell ----------
function shell(active, body) {
  const item = (route, name, icon) =>
    `<a href="#/${route}" class="${active === route ? "on" : ""}">${svg(icon)}<span>${name}</span></a>`;
  $("#root").innerHTML = `
    <div class="shell">
      <aside class="side">
        <div class="brand"><div class="brand-mark" style="color:var(--on-invert)">${svg("pawn")}</div><span>Knightwise</span></div>
        <nav class="nav">${item("home", "Home", "home")}${item("games", "Games", "games")}${item("practice", "Practice", "practice")}${item("plan", "Your plan", "plan")}${item("course", "Your course", "book")}${item("level", "Your level", "up")}${item("progress", "Progress", "progress")}${item("settings", "Settings", "settings")}</nav>
        <button class="btn side-voice" id="mute" title="Voice on or off">${Voice.on ? "Voice on" : "Voice off"}</button>
        <button class="side-ai" id="aiuse" hidden></button>
        <button class="side-ai" id="feedback" title="Tell us what went wrong or what was confusing">Send feedback</button>
        <div class="side-foot" id="status"><i class="dot"></i><span>Connecting…</span></div>
      </aside>
      <main><div class="page" id="page">${body}</div></main>
    </div>`;
  paintStatus(); paintAiUse();
  $("#feedback").onclick = feedbackBox;
  $("#mute").onclick = () => {
    Voice.set(!Voice.on);
    $("#mute").textContent = Voice.on ? "Voice on" : "Voice off";
    api("/api/settings", { voice: Voice.on }).catch(() => {});
  };
}

// the AI usage panel, like Claude's: a bar per key, what's left today, and who is resting
const FREE_DAY = { groq: 1000, gemini: 250 };  // published free requests a day; Groq's own numbers replace these
async function paintAiUse() {
  const b = $("#aiuse");
  if (!b) return;
  const u = await api("/api/ai-usage").catch(() => null);
  if (!u || !u.slots.length) { b.hidden = true; return; }
  const rows = u.slots.map(x => {
    const limit = x.requests_limit || FREE_DAY[x.provider], left = x.requests_left ?? (limit ? limit - x.requests : null);
    const pct = limit ? Math.min(100, Math.round(100 * (limit - left) / limit)) : 0;
    return { ...x, limit, left, pct };
  });
  const top = Math.max(...rows.map(r => r.pct)), rest = rows.some(r => r.resting_minutes);
  b.hidden = false;
  b.innerHTML = `<i class="dot ${rest ? "busy" : top > 80 ? "busy" : "ok"}"></i><span>AI · ${top}% used today</span>`;
  b.onclick = () => {
    const old = $(".ai-pop"); if (old) { old.remove(); return; }
    const pop = document.createElement("div"); pop.className = "ai-pop box";
    pop.innerHTML = `<div class="row spread"><b>AI use today</b><button class="btn ghost" data-x>×</button></div>
      ${rows.map(r => `<div class="ai-row"><div class="row spread"><span>${esc(r.name)}${r.slot === "slot1" ? " · main" : " · backup"}</span>
          <span class="muted">${r.resting_minutes ? `resting, ${r.resting_minutes} min` : `${r.pct}%`}</span></div>
        <div class="bar ${r.pct > 80 || r.resting_minutes ? "red" : ""}"><div style="width:${r.pct}%"></div></div>
        <div class="small muted">${r.requests} questions${r.tokens ? ` · ${r.tokens.toLocaleString()} tokens` : ""}${r.left != null ? ` · about ${r.left} left` : ""}${r.resets ? ` · resets in ${esc(r.resets)}` : ""}</div></div>`).join("")}
      <p class="small muted" style="margin:10px 0 0">When one is busy or used up, the other answers. If both are, your coaches use their written sentences.</p>`;
    document.body.appendChild(pop);
    $("[data-x]", pop).onclick = () => pop.remove();
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
    ${row("Key moments a game", v.now.moments, v.then.moments, true)}</div>`;
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
// A move in plain words: "Nf3" -> "knight to f3", "exd5" -> "pawn takes on d5", "O-O" -> "castles"
// (13 Oct test, point 21: the tree's notation was confusing for a beginner)
const PIECE_NAME = { N: "knight", B: "bishop", R: "rook", Q: "queen", K: "king" };
function plainMove(san) {
  if (san.startsWith("O-O-O")) return "castles on the queen's side";
  if (san.startsWith("O-O")) return "castles: the king goes to safety";
  const m = /^([NBRQK])?[a-h]?[1-8]?(x)?([a-h][1-8])(?:=([NBRQ]))?([+#])?$/.exec(san);
  if (!m) return san;
  const piece = PIECE_NAME[m[1]] || "pawn";
  return `${piece} ${m[2] ? "takes on" : "to"} ${m[3]}${m[4] ? `, becomes a ${PIECE_NAME[m[4]]}` : ""}${m[5] === "#" ? ", checkmate" : m[5] ? ", check" : ""}`;
}

async function openingTree() {
  shell("games", `<p class="muted">Loading…</p>`);
  const t = (await api("/api/openings")).tree || {};
  if (!t.white && !t.black) { $("#page").innerHTML = `<div class="empty">Your opening tree appears once your games are checked.</div>`; return; }
  const label = n => `${Math.ceil(n.ply / 2)}${n.ply % 2 ? "." : "..."} ${n.san}`;
  const byFen = {};
  let picked = null;
  const node = (n, depth, white) => {
    const kids = n.children.filter(c => c.games >= 2);
    const good = n.score >= 55, bad = n.score <= 40, yours = (n.ply % 2 === 1) === white;
    const key = (white ? "w " : "b ") + n.fen;  // the same position can be in both trees
    byFen[key] = { n, white };
    const row = `<div class="tree-row" data-fen="${esc(key)}"><span class="tree-move num">${esc(label(n))}</span>
      <span class="tree-name"><b>${yours ? "You" : "They"}:</b> ${esc(plainMove(n.san))}${n.name ? ` <span class="faint">· ${esc(n.name)}</span>` : ""}</span>
      <span class="tree-games small muted num">${n.games} game${n.games > 1 ? "s" : ""}</span>
      <span class="tree-score ${good ? "good" : bad ? "bad" : ""}" title="How you did in the games that went this way"><i style="width:${n.score}%"></i><b class="num">${n.score}%</b></span></div>
      ${n.note ? `<div class="tree-note ${bad ? "bad" : "good"}">${esc(n.note)}</div>` : ""}`;
    if (!kids.length) return `<div class="tree-leaf">${row}</div>`;
    return `<details class="tree-node" ${depth < 1 || n.note ? "open" : ""}><summary>${row}</summary>
      <div class="tree-kids">${kids.map(c => node(c, depth + 1, white)).join("")}</div></details>`;
  };
  const side = (name, root, white) => root ? `<div class="box rise"><div class="row spread"><h2 style="margin:0">When you are ${name}</h2>
      <span class="small muted">${root.games} games · you score ${root.score}%</span></div>
      <div class="tree">${root.children.filter(c => c.games >= 2).map(c => node(c, 0, white)).join("")}</div></div>` : "";
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/games" class="small muted" style="text-decoration:none">← Games</a>
      <h1 style="margin-top:6px">How your games start</h1><p class="sub">Your opening tree: the first three moves of every game you played, and how each way went for you.</p></div></div>
    <div class="game-layout">
      <div class="stack">
        <div class="box stack intro-box" style="padding:16px">
          <h2 style="margin:0">How to read it</h2>
          <p class="small" style="margin:0">Each row is one move from the start of your games. Click a row to see the board after it, and the moves that came next.</p>
          <p class="small" style="margin:0"><b>1. e4</b> is White's first move, <b>1... e5</b> is Black's answer. The letter and number are the square: files a to h, rows 1 to 8.
            A capital letter is the piece: N knight, B bishop, R rook, Q queen, K king. No letter means a pawn.</p>
          <p class="small" style="margin:0">The bar is your score in the games that went that way: a win counts 1, a draw a half. <span class="good-text">Green</span> is where you do well, <span class="bad-text">red</span> is where you lose more.</p>
        </div>
        ${side("White", t.white, true)}${side("Black", t.black, false)}
      </div>
      <div class="stack tree-side"><div class="board-wrap" id="treeboard"></div><div class="box" style="padding:14px" id="treesay">
        <p class="small muted" style="margin:0">Click a move on the left to see it here.</p></div></div>
    </div>`;
  Board.render($("#treeboard"), { fen: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1" });
  document.querySelectorAll(".tree-row[data-fen]").forEach(r => r.addEventListener("click", () => {
    const x = byFen[r.dataset.fen];
    if (!x) return;
    document.querySelectorAll(".tree-row.on").forEach(e => e.classList.remove("on"));
    r.classList.add("on");
    picked = x.n;
    Board.render($("#treeboard"), { fen: x.n.fen, flip: !x.white });
    const yours = (x.n.ply % 2 === 1) === x.white;
    $("#treesay").innerHTML = `<b>${esc(label(x.n))}</b>: ${yours ? "you played" : "they played"} ${esc(plainMove(x.n.san))}.
      <p class="small muted" style="margin:6px 0 0">${x.n.games} of your games went this way. You scored ${x.n.score}%: ${x.n.win} won, ${x.n.draw} drawn, ${x.n.loss} lost.${x.n.name ? ` Its name: ${esc(x.n.name)}.` : ""}</p>`;
  }));
  const worst = [t.white, t.black].filter(Boolean).flatMap(function all(n) { return [n, ...n.children.flatMap(all)]; })
    .filter(n => n.note && n.score <= 40).sort((a, b) => b.games - a.games)[0];
  if (worst) Coach.react("maya", "explain", `This is how your games start. Look at ${label(worst)}${worst.name ? `, the ${worst.name}` : ""}: ${worst.note} Your plan has an opening that fixes this.`,
    [{ label: "Your plan", app: "plan" }]);
  else Coach.react("maya", "explain", "This is how your games start, and how each way went for you. Click a move to see it on the board.");
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

// ---------- spar against a player you'll meet: their openings, then human moves at their rating (0.11) ----------
async function sparView(user, color) {
  shell("games", `<p class="muted">Reading their games…</p>`);
  let s;
  try { s = await api(`/api/spar/${encodeURIComponent(user)}?color=${color}`); }
  catch (e) { $("#page").innerHTML = `<div class="empty">${esc(e.message)}</div>`; return; }
  const history = [s], played = [];
  let picked = null, busy = false, last = {};
  const FROM = { book: "their usual move", human: "like a player of their rating", engine: "the engine, at about their level" };
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/prep/${esc(user)}" class="small muted" style="text-decoration:none">← Prep</a>
      <h1 style="margin-top:6px">Spar vs ${esc(user)} <span class="faint num">${s.rating}</span></h1>
      <p class="sub">They open the way they really do, from their games. When their games run out, ${s.human ? "Maia plays on like real players of their rating" : "the engine plays on at about their level"}. It's someone who plays like them, not the person.</p></div></div>
    <div class="game-layout">
      <div><div class="board-wrap" id="board"></div></div>
      <div class="stack"><div class="box stack" style="padding:16px">
        <h2 style="margin:0">You are ${color === "white" ? "White" : "Black"}</h2>
        <div class="small muted" id="sfrom"></div>
        <div class="movelist" id="smoves"></div><div class="err" id="smsg"></div>
        <div class="row"><button class="btn" id="undo">Take back</button><button class="btn" id="again">New game</button></div></div></div>
    </div>`;
  const cur = () => history[history.length - 1];
  const mineAt = sq => cur().legal.some(u => u.startsWith(sq));
  if (s.reply) { played.push(s.reply.san); last = { [s.reply.uci.slice(0, 2)]: "hl-last", [s.reply.uci.slice(2, 4)]: "hl-last" }; }
  function tell(r) { $("#sfrom").textContent = r && r.reply ? `${r.reply.san}: ${FROM[r.reply.from]}${r.reply.games ? `, in ${r.reply.games} of their games` : ""}.` : ""; }
  function draw() {
    const targets = picked ? cur().legal.filter(u => u.startsWith(picked)).map(u => u.slice(2, 4)) : [];
    const hl = { ...last }; if (picked) hl[picked] = "hl-pick";
    Board.render($("#board"), { fen: cur().fen, flip: s.flip, highlights: hl, targets, onClick: click });
    let html = "";  // every move in order, two to a line
    for (let i = 0; i < played.length; i += 2) html += `<span class="n">${i / 2 + 1}.</span><span>${esc(played[i])}</span><span>${esc(played[i + 1] || "")}</span>`;
    $("#smoves").innerHTML = html || `<span class="small muted" style="grid-column:1/-1">Your move.</span>`;
  }
  function click(sq) {
    if (busy || cur().over) return;
    if (picked && picked !== sq) { const uci = cur().legal.find(u => u.slice(0, 4) === picked + sq); if (uci) return move(uci); }
    picked = picked === sq || !mineAt(sq) ? null : sq; draw();
  }
  async function move(uci) {
    busy = true; picked = null;
    let r;
    try { r = await api("/api/spar/move", { user, fen: cur().fen, uci, color, rating: s.rating }); }
    catch (e) { $("#smsg").textContent = e.message; busy = false; draw(); return; }
    last = { [uci.slice(0, 2)]: "hl-last", [uci.slice(2, 4)]: "hl-last" };
    Board.render($("#board"), { fen: r.mine.fen, flip: s.flip, highlights: last }); Sound.move(r.mine.san);
    played.push(r.mine.san);
    await wait(r.reply ? 550 : 0);
    if (r.reply) {
      last = { [r.reply.uci.slice(0, 2)]: "hl-last", [r.reply.uci.slice(2, 4)]: "hl-last" }; Sound.move(r.reply.san);
      played.push(r.reply.san);
    }
    history.push(r); tell(r); busy = false; draw();
    if (r.over) { if (r.result === "win") confetti(); Coach.react("maya", r.result === "win" ? "celebrate" : "explain", r.say, [{ label: "New game", app: `spar/${user}/${color}` }]); }
  }
  $("#undo").onclick = () => { if (busy || history.length < 2) return; const r = history.pop(); played.splice(played.length - (r.reply ? 2 : 1)); last = {}; tell(cur()); draw(); };
  $("#again").onclick = () => sparView(user, color);
  tell(s); draw();
  Coach.react("maya", "explain", `${user} opens the way they really do. Play your repertoire against it, and watch what they like to do.`);
}

// ---------- Rematch your loss (flagship 4): the real game up to where it went wrong, then you play it out ----------
async function rematchView(gid, ply) {
  shell("games", `<p class="muted">Loading…</p>`);
  let s;
  try { s = await api(`/api/rematch/${gid}/${ply}`); }
  catch (e) { $("#page").innerHTML = `<div class="empty">There's no rematch for this game: rematches are for games you didn't win.</div>`; return; }
  const white = s.color === "white", history = [s], played = [];
  let picked = null, busy = true, last = {};
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/games/${esc(gid)}" class="small muted" style="text-decoration:none">← Back to the game</a>
      <h1 style="margin-top:6px">Rematch vs ${esc(s.opponent)} <span class="faint num">${s.rating}</span></h1>
      <p class="sub">From move ${s.move_number}, where it went wrong. In the real game you played ${esc(s.real_move)} and ${s.real === "loss" ? "lost" : "drew"}.</p></div></div>
    <div class="game-layout">
      <div><div class="board-wrap" id="board"></div></div>
      <div class="stack">
        <div class="box stack" style="padding:16px">
          <h2 style="margin:0">Your moves from here</h2>
          <p class="small muted" style="margin:0">${s.human ? `They play like real ${s.rating} players: Maia, the human-move model, learned from millions of games at that level. It's players like them, not the person.`
            : `They play at about their level: the engine makes mistakes on purpose, the way a ${s.rating} player might. It's an approximation, not the person.`}</p>
          <div class="movelist" id="rmoves"></div>
          <div class="err" id="rmsg"></div>
          <div class="row"><button class="btn" id="undo">Take back</button><button class="btn" id="again">Start again</button></div>
        </div>
      </div>
    </div>`;
  const cur = () => history[history.length - 1];
  const mineAt = (sq) => cur().legal.some(u => u.startsWith(sq));
  function draw() {
    const targets = picked ? cur().legal.filter(u => u.startsWith(picked)).map(u => u.slice(2, 4)) : [];
    const hl = { ...last };
    if (picked) hl[picked] = "hl-pick";
    Board.render($("#board"), { fen: cur().fen, flip: s.flip, highlights: hl, targets, onClick: click });
    let html = "";
    // numbered from the real game: you, then their answer
    played.forEach((p, i) => { html += `<span class="n">${s.move_number + i}.</span><span>${esc(p[0])}</span><span>${esc(p[1] || "")}</span>`; });
    $("#rmoves").innerHTML = html || `<span class="small muted" style="grid-column:1/-1">Your move. Not ${esc(s.real_move)} this time.</span>`;
  }
  async function click(sq) {
    if (busy || cur().over) return;
    if (picked && picked !== sq) {
      const uci = cur().legal.find(u => u.slice(0, 4) === picked + sq);
      if (uci) return move(uci);
    }
    picked = picked === sq || !mineAt(sq) ? null : sq;  // a click on the picked piece puts it down again
    draw();
  }
  async function move(uci) {
    busy = true; picked = null;
    const before = cur();
    let r;
    try { r = await api("/api/rematch/move", { fen: before.fen, uci, rating: s.rating, white, real: s.real }); }
    catch (e) { $("#rmsg").textContent = e.message; busy = false; draw(); return; }
    // your move first, then theirs a moment later
    last = { [uci.slice(0, 2)]: "hl-last", [uci.slice(2, 4)]: "hl-last" };
    Board.render($("#board"), { fen: r.mine.fen, flip: s.flip, highlights: last });
    Sound.move(r.mine.san);
    played.push([r.mine.san, r.reply ? r.reply.san : null]);
    await wait(r.reply ? 550 : 0);
    if (r.reply) { last = { [r.reply.uci.slice(0, 2)]: "hl-last", [r.reply.uci.slice(2, 4)]: "hl-last" }; Sound.move(r.reply.san); }
    history.push(r);
    busy = false; draw();
    if (played.length === 1) Coach.react("maya", "pleased", `${r.mine.san} instead of ${s.real_move}. Now play it out.`);
    if (r.over) {
      if (r.result === "win") confetti();
      Coach.react("maya", r.result === "win" ? "celebrate" : r.result === "loss" ? "encourage" : "explain", r.say,
        [{ label: "Start again", run: restart }, { label: "Back to the game", app: `games/${gid}` }]);
    } else if (r.check) Coach.react("maya", "worried", "Check. Your king first.");
  }
  function restart() { history.length = 1; played.length = 0; last = {}; picked = null; draw(); }
  $("#undo").onclick = () => { if (busy || history.length < 2) return; history.pop(); played.pop(); last = {}; picked = null; draw(); };
  $("#again").onclick = () => { if (!busy) restart(); };
  // the real game, its last few moves, so you see how you got here
  for (const fen of s.lead_in) { Board.render($("#board"), { fen, flip: s.flip }); await wait(420); }
  busy = false; draw();
  Coach.react("maya", "explain", `Your game against ${s.opponent}, just before move ${s.move_number}. In the real game you played ${s.real_move}` +
    ` and ${s.real === "loss" ? "lost" : "drew"}. Play something better this time, then play it out. They'll play at about their level.`);
}

// ---------- your level: the ladder from beginner to 2,000+, measured on your last 20 games (0.6) ----------
function skillValue(s) {
  if (s.value === null) return "not enough games yet";
  const v = s.unit === "%" ? `${Math.round(s.value)}%` : s.unit === "points" ? `${s.value.toFixed(1)}` : `${s.value}`;
  const t = s.unit === "%" ? `${s.target}%` : `${s.target}`;
  return `${v} ${s.unit && s.unit !== "%" ? s.unit : ""} · goal: ${s.way === "max" ? "at most" : "at least"} ${t}`.replace(/\s+/g, " ");
}

async function levelView() {
  shell("level", `<p class="muted">Loading…</p>`);
  const p = await api("/api/ladder");
  if (!p.player) return go("welcome");
  if (!p.levels || !p.levels.length) { $("#page").innerHTML = `<div class="empty">Your level appears once your games are checked.</div>`; return; }
  const cur = p.levels[p.current];
  const level = (l, i) => `<div class="box rise level ${i === p.current ? "now" : l.done ? "done" : "later"}">
      <div class="row spread"><div><div class="label">Level ${i + 1} · ${esc(l.band)}</div><h2 style="margin:4px 0 0">${esc(l.name)}</h2></div>
        <span class="chip ${l.done ? "win" : i === p.current ? "draw" : ""}">${l.done ? "Done" : i === p.current ? "Working on it" : "Later"}</span></div>
      ${i <= p.current || l.done ? `<div class="skills">${l.skills.map(s => `<div class="skill ${s.met ? "met" : s.met === false ? "not" : ""}">
        <div class="skill-head"><b>${s.met ? "✓ " : ""}${esc(s.name)}</b>${s.met === false && i === p.current ? `<a class="btn small-btn" href="#/${esc(s.train.route)}">${esc(s.train.label)}</a>` : ""}</div>
        <div class="small muted">${esc(s.what)}: ${esc(skillValue(s))}</div></div>`).join("")}</div>`
        : `<p class="small muted" style="margin:8px 0 0">${l.skills.map(s => esc(s.name)).join(" · ")}</p>`}
    </div>`;
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>Your level</h1>
      <p class="sub">Five levels from beginner to 2,000+, measured on your last ${p.games} games. A level is done when every skill meets its goal.</p></div>
      <div class="row"><a class="btn" href="#/repertoire">Your repertoire</a><a class="btn" href="#/calc">See it in your head</a><a class="btn" href="#/blindfold">Blindfold</a><a class="btn" href="#/guess">Weekly challenge: guess the human move</a><a class="btn" href="#/endgames">Endgame trainer</a></div></div>
    <div class="stack">${p.levels.map(level).join("")}</div>
    <p class="note">The goals are our first estimate of each level, and we'll tune them on real players' games. They don't promise a rating; your games show the progress.</p>`;
  const next = cur.skills.find(s => s.met === false);
  Coach.react("viktor", "explain", next
    ? `You're on level ${p.current + 1}, ${cur.name}. The one thing now: ${next.name.toLowerCase()}. ${next.what}: ${skillValue(next)}.`
    : `Every level done. Remarkable. Keep playing: the numbers keep watching.`,
    next ? [{ label: next.train.label, app: next.train.route }] : []);
}

// ---------- the course: the teacher. Lessons in order, picked by your games, passed by your games (0.10) ----------
const COURSE_CHIP = { open: ["To do", ""], again: ["Once more", "draw"], watching: ["Watching your games", "draw"],
  passed: ["Done ✓", "win"], fine: ["You already do this", "win"], later: ["Later", ""], coming: ["Coming", ""] };

async function courseView() {
  shell("course", `<p class="muted">Loading…</p>`);
  const c = await api("/api/course");
  if (!c.player) return go("welcome");
  const next = c.lessons.find(l => l.next);
  const row = l => {
    const [label, cls] = l.next ? ["Next for you", "draw"] : COURSE_CHIP[l.status];
    const can = l.status !== "coming";
    return `<div class="course-row ${l.next ? "now" : ""} ${l.status}">
      <div><b>${esc(l.title)}</b><div class="small muted">${esc(l.reason || l.habit)}</div></div>
      <div class="row"><span class="chip ${cls}">${esc(label)}</span>
        ${can ? `<a class="btn small-btn" href="#/course/${l.id}">${l.status === "passed" || l.status === "fine" ? "Again" : "Open"}</a>` : ""}</div></div>`;
  };
  const groups = Object.keys(c.levels).map((lv, i) => {
    const ls = c.lessons.filter(l => l.level === lv);
    const done = ls.filter(l => l.status === "passed" || l.status === "fine").length;
    return `<div class="box rise stack" style="padding:16px"><div class="row spread"><div><div class="label">Level ${i + 1}</div>
        <h2 style="margin:4px 0 0">${esc(c.levels[lv])}</h2></div><span class="small muted num">${done} of ${ls.length} done</span></div>
      ${ls.map(row).join("")}</div>`;
  }).join("");
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>Your course</h1>
      <p class="sub">From beginner to 2,000+, one idea at a time. Your games pick the next lesson, and a lesson is done only when that mistake drops in the games you play after it.</p></div></div>
    ${next ? `<div class="box plan-card new" style="margin-bottom:16px"><div class="plan-face">${KnightwiseFaces.figure("viktor", "pleased")}</div>
      <div class="plan-text"><div class="label">Next for you</div><h3>${esc(next.title)}</h3><p class="muted small">${esc(next.reason)}</p>
      <a class="btn primary" href="#/course/${next.id}">Start the lesson</a></div></div>` : ""}
    <div class="stack">${groups}</div>
    <p class="note">Lessons written for Knightwise. Positions from your own games and the Lichess puzzle database, checked by Stockfish. "Coming" lessons need strong players' games, a download that waits for your yes.</p>`;
  Coach.react("viktor", "explain", next ? `Next for you: ${next.title.toLowerCase()}. ${next.reason}` : "Every lesson at your level is done or already fine. Keep playing: your games keep watching.",
    next ? [{ label: "Start the lesson", app: `course/${next.id}` }] : []);
}

async function courseLesson(id) {
  shell("course", `<p class="muted">Setting up your positions…</p>`);
  let item;
  try { item = await api(`/api/course/${encodeURIComponent(id)}`); }
  catch (e) { $("#page").innerHTML = `<div class="empty">${esc(e.message)}</div>`; return; }
  const back = `<a href="#/course" class="small muted" style="text-decoration:none">← Your course</a>`;
  const own = item.drills.filter(d => d.kind === "game" && d.why);
  const finish = (right, total) => api("/api/course/done", { id: item.id, right, total }).catch(() => {});
  $("#page").innerHTML = `
    <div class="page-head"><div>${back}<h1 style="margin-top:6px">${esc(item.title)}</h1>
      ${item.reason ? `<p class="sub">${esc(item.reason)}</p>` : ""}</div></div>
    <div class="grid course-learn">
      <div class="box stack" style="padding:18px"><div class="label">The idea</div>
        ${item.teach.map(t => `<p style="margin:0 0 4px">${esc(t)}</p>`).join("")}
        <div class="coach-says"><b>The habit:</b> ${esc(item.habit)}</div></div>
      ${own.length ? `<div class="box stack" style="padding:18px"><div class="label">In your games</div>
        ${own.map(d => `<div><div class="small muted">${esc(d.where)}</div><p style="margin:2px 0 0">${esc(d.why)}</p></div>`).join("")}</div>` : ""}
    </div>
    <div class="row" style="margin-top:16px">
      ${item.drills.length ? `<button class="btn primary" id="practise">Practise it: ${item.drills.length} positions</button>` : ""}
      ${item.train ? `<a class="btn ${item.drills.length ? "" : "primary"}" href="#/${esc(item.train[1])}" id="train">${esc(item.train[0])}</a>` : ""}
      ${!item.drills.length ? `<button class="btn" id="studied">I've studied it</button>` : ""}</div>`;
  const tr = $("#train"); if (tr && !item.drills.length) tr.addEventListener("click", () => finish(0, 0));
  const st = $("#studied"); if (st) st.onclick = async () => { await finish(0, 0); go("course"); };
  const pr = $("#practise");
  if (pr) pr.onclick = () => {
    $("#page").innerHTML = trainerPage(item.title, { back: `<a href="#/course/${esc(item.id)}" class="small muted" style="text-decoration:none">← The lesson</a>`, text: item.habit });
    trainer(item.drills, { coach: item.coach, record: true, onDone: rightFirst => {
      finish(rightFirst, item.drills.length);
      setTimeout(() => Coach.react(item.coach, "celebrate",
        `${rightFirst} of ${item.drills.length} right first time. Now the real test: your next ${5} games. I'll watch for this mistake and tell you when it's gone.`,
        [{ label: "Back to your course", app: "course" }]), 2500);
    } });
  };
  Coach.react(item.coach, "explain", `${item.title}. ${item.teach[0]} The habit: ${item.habit}`);
}

// a lesson on one theme at your level, opened from a skill on Your level
async function themeLesson(theme) {
  shell("level", `<p class="muted">Loading…</p>`);
  const item = await api(`/api/lesson/${encodeURIComponent(theme)}`);
  return lessonView({ ...item, back: "level" });
}

// ---------- your repertoire: three opening lines to know by heart (0.8) ----------
async function repertoireView(fresh) {
  shell("level", `<p class="muted">Choosing your lines…</p>`);
  const lines = await api(`/api/repertoire${fresh ? "?fresh=1" : ""}`);
  const slot = l => l.side === "white" ? "As White" : `As Black, against 1. ${l.against}`;
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/level" class="small muted" style="text-decoration:none">← Your level</a>
      <h1 style="margin-top:6px">Your repertoire</h1>
      <p class="sub">Three lines to know by heart, chosen from what you already play: from the Lichess opening catalogue, checked by Stockfish. They stay until you ask for new ones.</p></div>
      <button class="btn" id="newlines">Choose new lines</button></div>
    <div class="plan-grid">${lines.map((l, i) => `<div class="box plan-card"><div class="plan-text">
      <div class="label">${esc(slot(l))}${l.kept ? " · you already play this" : ""}</div>
      <h3>${esc(l.name)}</h3><p class="muted small">${l.kept ? "It works for you: now learn it to move 6." : esc(l.why)}</p>
      <a class="btn ${i === 0 ? "primary" : ""}" href="#/repertoire/${i}">Practise it</a></div></div>`).join("") || `<div class="empty">Your lines appear once your games are checked.</div>`}</div>`;
  $("#newlines").onclick = () => repertoireView(true);
  Coach.react("viktor", "explain", "Three lines. Know them to move six without thinking, and every game starts on your terms.");
}

// ---------- the endgame trainer: the endings every player must know, against the best defence (0.7) ----------
const GOAL = { mate: "Checkmate them", promote: "Make a new queen", draw: "Hold the draw" };

async function endgamesView() {
  shell("level", `<p class="muted">Loading…</p>`);
  const list = await api("/api/endgames");
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/level" class="small muted" style="text-decoration:none">← Your level</a>
      <h1 style="margin-top:6px">Endgame trainer</h1>
      <p class="sub">The endings every player must know, played out against perfect defence: Lichess's endgame tablebase knows the best move in every one. A new position each time.</p></div></div>
    <div class="plan-grid">${list.map(e => `<div class="box plan-card">
      <div class="plan-text"><div class="label">Level ${e.level} · ${esc(GOAL[e.goal])} in ${e.limit} moves</div>
        <h3>${esc(e.name)}</h3><p class="muted small">${esc(e.idea)}</p>
        <a class="btn ${e.solved ? "" : "primary"}" href="#/endgame/${e.id}">${e.solved ? `Again · solved ${e.solved}×` : "Start"}</a></div></div>`).join("")}</div>`;
  Coach.react("viktor", "explain", "Endings. Every won game ends in one of these. Learn them once and they win games for the rest of your life.");
}

async function endgameView(id) {
  shell("level", `<p class="muted">Setting up the position…</p>`);
  let s;
  try { s = await api(`/api/endgame/${encodeURIComponent(id)}`); } catch (e) { $("#page").innerHTML = `<div class="empty">No such ending.</div>`; return; }
  const history = [{ ...s, made: 0 }];
  let picked = null, busy = false, last = {};
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/endgames" class="small muted" style="text-decoration:none">← Endgame trainer</a>
      <h1 style="margin-top:6px">${esc(s.name)}</h1><p class="sub">${esc(GOAL[s.goal])} within ${s.limit} moves. You are ${s.white ? "White" : "Black"}.</p></div></div>
    <div class="game-layout">
      <div><div class="board-wrap" id="board"></div></div>
      <div class="stack">
        <div class="box stack" style="padding:16px"><div class="label">The idea</div><p style="margin:0">${esc(s.idea)}</p></div>
        <div class="box stack" style="padding:16px"><div class="row spread"><h2 style="margin:0">Moves</h2><span class="small muted num" id="count">0 of ${s.limit}</span></div>
          <div class="movelist" id="emoves"></div><div class="small" id="emsg"></div>
          <div class="row"><button class="btn" id="undo">Take back</button><button class="btn" id="again">New position</button></div></div>
      </div>
    </div>`;
  const cur = () => history[history.length - 1];
  const moves = [];
  function draw() {
    const targets = picked ? cur().legal.filter(u => u.startsWith(picked)).map(u => u.slice(2, 4)) : [];
    Board.render($("#board"), { fen: cur().fen, flip: s.flip, highlights: { ...last, ...(picked ? { [picked]: "hl-pick" } : {}) }, targets, onClick: click });
    $("#emoves").innerHTML = moves.map((m, i) => `<span class="n">${i + 1}.</span><span>${esc(m[0])}</span><span>${esc(m[1] || "")}</span>`).join("")
      || `<span class="small muted" style="grid-column:1/-1">Your move.</span>`;
    $("#count").textContent = `${cur().made} of ${s.limit}`;
  }
  function click(sq) {
    if (busy || cur().over) return;
    if (picked && picked !== sq) {
      const uci = cur().legal.find(u => u.slice(0, 4) === picked + sq);
      if (uci) return move(uci);
    }
    picked = picked === sq || !cur().legal.some(u => u.startsWith(sq)) ? null : sq;
    draw();
  }
  async function move(uci) {
    busy = true; picked = null;
    let r;
    try { r = await api("/api/endgame/move", { id, fen: cur().fen, uci, made: cur().made, limit: s.limit }); }
    catch (e) { busy = false; draw(); return; }
    last = { [uci.slice(0, 2)]: "hl-last", [uci.slice(2, 4)]: "hl-last" };
    Board.render($("#board"), { fen: r.mine.fen, flip: s.flip, highlights: last });
    Sound.move(r.mine.san);
    moves.push([r.mine.san, r.reply ? r.reply.san : null]);
    if (r.reply) { await wait(450); last = { [r.reply.uci.slice(0, 2)]: "hl-last", [r.reply.uci.slice(2, 4)]: "hl-last" }; Sound.move(r.reply.san); }
    history.push(r);
    busy = false; draw();
    $("#emsg").innerHTML = r.warn ? `<span class="bad-text">${esc(r.warn)}</span>` : "";
    if (r.over) {
      if (r.result === "win") { confetti(); Sound.play("done"); }
      Coach.react("viktor", r.result === "win" ? "celebrate" : r.result === "stalemate" ? "worried" : "encourage", r.say,
        [{ label: r.result === "win" ? "Another one" : "Try again", run: () => endgameView(id) }]);
    } else if (r.warn) Coach.react("viktor", "warn", r.warn);
  }
  $("#undo").onclick = () => { if (busy || history.length < 2) return; history.pop(); moves.pop(); last = {}; picked = null; $("#emsg").innerHTML = ""; draw(); };
  $("#again").onclick = () => { if (!busy) endgameView(id); };
  draw();
  Coach.react("viktor", "explain", `${s.name}. ${s.idea}`);
}

// ---------- prep before a game: how a chess.com player plays, from their public games (0.8, flagship 1) ----------
async function prepView(user) {
  shell("games", `<p class="muted">Loading…</p>`);
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/games" class="small muted" style="text-decoration:none">← Games</a>
      <h1 style="margin-top:6px">Prep before a game</h1>
      <p class="sub">How a chess.com player plays, from their public games of the last three months. Only before a game: Knightwise is never active during one.</p></div></div>
    <div class="box stack" style="padding:16px"><div class="row"><input class="field" id="who" placeholder="Their chess.com username" value="${esc(user || "")}" spellcheck="false" style="max-width:280px">
      <button class="btn primary" id="look">Look them up</button></div><div class="err" id="prepmsg"></div></div>
    <div id="prep"></div>`;
  const look = async () => {
    const who = $("#who").value.trim().toLowerCase();
    if (!who) return;
    if (location.hash !== `#/prep/${who}`) history.replaceState(null, "", `#/prep/${who}`);
    $("#prepmsg").textContent = ""; $("#prep").innerHTML = `<p class="muted">Reading their games…</p>`;
    let s;
    try { s = await api(`/api/prep/${encodeURIComponent(who)}`); }
    catch (e) { $("#prep").innerHTML = ""; $("#prepmsg").textContent = e.message; return; }
    const list = (rows, label) => rows.length ? rows.map(r => `<div class="row spread"><span>${label(r)}</span>
        <span class="tree-score"><i style="width:${r.share}%"></i><b class="num">${r.share}%</b></span></div>`).join("") : `<p class="small muted">Not enough games.</p>`;
    const ends = Object.entries(s.endings).sort((a, b) => b[1] - a[1]);
    $("#prep").innerHTML = `
      <div class="grid" style="margin-top:16px">
        <div class="box stack" style="padding:16px"><h2 style="margin:0">${esc(s.user)} <span class="faint num">${s.rating}</span></h2>
          <p class="small muted" style="margin:0">${s.games} games in three months, mostly ${esc(s.time_class)}.</p>
          ${s.advice.map(a => `<p style="margin:0">${esc(a)}</p>`).join("")}</div>
        <div class="box stack" style="padding:16px"><h2 style="margin:0">As White, they start with</h2>
          ${list(s.as_white, r => `1. ${esc(r.what)} <span class="small muted">· ${esc(plainMove(r.what))}</span>`)}</div>
        <div class="box stack" style="padding:16px"><h2 style="margin:0">As Black, they answer</h2>
          ${list(s.as_black, r => { const [a, b] = r.what.split(" "); return `1. ${esc(a)} ${esc(b)} <span class="small muted">· after ${esc(plainMove(a))}: ${esc(plainMove(b))}</span>`; })}</div>
        <div class="box stack" style="padding:16px"><h2 style="margin:0">How their games end</h2>
          ${ends.map(([k, n]) => `<div class="row spread"><span>${esc(cap(k))}</span><b class="num">${n}</b></div>`).join("")}</div>
      </div>`;
    $("#prep").insertAdjacentHTML("beforeend", `<div class="box row" style="padding:16px;margin-top:16px"><div style="flex:1"><b>Spar against them</b>
      <div class="small muted">They open the way they really do, then play like players of their rating.</div></div>
      <a class="btn primary" href="#/spar/${esc(s.user)}/white">As White</a><a class="btn" href="#/spar/${esc(s.user)}/black">As Black</a></div>`);
    Coach.react("maya", "explain", `${s.user}: ${s.advice[0]}`);
  };
  $("#look").onclick = look;
  $("#who").onkeydown = e => { if (e.key === "Enter") look(); };
  if (user) look();
  else Coach.react("maya", "explain", "Playing someone soon? Type their chess.com name and I'll show you how they play.");
}

// ---------- the report for a human coach, and Knightwise Wrapped (1.0): coach/report.py ----------
// The week (or month) in facts: to read, to print or save as a PDF for a coach, or to play as cards, one at a time.
async function reportView(arg) {
  const days = arg === "month" ? 30 : 7;
  shell("progress", `<p class="muted">Putting your ${days === 7 ? "week" : "month"} together…</p>`);
  const r = await api(`/api/report?days=${days}`);
  if (!r.player) return go("welcome");
  const res = r.results || {}, rt = r.rating || {}, pr = r.practice || {};
  const per = v => v == null ? "–" : v.toFixed(v < 1 && v > 0 ? 2 : 1);
  const change = (now, before, lowerIsBetter = true) => before == null ? "" : now === before ? `<span class="muted">same</span>`
    : `<span class="delta ${(now < before) === lowerIsBetter ? "good" : "bad"}">${now < before ? "▼" : "▲"} from ${per(before)}</span>`;
  $("#page").innerHTML = `
    <div class="page-head no-print"><div><a href="#/progress" class="small muted" style="text-decoration:none">← Progress</a>
      <h1 style="margin-top:6px">${esc(r.title)} in facts</h1>
      <p class="sub">For you, or for your chess coach: from your real chess.com games, checked by Stockfish, and your practice in Knightwise.</p></div>
      <div class="row"><a class="btn ${days === 7 ? "primary" : ""}" href="#/report/week">Week</a><a class="btn ${days === 30 ? "primary" : ""}" href="#/report/month">Month</a></div></div>
    <div class="row no-print" style="margin-bottom:14px"><button class="btn primary" id="wrapped">▶ Play it as Wrapped</button>
      <button class="btn" id="print">Print or save as PDF</button></div>
    <div class="report" id="report">
      <div class="report-head"><div><div class="label">Knightwise report</div><h2 style="margin:2px 0 0">${esc(r.player)} · ${esc(r.title)}</h2>
        <div class="small muted">${esc(r.from)} to ${esc(r.to)}</div></div></div>
      <div class="box stack report-sum">${r.lines.map(l => `<p style="margin:0">${esc(l)}</p>`).join("")}</div>
      <div class="report-grid">
        <div class="box stack"><div class="label">Games</div>
          <div class="row"><b class="big">${r.games}</b><span class="small">${res.win || 0} won · ${res.draw || 0} drawn · ${res.loss || 0} lost</span></div>
          ${rt.from ? `<div class="small">Rating ${rt.from} → ${rt.to} <span class="delta ${rt.to >= rt.from ? "good" : "bad"}">${rt.to - rt.from >= 0 ? "+" : ""}${rt.to - rt.from}</span></div>` : ""}
          <div class="small muted">${Object.entries(r.kinds || {}).map(([k, n]) => `${n} ${esc(k)}`).join(" · ")}</div></div>
        <div class="box stack"><div class="label">Mistakes a game</div>
          <div class="small"><b>${per(r.pieces.now)}</b> pieces given away ${change(r.pieces.now, r.pieces.before)}</div>
          <div class="small"><b>${per(r.big)}</b> big mistakes (a game's three costliest)</div>
          ${r.clock && r.clock.lines.length ? r.clock.lines.map(l => `<div class="small muted">${esc(l)}</div>`).join("") : ""}</div>
        <div class="box stack"><div class="label">Practice in Knightwise</div>
          <div class="small"><b>${pr.days || 0}</b> day${pr.days === 1 ? "" : "s"} practised</div>
          <div class="small"><b>${pr.answers || 0}</b> positions, <b>${pr.right || 0}</b> right first time</div>
          <div class="small"><b>${r.lessons || 0}</b> lesson${r.lessons === 1 ? "" : "s"} studied</div></div>
      </div>
      ${r.habits.length ? `<div class="box stack"><div class="label">Habits, a game</div>
        <table class="report-table"><tr><th>What happens</th><th>Now</th><th>Before</th><th>The habit that fixes it</th></tr>
        ${r.habits.map(h => `<tr><td>${esc(h.pattern)}</td><td class="num">${per(h.now)}</td><td class="num">${per(h.before)}</td><td class="small">${esc(h.habit)}</td></tr>`).join("")}</table></div>` : ""}
      <div class="report-grid">
        ${r.best ? `<a class="box stack click" href="#/games/${r.best.id}" style="text-decoration:none;color:inherit"><div class="label">Best game</div>
          <b>vs ${esc(r.best.opponent)} <span class="chip ${r.best.result}">${r.best.result === "win" ? "W" : r.best.result === "loss" ? "L" : "D"}</span></b>
          <div class="small muted">${esc(r.best.date)} · ${r.best.moments ? `${r.best.moments} big mistake${r.best.moments > 1 ? "s" : ""}` : "no big mistakes"}</div></a>` : ""}
        ${r.worst ? `<a class="box stack click" href="#/games/${r.worst.id}" style="text-decoration:none;color:inherit"><div class="label">The costliest move</div>
          <b>Move ${r.worst.move_number}: ${esc(r.worst.move)}, against ${esc(r.worst.opponent)}</b>
          <div class="small">Better was <b>${esc(r.worst.best)}</b>. ${esc(cap(r.worst.pattern || ""))}.</div></a>` : ""}
        <div class="box stack"><div class="label">Next</div>
          ${r.next.habit ? `<div class="small">${esc(r.next.habit)}</div>` : ""}
          ${r.next.lesson ? `<div class="small muted">Next lesson: ${esc(r.next.lesson)}</div>` : ""}</div>
      </div>
      <p class="small muted report-foot">Made with Knightwise, a free chess coach. Every number is from real games checked by Stockfish; nothing is estimated.</p>
    </div>`;
  $("#print").onclick = () => window.print();
  $("#wrapped").onclick = () => wrapped(r);
  Coach.react("viktor", "explain", r.lines.slice(0, 2).join(" "));
}

// Wrapped: the same facts as big cards, one at a time, with Viktor saying each. Click, or the arrow keys, to move on.
function wrapped(r) {
  const res = r.results || {}, rt = r.rating || {}, pr = r.practice || {};
  const cards = [
    [r.title, `${esc(r.from)} to ${esc(r.to)}`, `${r.title}, ${r.player}. Let's look at it.`],
    [`${r.games}`, `game${r.games === 1 ? "" : "s"} played`, `${r.games} games.`],
    [`${res.win || 0}`, `won · ${res.draw || 0} drawn · ${res.loss || 0} lost`, `${res.win || 0} of them won.`],
  ];
  if (rt.from && rt.to !== rt.from) cards.push([`${rt.to - rt.from > 0 ? "+" : ""}${rt.to - rt.from}`, `rating: ${rt.from} to ${rt.to}`, `Your rating went from ${rt.from} to ${rt.to}.`]);
  if (r.pieces.before != null) cards.push([`${r.pieces.now}`, `pieces given away a game, ${r.pieces.now < r.pieces.before ? "down" : r.pieces.now > r.pieces.before ? "up" : "the same"} from ${r.pieces.before}`,
    r.pieces.now < r.pieces.before ? "Fewer pieces given away. That is the habit working." : "Pieces given away: that's our work for next time."]);
  if (r.best) cards.push([`vs ${esc(r.best.opponent)}`, `your best game · ${esc(r.best.date)}`, `Your best game: against ${r.best.opponent}.`]);
  if (pr.answers) cards.push([`${pr.days}`, `day${pr.days === 1 ? "" : "s"} of practice · ${pr.answers} positions`, `You practised on ${pr.days} days.`]);
  if (r.habits.length) cards.push([esc(r.habits[0].pattern), "the habit that costs you most", `The habit that costs most: ${r.habits[0].pattern}.`]);
  if (r.next.habit) cards.push(["Next", esc(r.next.habit), r.next.habit]);
  if (r.days > 7 && r.results && r.results.win) cards.push(["▶", "Your game of the month, as a film", "And now, your game of the month.", "film/month"]);
  const layer = document.createElement("div");
  layer.className = "wrapped";
  Coach.hide();  // nothing in front of the cards
  let song = null;
  if (Sound.on) {  // the sounds switch in Settings covers the music too
    const n = (Number(remember("kw-wrapped-song") || -1) + 1) % WRAPPED_SONGS.length, x = WRAPPED_SONGS[n];
    remember("kw-wrapped-song", String(n));
    song = new Audio(x.url); song.loop = true; song.volume = 0;
    song.currentTime = Math.max(0, x.peak - 6);  // the build-up's last seconds, then the main part
    song.play().catch(() => {});
    const up = setInterval(() => { if (!song || song.volume >= 0.22) return clearInterval(up); song.volume = Math.min(0.22, song.volume + 0.02); }, 120);
  }
  document.body.appendChild(layer);
  let k = 0;
  function show() {
    const [big, small, say] = cards[k];
    layer.innerHTML = `<div class="wrapped-card rise"><div class="wrapped-big">${big}</div><div class="wrapped-small">${small}</div></div>
      <div class="wrapped-dots">${cards.map((_, n) => `<i class="${n === k ? "on" : ""}"></i>`).join("")}</div>
      <button class="wrapped-x" title="Close">✕</button><div class="wrapped-foot">Knightwise Wrapped · click to go on</div>`;
    layer.querySelector(".wrapped-x").onclick = e => { e.stopPropagation(); close(); };
    Voice.speak(say, false, COACHES.viktor.voice);
  }
  function close() {
    Voice.stop(); layer.remove(); removeEventListener("keydown", keys);
    const s = song; song = null;
    if (s) { const down = setInterval(() => { s.volume = Math.max(0, s.volume - 0.03); if (!s.volume) { s.pause(); clearInterval(down); } }, 80); }
  }
  function next(step = 1) {
    if (step > 0 && cards[k][3]) { const to = cards[k][3]; close(); return go(to); }  // the last card opens the film
    k += step; if (k >= cards.length) { confetti(50); return close(); } if (k < 0) k = 0; show();
  }
  const keys = e => { if (e.key === "Escape") close(); if (e.key === "ArrowRight" || e.key === " ") next(); if (e.key === "ArrowLeft") next(-1); };
  layer.onclick = () => next();
  addEventListener("keydown", keys);
  show();
}

// ---------- your game as a short 3D film (1.0): coach/film.py writes it, coach/ui/film.js plays it ----------
// The film's songs, picked by the owner by ear (20 Oct), all CC BY 3.0, credited in Settings. peak: the second
// the song's main part starts (measured from its loudness, 20 Oct), so the film can bring it in on the first
// winning move. A different song each time: the next one in the list, remembered.
const FILM_SONGS = [
  { url: "/ui/vendor/film/time-has-come.mp3", name: "Time has come, by Reiswerk feat. SackJo22", peak: 19 },
  { url: "/ui/vendor/film/jalandhar.mp3", name: "Jalandhar, by Kevin MacLeod", peak: 83 },
  { url: "/ui/vendor/film/vadodora-chill-mix.mp3", name: "Vadodora Chill Mix, by Kevin MacLeod", peak: 37 },
];
// Wrapped's songs: livelier, started a little before their main part, under Viktor's voice
const WRAPPED_SONGS = [
  { url: "/ui/vendor/film/trio-cultural-mix.mp3", peak: 31 },
  { url: "/ui/vendor/film/vadodora-chill-mix.mp3", peak: 37 },
];
async function filmView(id) {
  shell("progress", `<p class="muted">Setting up the film…</p>`);
  let s;
  try { s = await api(`/api/film/${encodeURIComponent(id || "month")}`); }
  catch (e) { $("#page").innerHTML = `<div class="empty">No win to film yet this month. Win a game and it's here.</div>`; return; }
  const songs = [];
  for (const x of FILM_SONGS) if (await fetch(x.url, { method: "HEAD" }).then(r => r.ok).catch(() => false)) songs.push(x);
  // a different song each time: the next one in the list (20 Oct, the owner: rotated, no choosing)
  const pick = songs.length ? (Number(remember("kw-film-song") || -1) + 1) % songs.length : -1;
  let musicOn = songs.length > 0 && remember("kw-film-music") !== "off", stop = null;
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/progress" class="small muted" style="text-decoration:none">← Progress</a>
      <h1 style="margin-top:6px">${esc(s.title)}</h1>
      <p class="sub">Against ${esc(s.opponent)}, ${esc(s.date)}</p></div></div>
    <div class="film-wrap" id="film"></div>
    <div class="row film-controls"><button class="btn primary" id="filmgo">▶ Play</button>
      <button class="btn" id="filmsave">Save as a video</button>
      ${songs.length ? `<button class="btn ghost" id="filmmusic" title="Music on or off">${musicOn ? "♪ On" : "♪ Off"}</button>` : ""}
      <span class="small muted" id="filmmsg"></span></div>`;
  const ready = () => window.Film ? Promise.resolve() : new Promise(r => window.addEventListener("film-ready", r, { once: true }));
  const song = () => (musicOn && pick >= 0 ? songs[pick] : null);
  const go = $("#filmgo");
  const started = () => { remember("kw-film-song", String(pick)); Voice.stop(); Coach.hide(); };  // nothing in front of the film
  async function mount(autoplay, record) {  // the film: a still preview first, or playing (and recording)
    await ready();
    if (stop) stop();
    window.kwFilm = stop = window.Film.play($("#film"), s, { record, autoplay, music: song(), onEnd: async r => {
      go.textContent = "▶ Play again"; go.dataset.state = "ended"; $("#filmsave").disabled = false;
      if (r.error) { $("#filmmsg").textContent = r.error; return; }
      if (!r.video) return;
      $("#filmmsg").textContent = "Saving…";
      try {
        const res = await fetch(`/api/film/save?game=${encodeURIComponent(s.id)}`, { method: "POST", headers: { "Content-Type": "video/webm" }, body: r.video });
        const j = await res.json();
        $("#filmmsg").textContent = res.ok ? `Saved in Videos\\Knightwise` : (j.message || "Couldn't save it.");
      } catch (e) { $("#filmmsg").textContent = "Couldn't save it."; }
    } });
    if (autoplay) started();
    go.textContent = autoplay ? "❚❚ Pause" : "▶ Play"; go.dataset.state = autoplay ? "playing" : "preview";
    $("#filmsave").disabled = !!record;
    $("#filmmsg").textContent = record ? "Recording. Let it play to the end." : "";
  }
  go.onclick = () => {  // one button: play, pause, carry on, play again
    const st = go.dataset.state;
    if (st === "preview") { stop.resume(); started(); go.textContent = "❚❚ Pause"; go.dataset.state = "playing"; }
    else if (st === "playing") { stop.pause(); go.textContent = "▶ Carry on"; go.dataset.state = "paused"; }
    else if (st === "paused") { stop.resume(); go.textContent = "❚❚ Pause"; go.dataset.state = "playing"; }
    else mount(true, false);
  };
  $("#film").onclick = () => go.click();  // the picture itself plays and pauses too
  $("#filmsave").onclick = () => mount(true, true);
  const mb = $("#filmmusic");
  if (mb) mb.onclick = () => {
    musicOn = !musicOn; remember("kw-film-music", musicOn ? "on" : "off"); mb.textContent = musicOn ? "♪ On" : "♪ Off";
    if (go.dataset.state === "preview" || go.dataset.state === "ended") mount(false, false);
    else if (stop) { stop(); mount(false, false); }  // it starts again from the preview, with or without music
  };
  window.addEventListener("hashchange", () => { if (stop) stop(); stop = null; }, { once: true });
  mount(false, false);  // the preview: the board and the title, waiting
}

// ---------- blindfold by voice: follow one of your games in your head (1.0) ----------
// Maya reads out the first moves of one of your own games; the board stays empty. Then one question, answered by
// clicking a square (or saying it, with an AI key). Right: the next one is a move longer. With the voice off, the
// moves show one at a time instead, then disappear.
const each = plies => { const n = Math.ceil(plies / 2); return `${n} move${n === 1 ? "" : "s"} each`; };
async function blindfoldView() {
  shell("level", `<p class="muted">Finding one of your games…</p>`);
  let x;
  try { x = await api("/api/blindfold"); } catch (e) { $("#page").innerHTML = `<div class="empty">${esc(e.message)}</div>`; return; }
  let ready = false, done = false, peeked = false, reading = 0;
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/level" class="small muted" style="text-decoration:none">← Your level</a>
      <h1 style="margin-top:6px">Blindfold</h1>
      <p class="sub">Maya reads out the start of one of your games. Follow it in your head: the board stays empty. Then answer on the board.
        Each right answer makes the next one a move longer.</p></div>
      <span class="muted num">${each(x.plies)}${x.best ? ` · your record: ${each(x.best)}` : ""}</span></div>
    <div class="game-layout">
      <div><div class="board-wrap" id="board"></div></div>
      <div class="stack">
        <div class="box stack" style="padding:16px"><div class="label">Your game against ${esc(x.game.opponent || "an opponent")}</div>
          <div id="bfmoves" class="small" style="min-height:44px"></div>
          <div class="row"><button class="btn primary" id="bfplay">${Voice.on ? "Listen" : "Show the moves"}</button>
            <button class="btn" id="bfpeek" hidden>Show the moves</button></div></div>
        <div class="box stack" style="padding:16px" id="bfq" hidden><h3 style="margin:0" id="bfask"></h3>
          <div class="row">${TALK ? `<button class="btn" id="bfsay">Say the square</button>` : ""}<span class="small muted" id="bfheard"></span></div>
          <div class="small" id="bfmsg"></div>
          <div class="row"><button class="btn primary" id="bfnext" hidden>Next →</button></div></div>
      </div>
    </div>`;
  const board = (opts = {}) => Board.render($("#board"), { ...(opts.fen ? { fen: opts.fen } : { pieces: {} }), highlights: opts.hl || {}, onClick: answer });
  board();
  function ask() {
    ready = true;
    $("#bfq").hidden = false; $("#bfask").textContent = x.question;
    $("#bfpeek").hidden = false;
    Coach.react("maya", "listen", x.question);
  }
  async function play() {
    const mine = ++reading;
    $("#bfplay").disabled = true;
    if (Voice.on) {
      $("#bfmoves").innerHTML = `<span class="muted">Listening… ${x.plies} half-moves.</span>`;
      await Voice.speak(x.say, false, COACHES.maya.voice);
    } else {  // no voice: one move at a time, then gone
      for (let k = 0; k < x.moves.length && mine === reading; k++) {
        $("#bfmoves").innerHTML = `<span class="num">${Math.floor(k / 2) + 1}${k % 2 ? "…" : "."} <b>${esc(x.moves[k])}</b></span>`;
        await wait(1300);
      }
      $("#bfmoves").innerHTML = `<span class="muted">That's all of it. Now picture the board.</span>`;
    }
    if (mine !== reading) return;
    $("#bfplay").disabled = false; $("#bfplay").textContent = Voice.on ? "Hear it again" : "Show them again";
    if (!ready) ask();
  }
  function peek() {
    peeked = true;
    $("#bfmoves").innerHTML = x.moves.map((m, k) => `${k % 2 ? "" : `<span class="muted">${k / 2 + 1}.</span> `}${esc(m)}`).join(" ");
    $("#bfpeek").hidden = true;
  }
  async function answer(sq) {
    if (!ready || done) return;
    done = true; reading++; Voice.stop();
    const looked = peeked;  // read the moves before answering: no longer move for it
    const right = x.answers.includes(sq);
    const hl = Object.fromEntries(x.answers.map(a => [a, "hl-ok"]));
    if (!right) hl[sq] = "hl-no";
    board({ fen: x.fen, hl });
    peek();
    Sound.play(right ? "right" : "wrong", 0.6);
    const r = await api("/api/blindfold/done", { right, peeked: looked }).catch(() => ({}));
    const more = r.plies ? ` Next one: ${each(r.plies)}.` : "";
    const where = x.answers.length > 1 ? `The answers: ${x.answers.join(", ")}.` : `It's on ${x.answers[0]}.`;
    $("#bfmsg").innerHTML = right ? `<span class="ok-text"><b>Right.</b> You saw it without the board.</span>${esc(more)}`
      : `<span class="bad-text">Not ${esc(sq)}.</span> ${esc(where)}${esc(more)}`;
    if (r.record) confetti(40);
    $("#bfnext").hidden = false;
    Coach.react("maya", right ? "celebrate" : "encourage", right ? `Right, without seeing a thing.${r.record ? " That's your record." : ""}${more}`
      : `${where} This is hard for everyone at first: it gets easier every day.${more}`);
  }
  $("#bfplay").onclick = play;
  $("#bfpeek").onclick = peek;
  $("#bfnext").onclick = () => blindfoldView();
  const say = $("#bfsay");
  if (say) say.onclick = async () => {
    if (!ready || done) return;
    say.disabled = true; $("#bfheard").textContent = "Listening…";
    try {
      const text = await Mic.listen({ wait: 6000 });
      if (!text) { $("#bfheard").textContent = "I didn't hear a square. Say it again, or click it."; return; }
      const r = await api("/api/blindfold/heard", { text });
      if (r.square) { $("#bfheard").textContent = `"${text}": ${r.square}`; answer(r.square); }
      else $("#bfheard").textContent = `"${text}": which square was that? Click it.`;
    } catch (e) { $("#bfheard").textContent = e.message || "The microphone isn't available. Click the square."; }
    finally { say.disabled = false; }
  };
  Coach.react("maya", "explain", "Blindfold. I'll read out the start of one of your games. Keep the board in your head: no pieces to look at.");
}

// ---------- Guess the human move: the weekly challenge (1.0) ----------
// Five real positions from strong players' games, the same all week. What would a player of this rating play? The
// human-move model says how many of them play each move; your guess scores by that. Then the three most played
// moves, and what the engine prefers: where people and the engine differ is the lesson.
async function guessView() {
  shell("level", `<p class="muted">Setting up this week's challenge…</p>`);
  const c = await api("/api/guess");
  if (!c.positions.length) {
    $("#page").innerHTML = `<div class="empty">The weekly challenge needs the human-move model. Switch on "Human-like opponents" in Settings.</div>`;
    return;
  }
  let i = 0, picked = null, total = 0, answered = false;
  const scores = [];
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/level" class="small muted" style="text-decoration:none">← Your level</a>
      <h1 style="margin-top:6px">Guess the human move</h1>
      <p class="sub">This week's challenge: five positions from real games. What would a player of that rating play? The closer to what most of them play, the more points.
        ${c.best != null ? ` Your best this week: <b>${c.best}</b> of ${c.positions.length * 100}.` : ""}</p></div>
      <span class="muted num" id="gcount"></span></div>
    <div class="game-layout">
      <div><div class="board-wrap" id="board"></div></div>
      <div class="stack">
        <div class="box stack" style="padding:16px"><h3 style="margin:0" id="gtask"></h3>
          <p class="small muted" style="margin:0">Click a piece, then where it goes. Ratings here are online (Lichess) ratings.</p></div>
        <div class="box stack" style="padding:16px" id="gresult" hidden></div>
        <div class="row"><span class="num" id="gtotal"></span><button class="btn primary" id="gnext" hidden>Next →</button></div>
      </div>
    </div>`;
  const x = () => c.positions[i];
  const name = p => p.white ? "White" : "Black";
  function draw(extra = {}) {
    const p = x(), targets = picked ? p.legal.filter(u => u.startsWith(picked)).map(u => u.slice(2, 4)) : [];
    Board.render($("#board"), { fen: extra.fen || p.fen, flip: !p.white, targets: answered ? [] : targets, arrows: extra.arrows || [],
      highlights: { [p.last[0]]: "hl-last", [p.last[1]]: "hl-last", ...(picked ? { [picked]: "hl-pick" } : {}) }, onClick: click });
    $("#gcount").textContent = `${i + 1} of ${c.positions.length}`;
    $("#gtotal").textContent = `${total} points`;
  }
  function show() {
    picked = null; answered = false;
    $("#gtask").textContent = `${name(x())} to move. What would a ${x().rating.toLocaleString()} player play?`;
    $("#gresult").hidden = true; $("#gnext").hidden = true;
    draw();
  }
  function click(sq) {
    if (answered) return;
    const p = x();
    if (picked && picked !== sq) {
      const uci = p.legal.find(u => u.slice(0, 4) === picked + sq);
      if (uci) return guess(uci.length > 4 && p.legal.includes(picked + sq + "q") ? picked + sq + "q" : uci);
    }
    picked = picked === sq || !p.legal.some(u => u.startsWith(sq)) ? null : sq;
    draw();
  }
  function guess(uci) {
    const p = x();
    answered = true; picked = null;
    const pct = p.chances[uci] || 0, top = p.top[0];
    const pts = uci === top.uci ? 100 : Math.min(100, Math.round(100 * pct / (p.chances[top.uci] || top.pct || 1)));
    scores.push(pts); total += pts;
    const mine = p.top.find(t => t.uci === uci);
    const arrows = [{ from: uci.slice(0, 2), to: uci.slice(2, 4), kind: "mine", label: "Your guess" },
      ...(top.uci !== uci ? [{ from: top.uci.slice(0, 2), to: top.uci.slice(2, 4), kind: "real", label: "Most played" }] : [])];
    const eng = p.engine;
    const engLine = !eng ? "" : eng.uci === top.uci ? `The engine agrees: ${esc(eng.san)} is its best move too.`
      : `The engine prefers <b>${esc(eng.san)}</b>${p.chances[eng.uci] != null ? `, played by ${Math.round(p.chances[eng.uci])}% at this level` : ", which almost no one plays here"}: people and engines see different things.`;
    $("#gresult").innerHTML = `<div class="row spread"><h2 style="margin:0">${pts} points</h2><span class="small muted">${pct < 1 ? "almost no one plays it" : `${Math.round(pct)}% play your move`}</span></div>
      <div class="label">At ${p.rating.toLocaleString()}, players play</div>
      ${p.top.map(t => `<div class="small"><div class="row spread"><span><b>${esc(t.san)}</b>${t.uci === uci ? " · your guess" : ""}</span><span class="num">${t.pct}%</span></div>
        <div class="bar"><div style="width:${t.pct}%"></div></div></div>`).join("")}
      <p class="small" style="margin:6px 0 0">${engLine}</p>`;
    $("#gresult").hidden = false;
    $("#gnext").hidden = false;
    $("#gnext").textContent = i + 1 < c.positions.length ? "Next →" : "See your score";
    draw({ arrows });
    Sound.play(pts >= 60 ? "right" : "move", 0.6);
    const said = pts === 100 ? `Yes. ${top.san} is what most ${p.rating.toLocaleString()} players play here.`
      : mine ? `${mine.san} is a human move: ${mine.pct}% play it. The favourite is ${top.san}.`
      : `Few players at ${p.rating.toLocaleString()} play that. Most of them play ${top.san}.`;
    Coach.react("viktor", pts >= 60 ? "celebrate" : "explain", said);
  }
  $("#gnext").onclick = async () => {
    if (i + 1 < c.positions.length) { i++; return show(); }
    const r = await api("/api/guess/done", { total }).catch(() => ({ best: total, record: false }));
    if (r.record) { confetti(); Sound.play("done"); }
    $("#gresult").innerHTML = `<h2 style="margin:0">${total} of ${c.positions.length * 100}</h2>
      <p class="small" style="margin:6px 0 0">${scores.map((s, k) => `${k + 1}: ${s}`).join(" · ")}</p>
      <p class="small muted" style="margin:6px 0 0">${r.record ? "Your best this week." : `Your best this week: ${r.best}.`} The same five stay until Monday, then five new ones.</p>`;
    $("#gnext").hidden = true;
    Coach.react("viktor", r.record ? "celebrate" : "calm", r.record ? `${total} points: your best this week. Knowing what people play is how you predict your opponents.`
      : `${total} points. Your best is ${r.best}. Try again: now you know what people play.`, [{ label: "Try again", run: () => guessView() }]);
  };
  show();
  Coach.react("viktor", "explain", "A different kind of puzzle. Not the best move: the human move. Guess what most players of that rating play.");
}

// ---------- see it in your head: the calculation trainer (0.9) ----------
// The board stays still. You put in the whole line first, as arrows: your move, their answer, your next move.
// Only then is it checked and played out. Strong players don't move until they've seen the end.
async function calcView() {
  shell("level", `<p class="muted">Loading…</p>`);
  const items = await api("/api/calc");
  if (!items.length) { $("#page").innerHTML = `<div class="empty">The calculation puzzles appear once the puzzles are downloaded.</div>`; return; }
  let i = 0, line = [], picked = null, done = false;
  const firstTry = {};
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/level" class="small muted" style="text-decoration:none">← Your level</a>
      <h1 style="margin-top:6px">See it in your head</h1>
      <p class="sub">The board doesn't move. Put in the whole line as arrows first: your move, their best answer, your next move. Then check it.</p></div>
      <span class="muted num" id="calccount"></span></div>
    <div class="game-layout">
      <div><div class="board-wrap" id="board"></div><p class="small muted" id="calcwhere" style="margin-top:10px"></p></div>
      <div class="stack">
        <div class="box stack" style="padding:16px"><h3 style="margin:0" id="calctask"></h3><p class="small muted" style="margin:0" id="calchint"></p></div>
        <div class="box stack" style="padding:16px"><div class="label">Your line</div><div id="calcline" class="small"></div><div id="calcmsg" class="small"></div>
          <div class="row"><button class="btn" id="calcundo">Take back</button><button class="btn primary" id="calccheck">Check my line</button>
            <button class="btn" id="calcnext">Next →</button></div></div>
      </div>
    </div>`;
  const x = () => items[i];
  const need = () => x().steps.length * 2 - 1;  // your moves and their answers in between
  const yours = k => k % 2 === 0;
  function draw(pieces) {
    const arrows = line.map((u, k) => ({ from: u.slice(0, 2), to: u.slice(2, 4), kind: yours(k) ? "mine" : "real" }));
    const hl = { ...(x().last ? { [x().last[0]]: "hl-last", [x().last[1]]: "hl-last" } : {}), ...(picked ? { [picked]: "hl-pick" } : {}) };
    Board.render($("#board"), { pieces: pieces || x().steps[0].board, flip: x().flip, highlights: hl, arrows: done ? [] : arrows, onClick: click });
    $("#calcline").innerHTML = line.length ? line.map((u, k) => `${yours(k) ? "You" : "They"}: ${u.slice(0, 2)}→${u.slice(2, 4)}`).join(" · ")
      : `<span class="muted">Click a piece, then where it goes. ${need()} moves in all: yours, theirs${need() > 3 ? ", yours, theirs" : ""}, yours.</span>`;
    $("#calccount").textContent = `${i + 1} of ${items.length}`;
  }
  function show() {
    line = []; picked = null; done = false;
    $("#calctask").textContent = x().intro;
    $("#calchint").textContent = `${x().steps.length} moves of yours to find. ${x().hint}`;
    $("#calcwhere").textContent = x().where || "";
    $("#calcmsg").innerHTML = "";
    draw();
  }
  function click(sq) {
    if (done) return;
    if (!picked) { picked = sq; return draw(); }
    if (picked === sq) { picked = null; return draw(); }
    if (line.length < need()) line.push(picked + sq);
    picked = null; draw();
  }
  async function check() {
    if (done || line.length < need()) { $("#calcmsg").innerHTML = `<span class="muted">The line needs ${need()} moves; you have ${line.length}.</span>`; return; }
    done = true;
    const steps = x().steps;
    let wrong = -1;
    for (let k = 0; k < line.length && wrong < 0; k++) {
      const st = steps[Math.floor(k / 2)];
      const ok = yours(k) ? Object.entries(st.moves).some(([u, m]) => m.good && u.slice(0, 4) === line[k])
        : st.reply && st.reply.uci.slice(0, 4) === line[k];
      if (!ok) wrong = k;
    }
    const right = wrong < 0;
    if (!(x().id in firstTry)) { firstTry[x().id] = right; api("/api/practice", { id: x().id, kind: "puzzle", right }).catch(() => {}); }
    // play the real line out, so you see what was in it
    for (let s = 0; s < steps.length; s++) {
      const good = Object.entries(steps[s].moves).find(([, m]) => m.good);
      if (good && good[1].after) { Board.render($("#board"), { pieces: good[1].after, flip: x().flip }); Sound.move(good[1].san); await wait(650); }
      if (steps[s].reply) { Board.render($("#board"), { pieces: steps[s].reply.board, flip: x().flip }); Sound.move(steps[s].reply.san); await wait(650); }
    }
    const real = steps.flatMap(st => [Object.values(st.moves).find(m => m.good).san, st.reply ? st.reply.san : null]).filter(Boolean).join(", ");
    if (right) Sound.play("right");  // no confetti for each line: it stays rare (1.0 design rule)
    const where = wrong < 0 ? "" : yours(wrong) ? `Your move ${Math.floor(wrong / 2) + 1} wasn't the one.` : `You didn't see their answer: it's not what you expected.`;
    $("#calcmsg").innerHTML = right ? `<span class="ok-text"><b>You saw it all.</b> ${esc(real)}.</span>`
      : `<span class="bad-text">${esc(where)}</span> The line: ${esc(real)}.`;
    Coach.react("viktor", right ? "celebrate" : "explain", right ? "You saw it all before moving. That's calculation." : `${where} The line was ${real}. Try the next one: see the end first.`);
  }
  $("#calcundo").onclick = () => { if (!done && line.length) { line.pop(); draw(); } };
  $("#calccheck").onclick = check;
  $("#calcnext").onclick = () => { if (i + 1 < items.length) { i++; show(); } else Coach.react("viktor", "celebrate", `All ${items.length} done: ${Object.values(firstTry).filter(Boolean).length} seen all the way first time.`); };
  show();
  Coach.react("viktor", "explain", "Don't move yet. See the whole line in your head first: your move, their best answer, your next. Then check.");
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
    <div class="page-head"><div><h1>Progress</h1><p class="sub">From your real chess.com games, checked by Stockfish.</p></div>
      <div class="row"><a class="btn" href="#/report/week">Report for your coach</a><a class="btn" href="#/film/month">▶ Your game of the month</a>
        <a class="btn primary" href="#/report/month">▶ Your month, Wrapped</a></div></div>
    <div class="grid">
      ${s ? `<div class="box story rise" id="story">
        <div class="story-head"><div><div class="label">${esc(s.title)}</div><div class="small muted">${esc(s.from)} to ${esc(s.to)}</div></div>
          <button class="btn" id="sharepic">Share</button></div>
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
            <div class="small muted">${s.best.moments ? `${s.best.moments} big mistake${s.best.moments > 1 ? "s" : ""}` : "No big mistakes"} · ${esc(s.best.date)}</div>
</a>` : ""}
        </div>
        ${s.next ? `<div class="story-next"><span class="label">Next week's one thing</span><div>${esc(s.next.habit)}</div></div>` : ""}
      </div>` : `<div class="empty">Your story appears after your first checked games.</div>`}
      ${p.clock && p.clock.lines.length ? `<div class="box rise stack" style="padding:16px"><h2 style="margin:0">Your clock</h2>
        <p class="small muted" style="margin:0">Your last ${p.clock.games} games with a clock, from the time chess.com records on every move.</p>
        ${p.clock.lines.map(l => `<p style="margin:0">${esc(l)}</p>`).join("")}
        ${p.clock.big && p.clock.fast / p.clock.big >= 0.3 ? `<p class="small" style="margin:0"><b>Try this:</b> when they capture or give check, count to five before you answer.</p>` : ""}
        ${p.clock.fast ? `<div><a class="btn" href="#/clockdrill">Slow-down drill: your rushed moves</a></div>` : ""}</div>` : ""}
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

// what to say about your last game: never "0 key moments", and a game left after 2 moves isn't "a clean game" (19 Oct)
function lastGameWords(last, who) {
  if (last.moments) return `${who} ${last.moments} key moment${last.moments === 1 ? "" : "s"} to look at.`;
  if (last.moves && last.moves < 10) return last.result === "win" && last.how === "abandoned"
    ? `they left after ${last.moves} move${last.moves === 1 ? "" : "s"}, so there's nothing to learn from it.`
    : `it ended after ${last.moves} move${last.moves === 1 ? "" : "s"}, too short to learn from.`;
  return "there was nothing big to fix.";
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
      <div class="row"><button class="btn" id="brief" title="Maya says your focus in three sentences">▶ Hear it from Maya</button></div></div>
    <div class="grid">
      ${dailyCard(h.daily || {})}
      ${f ? `<div class="box focus hero rise">
        <div class="hero-main"><div class="label">Your focus</div>
          <h3 class="hero-title">${esc(PATTERN_TITLE[f.pattern] || cap(f.pattern))}</h3>
          <p class="hero-habit">${esc(f.habit)}</p>
          <div class="row"><a class="btn ${(h.daily || {}).done_today ? "primary" : ""}" href="#/practice/${encodeURIComponent(f.pattern)}">Practise this</a>
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
          <p class="sub">${cap(lastGameWords(last, "Maya found"))}</p></div>
        <a class="btn" href="#/games/${last.id}">Review game</a></div>` : ""}
      <div class="box rise"><h2>Ask the coach</h2><div id="askbox"></div></div>
    </div>`;
  countUp($("#page"));
  // three sentences, not six (13 Oct test, point 1: "is it needed?"): your focus, the habit, your last game
  const briefing = [`${hello}, ${h.player}.`,
    f ? `Your focus is to ${(PATTERN_TITLE[f.pattern] || f.pattern).toLowerCase()}: ${f.times} times in ${f.games} games.` : "",
    f ? f.habit : "",
    last ? `In your last game, against ${last.opponent}, ${lastGameWords(last, "I found")}` : ""].join(" ");
  $("#brief").onclick = () => Voice.speak(briefing, true, COACHES.maya.voice);  // Home is Maya's
  api("/api/settings").then(cfg => askBox($("#askbox"), { placeholder: "How do I stop leaving pieces hanging?", coach: "maya",
    enabled: Object.values(cfg.slots).some(x => x.set), listen: cfg.talk_ready,
    onAsk: async q => {  // the same brain as Talk (19 Oct): typing "open my last review" opens it
      const r = await api("/api/talk", { coach: "maya", text: q, history: [], where: { section: "home" } });
      if (r.action && r.action.route) setTimeout(() => go(r.action.route), 1200);
      return r;
    } }));
}

// ---------- games ----------
async function games() {
  shell("games", `<p class="muted">Loading…</p>`);
  const list = await api("/api/games");
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>Games</h1><p class="sub">${list.length} finished games from chess.com. Click one to see its key moments.</p></div>
      <div class="row"><a class="btn" href="#/prep">Prep for an opponent</a><a class="btn" href="#/openings">Your opening tree</a></div></div>
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
  // nothing shows or talks until you start (22 Oct test): then ◀ ▶ walk the review, and Maya says every step
  let ply = 0, mode = null;
  const said = g.narration || [];
  const END = { checkmated: "checkmated.", resigned: "resigned.", timeout: "ran out of time.", abandoned: "left the game.",
    stalemate: "Stalemate: a draw.", agreed: "A draw by agreement.", repetition: "A draw by repetition.",
    insufficient: "A draw: not enough pieces to mate.", timevsinsufficient: "A draw: time ran out, but no mate was possible.",
    "50move": "A draw by the 50-move rule." };
  const ending = () => {  // how the game ended, said on its last move
    const h = END[g.how] || "";
    if (!h || h[0] === h[0].toUpperCase()) return h;
    if (g.how === "checkmated") return g.result === "win" ? "You won by checkmate." : "Checkmate: they won.";
    return `${g.result === "win" ? g.opponent : "You"} ${h}`;
  };
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/games" class="small muted" style="text-decoration:none">← Games</a>
      <h1 style="margin-top:6px">vs ${esc(g.opponent)} <span class="faint num">${g.opponent_rating}</span></h1>
      <p class="sub">${cap(g.result)} · ${esc(g.date)} · ${esc(g.time_class)} · you were ${g.color}${g.opening ? " · " + esc(g.opening) : ""}</p></div>
      <div class="row">${g.result === "win" && g.positions.length > 20 ? `<a class="btn" href="#/film/${g.id}">▶ Watch it as a film</a>` : ""}
        <a class="btn" href="${esc(g.url)}" target="_blank" rel="noopener">Open on chess.com ↗</a></div></div>
    <div class="game-layout">
      <div><div class="board-wrap" id="board"></div>
        <div class="controls"><button class="btn" data-go="0">⏮</button><button class="btn" data-go="-1">◀</button>
          <button class="btn" data-go="1">▶</button><button class="btn" data-go="end">⏭</button></div>
        <div style="margin-top:12px">${Board.legend(["mine", "better", "real", "reply"])}</div></div>
      <div class="stack">
        <div class="box stack walk" id="walk"></div>
        ${g.clock && g.clock.lines.length ? `<div class="box stack clockbox" style="padding:14px"><h2 style="margin:0">Your clock</h2>
          ${g.clock.lines.map(l => `<p class="small" style="margin:0">${esc(l)}</p>`).join("")}
          <p class="small faint" style="margin:0">From the clock chess.com recorded on every move. Average: ${g.clock.average} s a move.</p></div>` : ""}
        <div class="box stack" style="padding:14px"><h2 style="margin:0">Ask the coach about this position</h2><div id="askbox"></div></div>
        <details class="box" style="padding:12px"><summary><b>All moves</b> <span class="small muted">click one to see the board there</span></summary>
          <div class="movelist" id="moves" style="margin-top:10px"></div></details>
      </div>
    </div>`;
  const stepPly = (k, st) => st.board === "before" ? k.ply - 1 : k.ply;
  const toArrows = list => list.map(([u, kind]) => ({ from: u.slice(0, 2), to: u.slice(2, 4), kind }));
  const momentAt = p => moments.findIndex(k => k.ply === p);
  let view = null;  // a key moment's step picked by hand: its board and arrows, until ◀ ▶ moves on
  function board() {
    const k = view ? moments[view[0]] : null, st = k ? k.steps[view[1]] : null, hl = {};
    const at = st ? stepPly(k, st) : ply, pos = g.positions[at];
    let arrows = st ? toArrows(st.arrows) : [];
    if (!st && ply > 0 && mode && said[ply - 1]) arrows = toArrows(said[ply - 1].arrows);
    else if (!st && pos.uci) { hl[pos.uci.slice(0, 2)] = "hl-last"; hl[pos.uci.slice(2, 4)] = "hl-last"; }
    Board.render($("#board"), { fen: pos.fen, flip, highlights: hl, arrows });
    let html = "";
    for (let i = 1; i < g.positions.length; i += 2) {
      html += `<span class="n">${(i + 1) / 2}.</span>`;
      for (const j of [i, i + 1]) html += g.positions[j]
        ? `<span data-p="${j}" class="${j === ply ? "cur" : ""} ${keyPly.has(j) ? "key" : ""}">${esc(g.positions[j].san)}</span>` : "<span></span>";
    }
    $("#moves").innerHTML = html;
    $("#moves").querySelectorAll("span[data-p]").forEach(el => el.onclick = () => move(Number(el.dataset.p)));
  }
  // the key moments, always one click away while you go through the game
  const jumps = () => moments.length ? `<div class="row small" style="gap:6px;align-items:center"><span class="muted">Key moments:</span>
      ${moments.map((k, i) => `<button class="btn small-btn ${k.ply === ply ? "primary" : ""}" data-jump="${k.ply}" title="${esc(cap(k.pattern))}">Move ${k.move_number}</button>`).join("")}</div>` : "";
  function draw() {
    board();
    const w = $("#walk");
    if (!mode) {  // the start: what's in the game, and how to begin
      w.innerHTML = `<h2 style="margin:0">${moments.length ? `${moments.length} key moment${moments.length === 1 ? "" : "s"} in this game`
          : "No big mistakes in this game"}</h2>
        <p class="muted" style="margin:0">Maya goes through the game with you, move by move, and stops to explain the key moments. Use ◀ ▶ under the board.</p>
        <div class="row"><button class="btn primary" id="startreview">▶ Start review</button></div>${jumps()}`;
      $("#startreview").onclick = () => move(1);
      wire(w);
      return;
    }
    const m = said[ply - 1], last = ply === g.positions.length - 1, total = g.move_numbers[g.move_numbers.length - 1];
    const ki = momentAt(ply), k = moments[ki];
    w.innerHTML = `<div class="row spread"><h2 style="margin:0">${ply ? `Move ${g.move_numbers[ply - 1]} of ${total}` : "The start"}</h2>
        <span class="small faint">◀ ▶ under the board</span></div>
      <p style="margin:0">${ply && m ? esc(m.text) : "The starting position. Press ▶ for the first move."}</p>
      ${last && ending() ? `<p class="small" style="margin:0"><b>The end:</b> ${esc(ending())}</p>` : ""}
      ${k ? `<div class="box stack keycard" style="padding:12px">
        <div class="row spread"><span class="what">Key moment ${ki + 1} of ${moments.length} · ${esc(cap(k.pattern))}</span>
          <span class="small faint" title="How much of your chance to win this move cost">−${Math.round(k.loss)}% win chance</span></div>
        <ol class="steps">${k.steps.map((st, i) => `<li class="step ${view && view[0] === ki && view[1] === i ? "on" : ""}" data-s="${i}" title="Show this on the board">
          <span class="tag"><i style="background:${Board.KIND[st.kind].color}"></i>${esc(st.title)}${st.san ? ` <b>${esc(st.san)}</b>` : ""}</span>
          <div class="small">${esc(st.text)}</div></li>`).join("")}</ol>
        ${k.habit ? `<div class="small"><b>Habit:</b> ${esc(k.habit)}</div>` : ""}
        ${k.hard ? `<div class="small" title="From the human-move model"><b>How hard was it?</b> ${esc(k.hard)}</div>` : ""}
        ${k.humans ? `<div class="small" title="From the human-move model"><b>Real players:</b> ${esc(k.humans)}</div>` : ""}
        ${explained[k.ply] ? `<div class="coach-says">${esc(explained[k.ply])}</div>` : ""}
        <div class="row"><a class="btn primary" href="#/try/${g.id}/${k.ply}">Try it again</a>
          ${k.lesson ? `<a class="btn" href="#/course/${k.lesson.id}" title="The course lesson on this idea">Learn it: ${esc(k.lesson.title)}</a>` : ""}
          ${g.result !== "win" ? `<a class="btn" href="#/rematch/${g.id}/${k.ply}" title="Play the game on from here against the engine, at their level">Rematch from here</a>` : ""}
          ${aiReady && !explained[k.ply] ? `<button class="btn" data-explain="${k.ply}">Explain like a coach</button>` : ""}</div></div>` : ""}
      ${jumps()}${last ? `<div data-helpful></div>` : ""}`;
    helpful(w.querySelector("[data-helpful]"), `review ${g.id}`);
    wire(w);
    w.querySelectorAll("[data-s]").forEach(li => li.onclick = () => {  // one step of the moment on the board, said again
      const i = Number(li.dataset.s), st = k.steps[i];
      view = [ki, i]; draw();
      Coach.react("maya", st.kind === "mine" ? "worried" : "explain", st.text);
    });
    w.querySelectorAll("[data-explain]").forEach(b => b.onclick = async () => {
      b.disabled = true; b.textContent = "Thinking…";
      try {
        const r = await api("/api/explain", { game: g.id, ply: Number(b.dataset.explain) });
        explained[Number(b.dataset.explain)] = r.text; draw(); Coach.react("maya", "explain", r.text);
      } catch (err) { b.textContent = err.message.slice(0, 80); }
    });
  }
  function wire(w) { w.querySelectorAll("[data-jump]").forEach(b => b.onclick = () => move(Number(b.dataset.jump))); }
  // one move of the game (yours, then theirs): the board after it, and Maya's line about it; on a key moment she
  // explains it there and then. Going back says it again.
  function move(p, speak = true) {
    mode = "game"; view = null;
    ply = Math.max(0, Math.min(g.positions.length - 1, p));
    draw();
    const m = said[ply - 1], k = moments[momentAt(ply)];
    let text = !ply || !m ? "The starting position." : m.text;
    if (k) text += " " + k.steps.slice(2).map(st => st.text).join(" ");  // the line already says the better move: then their reply
    if (ply === g.positions.length - 1 && ending()) text += ` ${ending()}`;
    if (speak) Coach.react("maya", k || (m && m.kind === "bad") ? "worried" : m && (m.kind === "good" || m.kind === "slip") ? "pleased" : "explain", text);
    return text;
  }
  // ◀ ▶ (and Next / Back by voice): one move; returns what Maya says
  function step(d) {
    if (!mode) return move(1);
    if (ply + d > g.positions.length - 1) { const t = ending() || "That was the last move."; Coach.react("maya", "calm", t); return t; }
    return move(ply + d);
  }
  window.kwNextStep = () => location.hash.includes(`games/${g.id}`) ? step(1) : null;
  window.kwBackStep = () => location.hash.includes(`games/${g.id}`) ? step(-1) : null;
  askBox($("#askbox"), { placeholder: "Why is my bishop in danger here?", coach: "maya", enabled: aiReady, listen: cfg.talk_ready,
    onAsk: q => { const k = moments[momentAt(ply)]; return api("/api/ask", { question: q, fen: g.positions[ply].fen, game: g.id, ply: k ? k.ply : null }); } });
  document.querySelectorAll("[data-go]").forEach(b => b.onclick = () => {
    const v = b.dataset.go, was = ply;
    if (v === "1" || v === "-1") step(Number(v));
    else move(v === "0" ? 0 : g.positions.length - 1);
    if (ply === was + 1) Sound.move(g.positions[ply].san);
  });
  draw();
  // Maya says what's in the game and waits for you: nothing is walked through until you start
  const worst = moments.reduce((a, b) => (b.loss > (a ? a.loss : -1) ? b : a), null);
  if (worst) Coach.react("maya", "explain",
    `${moments.length} key moment${moments.length === 1 ? "" : "s"} in this game; move ${worst.move_number} cost you the most. ` +
    "Press Start review and we'll go through it move by move.",
    [{ label: "▶ Start review", run: () => move(1) }]);
  else Coach.react("maya", "celebrate", "No big mistakes in this game. Press Start review and we'll go through it move by move.",
    [{ label: "▶ Start review", run: () => move(1) }]);
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
          <div class="row"><span class="small ${s.talk_ready ? "ok-text" : "muted"}" id="listenstate">${s.talk_ready
            ? "Talking is on: press Talk on a coach and just speak. Your Groq or Gemini key hears you, in about half a second."
            : "Talking by voice needs a free Groq or Gemini key: add one below."}</span></div>
          ${s.heard ? `<details class="small muted" id="heard"><summary>What your coaches heard: ${s.heard} line${s.heard === 1 ? "" : "s"}, kept as text on this PC</summary>
            <p style="margin:6px 0">Never the sound, never sent anywhere. It lets the hearing learn the names you use. If a line is wrong, that's what the coach misheard.</p>
            <div data-lines class="stack" style="gap:2px"></div><button class="btn small-btn" id="forgetheard">Delete all of it</button></details>` : ""}
          ${!s.listen_ready ? `<details class="small muted"><summary>Hear me on this PC instead (optional)</summary>
            <p style="margin:6px 0">A one-time 485 MB download. It's slower and mishears more than the key does; use it only if you have no key.</p>
            <button class="btn" id="getlisten">Install listening on this PC</button></details>` : ""}</div></div>
      <div class="settings-row"><div><h3>Sounds</h3><p class="note">Moves, right and wrong answers, a finished set. No background music.</p></div>
        <div class="row"><button class="switch ${s.sounds ? "on" : ""}" id="sounds" aria-label="Sounds"></button>
          <span class="small muted">${s.sounds ? "On" : "Off"}</span></div></div>
      ${s.human_ready ? `<div class="settings-row"><div><h3>Human-like opponents</h3><p class="note">The human-move model plays like real players of any rating, mistakes included: it learned from millions of online games.
        Your rematch and sparring opponents play like people, and reviews say how many players at your level find a move. It's an estimate of a level, never a real person. It runs on this PC.</p></div>
        <div class="row"><button class="switch ${s.human_moves ? "on" : ""}" id="humanmoves" aria-label="Human-like opponents"></button>
          <span class="small muted">${s.human_moves ? "On" : "Off"}</span></div></div>` : ""}
      <div class="settings-row"><div><h3>AI: talk with your coaches</h3><p class="note">Optional. With a key, the coach explains moves in its own words and answers your questions.
        Without one it uses the engine's built-in sentences. Keys are kept in Windows Credential Manager, encrypted for your Windows account,
        and are only sent to the provider you choose.</p>
        <button class="btn" id="aicompare" style="margin-top:8px">What AI adds</button></div>
        <div class="grid">${slot("slot1", 1)}${slot("slot2", 2)}<p class="note">Key 2 is used when key 1 fails or runs out.</p>
          <details class="keyguide"><summary><b>How to get a free key</b> <span class="small muted">about 2 minutes, never shown to anyone else</span></summary>
            <p class="small"><b>Under 18?</b> Ask a parent or guardian to make the key with you: Groq's and Google's terms are for adults, or need a parent's permission.</p>
            <ol class="small">
              <li><b>Groq</b> (recommended, free, no card): press <b>Get a Groq key ↗</b> above. console.groq.com opens in your browser.</li>
              <li>Sign in with a Google account or an email address. It asks for no card and no payment.</li>
              <li>On the <b>API Keys</b> page, press <b>Create API Key</b>, give it a name such as Knightwise, and press <b>Submit</b>.</li>
              <li>Copy the key it shows (it starts with <b>gsk_</b>). It is shown only once.</li>
              <li>Come back here, paste it into Key 1, and press <b>Save key</b>, then <b>Test key</b>. A green line means it works.</li>
            </ol>
            <p class="small muted">For a second key, Google Gemini works the same way at aistudio.google.com: <b>Get API key</b>, then <b>Create API key</b>. Put it in Key 2.
              Keys stay in Windows Credential Manager on this PC, are sent only to the provider you picked, and never to Knightwise.</p>
          </details></div></div>
      <div class="settings-row"><div><h3>Arrows on chess.com</h3><p class="note">The browser extension.</p></div>
        <div class="row">${connectedIn(st)}</div></div>
      <div class="settings-row"><div><h3>chess.com check</h3><p class="note">chess.com changes its site now and then. Knightwise checks everything it uses there, each time.</p></div>
        <div>${healthRow(st.health)}</div></div>
      <div class="settings-row"><div><h3>Your data</h3><p class="note">Games, checks, practice and your logbook.</p></div>
        <div class="row"><button class="btn" id="folder">Open data folder</button></div></div>
      <div class="settings-row"><div><h3>About and credits</h3><p class="note">Free and open source. Fair play: never active in games against real people.</p></div>
        <div class="muted small">Knightwise ${esc((STATUS && STATUS.version) || "")} · open source, GPL-3.0 · <a href="https://github.com/Abhra71/ChessCoach" target="_blank" rel="noopener">GitHub ↗</a>
          <details style="margin-top:6px"><summary>Made with the work of others, all free</summary><ul style="margin:6px 0 0;padding-left:18px">
            <li><b>Stockfish 19</b>, the move checker: the Stockfish team, GPL-3.0</li>
            <li><b>The human-move model</b> is Maia-3, by the CSSLab at the University of Toronto, AGPL-3.0: run by Knightwise itself</li>
            <li><b>python-chess</b>: Niklas Fiekas, GPL-3.0</li>
            <li><b>Puzzles, opening names, the endgame tablebase and strong players' games</b>: Lichess and the Lichess Elite Database, CC0</li>
            <li><b>The voices</b>: Kokoro, Apache-2.0, on this PC. <b>Hearing</b>: Whisper (MIT) on Groq, or Google Gemini, with your own key</li>
            <li><b>The 3D chess set</b>: "Chess Set" by Riley Queen, Poly Haven, CC0. <b>3D</b>: Three.js, MIT</li>
            <li><b>Sounds</b>: Kenney, CC0. <b>Welcome music</b>: Satie, Gymnopédie No. 1, played by Michael Laucke, public domain</li>
            <li><b>The film's and Wrapped's music</b>, from ccMixter, CC BY 3.0: "Time has come" by Reiswerk feat. SackJo22 (with SackJo22 and Apoxode),
              and "A Trio Cultural Mix (instrumental)" by CSoul (samples by debbizo); and "Jalandhar" and "Vadodora Chill Mix" by
              Kevin MacLeod (incompetech.com), licensed under Creative Commons: By Attribution 4.0</li>
            <li><b>Your games</b>: chess.com's public API. Knightwise is independent and not connected with chess.com</li>
          </ul></details></div></div>
    </div>`;
  $("#theme").querySelectorAll("button").forEach(b => b.onclick = async () => {
    const r = await api("/api/settings", { theme: b.dataset.t }); applyTheme(r.theme); settingsView();
  });
  const hm = $("#humanmoves"); if (hm) hm.onclick = async () => { await api("/api/settings", { human_moves: !s.human_moves }); settingsView(); };
  $("#sounds").onclick = async () => { await api("/api/settings", { sounds: !s.sounds }); Sound.set(!s.sounds); if (!s.sounds) Sound.play("right"); settingsView(); };
  $("#voice").onclick = async () => { await api("/api/settings", { voice: !s.voice }); Voice.set(!s.voice); settingsView(); };
  const HELLO = { maya: "Hi, I'm Maya. I'll walk you through your games, one moment at a time.",
    viktor: "Viktor. I keep an eye on your progress. Slowly, but surely." };
  document.querySelectorAll("[data-hear]").forEach(b => b.onclick = () => Voice.speak(HELLO[b.dataset.hear], true, COACHES[b.dataset.hear].voice));
  $("#aicompare").onclick = () => AiCard.open();
  if ($("#heard")) {  // what was heard, newest first (flagship 6: the hearing learns from it, on this PC)
    $("#heard").addEventListener("toggle", async () => {
      if (!$("#heard").open) return;
      const h = await api("/api/heard");
      $("#heard [data-lines]").innerHTML = h.recent.map(x => `<div><span class="faint num">${esc(x.at)}</span> ${esc(x.text)}</div>`).join("");
    });
    $("#forgetheard").onclick = async () => { await api("/api/heard/forget", {}); settingsView(); };
  }
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
async function screen(name, arg) {
  if (name === "plan") return await planView(arg);
  if (name === "games" && arg) return await gameView(arg);
  if (name === "games") return await games();
  if (name === "practice") return await practice(arg && decodeURIComponent(arg));
  if (name === "daily") return await daily();
  if (name === "progress") return await progressView();
  if (name === "level") return await levelView();
  if (name === "course" && arg) return await courseLesson(decodeURIComponent(arg));
  if (name === "course") return await courseView();
  if (name === "endgames") return await endgamesView();
  if (name === "calc") return await calcView();
  if (name === "guess") return await guessView();
  if (name === "film") return await filmView(arg && decodeURIComponent(arg));
  if (name === "report") return await reportView(arg);
  if (name === "blindfold") return await blindfoldView();
  if (name === "repertoire" && arg) { shell("level", `<p class="muted">Loading…</p>`); return lessonView({ ...(await api(`/api/repertoire/${arg}`)), back: "repertoire" }); }
  if (name === "repertoire") return await repertoireView();
  if (name === "prep") return await prepView(arg && decodeURIComponent(arg));
  if (name === "feedback") { history.replaceState(null, "", "#/home"); setTimeout(feedbackBox, 400); return await home(); }  // from chess.com
  if (name === "clockdrill") { shell("level", `<p class="muted">Finding your rushed moves…</p>`); return lessonView({ ...(await api("/api/clockdrill")), back: "level" }); }
  if (name === "endgame") return await endgameView(arg);
  if (name === "lesson") return await themeLesson(decodeURIComponent(arg || ""));
  if (name === "openings") return await openingTree();
  if (name === "try") return await tryAgain(arg, location.hash.split("/")[3]);
  if (name === "rematch") return await rematchView(arg, location.hash.split("/")[3]);
  if (name === "spar") return await sparView(decodeURIComponent(arg || ""), location.hash.split("/")[3] === "black" ? "black" : "white");
  if (name === "extension") return await extensionView();
  if (name === "settings") return await settingsView();
  return await home();
}

// A beginner's introduction at the top of each section, until "Got it" (13 Oct test, point 23: every major
// section needs one). What it is, and what to do here, in two lines.
const INTRO = {
  home: ["Home", "Your coach's summary: the habit you're working on, your last game, and what to do next. Maya's pick has a green \"My pick\" label."],
  games: ["Games", "Every finished game from chess.com, checked by the engine. Click one: Maya goes through its key moments one at a time, and you can rematch the ones you lost."],
  practice: ["Practice", "Positions from your own games where you went wrong, then puzzles on the same habit. Find the best move: your first try is what counts. New positions come every day."],
  daily: ["Today's 5 minutes", "Three positions a day: one from your games, one puzzle on today's idea, and the first moves of your opening. Do it daily and your streak grows; one missed day is forgiven."],
  plan: ["Your plan", "Four things chosen for your habit: one opening, one tactic, one idea and one endgame. Viktor explains each one, then you practise it on the board."],
  level: ["Your level", "Five levels from beginner to 2,000+. Each skill is a number from your own games and a goal; finish every skill and you move up. The button next to a skill trains it."],
  course: ["Your course", "Lessons from beginner to 2,000+, one idea at a time. Your games choose the next one, and a lesson is done when that mistake drops in your games, not when you've read it."],
  progress: ["Progress", "Your week, your clock and your badges, all from your real games. Badges from chess.com games and from Knightwise practice are counted apart."],
  openings: null, settings: null, extension: null,
};
function intro(name) {
  const it = INTRO[name], page = $("#page");
  if (!it || !page || remember(`kw-intro-${name}`) === "seen" || page.querySelector(".intro")) return;
  const box = document.createElement("div");
  box.className = "box intro rise";
  box.innerHTML = `<div><b>${esc(it[0])}</b><p class="small" style="margin:4px 0 0">${esc(it[1])}</p></div>
    <button class="btn small-btn">Got it</button>`;
  box.querySelector("button").onclick = () => { remember(`kw-intro-${name}`, "seen"); box.remove(); };
  const head = page.querySelector(".page-head");
  if (head) head.after(box); else page.prepend(box);
}

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
    await screen(name, arg);
    if (!arg) intro(name || "home");
  } catch (e) {
    console.error(e);
    if ($("#page")) $("#page").innerHTML = `<div class="empty">Couldn't load this screen: ${esc(e.message)}</div>`;
  }
}
window.addEventListener("hashchange", () => { Voice.stop(); route(); });
api("/api/settings").then(s => {
  applyTheme(s.theme); Voice.set(s.voice && s.voice_ready); Sound.set(s.sounds !== false); TALK = !!s.talk_ready;
  const m = $("#mute"); if (m) m.textContent = Voice.on ? "Voice on" : "Voice off";  // drawn before the settings came (20 Oct)
}).catch(() => {});
api("/api/status").then(s => { STATUS = s; if (!s.player && !location.hash.includes("welcome")) go("welcome"); else route(); })
  .catch(() => route());
pollStatus();
