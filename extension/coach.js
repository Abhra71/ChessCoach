// Knightwise on chess.com: arrows and a short note on the key moments of YOUR FINISHED games.
//
// Fair play: the coach on your computer only knows games that chess.com has already archived as finished.
// For any other game (including one being played right now) it answers "unknown" and this script shows nothing.
(() => {
  const FILES = "abcdefgh";
  const COLORS = { mine: "#e5484d", reply: "#f0a43a", best: "#2fb56f" };
  const LABELS = { mine: "You played", reply: "Reply", best: "Better" };
  let moments = [], overlay = null, panel = null, timer = null, gameId = null;
  let small = false;
  let maya = { mood: "calm", line: "" };  // Maya, the coach for game reviews: her face and her first line
  try { small = localStorage.getItem("chess-coach-small") === "1"; } catch (e) {}

  function idFromUrl() {
    const m = location.pathname.match(/\/game\/(?:live|daily)\/(\d+)/);
    return m ? m[1] : null;
  }

  function boardEl() { return document.querySelector("wc-chess-board"); }

  // Piece placement as in a FEN ("rnbqkbnr/pppppppp/8/...") read from chess.com's piece elements.
  function placement(board) {
    const grid = Array.from({ length: 8 }, () => Array(8).fill(null));
    board.querySelectorAll(".piece").forEach(el => {
      const cls = [...el.classList];
      const kind = cls.find(c => /^[wb][pnbrqk]$/.test(c));
      const sq = cls.find(c => /^square-\d\d$/.test(c));
      if (!kind || !sq) return;
      const file = Number(sq[7]) - 1, rank = Number(sq[8]) - 1;
      if (file < 0 || file > 7 || rank < 0 || rank > 7) return;
      grid[rank][file] = kind[0] === "w" ? kind[1].toUpperCase() : kind[1];
    });
    const rows = [];
    for (let rank = 7; rank >= 0; rank--) {
      let row = "", empty = 0;
      for (let file = 0; file < 8; file++) {
        const p = grid[rank][file];
        if (!p) { empty++; continue; }
        if (empty) { row += empty; empty = 0; }
        row += p;
      }
      rows.push(row + (empty || ""));
    }
    return rows.join("/");
  }

  function center(square, flipped) {
    const f = FILES.indexOf(square[0]), r = Number(square[1]) - 1;
    return [(flipped ? 7 - f : f) * 100 + 50, (flipped ? r : 7 - r) * 100 + 50];
  }

  // kind: "best" | "mine" | "reply"; every arrow carries its meaning written on it
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
    const board = boardEl();
    if (!board || !moments.length) return;
    if (!overlay || !board.contains(overlay)) {
      overlay = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      overlay.setAttribute("viewBox", "0 0 800 800");
      overlay.classList.add("chess-coach-arrows");
      board.appendChild(overlay);
    }
    const now = placement(board), flipped = board.classList.contains("flipped");
    clearArrows();
    let active = null;
    for (const m of moments) {
      if (now === m.placement) {          // just before your move: the better move, and your move (fainter)
        overlay.innerHTML = arrow(m.move_uci, "mine", flipped, true) + arrow(m.best_uci, "best", flipped);
        active = { m, when: "before" };
        break;
      }
      if (now === m.after_placement) {    // just after your move: your move and their answer
        overlay.innerHTML = arrow(m.move_uci, "mine", flipped) +
          (m.reply_uci ? arrow(m.reply_uci, "reply", flipped) : "");
        active = { m, when: "after" };
        break;
      }
    }
    renderPanel(active);
  }

  function goTo(m, when) {
    // chess.com numbers the moves in its list 0-0, 0-1, ... (one per half-move)
    const ply = when === "before" ? m.ply - 2 : m.ply - 1;
    const node = ply < 0 ? null : document.querySelector(`[data-node="0-${ply}"]`);
    if (node) node.click();
    setTimeout(draw, 300);
  }

  function renderPanel(active) {
    if (!panel) {
      panel = document.createElement("div");
      panel.className = "chess-coach-panel";
      document.body.appendChild(panel);
    }
    const items = moments.map((m, i) => {
      const on = active && active.m === m;
      return `<li class="${on ? "on" : ""}" data-i="${i}">
        <b>Move ${m.move_number}</b> · ${escapeHtml(m.pattern)}
        <div class="say">${escapeHtml(m.say)}</div>
        ${on ? (active.when === "before"
          ? `<div class="key"><span style="background:${COLORS.best}"></span>better: ${escapeHtml(m.best)}
             <span style="background:${COLORS.mine}"></span>you played ${escapeHtml(m.move)}</div>
             <button data-go="after" data-i="${i}">What happened next</button>`
          : `<div class="key"><span style="background:${COLORS.mine}"></span>your move ${escapeHtml(m.move)}
             <span style="background:${COLORS.reply}"></span>their answer</div>
             <button data-go="before" data-i="${i}">Show the better move</button>`) : ""}
      </li>`;
    }).join("");
    panel.classList.toggle("small", small);
    panel.innerHTML = small
      ? `<button class="pill">Maya · ${moments.length} key moment${moments.length === 1 ? "" : "s"}</button>`
      : `<div class="head"><span class="who"><span class="kw-mini">${KnightwiseFaces.svg("maya", maya.mood)}</span>` +
        `<span><b>Maya</b><small>Game reviews</small></span></span><span><button class="min" title="Make small">–</button>` +
        `<button class="x" title="Close for this game">×</button></span></div>
      <p>${escapeHtml(maya.line)}</p>
      <ol>${items}</ol>`;
    const setSmall = v => {
      small = v;
      try { localStorage.setItem("chess-coach-small", v ? "1" : "0"); } catch (e) {}
      renderPanel(active);
    };
    if (small) { panel.querySelector(".pill").onclick = () => setSmall(false); return; }
    panel.querySelector(".min").onclick = e => { e.stopPropagation(); setSmall(true); };
    panel.querySelector(".x").onclick = () => { panel.remove(); panel = null; moments = []; clearArrows(); };
    panel.querySelectorAll("li").forEach(li => li.onclick = e => {
      const m = moments[Number(li.dataset.i)];
      const go = e.target.dataset && e.target.dataset.go;
      goTo(m, go || "before");
    });
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  }

  function ask(id) {
    return new Promise(resolve => {
      try { chrome.runtime.sendMessage({ type: "game", id }, r => resolve(r && r.ok ? r.data : null)); }
      catch (e) { resolve(null); }
    });
  }

  const WAIT_EVERY = 60000, WAIT_FOR = 15 * 60000;  // a game that isn't archived yet: ask again, for a while
  let waiting = null;

  // Instant review. The coach only knows a game once chess.com's public archive lists it as finished, so while a
  // game is being played this shows nothing. When it ends and chess.com archives it, the app checks it at once.
  async function start() {
    const id = idFromUrl();
    if (!id || id === gameId) return;
    gameId = id;
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

  async function show(id, data) {
    if (!data.moments.length) return;  // a clean game: nothing to show on the board
    moments = data.moments;
    const n = moments.length;
    maya = { mood: "calm", line: `${n} key moment${n === 1 ? "" : "s"} in this game. Click one to see it on the board.` };
    const r = await new Promise(res => {
      try { chrome.runtime.sendMessage({ type: "coach", section: "review", game: id, hour: new Date().getHours() }, res); }
      catch (e) { res(null); }
    });
    if (gameId !== id) return;
    if (r && r.ok && r.data.lines.length) {
      maya = { mood: r.data.mood, line: r.data.lines[0] };
      if (r.data.voice_on) chrome.runtime.sendMessage({ type: "say", text: maya.line, voice: r.data.voice });
    }
    draw();
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
