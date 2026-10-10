// Chess Coach desktop app: one page, a few screens (#/home, #/games, #/practice, #/settings, #/welcome).
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
  settings: '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1 7 17M17 7l2.1-2.1"/>',
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

let STATUS = {};

// ---------- theme ----------
function applyTheme(theme) {
  if (theme === "dark" || theme === "light") document.documentElement.dataset.theme = theme;
  else delete document.documentElement.dataset.theme;
}

// ---------- voice ----------
const Voice = (() => {  // the coach speaks sentence by sentence; the next one is made while this one plays
  let on = true, playing = null, token = 0;
  const split = t => String(t).replace(/\s+/g, " ").split(/(?<=[.!?])\s+/).filter(Boolean);
  const audio = text => fetch("/api/say", { method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }) }).then(r => { if (!r.ok) throw new Error("voice"); return r.blob(); }).then(b => URL.createObjectURL(b));
  const play = url => new Promise(done => { const a = new Audio(url); playing = a; a.onended = a.onerror = done; a.play().catch(done); });
  function stop() { token++; if (playing) { playing.pause(); playing = null; } }
  async function speak(text, force) {
    stop();
    if ((!on && !force) || !text) return;
    const mine = ++token, parts = split(text);
    let next = audio(parts[0]);
    for (let i = 0; i < parts.length; i++) {
      let url;
      try { url = await next; } catch (e) { return; }
      if (mine !== token) return;
      if (i + 1 < parts.length) next = audio(parts[i + 1]);
      await play(url);
      if (mine !== token) return;
    }
  }
  return { speak, stop, set(v) { on = v; if (!v) stop(); }, get on() { return on; } };
})();

