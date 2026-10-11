// The coaches inside the Knightwise app: the same characters as on chess.com (/ext/faces.js), sitting on their box.
// Each tab has its coach, who comes up by themselves once a day; boards call them on every move (worried at a wrong
// move, with a hint; celebrating a right one). Also: the "Your plan" tab, the board trainer, and the AI card.

const COACHES = {
  maya: { name: "Maya", voice: "bf_emma", role: "Game reviews" },
  arjun: { name: "Arjun", voice: "am_puck", role: "Puzzles and practice" },
  zara: { name: "Zara", voice: "af_nova", role: "Before you play" },
  viktor: { name: "Viktor", voice: "bm_george", role: "Progress and your plan" },
};
const TAB_SECTION = { home: "home", games: "games", practice: "puzzles", plan: "plan" };

const Coach = (() => {
  let box = null, said = null, foldTimer = null;
  const remember = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } };
  const today = () => new Date().toISOString().slice(0, 10);

  function render(open) {
    if (!said) return;
    if (!box || !document.body.contains(box)) {
      box = document.createElement("div");
      document.body.appendChild(box);
    }
    const s = said, who = COACHES[s.coach] || COACHES.zara;
    box.className = `kw-coach kw-app ${open ? "open" : "folded"}`;
    const face = `<button class="kw-char" title="${esc(who.name)}">${KnightwiseFaces.figure(s.coach, s.pose || s.mood || "calm")}</button>`;
    box.innerHTML = open ? `${face}<div class="kw-box" role="status">
        <div class="kw-head"><b>${esc(who.name)}</b><span>${esc(who.role)}</span><button class="kw-x" title="Fold away">–</button></div>
        ${s.lines.map(l => `<p>${esc(l)}</p>`).join("")}
        ${(s.actions || []).length ? `<div class="kw-actions">${s.actions.map((a, i) =>
          `<button data-i="${i}">${esc(a.label)}</button>`).join("")}</div>` : ""}
      </div>` : `${face}<button class="kw-tab">${esc(who.name)}</button>`;
    box.querySelector(".kw-char").onclick = () => open ? fold() : (render(true), talk());
    const tab = box.querySelector(".kw-tab");
    if (tab) tab.onclick = () => { render(true); talk(); };
    const x = box.querySelector(".kw-x");
    if (x) x.onclick = fold;
    box.querySelectorAll(".kw-actions button").forEach(b => b.onclick = () => act(s.actions[Number(b.dataset.i)]));
  }

  function act(a) {
    if (a.run) return a.run();
    if (a.app) return go(a.app);
    if (a.url) window.open(a.url, "_blank", "noopener");
  }
  function fold() { clearTimeout(foldTimer); Voice.stop(); render(false); }
  function talk() { if (said) Voice.speak(said.lines.join(" "), false, (COACHES[said.coach] || {}).voice); }

  Voice.onTalk(on => {
    if (!box) return;
    box.classList.toggle("talking", on);
    if (!on) { clearTimeout(foldTimer); foldTimer = setTimeout(() => render(false), 30000); }
  });

  // say something now (open, with voice)
  function show(s, { speak = true } = {}) { if (!box) Sound.play("coach", 0.5); said = s; clearTimeout(foldTimer); render(true); if (speak) talk(); }
  // a quick reaction on a board: pose (worried, celebrate, explain...) and one line
  function react(coach, pose, text, actions) { show({ coach, pose, mood: pose, lines: [text], actions: actions || [] }); }
  function hide() { clearTimeout(foldTimer); if (box) box.remove(); box = null; said = null; }

  // the tab's coach comes up by themselves: open and speaking once a day, folded after that
  async function arrive(tab) {
    const section = TAB_SECTION[tab];
    if (!section) return hide();
    const r = await api(`/api/coach?section=${section}&hour=${new Date().getHours()}`).catch(() => null);
    if (!r || TAB_SECTION[location.hash.replace(/^#\/?/, "").split("/")[0] || "home"] !== section) return;
    const first = remember(`kw-app-greeted-${section}`) !== today();
    said = { ...r, pose: first ? "greet" : r.mood, actions: (r.actions || []).map(a => a.app ? a : { ...a, label: a.label + " ↗" }) };
    render(first);
    if (first) { remember(`kw-app-greeted-${section}`, today()); talk(); }
  }
  return { show, react, hide, arrive };
})();

// ---------- the board trainer: practice, plan lessons, openings ----------
// drills: as made by coach/drills.py. opts: {coach, record (save practice answers), onDone(rightFirstTime)}
function trainer(drills, opts) {
  const coach = opts.coach || "arjun", checklist = opts.checklist || [];
  let i = 0, k = 0, pieces = {}, picked = null, done = false, missed = false, last = {}, right = 0, solved = 0, ticked = 0;
  function paintChecks() {  // before each move: tick every question, then the board lets you move
    const el = $("#checks");
    if (!el || !checklist.length) return;
    el.innerHTML = `<div class="label">Before you move</div>${checklist.map((q, n) =>
      `<button class="check ${n < ticked ? "on" : ""}" data-n="${n}" ${n !== ticked ? "disabled" : ""}><i>${n < ticked ? "✓" : n + 1}</i>${esc(q)}</button>`).join("")}`;
    el.querySelectorAll(".check:not([disabled])").forEach(b => b.onclick = () => {
      ticked++; paintChecks();
      if (ticked < checklist.length) Coach.react(coach, "listen", checklist[ticked]);
      else Coach.react(coach, "encourage", "Good. Now make your move.");
    });
  }
  const ready = () => ticked >= checklist.length;
  const d = () => drills[i], step = () => d().steps[k];
  const mark = (sqs, cls) => Object.fromEntries(sqs.map(s => [s, cls]));
  const mine = sym => (sym === sym.toUpperCase()) === !d().flip;
  function draw(hl = {}, targets = []) { Board.render($("#board"), { pieces, flip: d().flip, highlights: { ...last, ...hl }, targets, onClick: click }); }
  function result(cls, html) { $("#result").innerHTML = `<div class="${cls}">${html}</div>`; }
  async function show() {
    k = 0; picked = null; done = false; missed = false; last = {};
    const x = d();
    $("#count").textContent = `${i + 1} of ${drills.length} · ${right} right first time`;
    $("#kind").textContent = x.kind === "game" ? "From your game" : x.kind === "opening" ? "Opening" : "Puzzle";
    $("#task").textContent = x.intro; $("#hint").textContent = x.kind === "opening" ? "" : x.hint;
    $("#where").innerHTML = `${esc(x.where)} · <a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.link)} ↗</a>`;
    result("muted", checklist.length ? "First the check, then click a piece and its square." : "Click a piece, then the square to move it to.");
    pieces = x.start; draw();
    ticked = 0; paintChecks();
    Coach.react(coach, checklist.length ? "listen" : x.kind === "opening" ? "explain" : "thinking",
      checklist.length ? `${x.intro} First: ${checklist[0]}` : x.intro);
    if (x.last) { done = true; await wait(700); if (d() !== x) return; pieces = x.steps[0].board; last = mark(x.last, "hl-last"); draw(); done = false; }
  }
  async function good(uci, m, shown) {
    const x = d(), s = step();
    pieces = m.after; last = {}; draw(mark([uci.slice(0, 2), uci.slice(2, 4)], "hl-ok"));
    Sound.move(m.san);
    if (s.reply) {
      done = true;
      result("ok-text", `<b>${esc(m.san)}</b>: yes. Now they play ${esc(s.reply.san)}. Keep going.`);
      if (s.idea) Coach.react(coach, "explain", s.idea);
      await wait(900); if (d() !== x) return;
      pieces = s.reply.board; last = mark([s.reply.uci.slice(0, 2), s.reply.uci.slice(2, 4)], "hl-last"); k++; done = false; draw();
      Sound.move(s.reply.san);
      ticked = 0; paintChecks();  // a new position: check again
      if (shown) answer(); return;
    }
    done = true; if (!missed) right++; solved++;
    setTimeout(() => Sound.play(shown ? "move" : "right"), 180);
    $("#count").textContent = `${i + 1} of ${drills.length} · ${right} right first time`;
    const note = x.kind === "game" ? `In the game you played ${esc(x.played)}.${m.san === x.best ? "" : " The engine's top move was " + esc(x.best) + "."}`
      : x.kind === "opening" ? "That's the whole line. Play it in your next games." : "Puzzle solved.";
    result("ok-text", `<b>${esc(m.san)}</b>: ${shown ? "that's the answer." : x.kind === "game" ? "yes, that keeps you safe." : "correct."}<div class="muted small" style="margin-top:4px">${note}</div>`);
    const praise = shown ? `The answer is ${m.san}. Next time you'll see it.` : s.idea ? `${s.idea} ${note}`
      : missed ? `${m.san}. You got there.` : x.kind === "game" ? `Yes! ${m.san} keeps you safe.` : `Correct, ${m.san}!`;
    Coach.react(coach, shown ? "explain" : missed ? "encourage" : "celebrate", praise);
    if (opts.record) api("/api/practice", { id: x.id, kind: x.kind, right: !missed }).then(stats).catch(() => {});
    if (solved === drills.length) { setTimeout(() => { Sound.play("done"); confetti(); }, 900); if (opts.onDone) opts.onDone(right); }
  }
  function click(sq) {
    if (done) return;
    if (!ready()) { Coach.react(coach, "warn", `Not yet. First: ${checklist[ticked]}`); return; }
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
    missed = true; Sound.play("wrong", 0.5);
    result("", `<b class="delta bad" style="font-size:14px">${esc(m.san)}: not quite.</b><div style="margin-top:4px">${esc(m.say)}</div><div class="small muted" style="margin-top:4px">Try again.</div>`);
    Coach.react(coach, "worried", `Not quite. ${m.say} Try again.`);  // the coach's face falls, with the hint
    draw(mark([uci.slice(0, 2), uci.slice(2, 4)], "hl-no"));
  }
  function answer() {
    const entries = Object.entries(step().moves).filter(([, m]) => m.good);
    const pick = (d().kind === "game" && entries.find(([, m]) => m.san === d().best)) || entries[0];
    missed = true; ticked = checklist.length; good(pick[0], pick[1], true);
  }
  function stats(s) { if (s && s.answers && $("#stats")) $("#stats").textContent = `So far: ${s.right} of ${s.answers} right first time · ${s.learned} positions learned (right 3 times, days apart).`; }
  $("#show").onclick = () => { if (!done) answer(); };
  $("#next").onclick = () => { i = (i + 1) % drills.length; show(); };
  if (opts.record) api("/api/stats").then(stats).catch(() => {});
  show();
}

function trainerPage(title, sub) {
  return `<div class="page-head"><div>${sub.back || ""}<h1>${esc(title)}</h1><p class="sub">${esc(sub.text)}</p></div>
      <span class="muted num" id="count"></span></div>
    <div class="game-layout">
      <div><div class="board-wrap" id="board"></div><p class="small muted" id="where" style="margin-top:10px"></p></div>
      <div class="stack"><div class="box"><div class="label" id="kind"></div><h3 id="task" style="margin:6px 0 10px"></h3>
        <p class="muted" id="hint" style="margin:0"></p></div>
        <div class="box checks" id="checks"></div>
        <div class="box" id="result" style="min-height:84px"><span class="muted">Click a piece, then the square to move it to.</span></div>
        <div class="row"><button class="btn" id="show">Show answer</button><button class="btn primary" id="next">Next</button></div>
        <p class="note" id="stats"></p></div>
    </div>`;
}

// ---------- Your plan ----------
const KIND_LABEL = { opening: "Opening", tactic: "Tactic", idea: "Way of thinking", endgame: "Endgame" };

async function planView(arg) {
  shell("plan", `<p class="muted">Picking your plan…</p>`);
  const p = await api("/api/plan");
  if (!p.player) { $("#page").innerHTML = `<div class="empty">Your plan appears once your games are checked.</div>`; return; }
  const all = [...(p.novelty ? [p.novelty] : []), ...Object.values(p.items).filter(Boolean)];
  if (arg) { const item = all.find(x => x.id === decodeURIComponent(arg)); if (item) return lessonView(item); }
  const card = (x, isNew) => `<div class="box plan-card ${isNew ? "new" : ""}">
      <div class="plan-face">${KnightwiseFaces.figure(x.coach, isNew ? "point" : "explain")}</div>
      <div class="plan-text"><div class="label">${isNew ? "New for you · " : ""}${KIND_LABEL[x.kind]} · with ${COACHES[x.coach].name}</div>
        <h3>${esc(x.title)}</h3><p class="muted small">${esc(x.why || x.intro)}</p>
        <button class="btn ${isNew ? "primary" : ""}" data-id="${esc(x.id)}">${p.done.includes(x.id) ? "Again" : "Start"}</button></div></div>`;
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>Your plan</h1>
      <p class="sub">Four things, picked for you from your games and from the coaches' library. One at a time.</p></div></div>
    ${p.novelty ? card(p.novelty, true) : ""}
    <div class="plan-grid">${Object.values(p.items).filter(Boolean).map(x => card(x, false)).join("")}</div>
    <p class="note">Puzzles: Lichess puzzle database. Openings: Lichess opening catalogue, checked by Stockfish.</p>`;
  document.querySelectorAll("[data-id]").forEach(b => b.onclick = () => go(`plan/${encodeURIComponent(b.dataset.id)}`));
  if (p.novelty && !p.novelty.again) api("/api/plan/mark", { id: p.novelty.id, novelty: true }).catch(() => {});
  if (p.novelty) AiCard.maybe("novelty");
}

function lessonView(item) {
  const back = `<a href="#/plan" class="small muted" style="text-decoration:none">← Your plan</a>`;
  api("/api/plan/mark", { id: item.id }).catch(() => {});
  if (item.kind === "idea") {  // a way of thinking, practised on your own positions with its checklist
    $("#page").innerHTML = trainerPage(item.title, { back, text: item.intro });
    trainer(item.drills, { coach: item.coach, checklist: item.checklist || [], onDone: rightFirst => {
      api("/api/plan/mark", { id: item.id, done: true }).catch(() => {});
      setTimeout(() => Coach.react(item.coach, "celebrate",
        `${rightFirst} of ${item.drills.length} right first time. Now do the same check in every game: after a week it becomes automatic.`,
        [{ label: "Back to your plan", app: "plan" }]), 2500);
    } });
    return;
  }
  $("#page").innerHTML = trainerPage(item.title, { back, text: item.why || item.intro });
  trainer(item.drills, { coach: item.coach, onDone: rightFirst => {
    api("/api/plan/mark", { id: item.id, done: true }).catch(() => {});
    setTimeout(() => Coach.react(item.coach, "celebrate",
      item.kind === "opening" ? "You know the line. Play it in your next games: I'll check how it goes." :
      `All done: ${rightFirst} of ${item.drills.length} right first time. That's a new weapon for your games.`,
      [{ label: "Back to your plan", app: "plan" }]), 2500);
  } });
}

