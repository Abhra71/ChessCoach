// Everything Knightwise reads from chess.com's pages, in one place, each with a check.
//
// chess.com changes its site without notice. On 13 Oct 2026 live games moved from /game/live/<id> to /game/<id>
// (and /live/game/<id>), and the review silently stopped appearing. So: every address and element we use is listed
// here with its backups; the page scripts use only these; and each one tells the Knightwise app whether it was
// found (the self-check, coach/health.py, shown in Settings). A broken one pauses only its feature, honestly.
//
// Fair play: nothing here reads a game that is still being played. The review asks the app first, and the app
// only knows games chess.com has archived as finished.
const KnightwiseContract = (() => {
  // the game page: every address chess.com has used for a game, newest first. The id is the game number.
  const GAME_ADDRESSES = [
    /^\/game\/(?:live\/|daily\/)?(\d+)(?:[/?#]|$)/,  // /game/123 (2026), /game/live/123, /game/daily/123
    /^\/live\/game\/(\d+)(?:[/?#]|$)/,                // /live/game/123 (where /game/123 forwards to)
    /^\/analysis\/game\/(?:live|daily)\/(\d+)(?:[/?#]|$)/,
  ];
  const BOARDS = ["wc-chess-board", "chess-board", ".board"];  // chess.com's board element, with older names
  const PIECE = /^[wb][pnbrqk]$/, SQUARE = /^square-(\d)(\d)$/;  // a piece's classes: "wp", "square-52"
  const moveNode = ply => `[data-node="0-${ply}"]`;  // chess.com's move list: one node per half-move
  // the games archive: one row per game, its link, and the line under it where the Knightwise tag goes
  const ARCHIVE_ROWS = [".game-history-games-row", "[class*=games-row]", "tr"];
  const ARCHIVE_SLOTS = [".game-history-games-info-footer", "[class*=info-footer]", "td:last-child"];

  function gameId(path) {
    for (const re of GAME_ADDRESSES) { const m = re.exec(path || ""); if (m) return m[1]; }
    return null;
  }

  // Something that looks like a game page at an address we don't know: a board, and a long number in the address.
  // Only reported (so we learn chess.com moved it); nothing is shown there.
  // known places with a board and a number that aren't games we review: bots (chess.com doesn't share those
  // games), puzzles, lessons, the analysis board, the play pages
  const NOT_OURS = /^\/(?:game\/computer|puzzles?|lessons?|learn|courses|drills|practice|analysis|play|daily-chess-puzzle)(?:[/?#]|$)/;
  function unknownGameAddress(path, hasBoard) {
    path = path || "";
    return hasBoard && !gameId(path) && !NOT_OURS.test(path) && /\/\d{6,}(?:[/?#]|$)/.test(path);
  }

  function board(doc) {
    for (const sel of BOARDS) { const el = doc.querySelector(sel); if (el) return el; }
    return null;
  }

  // Piece placement as in a FEN ("rnbqkbnr/pppppppp/8/..."), from each piece's class list. null if none could be read.
  function placement(classLists) {
    const grid = Array.from({ length: 8 }, () => Array(8).fill(null));
    let found = 0;
    for (const cls of classLists) {
      const kind = cls.find(c => PIECE.test(c)), sq = cls.map(c => SQUARE.exec(c)).find(Boolean);
      if (!kind || !sq) continue;
      const file = Number(sq[1]) - 1, rank = Number(sq[2]) - 1;
      if (file < 0 || file > 7 || rank < 0 || rank > 7) continue;
      grid[rank][file] = kind[0] === "w" ? kind[1].toUpperCase() : kind[1];
      found++;
    }
    if (!found) return null;
    return grid.slice().reverse().map(row => {
      let out = "", empty = 0;
      for (const p of row) { if (!p) { empty++; continue; } if (empty) out += empty; empty = 0; out += p; }
      return out + (empty || "");
    }).join("/");
  }

  function boardPlacement(boardEl) {
    return placement([...boardEl.querySelectorAll(".piece")].map(el => [...el.classList]));
  }

  // Each game row of the archive: {id, slot}. Rows without a game link (headers, ads) are skipped.
  function archiveRows(doc) {
    for (const sel of ARCHIVE_ROWS) {
      const rows = [...doc.querySelectorAll(sel)].map(row => {
        const link = row.querySelector('a[href*="/game/"]');
        const id = link && gameId(new URL(link.getAttribute("href"), "https://www.chess.com").pathname);
        const slot = id && ARCHIVE_SLOTS.map(s => row.querySelector(s)).find(Boolean);
        return id && slot ? { id, slot } : null;
      }).filter(Boolean);
      if (rows.length) return rows;
    }
    return [];
  }

  // both players' names somewhere on the page (chess.com fills them in a few seconds late)
  function namesOnPage(text, players) {
    const t = String(text || "").toLowerCase();
    return players.length === 2 && players.every(p => t.includes(String(p).toLowerCase()));
  }

  // Tell the app what a check found. Each check is sent when its answer changes, and at most once an hour otherwise.
  const sent = {};
  function report(check, ok, detail) {
    const key = `${check}:${ok}`;
    if (sent[check] === key && Date.now() - (sent[`${check}@`] || 0) < 3600000) return;
    sent[check] = key; sent[`${check}@`] = Date.now();
    try { chrome.runtime.sendMessage({ type: "health", check, ok: !!ok, detail: String(detail || "").slice(0, 200) }); }
    catch (e) {}
  }

  return { GAME_ADDRESSES, BOARDS, gameId, unknownGameAddress, board, placement, boardPlacement, moveNode,
           archiveRows, namesOnPage, report };
})();
if (typeof module !== "undefined") module.exports = KnightwiseContract;  // for the tests (tests/test_contract.py)
