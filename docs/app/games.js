// Your finished games, from chess.com's and Lichess's public APIs (no login, no server of ours).
//
// Fair play: both APIs used here return ONLY games that are over. chess.com's monthly archives hold
// finished games only; Lichess's games export leaves out games still being played (ongoing=false) and
// we also drop anything not ended by the rules (aborted, never started). Nothing here can look at a
// game in progress, and nothing lets you set up a position of your own.
//
// Made for cheap phones: one month (or a few Lichess games) at a time, newest first, shown as they arrive;
// only a short summary of each game is kept (the moves stay one text line until you open the game);
// fewer games on phones with little memory.
//
// Every game, from either site, becomes the same small object:
//   { id, site, url, white, black, whiteRating, blackRating, me: "w"|"b", result: "win"|"loss"|"draw",
//     how, speed, endedAt, moves: "e4 e5 Nf3 ...", plies, startFen (only if not the usual start), finalFen, opening }
const Games = (() => {
  const START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

  // how many games to load: 60 on most phones, fewer when the phone says it has little memory or few cores
  // (navigator.deviceMemory is rounded: 0.5, 1, 2, 4, 8; not every browser tells, then we assume a normal phone)
  function howMany() {
    const mem = (typeof navigator !== "undefined" && navigator.deviceMemory) || 4;
    const cores = (typeof navigator !== "undefined" && navigator.hardwareConcurrency) || 4;
    return mem <= 1 ? 20 : mem <= 2 || cores <= 2 ? 30 : 60;
  }

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

  async function chesscom(user, want, onSome) {
    const name = user.trim().toLowerCase();
    const { archives = [] } = await getJson(`https://api.chess.com/pub/player/${encodeURIComponent(name)}/games/archives`);
    const out = [];
    for (const month of archives.slice().reverse()) {   // newest month first, one at a time (chess.com asks for that)
      let { games = [] } = await getJson(month);
      for (let i = games.length - 1; i >= 0 && out.length < want; i--) {
        const g = games[i];
        if (g.rules === "chess" && g.pgn) out.push(fromChesscom(g, name));   // standard chess only for now
      }
      games = null;                                        // let the phone free the month's big download
      if (onSome) onSome(out.slice());
      if (out.length >= want) break;
    }
    return out;
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

  async function lichess(user, want, onSome) {
    const name = user.trim().toLowerCase();
    const url = `https://lichess.org/api/games/user/${encodeURIComponent(name)}` +
      `?max=${want}&ongoing=false&finished=true&moves=true&opening=true&clocks=false&evals=false`;
    const r = await fetch(url, { headers: { Accept: "application/x-ndjson" } });
    if (r.status === 404) throw new Error("no-player");
    if (!r.ok) throw new Error(`Lichess said ${r.status}`);
    const out = [], take = line => { if (line.trim()) { const g = fromLichess(JSON.parse(line), name); if (g) out.push(g); } };
    if (!r.body || !r.body.getReader) { (await r.text()).split("\n").forEach(take); if (onSome) onSome(out.slice()); return out; }
    const reader = r.body.getReader(), dec = new TextDecoder();
    let rest = "", shown = 0;
    for (;;) {
      const { done, value } = await reader.read();
      rest += dec.decode(value || new Uint8Array(), { stream: !done });
      const lines = rest.split("\n"); rest = lines.pop();
      lines.forEach(take);
      if (onSome && out.length - shown >= 10) { shown = out.length; onSome(out.slice()); }   // show every 10 games
      if (done) break;
    }
    take(rest);
    if (onSome) onSome(out.slice());
    return out;
  }

  // ---------- kept on the phone (IndexedDB), so the list opens at once and works offline ----------
  const key = (site, user) => `games.${site}.${user.trim().toLowerCase()}`;
  const saved = (site, user) => Store.get(key(site, user));

  // onSome(gamesSoFar) is called as games arrive, newest first, so the list can grow on screen
  async function load(site, user, onSome) {
    const want = howMany();
    const games = site === "lichess" ? await lichess(user, want, onSome) : await chesscom(user, want, onSome);
    games.sort((a, b) => b.endedAt - a.endedAt);
    await Store.set(key(site, user), { at: Date.now(), games });
    return games;
  }

  const sansOf = g => (g.moves ? g.moves.split(" ") : []);
  return { START, load, saved, howMany, sansOf, pgnMoves, pgnHeaders, fromChesscom, fromLichess };
})();

if (typeof module !== "undefined") module.exports = Games;
