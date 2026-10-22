// The coaches inside the Knightwise app, Maya and Viktor (two since 13 Oct 2026, the player's choice): the same
// characters as on chess.com (/ext/faces.js), sitting on their box. Each tab has its coach, the full welcome once a day; boards call them on every move (worried at a wrong
// move, with a hint; celebrating a right one). Also: the "Your plan" tab, the board trainer, and the AI card.

const COACHES = {
  maya: { name: "Maya", voice: "af_heart", role: "Your games and practice" },
  viktor: { name: "Viktor", voice: "am_michael", role: "Your progress and plan" },
};
const TAB_SECTION = { home: "home", train: "plan", games: "games", practice: "puzzles", daily: "puzzles", plan: "plan", progress: "progress", level: "plan", endgames: "plan", calc: "plan", repertoire: "plan", course: "plan" };
// whose page it is (the same split as coach/coaches.py): Viktor has progress and the plan, Maya the rest
const tabCoach = tab => TAB_SECTION[tab] ? (["progress", "plan", "lessons"].includes(TAB_SECTION[tab]) ? "viktor" : "maya") : null;

const Coach = (() => {
  let box = null, said = null, foldTimer = null, quiet = null, held = null;
  const remember = (k, v) => { try { if (v === undefined) return localStorage.getItem(k); localStorage.setItem(k, v); } catch (e) { return null; } };
  const today = () => new Date().toISOString().slice(0, 10);

  let more = false;
  const brief = t => { const parts = String(t).split(/(?<=[.!?])\s+/); return parts.length > 2 ? parts.slice(0, 2).join(" ") : t; };  // one line and one button (22 Oct, the approved look); More shows the rest, the voice says it all
  function render(open) {
    if (!said) return;
    if (!box || !document.body.contains(box)) {
      box = document.createElement("div");
      document.body.appendChild(box);
    }
    const s = said, who = COACHES[s.coach] || COACHES.maya;
    box.className = `kw-coach kw-app ${open ? "open" : "folded"}`;
    const face = `<button class="kw-char" title="${esc(who.name)}">${KnightwiseFaces.figure(s.coach, s.pose || s.mood || "calm")}</button>`;
    box.innerHTML = open ? `${face}<div class="kw-box" role="status">
        <div class="kw-head"><b>${esc(who.name)}</b><span>${esc(who.role)}</span>
          ${TALK && !s.talking ? `<button class="kw-speak" title="Talk with ${esc(who.name)}: click, speak, then click Stop">🎙 Talk</button>` : ""}
          <button class="kw-x" title="Fold away">–</button></div>
        ${(more ? s.lines : [brief(s.lines[0] || "")]).map(l => `<p>${esc(l)}</p>`).join("")}
        ${s.ai ? `<p class="kw-ai-note">AI can make mistakes. <button class="kw-report">Report it</button></p>` : ""}
        ${(s.actions || []).length ? `<div class="kw-actions">${(more ? s.actions : s.actions.slice(0, 1)).map((a, i) =>
          `<button data-i="${i}">${esc(a.label)}</button>`).join("")}</div>` : ""}
        ${!more && (s.lines.length > 1 || (s.actions || []).length > 1 || brief(s.lines[0] || "") !== (s.lines[0] || "")) ? `<button class="kw-more" title="Show everything">More</button>` : ""}
      </div>` : `${face}<button class="kw-tab">${esc(who.name)}</button>`;
    box.querySelector(".kw-char").onclick = () => open ? fold() : (render(true), talk());
    const tab = box.querySelector(".kw-tab");
    if (tab) tab.onclick = () => { render(true); talk(); };
    const x = box.querySelector(".kw-x");
    if (x) x.onclick = () => { if (Conv.on) Conv.stop(); fold(); };
    const t = box.querySelector(".kw-speak");
    if (t) t.onclick = () => Conv.start(s.coach);
    const mo = box.querySelector(".kw-more");
    if (mo) mo.onclick = () => { more = true; render(true); };
    const rep = box.querySelector(".kw-report");  // an AI answer that was wrong: straight to the feedback email (22 Oct)
    if (rep) rep.onclick = () => window.feedbackBox && window.feedbackBox();
    box.querySelectorAll(".kw-actions button").forEach(b => b.onclick = () => act(s.actions[Number(b.dataset.i)]));
  }

  function act(a) {
    if (a.run) return a.run();
    if (a.app) return go(a.app);
    if (a.url) window.open(a.url, "_blank", "noopener");
  }
  function fold() { clearTimeout(foldTimer); Voice.stop(); render(false); }
  function talk() { if (said) Voice.speak(said.spoken || said.lines.join(" "), false, (COACHES[said.coach] || {}).voice, !said.casual); }

  Voice.onTalk(on => {
    if (!box) return;
    box.classList.toggle("talking", on);
    if (!on) { clearTimeout(foldTimer); foldTimer = setTimeout(() => render(false), 30000); }
  });

  // say something now (open, with voice)
  function show(s, { speak = true } = {}) {
    if (Conv.on && !s.talking) { held = s; return; }  // in a conversation, only the conversation speaks (kept for a handover)
    said = s; more = !!s.talking; clearTimeout(foldTimer); render(true); if (speak) talk();
  }
  // a quick reaction on a board: pose (worried, celebrate, explain...) and one line
  // spoken: what the voice says when it differs from the short line in the bubble
  function react(coach, pose, text, actions, spoken) { show({ coach, pose, mood: pose, lines: [text], actions: actions || [], spoken }); }
  function hide() { clearTimeout(foldTimer); if (box) box.remove(); box = null; said = null; }

  // the tab's coach comes up by themselves: open and speaking once a day, folded after that
  async function arrive(tab, force) {  // force: a handover in a conversation, so the new coach speaks
    if (Conv.on) return;  // talking: the coach stays with the conversation
    const section = TAB_SECTION[tab];
    if (!section) return hide();
    const first = remember(`kw-app-greeted-${section}`) !== today();  // the first visit to this section today
    const r = await api(`/api/coach?section=${section}&in=app&hour=${new Date().getHours()}${first || force ? "" : "&again=1"}`).catch(() => null);
    if (!r || TAB_SECTION[location.hash.replace(/^#\/?/, "").split("/")[0] || "home"] !== section) return;
    said = { ...r, casual: true, pose: first ? "greet" : r.mood, actions: (r.actions || []).map(a => a.app ? a : { ...a, label: a.label + " ↗" }) };
    more = false;
    if (r.quiet && !force) { said.lines = ["I'm here if you need anything."]; return render(false); }  // nothing new: just the tab
    render(true);  // the full welcome first, later just where things stand (once a day)
    if (first || force) { remember(`kw-app-greeted-${section}`, today()); talk(); }
    else { const now = said; clearTimeout(quiet); quiet = setTimeout(() => { if (said === now) render(false); }, 20000); }
  }
  // what the page itself said while the conversation spoke (the page's own coach line), taken once
  const takeHeld = () => { const h = held; held = null; return h; };
  return { show, react, hide, arrive, takeHeld };
})();

// ---------- talking with your coach by voice (0.6, flagship 2) ----------
// Talk with your coach: click Talk, speak, click Stop (20 Oct, the user: "click to talk, click again to stop is
// better", not hold-to-talk and not stopping by itself; it stops by itself only after a minute). The coach hears you
// through your Groq or Gemini key and answers out loud; click Talk again to say more. The coach can open a page, a
// game's review or a rematch, or show the next step of the review; the app checks each one first (coach/talk.py).
const Conv = (() => {
  let on = false, rec = false, history = [], coach = "maya", limit = null;
  const where = () => {
    const [name, arg] = location.hash.replace(/^#\/?/, "").split("/");
    // in a review, the move on screen too, so "why was that bad?" is about that move (22 Oct test)
    return name === "games" && arg ? { section: "review", game: arg, ply: String(window.kwPly ? window.kwPly() : "") } : { section: name || "home" };
  };
  const show = (pose, lines, actions = []) => Coach.show({ coach, pose, mood: pose, lines, talking: true, actions }, { speak: false });
  async function start(who) {
    if (rec) return finish();
    if (on) return;  // still answering the last thing you said
    on = true; coach = who in COACHES ? who : "maya";
    Voice.stop();
    try { await Mic.start(); } catch (e) { on = false; Coach.react(coach, "worried", "The microphone isn't available.", [], ""); return; }
    rec = true;
    show("listen", ["I'm listening. Click Stop when you've finished."], [{ label: "■ Stop", best: true, run: finish }]);
    limit = setTimeout(finish, 60000);
  }
  async function finish() {  // Stop: what you said goes to the coach
    if (!rec) return;
    rec = false; clearTimeout(limit);
    show("thinking", ["…"]);
    let text;
    try { text = await Mic.stop(); }
    catch (e) { on = false; Coach.react(coach, "worried", e.message || "I couldn't hear that.", [], ""); return; }
    if (!on) return;
    if (!text) { on = false; Coach.react(coach, "calm", "I didn't catch that. Click Talk and try again.", [], ""); return; }
    show("thinking", [`"${text}"`, "…"]);
    let r;
    try { r = await api("/api/talk", { coach, text, history, where: where() }); }
    catch (e) { r = { text: "I can't reach the Knightwise app right now.", mood: "calm" }; }
    if (!on) return;
    let speech = r.text, handover = null;
    Coach.takeHeld();
    if (r.action && r.action.route) {
      go(r.action.route); await wait(400);
      // the page belongs to the other coach: they take over, as two coaches in one room (22 Oct test: Maya opened
      // the course, Viktor's page, and Viktor never came)
      const tab = r.action.route.split("/")[0], owner = tabCoach(tab);
      if (owner && owner !== coach) { handover = { tab, owner }; speech = `${speech} Here's ${COACHES[owner].name}.`; }
    }
    if (r.action && r.action.next && window.kwNextStep) speech = window.kwNextStep() || speech;  // the review's next step
    if (r.action && r.action.back && window.kwBackStep) speech = window.kwBackStep() || speech;  // and back again
    history.push(["player", text], ["coach", speech]);
    on = false;  // her answer; Talk again to say more
    Coach.show({ coach, pose: r.mood || "explain", mood: r.mood || "explain", lines: [speech], actions: [], ai: !!r.ai }, { speak: false });
    await Voice.speak(speech, true, (COACHES[coach] || {}).voice, !!(r.action && (r.action.next || r.action.back)));  // review steps: teaching pace
    if (!handover || on || location.hash.replace(/^#\/?/, "").split("/")[0] !== handover.tab) return;
    const page = Coach.takeHeld();  // the page's own line, if it said one, else the coach's greeting for it
    if (page && page.coach === handover.owner) Coach.show(page);
    else Coach.arrive(handover.tab, true);
  }
  function stop() {  // closing the box or leaving: stop listening, nothing is sent
    clearTimeout(limit);
    if (!on) return;
    on = false; rec = false; Mic.close(); Voice.stop();
    Coach.react(coach, "calm", "Okay. Click Talk whenever you want to talk again.", [], "");
  }
  return { start, stop, get on() { return on; } };
})();

// ---------- the board trainer: practice, plan lessons, openings ----------
// drills: as made by coach/drills.py. opts: {coach, record (save practice answers), onDone(rightFirstTime)}
// With record, today's answers come from the server: leaving the page and coming back keeps them, a position
// answered today stays answered (solving it again is practice and changes nothing), and onDone fires once.
function trainer(drills, opts) {
  const coach = opts.coach || "maya", checklist = opts.checklist || [];
  let i = 0, k = 0, pieces = {}, picked = null, done = false, missed = false, last = {}, ticked = 0, finishedAll = false;
  const state = drills.map(() => null), briefed = drills.map(() => false);  // per position: right, missed, shown
  const answered = drills.map(() => false);  // has today's answer: right, missed or shown
  const right = () => state.filter(x => x === "right").length;
  const counter = () => { $("#count").innerHTML = `<b class="num">${i + 1}</b>/${drills.length} <span class="count-ok" title="Right first time today">${svg("check")} ${right()}</span>`; };
  function save(x, result) {  // the day's first answer to this position; the server ignores later ones
    if (opts.record) api("/api/practice", { id: x.id, kind: x.kind, right: result === "right", shown: result === "shown" })
      .then(stats).catch(() => {});
  }
  function allDone(already) {  // every position answered: say so clearly, once
    if (finishedAll) return;
    finishedAll = true;
    result("ok-text", `<b>All ${drills.length} done${opts.record ? " for today" : ""}.</b> ${right()} of ${drills.length} right first time.<div data-helpful></div>`);
    helpful($("#result [data-helpful]"), `practice ${location.hash.replace(/^#\/?/, "")}`);
    if (!already) setTimeout(() => { Sound.play("done"); confetti(); }, 900);
    if (opts.onDone) opts.onDone(right(), already);
  }
  const group = x => x.pattern || x.kind;
  const groupName = x => (x.pattern && (HABIT[x.pattern] || [])[1]) || { opening: "Your opening", puzzle: "Puzzles", game: "Your games" }[x.kind] || "Practice";
  function paintDots() {  // one thin bar: a segment per position, grouped by habit (22 Oct: "why so many circles")
    const el = $("#dots");
    if (!el) return;
    if (drills.length < 2) { el.innerHTML = ""; return; }
    let html = "", n = 0;
    while (n < drills.length) {
      const g = group(drills[n]), first = n, x0 = drills[n];
      while (n < drills.length && group(drills[n]) === g) n++;
      const icon = (x0.pattern && (HABIT[x0.pattern] || [])[0]) || (x0.kind === "opening" ? "book" : "practice");
      html += `<div class="pgroup" title="${esc(groupName(x0))}">${svg(icon)}<div class="psegs">${
        drills.slice(first, n).map((x, j) => `<button class="pseg ${first + j === i ? "on" : ""} ${state[first + j] || ""}"
          data-n="${first + j}" title="${first + j + 1} · ${x.kind === "puzzle" ? "Puzzle" : x.kind === "opening" ? "Opening" : "From your game"}"></button>`).join("")}</div></div>`;
    }
    el.innerHTML = html;
    el.querySelectorAll(".pseg").forEach(b => b.onclick = () => { i = Number(b.dataset.n); show(); });
  }
  function paintBrief(x) {  // before the board: where this comes from, what's going on, how to think
    const b = x.brief, el = $("#briefbox");
    const title = String(b.title || "").replace(/^Your game /, "");
    el.innerHTML = `<div class="brief-head">${svg(x.kind === "game" ? "games" : x.kind === "opening" ? "book" : "practice")}
        <h3 class="brief-title">${esc(title)}</h3></div>
      <div class="muted small">${b.facts.map(esc).join(" · ")}</div>
      <div class="brief-mind">${svg("bolt")}<span>${esc(b.mindset)}</span></div>
      <button class="btn primary" id="go">I'm ready</button>`;
    $("#go").onclick = () => { briefed[i] = true; show(); };
  }
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
  const whereLink = x => `<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.link[0].toUpperCase() + x.link.slice(1))} ↗</a>`;
  const NAMES = { p: "pawn", n: "knight", b: "bishop", r: "rook", q: "queen", k: "king" };
  let tries = 0;  // wrong moves on this step: the help grows with each one
  const d = () => drills[i], step = () => d().steps[k];
  const mark = (sqs, cls) => Object.fromEntries(sqs.map(s => [s, cls]));
  const mine = sym => (sym === sym.toUpperCase()) === !d().flip;
  function draw(hl = {}, targets = []) { Board.render($("#board"), { pieces, flip: d().flip, highlights: { ...last, ...hl }, targets, onClick: click }); }
  function result(cls, html) { $("#result").innerHTML = `<div class="${cls}">${html}</div>`; }
  async function show() {
    k = 0; picked = null; done = false; missed = false; last = {};
    const x = d();
    counter();
    paintDots();
    const briefing = x.brief && !briefed[i] && !answered[i];  // answered today: straight to the board
    $("#briefbox").hidden = !briefing;
    document.querySelectorAll(".play-only").forEach(el => el.hidden = briefing);
    $("#board").classList.toggle("dim", !!briefing);
    if (briefing) {  // the coach welcomes you to this position first, then the board wakes up
      pieces = x.last ? x.steps[0].board : x.start; last = x.last ? mark(x.last, "hl-last") : {}; done = true; draw();
      paintBrief(x);
      $("#where").innerHTML = whereLink(x);
      Coach.react(coach, "explain", x.brief.situation, [], `${x.brief.situation} The mindset: ${x.brief.mindset}`);
      return;
    }
    $("#kind").textContent = x.kind === "game" ? "From your game" : x.kind === "opening" ? "Opening" : "Puzzle";
    $("#task").textContent = x.intro; $("#hint").textContent = x.kind === "opening" ? "" : x.hint;
    $("#where").innerHTML = whereLink(x);
    tries = 0;
    result("muted", answered[i] ? `Done today: ${{ right: "right first time", missed: "missed the first time", shown: "you used Show answer" }[state[i]]}. Play it again for practice; it won't change your score.`
      : checklist.length ? "First the check, then click a piece and its square." : "");
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
    const more = k + 1 < x.steps.length;  // the last step of an opening line can end with their answer too
    if (s.reply) {
      done = true;
      result("ok-text", `<b>${esc(m.san)}</b>: yes. Now they play ${esc(s.reply.san)}.${more ? " Keep going." : ""}`);
      if (s.idea) Coach.react(coach, "explain", s.idea);
      await wait(900); if (d() !== x) return;
      pieces = s.reply.board; last = mark([s.reply.uci.slice(0, 2), s.reply.uci.slice(2, 4)], "hl-last"); draw();
      Sound.move(s.reply.san);
      if (more) {
        k++; done = false;
        ticked = 0; paintChecks();  // a new position: check again
        if (shown) answer(); return;
      }
      await wait(600); if (d() !== x) return;
    }
    done = true;
    const again = answered[i];  // already answered today: practice only, nothing changes
    if (!again) { state[i] = shown ? "shown" : missed ? "missed" : "right"; answered[i] = true; save(x, state[i]); }
    paintDots();
    setTimeout(() => Sound.play(shown ? "move" : "right"), 180);
    counter();
    const note = x.kind === "game" ? `In the game you played ${esc(x.played)}.${m.san === x.best ? "" : " The engine's top move was " + esc(x.best) + "."}`
      : x.kind === "opening" ? "That's the whole line. Play it in your next games." : (x.end || "Puzzle solved.");
    result("ok-text", `<b>${esc(m.san)}</b>: ${shown ? "that's the answer." : "right."}<div class="muted small" style="margin-top:4px">${esc(x.kind === "puzzle" ? (x.end || "Puzzle solved.") : note)}</div>`);
    // what the move achieved in this exact position: for your own game, what your game move cost; for a puzzle,
    // why it ends there
    const played = x.kind === "game" && Object.values(x.steps[0].moves).find(e => e.san === x.played);
    const lesson = x.kind === "game" ? (played && played.say ? `In the game you played ${x.played}. ${played.say} This time you avoided it.` : note)
      : x.kind === "puzzle" ? (x.end || "Puzzle solved.") : note;
    const praise = shown ? `The answer is ${m.san}. ${lesson}` : s.idea ? `${s.idea} ${note}`
      : `${missed ? `${m.san}. You got there.` : `Yes, ${m.san}!`} ${lesson}`;
    Coach.react(coach, shown ? "explain" : missed ? "encourage" : "celebrate", praise);
    if (!again && answered.every(Boolean)) allDone(false);
  }
  function click(sq) {
    if (done) return;
    if (!ready()) { Coach.react(coach, "warn", `Not yet. First: ${checklist[ticked]}`); return; }
    const sym = pieces[sq];
    if (sym && mine(sym)) {
      if (picked === sq) { picked = null; return draw(); }  // the same piece again: put it down
      picked = sq;
      return draw({ [sq]: "hl-pick" }, Object.keys(step().moves).filter(u => u.startsWith(sq)).map(u => u.slice(2, 4)));
    }
    if (!picked) return;
    const uci = step().moves[picked + sq] ? picked + sq : picked + sq + "q", m = step().moves[uci];
    picked = null;
    if (!m) return draw();
    if (m.good) return good(uci, m, false);
    if (m.close) {  // playable, not the answer: no red square, no penalty, just look again
      result("", `<b style="font-size:14px">${esc(m.san)}: playable.</b><div style="margin-top:4px">${esc(m.say)}</div>`);
      Coach.react(coach, "thinking", m.say);
      return draw();
    }
    missed = true; tries++;
    if (tries === 1) Sound.play("wrong", 0.5);  // the low sound once, not on every try
    if (!answered[i]) { state[i] = "missed"; answered[i] = true; save(d(), "missed"); paintDots(); }  // saved now: leaving can't undo it
    // the help grows: first why it's wrong, then the idea, then which piece, never the move itself
    const right = Object.entries(step().moves).find(([, e]) => e.good), from = right ? right[0].slice(0, 2) : null;
    const help = tries === 1 ? `${m.say} Try again.`
      : tries === 2 ? `Here's a hint: ${d().hint || "look at every check and capture first."}`
      : from ? `Look at your ${NAMES[pieces[from].toLowerCase()]} on ${from}. Where can it go?` : `${m.say} Try again.`;
    result("", `<b class="delta bad" style="font-size:14px">${esc(m.san)}: not quite.</b><div style="margin-top:4px">${esc(help)}</div>`);
    Coach.react(coach, tries === 1 ? "worried" : "encourage", tries === 1 ? `Not quite. ${help}` : help);
    draw({ ...mark([uci.slice(0, 2), uci.slice(2, 4)], "hl-no"), ...(tries >= 3 && from ? { [from]: "hl-pick" } : {}) });
  }
  function answer() {
    const entries = Object.entries(step().moves).filter(([, m]) => m.good);
    const pick = (d().kind === "game" && entries.find(([, m]) => m.san === d().best)) || entries[0];
    missed = true; ticked = checklist.length; good(pick[0], pick[1], true);
  }
  function stats(s) { if (s && s.positions && $("#stats")) $("#stats").textContent = `All time: ${s.right_first} of ${s.positions} positions right the very first time you saw them · ${s.learned} learned for good.`; }  // not today's count: a position you see again adds to that (19 Oct)
  $("#show").onclick = () => { if (!done) answer(); };
  $("#next").onclick = () => {  // from the last one: the next unanswered, or the end of the session, never a silent loop
    if (i === drills.length - 1 && answered.every(Boolean)) { finishedAll = false; return allDone(true); }
    const ahead = drills.map((_, n) => (i + 1 + n) % drills.length);
    i = i === drills.length - 1 ? (ahead.find(n => !answered[n]) ?? 0) : i + 1; show();
  };
  $("#prev").onclick = () => { i = (i - 1 + drills.length) % drills.length; show(); };
  $("#prev").hidden = $("#next").hidden = drills.length < 2;
  if (!opts.record) return show();
  api("/api/stats").then(s => {  // pick up where you were today
    stats(s);
    drills.forEach((x, n) => { const t = s.today && s.today[x.id]; if (t) { state[n] = t; answered[n] = true; } });
    const first = answered.findIndex(a => !a);
    i = first < 0 ? 0 : first;
    show();
    if (first < 0) allDone(true);
  }).catch(() => show());
}

function trainerPage(title, sub) {
  return `<div class="page-head"><div>${sub.back || ""}<h1>${esc(title)}</h1><p class="sub">${esc(sub.text)}</p></div>
      <span class="muted num" id="count"></span></div>
    <div class="dots" id="dots"></div>
    <div class="game-layout">
      <div><div class="board-wrap" id="board"></div><p class="small muted" id="where" style="margin-top:10px"></p></div>
      <div class="stack"><div class="box brief" id="briefbox" hidden></div>
        <div class="box play-only"><div class="label" id="kind"></div><h3 id="task" style="margin:6px 0 10px"></h3>
        <p class="muted" id="hint" style="margin:0"></p></div>
        <div class="box checks play-only" id="checks"></div>
        <div class="box play-only" id="result" style="min-height:84px"><span class="muted">Click a piece, then the square to move it to.</span></div>
        <div class="row"><button class="btn" id="prev">← Back</button><button class="btn play-only" id="show">Show answer</button>
          <button class="btn" id="next">Next →</button></div>
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
  // a picture of each thing, not a sentence (22 Oct: "what is the plan and why so less in it"): its board, how many
  // positions, done or not; one Viktor in his bubble, not on every card
  const ICONS = { opening: "book", tactic: "bolt", idea: "sparkles", endgame: "mate" };
  const card = (x, isNew) => {
    const n = (x.drills || []).length, done = p.done.includes(x.id);
    return `<div class="box pcard ${isNew ? "new" : ""}" data-id="${esc(x.id)}" title="${esc(x.why || x.intro || "")}">
      <div class="row spread"><span class="pkind">${svg(ICONS[x.kind] || "plan")}${KIND_LABEL[x.kind]}</span>
        ${isNew ? `<span class="pnew">New</span>` : done ? `<span class="pdone">${svg("check")}</span>` : ""}</div>
      <h3>${esc(x.title)}</h3>
      <div class="mini-board" data-board="${esc(x.id)}"></div>
      ${n ? `<div class="psegs">${Array.from({ length: n }, () => `<i class="pseg ${done ? "right" : ""}"></i>`).join("")}</div>` : ""}
      <button class="btn ${isNew ? "primary" : ""}">${done ? "Again" : "Start"}</button></div>`;
  };
  $("#page").innerHTML = `
    <div class="page-head"><div><h1>Your plan</h1></div></div>
    <div class="plan-cards rise">${all.map((x, i) => card(x, !!p.novelty && i === 0)).join("")}</div>`;
  all.forEach(x => {  // the position each one starts from
    const el = document.querySelector(`[data-board="${CSS.escape(x.id)}"]`), d0 = (x.drills || [])[0];
    if (!el) return;
    if (x.fen) Board.render(el, { fen: x.fen, flip: x.side === "black" });
    else if (d0 && d0.start) Board.render(el, typeof d0.start === "string" ? { fen: d0.start, flip: d0.flip } : { pieces: d0.start, flip: d0.flip });
    else el.remove();
  });
  document.querySelectorAll("[data-id]").forEach(b => b.onclick = () => go(`plan/${encodeURIComponent(b.dataset.id)}`));
  if (p.novelty && !p.novelty.again) api("/api/plan/mark", { id: p.novelty.id, novelty: true }).catch(() => {});
  if (p.novelty) AiCard.maybe("novelty");
}

function lessonView(item) {
  const back = item.back === "repertoire" ? `<a href="#/repertoire" class="small muted" style="text-decoration:none">← Your repertoire</a>`
    : item.back === "level" ? `<a href="#/level" class="small muted" style="text-decoration:none">← Your level</a>`
    : `<a href="#/plan" class="small muted" style="text-decoration:none">← Your plan</a>`;
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
    ["Your two coaches, their faces and voices, on chess.com and here", true, true],
    ["Your plan and new ideas from the library", true, true],
    ["One-to-one conversation with your coach", false, true],
    ["Ask your coach anything and get a reply", false, true],
    ["Talk it through: why this move, what to do next time", false, true],
  ];
  function html() {
    const cell = (v, plus) => `<td class="${plus ? "plus " : "free "}${v ? "yes" : "no"}">${v ? "✓" : "✗"}</td>`;  // ticks and crosses only
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
