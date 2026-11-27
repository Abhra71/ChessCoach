// Knightwise on the phone (preview): three screens.
//   #/          who are you? (chess.com or Lichess username)
//   #/games     your newest finished games, with wins / losses / draws on top
//   #/game/ID   one game, move by move on a board
// Everything stays on this phone (localStorage). No server of ours, no engine yet (see docs/MOBILE-PLAN.md).
(() => {
  const view = document.getElementById("view");
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  let games = [];          // the games on screen right now
  let note = "";           // a line under the list: "saved 5 min ago", "offline", ...

  // ---------- who is playing (kept on the phone) ----------
  function player() { try { return JSON.parse(localStorage.getItem("kw.player") || "null"); } catch { return null; } }
  function setPlayer(p) { try { p ? localStorage.setItem("kw.player", JSON.stringify(p)) : localStorage.removeItem("kw.player"); } catch { } }

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
      if (!user) return;
      const btn = view.querySelector(".btn.primary"), err = view.querySelector("#err");
      btn.disabled = true; btn.textContent = "Downloading your games..."; err.hidden = true;
      try {
        games = await Games.load(site, user);
        if (!games.length) throw new Error("no-games");
        setPlayer({ site, user }); note = "Updated just now.";
        location.hash = "#/games";
      } catch (x) {
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
      const s = Games.saved(p.site, p.user);
      if (s) { games = s.games; note = `Saved ${ago(s.at)}.`; }
    }
    drawGames(p);
    if (!note.startsWith("Updated")) refresh(p);
  }

  async function refresh(p) {
    try {
      games = await Games.load(p.site, p.user);
      note = "Updated just now.";
    } catch {
      note = navigator.onLine ? "Couldn't update; showing the saved games." : "Offline; showing the saved games.";
    }
    if (location.hash === "#/games") drawGames(p);
  }

  function drawGames(p) {
    const n = r => games.filter(g => g.result === r).length;
    view.innerHTML = `
      <div class="links"><h1>${esc(p.user)}</h1>
        <button id="change" class="btn ghost small">Change player</button></div>
      <p class="sub small">${games.length} newest finished games on ${p.site === "lichess" ? "Lichess" : "chess.com"}. ${esc(note)}</p>
      <div class="stats">
        <div class="stat"><b class="num">${n("win")}</b><span>won</span></div>
        <div class="stat"><b class="num">${n("loss")}</b><span>lost</span></div>
        <div class="stat"><b class="num">${n("draw")}</b><span>drawn</span></div>
      </div>
      <h2>Games</h2>
      <ul class="games">${games.map(g => {
        const opp = g.me === "w" ? g.black : g.white, oppR = g.me === "w" ? g.blackRating : g.whiteRating;
        return `<li><a class="game" href="#/game/${encodeURIComponent(g.id)}">
          <span class="chip ${g.result}">${g.result === "win" ? "W" : g.result === "loss" ? "L" : "½"}</span>
          <span class="grow"><div class="who">${esc(opp)} <span class="muted small num">${esc(oppR || "")}</span></div>
            <div class="meta">${esc(g.how)} · ${esc(g.speed)} · ${Math.ceil(g.sans.length / 2)} moves · ${dateOf(g.endedAt)}</div></span>
          <span class="side ${g.me}" title="You played ${g.me === "w" ? "White" : "Black"}"></span></a></li>`;
      }).join("")}</ul>`;
    view.querySelector("#change").onclick = () => { setPlayer(null); games = []; note = ""; location.hash = "#/"; };
  }

  // ---------- screen 3: one game on the board ----------
  function showGame(id) {
    const p = player();
    if (!games.length && p) { const s = Games.saved(p.site, p.user); if (s) games = s.games; }
    const g = games.find(x => x.id === id);
    if (!g) { location.hash = "#/games"; return; }
    let line;
    try { line = Rules.replay(g.sans, g.startFen); }
    catch (x) { view.innerHTML = `<p class="error">This game's record couldn't be read: ${esc(x.message)}</p><a href="#/games">Back</a>`; return; }
    const flip = g.me === "b", last = line.fens.length - 1;
    let at = last;   // open at the end: how it finished
    const top = flip ? ["w", g.white, g.whiteRating] : ["b", g.black, g.blackRating];
    const bottom = flip ? ["b", g.black, g.blackRating] : ["w", g.white, g.whiteRating];
    const word = { win: "You won", loss: "You lost", draw: "Draw" }[g.result];

    view.className = "page game-page";
    view.innerHTML = `
      <div class="links"><a href="#/games" class="btn ghost small">‹ Games</a>
        <a href="${esc(g.url)}" target="_blank" rel="noopener" class="btn ghost small">Open on ${esc(g.site)}</a></div>
      <div class="game-grid"><div>
        <div class="players"><span>${esc(top[1])} <span class="r num">${esc(top[2] || "")}</span></span></div>
        <div class="board-wrap" id="board"></div>
        <div class="players"><span>${esc(bottom[1])} <span class="r num">${esc(bottom[2] || "")}</span></span></div>
        <div class="controls">
          <button class="btn" data-go="start" aria-label="Start">⏮</button>
          <button class="btn" data-go="back" aria-label="Back">◀</button>
          <button class="btn" data-go="next" aria-label="Next">▶</button>
          <button class="btn" data-go="end" aria-label="End">⏭</button>
        </div>
        <p class="ply" id="ply"></p>
      </div><div>
        <p class="end">${word}${g.how ? ", " + esc(g.how) : ""}${g.opening ? `<br><span class="muted small">${esc(g.opening)}</span>` : ""}</p>
        <div class="moves" id="moves">${line.moves.map((m, i) =>
          `${i % 2 === 0 ? `<span class="n">${i / 2 + 1}.</span>` : ""}<button data-i="${i + 1}">${esc(m.san)}</button>`).join("")}</div>
      </div></div>`;

    const boardEl = view.querySelector("#board"), ply = view.querySelector("#ply");
    function draw() {
      const hl = {}, m = line.moves[at - 1];
      if (m) { hl[m.from] = "hl-last"; hl[m.to] = "hl-last"; }
      if (m && m.check) {                              // the king in check gets a red square
        const pos = Rules.parse(line.fens[at]), k = pos.board.indexOf(pos.turn === "w" ? "K" : "k");
        if (k >= 0) hl[Rules.name(k)] = "hl-check";
      }
      Board.render(boardEl, { fen: line.fens[at], flip, highlights: hl });
      ply.textContent = at === 0 ? "Start position" : `Move ${Math.ceil(at / 2)}${at % 2 ? "" : "…"} ${m.san} · ${at} of ${last}`;
      view.querySelectorAll("#moves button").forEach(b => {
        const on = Number(b.dataset.i) === at;
        b.classList.toggle("on", on);
        if (on) b.parentNode.scrollTop = b.offsetTop - b.parentNode.clientHeight / 2;   // only the list scrolls, not the page
      });
    }
    const go = to => { at = Math.max(0, Math.min(last, to)); draw(); };
    const moves = { start: () => go(0), back: () => go(at - 1), next: () => go(at + 1), end: () => go(last) };
    view.querySelectorAll("[data-go]").forEach(b => b.onclick = moves[b.dataset.go]);
    view.querySelectorAll("#moves button").forEach(b => b.onclick = () => go(Number(b.dataset.i)));
    // swipe the board left or right to step through the game
    let x0 = null;
    boardEl.addEventListener("touchstart", e => { x0 = e.touches[0].clientX; }, { passive: true });
    boardEl.addEventListener("touchend", e => {
      if (x0 === null) return;
      const dx = e.changedTouches[0].clientX - x0; x0 = null;
      if (Math.abs(dx) > 30) go(at + (dx < 0 ? 1 : -1));
    });
    keys = e => { if (e.key === "ArrowLeft") moves.back(); if (e.key === "ArrowRight") moves.next(); };
    draw();
  }
  let keys = null;
  document.addEventListener("keydown", e => keys && keys(e));

  // ---------- which screen ----------
  function route() {
    keys = null;
    view.className = "page";
    const h = location.hash || "#/";
    if (h.startsWith("#/game/")) showGame(decodeURIComponent(h.slice(7)));
    else if (h === "#/games") showGames();
    else if (player() && h === "#/" && !route.started) { location.hash = "#/games"; }
    else showStart();
    route.started = true;
    window.scrollTo(0, 0);
  }
  addEventListener("hashchange", route);
  route();

  // ---------- installable, and works offline ----------
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
  let ask = null;
  const installBtn = document.getElementById("install");
  addEventListener("beforeinstallprompt", e => { e.preventDefault(); ask = e; installBtn.hidden = false; });
  installBtn.onclick = async () => { if (!ask) return; ask.prompt(); await ask.userChoice; ask = null; installBtn.hidden = true; };
})();
