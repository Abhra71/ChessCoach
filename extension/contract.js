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

  // The fix file (flagship 6, coach/fixes.py): new names from GitHub, tried before ours, and features paused for
  // everyone. The background keeps the latest copy in storage; until it's read, ours alone are used.
  let FIX = {};
  try { chrome.storage.local.get("fixes").then(v => { FIX = (v && v.fixes) || {}; }); } catch (e) {}
  const list = (name, ours) => [...(Array.isArray(FIX[name]) ? FIX[name] : []), ...ours];
  const off = feature => Array.isArray(FIX.off) && FIX.off.includes(feature);
  const all = (doc, sel) => { try { return [...doc.querySelectorAll(sel)]; } catch (e) { return []; } };  // a bad name can't break us
  const one = (root, sel) => { try { return root.querySelector(sel); } catch (e) { return null; } };

  function gameId(path) {
    const extra = list("game_addresses", []).map(s => { try { return new RegExp(s); } catch (e) { return null; } }).filter(Boolean);
    for (const re of [...extra, ...GAME_ADDRESSES]) { const m = re.exec(path || ""); if (m && /^\d+$/.test(m[1] || "")) return m[1]; }
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
    for (const sel of list("boards", BOARDS)) { const el = one(doc, sel); if (el) return el; }
    return boardByMeaning(doc);
  }

  // When every name has failed (chess.com renamed the board): the board is the smallest box that holds the pieces,
  // found by what the pieces are ("wp", "square-52"), not by what chess.com calls the board. Reported, so we learn.
  function boardByMeaning(doc) {
    const pieces = all(doc, "[class*='square-']").filter(el => [...el.classList].some(c => PIECE.test(c)));
    if (pieces.length < 2) return null;
    let box = pieces[0].parentElement;
    while (box && !pieces.every(p => box.contains(p))) box = box.parentElement;
    if (box) report("board-by-meaning", true, box.tagName.toLowerCase() + "." + String(box.className).slice(0, 60));
    return box || null;
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
  const linkId = link => { try { return gameId(new URL(link.getAttribute("href"), "https://www.chess.com").pathname); } catch (e) { return null; } };

  function archiveRows(doc) {
    const slots = list("archive_slots", ARCHIVE_SLOTS);
    for (const sel of list("archive_rows", ARCHIVE_ROWS)) {
      const rows = all(doc, sel).map(row => {
        const link = one(row, 'a[href*="/game/"]');
        const id = link && linkId(link);
        const slot = id && slots.map(s => one(row, s)).find(Boolean);
        return id && slot ? { id, slot } : null;
      }).filter(Boolean);
      if (rows.length) return rows;
    }
    return rowsByMeaning(doc);
  }

  // When every name has failed: a game's row is the biggest box around its link that holds no other game, and the
  // tag goes at its end. Found by the links, which chess.com can't rename without breaking its own site.
  function rowsByMeaning(doc) {
    const seen = new Set(), rows = [];
    for (const link of all(doc, 'a[href*="/game/"]')) {
      const id = linkId(link);
      if (!id || seen.has(id)) continue;
      let row = link;
      while (row.parentElement && row.parentElement !== doc.body &&
             all(row.parentElement, 'a[href*="/game/"]').every(a => linkId(a) === id)) row = row.parentElement;
      if (row === link) continue;
      seen.add(id);
      rows.push({ id, slot: row });
    }
    if (rows.length) report("archive-by-meaning", true, `${rows.length} rows`);
    return rows;
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
           archiveRows, namesOnPage, report, off, fixes: () => FIX };
})();
if (typeof module !== "undefined") module.exports = KnightwiseContract;  // for the tests (tests/test_contract.py)