// ---------- shell ----------
function shell(active, body) {
  const item = (route, name, icon) =>
    `<a href="#/${route}" class="${active === route ? "on" : ""}">${svg(icon)}<span>${name}</span></a>`;
  $("#root").innerHTML = `
    <div class="shell">
      <aside class="side">
        <div class="brand"><div class="brand-mark" style="color:var(--on-invert)">${svg("pawn")}</div><span>Chess Coach</span></div>
        <nav class="nav">${item("home", "Home", "home")}${item("games", "Games", "games")}${item("practice", "Practice", "practice")}${item("settings", "Settings", "settings")}</nav>
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
function trendChart(points, window) {
  if (points.length < 2) return `<p class="muted">The trend appears after ${window * 2} games.</p>`;
  const W = 600, H = 140, pad = 24, max = Math.max(...points, 1) * 1.15;
  const x = i => pad + i * (W - pad * 2) / (points.length - 1), y = v => H - pad - v / max * (H - pad * 2);
  const d = points.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
  const dots = points.map((v, i) => `<circle class="pt ${i === points.length - 1 ? "last" : ""}" cx="${x(i)}" cy="${y(v)}" r="3.2"/>`).join("");
  return `<svg class="chart" viewBox="0 0 ${W} ${H}" preserveAspectRatio="none">
    <line class="axis" x1="${pad}" y1="${H - pad}" x2="${W - pad}" y2="${H - pad}"/>
    <path class="line" d="${d}"/>${dots}
    <text x="${pad}" y="${H - 6}">oldest</text><text x="${W - pad}" y="${H - 6}" text-anchor="end">now</text></svg>`;
}

async function home() {
  shell("home", `<p class="muted">Loading…</p>`);
  const h = await api("/api/home");
  if (!h.player) return go("welcome");
  const hour = new Date().getHours(), hello = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const f = h.focus, last = h.last_game, r = h.results || {};
  const better = h.pieces_last20 < h.pieces_per_game;
  const maxP = Math.max(...h.patterns.map(p => p.times), 1);
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>${hello}, ${esc(h.player)}</h1>
      <p class="sub">${h.games} games checked by Stockfish${STATUS.last_update ? " · last check " + esc(STATUS.last_update) : ""}</p></div>
      <div class="row"><button class="btn" id="brief">Hear your briefing</button><a class="btn primary" href="#/practice">Start practice</a></div></div>
    <div class="grid">
      ${f ? `<div class="box focus"><div class="label">Your focus</div>
        <h3 style="font-size:22px;margin:6px 0 8px">${esc(PATTERN_TITLE[f.pattern] || cap(f.pattern))}</h3>
        <p class="muted" style="margin:0 0 6px">${esc(f.meaning)}</p>
        <p style="margin:0 0 14px"><b>The habit:</b> ${esc(f.habit)}</p>
        <div class="row small muted"><span class="num">${f.times} times in ${f.games} of your ${h.games} games</span></div></div>` : ""}
      <div class="grid cols-3">
        <div class="box"><div class="big num">${h.pieces_per_game.toFixed(1)}</div><div class="stat-label">Pieces given away per game</div>
          <div class="delta ${better ? "good" : "bad"} num">${h.pieces_last20.toFixed(1)} in your last 20 · ${better ? "better" : "worse"}</div></div>
        <div class="box"><div class="big num">${h.rating ?? "–"}</div><div class="stat-label">${cap(h.rating_class || "")} rating on chess.com</div></div>
        <div class="box"><div class="big num">${r.win || 0}<span class="faint"> / </span>${r.loss || 0}<span class="faint"> / </span>${r.draw || 0}</div>
          <div class="stat-label">Won / lost / drawn</div></div>
      </div>
      <div class="grid cols-2">
        <div class="box"><h2>Pieces given away, per ${h.trend_window} games</h2>${trendChart(h.trend, h.trend_window)}
          <p class="note">Lower is better. The red dot is now.</p></div>
        <div class="box"><h2>Where your games go wrong</h2><div class="stack">
          ${h.patterns.map((p, i) => `<div><div class="row spread small"><span>${esc(cap(p.pattern))}</span><span class="num muted">${p.times}</span></div>
            <div class="bar ${i === 0 ? "red" : ""}"><div style="width:${100 * p.times / maxP}%"></div></div></div>`).join("")}</div></div>
      </div>
      ${last ? `<div class="box row spread"><div><h2 style="margin-bottom:6px">Your last game</h2>
          <h3>vs ${esc(last.opponent)} <span class="faint">(${last.opponent_rating})</span> · <span class="${last.result === "loss" ? "delta bad" : ""}">${cap(last.result)}</span></h3>
          <p class="sub">${esc(last.date)} · ${esc(last.time_class)} · ${last.pieces_lost} pieces given away · ${last.moments} key moments</p></div>
        <a class="btn" href="#/games/${last.id}">Review game</a></div>` : ""}
      <p class="note">Practice so far: ${h.practice.answers} answers, ${h.practice.right} right first time, ${h.practice.learned} positions learned.</p>
    </div>`;
  const briefing = [`${hello}, ${h.player}.`,
    f ? `Your focus is: ${PATTERN_TITLE[f.pattern] || f.pattern}. It happened ${f.times} times, in ${f.games} of your ${h.games} games.` : "",
    f ? f.habit : "",
    `You give away ${h.pieces_per_game.toFixed(1)} pieces per game, and ${h.pieces_last20.toFixed(1)} in your last 20 games${better ? ", which is better" : ""}.`,
    last ? `Your last game was a ${last.result} against ${last.opponent}, with ${last.moments} key moments to look at.` : ""].join(" ");
  $("#brief").onclick = () => Voice.speak(briefing, true);
}

