// Knightwise on chess.com: arrows and a short note on the key moments of YOUR FINISHED games.
//
// Fair play: the coach on your computer only knows games that chess.com has already archived as finished.
// For any other game (including one being played right now) it answers "unknown" and this script shows nothing.
(() => {
  if (window.top !== window) return;
  const FILES = "abcdefgh";
  const COLORS = { mine: "#e5484d", reply: "#f0a43a", real: "#6b9bff", best: "#2fb56f", better: "#2fb56f" };
  // "reply" is the engine's best answer; "real" is what the opponent really played, when it was different
  const LABELS = { mine: "You played", reply: "Their best reply", real: "They played", best: "Better", better: "Better" };
  let moments = [], overlay = null, panel = null, timer = null, gameId = null;
  // one key moment at a time, one step at a time (the same as the app's review): which moment, which step, how many shown
  let mi = 0, si = 0, shown = 0, extra = { clock: null, rematch: null }, voice = null;
  let small = false;
  let maya = { mood: "calm", line: "" };  // Maya, the coach for game reviews: her face and her first line
  try { small = localStorage.getItem("chess-coach-small") === "1"; } catch (e) {}

  // what we read from chess.com's page comes from contract.js, which also checks it (the self-check)
  const idFromUrl = () => KnightwiseContract.gameId(location.pathname);
  const boardEl = () => KnightwiseContract.board(document);
  const report = KnightwiseContract.report;
  let fallback = null;  // set when chess.com's page can't be read: the review then points to Knightwise
  const PIECES_GRACE = 20000;
  let noPiecesSince = 0, retry = null;

  function center(square, flipped) {
    const f = FILES.indexOf(square[0]), r = Number(square[1]) - 1;
    return [(flipped ? 7 - f : f) * 100 + 50, (flipped ? r : 7 - r) * 100 + 50];
  }

  // kind: "best" | "mine" | "reply" | "real"; every arrow carries its meaning written on it
  function arrow(uci, kind, flipped, faint) {
    const color = COLORS[kind], label = LABELS[kind];
    const [x1, y1] = center(uci.slice(0, 2), flipped), [x2, y2] = center(uci.slice(2, 4), flipped);
    const len = Math.hypot(x2 - x1, y2 - y1), ux = (x2 - x1) / len, uy = (y2 - y1) / len;
    const hx = x2 - ux * 36, hy = y2 - uy * 36; // where the head starts
    const px = -uy * 22, py = ux * 22;
    const tx = (x1 + hx) / 2, ty = (y1 + hy) / 2, w = label.length * 12 + 18;
    return `<g opacity="${faint ? 0.7 : 0.92}">
      <line x1="${x1}" y1="${y1}" x2="${hx}" y2="${hy}" stroke="${color}" stroke-width="${faint ? 11 : 16}" stroke-linecap="round"/>
      <polygon points="${x2},${y2} ${hx + px},${hy + py} ${hx - px},${hy - py}" fill="${color}"/>
      <rect x="${tx - w / 2}" y="${ty - 17}" width="${w}" height="34" rx="9" fill="${color}"/>
      <text x="${tx}" y="${ty + 7}" text-anchor="middle" font-family="Segoe UI, system-ui, sans-serif" font-size="20" font-weight="700" fill="#fff">${label}</text></g>`;
  }

  function clearArrows() { if (overlay) overlay.innerHTML = ""; }

  function draw() {
    if (!moments.length || (fallback && fallback !== FALLBACK.pieces)) return;  // after a fallback: the panel only, no arrows
    const board = boardEl();
    if (!board) return;  // start() waits for it and reports if it never comes
    const now = KnightwiseContract.boardPlacement(board);
    // chess.com shows a placeholder board first and its real pieces a few seconds later (14 Oct: the self-check said
    // "chess.com changed how it shows the pieces" on a page still loading). Only after 20 s of no pieces is it broken.
    if (!now) {
      noPiecesSince = noPiecesSince || Date.now();
      if (Date.now() - noPiecesSince < PIECES_GRACE) { clearTimeout(retry); retry = setTimeout(draw, 1000); return; }
      if (!fallback) report("pieces", false, "no piece could be read after 20 s");
      useFallback("pieces");
      clearTimeout(retry); retry = setTimeout(draw, 3000);  // keep looking: a page that reconnected gets its arrows (22 Oct)
      return;
    }
    noPiecesSince = 0;
    if (fallback === FALLBACK.pieces) { fallback = null; renderPanel(); }  // the pieces came back: arrows after all
    report("pieces", true);
    if (!overlay || !board.contains(overlay)) {
      overlay = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      overlay.setAttribute("viewBox", "0 0 800 800");
      overlay.classList.add("chess-coach-arrows");
      board.appendChild(overlay);
    }
    const flipped = board.classList.contains("flipped");
    clearArrows();
    // the step on show, when the board is where it belongs; if the player moved to a key position themselves,
    // that moment's step for this board (the better move before, everything after)
    let step = null;
    const k = moments[mi], cur = k && k.steps[si];
    if (cur && now === (cur.board === "before" ? k.placement : k.after_placement)) step = cur;
    else {
      for (let i = 0; i < moments.length && !step; i++) {
        const m = moments[i], at = now === m.placement ? "before" : now === m.after_placement ? "after" : null;
        if (!at) continue;
        const of = m.steps.map((st, j) => [st, j]).filter(([st]) => st.board === at);
        const [st, j] = at === "before" ? of[Math.min(1, of.length - 1)] : of[of.length - 1];
        if (i !== mi) { mi = i; shown = j; } else shown = Math.max(shown, j);
        si = j; step = st;
      }
    }
    if (step) overlay.innerHTML = step.arrows.map(([u, kind], n) => arrow(u, kind, flipped, step.arrows.length > 1 && n > 0)).join("");
    renderPanel();
  }

  function goTo(m, when, tries = 0) {  // when: "before" or "after" your move
    // chess.com numbers the moves in its list 0-0, 0-1, ... (one per half-move); the list fills in a little after
    // the board, so look again for up to 10 s before saying it's missing
    const ply = when === "before" ? m.ply - 2 : m.ply - 1;
    const node = ply < 0 ? null : document.querySelector(KnightwiseContract.moveNode(ply));
    if (ply >= 0 && !node && tries < 20) return setTimeout(() => goTo(m, when, tries + 1), 500);
    if (ply >= 0) report("move-list", !!node, node ? "" : "no move node after 10 s");
    if (node) node.click();
    setTimeout(draw, 300);
  }

  function say(text) { if (voice && voice.on) chrome.runtime.sendMessage({ type: "say", text, voice: voice.name }); }

  function pick(i, speak = true) {  // one step: the board where it belongs, its arrows, and Maya says it
    const k = moments[mi], st = k.steps[i];
    si = i; shown = Math.max(shown, i);
    goTo(k, st.board);
    renderPanel();
    if (speak) say(st.text);
  }

  function renderPanel() {
    if (!panel) {
      panel = document.createElement("div");  // Maya, leaning on the top of her review box
      panel.className = "kw-coach kw-review";
      document.body.appendChild(panel);
    }
    const k = moments[mi];
    panel.classList.toggle("folded", small);
    panel.classList.toggle("open", !small);
    const st = k && k.steps[si];
    const pose = st ? (st.kind === "mine" ? "worried" : "explain") : maya.mood;
    const char = `<button class="kw-char" title="Maya, game reviews">${KnightwiseFaces.figure("maya", pose)}</button>`;
    const broken = fallback ? `<p class="kw-broken">${escapeHtml(fallback)}</p>` : "";
    const steps = k ? k.steps.slice(0, shown + 1).map((x, i) => `<li class="${i === si ? "on" : ""}" data-s="${i}">
        <span class="kw-step"><i style="background:${COLORS[x.kind]}"></i>${escapeHtml(x.title)}${x.san ? ` <b>${escapeHtml(x.san)}</b>` : ""}</span>
        <div class="say">${escapeHtml(x.text)}</div></li>`).join("") : "";
    const last = k && shown >= k.steps.length - 1;
    const clock = extra.clock && extra.clock.lines.length ? `<details class="kw-clock"><summary>Your clock</summary>
        ${extra.clock.lines.map(l => `<div>${escapeHtml(l)}</div>`).join("")}</details>` : "";
    panel.innerHTML = small
      ? `${char}<button class="kw-tab pill">Maya · ${moments.length} key moment${moments.length === 1 ? "" : "s"}</button>`
      : `${char}<div class="chess-coach-panel"><div class="head"><span><b>Maya</b> <small>Game reviews</small></span>` +
        `<span><button class="min" title="Make small">–</button>` +
        `<button class="x" title="Close for this game">×</button></span></div>
      <p>${escapeHtml(maya.line)}</p>${broken}
      ${k ? `<div class="kw-moment"><b>Key moment ${mi + 1} of ${moments.length}</b> · move ${k.move_number}
        <span class="kw-dots">${moments.map((m, i) => `<button class="${i === mi ? "on" : ""}" data-m="${i}" title="Move ${m.move_number}"></button>`).join("")}</span></div>
        <ol>${steps}</ol>
        ${last && k.hard ? `<p class="kw-humans"><b>How hard was it?</b> ${escapeHtml(k.hard)}</p>` : ""}
        ${last && k.humans ? `<p class="kw-humans"><b>Real players:</b> ${escapeHtml(k.humans)}</p>` : ""}
        <div class="kw-row">${!last ? `<button class="kw-go" data-next>Next: ${escapeHtml(k.steps[shown + 1].title)} ▶</button>`
          : mi < moments.length - 1 ? `<button class="kw-go" data-nextm>Next moment ▶</button>` : ""}
          ${last && k.lesson ? `<button class="kw-open" data-lesson title="The Knightwise lesson on this idea">Learn it: ${escapeHtml(k.lesson.title)}</button>` : ""}
          ${last && extra.rematch ? `<button class="kw-open" data-rematch title="Play it on from here in Knightwise, at their level">Rematch from move ${extra.rematch.move_number}</button>` : ""}
          <button class="kw-open" data-open>Open in Knightwise</button></div>` : ""}
      ${clock}</div>`;
    panel.querySelector(".kw-char").onclick = () => setSmall(!small);
    const setSmall = v => {
      small = v;
      try { localStorage.setItem("chess-coach-small", v ? "1" : "0"); } catch (e) {}
      renderPanel();
    };
    if (small) { panel.querySelector(".pill").onclick = () => setSmall(false); return; }
    panel.querySelector(".min").onclick = e => { e.stopPropagation(); setSmall(true); };
    panel.querySelector(".x").onclick = () => { send("hush"); panel.remove(); panel = null; moments = []; clearArrows(); };
    const on = (sel, f) => panel.querySelectorAll(sel).forEach(el => el.onclick = e => { e.stopPropagation(); f(el); });
    on("[data-open]", () => chrome.runtime.sendMessage({ type: "open-app", route: `games/${gameId}` }));
    on("[data-rematch]", () => chrome.runtime.sendMessage({ type: "open-app", route: `rematch/${gameId}/${extra.rematch.ply}` }));
    on("[data-lesson]", () => chrome.runtime.sendMessage({ type: "open-app", route: `course/${k.lesson.id}` }));
    on("[data-next]", () => pick(shown + 1));
    on("[data-nextm]", () => { mi++; shown = 0; pick(0); });
    on("[data-m]", el => { mi = Number(el.dataset.m); shown = 0; pick(0); });
    on("li[data-s]", el => pick(Number(el.dataset.s)));
    const box = panel.querySelector(".chess-coach-panel"), cur = panel.querySelector("li.on");
    if (box && cur) box.scrollTop = Math.max(0, cur.offsetTop - 90);  // the step on show stays in view
  }
  const send = type => { try { chrome.runtime.sendMessage({ type }); } catch (e) {} };

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }

  function ask(id) {
    return new Promise(resolve => {
      try { chrome.runtime.sendMessage({ type: "game", id }, r => resolve(r && r.ok ? r.data : null)); }
      catch (e) { resolve(null); }
    });
  }

  const WAIT_EVERY = 20000, WAIT_FOR = 15 * 60000;  // a game that isn't archived yet: ask again, for a while
  let waiting = null;

  // Instant review. The coach only knows a game once chess.com's public archive lists it as finished, so while a
  // game is being played this shows nothing. When it ends and chess.com archives it, the app checks it at once.
  async function start() {
    const id = idFromUrl();
    if (id === gameId) return;
    if (!id) {  // left the game page (chess.com changes pages without reloading): take everything away
      gameId = null; moments = []; fallback = null; clearTimeout(waiting); clearArrows();
      if (panel) { panel.remove(); panel = null; }
      return;
    }
    gameId = id; fallback = null;
    report("game-address", true);
    clearTimeout(waiting);
    moments = []; clearArrows();
    if (panel) { panel.remove(); panel = null; }
    const since = Date.now();
    const look = async () => {
      if (gameId !== id) return;
      const data = await ask(id);
      if (gameId !== id) return;
      if (data && data.known) return show(id, data);
      if (!data || Date.now() - since > WAIT_FOR) return;  // the app isn't running, or it's been too long
      chrome.runtime.sendMessage({ type: "check-now" });  // the app looks at chess.com's archive for new games
      waiting = setTimeout(look, WAIT_EVERY);
    };
    look();
  }

  // the page must be this game: both players' names on it (chess.com's archive can point a bot game at someone
  // else's game address). Otherwise nothing is shown.
  // the page title has both names at once ("Chess: a vs b - Chess.com"); the page text fills in later, and reading
  // all of it is heavy on chess.com's busy page, so only every few seconds
  function samePlayers(players, i) {
    return KnightwiseContract.namesOnPage(document.title, players)
      || (i % 3 === 2 && KnightwiseContract.namesOnPage(document.body.innerText, players));
  }

  // chess.com's page couldn't be read: no arrows, but Maya still has the moments, and says honestly why
  const FALLBACK = {
    "player-names": "I can't confirm this page is your game, so no arrows here.",
    board: "chess.com changed its board, so I can't draw the arrows here.",
    pieces: "chess.com changed how it shows the pieces, so I can't draw the arrows here.",
  };
  function useFallback(check) {
    if (fallback) return;
    fallback = FALLBACK[check] || "I can't draw the arrows on this page.";
    clearArrows(); renderPanel();
  }

  async function show(id, data) {
    if (!data.moments.length) return;  // a clean game: nothing to show on the board
    if (KnightwiseContract.off("review")) return;  // paused for everyone in fixes.json: the review is in the app
    let names = false, board = null;
    for (let i = 0; i < 45 && gameId === id; i++) {  // chess.com fills in the names and the board a few seconds late
      names = names || samePlayers(data.players || [], i); board = boardEl();
      if (names && board) break;
      await new Promise(r => setTimeout(r, 1000));
    }
    if (gameId !== id) return;
    report("player-names", names, names ? "" : "names not on the page after 45 s");
    report("board", !!board, board ? "" : "no board element after 45 s");
    moments = data.moments; mi = 0; si = 0; shown = 0;
    extra = { clock: data.clock || null, rematch: data.rematch || null };
    if (!names || !board) useFallback(!names ? "player-names" : "board");
    const n = moments.length;
    maya = { mood: "calm", line: `${n} key moment${n === 1 ? "" : "s"} in this game. We'll take them one at a time: press Next.` };
    const r = await new Promise(res => {
      try { chrome.runtime.sendMessage({ type: "coach", section: "review", game: id, hour: new Date().getHours() }, res); }
      catch (e) { res(null); }
    });
    if (gameId !== id) return;
    if (r && r.ok) voice = { on: !!r.data.voice_on, name: r.data.voice };
    if (r && r.ok && r.data.lines.length) maya = { mood: r.data.mood, line: r.data.lines[0] };
    say(maya.line);
    pick(0, false);  // the first moment's first step, on the board at once
  }


  // Maya's mouth moves while her voice plays
  chrome.runtime.onMessage.addListener(msg => { if (msg.type === "speaking" && panel) panel.classList.toggle("talking", !!msg.on); });

  // Redraw when the board changes (moving through the game) and notice when chess.com changes page.
  const ours = node => (overlay && overlay.contains(node)) || (panel && panel.contains(node)) || node === overlay;
  new MutationObserver(records => {
    if (records.every(r => ours(r.target))) return; // our own drawing, not chess.com
    clearTimeout(timer);
    timer = setTimeout(() => { if (idFromUrl() !== gameId) start(); else draw(); }, 150);
  }).observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ["class"] });
  start();
})();
