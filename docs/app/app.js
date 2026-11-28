// Knightwise on the phone (preview): three screens.
//   #/          who are you? (chess.com or Lichess username)
//   #/games     every finished game of yours, with wins / losses / draws on top
//   #/game/ID   one game, move by move on a board
// Everything stays on this phone (IndexedDB, see store.js). No server of ours, no engine yet (docs/MOBILE-PLAN.md).
// Cheap phones first: the first screen needs only this file, games.js and store.js; the board, pieces and
// rules (about 26 KB) load the first time you open a game.
(() => {
  const view = document.getElementById("view");
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  let games = [];          // summaries of the games on screen right now
  let note = "";           // a line under the list: "Saved 5 min ago", "Offline", ...
  let loading = false;     // a download is running

  // ---------- load a script only when it's first needed ----------
  const scripts = {};
  const need = src => scripts[src] || (scripts[src] = new Promise((ok, bad) => {
    const s = document.createElement("script");
    s.src = src; s.onload = ok;
    s.onerror = () => { delete scripts[src]; bad(new Error("Couldn't load " + src)); };
    document.head.append(s);
  }));

  // ---------- who is playing (kept on the phone) ----------
  function player() { try { return JSON.parse(localStorage.getItem("kw.player") || "null"); } catch { return null; } }
  function setPlayer(p) { try { p ? localStorage.setItem("kw.player", JSON.stringify(p)) : localStorage.removeItem("kw.player"); } catch { } }

  // ---------- downloading, shown as it arrives ----------
  // resolves when the first games are in (or fails with the reason), keeps going in the background
  function download(site, user) {
    loading = true;
    const still = () => { const q = player(); return q && q.site === site && q.user === user; };   // not changed player meanwhile
    return new Promise((first, fail) => {
      let started = false;
      Games.load(site, user, (some, month) => {
        if (!still()) return;
        games = some;
        const when = month ? new Date(month.replace("/", "-") + "-15").toLocaleDateString(undefined, { month: "short", year: "numeric" }) : "";
        note = `Downloading${when ? " " + when : ""}... ${some.length} so far.`;
        if (!started && some.length) { started = true; first(); }
        else if (location.hash === "#/games") drawGames(player());
      }).then(all => {
        loading = false;
        if (!still()) return;
        games = all; note = "Updated just now.";
        if (!all.length) return fail(new Error("no-games"));
        if (!started) first();
        if (location.hash === "#/games") drawGames(player());
      }).catch(x => {
        loading = false;
        if (!started) return fail(x);
        note = "The download stopped; showing what came in.";
        if (location.hash === "#/games") drawGames(player());
      });
    });
  }

  // ---------- screen 1: username ----------
  function showStart() {
    const p = player() || { site: "chesscom", user: "" };
    view.innerHTML = `
      <h1>Your games, on your phone</h1>
      <p class="sub">Type your username. Knightwise reads your finished games from the site's public records.</p>
      <form id="who" class="box stack">
        <div class="seg" role="radiogroup">
          <button type="button" data-site="chesscom" class="${p.site !== "lichess" ? "on" : ""}">chess.com</button>
          <button type="button" data-site="lichess" class="${p.site === "lichess" ? "on" : ""}">Lichess</button>
        </div>
        <input id="user" class="field" placeholder="Username" autocomplete="username" autocapitalize="off"
          spellcheck="false" value="${esc(p.user)}" required>
        <button class="btn primary">Show my games</button>
        <p id="err" class="error" hidden></p>
      </form>`;
    let site = p.site || "chesscom";
    view.querySelectorAll(".seg button").forEach(b => b.onclick = () => {
      site = b.dataset.site;
      view.querySelectorAll(".seg button").forEach(x => x.classList.toggle("on", x === b));
    });
    view.querySelector("#who").onsubmit = async e => {
      e.preventDefault();
      const user = view.querySelector("#user").value.trim();
      if (!user || loading) return;
      const btn = view.querySelector(".btn.primary"), err = view.querySelector("#err");
      btn.disabled = true; btn.textContent = "Downloading your games..."; err.hidden = true;
      try {
        setPlayer({ site, user });
        await download(site, user);
        location.hash = "#/games";
      } catch (x) {
        setPlayer(null);
        err.hidden = false;
        err.textContent = x.message === "no-player" ? `No ${site === "lichess" ? "Lichess" : "chess.com"} player called "${user}".`
          : x.message === "no-games" ? "No finished games yet. Play one, then come back."
          : navigator.onLine ? `Couldn't download the games (${x.message}). Try again in a minute.`
          : "You're offline. Connect once to download your games.";
        btn.disabled = false; btn.textContent = "Show my games";
      }
    };
  }

  // ---------- screen 2: the games list ----------
  function ago(ms) {
    const m = Math.round((Date.now() - ms) / 60000);
    return m < 60 ? `${m} min ago` : m < 1440 ? `${Math.round(m / 60)} h ago` : `${Math.round(m / 1440)} days ago`;
  }
  const dateOf = ms => new Date(ms).toLocaleDateString(undefined, { day: "numeric", month: "short",
    year: new Date(ms).getFullYear() === new Date().getFullYear() ? undefined : "numeric" });

  async function showGames() {
    const p = player();
    if (!p) { location.hash = "#/"; return; }
    if (!games.length) {                               // opened fresh: show what's saved at once, then refresh
      const s = await Games.saved(p.site, p.user);
      if (s) { games = s.games; note = `Saved ${ago(s.at)}.`; }
    }
    drawGames(p);
    if (!loading && !note.startsWith("Updated")) {
      if (!navigator.onLine) { note = "Offline; showing the saved games."; drawGames(p); return; }
      download(p.site, p.user).catch(() => {
        note = games.length ? "Couldn't update; showing the saved games." : "Couldn't download the games. Try again later.";
        if (location.hash === "#/games") drawGames(p);
      });
    }
  }

  // every game is kept; the list shows 100 at a time, so a phone with thousands of games stays quick
  let shown = 100;
  function drawGames(p) {
    const n = r => games.filter(g => g.result === r).length;
    const more = games.length - shown;
    view.innerHTML = `
      <div class="links"><h1>${esc(p.user)}</h1>
        <button id="change" class="btn ghost small">Change player</button></div>
      <p class="sub small">${games.length} finished games on ${p.site === "lichess" ? "Lichess" : "chess.com"}. ${esc(note)}</p>
      <div class="stats">
        <div class="stat"><b class="num">${n("win")}</b><span>won</span></div>
        <div class="stat"><b class="num">${n("loss")}</b><span>lost</span></div>
        <div class="stat"><b class="num">${n("draw")}</b><span>drawn</span></div>
      </div>
      <h2>Games</h2>
      <ul class="games">${games.slice(0, shown).map(g => {
        const opp = g.me === "w" ? g.black : g.white, oppR = g.me === "w" ? g.blackRating : g.whiteRating;
        return `<li><a class="game" href="#/game/${encodeURIComponent(g.id)}">
          <span class="chip ${g.result}">${g.result === "win" ? "W" : g.result === "loss" ? "L" : "½"}</span>
          <span class="grow"><div class="who">${esc(opp)} <span class="muted small num">${esc(oppR || "")}</span></div>
            <div class="meta">${esc(g.how)} · ${esc(g.speed)} · ${Math.ceil(g.plies / 2)} moves · ${dateOf(g.endedAt)}</div></span>
          <span class="side ${g.me}" title="You played ${g.me === "w" ? "White" : "Black"}"></span></a></li>`;
      }).join("")}</ul>
      ${more > 0 ? `<button id="more" class="btn" style="width:100%;margin-top:12px">Show ${Math.min(100, more)} more (${more} older)</button>` : ""}`;
    view.querySelector("#change").onclick = () => { setPlayer(null); games = []; note = ""; shown = 100; location.hash = "#/"; };
    const moreBtn = view.querySelector("#more");
    if (moreBtn) moreBtn.onclick = () => { const y = scrollY; shown += 100; drawGames(p); scrollTo(0, y); };
  }

  // ---------- screen 3: one game on the board ----------
  async function showGame(id) {
    const p = player();
    if (!games.length && p) { const s = await Games.saved(p.site, p.user); if (s) games = s.games; }
    const g = games.find(x => x.id === id);
    if (!g) { location.hash = "#/games"; return; }
    view.innerHTML = `<p class="muted">Opening the game...</p>`;
    let line;
    try {
      await Promise.all([need("pieces.js"), need("rules.js")]);
      await need("board.js");
      line = Rules.replay(Games.sansOf(g), g.startFen || Games.START);   // worked out now, not kept for every game
    } catch (x) {
      view.innerHTML = `<p class="error">This game couldn't be opened: ${esc(x.message)}</p><a href="#/games">Back</a>`;
      return;
    }
    if (location.hash !== "#/game/" + encodeURIComponent(id)) return;   // the player went elsewhere meanwhile
    const flip = g.me === "b", last = line.fens.length - 1;
    let at = last;   // open at the end: how it finished
    const top = flip ? [g.white, g.whiteRating] : [g.black, g.blackRating];
    const bottom = flip ? [g.black, g.blackRating] : [g.white, g.whiteRating];
    const word = { win: "You won", loss: "You lost", draw: "Draw" }[g.result];

    view.className = "page game-page";
    view.innerHTML = `
      <div class="links"><a href="#/games" class="btn ghost small">‹ Games</a>
        <a href="${esc(g.url)}" target="_blank" rel="noopener" class="btn ghost small">Open on ${esc(g.site)}</a></div>
      <div class="game-grid"><div>
        <div class="players"><span>${esc(top[0])} <span class="r num">${esc(top[1] || "")}</span></span></div>
        <div class="board-wrap" id="board"></div>
        <div class="players"><span>${esc(bottom[0])} <span class="r num">${esc(bottom[1] || "")}</span></span></div>
        <div class="controls">
          <button class="btn" data-go="start" aria-label="Start">⏮</button>
          <button class="btn" data-go="back" aria-label="Back">◀</button>
          <button class="btn" data-go="next" aria-label="Next">▶</button>
          <button class="btn" data-go="end" aria-label="End">⏭</button>
        </div>
        <p class="ply" id="ply"></p>
        <button class="btn" id="analyse" style="width:100%">Analyse from here</button>
      </div><div>
        <p class="end">${word}${g.how ? ", " + esc(g.how) : ""}${g.opening ? `<br><span class="muted small">${esc(g.opening)}</span>` : ""}</p>
        <div class="moves" id="moves">${line.moves.map((m, i) =>
          `${i % 2 === 0 ? `<span class="n">${i / 2 + 1}.</span>` : ""}<button data-i="${i + 1}">${esc(m.san)}</button>`).join("")}</div>
      </div></div>`;

    const boardEl = view.querySelector("#board"), ply = view.querySelector("#ply"), list = view.querySelector("#moves");
    const buttons = list.querySelectorAll("button");
    let lit = null;   // the highlighted move: only it and the new one change, so the phone redraws little
    let queued = false;
    function draw() {
      queued = false;
      const hl = {}, m = line.moves[at - 1];
      if (m) { hl[m.from] = "hl-last"; hl[m.to] = "hl-last"; }
      if (m && m.check) {                              // the king in check gets a red square
        const pos = Rules.parse(line.fens[at]), k = pos.board.indexOf(pos.turn === "w" ? "K" : "k");
        if (k >= 0) hl[Rules.name(k)] = "hl-check";
      }
      Board.render(boardEl, { fen: line.fens[at], flip, highlights: hl });
      ply.textContent = at === 0 ? "Start position" : `Move ${Math.ceil(at / 2)}${at % 2 ? "" : "…"} ${m.san} · ${at} of ${last}`;
      if (lit) lit.classList.remove("on");
      lit = at ? buttons[at - 1] : null;
      if (lit) { lit.classList.add("on"); list.scrollTop = lit.offsetTop - list.clientHeight / 2; }   // only the list scrolls
    }
    // fast taps on a slow phone: draw once per screen frame, with the newest position
    const go = to => { at = Math.max(0, Math.min(last, to)); if (!queued) { queued = true; requestAnimationFrame(draw); } };
    const moves = { start: () => go(0), back: () => go(at - 1), next: () => go(at + 1), end: () => go(last) };
    view.querySelectorAll("[data-go]").forEach(b => b.onclick = moves[b.dataset.go]);
    list.onclick = e => { const b = e.target.closest("button"); if (b) go(Number(b.dataset.i)); };   // one listener, not one per move
    let x0 = null;   // swipe the board left or right to step through the game
    boardEl.addEventListener("touchstart", e => { x0 = e.touches[0].clientX; }, { passive: true });
    boardEl.addEventListener("touchend", e => {
      if (x0 === null) return;
      const dx = e.changedTouches[0].clientX - x0; x0 = null;
      if (Math.abs(dx) > 30) go(at + (dx < 0 ? 1 : -1));
    });
    keys = e => { if (e.key === "ArrowLeft") moves.back(); if (e.key === "ArrowRight") moves.next(); };
    view.querySelector("#analyse").onclick = () => { location.hash = `#/board/${encodeURIComponent(g.id)}/${at}`; };
    draw();
  }
  let keys = null;
  document.addEventListener("keydown", e => keys && keys(e));

  // ---------- screen 4: the analysis board (no engine, ever) ----------
  // #/board                 an empty start position
  // #/board/<gameId>/<ply>  a finished game of yours, from that move (you can play on from there)
  let board = null;
  const css = href => { if (!document.querySelector(`link[href="${href}"]`)) {
    const l = document.createElement("link"); l.rel = "stylesheet"; l.href = href; document.head.append(l); } };
  async function showBoard(rest) {
    view.className = "page game-page";
    view.innerHTML = `<p class="muted">Opening the board...</p>`;
    const [gid, ply] = rest.split("/").map(decodeURIComponent);
    let line = { fen: undefined, moves: [], at: 0, orientation: "white", title: "Analysis board" };
    try {
      ["vendor/chessground/chessground.base.css", "vendor/chessground/chessground.cburnett.css", "analysis/analysis-board.css"].forEach(css);
      await need("rules.js");
      const mod = await import("./analysis/analysis-board.js");
      if (gid) {
        const p = player();
        if (!games.length && p) { const s = await Games.saved(p.site, p.user); if (s) games = s.games; }
        const g = games.find(x => x.id === gid);
        if (g) line = { fen: g.startFen, moves: Games.sansOf(g), at: Number(ply) || 0, orientation: g.me === "b" ? "black" : "white",
          title: `vs ${g.me === "w" ? g.black : g.white}`, back: "#/game/" + encodeURIComponent(gid) };
      }
      if (!location.hash.startsWith("#/board")) return;   // the player went elsewhere meanwhile
      view.innerHTML = `<div class="links"><a href="${line.back || "#/games"}" class="btn ghost small">‹ ${line.back ? "Game" : "Games"}</a>
        <span class="muted small">${esc(line.title)}</span></div><div id="ab"></div>`;
      board = mod.mountAnalysisBoard(view.querySelector("#ab"), { rules: Rules, fen: line.fen, moves: line.moves, at: line.at, orientation: line.orientation });
    } catch (x) {
      view.innerHTML = `<p class="error">The board couldn't open: ${esc(x.message)}</p><a href="#/games">Back</a>`;
    }
  }

  // ---------- which screen ----------
  function route() {
    keys = null;
    if (board) { board.destroy(); board = null; }
    view.className = "page";
    const h = location.hash || "#/";
    if (h.startsWith("#/board")) showBoard(h.slice(8));
    else if (h.startsWith("#/game/")) showGame(decodeURIComponent(h.slice(7)));
    else if (h === "#/games") showGames();
    else if (player() && h === "#/" && !route.started) { location.hash = "#/games"; }
    else showStart();
    route.started = true;
    document.querySelectorAll(".tabs a").forEach(a => a.classList.toggle("on",
      a.getAttribute("href") === "#/board" ? h.startsWith("#/board") : h.startsWith("#/game")));
    window.scrollTo(0, 0);
  }
  addEventListener("hashchange", route);
  route();

  // ---------- installable, and works offline ----------
  if ("serviceWorker" in navigator) addEventListener("load", () => navigator.serviceWorker.register("sw.js").catch(() => {}));
  let ask = null;
  const installBtn = document.getElementById("install");
  addEventListener("beforeinstallprompt", e => { e.preventDefault(); ask = e; installBtn.hidden = false; });
  installBtn.onclick = async () => { if (!ask) return; ask.prompt(); await ask.userChoice; ask = null; installBtn.hidden = true; };
})();
