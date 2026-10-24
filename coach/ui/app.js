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
  sparkles: '<path d="M11 3l1.9 5.1L18 10l-5.1 1.9L11 17l-1.9-5.1L4 10l5.1-1.9z"/><path d="M19 14l.8 2.2 2.2.8-2.2.8L19 20l-.8-2.2L16 17l2.2-.8z"/>',
  message: '<path d="M4 5h16v11H9.5L4 20.5z"/>',
  sync: '<path d="M20 11a8 8 0 1 0-2.4 5.7"/><path d="M20 4.5V11h-6.5"/>',
  lock: '<rect x="5" y="11" width="14" height="9" rx="2"/><path d="M8 11V8a4 4 0 0 1 8 0v3"/>',
  clock: '<circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2.5M9.5 2.5h5"/>',
  barbell: '<path d="M2 12h2M20 12h2M7 12h10"/><rect x="4" y="8" width="3" height="8" rx="1"/><rect x="17" y="8" width="3" height="8" rx="1"/>',
  tree: '<circle cx="5" cy="12" r="2"/><circle cx="19" cy="5" r="2"/><circle cx="19" cy="12" r="2"/><circle cx="19" cy="19" r="2"/><path d="M7 12h10M7 11l10-5.5M7 13l10 5.5"/>',
  ear: '<path d="M7 9a5 5 0 0 1 10 0c0 3-3 4-3 7a3 3 0 0 1-6 0"/><path d="M10 9a2 2 0 0 1 4 0"/>',
  users: '<circle cx="9" cy="8" r="3"/><path d="M3 20a6 6 0 0 1 12 0"/><circle cx="17" cy="9" r="2.5"/><path d="M16 14a5 5 0 0 1 5 6"/>',
  search: '<circle cx="11" cy="11" r="6"/><path d="m20 20-4.5-4.5"/>',
  mic: '<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/>',
  send: '<path d="M4 12h15M13 6l6 6-6 6"/>',
  stop: '<rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor"/>',
  check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
  sound: '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4z"/><path d="M15.5 9a4 4 0 0 1 0 6M18 6.5a7.5 7.5 0 0 1 0 11"/>',
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
  const audio = (text, voice, slow) => fetch("/api/say", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, ...(voice ? { voice } : {}), ...(slow ? { slow: true } : {}) }) }).then(r => { if (!r.ok) throw new Error("voice"); return r.blob(); }).then(b => URL.createObjectURL(b));
  const play = url => new Promise(done => { const a = new Audio(url); playing = a; a.onended = a.onerror = done; a.play().catch(done); });
  function stop() { token++; if (playing) { playing.pause(); playing = null; } tell(false); }
  async function speak(text, force, voice, slow = false) {  // slow: the teaching pace (reviews, training, numbers)
    stop();
    if ((!on && !force) || !text) return;
    const mine = ++token, parts = split(text);
    let next = audio(parts[0], voice, slow);
    for (let i = 0; i < parts.length; i++) {
      let url;
      try { url = await next; } catch (e) { return; }
      if (mine !== token) return;
      if (i + 1 < parts.length) next = audio(parts[i + 1], voice, slow);
      tell(true);
      await play(url);
      if (mine !== token) return;
      if (i + 1 < parts.length) await wait(slow ? PAUSE + 250 : PAUSE);  // a breath between sentences, like a person (13 Oct: "too fast")
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
// the coach points: every link to that page glows, and the menu item it lives under; gone after a minute or on a
// click (23 Oct test: "a coach points at her suggestions by herself")
const NAV_OF = { prep: "train", openings: "train", repertoire: "train", spar: "train", calc: "train", blindfold: "train",
  guess: "train", endgames: "train", rematch: "games", daily: "home", report: "progress", clockdrill: "progress",
  extension: "settings" };
// The ring follows the way (23 Oct test): 10 s on each step if nothing happens; follow it (Games, then the game) and it
// moves to the next step; arrive and it's done; open something else and it goes at once.
let kwPointTimer = null, kwPointing = null;
function kwUnpoint() { clearTimeout(kwPointTimer); kwPointing = null; document.querySelectorAll(".kw-point").forEach(a => a.classList.remove("kw-point")); }
// No rings in the app (23 Oct test: one pointed at Your plan for Blindfold; a wrong ring is worse than none): the coach
// says where things are instead. chess.com keeps its red ring. The ring code stays for a later, tested return.
const KW_RINGS = false;
function kwPoint(route) { kwUnpoint(); if (!KW_RINGS) return; kwPointing = route; kwRing(0); }
function kwRing(tries) {  // the step on this page: the thing itself if it's here, else its menu item
  if (!kwPointing) return;
  document.querySelectorAll(".kw-point").forEach(a => a.classList.remove("kw-point"));
  // "plan@#xq": the page, then that thing on it (the tour: the Explore box, the Done row, the ask bar)
  const [route, inside] = kwPointing.split("@"), top = route.split("/")[0], nav = NAV_OF[top] || top;
  const here = (location.hash.replace(/^#\/?/, "") || "home") === route;
  const menu = () => document.querySelector(`.nav a[href="#/${nav}"]`) ||
    [...document.querySelectorAll(`a[href="#/${nav}"]`)].find(a => !a.closest("#page"));  // Settings sits under the menu
  const el = here && inside ? document.querySelector(`#page ${inside}`)
    : document.querySelector(`#page a[href="#/${route}"]`) || (tries < 15 && (location.hash.replace(/^#\/?/, "").split("/")[0] || "home") === nav
    ? null : menu());
  if (!el && here && inside && tries >= 25) return kwUnpoint();  // not on this page after all
  if (el && here && inside) setTimeout(() => el.scrollIntoView({ block: "center" }), 400);  // once the page has settled
  if (!el) { kwPointTimer = setTimeout(() => kwRing(tries + 1), 200); return; }  // the page is still loading
  el.classList.add("kw-point");
  clearTimeout(kwPointTimer); kwPointTimer = setTimeout(kwUnpoint, 10000);
}
addEventListener("hashchange", () => {
  if (!kwPointing) return;
  const now = location.hash.replace(/^#\/?/, "") || "home", [route, inside] = kwPointing.split("@"), top = route.split("/")[0];
  if (now === route && inside) { clearTimeout(kwPointTimer); return kwRing(0); }  // arrived: now the thing on the page
  if (now === route || now.startsWith(route + "/")) return kwUnpoint();  // arrived: done
  if (now.split("/")[0] === (NAV_OF[top] || top)) { clearTimeout(kwPointTimer); return kwRing(0); }  // followed: the next step
  kwUnpoint();  // somewhere else: it goes
});
// Ask the coach: her face, a field that looks like one, the mic and send inside it, and a few questions to tap
// (22 Oct test: "people won't click here to type, it's not understandable")
const ASK_CHIPS = { home: ["Review my last game", "Why do I lose?", "What should I practise?"],
  review: ["Why was that bad?", "What should I have played?", "Next"] };
function askBox(el, { placeholder, enabled, listen, onAsk, coach, chips }) {
  const face = typeof KnightwiseFaces !== "undefined" ? KnightwiseFaces.svg(coach || "maya", "pleased") : "";
  el.innerHTML = `<div class="askbar"><span class="ask-face">${face}</span>
      <input class="ask-in" data-q placeholder="${esc(enabled ? placeholder : "Add an AI key in Settings to ask the coach")}" ${enabled ? "" : "disabled"}>
      ${listen && enabled ? `<button class="ask-ic" data-mic title="Talk: click, speak, click again to stop">${svg("mic")}</button>` : ""}
      <button class="ask-ic send" data-ask title="Ask" ${enabled ? "" : "disabled"}>${svg("send")}</button></div>
    ${enabled && chips && chips.length ? `<div class="ask-chips">${chips.map(c => `<button data-chip>${esc(c)}</button>`).join("")}</div>` : ""}
    <div data-a class="small" style="margin-top:8px"></div>`;
  if (!enabled) {  // the feature is never hidden: say what a free key gives, and where to add it
    el.innerHTML = `<p class="small" style="margin:0 0 10px">Talk with your coaches and get real replies with a free AI key.</p>
      <a class="btn" href="#/settings">Set up now</a>`;
    return;
  }
  const q = $("[data-q]", el), out = $("[data-a]", el), mic = $("[data-mic]", el);
  // the answer goes away after a minute, or when they do something else (23 Oct test), unless the mouse is on it
  let fade = null;
  const clearAnswer = () => { clearTimeout(fade); out.innerHTML = ""; q.value = "";
    document.removeEventListener("pointerdown", elsewhere, true); };
  // only doing something else clears it (a button, a link, a field), not a click on empty space (23 Oct test)
  const elsewhere = e => { if (!el.contains(e.target) && e.target.closest("a,button,input,select,textarea,label,[onclick]")) clearAnswer(); };
  const fadeLater = () => { clearTimeout(fade); fade = setTimeout(function tick() {
    if (out.matches(":hover")) { fade = setTimeout(tick, 10000); return; }
    clearAnswer(); }, 60000);
    document.addEventListener("pointerdown", elsewhere, true); };
  // her suggestion: the menu item it lives under glows, like a coach pointing; no button (23 Oct test)
  const point = offer => { if (offer && offer.route) kwPoint(offer.route); };
  let busy = false;  // a second press while she's answering is ignored: the first one counts (23 Oct test)
  const go = async () => {
    const text = q.value.trim(); if (!text || busy) return;
    busy = true;
    api("/api/seen?route=ask").catch(() => {});  // the tour: asking has been tried
    clearTimeout(fade);
    out.innerHTML = `<span class="muted">Thinking…</span>`;
    try { const r = await onAsk(text); out.innerHTML = `<div class="coach-says">${esc(r.text)}</div>` +
      (r.ai !== false ? `<p class="kw-ai-note">AI can make mistakes. <button class="kw-report">Report it</button></p>` : "");
      const rep = $(".kw-report", out); if (rep) rep.onclick = feedbackBox; Voice.speak(r.text, false, (COACHES[coach] || {}).voice);
      point(r.offer); fadeLater(); }
    catch (e) { out.innerHTML = `<span class="err">${esc(e.message)}</span>`; }
    finally { busy = false; }
  };
  $("[data-ask]", el).onclick = go;
  el.querySelectorAll("[data-chip]").forEach(b => b.onclick = () => { q.value = b.textContent; go(); });
  q.oninput = () => $("[data-ask]", el).classList.toggle("ready", !!q.value.trim());  // green only when there's something to send
  q.onkeydown = e => { if (e.key === "Enter") go(); };
  if (mic) mic.onclick = async () => {
    if (!Mic.on) {
      Voice.stop();
      try { await Mic.start(); } catch (e) { out.innerHTML = `<span class="err">The microphone isn't available.</span>`; return; }
      mic.innerHTML = svg("stop"); mic.classList.add("rec"); out.innerHTML = `<span class="muted">Listening… click ■ when you're done.</span>`;
    } else {
      mic.innerHTML = svg("mic"); mic.classList.remove("rec"); out.innerHTML = `<span class="muted">Writing down what you said…</span>`;
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
    `<a href="#/${route}" class="${active === route ? "on" : ""}" aria-label="${name}" title="${name}">${svg(icon)}<span>${name}</span></a>`;
  $("#root").innerHTML = `
    <div class="shell">
      <aside class="side">
        <div class="brand"><div class="brand-mark" style="color:var(--on-invert)">${svg("pawn")}</div><span>Knightwise</span></div>
        <nav class="nav">${item("home", "Home", "home")}${item("games", "Games", "games")}${item("practice", "Practice", "practice")}${item("train", "Train", "barbell")}${item("plan", "Your plan", "plan")}${item("course", "Your course", "book")}${item("level", "Your level", "up")}${item("progress", "Progress", "progress")}</nav>
        <div class="side-foot" id="status" hidden></div>
        <a class="side-me" href="#/settings" title="Your chess.com account and settings"><span class="me-pic">${svg("pawn")}</span>
          <span class="me-name" id="mename">${esc((STATUS && STATUS.player) || "")}</span></a>
        <div class="side-icons">
          <button id="sideset" class="${active === "settings" ? "on" : ""}" title="Settings">${svg("settings")}</button>
          <button id="aiuse" title="AI use today">${svg("sparkles")}<i class="dot"></i></button>
          <button id="feedback" title="Send feedback">${svg("message")}</button>
          <button id="synced" title="Checking…" onclick="kwRefresh()">${svg("sync")}<i class="dot"></i></button>
        </div>
      </aside>
      <main><div class="page" id="page">${body}</div></main>
    </div>`;
  paintStatus(); paintAiUse();
  $("#feedback").onclick = feedbackBox;  // the Voice button left the sidebar (22 Oct test): it's in Settings
  $("#sideset").onclick = () => go("settings");
}

// the AI usage panel, like Claude's: a bar per key, what's left today, and who is resting
const FREE_DAY = { groq: 1000, gemini: 250 };  // published free requests a day; Groq's own numbers replace these
async function paintAiUse() {
  const b = $("#aiuse");
  if (!b) return;
  const u = await api("/api/ai-usage").catch(() => null);
  if (!u || !u.slots.length) { b.title = "No AI key: add one in Settings"; b.querySelector(".dot").className = "dot"; b.onclick = () => go("settings"); return; }
  const rows = u.slots.map(x => {
    const limit = x.requests_limit || FREE_DAY[x.provider], left = x.requests_left ?? (limit ? limit - x.requests : null);
    const pct = limit ? Math.min(100, Math.round(100 * (limit - left) / limit)) : 0;
    return { ...x, limit, left, pct };
  });
  const top = Math.max(...rows.map(r => r.pct)), rest = rows.some(r => r.resting_minutes);
  b.title = `AI · ${top}% used today`;
  b.querySelector(".dot").className = `dot ${rest ? "busy" : top > 80 ? "busy" : "ok"}`;
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
  // quiet when all is well: a grey icon with a dot; words only while it's working on something or went wrong
  el.hidden = !busy && s.phase !== "error" && !!s.phase;
  el.innerHTML = `<i class="dot ${!s.phase ? "" : busy ? "busy" : "ok"}"></i><span>${esc(text)}</span>`;
  const icon = $("#synced");
  if (icon) { icon.title = text; icon.querySelector(".dot").className = `dot ${!s.phase || s.phase === "error" ? "bad" : busy ? "busy" : "ok"}`; }
  const me = $("#mename"); if (me && s.player && !me.textContent) me.textContent = s.player;
}

let lastPhase = null, lastVersion = null;
const LIVE_PAGES = ["home", "games", "progress", "level", "plan", "course", "practice", "train"];
async function pollStatus() {
  try { STATUS = await api("/api/status"); } catch (e) { STATUS = {}; }
  paintStatus();
  // new games checked: a page of numbers shows the new numbers by itself (22 Oct finding 5; 23 Oct: every page of
  // stats, not only Home, and never in the middle of practice, a review or training)
  const page = (location.hash.replace(/^#\/?/, "") || "home");
  if (lastVersion !== null && STATUS.data_version !== lastVersion && LIVE_PAGES.includes(page)) route();
  lastVersion = STATUS.data_version ?? lastVersion;
  lastPhase = STATUS.phase;
  setTimeout(pollStatus, STATUS.phase && STATUS.phase !== "ready" ? 1500 : 6000);
}

// ---------- home ----------
function spark(points, good) {  // a small line, no axes: is it going down? good: the last dot in green
  if (points.length < 2) return "";
  const W = 220, H = 56, max = Math.max(...points, 1) * 1.1;
  const x = i => 4 + i * (W - 8) / (points.length - 1), y = v => H - 6 - v / max * (H - 12);
  const d = points.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const n = points.length - 1;
  return `<svg class="spark" viewBox="0 0 ${W} ${H}"><path class="line draw" d="${d}" pathLength="1"/>
    <circle class="last${good ? " good" : ""}" cx="${x(n)}" cy="${y(points[n])}" r="4"/></svg>`;
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
      location.hash.startsWith("#/home") ? [] : [{ label: "Back home", app: "home" }]), 2500);  // no "Back home" on Home (23 Oct test)
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
  shell("train", `<p class="muted">Loading…</p>`);
  const t = (await api("/api/openings")).tree || {};
  if (!t.white && !t.black) { $("#page").innerHTML = `<div class="empty">Your opening tree appears once your games are checked.</div>`; return; }
  const label = n => `${Math.ceil(n.ply / 2)}${n.ply % 2 ? "." : "..."} ${n.san}`;
  const byFen = {};
  let picked = null;
  const node = (n, depth, white, path = []) => {
    const kids = n.children.filter(c => c.games >= 2), line = [...path, n.san];
    const good = n.score >= 55, bad = n.score <= 40, yours = (n.ply % 2 === 1) === white;
    const key = (white ? "w " : "b ") + n.fen;  // the same position can be in both trees
    byFen[key] = { n, white, line };
    const row = `<div class="tree-row" data-fen="${esc(key)}"><span class="tree-move num">${esc(label(n))}</span>
      <span class="tree-name"><b>${yours ? "You" : "They"}:</b> ${esc(plainMove(n.san))}${n.name ? ` <span class="faint">· ${esc(n.name)}</span>` : ""}</span>
      <span class="tree-games small muted num">${n.games} game${n.games > 1 ? "s" : ""}</span>
      <span class="tree-score ${good ? "good" : bad ? "bad" : ""}" title="How you did in the games that went this way"><i style="width:${n.score}%"></i><b class="num">${n.score}%</b></span></div>
      ${n.note ? `<div class="tree-note ${bad ? "bad" : "good"}">${esc(n.note)}</div>` : ""}`;
    if (!kids.length) return `<div class="tree-leaf">${row}</div>`;
    return `<details class="tree-node" ${depth < 1 || n.note ? "open" : ""}><summary>${row}</summary>
      <div class="tree-kids">${kids.map(c => node(c, depth + 1, white, line)).join("")}</div></details>`;
  };
  const side = (name, root, white) => root ? `<div class="box rise"><div class="row spread"><h2 style="margin:0">When you are ${name}</h2>
      <span class="small muted">${root.games} games · you score ${root.score}%</span></div>
      <div class="tree">${root.children.filter(c => c.games >= 2).map(c => node(c, 0, white)).join("")}</div></div>` : "";
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/train" class="small muted" style="text-decoration:none">← Train</a>
      <h1 style="margin-top:6px">How your games start</h1><p class="sub">Your opening tree: the first three moves of every game you played, and how each way went for you.</p></div></div>
    <div class="game-layout">
      <div class="stack">
        <details class="box stack intro-box" style="padding:12px 16px">
          <summary class="small muted" style="cursor:pointer">How to read it</summary>
          <p class="small" style="margin:0">Each row is one move from the start of your games. Click a row to see the board after it, and the moves that came next.</p>
          <p class="small" style="margin:0"><b>1. e4</b> is White's first move, <b>1... e5</b> is Black's answer. The letter and number are the square: files a to h, rows 1 to 8.
            A capital letter is the piece: N knight, B bishop, R rook, Q queen, K king. No letter means a pawn.</p>
          <p class="small" style="margin:0">The bar is your score in the games that went that way: a win counts 1, a draw a half. <span class="good-text">Green</span> is where you do well, <span class="bad-text">red</span> is where you lose more.</p>
        </details>
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
    picked = x;
    Board.render($("#treeboard"), { fen: x.n.fen, flip: !x.white });
    const yours = (x.n.ply % 2 === 1) === x.white;
    $("#treesay").innerHTML = `<b>${esc(label(x.n))}</b>: ${yours ? "you played" : "they played"} ${esc(plainMove(x.n.san))}.
      <p class="small muted" style="margin:6px 0 0">${x.n.games} of your games went this way. You scored ${x.n.score}%: ${x.n.win} won, ${x.n.draw} drawn, ${x.n.loss} lost.${x.n.name ? ` Its name: ${esc(x.n.name)}.` : ""}</p>`;
  }));
  // what's on screen, for a question typed or said here (24 Oct: "why do I lose from this side?" got a general answer)
  window.kwOnScreen = { route: "openings", extra: () => picked ? { line: picked.line.join(" "), side: picked.white ? "white" : "black" } : {},
    get: () => picked ? `Opening tree, the player is ${picked.white ? "White" : "Black"}. ` +
    `Line selected: ${picked.line.map((m, i) => (i % 2 ? "" : `${i / 2 + 1}. `) + m).join(" ")}${picked.n.name ? ` (${picked.n.name})` : ""}. ` +
    `${picked.n.games} of their games went this way: ${picked.n.win} won, ${picked.n.draw} drawn, ${picked.n.loss} lost (score ${picked.n.score}%).`
    : `Opening tree. As White they score ${t.white ? t.white.score : "?"}% in ${t.white ? t.white.games : 0} games; as Black ${t.black ? t.black.score : "?"}% in ${t.black ? t.black.games : 0}. No line selected.` };
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
  shell("train", `<p class="muted">Reading their games…</p>`);
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
      <p class="sub">From move ${s.move_number} · you played ${esc(s.real_move)} and ${s.real === "loss" ? "lost" : "drew"}</p></div></div>
    <div class="game-layout">
      <div><div class="board-wrap" id="board"></div></div>
      <div class="stack">
        <div class="box stack" style="padding:16px">
          <div class="rival" title="${esc(s.human ? `Maia, the human-move model, learned from millions of real games at ${s.rating}: it plays and slips like players of that rating, never the person.` : `The engine at about ${s.rating}, making human-like mistakes on purpose; never the person.`)}">
            <span class="rival-face">${svg("users")}</span>
            <div><b>${esc(s.opponent)}-style <span class="faint num">${s.rating}</span></b>
              <div class="small muted">${s.human ? `Plays like real ${s.rating} players` : `Plays at about ${s.rating}`}</div></div></div>
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
    html += `<span class="rstart">▶ Starts here: move ${s.move_number}, you to move</span>`;  // 22 Oct: "where does it start from?"
    played.forEach((p, i) => { html += `<span class="n">${s.move_number + i}.</span><span>${esc(p[0])}</span><span>${esc(p[1] || "")}</span>`; });
    $("#rmoves").innerHTML = html + (played.length ? "" : `<span class="small muted" style="grid-column:1/-1">Not ${esc(s.real_move)} this time.</span>`);
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
  // a lesson already learnt is being watched in your games: the green button goes to the next thing to do (23 Oct)
  const learnt = s => ["watching", "passed"].includes(s.lesson);
  const cur = p.levels[p.current], up = p.levels[p.current + 1];
  const next = cur.skills.find(s => s.met === false && !learnt(s)) || cur.skills.find(s => s.met === false);
  // the purpose at a glance (22 Oct: "clean, but I did not understand its purpose"): a ladder of five levels, and
  // each skill counted in games you can picture, not decimals
  // one view, no sentences (23 Oct test): each card one big number against its aim, Done or how many too many; the
  // words on hover. Every level's cards can be looked at: click a level.
  const count = s => {
    if (s.value === null || s.value === undefined) return null;
    if (s.unit === "a game") return { n: Math.round(s.value * p.games), aim: Math.floor(s.target * p.games + 1e-9) };
    if (s.unit === "%") return { n: Math.round(s.value), aim: s.target, pct: true };
    return { n: s.value, aim: s.target };
  };
  const skill = (s, mine) => {
    const c = count(s), low = s.way === "max";
    if (!c) return `<div class="box lskill"><b>${esc(s.name)}</b><span class="muted small">Not enough games yet</span></div>`;
    const v = x => c.pct ? `${x}%` : x, gap = Math.round(Math.abs(c.n - c.aim) * 100) / 100;
    return `<div class="box lskill ${s.met ? "met" : "over"}" title="${esc(cap(s.what.replace(/, in \d+ games$/, "")))}: ${v(c.n)} in your last ${p.games} games; aim ${low ? "at most" : "at least"} ${v(c.aim)}">
      <b>${esc(s.name)}</b>
      <div class="lnum"><b class="num">${v(c.n)}</b><span class="muted">aim ${low ? "≤" : "≥"} ${v(c.aim)}</span></div>
      ${s.met ? `<span class="lstate ok">${svg("check")} Done</span>` : `<span class="lstate">${v(gap)} ${low ? "too many" : "to go"}</span>`}
      ${mine && s.met === false && learnt(s) ? `<span class="muted small" title="Only the games you play after a lesson judge it">Learnt · watching your next games</span>` : ""}
      ${mine && s.met === false ? `<a class="btn ${s === next ? "primary" : ""}" href="#/${esc(s.train.route)}">${learnt(s) ? "Learn again" : esc(s.train.label.replace(/ it$/, ""))}</a>` : ""}</div>`;
  };
  const draw = sel => {
    const lv = p.levels[sel], mine = sel === p.current, total = lv.skills.length, doneN = lv.skills.filter(x => x.met).length;
    const ladder = `<div class="ladder">${p.levels.map((l, i) => `<button class="lstepbox ${i < p.current || l.done ? "done" : i === p.current ? "now" : ""} ${i === sel ? "sel" : ""}" data-lv="${i}" title="Players here are usually rated ${esc(l.band)}. You move up by meeting the aims, not by rating.">
      <span class="lcircle num">${l.done ? svg("check") : i + 1}</span><b>${esc(l.name)}</b><span class="faint small">${esc("rated " + l.band.replace(/^about /, "").replace("up to ", "≤ ").replace(" and above", "+"))}</span></button>`).join("")}</div>`;
    const line = mine
      ? (up ? `<b class="num">${doneN} of ${total}</b>&nbsp;done ${svg("down")} all ${total}: Level ${p.current + 2}` : "The top level. Keep it there.")
      : sel > p.current ? `Level ${sel + 1}: a look ahead. Your numbers today, against its aims.`
      : `Level ${sel + 1}: done.`;
    $("#page").innerHTML = `
      <div class="page-head"><div><h1>Your level</h1></div></div>
      ${ladder}
      <p class="lgoal">${line}<span class="muted small" style="font-weight:400;margin-left:auto">your last ${p.games} games</span></p>
      <div class="lskills rise ${mine ? "" : "ahead"}">${lv.skills.slice().sort((a, b) => (a.met === true) - (b.met === true)).map(x => skill(x, mine)).join("")}</div>`;
    $(".lgoal svg") && ($(".lgoal svg").style.transform = "rotate(-90deg)");
    document.querySelectorAll("[data-lv]").forEach(b => b.onclick = () => draw(Number(b.dataset.lv)));
  };
  draw(p.current);  // cards with something to do come first; done ones go to the bottom (23 Oct test)
  Coach.react("viktor", "explain", next
    ? `You're on level ${p.current + 1} of 5, ${cur.name}. Meet every aim and you move up, whatever your rating. The one to fix first: ${next.name.toLowerCase()}.`
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
  // a path of lessons per level, like chess.com's: a circle a lesson, the next one lit (22 Oct: less text)
  const ICON = { passed: "check", fine: "check", coming: "lock", later: "lock" };
  const node = l => {
    const can = l.status !== "coming", cls = l.next ? "next" : l.status;
    return `<a class="cnode ${cls}" ${can ? `href="#/course/${l.id}"` : ""} title="${esc(l.reason || l.habit || "")}${(COURSE_CHIP[l.status] || [])[0] ? " · " + esc(COURSE_CHIP[l.status][0]) : ""}">
      <span class="cdot">${ICON[l.status] && !l.next ? svg(ICON[l.status]) : l.next ? svg("practice") : ""}</span>
      <span class="ctitle">${esc(l.title)}</span></a>`;
  };
  const groups = Object.keys(c.levels).map((lv, i) => {
    const ls = c.lessons.filter(l => l.level === lv);
    const done = ls.filter(l => l.status === "passed" || l.status === "fine").length;
    return `<div class="box cgroup rise"><div class="row spread"><b>Level ${i} · ${esc(c.levels[lv])}</b>
        <span class="muted small num">${done}/${ls.length}</span></div>
      <div class="cpath">${ls.map(node).join("")}</div></div>`;
  }).join("");
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>Your course</h1></div></div>
    ${next ? `<a class="box cnext rise" href="#/course/${next.id}">
      <span class="cnext-icon">${svg("book")}</span>
      <div><div class="muted small">Next for you</div><h3>${esc(next.title)}</h3></div>
      <span class="btn primary">Start</span></a>` : ""}
    <div class="stack">${groups}</div>`;
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
  // the habit in one line, a number for where you are, your own positions as boards; the words on hover and in
  // Viktor's voice (23 Oct test: "see so much of text")
  const rate = typeof item.rate === "number" && typeof item.goal === "number"
    ? (item.rate <= item.goal  // already under the goal: a tick, not an arrow that reads like getting worse
      ? `<div class="lrate" title="${esc(item.reason || "")}"><b class="num good">✓ ${item.rate}</b><span class="muted small">a game, your last 20: under the goal of ${item.goal}</span></div>`
      : `<div class="lrate" title="${esc(item.reason || "")}"><b class="num">${item.rate}</b><span class="faint">→</span><b class="num good">${item.goal}</b><span class="muted small">a game, your last 20</span></div>`) : "";
  $("#page").innerHTML = `
    <div class="page-head"><div>${back}<h1 style="margin-top:6px">${esc(item.title)}</h1></div></div>
    <div class="box lhabit" title="${esc(item.teach.join(" "))}"><span class="label">The habit</span><b>${esc(item.habit)}</b>${rate}</div>
    ${own.length ? `<div class="label" style="margin:18px 0 8px">In your games</div>
      <div class="lboards">${own.map((d, i) => `<div class="lb" title="${esc(d.why)}"><div class="lbb" id="lb${i}"></div>
        <div class="small muted">${esc(String(d.where).replace(/^From your game: /, "").replace(/, you are \w+$/, "").replace(/^m/, "M"))}</div></div>`).join("")}</div>` : ""}
    <div class="row" style="margin-top:16px">
      ${item.drills.length ? `<button class="btn primary" id="practise">Practise it: ${item.drills.length} positions</button>` : ""}
      ${item.train ? `<a class="btn ${item.drills.length ? "" : "primary"}" href="#/${esc(item.train[1])}" id="train">${esc(item.train[0])}</a>` : ""}
      ${!item.drills.length ? `<button class="btn" id="studied">I've studied it</button>` : ""}</div>`;
  own.forEach((d, i) => { const el = $(`#lb${i}`); if (el && d.steps && d.steps[0]) Board.render(el, { pieces: d.steps[0].board, flip: d.flip }); });
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
  shell("train", `<p class="muted">Choosing your lines…</p>`);
  const lines = await api(`/api/repertoire${fresh ? "?fresh=1" : ""}`);
  const slot = l => l.side === "white" ? "As White" : `As Black, against 1. ${l.against}`;
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/train" class="small muted" style="text-decoration:none">← Train</a>
      <h1 style="margin-top:6px">Your repertoire</h1>
      <p class="sub">Three lines to know by heart, chosen from what you already play: from the Lichess opening catalogue, checked by Stockfish. They stay until you ask for new ones.</p></div>
      <button class="btn" id="newlines">Choose new lines</button></div>
    <div class="plan-cards rep-cards">${lines.map((l, i) => `<a class="box pcard" href="#/repertoire/${i}" title="${esc(l.kept ? "You already play this, and it works for you." : l.why)}">
      <div class="row spread"><span class="pkind rep-${l.side}">${svg("pawn")}${l.side === "white" ? "You play White" : `You play Black, against 1. ${esc(l.against)}`}</span>
        ${l.kept ? `<span class="pdone" title="You already play this">${svg("check")}</span>` : ""}</div>
      <h3>${esc(l.name)}</h3><span class="rep-moves num">${esc((l.moves || []).map((m, j) => (j % 2 ? "" : `${j / 2 + 1}. `) + m).join(" "))}</span>${l.stale ? `<span class="small bad-text">Out of date: ${esc(l.stale)}. Choose new lines?</span>` : ""}
      <span class="btn ${i === 0 ? "primary" : ""}">Practise</span></a>`).join("") || `<div class="empty">Your lines appear once your games are checked.</div>`}</div>`;
  $("#newlines").onclick = () => repertoireView(true);
  Coach.react("viktor", "explain", "Your three openings: one as White, two as Black. Practise each one until you can play its first moves without thinking.");
}

// ---------- the endgame trainer: the endings every player must know, against the best defence (0.7) ----------
const GOAL = { mate: "Checkmate them", promote: "Make a new queen", draw: "Hold the draw" };

async function endgamesView() {
  shell("train", `<p class="muted">Loading…</p>`);
  const list = await api("/api/endgames");
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/train" class="small muted" style="text-decoration:none">← Train</a>
      <h1 style="margin-top:6px">Endgame trainer</h1>
      <p class="sub">The endings every player must know, played out against perfect defence: Lichess's endgame tablebase knows the best move in every one. A new position each time.</p></div></div>
    <div class="plan-cards">${list.map(e => `<a class="box pcard" href="#/endgame/${e.id}" title="${esc(e.idea)}">
      <div class="row spread"><span class="pkind">${svg({ mate: "mate", promote: "up", draw: "draw" }[e.goal] || "mate")}Level ${e.level}</span>
        ${e.solved ? `<span class="pdone" title="Solved ${e.solved}×">${svg("check")}</span>` : ""}</div>
      <h3>${esc(e.name)}</h3>
      <span class="muted small">${esc(GOAL[e.goal])} · ${e.limit} moves</span>
      <span class="btn ${e === list.find(x => !x.solved) ? "primary" : ""}">${e.solved ? "Again" : "Start"}</span></a>`).join("")}</div>`;
  Coach.react("viktor", "explain", "Endings. Every won game ends in one of these. Learn them once and they win games for the rest of your life.");
}

async function endgameView(id) {
  shell("train", `<p class="muted">Setting up the position…</p>`);
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

// How to beat them (24 Oct, owner's idea): Stockfish checks their last 30 games (about 20-40 s), then one view, in
// order: the killer insights, their weak spot / where they go wrong / your plan, then practice against them
const KILLER_ICON = { opening: "book", king: "mate", clock: "clock", tilt: "bolt" };
async function scoutBox(user) {
  const el = () => document.getElementById("scout");
  if (!el()) return;
  el().innerHTML = `<div class="box scout-wait"><b>How to beat ${esc(user)}</b><span class="muted small" id="scoutn">Stockfish is checking their games…</span>
    <div class="bar"><div id="scoutbar" style="width:3%"></div></div></div>`;
  let r, drawn = false;
  for (;;) {
    r = await api(`/api/scout/${encodeURIComponent(user)}`).catch(() => null);
    if (!el()) return;  // they moved on
    if (r && r.result) { paintScout(user, r); drawn = true; }
    if (!r || r.state !== "running") break;
    if (!drawn && r.total) {
      $("#scoutbar").style.width = `${Math.max(3, 100 * r.done / r.total)}%`;
      $("#scoutn").textContent = `Stockfish is checking their games… ${Math.round(100 * r.done / r.total)}%`;
    }
    await new Promise(ok => setTimeout(ok, 1200));
  }
  if (!r || r.state !== "done") { el().innerHTML = `<p class="small muted">${esc((r && r.message) || "The deeper look didn't work this time.")}</p>`; return; }
  const x = r.result, k = x.killers[0];
  Coach.react("maya", "explain", `${user}: ${k ? k.text : x.tips[0]}`, x.puzzles.length ? [{ label: "Punish their mistakes", app: `punish/${user}` }] : []);
}

function paintScout(user, r) {
  const x = r.result, h = x.habits[0], ph = x.phases, total = ph.opening + ph.middlegame + ph.endgame;
  const seg = (k, c) => total && ph[k] ? `<i style="flex:${ph[k]};background:${c}" title="${cap(k)}: ${ph[k]}"></i>` : "";
  const puzzles = x.puzzles;  // null while they're still being made
  const left = r.total ? Math.round(100 * r.done / r.total) : 0;
  $("#scout").innerHTML = `
    <div class="scout-head"><h2>How to beat ${esc(user)}</h2><span class="muted small">Stockfish, their last ${x.games} games</span></div>
    ${x.killers.length ? `<div class="scout-killers">${x.killers.map(k => `<div class="box scout-killer ${k.kind}">
        <div class="scout-k-top">${svg(KILLER_ICON[k.kind] || "bolt")}<span>${esc(k.title)}</span><b class="num">${esc(k.big)}</b></div>
        <p>${esc(k.text)}</p>
        ${k.practise ? `<a class="btn small-btn" href="#/${esc(k.practise)}">Practise this line</a>` : ""}</div>`).join("")}</div>` : ""}
    <div class="scout-grid">
      <div class="box scout-card"><div class="label">Their weak spot</div>
        ${h ? `<div class="scout-big"><b class="num">${h.per_game}</b><span>${esc(h.what)} a game</span></div>
          ${x.habits[1] ? `<div class="small muted">then ${esc(x.habits[1].what)}: ${x.habits[1].per_game} a game</div>` : ""}`
          : `<div class="scout-big"><b class="num">${x.big_per_game}</b><span>big mistakes a game</span></div>`}</div>
      <div class="box scout-card"><div class="label">When they go wrong</div>
        ${total ? `<div class="scout-phase">${seg("opening", "#5ea4e8")}${seg("middlegame", "#e9a23b")}${seg("endgame", "#b48ce0")}</div>
        <div class="scout-keys small"><span><i style="background:#5ea4e8"></i>Opening ${ph.opening}</span><span><i style="background:#e9a23b"></i>Middlegame ${ph.middlegame}</span><span><i style="background:#b48ce0"></i>Endgame ${ph.endgame}</span></div>`
          : `<div class="small muted">Hardly any big mistakes.</div>`}
        ${x.slipped.of ? `<div class="small">${x.slipped.lost} of ${x.slipped.of} winning games let slip</div>` : ""}</div>
      <div class="box scout-card scout-tips"><div class="label">Your plan</div>
        <ol>${x.tips.map(t => `<li>${esc(t)}</li>`).join("")}</ol></div>
    </div>
    <div class="scout-practice">
      <div class="box scout-punish"><div class="label">Practise against them</div>
        <b>Punish their mistakes</b><span class="small muted">${puzzles ? `${puzzles.length} real positions where ${esc(user)} went wrong. Find the right move.` : `Picking positions from their games… ${left}%`}</span>
        ${puzzles && puzzles.length ? `<a class="btn primary" href="#/punish/${esc(user)}">${svg("practice")} Punish ${puzzles.length}</a>` : ""}</div>
      ${homeworkCard(user, r.homework)}
    </div>
    <div class="box scout-spar"><span class="spar-ic">${svg("users")}</span><div style="flex:1"><b>Spar against them</b>
      <div class="small muted">They open the way they really do, then play like players of their rating.</div></div>
      <a class="btn" href="#/spar/${esc(user)}/white">As White</a><a class="btn" href="#/spar/${esc(user)}/black">As Black</a></div>
    <h2 class="scout-details">The details</h2>`;
}

// the Homework done badge as a medal: win your very next game against them after Prep (levels 1, 3, 10)
function homeworkCard(user, n) {
  n = n || 0;
  const levels = [1, 3, 10], next = levels.find(l => n < l), tier = levels.filter(l => n >= l).length;
  const metal = ["none", "bronze", "silver", "gold"][tier];
  return `<div class="box scout-badge ${metal}" title="A badge in Progress">
    <div class="hw-medal">${svg("medal")}</div>
    <div class="hw-text"><b>Homework done</b>
      <span class="small muted">${next ? `Beat ${esc(user)} in your next game against them` : "Every level done"}</span>
      <div class="hw-bar"><i style="width:${next ? Math.round(100 * n / next) : 100}%"></i></div>
      <span class="small num">${n}${next ? ` / ${next}` : ""}</span></div></div>`;
}

// their real mistakes as puzzles, from the deeper look (kept an hour; if it's gone, it runs again first)
async function punishView(user) {
  shell("train", `<p class="muted">Loading…</p>`);
  let r;
  for (let n = 0; n < 120; n++) {
    r = await api(`/api/scout/${encodeURIComponent(user)}`).catch(() => null);
    if (!r || r.state !== "running") break;
    if (!location.hash.startsWith("#/punish/")) return;
    $("#page").innerHTML = `<p class="muted">Stockfish is checking ${esc(user)}'s games… ${r.total ? Math.round(100 * r.done / r.total) + "%" : ""}</p>`;
    await new Promise(ok => setTimeout(ok, 1200));
  }
  if (!location.hash.startsWith("#/punish/")) return;
  const drills = (r && r.result && r.result.puzzles) || [];
  if (!drills.length) { $("#page").innerHTML = `<div class="empty">No positions to punish this time. <a href="#/prep/${esc(user)}">Back to Prep</a></div>`; return; }
  $("#page").innerHTML = trainerPage(`Punish ${user}'s mistakes`,
    { back: `<a href="#/prep/${esc(user)}" class="small muted" style="text-decoration:none">← Prep</a>`, text: "" });
  trainer(drills, { coach: "maya" });
}

// ---------- prep before a game: how a chess.com player plays, from their public games (0.8, flagship 1) ----------
async function prepView(user) {
  shell("train", `<p class="muted">Loading…</p>`);
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/train" class="small muted" style="text-decoration:none">← Train</a>
      <h1 style="margin-top:6px">Prep before a game</h1>
      <p class="sub">How a chess.com player plays, from their public games of the last three months. Only before a game: Knightwise is never active during one.</p></div></div>
    <div class="box stack" style="padding:16px"><div class="row"><input class="field" id="who" placeholder="Their chess.com username" value="${esc(user || "")}" spellcheck="false" style="max-width:280px">
      <button class="btn" id="look">Look them up</button></div><div class="err" id="prepmsg"></div></div>
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
      <div class="prep-grid prep-colour">
        <div class="box stack prep-who" style="padding:16px"><h2 style="margin:0">${esc(s.user)} <span class="faint num">${s.rating}</span></h2>
          <p class="small muted" style="margin:0">${s.games} games in three months, mostly ${esc(s.time_class)}.</p>
          ${s.advice.map(a => `<p style="margin:0">${esc(a)}</p>`).join("")}</div>
        <div class="box stack" style="padding:16px"><h2 style="margin:0">As White, they start with</h2>
          ${list(s.as_white, r => `1. ${esc(r.what)} <span class="small muted">· ${esc(plainMove(r.what))}</span>`)}</div>
        <div class="box stack" style="padding:16px"><h2 style="margin:0">As Black, they answer</h2>
          ${list(s.as_black, r => { const [a, b] = r.what.split(" "); return `1. ${esc(a)} ${esc(b)} <span class="small muted">· after ${esc(plainMove(a))}: ${esc(plainMove(b))}</span>`; })}</div>
        <div class="box stack" style="padding:16px"><h2 style="margin:0">How their games end</h2>
          ${ends.map(([k, n]) => `<div class="pend ${k === "won" ? "won" : k === "drew" ? "" : "lost"}"><span>${esc(cap(k))}</span><i><b style="width:${100 * n / Math.max(...ends.map(e => e[1]))}%"></b></i><b class="num">${n}</b></div>`).join("")}</div>
      </div>`;
    $("#prep").insertAdjacentHTML("afterbegin", `<div id="scout" class="scout"></div>`);
    scoutBox(s.user);
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
          ${(r.ratings || []).map(x => `<div class="small">${esc(cap(x.kind))} <span class="muted">(${x.games})</span> ${x.from} → ${x.to}
            ${x.to !== x.from ? `<span class="delta ${x.to > x.from ? "good" : "bad"}">${x.to - x.from > 0 ? "+" : ""}${x.to - x.from}</span>` : `<span class="muted">same</span>`}</div>`).join("")}</div>
        <div class="box stack"><div class="label">Mistakes a game</div>
          <div class="small"><b>${per(r.pieces.now)}</b> pieces given away ${change(r.pieces.now, r.pieces.before)}</div>
          <div class="small" title="The named mistakes (a piece left hanging, a missed mate and so on), the three costliest a game at most"><b>${per(r.big)}</b> big mistakes</div>
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

// Wrapped: the same facts as big cards, one at a time, with Viktor saying the last one. Click, or the arrow keys, to move on.
function wrapped(r) {
  const res = r.results || {}, rt = r.rating || {}, pr = r.practice || {};
  const cards = [
    [r.title, `${esc(r.from)} to ${esc(r.to)}`, `${r.title}, ${r.player}. Let's look at it.`],
    [`${r.games}`, `game${r.games === 1 ? "" : "s"} played`, `${r.games} games.`],
    [`${res.win || 0}`, `won · ${res.draw || 0} drawn · ${res.loss || 0} lost`, `${res.win || 0} of them won.`],
  ];
  if (rt.from && rt.to !== rt.from) cards.push([`${rt.to - rt.from > 0 ? "+" : ""}${rt.to - rt.from}`, `${rt.kind || ""} rating: ${rt.from} to ${rt.to}`, `Your ${rt.kind || ""} rating went from ${rt.from} to ${rt.to}.`]);
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
    // Viktor speaks only on the last card; the others are read under the music (24 Oct, owner)
    if (k === cards.length - 1) Voice.speak(say, false, COACHES.viktor.voice); else Voice.stop();
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
  let musicOn = songs.length > 0, stop = null;  // music on by default, every time (23 Oct test)
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/progress" class="small muted" style="text-decoration:none">← Progress</a>
      <h1 style="margin-top:6px">${esc(s.title)}</h1>
      <p class="sub">Against ${esc(s.opponent)}, ${esc(s.date)}</p></div></div>
    <div class="film-wrap" id="film"></div>
    <div class="row film-controls"><button class="btn primary" id="filmgo">▶ Play</button>
      ${songs.length ? `<button class="btn ghost" id="filmmusic" title="Music on or off">${musicOn ? "♪ On" : "♪ Off"}</button>` : ""}
      <span class="small muted" id="filmmsg"></span></div>`;
  const ready = () => window.Film ? Promise.resolve() : new Promise(r => window.addEventListener("film-ready", r, { once: true }));
  const song = () => (pick >= 0 ? songs[pick] : null);  // always loaded; the switch only mutes it
  const go = $("#filmgo");
  const started = () => { remember("kw-film-song", String(pick)); Voice.stop(); Coach.hide(); };  // nothing in front of the film
  async function mount(autoplay, record) {  // the film: a still preview first, or playing (and recording)
    await ready();
    if (stop) stop();
    window.kwFilm = stop = window.Film.play($("#film"), s, { record, autoplay, music: song(), muted: !musicOn, onEnd: async r => {
      go.textContent = "▶ Play again"; go.dataset.state = "ended";
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
    $("#filmmsg").textContent = "";
  }
  go.onclick = () => {  // one button: play, pause, carry on, play again
    const st = go.dataset.state;
    if (st === "preview") { stop.resume(); started(); go.textContent = "❚❚ Pause"; go.dataset.state = "playing"; }
    else if (st === "playing") { stop.pause(); go.textContent = "▶ Carry on"; go.dataset.state = "paused"; }
    else if (st === "paused") { stop.resume(); go.textContent = "❚❚ Pause"; go.dataset.state = "playing"; }
    else mount(true, false);
  };
  $("#film").onclick = () => go.click();  // the picture itself plays and pauses too
  const mb = $("#filmmusic");
  if (mb) mb.onclick = () => {
    musicOn = !musicOn; mb.textContent = musicOn ? "♪ On" : "♪ Off";
    if (stop && stop.mute) stop.mute(!musicOn);  // the film carries on where it is
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
  shell("train", `<p class="muted">Finding one of your games…</p>`);
  let x;
  try { x = await api("/api/blindfold"); } catch (e) { $("#page").innerHTML = `<div class="empty">${esc(e.message)}</div>`; return; }
  let ready = false, done = false, peeked = false, reading = 0;
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/train" class="small muted" style="text-decoration:none">← Train</a>
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
  shell("train", `<p class="muted">Setting up this week's challenge…</p>`);
  const c = await api("/api/guess");
  if (!c.positions.length) {
    $("#page").innerHTML = `<div class="empty">The weekly challenge needs the human-move model. Switch on "Human-like opponents" in Settings.</div>`;
    return;
  }
  let i = 0, picked = null, total = 0, answered = false;
  const scores = [];
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/train" class="small muted" style="text-decoration:none">← Train</a>
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
  shell("train", `<p class="muted">Loading…</p>`);
  const items = await api("/api/calc");
  if (!items.length) { $("#page").innerHTML = `<div class="empty">The calculation puzzles appear once the puzzles are downloaded.</div>`; return; }
  let i = 0, line = [], picked = null, done = false;
  // today's answers are kept in this app: leaving and coming back doesn't start the set again (24 Oct test)
  const KEY = "kw-calc", today = new Date().toDateString();
  let kept = {};
  try { const k = JSON.parse(localStorage.getItem(KEY) || "{}"); kept = k.day === today ? k.answers || {} : {}; } catch (e) {}
  const keep = () => { try { localStorage.setItem(KEY, JSON.stringify({ day: today, answers: kept })); } catch (e) {} };
  const firstTry = {};
  i = Math.max(0, items.findIndex(it => !(it.id in kept)));  // the first one not done today
  if (items.every(it => it.id in kept)) i = items.length - 1;
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/train" class="small muted" style="text-decoration:none">← Train</a>
      <h1 style="margin-top:6px">See it in your head</h1>
      <p class="sub calc-sub">Plan moves ahead without moving the pieces: the skill of seeing ahead.</p></div>
      <span class="muted num" id="calccount"></span></div>
    <div class="game-layout">
      <div><div class="board-wrap" id="board"></div><p class="small muted" id="calcwhere" style="margin-top:10px"></p></div>
      <div class="stack">
        <div class="box stack" style="padding:16px"><h3 style="margin:0" id="calctask"></h3><p class="small muted" style="margin:0" id="calchint"></p></div>
        <div class="box stack" style="padding:16px"><div class="label">Your plan, before anything moves</div><div id="calcline" class="calc-slots"></div><div id="calcmsg" class="small"></div>
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
    // one slot per move of the plan: yours, theirs, yours... filled as you click (24 Oct: "first glance doesn't say what this is")
    $("#calcline").innerHTML = Array.from({ length: need() }, (_, k) => `<div class="calc-slot ${yours(k) ? "mine" : "theirs"} ${line[k] ? "full" : k === line.length ? "now" : ""}">
        <span class="num">${k + 1}</span><b>${yours(k) ? "Your move" : "Their reply"}</b>
        <i class="num">${line[k] ? `${line[k].slice(0, 2)} → ${line[k].slice(2, 4)}` : k === line.length ? "click a piece, then its square" : "…"}</i></div>`).join("");
    $("#calccount").textContent = `${i + 1} of ${items.length} · ${Object.keys(kept).filter(id => items.some(it => it.id === id)).length} done today`;
  }
  function show() {
    line = []; picked = null; done = false;
    $("#calctask").textContent = x().intro;
    $("#calchint").textContent = `Clue: ${x().hint}`;
    $("#calcwhere").textContent = x().where || "";
    $("#calcmsg").innerHTML = "";
    draw();
    if (x().id in kept) {  // done earlier today: say so, and show the line
      done = true;
      $("#calcmsg").innerHTML = `<span class="${kept[x().id].right ? "ok-text" : "muted"}"><b>Done today${kept[x().id].right ? ", seen all the way" : ""}.</b> The line: ${esc(kept[x().id].real)}.</span> <span class="muted">Press Next.</span>`;
    }
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
    kept[x().id] = { right, real }; keep();
    if (right) Sound.play("right");  // no confetti for each line: it stays rare (1.0 design rule)
    const where = wrong < 0 ? "" : yours(wrong) ? `Your move ${Math.floor(wrong / 2) + 1} wasn't the one.` : `You didn't see their answer: it's not what you expected.`;
    $("#calcmsg").innerHTML = right ? `<span class="ok-text"><b>You saw it all.</b> ${esc(real)}.</span>`
      : `<span class="bad-text">${esc(where)}</span> The line: ${esc(real)}.`;
    Coach.react("viktor", right ? "celebrate" : "explain", right ? "You saw it all before moving. That's calculation." : `${where} The line was ${real}. Try the next one: see the end first.`);
  }
  $("#calcundo").onclick = () => { if (!done && line.length) { line.pop(); draw(); } };
  $("#calccheck").onclick = check;
  $("#calcnext").onclick = () => {
    const left = items.findIndex((it, n) => n > i && !(it.id in kept));
    if (left >= 0) { i = left; show(); return; }
    const all = items.filter(it => it.id in kept);
    if (all.length === items.length) Coach.react("viktor", "celebrate", `All ${items.length} done today: ${all.filter(it => kept[it.id].right).length} seen all the way first time. New ones tomorrow.`);
    else { i = items.findIndex(it => !(it.id in kept)); show(); }
  };
  show();
  Coach.react("viktor", "explain", "Don't move yet. See the whole line in your head first: your move, their best answer, your next. Then check.");
}

// ---------- progress: Viktor's story of your week, and badges from your real games ----------
// chess.com games and Knightwise practice counted apart, never blended (13 Oct test, point 16)
const BADGE_SOURCES = [["From your chess.com games", ["Habits", "Clean play", "Results", "Big moments", "Accuracy", "Clock", "Rating", "Openings"]],
  ["From your Knightwise training", ["Practice", "Training"]]];
const TIERS = ["Bronze", "Silver", "Gold"];
function badgeCard(b) {  // what you have, what's next, and whether it's complete: one look
  const state = b.tier === 3 ? "Complete" : b.tier ? `${b.tier_name} · Gold at ${b.tiers[2]}` : `Not started · Bronze at ${b.tiers[0]}`;
  // a medal, its name, a number and a bar; the words are on hover (22 Oct: less text)
  return `<div class="badge t${b.tier}" title="${esc(state)} · ${esc(b.what)}">
    <div class="medal">${svg(b.icon)}</div><b>${esc(b.name)}</b>
    <div class="small muted num">${b.next ? `${b.best}/${b.next}` : `${b.best}`}${b.tier === 3 ? " ✓" : ""}</div>
    <div class="bar"><div style="width:${b.next ? Math.min(100, 100 * b.best / b.next) : 100}%"></div></div></div>`;
}
async function progressView() {
  shell("progress", `<p class="muted">Loading…</p>`);
  const p = await api("/api/progress");
  if (!p.player) return go("welcome");
  const s = p.story, r = (s && s.results) || {};
  const complete = p.badges.filter(b => b.tier === 3).length, started = p.badges.filter(b => b.tier && b.tier < 3).length;
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>Progress</h1></div>
      <div class="row"><a class="ltool" href="#/report/week" title="A report for your coach or a parent">${svg("plan")}<span>Report</span></a>
        <a class="btn primary" href="#/film/month" title="Your game of the month, as a film">▶ Game of the month</a></div></div>
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
        ${s.next ? `<div class="story-next" title="Next week's one thing">${svg("bolt")}<span>${esc(s.next.habit)}</span></div>` : ""}
      </div>` : `<div class="empty">Your story appears after your first checked games.</div>`}
      ${p.clock && p.clock.lines.length ? `<div class="box rise pclock" title="${esc(p.clock.lines.join(" "))}">
        <h2 style="margin:0">${svg("clock")}Your clock</h2>
        <div class="pclock-n"><b class="num">${p.clock.fast}<span class="faint">/${p.clock.big}</span></b><span class="muted small">big mistakes in a rush</span></div>
        <div class="pclock-n"><b class="num">${p.clock.on_time}<span class="faint">/${p.clock.losses}</span></b><span class="muted small">losses on time</span></div>
        ${p.clock.fast ? `<a class="btn" href="#/clockdrill" title="Your rushed moves, again: count to five first">Slow down</a>` : ""}</div>` : ""}
      <div class="box rise"><div class="row spread"><h2 style="margin:0">Badges</h2>
          <div class="ring-legend"><span><i class="t1"></i>Bronze</span><span><i class="t2"></i>Silver</span><span><i class="t3"></i>Gold, complete</span></div></div>
        <p class="small muted num" style="margin:6px 0 0" title="A badge is complete at Gold">${complete} complete · ${started} on the way · ${p.badges.length - complete - started} to start</p>
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
  const hour = new Date().getHours(), hello = hour >= 5 && hour < 12 ? "Good morning" : hour >= 12 && hour < 18 ? "Good afternoon" : "Good evening";  // the coaches' rule: evening until 5 am
  const f = h.focus, last = h.last_game, r = h.results || {}, pr = h.practice || {};
  const better = h.pieces_last20 < h.pieces_per_game;
  const played = (r.win || 0) + (r.loss || 0) + (r.draw || 0) || 1, pct = n => (100 * (n || 0) / played).toFixed(1);
  const rc = h.rating_change;
  const arrow = (good, text) => `<span class="trend ${good ? "good" : "bad"}">${svg(good ? "down" : "up")}${text}</span>`;
  // pictures and numbers, not sentences (22 Oct, the approved mockup): three cards, small tiles, one green button
  const d = h.daily || {}, tiles = h.patterns.slice(0, 3), v = h.you_vs_you;
  // good or bad decides the colour; rising (more wins) or falling (fewer pieces lost) decides the arrow
  const trend = (good, text, rises = false) => `<span class="${good ? "up-good" : "up-bad"}">${svg(good === rises ? "up" : "down")}${text}</span>`;
  const short = { "left a piece hanging": "hanging", "walked into a fork or trick": "forks", "missed a free capture": "missed takes",
    "walked into checkmate": "walked into mate", "missed a checkmate": "missed mates", "stalemated a won game": "stalemates" };
  // one green button: the first of the three not done today (5 minutes, then the latest game's review, then the
  // focus); all done, all grey; after midnight it starts again from the 5 minutes (23 Oct test)
  const td = { daily: !!d.done_today, ...(h.today_done || {}) };
  const green = [["daily", true], ["review", !!last], ["practice", !!f]].find(([k, has]) => has && !td[k]);
  const btn = k => `btn${green && green[0] === k ? " primary" : ""}`;
  $("#page").innerHTML = `
    ${STATUS.phase && !["ready", "starting"].includes(STATUS.phase) && STATUS.total ? `<div class="box checking">${svg("sync")}
      <span>Checking your games: <b class="num">${STATUS.done}</b> of ${STATUS.total}</span><div class="bar"><div style="width:${100 * STATUS.done / STATUS.total}%"></div></div></div>` : ""}
    <div class="home-head"><h1>${hello}, ${esc(h.player)}</h1>
      <span class="home-streak" title="Days in a row of your five minutes">${svg("flame")}<b class="num">${d.streak || 0}</b></span></div>
    <div class="home-cards rise">
      <a class="box hcard" href="#/daily">
        <div class="row spread"><b>${d.done_today ? "Done today" : "Today"}</b><span class="muted">5 min</span></div>
        <div class="mini-board" id="todayboard"></div>
        <div class="week-bars" title="Your last 7 days: green when your 5 minutes were done">${(d.week || []).map((on, i) => {
          // the last 7 days, today on the right, each with its letter (23 Oct test: "why is the bar filled at the end?")
          const day = new Date(Date.now() - (6 - i) * 86400000);
          return `<span class="${i === 6 ? "today" : ""}" title="${day.toLocaleDateString(undefined, { weekday: "long" })}${i === 6 ? " (today)" : ""}: ${on ? "done" : "not done"}"><i class="${on ? "on" : ""}"></i><b>${"SMTWTFS"[day.getDay()]}</b></span>`;
        }).join("")}</div>
        <span class="${btn("daily")}">${d.done_today ? "Play again" : "Start"}</span></a>
      ${last ? `<a class="box hcard" href="#/games/${last.id}">
        <div class="row spread"><b class="ellipsis">${esc(last.opponent)} <span class="faint num">${last.opponent_rating}</span></b>
          <span class="chip ${last.result}">${last.result === "win" ? "W" : last.result === "loss" ? "L" : "D"}</span></div>
        <div class="mini-board" id="lastboard"></div>
        <div class="row spread muted small"><span title="Key moments">${svg("bolt")} ${last.moments}</span>
          <span title="Pieces given away">${svg("hang")} ${last.pieces_lost}</span></div>
        <span class="${btn("review")}">Review</span></a>` : ""}
      ${f ? `<a class="box hcard" href="#/practice/${encodeURIComponent(f.pattern)}">
        <div class="row spread"><b>Your focus</b><span class="hicon calm" title="Practise: ${esc((PATTERN_TITLE[f.pattern] || cap(f.pattern)).toLowerCase())}">${svg("practice")}</span></div>
        <div class="hnum"><b class="num">${roll(h.pieces_last20, 1)}</b>${trend(better, `from ${h.pieces_per_game.toFixed(1)}`)}</div>
        <div title="Pieces lost a game, each point the average of ${h.trend_window || 10} games, oldest on the left. Now ${Number(h.pieces_last20).toFixed(1)}; over all your games ${h.pieces_per_game.toFixed(1)}.">${spark(h.trend, better)}</div>
        <span class="muted small">pieces lost a game</span>
        <span class="${btn("practice")}">Practise</span></a>` : ""}
    </div>
    <div class="home-tiles rise">
      ${tiles.map(p => { const [icon] = HABIT[p.pattern] || ["hang"], fewer = p.recent <= p.per_game;
        return `<a class="box tile" href="#/practice/${encodeURIComponent(p.pattern)}" title="${esc((HABIT[p.pattern] || [])[1] || p.pattern)}: practise it">
          ${svg(icon)}<b class="num">${roll(p.times)}</b><span class="muted small">${esc(short[p.pattern] || p.pattern)} ${trend(fewer, "")}</span></a>`; }).join("")}
      <div class="box tile" title="${cap(h.rating_class || "")} rating · ${r.win || 0} won, ${r.draw || 0} drawn, ${r.loss || 0} lost">
        <div class="row spread"><b class="num">${h.rating ? roll(h.rating) : "–"}</b>${rc ? `<span class="${rc > 0 ? "up-good" : "up-bad"} small">${rc > 0 ? "+" : ""}${rc}</span>` : ""}</div>
        <div class="wld"><i class="w" style="width:${pct(r.win)}%"></i><i class="d" style="width:${pct(r.draw)}%"></i><i class="l" style="width:${pct(r.loss)}%"></i></div>
        <span class="muted small">${esc(h.rating_class || "rating")}</span></div>
    </div>
    ${v ? `<div class="home-vs rise" title="${esc(v.now.label)} against ${esc(v.then.label.toLowerCase())}">
      <span class="muted small">You vs you</span>
      <span title="Pieces given away a game">${svg("hang")}<b class="num">${v.now.pieces}</b>${trend(v.now.pieces <= v.then.pieces, v.then.pieces)}</span>
      <span title="Games won">${svg("medal")}<b class="num">${v.now.wins}%</b>${trend(v.now.wins >= v.then.wins, v.then.wins + "%", true)}</span>
      <span title="Key moments a game">${svg("bolt")}<b class="num">${v.now.moments}</b>${trend(v.now.moments <= v.then.moments, v.then.moments)}</span></div>` : ""}
    <div class="askpill" id="askbox"></div>`;
  if (last && last.fen) Board.render($("#lastboard"), { fen: last.fen, flip: last.flip });
  api("/api/warmup").then(w => { const x = (w.items || [])[0]; if (x && $("#todayboard")) Board.render($("#todayboard"), { pieces: x.board, flip: x.flip }); }).catch(() => {});
  countUp($("#page"));
  // no "Hear it from Maya" button (23 Oct notes: unnecessary): Maya greets and talks by herself
  api("/api/settings").then(cfg => askBox($("#askbox"), { placeholder: "Ask Maya anything about your chess", coach: "maya",
    enabled: Object.values(cfg.slots).some(x => x.set), listen: cfg.talk_ready,
    onAsk: async q => {  // the same brain as Talk (19 Oct): typing "open my last review" opens it
      const r = await api("/api/talk", { coach: "maya", text: q, history: homeTalk.slice(-4), where: { section: "home" } });
      homeTalk.push(["player", q], ["coach", r.text]);  // so "please do" knows what she offered
      if (r.action && r.action.route) { window.kwOpenedFor = Date.now() + 8000; setTimeout(() => go(r.action.route), 1200); }
      return r;
    } }));
}

const homeTalk = [];
// ---------- games ----------
async function games() {
  shell("games", `<p class="muted">Loading…</p>`);
  const list = await api("/api/games");
  // rows like chess.com's archive, by month: the result, who, what kind, and two numbers with icons (22 Oct)
  const month = g => String(g.date).split(" ").slice(1).join(" ");
  let html = "", last = null;
  for (const g of list) {
    if (month(g) !== last) { last = month(g); html += `<div class="gmonth">${esc(last)}</div>`; }
    html += `<a class="grow" href="#/games/${g.id}">
      <span class="chip ${g.result}">${g.result === "win" ? "W" : g.result === "loss" ? "L" : "D"}</span>
      <span class="gside ${g.color}" title="You were ${g.color}"></span>
      <b class="ellipsis">${esc(g.opponent)} <span class="faint num">${g.opponent_rating}</span></b>
      <span class="muted small gtype">${esc(cap(g.time_class))}</span>
      <span class="gstat ${g.checked && g.pieces_lost ? "bad" : ""}" title="Pieces given away">${svg("hang")}<span class="num">${g.checked ? g.pieces_lost : "–"}</span></span>
      <span class="gstat" title="Key moments">${svg("bolt")}<span class="num">${g.checked ? g.moments : "–"}</span></span>
      <span class="faint small num gdate">${esc(String(g.date).split(" ")[0])}</span></a>`;
  }
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>Games <span class="faint num" style="font-size:16px">${list.length}</span></h1></div>
</div>
    <div class="box glist">${html}</div>`;
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
      <p class="sub">${cap(g.result)} · ${esc(g.time_class)} · you were ${g.color}${g.opening ? " · " + esc(g.opening) : ""}</p></div>
      <div class="row">${g.result === "win" && g.positions.length > 20 ? `<a class="btn" href="#/film/${g.id}">▶ Watch it as a film</a>` : ""}
        <a class="btn" href="${esc(g.url)}" target="_blank" rel="noopener">Open on chess.com ↗</a></div></div>
    <div class="game-layout">
      <div><div class="evalwrap"><div class="evalbar ${flip ? "flip" : ""}" id="evalbar" title="Who's winning"><i></i><span></span></div>
          <div class="board-wrap" id="board"></div></div>
        <div class="controls"><button class="btn" data-go="0">⏮</button><button class="btn" data-go="-1">◀</button>
          <button class="btn" data-go="1">▶</button><button class="btn" data-go="end">⏭</button></div>
        <div class="evalgraph" id="evalgraph" title="Your chance to win, move by move: click to go there"></div>
        <div style="margin-top:12px">${Board.legend(["mine", "better", "real", "reply"])}</div></div>
      <div class="stack">
        <div class="box stack walk" id="walk"></div>
        ${g.clock && g.clock.lines.length ? `<div class="box rclock" title="${esc(g.clock.lines.join(" "))}">
          ${svg("clock")}<span><b class="num">${g.clock.average}s</b><span class="muted small">a move</span></span>
          ${g.clock.longest ? `<span><b class="num">${Math.floor(g.clock.longest.seconds / 60)}:${String(g.clock.longest.seconds % 60).padStart(2, "0")}</b><span class="muted small">longest, move ${g.clock.longest.move}</span></span>` : ""}
          ${g.clock.left != null ? `<span><b class="num">${Math.floor(g.clock.left / 60)}:${String(g.clock.left % 60).padStart(2, "0")}</b><span class="muted small">left at the end</span></span>` : ""}</div>` : ""}
        <div class="askpill" id="askbox" title="Ask the coach about this position"></div>
        <details class="box" style="padding:12px"><summary><b>All moves</b> <span class="small muted">click one to see the board there</span></summary>
          <div class="movelist" id="moves" style="margin-top:10px"></div></details>
      </div>
    </div>`;
  const stepPly = (k, st) => st.board === "before" ? k.ply - 1 : k.ply;
  const toArrows = list => list.map(([u, kind, label]) => ({ from: u.slice(0, 2), to: u.slice(2, 4), kind, ...(label ? { label } : {}) }));
  const momentAt = p => moments.findIndex(k => k.ply === p);
  // a move's label: its colour and its mark on the board, like chess.com's icons (22 Oct)
  const LABEL = { Brilliant: ["#26c2a3", "!!"], Best: ["#36c27a", "★"], Excellent: ["#36c27a", "✓"], Good: ["#95b776", "✓"],
    Book: ["#a88865", "≡"], Inaccuracy: ["#f0c15c", "?!"], Mistake: ["#f0a43a", "?"], Blunder: ["#ff4d42", "??"] };
  const ORDER = ["Brilliant", "Best", "Excellent", "Good", "Book", "Inaccuracy", "Mistake", "Blunder"];
  const badge = l => l ? `<span class="mv-label lbl-${l.toLowerCase()}">${LABEL[l][1]} ${l}</span>` : "";
  let view = null;  // a key moment's step picked by hand: its board and arrows, until ◀ ▶ moves on
  function evalbar() {  // your chance to win after this move: the bar fills from your side
    const bar = $("#evalbar"); if (!bar) return;
    const back = said.slice(0, ply).reverse().find(m => m.win != null), win = ply && back ? back.win : 50;
    bar.querySelector("i").style.height = `${win}%`;
    bar.querySelector("span").textContent = `${Math.round(win)}%`;
  }
  function graph() {  // the whole game at a glance: click anywhere to go to that move
    const el = $("#evalgraph"); if (!el || !said.length) return;
    const n = said.length, W = 100, H = 24, x = i => (i / n) * W, y = v => H - (v / 100) * H;
    let last = 50, pts = [`0,${y(50)}`];
    said.forEach((m, i) => { if (m.win != null) last = m.win; pts.push(`${x(i + 1).toFixed(2)},${y(last).toFixed(2)}`); });
    const dots = said.filter(m => ["Mistake", "Blunder", "Brilliant"].includes(m.label) && m.mine)
      .map(m => `<circle cx="${x(m.ply)}" cy="${y(m.win ?? 50)}" r="1.1" fill="${LABEL[m.label][0]}"/>`).join("");
    el.innerHTML = `<svg viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
      <polygon points="0,${H} ${pts.join(" ")} ${W},${H}" class="eg-area"/>
      <line x1="0" y1="${H / 2}" x2="${W}" y2="${H / 2}" class="eg-mid"/>
      <polyline points="${pts.join(" ")}" class="eg-line"/>${dots}
      ${mode ? `<line x1="${x(ply)}" y1="0" x2="${x(ply)}" y2="${H}" class="eg-now"/>` : ""}</svg>`;
    el.onclick = e => { const r = el.getBoundingClientRect(); move(Math.round(((e.clientX - r.left) / r.width) * n)); };
  }
  function board() {
    const k = view ? moments[view[0]] : null, st = k ? k.steps[view[1]] : null, hl = {};
    const at = st ? stepPly(k, st) : ply, pos = g.positions[at], m = said[ply - 1];
    let arrows = st ? toArrows(st.arrows) : [];
    if (!st && ply > 0 && mode && m) arrows = toArrows(m.arrows);
    if (pos.uci) { hl[pos.uci.slice(0, 2)] = "hl-last"; hl[pos.uci.slice(2, 4)] = "hl-last"; }
    const mark = !st && mode && m && m.label && pos.uci ? { sq: pos.uci.slice(2, 4), text: LABEL[m.label][1], color: LABEL[m.label][0] } : null;
    Board.render($("#board"), { fen: pos.fen, flip, highlights: hl, arrows, badge: mark });
    evalbar(); graph();
    let html = "";
    for (let i = 1; i < g.positions.length; i += 2) {
      html += `<span class="n">${(i + 1) / 2}.</span>`;
      for (const j of [i, i + 1]) html += g.positions[j]
        ? `<span data-p="${j}" class="${j === ply ? "cur" : ""} ${keyPly.has(j) ? "key" : ""} ${said[j - 1] && said[j - 1].label ? "lbl-" + said[j - 1].label.toLowerCase() : ""}"
            title="${said[j - 1] && said[j - 1].label ? said[j - 1].label : ""}">${esc(g.positions[j].san)}${said[j - 1] && said[j - 1].sign ? said[j - 1].sign : ""}</span>` : "<span></span>";
    }
    $("#moves").innerHTML = html;
    $("#moves").querySelectorAll("span[data-p]").forEach(el => el.onclick = () => { if (mode !== "key") mode = "game"; move(Number(el.dataset.p)); });
  }
  // the report at the start, like chess.com's: accuracy, and how many of each kind of move, for both of you
  function report() {
    const s = g.summary || {}, you = s.you || { counts: {} }, them = s.them || { counts: {} };
    const acc = v => v == null ? "–" : v.toFixed(1);
    return `<div class="report">
      <div class="rep-acc"><div><b>${acc(you.accuracy)}</b><span>You</span></div><div class="faint">Accuracy</div>
        <div><b>${acc(them.accuracy)}</b><span>${esc(g.opponent)}</span></div></div>
      <table class="rep-counts">${ORDER.filter(l => you.counts[l] || them.counts[l]).map(l => `<tr>
        <td class="num">${you.counts[l] || 0}</td><td>${badge(l)}</td><td class="num">${them.counts[l] || 0}</td></tr>`).join("")}</table>
      ${g.opening ? `<p class="small muted" style="margin:0">Opening: ${esc(g.opening)}</p>` : ""}</div>`;
  }
  const modes = () => `<div class="row">
      <button class="btn small-btn ${mode === "game" ? "primary" : ""}" data-mode="game">Whole game</button>
      ${moments.length ? `<button class="btn small-btn ${mode === "key" ? "primary" : ""}" data-mode="key">Key moments only</button>` : ""}</div>`;
  function draw() {
    board();
    const w = $("#walk");
    if (!mode) {  // the start: the report, and two ways in
      w.innerHTML = `<h2 style="margin:0">Game review</h2>${report()}
        <p class="muted small" style="margin:0">${moments.length ? `${moments.length} key moment${moments.length === 1 ? "" : "s"}` : "No big mistakes"}</p>
        <div class="row"><button class="btn primary" id="startreview">▶ Review the whole game</button>
          ${moments.length ? `<button class="btn" data-mode="key">Key moments only</button>` : ""}</div>`;
      $("#startreview").onclick = () => setMode("game");
      wire(w);
      return;
    }
    const m = said[ply - 1], last = ply === g.positions.length - 1, total = g.move_numbers[g.move_numbers.length - 1];
    const ki = momentAt(ply), k = moments[ki];
    const head = mode === "key" && k ? `Key moment ${ki + 1} of ${moments.length}` : ply ? `Move ${g.move_numbers[ply - 1]} of ${total}` : "The start";
    w.innerHTML = `${modes()}<div class="row spread"><h2 style="margin:0">${head}</h2>
        <span class="small faint">◀ ▶ under the board</span></div>
      <p style="margin:0">${ply && m ? `${badge(m.label)} ${esc(m.text)}` : "The starting position. Press ▶ for the first move."}</p>
      ${last && ending() ? `<p class="small" style="margin:0"><b>The end:</b> ${esc(ending())}</p>` : ""}
      ${k ? `<div class="box keycard" title="${esc([k.habit && "Habit: " + k.habit, k.humans].filter(Boolean).join(" · "))}">
        <div class="row spread"><span class="what">${svg("bolt")} Key moment ${ki + 1}/${moments.length}</span>
          <span class="small bad-text" title="How much of your chance to win this move cost">−${Math.round(k.loss)}%</span></div>
        <div class="kchips">${k.steps.map((st, i) => `<button class="kchip ${view && view[0] === ki && view[1] === i ? "on" : ""}" data-s="${i}" title="${esc(st.text)}">
          <i style="background:${Board.KIND[st.kind].color}"></i>${esc(st.title.replace(/^You played$/, "You").replace(/^They replied$/, "They"))}${st.san ? ` <b>${esc(st.san)}</b>` : ""}</button>`).join("")}</div>
        ${view && view[0] === ki ? `<p class="small" style="margin:0">${esc(k.steps[view[1]].text)}</p>` : ""}
        ${k.hard ? `<p class="small muted" style="margin:0" title="${esc(k.hard)} From the human-move model.">${svg("users")} ${esc(String(k.hard).split(/(?<=\.)\s/)[0])}</p>` : ""}
        ${explained[k.ply] ? `<div class="coach-says">${esc(explained[k.ply])}</div>` : ""}
        <div class="kbtns"><a class="btn primary" href="#/try/${g.id}/${k.ply}">Try again</a>
          ${k.lesson ? `<a class="btn" href="#/course/${k.lesson.id}" title="The lesson: ${esc(k.lesson.title)}">Learn it</a>` : ""}
          ${g.result !== "win" ? `<a class="btn" href="#/rematch/${g.id}/${k.ply}" title="Play on from here against the engine, at their level">Rematch</a>` : ""}
          ${aiReady && !explained[k.ply] ? `<button class="btn" data-explain="${k.ply}" title="The coach explains it in their own words">Explain</button>` : ""}</div></div>` : ""}
      ${last || (mode === "key" && ki === moments.length - 1) ? `<div data-helpful></div>` : ""}`;
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
  function wire(w) { w.querySelectorAll("[data-mode]").forEach(b => b.onclick = () => setMode(b.dataset.mode)); }
  // one move of the game (yours, then theirs): the board after it, and Maya's line about it; on a key moment she
  // explains it there and then. Going back says it again.
  function move(p, speak = true) {
    mode = mode || "game"; view = null;
    ply = Math.max(0, Math.min(g.positions.length - 1, p));
    draw();
    const q = $("#askbox input");  // the question follows the move you're on (22 Oct: not always "my bishop")
    if (q && ply) q.placeholder = `Ask about ${g.move_numbers[ply - 1]}${ply % 2 ? "." : "..."} ${g.positions[ply].san}`;
    const m = said[ply - 1], k = moments[momentAt(ply)];
    let text = !ply || !m ? "The starting position." : m.text;
    if (k) text = (mode === "key" ? `Key moment ${momentAt(ply) + 1}. ` : "Key moment! ") + text + " " + k.steps.slice(2).map(st => st.text).join(" ");
    if (ply === g.positions.length - 1 && ending()) text += ` ${ending()}`;
    if (speak) Coach.react("maya", k || (m && m.kind === "bad") ? "worried" : m && (m.kind === "good" || m.kind === "slip") ? "pleased" : "explain", text);
    return text;
  }
  function setMode(md) {
    mode = md;
    return md === "key" ? move(moments[0].ply) : move(ply || 1);
  }
  // ◀ ▶ (and Next / Back by voice): one move, or one key moment in "Key moments only"; returns what Maya says
  function step(d) {
    if (!mode) return setMode("game");
    if (mode === "key") {
      const at = momentAt(ply), to = at < 0 ? (d > 0 ? moments.findIndex(k => k.ply > ply) : -1) : at + d;
      if (to < 0) return move(moments[0].ply);
      if (to >= moments.length) { const t = "That was the last key moment. Try it again, or review the whole game."; Coach.react("maya", "calm", t); return t; }
      return move(moments[to].ply);
    }
    if (ply + d > g.positions.length - 1) { const t = ending() || "That was the last move."; Coach.react("maya", "calm", t); return t; }
    return move(ply + d);
  }
  window.kwNextStep = () => location.hash.includes(`games/${g.id}`) ? step(1) : null;
  window.kwPly = () => location.hash.includes(`games/${g.id}`) ? ply : null;
  window.kwBackStep = () => location.hash.includes(`games/${g.id}`) ? step(-1) : null;
  askBox($("#askbox"), { placeholder: "Ask Maya about this position", coach: "maya", enabled: aiReady, listen: cfg.talk_ready,
    onAsk: q => { const k = moments[momentAt(ply)]; return api("/api/ask", { question: q, fen: g.positions[ply].fen, game: g.id, ply: k ? k.ply : null }); } });
  document.querySelectorAll("[data-go]").forEach(b => b.onclick = () => {
    const v = b.dataset.go, was = ply;
    if (v === "1" || v === "-1") step(Number(v));
    else if (mode === "key") move(v === "0" ? moments[0].ply : moments[moments.length - 1].ply);
    else move(v === "0" ? 0 : g.positions.length - 1);
    if (ply === was + 1) Sound.move(g.positions[ply].san);
  });
  draw();
  // Maya gives the headline and waits for you: nothing is walked through until you start
  const s = g.summary || {}, acc = s.you && s.you.accuracy != null ? ` Your accuracy: ${Math.round(s.you.accuracy)}.` : "";
  const worst = moments.reduce((a, b) => (b.loss > (a ? a.loss : -1) ? b : a), null);
  if (worst) Coach.react("maya", "explain",
    `${moments.length} key moment${moments.length === 1 ? "" : "s"} in this game; move ${worst.move_number} cost you the most.${acc} ` +
    "Review the whole game with me, or just the key moments.",
    [{ label: "▶ Whole game", run: () => setMode("game") }, { label: "Key moments", run: () => setMode("key") }]);
  else Coach.react("maya", "celebrate", `No big mistakes in this game.${acc} Press Review and we'll go through it move by move.`,
    [{ label: "▶ Review", run: () => setMode("game") }]);
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
  const where = (st.extension_now || []).map(b => names[b] || "your browser"), ever = Object.entries(st.extension_in || {});
  if (where.length) return `<span class="ok-text">Connected in ${where.join(" and ")}</span>`;
  return ever.length ? `<span class="faint">Not connected · last seen ${esc(ever.map(([, t]) => t.slice(11)).sort().pop())}</span><a class="btn" href="#/extension">Set up</a>`
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
  if (!location.hash.startsWith("#/settings")) return;  // a switch answered after you'd left: don't draw Settings over another page
  const was = ($("main") || {}).scrollTop || 0, again = location.hash.startsWith("#/settings") && $("#page .settings-row");
  if (!again) shell("settings", `<p class="muted">Loading…</p>`);
  const [s, st] = await Promise.all([api("/api/settings"), api("/api/status")]);
  if (!location.hash.startsWith("#/settings")) return;
  const aiSet = Object.values(s.slots).some(x => x.set);  // the real key state, never a stale flag
  const slot = (id, n) => {
    const x = s.slots[id], prov = s.providers[x.provider];
    return `<div class="box stack" data-slot="${id}"><div class="row spread"><h3>AI key ${n}</h3>
        <span class="small ${x.set ? "ok-text" : "faint"}">${x.set ? `Saved · ends with ••••${esc(x.ends)}` : "Not set"}</span></div>
      <select class="field" data-provider aria-label="AI key ${n}: provider">${Object.entries(s.providers).map(([k, p]) =>
        `<option value="${k}" ${k === x.provider ? "selected" : ""}>${esc(p.name)}${p.free ? ", free" : ", paid"}</option>`).join("")}</select>
      <input class="field" type="password" autocomplete="off" spellcheck="false" placeholder="${x.set ? "Paste a new key to replace it" : "Paste your API key"}" aria-label="AI key ${n}" data-key>
      <div class="row"><button class="btn" data-save>Save key</button>${x.set ? `<button class="btn" data-test>Test key</button><button class="btn danger" data-remove>Remove</button>` : ""}
        <a class="small muted" data-get href="${esc(prov.get_key)}" target="_blank" rel="noopener">Get a ${esc(prov.name)} key ↗</a></div>
      <div class="err" data-msg></div></div>`;
  };
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>Settings</h1></div></div>
    <div class="box">
      <div class="settings-row"><div><h3 title="Only public games are read. No password.">chess.com account</h3></div>
        <div class="stack"><div class="row"><input class="field" id="user" aria-label="Your chess.com username" value="${esc(st.player || "")}" spellcheck="false" style="max-width:280px">
          <button class="btn" id="saveuser">Change</button></div><div class="err" id="usermsg"></div></div></div>
      <div class="settings-row"><div><h3>Appearance</h3></div>
        <div><div class="seg" id="theme">${["system", "dark", "light"].map(t => `<button data-t="${t}" class="${s.theme === t ? "on" : ""}">${cap(t)}</button>`).join("")}</div></div></div>
      <div class="settings-row"><div><h3 title="Your coaches speak. It runs on this computer, no internet needed.">Voice</h3></div>
        <div class="stack"><div class="row"><button class="switch ${s.voice ? "on" : ""}" id="voice" aria-label="Voice"></button>
          <span class="small muted">${s.voice_ready ? (s.voice ? "On" : "Off") : "Voice files not installed"}</span></div>
          <div class="voices">${Object.entries(COACHES).map(([id, c]) => `<button class="btn voice-chip" data-hear="${id}">
            ${KnightwiseFaces.svg(id, "pleased")}<span><b>${esc(c.name)}</b><small>${esc(c.role)}</small></span><i>▶</i></button>`).join("")}</div>
          <div class="row"><span class="small ${s.talk_ready ? "ok-text" : "muted"}" id="listenstate">${s.talk_ready
            ? "✓ Talk is ready" : "Talking needs a key that can hear: add one below."}</span></div>
          ${s.heard ? `<details class="small muted" id="heard"><summary title="Kept as text on this PC: never the sound, never sent anywhere. It lets the hearing learn the names you use.">What your coaches heard (${s.heard})</summary>
            <div data-lines class="stack" style="gap:2px"></div><button class="btn small-btn" id="forgetheard">Delete all of it</button></details>` : ""}
          ${!s.listen_ready ? `<details class="small muted"><summary title="A one-time 485 MB download. Slower, and it mishears more than a key does.">Hear me on this PC instead</summary>
            <button class="btn" id="getlisten">Install listening on this PC</button></details>` : ""}</div></div>
      <div class="settings-row"><div><h3 title="Moves, right and wrong answers, a finished set. No background music.">Sounds</h3></div>
        <div class="row"><button class="switch ${s.sounds ? "on" : ""}" id="sounds" aria-label="Sounds"></button>
          <span class="small muted">${s.sounds ? "On" : "Off"}</span></div></div>
      ${s.human_ready ? `<div class="settings-row"><div><h3 title="The human-move model plays like real players of any rating, mistakes included: it learned from millions of online games.
        Your rematch and sparring opponents play like people, and reviews say how many players at your level find a move. It's an estimate of a level, never a real person. It runs on this PC.">Human-like opponents</h3></div>
        <div class="row"><button class="switch ${s.human_moves ? "on" : ""}" id="humanmoves" aria-label="Human-like opponents"></button>
          <span class="small muted">${s.human_moves ? "On" : "Off"}</span></div></div>` : ""}
      <div class="settings-row"><div><h3 title="Optional. With a key, the coach explains moves in its own words and answers your questions.
        Without one it uses the engine's built-in sentences. Keys are kept in Windows Credential Manager, encrypted for your Windows account,
        and are only sent to the provider you choose.">AI: talk with your coaches</h3>
        <button class="btn" id="aicompare" style="margin-top:8px">What AI adds</button></div>
        <div class="grid">${slot("slot1", 1)}${slot("slot2", 2)}<p class="note" style="margin:0">Key 2 steps in when key 1 is busy.</p>
          <details class="keyguide"><summary><b>How to get a free key</b> <span class="small muted">about 2 minutes, never shown to anyone else</span></summary>
            <p class="small"><b>Under 18?</b> Ask a parent or guardian to make the key with you: Groq's and Google's terms are for adults, or need a parent's permission.</p>
            <ol class="small">
              <li>Pick a company in Key 1 and press its <b>Get a key ↗</b> link: its site opens in your browser.</li>
              <li>Sign in with a Google account or an email address. It asks for no card and no payment.</li>
              <li>Find <b>API keys</b>, press <b>Create</b>, and name it Knightwise.</li>
              <li>Copy the key it shows. It is shown only once.</li>
              <li>Come back here, paste it into Key 1, and press <b>Save key</b>, then <b>Test key</b>. A green line means it works.</li>
            </ol>
            <p class="small muted">A second company's key goes in Key 2. Keys stay on this PC and go only to the company you picked.</p>
          </details></div></div>
      <div class="settings-row"><div><h3 title="The browser extension.">Arrows on chess.com</h3></div>
        <div class="row">${connectedIn(st)}</div></div>
      <div class="settings-row"><div><h3 title="chess.com changes its site now and then. Knightwise checks everything it uses there, each time.">chess.com check</h3></div>
        <div>${healthRow(st.health)}</div></div>
      <div class="settings-row"><div><h3 title="Games, checks, practice and your logbook.">Your data</h3></div>
        <div class="row"><button class="btn" id="folder">Open data folder</button></div></div>
      <div class="settings-row"><div><h3 title="Free and open source. Fair play: never active in games against real people.">About and credits</h3></div>
        <div class="muted small">Knightwise ${esc((STATUS && STATUS.version) || "")} · GPL-3.0 · <a href="https://github.com/Abhra71/ChessCoach" target="_blank" rel="noopener">GitHub ↗</a>
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
  if (again && $("main")) $("main").scrollTop = was;
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
// a link to the page you're already on draws it again: a page that swaps its content in place (a lesson's practice,
// a set finished) keeps the same address, so "← The lesson" or "Back to …" did nothing (23 Oct test)
function go(to) { const h = "#/" + to; if (location.hash === h) route(); else location.hash = h; }
document.addEventListener("click", e => {
  const a = e.target.closest && e.target.closest('a[href^="#/"]');
  if (a && !e.defaultPrevented && a.getAttribute("href") === location.hash) { e.preventDefault(); route(); }
});
// the round arrow, bottom left: look for new games now, then load the page again (23 Oct test: "reload is not working")
async function kwRefresh() {
  const b = $("#synced"); if (b) b.classList.add("spin");
  await api("/api/check-now", {}).catch(() => {});
  location.reload();
}
async function screen(name, arg) {
  if (name === "plan") return await planView(arg);
  if (name === "games" && arg) return await gameView(arg);
  if (name === "games") return await games();
  if (name === "practice") return await practice(arg && decodeURIComponent(arg));
  if (name === "daily") return await daily();
  if (name === "progress") return await progressView();
  if (name === "level") return await levelView();
  if (name === "train") return trainView();
  toolIntro(name);
  if (name === "course" && arg) return await courseLesson(decodeURIComponent(arg));
  if (name === "course") return await courseView();
  if (name === "endgames") return await endgamesView();
  if (name === "calc") return await calcView();
  if (name === "guess") return await guessView();
  if (name === "film") return await filmView(arg && decodeURIComponent(arg));
  if (name === "report") return await reportView(arg);
  if (name === "blindfold") return await blindfoldView();
  if (name === "repertoire" && arg) { shell("train", `<p class="muted">Loading…</p>`); return lessonView({ ...(await api(`/api/repertoire/${arg}`)), back: "repertoire" }); }
  if (name === "repertoire") return await repertoireView();
  if (name === "prep") return await prepView(arg && decodeURIComponent(arg));
  if (name === "punish") return await punishView(decodeURIComponent(arg || ""));
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
function intro(name) {  // a small ? by the page's title, not a card on the page (22 Oct: the calm look)
  const it = INTRO[name], page = $("#page"), h1 = page && page.querySelector("h1");
  if (!it || !h1 || h1.querySelector(".help-q")) return;
  const q = document.createElement("button");
  q.className = "help-q" + (remember(`kw-intro-${name}`) === "seen" ? "" : " new");
  q.title = it[1]; q.textContent = "?"; q.setAttribute("aria-label", `What is ${it[0]}?`);
  q.onclick = e => {
    e.preventDefault(); remember(`kw-intro-${name}`, "seen"); q.classList.remove("new");
    const old = page.querySelector(".help-pop"); if (old) { old.remove(); return; }
    const pop = document.createElement("div"); pop.className = "help-pop"; pop.textContent = it[1];
    h1.after(pop);
  };
  h1.appendChild(q);
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
    const asked = location.hash;
    await screen(name, arg);
    // a slow page finished after you'd moved on: it may have drawn over the page you're on, so draw that one again
    // (23 Oct chaos test)
    if (location.hash !== asked) return route();
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

// ---------- Train: every training tool on one page, each one a picture and a few words (22 Oct) ----------
// The owner: "the flagships feel hidden… I myself did not understand what each does, how do we manage without
// injecting boring text". Each card shows what it does; the coach says one sentence the first time you open one.
const TRAIN = [
  ["Before a game", "#e9a23b", [
    ["prep", "search", "Prep", "Know them before you play", "maya", "Type any chess.com name. I'll show how they open and how their games end, then you can spar their style."],
    ["openings", "tree", "Opening tree", "How your games start", "maya", "Every game you played, branching from move one. Green is where you score well, red where you lose."],
    ["repertoire", "book", "Repertoire", "Three lines, by heart", "viktor", "Three opening lines picked from what you already play. Learn them to move six and every game starts on your terms."],
  ]],
  ["Sharpen your eye", "#5ea4e8", [
    ["calc", "sparkles", "In your head", "See the whole line first", "viktor", "This trains seeing ahead. The pieces stay still: click your move, their best reply, then your next move. Then press Check my line."],
    ["blindfold", "ear", "Blindfold", "Hear it, see it, no board", "viktor", "I read out the start of one of your games. Follow it in your head, then answer on the board."],
    ["guess", "users", "Guess the move", "What would they play?", "viktor", "Five real positions a week. Guess what most players of that rating play: the closer, the more points."],
    ["endgames", "mate", "Endgames", "Win the won games", "viktor", "The endings every player must know, against perfect defence. Learn them once, keep them for life."],
  ]],
];
const TRAIN_PIC = {  // what each tool looks like, drawn small
  prep: `<div class="tp-bars"><i style="height:52px;background:#81b64c"></i><i style="height:20px;background:#a6a19a"></i><i style="height:34px;background:#e5734f"></i></div>`,
  openings: `<svg viewBox="0 0 110 70" width="110" height="70"><circle cx="12" cy="35" r="6" fill="#f3f1ee"/><path d="M18 35 48 15M18 35h30M18 35l30 20" stroke="#807a72" stroke-width="2"/><circle cx="52" cy="15" r="5" fill="#81b64c"/><circle cx="52" cy="35" r="5" fill="#a6a19a"/><circle cx="52" cy="55" r="5" fill="#e5734f"/><path d="M57 15 88 8M57 15l31 7" stroke="#807a72" stroke-width="2"/><circle cx="92" cy="8" r="4" fill="#81b64c"/><circle cx="92" cy="22" r="4" fill="#a6a19a"/></svg>`,
  repertoire: { fen: "r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4" },
  spar: `<div class="tp-vs">${"<svg viewBox='0 0 24 24' width='30' height='30' fill='none' stroke='#f3f1ee' stroke-width='1.8'><circle cx='12' cy='8' r='4'/><path d='M4 21a8 8 0 0 1 16 0'/></svg>"}<span>vs</span>${"<svg viewBox='0 0 24 24' width='30' height='30' fill='none' stroke='#a6a19a' stroke-width='1.8'><circle cx='12' cy='8' r='4'/><path d='M4 21a8 8 0 0 1 16 0'/></svg>"}</div>`,
  calc: { fen: "6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1", arrows: [{ from: "d1", to: "d8", kind: "better" }] },
  blindfold: { fen: "8/8/8/8/8/8/8/8 w - - 0 1", ear: true },
  guess: `<div class="tp-bars"><i style="height:14px"></i><i style="height:48px;background:#5ea4e8"></i><i style="height:26px"></i><i style="height:8px"></i></div>`,
  endgames: { fen: "8/8/4k3/8/4P3/4K3/8/8 w - - 0 1" },
};
function trainView() {
  shell("train", "");
  $("#page").innerHTML = `<div class="page-head"><div><h1>Train</h1></div></div>
    ${TRAIN.map(([group, colour, tools]) => `<div class="tgroup">${esc(group)}</div>
      <div class="tcards" style="--n:${tools.length}">${tools.map(([route, icon, name, line]) => `<a class="box tcard" href="#/${route === "spar" ? "prep" : route}">
        <div class="tpic" data-pic="${route}"></div>
        <b class="tname"><span style="color:${colour}">${svg(icon)}</span>${esc(name)}</b><span class="muted small">${esc(line)}</span></a>`).join("")}</div>`).join("")}`;
  document.querySelectorAll("[data-pic]").forEach(el => {
    const p = TRAIN_PIC[el.dataset.pic];
    if (typeof p === "string") { el.innerHTML = p; return; }
    const b = document.createElement("div"); b.className = "mini-board"; el.appendChild(b);
    Board.render(b, { fen: p.fen, arrows: p.arrows || [] });
    if (p.ear) el.insertAdjacentHTML("beforeend", `<span class="tp-ear">${svg("ear")}</span>`);
  });
  Coach.react("viktor", "explain", "Your training tools. Pick one: I'll tell you what it does the first time.");
}
// the first time you open a tool, its coach says what it's for, in one or two sentences (spoken, not written)
function toolIntro(name) {
  const t = TRAIN.flatMap(g => g[2]).find(x => x[0] === name);
  if (!t) return;
  try { if (localStorage.getItem(`kw-tool-${name}`)) return; localStorage.setItem(`kw-tool-${name}`, "1"); } catch (e) { return; }
  setTimeout(() => Coach.react(t[4], "explain", t[5]), 900);
}

// Long page intros fold into a small ? by the title, on every page (22 Oct: "keep as less text as possible, with
// some space to breathe"). Short lines, like a game's date and result, stay as they are.
const HINT_LEN = 90;
function foldIntros() {
  document.querySelectorAll("#page .page-head .sub:not([data-folded])").forEach(p => {
    p.dataset.folded = "1";
    const h1 = p.closest(".page-head").querySelector("h1");
    if (!h1 || p.textContent.trim().length <= HINT_LEN || h1.querySelector(".help-q")) return;
    const q = document.createElement("button");
    q.className = "help-q"; q.textContent = "?"; q.title = p.textContent.trim(); q.setAttribute("aria-label", "What is this page?");
    p.hidden = true;
    q.onclick = e => { e.preventDefault(); p.hidden = !p.hidden; };
    h1.appendChild(q);
  });
}
new MutationObserver(() => foldIntros()).observe(document.getElementById("root") || document.body, { childList: true, subtree: true });

// A badge completed: the banner (same as on chess.com). The server picks when; this shows it and says it was seen,
// so chess.com doesn't show it again.
function badgeUnlocked(b) {
  if (!b) return;
  api("/api/badges/shown", { id: b.id }).catch(() => {});
  kwBadgeBanner(b, { esc, sound: Sound.on });
}
const MEDAL = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="14" r="6"/><path d="M8.5 3h7l-2 5.5h-3z"/><path d="m12 11.5.9 1.8 2 .3-1.45 1.4.35 2-1.8-.95-1.8.95.35-2-1.45-1.4 2-.3z"/></svg>`;
// A badge completed (Gold): a banner slides down at the top, nothing blurred or covered (23 Oct test). The medal
// fills from silver to gold, a chime and confetti; the close button appears when that's done, and the banner goes
// by itself 5 seconds later.
function kwBadgeBanner(b, opts) {
  if (!b || document.querySelector(".kwb")) return;
  const o = opts || {}, FILL_AT = 900, FILL = 950, DONE = FILL_AT + FILL + 150, STAY = o.stay || 5000;
  const el = document.createElement("div");
  el.className = "kwb";
  el.setAttribute("role", "status");
  const STAR = `<svg viewBox="0 0 24 24" fill="currentColor"><path d="m12 2 2.9 6.6 7.1.6-5.4 4.7 1.7 7-6.3-3.8-6.3 3.8 1.7-7L2 9.2l7.1-.6z"/></svg>`;
  el.innerHTML = `<div class="kwb-medal"><div class="kwb-coin"><div class="kwb-m kwb-silver">${MEDAL}</div><div class="kwb-m kwb-gold">${MEDAL}</div></div>
      ${Array.from({ length: 8 }, (_, i) => `<span class="kwb-star" style="--i:${i};--a:${i * 45}deg">${STAR}</span>`).join("")}</div>
    <div class="kwb-text"><div class="kwb-label">Badge complete · <b>Gold</b></div>
      <div class="kwb-name">${o.esc(b.name)}</div>
      <div class="kwb-what"><b>${o.esc(String(b.gold))}</b> ${o.esc(b.what)} · earned in ${o.esc(b.from)}</div></div>
    <button class="kwb-x" aria-label="Close" title="Close">✕<svg viewBox="0 0 48 48"><circle cx="24" cy="24" r="21"/></svg></button>`;
  el.style.setProperty("--stay", STAY / 1000 + "s");  // the ring round the close button runs down these seconds
  document.body.appendChild(el);
  let gone = false;
  const close = () => { if (gone) return; gone = true; el.classList.add("out"); setTimeout(() => el.remove(), 350); };
  el.querySelector(".kwb-x").onclick = close;
  requestAnimationFrame(() => el.classList.add("in"));
  setTimeout(() => { el.classList.add("fill"); if (o.sound !== false) kwChime(); }, FILL_AT);
  setTimeout(() => { el.classList.add("gold"); kwBurst(el); }, FILL_AT + FILL);
  setTimeout(() => el.classList.add("done"), DONE);  // the close button only now
  setTimeout(close, DONE + STAY);
}
function kwChime() {  // three rising notes and a shimmer, made here: no sound file
  try {
    const ac = new (window.AudioContext || window.webkitAudioContext)(), t0 = ac.currentTime + 0.02;
    [[659.25, 0], [830.61, 0.12], [987.77, 0.24], [1318.5, 0.38]].forEach(([f, at], i) => {
      const osc = ac.createOscillator(), g = ac.createGain();
      osc.type = i === 3 ? "sine" : "triangle"; osc.frequency.value = f;
      g.gain.setValueAtTime(0, t0 + at); g.gain.linearRampToValueAtTime(i === 3 ? 0.12 : 0.18, t0 + at + 0.02);
      g.gain.exponentialRampToValueAtTime(0.001, t0 + at + (i === 3 ? 1.2 : 0.5));
      osc.connect(g).connect(ac.destination); osc.start(t0 + at); osc.stop(t0 + at + 1.3);
    });
    setTimeout(() => ac.close(), 1800);
  } catch (e) {}
}
function kwBurst(el) {  // confetti from the medal, falling over the page
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const r = el.querySelector(".kwb-medal").getBoundingClientRect(), layer = document.createElement("div");
  layer.className = "kwb-confetti";
  const colours = ["#f2c94c", "#81b64c", "#ffffff", "#e5734f", "#5ea4e8"];
  for (let i = 0; i < 60; i++) {
    const p = document.createElement("i");
    p.style.cssText = `left:${r.left + r.width / 2}px;top:${r.top + r.height / 2}px;background:${colours[i % colours.length]};` +
      `--dx:${(Math.random() - .3) * 700}px;--dy:${120 + Math.random() * 420}px;--r:${Math.random() * 720}deg;animation-delay:${Math.random() * .12}s`;
    layer.appendChild(p);
  }
  document.body.appendChild(layer);
  setTimeout(() => layer.remove(), 2000);
}