// ---------- games ----------
async function games() {
  shell("games", `<p class="muted">Loading…</p>`);
  const list = await api("/api/games");
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>Games</h1><p class="sub">${list.length} finished games from chess.com. Click one to see its key moments.</p></div></div>
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

async function gameView(id) {
  shell("games", `<p class="muted">Loading…</p>`);
  const g = await api(`/api/games/${id}`);
  const flip = g.color === "black", keyPly = new Set(g.key_moments.map(m => m.ply));
  let ply = g.key_moments.length ? g.key_moments[0].ply - 1 : g.positions.length - 1, view = "before";
  $("#page").innerHTML = `
    <div class="page-head"><div><a href="#/games" class="small muted" style="text-decoration:none">← Games</a>
      <h1 style="margin-top:6px">vs ${esc(g.opponent)} <span class="faint">(${g.opponent_rating})</span></h1>
      <p class="sub">${cap(g.result)} · ${esc(g.date)} · ${esc(g.time_class)} · you were ${g.color}${g.opening ? " · " + esc(g.opening) : ""}</p></div>
      <a class="btn" href="${esc(g.url)}" target="_blank" rel="noopener">Open on chess.com ↗</a></div>
    <div class="game-layout">
      <div><div class="board-wrap" id="board"></div>
        <div class="controls"><button class="btn" data-go="0">⏮</button><button class="btn" data-go="-1">◀</button>
          <button class="btn" data-go="1">▶</button><button class="btn" data-go="end">⏭</button></div>
        <div style="margin-top:12px">${Board.legend(["better", "mine", "reply"])}</div></div>
      <div class="stack">
        <h2>${g.key_moments.length ? `${g.key_moments.length} key moments` : "No big mistakes in this game"}</h2>
        <div class="stack" id="moments"></div>
        <div class="box" style="padding:12px"><h2>Moves</h2><div class="movelist" id="moves"></div></div>
      </div>
    </div>`;
  const momentAt = p => g.key_moments.find(m => m.ply === p + 1 && view === "before") || g.key_moments.find(m => m.ply === p && view === "after");
  function draw() {
    const pos = g.positions[ply], m = momentAt(ply), hl = {};
    if (pos.uci && !m) { hl[pos.uci.slice(0, 2)] = "hl-last"; hl[pos.uci.slice(2, 4)] = "hl-last"; }
    const arrows = !m ? [] : view === "before"
      ? [{ from: m.best_uci.slice(0, 2), to: m.best_uci.slice(2, 4), kind: "better" }, { from: m.move_uci.slice(0, 2), to: m.move_uci.slice(2, 4), kind: "mine" }]
      : [{ from: m.move_uci.slice(0, 2), to: m.move_uci.slice(2, 4), kind: "mine" }].concat(m.reply_uci ? [{ from: m.reply_uci.slice(0, 2), to: m.reply_uci.slice(2, 4), kind: "reply" }] : []);
    Board.render($("#board"), { fen: pos.fen, flip, highlights: hl, arrows });
    $("#moments").innerHTML = g.key_moments.map((k, i) => `<div class="moment ${k === m ? "on" : ""}" data-i="${i}">
      <div class="row spread"><span class="what">Move ${k.move_number} · ${esc(cap(k.pattern))}</span><span class="small faint">−${Math.round(k.loss)}%</span></div>
      <div style="margin-top:4px">${esc(k.say)}</div>
      ${k === m ? `<div class="small muted" style="margin-top:6px">${view === "before" ? `Better: <b>${esc(k.best)}</b> · you played <b>${esc(k.move)}</b>` : `You played <b>${esc(k.move)}</b>, and their reply wins material.`}</div>
        ${k.habit ? `<div class="small" style="margin-top:6px"><b>Habit:</b> ${esc(k.habit)}</div>` : ""}
        <button class="btn" style="margin-top:10px" data-view="${view === "before" ? "after" : "before"}">${view === "before" ? "What happened next" : "Show the better move"}</button>` : ""}
    </div>`).join("");
    $("#moments").querySelectorAll(".moment").forEach(el => el.onclick = e => {
      const k = g.key_moments[Number(el.dataset.i)];
      view = e.target.dataset.view || "before";
      ply = view === "before" ? k.ply - 1 : k.ply; draw();
      Voice.speak(view === "before"
        ? `Move ${k.move_number}. ${cap(k.pattern)}. ${k.say} The better move was ${k.best}.`
        : `You played ${k.move}. Watch their reply.`);
    });
    let html = "";
    for (let i = 1; i < g.positions.length; i += 2) {
      html += `<span class="n">${(i + 1) / 2}.</span>`;
      for (const j of [i, i + 1]) html += g.positions[j]
        ? `<span data-p="${j}" class="${j === ply ? "cur" : ""} ${keyPly.has(j) ? "key" : ""}">${esc(g.positions[j].san)}</span>` : "<span></span>";
    }
    $("#moves").innerHTML = html;
    $("#moves").querySelectorAll("span[data-p]").forEach(s => s.onclick = () => { ply = Number(s.dataset.p); view = "after"; draw(); });
  }
  document.querySelectorAll("[data-go]").forEach(b => b.onclick = () => {
    const v = b.dataset.go; view = "before";
    ply = v === "0" ? 0 : v === "end" ? g.positions.length - 1 : Math.max(0, Math.min(g.positions.length - 1, ply + Number(v)));
    draw();
  });
  draw();
}

// ---------- practice ----------
async function practice() {
  shell("practice", `<p class="muted">Loading…</p>`);
  const drills = await api("/api/practice-set").catch(() => []);
  if (!drills.length) { $("#page").innerHTML = `<div class="empty">Practice appears once your games are checked.</div>`; return; }
  let i = 0, k = 0, pieces = {}, picked = null, done = false, missed = false, last = {}, right = 0;
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>Practice</h1><p class="sub">Your own positions (the move before a big mistake) and puzzles on the same habits.</p></div>
      <span class="muted num" id="count"></span></div>
    <div class="game-layout">
      <div><div class="board-wrap" id="board"></div><p class="small muted" id="where" style="margin-top:10px"></p></div>
      <div class="stack"><div class="box"><div class="label" id="kind"></div><h3 id="task" style="margin:6px 0 10px"></h3>
        <p class="muted" id="hint" style="margin:0"></p></div>
        <div class="box" id="result" style="min-height:84px"><span class="muted">Click a piece, then the square to move it to.</span></div>
        <div class="row"><button class="btn" id="show">Show answer</button><button class="btn primary" id="next">Next position</button></div>
        <p class="note" id="stats"></p></div>
    </div>`;
  const d = () => drills[i], step = () => d().steps[k];
  const mark = (sqs, cls) => Object.fromEntries(sqs.map(s => [s, cls]));
  const mine = sym => (sym === sym.toUpperCase()) === !d().flip;
  function draw(hl = {}, targets = []) { Board.render($("#board"), { pieces, flip: d().flip, highlights: { ...last, ...hl }, targets, onClick: click }); }
  function result(cls, html) { $("#result").innerHTML = `<div class="${cls}">${html}</div>`; }
  async function show() {
    k = 0; picked = null; done = false; missed = false; last = {};
    const x = d();
    $("#count").textContent = `${i + 1} of ${drills.length} · ${right} right first time`;
    $("#kind").textContent = x.kind === "game" ? "From your game" : "Puzzle";
    $("#task").textContent = x.intro; $("#hint").textContent = x.hint;
    $("#where").innerHTML = `${esc(x.where)} · <a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.link)} ↗</a>`;
    result("muted", "Click a piece, then the square to move it to.");
    pieces = x.start; draw();
    Voice.speak(x.intro);
    if (x.last) { done = true; await wait(700); if (d() !== x) return; pieces = x.steps[0].board; last = mark(x.last, "hl-last"); draw(); done = false; }
  }
  async function good(uci, m, shown) {
    const x = d(), s = step();
    pieces = m.after; last = {}; draw(mark([uci.slice(0, 2), uci.slice(2, 4)], "hl-ok"));
    if (s.reply) {
      done = true; result("ok-text", `<b>${esc(m.san)}</b>: yes. Now they play ${esc(s.reply.san)}. Keep going.`);
      await wait(800); if (d() !== x) return;
      pieces = s.reply.board; last = mark([s.reply.uci.slice(0, 2), s.reply.uci.slice(2, 4)], "hl-last"); k++; done = false; draw();
      if (shown) answer(); return;
    }
    done = true; if (!missed) right++;
    $("#count").textContent = `${i + 1} of ${drills.length} · ${right} right first time`;
    const note = x.kind === "game" ? `In the game you played ${esc(x.played)}.${m.san === x.best ? "" : " The engine's top move was " + esc(x.best) + "."}` : "Puzzle solved.";
    result("ok-text", `<b>${esc(m.san)}</b>: ${shown ? "that's the answer." : x.kind === "game" ? "yes, that keeps you safe." : "correct."}<div class="muted small" style="margin-top:4px">${note}</div>`);
    Voice.speak(shown ? `The answer is ${m.san}.` : x.kind === "game" ? `Yes. ${m.san} keeps you safe.` : `Correct, ${m.san}.`);
    api("/api/practice", { id: x.id, kind: x.kind, right: !missed }).then(stats).catch(() => {});
  }
  function click(sq) {
    if (done) return;
    const sym = pieces[sq];
    if (sym && mine(sym)) {
      picked = sq;
      return draw({ [sq]: "hl-pick" }, Object.keys(step().moves).filter(u => u.startsWith(sq)).map(u => u.slice(2, 4)));
    }
    if (!picked) return;
    const uci = step().moves[picked + sq] ? picked + sq : picked + sq + "q", m = step().moves[uci];
    picked = null;
    if (!m) return draw();
    if (m.good) return good(uci, m, false);
    missed = true;
    result("", `<b class="delta bad" style="font-size:14px">${esc(m.san)}: not quite.</b><div style="margin-top:4px">${esc(m.say)}</div><div class="small muted" style="margin-top:4px">Try again.</div>`);
    Voice.speak(`Not quite. ${m.say} Try again.`);
    draw(mark([uci.slice(0, 2), uci.slice(2, 4)], "hl-no"));
  }
  function answer() {
    const entries = Object.entries(step().moves).filter(([, m]) => m.good);
    const pick = (d().kind === "game" && entries.find(([, m]) => m.san === d().best)) || entries[0];
    missed = true; good(pick[0], pick[1], true);
  }
  function stats(s) { if (s && s.answers) $("#stats").textContent = `So far: ${s.right} of ${s.answers} right first time · ${s.learned} positions learned (right 3 times, days apart).`; }
  $("#show").onclick = () => { if (!done) answer(); };
  $("#next").onclick = () => { i = (i + 1) % drills.length; show(); };
  api("/api/stats").then(stats).catch(() => {});
  show();
}

// ---------- settings ----------
async function settingsView() {
  shell("settings", `<p class="muted">Loading…</p>`);
  const [s, st] = await Promise.all([api("/api/settings"), api("/api/status")]);
  const slot = (id, n) => {
    const x = s.slots[id], prov = s.providers[x.provider];
    return `<div class="box stack" data-slot="${id}"><div class="row spread"><h3>AI key ${n}</h3>
        <span class="small ${x.set ? "ok-text" : "faint"}">${x.set ? `Saved · ends with ••••${esc(x.ends)}` : "Not set"}</span></div>
      <select class="field" data-provider>${Object.entries(s.providers).map(([k, p]) =>
        `<option value="${k}" ${k === x.provider ? "selected" : ""}>${esc(p.name)}${p.free ? " (has a free tier)" : ""}</option>`).join("")}</select>
      <input class="field" type="password" autocomplete="off" spellcheck="false" placeholder="${x.set ? "Paste a new key to replace it" : "Paste your API key"}" data-key>
      <div class="row"><button class="btn primary" data-save>Save key</button>${x.set ? `<button class="btn danger" data-remove>Remove</button>` : ""}
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
      <div class="settings-row"><div><h3>Voice</h3><p class="note">The coach speaks its explanations. It runs on this computer (Kokoro), no internet needed.</p></div>
        <div class="stack"><div class="row"><button class="switch ${s.voice ? "on" : ""}" id="voice" aria-label="Voice"></button>
          <span class="small muted">${s.voice_ready ? (s.voice ? "On" : "Off") : "Voice files not installed"}</span></div>
          <div class="row"><select class="field" id="voicename" style="max-width:240px">${Object.entries(s.voices).map(([k, v]) =>
            `<option value="${k}" ${k === s.voice_name ? "selected" : ""}>${esc(v)}</option>`).join("")}</select>
          <button class="btn" id="sample">Play sample</button></div></div></div>
      <div class="settings-row"><div><h3>AI explanations</h3><p class="note">Optional. With a key, the coach explains moves in its own words and answers your questions.
        Without one it uses the engine's built-in sentences. Keys are kept in Windows Credential Manager, encrypted for your Windows account,
        and are only sent to the provider you choose.</p></div>
        <div class="grid">${slot("slot1", 1)}${slot("slot2", 2)}<p class="note">Key 2 is used when key 1 fails or runs out.</p></div></div>
      <div class="settings-row"><div><h3>Arrows on chess.com</h3><p class="note">The browser extension.</p></div>
        <div class="row"><span class="${st.extension_seen ? "ok-text" : "faint"}">${st.extension_seen ? "Connected" : "Not connected yet"}</span>
          <a class="btn" href="/setup-arrows">Set up</a></div></div>
      <div class="settings-row"><div><h3>Your data</h3><p class="note">Games, checks, practice and your logbook.</p></div>
        <div class="row"><button class="btn" id="folder">Open data folder</button></div></div>
      <div class="settings-row"><div><h3>About</h3></div>
        <div class="muted small">Chess Coach · beta · open source (GPL-3.0) · <a href="https://github.com/Abhra71/ChessCoach" target="_blank" rel="noopener">GitHub ↗</a><br>
          Engine: Stockfish 19 · Puzzles: Lichess (CC0) · Fair play: never active in games against real people.</div></div>
    </div>`;
  $("#theme").querySelectorAll("button").forEach(b => b.onclick = async () => {
    const r = await api("/api/settings", { theme: b.dataset.t }); applyTheme(r.theme); settingsView();
  });
  $("#voice").onclick = async () => { await api("/api/settings", { voice: !s.voice }); Voice.set(!s.voice); settingsView(); };
  const SAMPLE = "Hi, I'm your chess coach. Before every move, ask: what can they take?";
  $("#voicename").onchange = async e => { await api("/api/settings", { voice_name: e.target.value }); Voice.speak(SAMPLE, true); };
  $("#sample").onclick = () => Voice.speak(SAMPLE, true);
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
    const rm = $("[data-remove]", box);
    if (rm) rm.onclick = async () => { if (confirm("Remove this key?")) { await api("/api/keys/remove", { slot: id }); settingsView(); } };
  });
}

// ---------- welcome ----------
async function welcome() {
  $("#root").innerHTML = `<div class="onboard"><div class="backdrop" id="backdrop"></div>
    <div class="card" id="card"></div></div>`;
  if (window.Backdrop) window.Backdrop.mount($("#backdrop"));
  const card = $("#card");
  const dots = n => `<div class="steps-dots">${[0, 1, 2].map(i => `<i class="${i <= n ? "on" : ""}"></i>`).join("")}</div>`;
  function intro() {
    card.innerHTML = `${dots(0)}<h1>Your chess coach</h1>
      <p class="muted" style="margin-top:8px">It studies your finished chess.com games, finds the one or two habits that cost you the most, and trains you out of them.</p>
      <div class="does"><div><b>It does</b><ul><li>Check every move of your finished games with Stockfish</li>
        <li>Show the key moments, with arrows</li><li>Train you on your own positions</li><li>Run quietly and check each new game</li></ul></div>
        <div class="no"><b>It never</b><ul><li>Helps during a game against a real person</li><li>Moves pieces for you</li>
        <li>Needs your password</li><li>Sends your data anywhere</li></ul></div></div>
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
      if (s.phase === "ready" && s.review_ready) return go("home");
      $("#phase").textContent = s.phase === "error" ? `Something went wrong (${s.error}). Retrying by itself.` : cap(s.phase || "working") + "…";
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
    if (name === "welcome") return await welcome();
    if (name === "games" && arg) return await gameView(arg);
    if (name === "games") return await games();
    if (name === "practice") return await practice();
    if (name === "settings") return await settingsView();
    return await home();
  } catch (e) {
    console.error(e);
    if ($("#page")) $("#page").innerHTML = `<div class="empty">Couldn't load this screen: ${esc(e.message)}</div>`;
  }
}
window.addEventListener("hashchange", () => { Voice.stop(); route(); });
api("/api/settings").then(s => { applyTheme(s.theme); Voice.set(s.voice && s.voice_ready); }).catch(() => {});
api("/api/status").then(s => { STATUS = s; if (!s.player && !location.hash.includes("welcome")) go("welcome"); else route(); })
  .catch(() => route());
pollStatus();
