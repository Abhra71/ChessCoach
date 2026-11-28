// The rules of chess, just enough to replay a finished game: read a move written like "Nf3" or "exd5"
// and work out which piece moved from where. No library, no engine.
//
// How it works (a good file to learn from):
//   1. The board is a list of 64 squares, a8 first and h1 last, like a FEN string reads.
//   2. A move such as "Nbd7" says: a knight (N), from the b-file (b), lands on d7.
//   3. We look at every one of our knights, keep the ones that can reach d7 and match "b",
//      and drop any whose move would leave our own king in check (a pinned piece).
//   4. Exactly one should be left. If not, the game record is broken and we say so.
//
// Works in the browser (as the global Rules) and in Node (for tests: node tests/mobile/rules_test.js).
const Rules = (() => {
  const FILES = "abcdefgh";
  const START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

  const idx = sq => (8 - Number(sq[1])) * 8 + FILES.indexOf(sq[0]);   // "a8" -> 0, "h1" -> 63
  const name = i => FILES[i % 8] + (8 - Math.floor(i / 8));           // 0 -> "a8"
  const fileOf = i => i % 8, rankOf = i => 7 - Math.floor(i / 8);      // rank 0 = White's back row
  const white = p => p && p === p.toUpperCase();
  const colorOf = p => (p ? (white(p) ? "w" : "b") : null);

  // FEN text -> a position object we can change move by move
  function parse(fen) {
    const [rows, turn, castle, ep, half, full] = fen.trim().split(/\s+/);
    const board = [];
    for (const c of rows.replace(/\//g, "")) {
      if (/\d/.test(c)) for (let k = 0; k < Number(c); k++) board.push(null);
      else board.push(c);
    }
    if (board.length !== 64) throw new Error("Bad FEN: " + fen);
    return { board, turn: turn || "w", castle: castle || "-", ep: ep || "-",
      half: Number(half || 0), full: Number(full || 1) };
  }

  // the position object -> FEN text
  function fen(pos) {
    let out = "";
    for (let r = 0; r < 8; r++) {
      let empty = 0;
      for (let f = 0; f < 8; f++) {
        const p = pos.board[r * 8 + f];
        if (!p) { empty++; continue; }
        if (empty) { out += empty; empty = 0; }
        out += p;
      }
      if (empty) out += empty;
      if (r < 7) out += "/";
    }
    return `${out} ${pos.turn} ${pos.castle || "-"} ${pos.ep} ${pos.half} ${pos.full}`;
  }

  const KNIGHT = [[1, 2], [2, 1], [2, -1], [1, -2], [-1, -2], [-2, -1], [-2, 1], [-1, 2]];
  const KING = [[1, 0], [1, 1], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1]];
  const ROOK_DIRS = [[1, 0], [-1, 0], [0, 1], [0, -1]];
  const BISHOP_DIRS = [[1, 1], [1, -1], [-1, 1], [-1, -1]];

  // the square df files and dr ranks away, or -1 off the board
  function step(i, df, dr) {
    const f = fileOf(i) + df, r = rankOf(i) + dr;
    return f < 0 || f > 7 || r < 0 || r > 7 ? -1 : (7 - r) * 8 + f;
  }

  // can the piece standing on `from` attack `to`? (pawns: diagonal captures only)
  function attacks(board, from, to) {
    const p = board[from]; if (!p) return false;
    const t = p.toUpperCase(), df = fileOf(to) - fileOf(from), dr = rankOf(to) - rankOf(from);
    if (t === "P") return Math.abs(df) === 1 && dr === (white(p) ? 1 : -1);
    if (t === "N") return KNIGHT.some(([a, b]) => a === df && b === dr);
    if (t === "K") return Math.max(Math.abs(df), Math.abs(dr)) === 1;
    const straight = df === 0 || dr === 0, diagonal = Math.abs(df) === Math.abs(dr);
    if ((t === "R" && !straight) || (t === "B" && !diagonal) || (t === "Q" && !straight && !diagonal)) return false;
    if (df === 0 && dr === 0) return false;
    const sf = Math.sign(df), sr = Math.sign(dr);   // walk the line; every square between must be empty
    for (let i = step(from, sf, sr); i !== to; i = step(i, sf, sr)) if (i < 0 || board[i]) return false;
    return true;
  }

  // is square `sq` attacked by any piece of colour `by` ("w" or "b")?
  function attacked(board, sq, by) {
    for (let i = 0; i < 64; i++) if (colorOf(board[i]) === by && attacks(board, i, sq)) return true;
    return false;
  }

  function inCheck(pos, color = pos.turn) {
    const king = pos.board.indexOf(color === "w" ? "K" : "k");
    return king >= 0 && attacked(pos.board, king, color === "w" ? "b" : "w");
  }

  // can the piece on `from` move to `to` by its own way of moving (ignoring checks)?
  function reaches(pos, from, to) {
    const p = pos.board[from], target = pos.board[to];
    if (!p || colorOf(target) === colorOf(p)) return false;
    if (p.toUpperCase() !== "P") return attacks(pos.board, from, to);
    const dir = white(p) ? 1 : -1, df = fileOf(to) - fileOf(from), dr = rankOf(to) - rankOf(from);
    if (df === 0) {                              // straight ahead: the square(s) must be empty
      if (target) return false;
      if (dr === dir) return true;
      const home = white(p) ? 1 : 6;
      return dr === 2 * dir && rankOf(from) === home && !pos.board[step(from, 0, dir)];
    }
    return Math.abs(df) === 1 && dr === dir && (!!target || name(to) === pos.ep);   // capture, or en passant
  }

  // make a move { from, to, promo } and return the new position (the old one is left as it was)
  function play(pos, mv) {
    const b = pos.board.slice(), p = b[mv.from], t = p.toUpperCase(), me = colorOf(p);
    const capture = !!b[mv.to] || (t === "P" && fileOf(mv.from) !== fileOf(mv.to));
    if (t === "P" && !b[mv.to] && fileOf(mv.from) !== fileOf(mv.to)) b[step(mv.to, 0, me === "w" ? -1 : 1)] = null;  // en passant
    b[mv.to] = mv.promo ? (me === "w" ? mv.promo.toUpperCase() : mv.promo.toLowerCase()) : p;
    b[mv.from] = null;
    if (t === "K" && Math.abs(fileOf(mv.to) - fileOf(mv.from)) === 2) {   // castling: the rook jumps over
      const kingSide = fileOf(mv.to) === 6, row = me === "w" ? 7 : 0;
      b[row * 8 + (kingSide ? 5 : 3)] = b[row * 8 + (kingSide ? 7 : 0)];
      b[row * 8 + (kingSide ? 7 : 0)] = null;
    }
    let castle = pos.castle === "-" ? "" : pos.castle;   // a king or rook that moves (or a rook taken) ends castling there
    const lose = { 63: "K", 56: "Q", 7: "k", 0: "q" };
    if (t === "K") castle = castle.replace(me === "w" ? /[KQ]/g : /[kq]/g, "");
    for (const sq of [mv.from, mv.to]) if (lose[sq]) castle = castle.replace(lose[sq], "");
    const ep = t === "P" && Math.abs(rankOf(mv.to) - rankOf(mv.from)) === 2 ? name(step(mv.from, 0, me === "w" ? 1 : -1)) : "-";
    return { board: b, turn: me === "w" ? "b" : "w", castle: castle || "-", ep,
      half: t === "P" || capture ? 0 : pos.half + 1, full: pos.full + (me === "b" ? 1 : 0) };
  }

  // a move is legal if it doesn't leave your own king attacked
  const legal = (pos, mv) => !inCheck(play(pos, mv), pos.turn);

  // every legal move for the side to move: [{ from, to, promo }] (squares as numbers 0..63).
  // Used by the analysis board to know where a piece may go. Checked by "perft" counts in the tests.
  function moves(pos) {
    const out = [], me = pos.turn, them = me === "w" ? "b" : "w";
    for (let from = 0; from < 64; from++) {
      const p = pos.board[from];
      if (colorOf(p) !== me) continue;
      const lastRank = white(p) ? 7 : 0;
      for (let to = 0; to < 64; to++) {
        if (!reaches(pos, from, to)) continue;
        if (p.toUpperCase() === "P" && rankOf(to) === lastRank) {
          for (const promo of "qrbn") if (legal(pos, { from, to, promo })) out.push({ from, to, promo });
        } else if (legal(pos, { from, to })) out.push({ from, to, promo: null });
      }
    }
    // castling: the right still there, the squares between empty, and the king not in, through or into check
    const row = me === "w" ? 7 : 0, king = row * 8 + 4, rights = pos.castle || "";
    if (pos.board[king] === (me === "w" ? "K" : "k") && !inCheck(pos)) {
      const sides = [[me === "w" ? "K" : "k", 7, [5, 6], [5, 6]], [me === "w" ? "Q" : "q", 0, [1, 2, 3], [3, 2]]];
      for (const [right, rookFile, empty, safe] of sides) {
        if (!rights.includes(right) || pos.board[row * 8 + rookFile] !== (me === "w" ? "R" : "r")) continue;
        if (empty.some(f => pos.board[row * 8 + f])) continue;
        if (safe.some(f => attacked(pos.board, row * 8 + f, them))) continue;
        out.push({ from: king, to: row * 8 + safe[1], promo: null });
      }
    }
    return out;
  }

  // the move written the usual way ("Nbd7", "exd8=Q+", "O-O") for a { from, to, promo } move
  function toSan(pos, mv) {
    const p = pos.board[mv.from], t = p.toUpperCase();
    let san;
    if (t === "K" && Math.abs(fileOf(mv.to) - fileOf(mv.from)) === 2) san = fileOf(mv.to) === 6 ? "O-O" : "O-O-O";
    else {
      const capture = !!pos.board[mv.to] || (t === "P" && fileOf(mv.from) !== fileOf(mv.to));
      if (t === "P") san = (capture ? FILES[fileOf(mv.from)] + "x" : "") + name(mv.to) + (mv.promo ? "=" + mv.promo.toUpperCase() : "");
      else {
        const rivals = moves(pos).filter(m => m.to === mv.to && m.from !== mv.from && pos.board[m.from] === p);
        let which = "";
        if (rivals.length) {
          if (!rivals.some(m => fileOf(m.from) === fileOf(mv.from))) which = FILES[fileOf(mv.from)];
          else if (!rivals.some(m => rankOf(m.from) === rankOf(mv.from))) which = String(rankOf(mv.from) + 1);
          else which = name(mv.from);
        }
        san = t + which + (capture ? "x" : "") + name(mv.to);
      }
    }
    const next = play(pos, mv);
    if (inCheck(next)) san += moves(next).length ? "+" : "#";
    return san;
  }

  // "Nbd7", "exd8=Q+", "O-O" ... -> { from, to, promo, san } or throws an Error saying what's wrong
  function fromSan(pos, san) {
    const clean = san.replace(/[+#?!]+$/g, "").replace(/0/g, "O");
    const row = pos.turn === "w" ? 7 : 0, king = row * 8 + 4;
    if (clean === "O-O" || clean === "O-O-O") {
      const mv = { from: king, to: row * 8 + (clean === "O-O" ? 6 : 2) };
      if (pos.board[king] !== (pos.turn === "w" ? "K" : "k")) throw new Error(`Can't castle: ${san}`);
      return { ...mv, san };
    }
    const m = clean.match(/^([NBRQK])?([a-h])?([1-8])?x?([a-h][1-8])(?:=?([NBRQ]))?$/);
    if (!m) throw new Error(`Can't read the move "${san}"`);
    const [, piece = "P", fromFile, fromRank, to, promo] = m;
    const want = pos.turn === "w" ? piece : piece.toLowerCase(), target = idx(to);
    const found = [];
    for (let i = 0; i < 64; i++) {
      if (pos.board[i] !== want) continue;
      if (fromFile && FILES[fileOf(i)] !== fromFile) continue;
      if (fromRank && String(rankOf(i) + 1) !== fromRank) continue;
      const mv = { from: i, to: target, promo: promo || null };
      if (reaches(pos, i, target) && legal(pos, mv)) found.push(mv);
    }
    if (found.length !== 1) throw new Error(`The move "${san}" fits ${found.length} pieces`);
    return { ...found[0], san };
  }

  // a whole game: list of SAN moves -> list of positions (FEN), the start included, plus each move's squares
  function replay(sans, startFen = START) {
    let pos = parse(startFen);
    const fens = [fen(pos)], moves = [];
    for (const san of sans) {
      const mv = fromSan(pos, san);
      pos = play(pos, mv);
      fens.push(fen(pos));
      moves.push({ san, from: name(mv.from), to: name(mv.to), check: inCheck(pos) });
    }
    return { fens, moves };
  }

  return { START, parse, fen, fromSan, toSan, moves, play, replay, inCheck, name, idx };
})();

if (typeof module !== "undefined") module.exports = Rules;
