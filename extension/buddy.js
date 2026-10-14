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
    try { chrome.runtime.sendMessage(msg, r => resolve(chrome.runtime.lastError ? null : r)); } catch (e) { resolve(null); }
  });
  const today = () => new Date().toISOString().slice(0, 10);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  function remove() {
    if (box) box.remove();
    box = null; current = null; clearTimeout(foldTimer); warm = null;
    if (talking) { talking = false; send({ type: "listen-stop" }); }
    send({ type: "hush" });
  }

  function render(open) {
    const s = said;
    if (!s) return;
    if (!box) {
      box = document.createElement("div");
      box.className = "kw-coach";
      document.body.appendChild(box);
    }
    box.className = `kw-coach ${open ? "open" : "folded"}`;
    const face = `<button class="kw-char" title="${esc(s.name)}, your Knightwise coach">${KnightwiseFaces.figure(s.coach, s.pose || s.mood)}</button>`;
    box.innerHTML = open ? `${face}
      <div class="kw-box" role="status">
        <div class="kw-head"><b>${esc(s.name)}</b><span>${esc(s.role || "Knightwise coach")}</span>
          ${s.talk_ready && !s.talking ? `<button class="kw-speak" title="Talk with ${esc(s.name)}: press, then just speak">🎙 Talk</button>` : ""}
          <button class="kw-x" title="Fold away">–</button></div>
        ${s.lines.map(l => `<p>${esc(l)}</p>`).join("")}
        ${s.actions && s.actions.length ? `<div class="kw-actions">${s.actions.map((a, i) => {
          const best = a.best ? ` class="kw-best" title="${esc(a.why || "My pick")}"` : "";  // the coach's pick, said out loud
          return a.warmup ? `<button data-warmup${best}>${esc(a.label)}</button>`
            : a.app ? `<button data-app="${esc(a.app)}"${best}>${esc(a.label)}</button>`
            : a.find && target(a.find) ? `<button data-guide="${i}"${best}>${esc(a.label)}</button>`
            : `<a href="${esc(a.url)}"${best}>${esc(a.label)}</a>`;
        }).join("")}</div>` : ""}
        ${s.ai_hint ? `<p class="kw-hint">${esc(s.ai_hint)}</p>` : ""}
        ${s.ai_ready ? `<form class="kw-ask"><input placeholder="Ask ${esc(s.name)} anything about your chess" maxlength="300">
          <button>Ask</button></form>` : ""}
        ${s.note ? `<p class="kw-hint">${esc(s.note)}</p>` : ""}
      </div>` : `${face}<button class="kw-tab">${esc(s.name)}</button>`;
    const wake = box.querySelector(".kw-tab");
    if (wake) wake.onclick = () => { render(true); speak(); };
    box.querySelector(".kw-char").onclick = () => { if (open) fold(); else { render(true); speak(); } };
    box.querySelectorAll("[data-app]").forEach(b => b.onclick = () => {  // opens the Knightwise app at that page
      send({ type: "open-app", route: b.dataset.app });
      said = { ...said, pose: "pleased", lines: ["Opening Knightwise for you. See you there."], actions: [] };
      render(true); speak();
    });
    box.querySelectorAll("[data-guide]").forEach(b => b.onclick = () => guide(s.actions[Number(b.dataset.guide)]));
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

  // ---- Talk (0.6): a spoken conversation with the coach, hands-free, on the pages where the coach appears ----
  // Leaving the page ends it, so the microphone is never on during a game.
  let talking = false, talkHistory = [], speakingNow = false;
  const talkShow = (pose, lines, extra = {}) => {
    said = { ...said, pose, lines, actions: [], ai_hint: null, note: null, talking: true, ...extra };
    render(true);
    const stop = document.createElement("div");
    stop.className = "kw-actions";
    stop.innerHTML = `<button data-stop>Stop talking</button>`;
    box.querySelector(".kw-box").appendChild(stop);
    stop.querySelector("button").onclick = talkStop;
  };
  function speakAndWait(text) {  // say it, and wait until the voice has finished
    if (!said.voice_on) return Promise.resolve();
    speakingNow = false;
    send({ type: "say", text, voice: said.voice });
    return new Promise(done => {
      const began = Date.now();
      const tick = setInterval(() => {
        const t = Date.now() - began;
        if ((!speakingNow && t > 4000 && !box?.classList.contains("talking")) || t > 40000 || !talking) { clearInterval(tick); done(); }
        if (speakingNow === "done") { clearInterval(tick); done(); }
      }, 200);
    });
  }
  async function talkStart() {
    if (talking) return talkStop();
    talking = true; talkHistory = [];
    send({ type: "hush" });
    while (talking && box) {
      talkShow("listen", ["I'm listening…"]);
      const r = await send({ type: "listen" });
      if (!talking) return;
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
      if (!r.text) { talking = false; said = { ...said, pose: "calm", talking: false, lines: ["I'll be here. Press Talk when you want to carry on."] }; return render(true); }
      talkShow("thinking", [`"${r.text}"`, "…"]);
      const a = await send({ type: "talk", coach: said.coach, text: r.text, history: talkHistory, where: { section: current } });
      if (!talking) return;
      const reply = a && a.ok ? a.data : { text: "I can't reach the Knightwise app right now.", mood: "calm" };
      talkHistory.push(["player", r.text], ["coach", reply.text]);
      talkShow(reply.mood || "explain", [reply.text]);
      await speakAndWait(reply.text);
      const route = reply.action && reply.action.route;
      if (route) {  // a game's review: on chess.com's own board; anything else: in the Knightwise app
        talking = false;
        const game = /^games\/(\d+)$/.exec(route);
        if (game) location.href = `https://www.chess.com/game/live/${game[1]}`;
        else send({ type: "open-app", route });
        return;
      }
    }
  }
  function talkStop() {
    if (!talking) return;
    talking = false;
    send({ type: "listen-stop" }); send({ type: "hush" });
    said = { ...said, pose: "calm", talking: false, lines: ["Okay. Press Talk whenever you want to talk again."] };
    render(true);
  }

  // ---- the navigation guide: point at chess.com's own link, the player clicks it, the next coach notices ----
  let ring = null, ringFor = null, nudge = null;

  function target(find) {  // chess.com's visible link to that section, preferring the menu on the left
    const links = [...document.querySelectorAll("a[href]")].filter(a => {
      try { return new URL(a.href, location.href).pathname.startsWith(find.path) && a.getClientRects().length; } catch (e) { return false; }
    });
    return links.sort((a, b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left)[0] || null;
  }

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

  function guide(action) {
    const el = target(action.find);
    if (!el) { location.href = action.url; return; }  // their menu moved: plain link (the player asked to go there)
    unring();
    ringFor = el;
    ring = document.createElement("div");
    ring.className = "kw-ring";
    document.body.appendChild(ring);
    placeRing();
    addEventListener("scroll", placeRing, true); addEventListener("resize", placeRing);
    try { sessionStorage.setItem("kw-guided", action.find.path); } catch (e) {}
    said = { ...said, mood: "calm", pose: "point", actions: [], ai_hint: null,
             lines: [`Click "${action.find.name}" where the red ring is. I'll wait.`] };
    render(true); speak();
    nudge = setTimeout(() => {  // still here: point again, a little bigger
      if (!ring) return;
      ring.classList.add("again");
      said = { ...said, lines: [`It's right there, in the red ring: "${action.find.name}".`] };
      render(true); speak();
    }, 12000);
  }

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
    const r = await send({ type: "chat", coach: said.coach, message: question, history: history.slice(0, -1) });
    const reply = r && r.ok ? r.data : { text: "I can't reach the Knightwise app on this PC, and I answer from there. Open it from the Start menu.", mood: "calm" };
    history.push(["coach", reply.text]);
    said = { ...said, mood: reply.mood, pose: "explain", lines: [reply.text], note: reply.note || null };
    render(true); speak();
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
    if (talking) { speakingNow = msg.on ? true : (speakingNow ? "done" : speakingNow); return; }
    if (warm) return;  // the warm-up's board stays up, and never folds by itself
    if (!msg.on) {
      if (said && said.pose && said.pose !== "point") { said = { ...said, pose: null }; render(true); }  // back to their mood
      clearTimeout(foldTimer); foldTimer = setTimeout(() => render(false), MINUTES_OPEN * 60000);
    }
  });

  async function arrive() {
    const here = section(location.pathname), path = location.pathname;
    if (!here) setTimeout(() => {  // the self-check: a game page at an address the review doesn't know yet?
      if (location.pathname === path && KnightwiseContract.unknownGameAddress(path, !!KnightwiseContract.board(document)))
        KnightwiseContract.report("game-address", false, `unknown: ${path.replace(/\d{6,}/g, "<id>")}`);
    }, 4000);
    if (here === current) return;
    unring();
    remove();
    if (!here) return;  // not a coach section: nothing at all
    current = here;
    const store = (await send({ type: "greeted", section: here })) || {};
    const first = store.day !== today();  // the first visit to this section today: the full welcome
    const who = here === "member" ? location.pathname.split("/")[2] : undefined;
    const r = await send({ type: "coach", section: here, hour: new Date().getHours(), again: !first, who });
    if (current !== here) return;
    if (r && r.ok && !r.data.lines.length) { remove(); return; }  // nothing to say here (your own profile): no coach
    said = r && r.ok ? r.data : {
      coach: "maya", name: "Maya", mood: "calm", voice_on: false, actions: [],
      lines: ["I'm asleep: the Knightwise app isn't running on this PC.",
              "Everything I do here, your reviews, my advice and my voice, comes from the app. Open Knightwise from the Start menu and I'll be right back."],
    };
    let guided = null;
    try { guided = sessionStorage.getItem("kw-guided"); sessionStorage.removeItem("kw-guided"); } catch (e) {}
    if (guided && location.pathname.startsWith(guided) && r && r.ok) {  // they followed the guide: say so, warmly
      said = { ...said, mood: "pleased", pose: "celebrate", lines: ["Nice, you found it.", ...said.lines.slice(1)] };
      render(true); speak();
      return;
    }
    if (current !== here) return;
    if (first && r && r.ok) said = { ...said, pose: "greet" };
    render(true);  // never silent: the full welcome first, later in the day just where things stand
    if (first && r && r.ok) { send({ type: "greeted", section: here, set: today() }); speak(); }  // asleep: try again later
    else { clearTimeout(foldTimer); foldTimer = setTimeout(() => render(false), MINUTES_OPEN * 60000); }
  }

  // ---- the archive: a Knightwise tag on each finished game ("clean game", "2 pieces left hanging") ----
  let tagTimer = null, archiveSince = null;
  async function tagArchive() {
    if (!/^\/games\/archive(\/|$)/.test(location.pathname)) { archiveSince = null; return; }
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
