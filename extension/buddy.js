// The Knightwise coach on chess.com: a face in the corner, what it says in a box under it, and its voice.
//
// Fair play: it appears ONLY on sections where no game can be running (an allow-list below). On any play page,
// game page, Puzzle Battle or anything unknown it does not appear at all and reads nothing from the page.
// It never clicks or moves anything: it suggests, the player clicks.
(() => {
  if (window.top !== window) return;

  // path -> section. Anything not listed: no coach.
  function section(path) {
    if (path === "/" || path === "/home") return "home";
    if (/^\/puzzles\/(battle|rush\/battle)/.test(path)) return null;  // against other people
    if (/^\/puzzles(\/|$)/.test(path)) return "puzzles";
    if (/^\/(lessons|learn|courses)(\/|$)/.test(path)) return "lessons";
    if (/^\/games\/archive(\/|$)/.test(path)) return "archive";  // the tags on your games: Maya explains them
    if (/^\/stats(\/|$)/.test(path)) return "progress";
    if (/^\/member\/[\w-]+\/?$/.test(path)) return "member";  // a player's profile: prep against them (0.8)
    return null;
  }

  const MINUTES_OPEN = 0.5;  // the box folds back to the face this long after it has finished talking
  let box = null, current = null, foldTimer = null, said = null;

  const send = msg => new Promise(resolve => {
    if (!(chrome.runtime && chrome.runtime.id)) { updated(); return resolve(null); }
    try { chrome.runtime.sendMessage(msg, r => resolve(chrome.runtime.lastError ? null : r)); } catch (e) { updated(); resolve(null); }
  });
  // Knightwise updated itself while this page was open: this copy of the coach is the old one and can't reach the
  // app any more. Say so once, plainly; the player refreshes when they like (never automatic: never mid-game).
  let staleShown = false;
  function updated() {
    if (staleShown || !document.body) return;
    staleShown = true;
    const note = document.createElement("div");
    note.className = "kw-updated";
    note.innerHTML = `Knightwise was updated. <button>Refresh this page</button> to see the new version.`;
    note.querySelector("button").onclick = () => location.reload();
    if (box) box.remove();
    document.body.appendChild(note);
  }
  const today = () => new Date().toISOString().slice(0, 10);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const brief = t => { const parts = String(t).split(/(?<=[.!?])\s+/); return parts.length > 2 ? parts.slice(0, 2).join(" ") : t; };

  addEventListener("pagehide", () => { if (talking) { talking = false; send({ type: "listen-stop", send: false }); } });
  function remove() {
    if (box) box.remove();
    box = null; current = null; clearTimeout(foldTimer); warm = null;
    if (talking) { talking = false; send({ type: "listen-stop" }); }
    send({ type: "hush" });
  }

  function render(open) {
    const off = KnightwiseContract.off;  // features paused for everyone in fixes.json: their buttons don't show
    const s = said && { ...said, talk_ready: said.talk_ready && !off("talk"),
                        actions: (said.actions || []).filter(a => !(a.warmup && off("warmup"))) };
    if (!s) return;
    if (!box) {
      box = document.createElement("div");
      box.className = "kw-coach";
      document.body.appendChild(box);
    }
    box.className = `kw-coach ${open ? "open" : "folded"}`;
    // one line and one button, like the app (22 Oct, the calm look); More shows the rest, the voice says it all
    // buttons need the words that explain them: with any, everything shows; without, two sentences and More (22 Oct)
    const full = !!(s.more || s.ai || s.talking || warm || (s.actions || []).length), best = (s.actions || []).find(a => a.best) || (s.actions || [])[0];
    const shown = full ? (s.actions || []) : best ? [best] : [];
    const face = `<button class="kw-char" title="${esc(s.name)}, your Knightwise coach">${KnightwiseFaces.figure(s.coach, s.pose || s.mood)}</button>`;
    box.innerHTML = open ? `${face}
      <div class="kw-box" role="status">
        <div class="kw-head"><b>${esc(s.name)}</b><span>${esc(s.role || "Knightwise coach")}</span>
          ${s.talk_ready && !s.talking ? `<button class="kw-speak" title="Talk with ${esc(s.name)}: click, speak, then click Stop">🎙 Talk</button>` : ""}
          <button class="kw-x" title="Fold away">–</button></div>
        ${(full ? s.lines : [brief(s.lines[0] || "")]).map(l => `<p>${esc(l)}</p>`).join("")}
        ${s.ai ? `<p class="kw-hint">AI can make mistakes. <button class="kw-report">Report it</button></p>` : ""}
        ${shown.length ? `<div class="kw-actions">${shown.map(a => { const i = s.actions.indexOf(a);
          const best = a.best ? ` class="kw-best" title="${esc(a.why || "My pick")}"` : "";  // the coach's pick, said out loud
          return a.warmup ? `<button data-warmup${best}>${esc(a.label)}</button>`
            : a.app ? `<button data-app="${esc(a.app)}"${best}>${esc(a.label)}</button>`
            : a.stopGuide ? `<button data-stopguide>${esc(a.label)}</button>`
            : a.guide && !off("guide") ? `<button data-guide="${i}"${best}>${esc(a.label)}</button>`
            : `<a href="${esc(a.url)}"${best}>${esc(a.label)}</a>`;
        }).join("")}</div>` : ""}
        ${full && s.ai_hint ? `<p class="kw-hint">${esc(s.ai_hint)}</p>` : ""}
        ${full && s.ai_ready ? `<form class="kw-ask"><input placeholder="Ask ${esc(s.name)} anything" maxlength="300">
          <button>Ask</button></form>` : ""}
        ${s.note ? `<p class="kw-hint">${esc(s.note)}</p>` : ""}
        ${full ? `<button class="kw-feedback" title="Tell us what went wrong or what was confusing">Send feedback</button>`
          : `<button class="kw-more" title="Everything ${esc(s.name)} said, the other buttons and Ask">More</button>`}
      </div>` : `${face}<button class="kw-tab">${esc(s.name)}</button>`;
    const mo = box.querySelector(".kw-more");
    if (mo) mo.onclick = () => { said = { ...said, more: true }; render(true); };
    const rep = box.querySelector(".kw-report");  // an AI answer that was wrong: the feedback form (22 Oct)
    if (rep) rep.onclick = () => send({ type: "open-app", route: "feedback" });
    const fb = box.querySelector(".kw-feedback");  // always in the same quiet place (19 Oct)
    if (fb) fb.onclick = () => send({ type: "open-app", route: "feedback" });
    const wake = box.querySelector(".kw-tab");
    if (wake) wake.onclick = () => { render(true); speak(); };
    box.querySelector(".kw-char").onclick = () => { if (open) fold(); else { render(true); speak(); } };
    box.querySelectorAll("[data-app]").forEach(b => b.onclick = () => {  // opens the Knightwise app at that page
      send({ type: "open-app", route: b.dataset.app });
      said = { ...said, pose: "pleased", lines: ["Opening Knightwise for you. See you there."], actions: [] };
      render(true); speak();
    });
    box.querySelectorAll("[data-guide]").forEach(b => b.onclick = () => guideStart(s.actions[Number(b.dataset.guide)].guide));
    box.querySelectorAll("[data-stopguide]").forEach(b => b.onclick = () => stopGuide("Okay, I'll stop. Ask me again whenever you like."));
    box.querySelectorAll("[data-warmup]").forEach(b => b.onclick = warmup);
    const form = box.querySelector(".kw-ask");
    if (form) form.onsubmit = e => { e.preventDefault(); const q = form.querySelector("input").value.trim(); if (q) ask(q); };
    const x = box.querySelector(".kw-x");
    if (x) x.onclick = () => { talkStop(); fold(); };
    const t = box.querySelector(".kw-speak");
    if (t) t.onclick = talkStart;
    const allow = box.querySelector("[data-mic]");
    if (allow) allow.onclick = () => send({ type: "mic-setup" });
  }

  // ---- Talk (0.6): a spoken conversation with the coach, on the pages where the coach appears ----
  // Click Talk to speak, click Stop when you've finished (20 Oct, the user: not hold-to-talk, not stopping by itself).
  // Leaving the page ends it without sending, so the microphone is never on during a game.
  let talking = false, talkHistory = [];
  const talkShow = (pose, lines, button) => {  // button: "Stop" while recording; none while she thinks
    said = { ...said, pose, lines, actions: [], ai_hint: null, note: null, talking: true };
    render(true);
    if (!button) return;
    const stop = document.createElement("div");
    stop.className = "kw-actions";
    stop.innerHTML = `<button data-stop class="kw-best">■ ${button}</button>`;
    box.querySelector(".kw-box").appendChild(stop);
    stop.querySelector("button").onclick = talkSend;
  };
  function talkSend() { send({ type: "listen-stop", send: true }); }  // Stop: what was said goes to the coach
  async function talkStart() {
    if (talking) return talkSend();
    talking = true;
    send({ type: "hush" });
    talkShow("listen", ["I'm listening. Click Stop when you've finished."], "Stop");
    const r = await send({ type: "listen" });
    if (!talking || (r && r.cancelled)) return;
    if (!r || r.error) {
      talking = false;
      if (r && r.error === "mic") {
        said = { ...said, pose: "calm", talking: false, actions: [],
                 lines: ["To hear you here, Chrome needs your OK once. Press Allow, then Talk again."] };
        render(true);
        const b = document.createElement("div"); b.className = "kw-actions";
        b.innerHTML = `<button data-mic class="kw-best">Allow the microphone</button>`;
        box.querySelector(".kw-box").appendChild(b);
        b.querySelector("button").onclick = () => send({ type: "mic-setup" });
        return;
      }
      said = { ...said, pose: "calm", talking: false, lines: [r && r.error && r.error !== "app" ? r.error
               : "I can't reach the Knightwise app on this PC, and I hear you through it. Open it from the Start menu."] };
      return render(true);
    }
    if (!r.text) { talking = false; said = { ...said, pose: "calm", talking: false, lines: ["I didn't catch that. Click Talk and try again."] }; return render(true); }
    talkShow("thinking", [`"${r.text}"`, "…"]);
    const a = await send({ type: "talk", coach: said.coach, text: r.text, history: talkHistory, where: { section: current, chesscom: true } });
    if (!talking) return;
    const reply = a && a.ok ? a.data : { text: "I can't reach the Knightwise app right now.", mood: "calm" };
    talkHistory.push(["player", r.text], ["coach", reply.text]);
    talking = false;  // her answer, then Talk again when you want to say more
    said = { ...said, pose: reply.mood || "explain", talking: false, lines: [reply.text], ai: !!reply.ai };
    render(true); speak();
    if (reply.action && reply.action.guide) { talking = false; guideStart(reply.action.guide); return; }  // the red ring
    const route = reply.action && reply.action.route;
    if (route) {  // a game's review: on chess.com's own board; anything else: in the Knightwise app
      talking = false;
      const game = /^games\/(\d+)$/.exec(route);
      if (game) location.href = `https://www.chess.com/game/live/${game[1]}`;
      else send({ type: "open-app", route });
      return;
    }
  }
  function talkStop() {  // folding the box or leaving: stop listening, send nothing
    if (!talking) return;
    talking = false;
    send({ type: "listen-stop", send: false }); send({ type: "hush" });
    said = { ...said, pose: "calm", talking: false, lines: ["Okay. Click Talk whenever you want to talk again."] };
    render(true);
  }

  // ---- the red ring (1.0): step by step to the exact chess.com page; it never clicks, the player does ----
  // The route (coach/coaches.py ROUTES) is kept in this tab's sessionStorage, so it carries on across pages. On each
  // page it rings the furthest step it can see. Fair play: it only runs where the coach may appear, plus chess.com's
  // Play menu page when no board is on it; it reads links and buttons, never a board.
  const GUIDE_KEY = "kw-guide", GUIDE_MINUTES = 10;
  let ring = null, ringFor = null, nudge = null, guiding = null;

  const pathOf = el => { try { return new URL(el.href, location.href).pathname.replace(/\/$/, "") || "/"; } catch (e) { return null; } };
  const shown = el => el.getClientRects().length && getComputedStyle(el).visibility !== "hidden" && !el.closest(".kw-coach");
  const words = el => (el.textContent || el.getAttribute("aria-label") || "").trim().replace(/\s+/g, " ").toLowerCase();
  function matches(step, el) {  // a link to the step's address, or a button with its words
    const p = el.href && pathOf(el);
    if (p && (step.exact ? p === step.path : p === step.path || p.startsWith(step.path + "/"))) return true;
    return !!(step.text && !el.href && words(el).includes(step.text.toLowerCase()));
  }
  function find(step) {  // chess.com's own link or button for this step, preferring the menu on the left
    const els = [...document.querySelectorAll(step.text ? "a[href],button,[role=button]" : "a[href]")]
      .filter(el => shown(el) && matches(step, el));
    return els.sort((a, b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left)[0] || null;
  }
  function steps(route) {  // fixes.json can replace a route for everyone: "path" or "path|Button words"
    const fix = (KnightwiseContract.fixes().nav || {})[route.id];
    if (!Array.isArray(fix) || !fix.length) return route.steps;
    return fix.map((s, i) => {
      const [path, text] = String(s).split("|");
      return { path, text: text || null, name: text || (route.steps[i] || {}).name || path, exact: i < fix.length - 1 };
    });
  }
  const here = () => location.pathname.replace(/\/$/, "") || "/";
  const arrived = route => here() === route.to || here().startsWith(route.to + "/");

  function placeRing() {
    if (!ring || !ringFor || !ringFor.isConnected) return unring();
    const r = ringFor.getBoundingClientRect();
    const left = Math.max(2, r.left - 6), top = Math.max(2, r.top - 6);  // never cut off at the edge
    Object.assign(ring.style, { left: `${left}px`, top: `${top}px`, width: `${r.right + 6 - left}px`, height: `${r.bottom + 6 - top}px` });
  }
  function unring() {
    if (ring) ring.remove();
    ring = null; ringFor = null; clearTimeout(nudge);
    removeEventListener("scroll", placeRing, true); removeEventListener("resize", placeRing);
  }
  function saveGuide() {
    try { guiding ? sessionStorage.setItem(GUIDE_KEY, JSON.stringify(guiding)) : sessionStorage.removeItem(GUIDE_KEY); } catch (e) {}
  }
  function loadGuide() {
    try {
      const g = JSON.parse(sessionStorage.getItem(GUIDE_KEY) || "null");
      return g && Date.now() - g.at < GUIDE_MINUTES * 60000 ? g : null;
    } catch (e) { return null; }
  }
  function stopGuide(line) {
    unring(); guiding = null; saveGuide();
    if (line && box) { said = { ...said, pose: "calm", actions: [], lines: [line] }; render(true); speak(); }
  }
  function overlapsBox(el) {  // the coach's own box must never cover what the ring points at
    if (!box) return false;
    const a = el.getBoundingClientRect(), b = box.getBoundingClientRect();
    return !(a.right < b.left || a.left > b.right || a.bottom < b.top || a.top > b.bottom);
  }
  function guideSay(lines) {
    if (!box || !said) return;
    said = { ...said, mood: "calm", pose: "point", ai_hint: null, note: null, lines,
             actions: [{ label: "Stop showing me", stopGuide: true }] };
    render(true); speak();
    if (ringFor && overlapsBox(ringFor)) render(false);  // fold to the face: the ring stays in view, her voice carries on
  }
  function guideStart(route, intro) {  // intro: her own suggestion, said before the first step (23 Oct)
    guiding = { id: route.id, to: route.to, name: route.name, url: route.url, steps: steps(route), wrong: 0,
                at: Date.now(), last: here(), intro: intro || null };
    saveGuide();
    guideStep(true);
  }
  function guideStep(first) {  // ring the furthest step that can be seen on this page
    if (!guiding) return;
    if (arrived(guiding)) {
      const name = guiding.name;
      stopGuide();
      if (box && said) { said = { ...said, mood: "pleased", pose: "celebrate", actions: [], lines: [`Nice, you found ${name}.`] }; render(true); speak(); }
      return;
    }
    const all = guiding.steps;
    let i = all.length - 1, el = null;
    for (; i >= 0; i--) { el = find(all[i]); if (el) break; }
    unring();
    if (!el) {  // nothing of the route on this page (chess.com changed it, or a page we don't know)
      KnightwiseContract.report("guide", false, `no step of ${guiding.id} on ${here().replace(/\d{6,}/g, "<id>")}`);
      const url = guiding.url;
      guiding = null; saveGuide();
      if (box && said) {
        said = { ...said, pose: "calm", lines: ["I can't find the way from this page. This link goes straight there."],
                 actions: [{ label: "Take me there", url }] };
        render(true); speak();
      }
      return;
    }
    KnightwiseContract.report("guide", true);
    ringFor = el;
    const rect = el.getBoundingClientRect();
    if (rect.bottom > innerHeight || rect.top < 0) el.scrollIntoView({ block: "center", behavior: "smooth" });
    ring = document.createElement("div");
    ring.className = "kw-ring";
    document.body.appendChild(ring);
    placeRing();
    setTimeout(placeRing, 600);  // after the smooth scroll
    addEventListener("scroll", placeRing, true); addEventListener("resize", placeRing);
    // the words on chess.com's own button, so Maya says what the player sees ("View All Games", not our name for it)
    const label = (el.innerText || "").split(/\n/).map(t => t.trim()).filter(t => /[a-z]/i.test(t)).pop() || "";
    const name = label.length >= 2 && label.length <= 30 ? label : all[i].name, last = i === all.length - 1;
    const intro = first && guiding.intro; if (intro) { guiding.intro = null; saveGuide(); }
    guideSay([...(intro ? [intro] : []), first ? `Click "${name}" where the red ring is.${last ? "" : " I'll show you the next step there."}`
      : guiding.wrong ? `That's not it, no problem. Click "${name}" in the red ring.`
      : `Good. Now click "${name}".`]);
    nudge = setTimeout(() => {  // still here: point again, a little bigger
      if (!ring) return;
      ring.classList.add("again");
      guideSay([`It's right there, in the red ring: "${name}".`]);
    }, 12000);
  }
  // going back (Chrome's back button) ends the guide: you changed your mind (22 Oct test: the ring was still there)
  let wentBack = false;
  addEventListener("popstate", () => { wentBack = true; });
  try { wentBack = (performance.getEntriesByType("navigation")[0] || {}).type === "back_forward"; } catch (e) {}
  function guideArrive() {  // a new page while guiding: on the way, arrived, or a wrong turn
    guiding = loadGuide();
    if (!guiding) return;
    if (wentBack) { wentBack = false; guiding = null; saveGuide(); document.querySelectorAll(".kw-ring").forEach(r => r.remove()); return; }
    const p = here();
    if (p !== guiding.last) {
      const onRoute = arrived(guiding) || guiding.steps.some(s => p === s.path || (!s.exact && p.startsWith(s.path + "/")));
      if (!onRoute) guiding.wrong++;
      guiding.last = p; guiding.at = Date.now(); saveGuide();
      if (guiding.wrong > 2) { stopGuide("We took a few wrong turns. Ask me again whenever you like."); return; }
    }
    setTimeout(guideStep, 900);  // chess.com builds its menus a moment after the address changes
  }
  // chess.com's Play menu page (/play, exactly): the ring may carry on there, with no coach box and nothing read but
  // links. Its board is only a picture (20 Oct: no game board element, no clock); a game clock on it means no ring.
  const playHub = () => here() === "/play" && !document.querySelector('[class*="clock"]');

  // ---- the warm-up before you play: three positions from today's practice, right here on chess.com's home ----
  // Only on the home page (no game can be running there); leaving the page ends it. Answers count as practice.
  // the app's own piece drawings (pieces.js): Windows drew the chess symbols as fixed-colour emoji (14 Oct)
  const piece = p => `<svg viewBox="0 0 45 45">${PIECES[p]}</svg>`;
  let warm = null;
  async function warmup() {
    const r = await send({ type: "warmup" });
    const items = r && r.ok ? r.data.items : [];
    if (!items.length) {
      said = { ...said, pose: "pleased", lines: ["You've done today's positions already. Go and play: one move at a time."], actions: [] };
      return (render(true), speak());
    }
    warm = { items, i: 0, picked: null, tries: 0, right: 0, done: false, msg: null };
    showWarm(true);
  }
  function warmSay(text, pose) { said = { ...said, pose, lines: [text] }; speak(); }
  function showWarm(intro) {
    if (!box || current !== "home") { warm = null; return; }
    clearTimeout(foldTimer);
    const x = warm.items[warm.i], flip = x.flip;
    const files = flip ? "hgfedcba" : "abcdefgh", ranks = flip ? "12345678" : "87654321";
    const targets = warm.picked ? Object.keys(x.moves).filter(u => u.startsWith(warm.picked)).map(u => u.slice(2, 4)) : [];
    const last = x.last || [];
    let cells = "";
    for (const r of ranks) for (const f of files) {
      const sq = f + r, p = x.board[sq], dark = ("abcdefgh".indexOf(f) + Number(r)) % 2 === 1 ? " dark" : "";
      const cls = `kw-sq${dark}${sq === warm.picked ? " pick" : ""}${last.includes(sq) ? " last" : ""}${targets.includes(sq) ? (p ? " take" : " dot") : ""}`;
      cells += `<button class="${cls}" data-sq="${sq}">${p ? piece(p) : ""}</button>`;
    }
    const face = `<button class="kw-char" title="${esc(said.name)}">${KnightwiseFaces.figure(said.coach, said.pose || "explain")}</button>`;
    box.className = "kw-coach open";
    box.innerHTML = `${face}<div class="kw-box kw-warm" role="status">
      <div class="kw-head"><b>${esc(said.name)}</b><span>Warm-up · ${warm.i + 1} of ${warm.items.length}</span><button class="kw-x" title="Stop the warm-up">–</button></div>
      <p>${esc(warm.msg || x.intro)}</p>
      <div class="kw-mini">${cells}</div>
      <p class="kw-hint">${esc(warm.tries >= 2 ? x.hint : x.where || "")}</p>
      ${warm.done ? `<div class="kw-actions"><button data-wnext class="kw-best">${warm.i + 1 < warm.items.length ? "Next position" : "Done: go and play"}</button></div>`
        : warm.tries >= 3 ? `<div class="kw-actions"><button data-wshow>Show me</button></div>` : ""}
    </div>`;
    box.querySelector(".kw-x").onclick = () => { warm = null; fold(); };
    box.querySelector(".kw-char").onclick = () => { warm = null; fold(); };
    box.querySelectorAll("[data-sq]").forEach(b => b.onclick = () => warmClick(b.dataset.sq));
    const nx = box.querySelector("[data-wnext]"); if (nx) nx.onclick = warmNext;
    const sh = box.querySelector("[data-wshow]"); if (sh) sh.onclick = warmShow;
    if (intro) warmSay(`${x.intro} ${warm.i === 0 ? "Three positions, then you play." : ""}`.trim(), "explain");
  }
  function warmClick(sq) {
    const x = warm.items[warm.i];
    if (warm.done) return;
    const mine = p => p && ((p === p.toUpperCase()) === !x.flip);
    if (warm.picked && warm.picked !== sq) {
      const uci = Object.keys(x.moves).find(u => u.slice(0, 4) === warm.picked + sq);
      if (uci) return warmMove(uci);
    }
    warm.picked = warm.picked === sq || !mine(x.board[sq]) ? null : sq;
    showWarm(false);
  }
  function warmMove(uci) {
    const x = warm.items[warm.i], m = x.moves[uci];
    warm.picked = null;
    if (m.good) {
      if (!warm.tries) warm.right++;
      if (warm.tries === 0) send({ type: "practice", id: x.id, kind: x.kind, right: true });
      warm.done = true; warm.msg = `${m.san}. That's it.`;
      if (m.after) x.board = m.after;
      showWarm(false); warmSay(warm.msg, "celebrate");
      return;
    }
    if (m.close) { warm.msg = `${m.san} is playable, but there's a better move. Look again.`; showWarm(false); return warmSay(warm.msg, "listen"); }
    if (warm.tries === 0) send({ type: "practice", id: x.id, kind: x.kind, right: false });
    warm.tries++;
    warm.msg = `Not ${m.san}. ${m.say || ""}`.trim();
    showWarm(false); warmSay(warm.msg, "worried");
  }
  function warmShow() {
    const x = warm.items[warm.i], [uci, m] = Object.entries(x.moves).find(([, v]) => v.good);
    if (m.after) x.board = m.after;
    warm.done = true; warm.msg = `The move was ${m.san}. It comes back in your practice tomorrow.`;
    showWarm(false); warmSay(warm.msg, "explain");
  }
  function warmNext() {
    if (warm.i + 1 >= warm.items.length) {
      const n = warm.right, of = warm.items.length;
      warm = null;
      said = { ...said, pose: "celebrate", actions: [],
               lines: [`Warm-up done: ${n} of ${of} at the first try. Now play, and before every move, ask what they can take.`] };
      render(true); speak();
      return;
    }
    warm.i++; warm.tries = 0; warm.done = false; warm.msg = null;
    showWarm(true);
  }

  // ---- talking with the coach (with the player's free AI key; written replies when the AI is busy) ----
  const history = [];
  async function ask(question) {
    clearTimeout(foldTimer);
    history.push(["player", question]);
    said = { ...said, mood: "thinking", pose: "listen", lines: [`"${question}"`, "…"], actions: [], note: null };
    render(true);
    // the same brain as Talk (19 Oct): typing "open my last review" opens it, not just words about it
    const r = await send({ type: "talk", coach: said.coach, text: question, history: history.slice(0, -1), where: { section: current, chesscom: true } });
    const reply = r && r.ok ? r.data : { text: "I can't reach the Knightwise app on this PC, and I answer from there. Open it from the Start menu.", mood: "calm" };
    history.push(["coach", reply.text]);
    said = { ...said, mood: reply.mood, pose: "explain", lines: [reply.text], note: reply.note || null, ai: !!reply.ai };
    render(true); speak();
    if (reply.action && reply.action.guide) { setTimeout(() => guideStart(reply.action.guide), 1200); return; }  // the red ring
    const route = reply.action && reply.action.route;
    if (route) {  // as with Talk: a game's review on chess.com's own board, anything else in the Knightwise app
      const game = /^games\/(\d+)$/.exec(route);
      setTimeout(() => game ? (location.href = `https://www.chess.com/game/live/${game[1]}`) : send({ type: "open-app", route }), 1500);
      return;
    }
    const input = box && box.querySelector(".kw-ask input");
    if (input) input.focus();
  }

  function fold() { clearTimeout(foldTimer); send({ type: "hush" }); render(false); }

  async function speak() {
    if (!said || !said.voice_on) return;
    send({ type: "say", text: said.lines.join(" "), voice: said.voice });
  }

  // the offscreen player tells us when the voice starts and stops, so the mouth moves only while it talks
  chrome.runtime.onMessage.addListener(msg => {
    if (msg.type !== "speaking" || !box) return;
    box.classList.toggle("talking", !!msg.on);
    if (talking) return;
    if (warm) return;  // the warm-up's board stays up, and never folds by itself
    if (!msg.on) {
      if (said && said.pose && said.pose !== "point") { said = { ...said, pose: null }; render(true); }  // back to their mood
      clearTimeout(foldTimer); foldTimer = setTimeout(() => render(false), MINUTES_OPEN * 60000);
    }
  });

  // A badge completed (Gold): the banner at the top, once, only on a calm chess.com page (home, puzzles, lessons, stats:
  // the app only sends it there, never on a game page). Seen here: the app won't show it again.
  function badgeUnlocked(b) {
    if (!b || !section(location.pathname)) return;
    send({ type: "badge-shown", id: b.id });
    kwBadgeBanner(b, { esc });
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

  async function arrive() {
    const here = section(location.pathname), path = location.pathname;
    await send({ type: "page", live: /^\/(?:game\/live|play\/online)(?:[/?#]|$)/.test(path) });  // fair play across tabs:
    // said before anything else, so a profile in another tab already knows
    if (!here) setTimeout(() => {  // the self-check: a game page at an address the review doesn't know yet?
      // the address first: the page is only looked at when it could be a finished game we don't know (never /game/live)
      if (location.pathname === path && !/^\/(?:game\/live|game\/daily|play)(?:[/?#]|$)/.test(path)
          && KnightwiseContract.unknownGameAddress(path, true) && KnightwiseContract.unknownGameAddress(path, !!KnightwiseContract.board(document)))
        KnightwiseContract.report("game-address", false, `unknown: ${path.replace(/\d{6,}/g, "<id>")}`);
    }, 4000);
    if (here && here === current) { if (loadGuide()) guideArrive(); return; }  // never on a page without the coach:
    // null === null used to run the ring's guide on any such page, a live game included (cloud review, 26 Oct)
    unring();
    remove();
    if (!here) {  // not a coach section: nothing at all, except the ring's next step on chess.com's Play menu page
      if (loadGuide() && playHub()) guideArrive();
      else if (loadGuide()) { guiding = null; saveGuide(); }  // arrived (a bots page), or somewhere a game can run: done
      return;
    }
    if (KnightwiseContract.off("coach") || (here === "member" && KnightwiseContract.off("prep"))) return;  // paused (fixes.json)
    current = here;
    // every time chess.com is opened (a new tab or window), the coach opens and talks once; the pages after that in the
    // same visit show the folded tab, open on click (22 Oct test: "open and talk automatically the first time every
    // web open, then open on click")
    let first = false;
    try { first = !sessionStorage.getItem("kw-visit-greeted"); sessionStorage.setItem("kw-visit-greeted", "1"); } catch (e) {
      const store = (await send({ type: "greeted", section: here })) || {};
      first = store.day !== today();
    }
    const who = here === "member" ? location.pathname.split("/")[2] : undefined;
    const r = await send({ type: "coach", section: here, hour: new Date().getHours(), again: !first, who });
    if (current !== here) return;
    if (r && r.ok && r.data.badge) setTimeout(() => badgeUnlocked(r.data.badge), 1200);  // a badge completed (calm pages only)
    // a repeat visit with nothing new: the coach waits as a folded tab, one click away (22 Oct test: "where are you")
    if (r && r.ok && r.data.quiet && loadGuide()) { said = { ...r.data, lines: ["This way: follow the red ring."] }; render(true); guideArrive(); return; }  // on the way with the ring first
    if (r && r.ok && r.data.quiet) { said = { ...r.data, lines: ["I'm here if you need anything."] }; render(false); return; }
    if (r && r.ok && !r.data.lines.length) { remove(); return; }  // nothing to say here (your own profile): no coach
    said = r && r.ok ? r.data : {
      coach: "maya", name: "Maya", mood: "calm", voice_on: false, actions: [],
      lines: ["I'm asleep: the Knightwise app isn't running on this PC.",
              "Everything I do here, your reviews, my advice and my voice, comes from the app. Open Knightwise from the Start menu and I'll be right back."],
    };
    if (r && r.ok && loadGuide()) { render(true); guideArrive(); return; }  // on the way with the red ring
    if (current !== here) return;
    if (first && r && r.ok) said = { ...said, pose: "greet" };
    // something new for this player on chess.com: she comes up by herself, says it and the red ring starts (23 Oct test:
    // "it never comes up and talks itself... a teacher comes up and teaches every day")
    const pt = r && r.ok && r.data.point;
    if (pt && pt.route_guide && !loadGuide()) {
      render(true); if (first) send({ type: "greeted", section: here, set: today() });
      guideStart(pt.route_guide, pt.line); return;
    }
    if (pt) {  // something new that lives in the app: she says it, with one button there
      render(true); if (first) send({ type: "greeted", section: here, set: today() }); speak(); return;
    }
    // the first page of a visit: open and talk; the pages after it: the folded tab, open on click (22 Oct test)
    if (first || !(r && r.ok)) render(true); else render(false);
    if (first && r && r.ok) { send({ type: "greeted", section: here, set: today() }); speak(); }  // asleep: try again later
  }

  // ---- the archive: a Knightwise tag on each finished game ("clean game", "2 pieces left hanging") ----
  let tagTimer = null, archiveSince = null;
  async function tagArchive() {
    if (!/^\/games\/archive(\/|$)/.test(location.pathname) || KnightwiseContract.off("tags")) { archiveSince = null; return; }
    archiveSince = archiveSince || Date.now();
    const rows = KnightwiseContract.archiveRows(document).filter(r => !r.slot.querySelector(".kw-tag"));
    if (!rows.length) {
      if (!document.querySelector(".kw-tag") && Date.now() - archiveSince > 15000) {  // still loading before that
        KnightwiseContract.report("archive-rows", false, "no game rows after 15 s");
      }
      if (!document.querySelector(".kw-tag")) { clearTimeout(tagTimer); tagTimer = setTimeout(tagArchive, 5000); }
      return;
    }
    KnightwiseContract.report("archive-rows", true);
    const r = await send({ type: "tags", ids: rows.map(x => x.id) });
    if (!r || !r.ok) return;  // the app isn't running: no tags, nothing else changes
    for (const { id, slot } of rows) {
      const t = r.data[id];
      if (!t || slot.querySelector(".kw-tag")) continue;
      const tag = document.createElement("span");
      tag.className = `kw-tag ${t.tone}`;
      tag.title = "Knightwise checked this game";
      tag.textContent = t.tone === "good" ? `✓ ${t.text}` : t.text;
      tag.onclick = e => { e.preventDefault(); e.stopPropagation(); send({ type: "open-app", route: `games/${id}` }); };
      slot.appendChild(tag);
    }
  }
  new MutationObserver(() => { clearTimeout(tagTimer); tagTimer = setTimeout(tagArchive, 600); })  // next pages load later
    .observe(document.body, { childList: true, subtree: true });

  // chess.com changes pages without reloading: notice the address changing
  let last = location.pathname;
  setInterval(() => { if (location.pathname !== last) { last = location.pathname; arrive(); } }, 700);
  arrive();
})();
