// Your finished games, from chess.com's and Lichess's public APIs (no login, no server of ours).
//
// Fair play: both APIs used here return ONLY games that are over. chess.com's monthly archives hold
// finished games only; Lichess's games export leaves out games still being played (ongoing=false) and
// we also drop anything not ended by the rules (aborted, never started). Nothing here can look at a
// game in progress, and nothing lets you set up a position of your own.
//
// EVERY finished game is taken (owner, 28 Nov), made light for cheap phones: one month (or a stream of Lichess
// games) at a time, newest first, shown and saved as they arrive; each game is a short summary (the moves stay one
// text line until you open the game); next time only the new games are downloaded.
//
// Every game, from either site, becomes the same small object:
//   { id, site, url, white, black, whiteRating, blackRating, me: "w"|"b", result: "win"|"loss"|"draw",
//     how, speed, endedAt, moves: "e4 e5 Nf3 ...", plies, startFen (only if not the usual start), finalFen, opening }
const Games = (() => {
  const NL = String.fromCharCode(10);   // a new line (one Lichess game per line)
  const START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

  // ---------- reading a PGN (the text format chess.com uses for a game) ----------
  function pgnHeaders(pgn) {
    const out = {};
    for (const m of pgn.matchAll(/\[(\w+)\s+"([^"]*)"\]/g)) out[m[1]] = m[2];
    return out;
  }
  function pgnMoves(pgn) {
    const text = pgn.replace(/\[[^\]]*\]/g, " ")   // headers
      .replace(/\{[^}]*\}/g, " ")                   // comments, like the clock {[%clk 0:04:58.1]}
      .replace(/\([^()]*\)/g, " ")                  // side lines (chess.com doesn't send them, but be safe)
      .replace(/\$\d+/g, " ")                        // marks like $1
      .replace(/\d+\.(\.\.)?/g, " ");                // move numbers 1. and 1...
    return text.split(/\s+/).filter(t => t && !/^(1-0|0-1|1\/2-1\/2|\*)$/.test(t));
  }

  // ---------- chess.com ----------
  const CC_HOW = { checkmated: "checkmate", resigned: "resigned", timeout: "on time", abandoned: "abandoned",
    stalemate: "stalemate", agreed: "agreed draw", repetition: "repetition", insufficient: "not enough pieces",
    "50move": "50-move rule", timevsinsufficient: "time out, not enough pieces" };

  async function getJson(url) {
    const r = await fetch(url);
    if (r.status === 404) throw new Error("no-player");
    if (!r.ok) throw new Error(`chess.com said ${r.status}`);
    return r.json();
  }

  function fromChesscom(g, name) {
    const h = pgnHeaders(g.pgn), me = g.white.username.toLowerCase() === name ? "w" : "b";
    const mine = me === "w" ? g.white : g.black, theirs = me === "w" ? g.black : g.white;
    const result = mine.result === "win" ? "win" : theirs.result === "win" ? "loss" : "draw";
    const sans = pgnMoves(g.pgn);
    return {
      id: "cc-" + (g.uuid || g.url.split("/").pop()), site: "chess.com", url: g.url,
      white: g.white.username, black: g.black.username, whiteRating: g.white.rating, blackRating: g.black.rating,
      me, result, how: CC_HOW[result === "win" ? theirs.result : mine.result] || "",
      speed: g.time_class, endedAt: g.end_time * 1000, moves: sans.join(" "), plies: sans.length,
      startFen: h.SetUp === "1" && h.FEN ? h.FEN : undefined, finalFen: g.fen,
      opening: (h.ECOUrl || "").split("/").pop().replace(/-/g, " ").replace(/\s\d.*$/, ""),
    };
  }

  // newest, oldest: the times (ms) of the newest and oldest games already saved (0 if none); complete: the oldest
  // month was reached once. Downloads the newest saved month and newer ones, then, if an earlier download stopped
  // halfway, carries on backwards from the oldest saved month.
  const monthOf = ms => new Date(ms).toISOString().slice(0, 7).replace("-", "/");   // "2026/11"
  async function chesscom(user, { newest, oldest, complete }, add) {
    const name = user.trim().toLowerCase();
    const { archives = [] } = await getJson(`https://api.chess.com/pub/player/${encodeURIComponent(name)}/games/archives`);
    const months = archives.slice().reverse();   // newest month first, one at a time (chess.com asks for that)
    const todo = !newest ? months
      : months.filter(m => m.slice(-7) >= monthOf(newest) || (!complete && m.slice(-7) <= monthOf(oldest)));
    for (const month of todo) {
      let { games = [] } = await getJson(month);
      const found = [];
      for (const g of games) if (g.rules === "chess" && g.pgn) found.push(fromChesscom(g, name));   // standard chess only
      games = null;                                        // let the phone free the month's big download
      await add(found, month.slice(-7));
    }
  }

  // ---------- Lichess (read as it streams in, one game per line) ----------
  const LI_HOW = { mate: "checkmate", resign: "resigned", outoftime: "on time", timeout: "left the game",
    stalemate: "stalemate", draw: "draw", variantEnd: "", cheat: "cheat detected", unknownFinish: "" };

  function fromLichess(g, name) {
    if (g.variant !== "standard" || LI_HOW[g.status] === undefined || !g.moves) return null;
    const w = g.players.white, b = g.players.black;
    const wn = (w.user && w.user.name) || "Computer", bn = (b.user && b.user.name) || "Computer";
    const me = wn.toLowerCase() === name ? "w" : "b";
    const result = !g.winner ? "draw" : g.winner === (me === "w" ? "white" : "black") ? "win" : "loss";
    return {
      id: "li-" + g.id, site: "Lichess", url: "https://lichess.org/" + g.id,
      white: wn, black: bn, whiteRating: w.rating, blackRating: b.rating,
      me, result, how: LI_HOW[g.status], speed: g.speed, endedAt: g.lastMoveAt || g.createdAt,
      moves: g.moves, plies: g.moves.split(" ").length, finalFen: null, opening: g.opening ? g.opening.name : "",
    };
  }

  // the same range idea as chess.com: games newer than the newest saved one, then (if an earlier download
  // stopped halfway) games older than the oldest saved one; everything when nothing is saved yet
  async function lichess(user, { newest, oldest, complete }, add) {
    const name = user.trim().toLowerCase();
    const base = `https://lichess.org/api/games/user/${encodeURIComponent(name)}` +
      "?ongoing=false&finished=true&moves=true&opening=true&clocks=false&evals=false";
    await stream(newest ? `${base}&since=${newest + 1}` : base, name, add);
    if (newest && !complete) await stream(`${base}&until=${oldest - 1}`, name, add);
  }
  async function stream(url, name, add) {
    const r = await fetch(url, { headers: { Accept: "application/x-ndjson" } });
    if (r.status === 404) throw new Error("no-player");
    if (!r.ok) throw new Error(`Lichess said ${r.status}`);
    let batch = [];
    const take = line => { if (line.trim()) { const g = fromLichess(JSON.parse(line), name); if (g) batch.push(g); } };
    const flush = async () => { if (batch.length) { const b = batch; batch = []; await add(b, ""); } };
    if (!r.body || !r.body.getReader) { (await r.text()).split(NL).forEach(take); return flush(); }
    const reader = r.body.getReader(), dec = new TextDecoder();
    let rest = "";
    for (;;) {
      const { done, value } = await reader.read();
      rest += dec.decode(value || new Uint8Array(), { stream: !done });
      const lines = rest.split(NL); rest = lines.pop();
      lines.forEach(take);
      if (batch.length >= 100) await flush();   // shown and saved every 100 games
      if (done) break;
    }
    take(rest);
    await flush();
  }

  // ---------- kept on the phone (IndexedDB), so the list opens at once and works offline ----------
  const key = (site, user) => `games.${site}.${user.trim().toLowerCase()}`;
  const saved = (site, user) => Store.get(key(site, user));

  // Every finished game: the saved ones at once, then the new ones as they arrive (onSome(allSoFar, note) each
  // month, or every 100 Lichess games), saved as they come, so a closed app loses nothing.
  async function load(site, user, onSome) {
    const saved = (await Store.get(key(site, user))) || { games: [] };
    const byId = new Map(saved.games.map(g => [g.id, g]));
    const times = saved.games.map(g => g.endedAt || 0);   // (a loop, not Math.max(...): tens of thousands of games)
    const range = { newest: times.reduce((a, b) => Math.max(a, b), 0), oldest: times.reduce((a, b) => Math.min(a, b), Infinity),
      complete: !!saved.complete };
    if (!times.length) range.oldest = 0;
    let all = saved.games.slice(), savedAt = Date.now(), unsaved = false, complete = range.complete;
    const keep = () => Store.set(key(site, user), { at: Date.now(), games: all, complete });
    const add = async (found, month) => {
      let fresh = 0;
      for (const g of found) if (!byId.has(g.id)) { byId.set(g.id, g); fresh++; }
      if (fresh) {
        all = [...byId.values()].sort((a, b) => b.endedAt - a.endedAt);
        unsaved = true;
        // saved at most every 5 seconds: saving thousands of games after every month was slow on a cheap phone
        if (Date.now() - savedAt > 5000) { await keep(); savedAt = Date.now(); unsaved = false; }
      }
      if (onSome) onSome(all, month);
    };
    try {
      if (site === "lichess") await lichess(user, range, add); else await chesscom(user, range, add);
      if (!complete) { complete = true; unsaved = true; }   // reached the very first game: only new ones from now on
    } finally {   // what came in is kept even if the download stops halfway (no internet, the site busy)
      if (unsaved || !saved.at) await keep();
    }
    return all;
  }

  const sansOf = g => (g.moves ? g.moves.split(" ") : []);
  return { START, load, saved, sansOf, pgnMoves, pgnHeaders, fromChesscom, fromLichess };
})();

if (typeof module !== "undefined") module.exports = Games;