// ---------- what AI adds: shown at the right moments, never nagging ----------
const AiCard = (() => {
  const KEY = "kw-ai-card";
  const state = () => { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } };
  const save = s => { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) {} };
  const ROWS = [
    ["Every game checked by Stockfish, key moments with arrows", true, true],
    ["Your four coaches, their faces and voices, on chess.com and here", true, true],
    ["Your plan and new ideas from the library", true, true],
    ["The coaches explain each moment in their own words", "Short, ready-made sentences", "Full explanations, tuned to you"],
    ["Ask your coach anything and get a reply", false, true],
    ["Talk it through: why this move, what to do next time", false, true],
  ];
  function html() {
    const cell = (v, plus) => `<td class="${plus ? "plus " : "free "}${v === true ? "yes" : v === false ? "no" : "small"}">${v === true ? "✓" : v === false ? "–" : esc(v)}</td>`;
    return `<div class="ai-card box"><button class="btn ghost ai-x" data-x title="Close">×</button>
      <div class="ai-title">Talk with your coaches</div>
      <p class="ai-lead">Add a free AI key and your coaches answer you in their own words. Both versions are free.</p>
      <table class="ai-table"><tr><th></th><th><span class="tier">Knightwise</span><small>Free</small></th>
        <th class="plus"><span class="tier">Knightwise + AI</span><small>Free key</small></th></tr>
        ${ROWS.map(([what, a, b]) => `<tr><td>${esc(what)}</td>${cell(a)}${cell(b, true)}</tr>`).join("")}</table>
      <div class="row" style="margin-top:14px"><a class="btn primary" href="#/settings" data-go>Set up now</a>
        <button class="btn" data-later>Not now</button><button class="btn ghost small" data-never>Don't show again</button></div></div>`;
  }
  function open() {
    const wrap = document.createElement("div");
    wrap.className = "ai-wrap";
    wrap.innerHTML = html();
    document.body.appendChild(wrap);
    const close = () => wrap.remove();
    wrap.querySelector("[data-x]").onclick = close;
    wrap.querySelector("[data-go]").onclick = close;
    wrap.querySelector("[data-later]").onclick = () => { save({ ...state(), next: Date.now() + 14 * 86400000 }); close(); };
    wrap.querySelector("[data-never]").onclick = () => { save({ ...state(), never: true }); close(); };
  }
  // moments: "welcome" (new player), "novelty" (the first new thing), "week" (a week of use without a key)
  async function maybe(moment) {
    const s = state();
    if (s.never || (s.next && Date.now() < s.next) || (s.seen || []).includes(moment)) return;
    const set = await api("/api/settings").catch(() => null);
    if (!set || Object.values(set.slots || {}).some(x => x.set)) return;  // already has a key
    if (moment === "week" && (!s.first || Date.now() - s.first < 7 * 86400000)) { if (!s.first) save({ ...s, first: Date.now() }); return; }
    save({ ...s, seen: [...(s.seen || []), moment], first: s.first || Date.now(), next: Date.now() + 3 * 86400000 });
    open();
  }
  return { open, maybe };
})();
