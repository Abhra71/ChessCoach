// The analysis board: a free board to think on. Move either side, step back and forth, draw arrows and circles,
// set up any position. NO ENGINE, ever (owner's decision, 28 Nov 2026): it's a wooden board on a screen, nothing
// more, so it can never become a way to get help during a game.
//
// A self-contained piece, so the PC app can use it too:
//   import { mountAnalysisBoard } from "./analysis/analysis-board.js";
//   const board = mountAnalysisBoard(element, { fen, moves: ["e4", "e5"], at: 2, orientation: "white", rules: Rules });
//   board.load(fen, moves, at);  board.fen();  board.destroy();
// Needs: chessground (vendor/chessground, Lichess's board, GPL-3.0-or-later) and rules.js (our chess rules).
import { Chessground } from "../vendor/chessground/chessground.min.js";

const PIECE_NAMES = { p: "pawn", n: "knight", b: "bishop", r: "rook", q: "queen", k: "king" };
const LETTER = { pawn: "p", knight: "n", bishop: "b", rook: "r", queen: "q", king: "k" };
const BRUSHES = ["green", "red", "blue", "yellow"];
const esc = s => String(s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

export function mountAnalysisBoard(root, opts = {}) {
  const R = opts.rules || globalThis.Rules;
  if (!R) throw new Error("rules.js must be loaded before the analysis board");

  // the line on the board: positions[0] is the start, moves[i] leads from positions[i] to positions[i + 1]
  let positions = [], moves = [], at = 0, orientation = opts.orientation || "white";
  let shapes = {};            // arrows and circles you drew, kept per position (by its FEN)
  let mode = "play";          // "play" | "draw" | "setup"
  let brush = "green", drawFrom = null;
  let setupPiece = null;      // in setup: the piece you tapped in the palette, or "delete"
  let setupTurn = "w";

  root.classList.add("ab");
  root.innerHTML = `
    <div class="ab-board-wrap"><div class="ab-board"></div><div class="ab-promo" hidden></div></div>
    <div class="ab-tools" data-for="play draw">
      <button class="ab-btn" data-go="start" aria-label="Start">⏮</button>
      <button class="ab-btn" data-go="back" aria-label="Back">◀</button>
      <button class="ab-btn" data-go="next" aria-label="Next">▶</button>
      <button class="ab-btn" data-go="end" aria-label="End">⏭</button>
    </div>
    <div class="ab-row" data-for="play draw">
      <button class="ab-btn ab-draw" aria-pressed="false">✎ Draw</button>
      <span class="ab-brushes" hidden>${BRUSHES.map(b => `<button class="ab-brush ${b}" data-brush="${b}" aria-label="${b}"></button>`).join("")}
        <button class="ab-btn small ab-clear">Clear</button></span>
      <button class="ab-btn ab-flip" aria-label="Flip the board">⇅</button>
      <button class="ab-btn ab-setup-open">Set up</button>
    </div>
    <div class="ab-setup" data-for="setup" hidden>
      <div class="ab-palette"></div>
      <div class="ab-row">
        <span class="ab-seg"><button data-turn="w">White to move</button><button data-turn="b">Black to move</button></span>
      </div>
      <div class="ab-row">
        <button class="ab-btn small" data-fill="start">Start position</button>
        <button class="ab-btn small" data-fill="empty">Empty board</button>
        <button class="ab-btn small ab-flip">⇅</button>
      </div>
      <input class="ab-fen" spellcheck="false" autocapitalize="off" aria-label="Position as FEN">
      <p class="ab-err" hidden></p>
      <button class="ab-btn primary ab-setup-done">Done</button>
    </div>
    <p class="ab-line" data-for="play draw"></p>
    <div class="ab-moves" data-for="play draw"></div>
    <p class="ab-note">No engine here. Using any board during a live game breaks chess.com's and Lichess's rules.</p>`;
  const $ = s => root.querySelector(s), $$ = s => root.querySelectorAll(s);

  const cg = Chessground($(".ab-board"), {
    coordinates: true, orientation, animation: { duration: 160 },
    highlight: { lastMove: true, check: true },
    movable: { free: false, showDests: true, events: { after: onMove } },
    premovable: { enabled: false },
    draggable: { enabled: true, showGhost: true },
    selectable: { enabled: true },
    drawable: { enabled: true, visible: true, eraseOnClick: false, onChange: s => { shapes[cur().fen] = s; } },  // right-click drawing on a PC
    events: { select: onSelect },
  });

  // ---------- the position on the board ----------
  const cur = () => positions[at];
  function dests(pos) {   // where each piece may go: Map("e2" -> ["e3", "e4"])
    const m = new Map();
    for (const mv of R.moves(pos)) {
      const f = R.name(mv.from), t = R.name(mv.to);
      if (!m.has(f)) m.set(f, []);
      if (!m.get(f).includes(t)) m.get(f).push(t);
    }
    return m;
  }
  function draw() {
    const p = cur(), last = moves[at - 1];
    const color = p.pos.turn === "w" ? "white" : "black";
    cg.set({
      fen: p.fen.split(" ")[0], orientation, turnColor: color,
      lastMove: last ? [last.from, last.to] : undefined,
      check: R.inCheck(p.pos) ? color : false,
      movable: mode === "play" ? { free: false, color, dests: dests(p.pos) } : { free: false, color: undefined, dests: new Map() },
      draggable: { enabled: mode === "play" },
    });
    cg.setShapes(shapes[p.fen] || []);
    $(".ab-line").textContent = at === 0 ? (moves.length ? "Start of the line" : `${p.pos.turn === "w" ? "White" : "Black"} to move`)
      : `${Math.ceil(at / 2)}${at % 2 ? "." : "…"} ${last.san} · ${at} of ${moves.length}`;
    const list = $(".ab-moves");
    list.innerHTML = moves.map((m, i) => {
      const n = R.parse(positions[i].fen).full, white = positions[i].pos.turn === "w";
      const num = white ? `<span class="n">${n}.</span>` : i === 0 ? `<span class="n">${n}…</span>` : "";
      return `${num}<button data-i="${i + 1}" class="${i + 1 === at ? "on" : ""}">${esc(m.san)}</button>`;
    }).join("");
    const on = list.querySelector(".on");
    if (on) list.scrollTop = on.offsetTop - list.clientHeight / 2;
  }

  function load(fen = R.START, sans = [], start = sans.length) {
    let pos = R.parse(fen);
    positions = [{ pos, fen: R.fen(pos) }]; moves = []; shapes = {};
    for (const san of sans) {
      const mv = R.fromSan(pos, san);
      pos = R.play(pos, mv);
      moves.push({ san: R.toSan(positions.at(-1).pos, mv), from: R.name(mv.from), to: R.name(mv.to) });
      positions.push({ pos, fen: R.fen(pos) });
    }
    at = Math.max(0, Math.min(moves.length, start));
    draw();
  }

  // ---------- playing moves (either side) ----------
  function onMove(from, to) {
    const before = cur().pos, fromI = R.idx(from), toI = R.idx(to);
    const options = R.moves(before).filter(m => m.from === fromI && m.to === toI);
    if (!options.length) return draw();
    if (options.length > 1) return askPromotion(before, options, from, to);   // a pawn reached the last row
    add(before, options[0]);
  }
  function add(before, mv) {
    const san = R.toSan(before, mv), pos = R.play(before, mv);
    // a new move from the middle of the line replaces what came after (one line, like a real board)
    if (moves[at] && moves[at].san === san) { at++; return draw(); }
    moves = moves.slice(0, at); positions = positions.slice(0, at + 1);
    moves.push({ san, from: R.name(mv.from), to: R.name(mv.to) });
    positions.push({ pos, fen: R.fen(pos) });
    at++;
    draw();
    if (opts.onChange) opts.onChange({ fen: cur().fen, moves: moves.map(m => m.san), at });
  }
  function askPromotion(before, options, from, to) {
    const box = $(".ab-promo"), color = before.turn === "w" ? "white" : "black";
    box.innerHTML = `<p>Promote to</p>` + ["q", "r", "b", "n"].map(p =>
      `<button data-p="${p}" aria-label="${PIECE_NAMES[p]}"><span class="cg-wrap ab-piece"><piece class="${PIECE_NAMES[p]} ${color}"></piece></span></button>`).join("") +
      `<button class="ab-btn small" data-p="">Cancel</button>`;
    box.hidden = false;
    box.onclick = e => {
      const b = e.target.closest("button"); if (!b) return;
      box.hidden = true;
      const mv = options.find(m => m.promo === b.dataset.p);
      mv ? add(before, mv) : draw();
    };
  }

  // ---------- drawing arrows and circles by tapping (phones have no right-click) ----------
  function onSelect(key) {
    if (mode === "setup") return placePiece(key);
    if (mode !== "draw") return;
    if (!drawFrom) { drawFrom = key; cg.set({ selected: key }); return; }
    const shape = drawFrom === key ? { orig: key, brush } : { orig: drawFrom, dest: key, brush };
    drawFrom = null;
    const list = shapes[cur().fen] || [], same = s => s.orig === shape.orig && s.dest === shape.dest;
    shapes[cur().fen] = list.some(same) ? list.filter(s => !same(s)) : [...list, shape];   // tap again to remove
    cg.selectSquare(null);
    cg.setShapes(shapes[cur().fen]);
  }

  // ---------- setting up a position ----------
  function palette() {
    const pieces = ["k", "q", "r", "b", "n", "p"];
    $(".ab-palette").innerHTML = ["white", "black"].map(c => pieces.map(p =>
      `<button data-piece="${c} ${PIECE_NAMES[p]}" aria-label="${c} ${PIECE_NAMES[p]}"><span class="cg-wrap ab-piece"><piece class="${PIECE_NAMES[p]} ${c}"></piece></span></button>`).join("")).join("") +
      `<button data-piece="delete" class="ab-del" aria-label="Remove a piece">✕</button>`;
  }
  function placePiece(key) {
    if (!setupPiece) return;
    const map = new Map();
    if (setupPiece === "delete") map.set(key, undefined);
    else { const [color, role] = setupPiece.split(" "); map.set(key, { color, role }); }
    cg.setPieces(map);
    showSetupFen();
  }
  function boardFen() {   // the pieces chessground shows -> the first part of a FEN
    const rows = [];
    for (let r = 8; r >= 1; r--) {
      let row = "", empty = 0;
      for (const f of "abcdefgh") {
        const p = cg.state.pieces.get(f + r);
        if (!p) { empty++; continue; }
        if (empty) { row += empty; empty = 0; }
        const l = LETTER[p.role]; row += p.color === "white" ? l.toUpperCase() : l;
      }
      rows.push(row + (empty || ""));
    }
    return rows.join("/");
  }
  function castlingFor(rows) {   // castling allowed only when the king and rook still stand at home
    const pos = R.parse(`${rows} w - - 0 1`), at = sq => pos.board[R.idx(sq)];
    let c = "";
    if (at("e1") === "K") { if (at("h1") === "R") c += "K"; if (at("a1") === "R") c += "Q"; }
    if (at("e8") === "k") { if (at("h8") === "r") c += "k"; if (at("a8") === "r") c += "q"; }
    return c || "-";
  }
  const setupFen = () => { const rows = boardFen(); return `${rows} ${setupTurn} ${castlingFor(rows)} - 0 1`; };
  function showSetupFen() { $(".ab-fen").value = setupFen(); $(".ab-err").hidden = true; }
  function problem(fen) {   // why this position can't be played, in plain words (or "" if it's fine)
    let pos; try { pos = R.parse(fen); } catch { return "That isn't a position Knightwise can read."; }
    const count = p => pos.board.filter(x => x === p).length;
    if (count("K") !== 1 || count("k") !== 1) return "Each side needs exactly one king.";
    if (pos.board.slice(0, 8).concat(pos.board.slice(56)).some(p => p && p.toUpperCase() === "P")) return "Pawns can't stand on the first or last row.";
    if (R.inCheck(pos, pos.turn === "w" ? "b" : "w")) return `${pos.turn === "w" ? "Black" : "White"} is in check, but it's ${pos.turn === "w" ? "White" : "Black"}'s move.`;
    return "";
  }
  function setMode(m) {
    mode = m; drawFrom = null;
    $$("[data-for]").forEach(el => { el.hidden = !el.dataset.for.split(" ").includes(m); });
    $(".ab-draw").setAttribute("aria-pressed", String(m === "draw"));
    $(".ab-brushes").hidden = m !== "draw";
    root.classList.toggle("ab-drawing", m === "draw");
    if (m === "setup") {
      setupTurn = cur().pos.turn; setupPiece = null; palette();
      $$("[data-turn]").forEach(b => b.classList.toggle("on", b.dataset.turn === setupTurn));
      cg.set({ fen: cur().fen.split(" ")[0], lastMove: undefined, check: false, movable: { free: true, color: "both", dests: new Map() },
        draggable: { enabled: true, deleteOnDropOff: true }, events: { change: showSetupFen } });
      cg.setShapes([]);
      showSetupFen();
    } else {
      cg.set({ draggable: { deleteOnDropOff: false }, events: { change: undefined } });
      draw();
    }
  }

  // ---------- buttons ----------
  const go = to => { at = Math.max(0, Math.min(moves.length, to)); draw(); };
  const steps = { start: () => go(0), back: () => go(at - 1), next: () => go(at + 1), end: () => go(moves.length) };
  root.addEventListener("click", e => {
    const b = e.target.closest("button"); if (!b || !root.contains(b)) return;
    if (b.dataset.go) steps[b.dataset.go]();
    else if (b.dataset.i) go(Number(b.dataset.i));
    else if (b.classList.contains("ab-draw")) setMode(mode === "draw" ? "play" : "draw");
    else if (b.dataset.brush) { brush = b.dataset.brush; $$(".ab-brush").forEach(x => x.classList.toggle("on", x === b)); }
    else if (b.classList.contains("ab-clear")) { shapes[cur().fen] = []; cg.setShapes([]); }
    else if (b.classList.contains("ab-flip")) { orientation = orientation === "white" ? "black" : "white"; cg.set({ orientation }); }
    else if (b.classList.contains("ab-setup-open")) setMode("setup");
    else if (b.dataset.piece) {
      setupPiece = setupPiece === b.dataset.piece ? null : b.dataset.piece;
      $$("[data-piece]").forEach(x => x.classList.toggle("on", x.dataset.piece === setupPiece));
      // a palette piece chosen: taps only place it (the board's own select-and-move would fight it);
      // none chosen: drag pieces around freely, or off the board to remove them
      cg.selectSquare(null);
      cg.set(setupPiece ? { movable: { color: undefined }, draggable: { enabled: false } }
                        : { movable: { free: true, color: "both" }, draggable: { enabled: true, deleteOnDropOff: true } });
    }
    else if (b.dataset.turn) { setupTurn = b.dataset.turn; $$("[data-turn]").forEach(x => x.classList.toggle("on", x === b)); showSetupFen(); }
    else if (b.dataset.fill) {
      cg.set({ fen: b.dataset.fill === "start" ? R.START.split(" ")[0] : "8/8/8/8/8/8/8/8" });
      if (b.dataset.fill === "start") { setupTurn = "w"; $$("[data-turn]").forEach(x => x.classList.toggle("on", x.dataset.turn === "w")); }
      showSetupFen();
    }
    else if (b.classList.contains("ab-setup-done")) {
      const fen = $(".ab-fen").value.trim(), why = problem(fen);
      if (why) { const err = $(".ab-err"); err.textContent = why; err.hidden = false; return; }
      const p = R.parse(fen);
      p.castle = castlingFor(fen.split(" ")[0]).split("").filter(c => (p.castle || "").includes(c)).join("") || "-";  // never more than the pieces allow
      mode = "play"; load(R.fen(p), [], 0); setMode("play");
    }
  });
  $(".ab-fen").addEventListener("change", () => {   // a pasted FEN shows on the board at once if it can be read
    try { const p = R.parse($(".ab-fen").value); cg.set({ fen: R.fen(p).split(" ")[0] }); setupTurn = p.turn;
      $$("[data-turn]").forEach(x => x.classList.toggle("on", x.dataset.turn === setupTurn)); $(".ab-err").hidden = true; }
    catch { const err = $(".ab-err"); err.textContent = "That isn't a position Knightwise can read."; err.hidden = false; }
  });
  const keys = e => {
    if (mode === "setup" || /INPUT|TEXTAREA/.test(document.activeElement?.tagName || "")) return;
    if (e.key === "ArrowLeft") steps.back(); if (e.key === "ArrowRight") steps.next();
  };
  document.addEventListener("keydown", keys);

  load(opts.fen || R.START, opts.moves || [], opts.at ?? (opts.moves || []).length);
  setMode("play");
  $(`[data-brush="${brush}"]`).classList.add("on");

  return {
    load,
    fen: () => cur().fen,
    line: () => ({ moves: moves.map(m => m.san), at }),
    destroy() { document.removeEventListener("keydown", keys); cg.destroy(); root.innerHTML = ""; root.classList.remove("ab"); },
  };
}
