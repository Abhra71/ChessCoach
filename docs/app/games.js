// Your finished games, from chess.com's and Lichess's public APIs (no login, no server of ours).
//
// Fair play: both APIs used here return ONLY games that are over. chess.com's monthly archives hold
// finished games only; Lichess's games export leaves out games still being played (ongoing=false) and
// we also drop anything not ended by the rules (aborted, never started). Nothing here can look at a
// game in progress, and nothing lets you set up a position of your own.
//
// Every game, from either site, becomes the same plain object:
//   { id, site, url, white, black, whiteRating, blackRating, me: "w"|"b", result: "win"|"loss"|"draw",
//     how, speed, endedAt, sans: ["e4", "e5", ...], startFen, finalFen, opening }
const Games = (() => {
  const WANT = 60;   // the newest 60 games are plenty for a first look, and quick to download

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

  async function chesscom(user) {
    const name = user.trim().toLowerCase();
    const { archives = [] } = await getJson(`https://api.chess.com/pub/player/${encodeURIComponent(name)}/games/archives`);
    const out = [];
    for (const month of archives.slice().reverse()) {   // newest month first, one at a time (chess.com asks for that)
      const { games = [] } = await getJson(month);
      for (const g of games.slice().reverse()) {
        if (g.rules !== "chess" || !g.pgn) continue;     // standard chess only (no Chess960 or other variants yet)
        const h = pgnHeaders(g.pgn), me = g.white.username.toLowerCase() === name ? "w" : "b";
        const mine = me === "w" ? g.white : g.black, theirs = me === "w" ? g.black : g.white;
        const result = mine.result === "win" ? "win" : theirs.result === "win" ? "loss" : "draw";
        out.push({
          id: "cc-" + (g.uuid || g.url.split("/").pop()), site: "chess.com", url: g.url,
          white: g.white.username, black: g.black.username, whiteRating: g.white.rating, blackRating: g.black.rating,
          me, result, how: CC_HOW[result === "win" ? theirs.result : mine.result] || "",
          speed: g.time_class, endedAt: g.end_time * 1000, sans: pgnMoves(g.pgn),
          startFen: h.SetUp === "1" && h.FEN ? h.FEN : Rules.START, finalFen: g.fen,
          opening: (h.ECOUrl || "").split("/").pop().replace(/-/g, " ").replace(/\s\d.*$/, ""),
        });
        if (out.length >= WANT) return out;
      }
    }
    return out;
  }

  // ---------- Lichess ----------
  const LI_HOW = { mate: "checkmate", resign: "resigned", outoftime: "on time", timeout: "left the game",
    stalemate: "stalemate", draw: "draw", variantEnd: "", cheat: "cheat detected", unknownFinish: "" };

  async function lichess(user) {
    const name = user.trim().toLowerCase();
    const url = `https://lichess.org/api/games/user/${encodeURIComponent(name)}` +
      `?max=${WANT}&ongoing=false&finished=true&moves=true&opening=true&clocks=false&evals=false`;
    const r = await fetch(url, { headers: { Accept: "application/x-ndjson" } });
    if (r.status === 404) throw new Error("no-player");
    if (!r.ok) throw new Error(`Lichess said ${r.status}`);
    const lines = (await r.text()).split("\n").filter(Boolean).map(l => JSON.parse(l));
    return lines.filter(g => g.variant === "standard" && LI_HOW[g.status] !== undefined && g.moves)
      .map(g => {
        const w = g.players.white, b = g.players.black;
        const wn = (w.user && w.user.name) || "Computer", bn = (b.user && b.user.name) || "Computer";
        const me = wn.toLowerCase() === name ? "w" : "b";
        const result = !g.winner ? "draw" : g.winner === (me === "w" ? "white" : "black") ? "win" : "loss";
        return {
          id: "li-" + g.id, site: "Lichess", url: "https://lichess.org/" + g.id,
          white: wn, black: bn, whiteRating: w.rating, blackRating: b.rating,
          me, result, how: LI_HOW[g.status], speed: g.speed, endedAt: g.lastMoveAt || g.createdAt,
          sans: g.moves.split(" "), startFen: Rules.START, finalFen: null,
          opening: g.opening ? g.opening.name : "",
        };
      });
  }

  // ---------- kept on the phone, so the list opens at once and works offline ----------
  const key = (site, user) => `kw.games.${site}.${user.trim().toLowerCase()}`;
  function saved(site, user) {
    try { return JSON.parse(localStorage.getItem(key(site, user)) || "null"); } catch { return null; }
  }
  function keep(site, user, games) {
    try { localStorage.setItem(key(site, user), JSON.stringify({ at: Date.now(), games })); } catch { /* full or private mode */ }
  }

  async function load(site, user) {
    const games = site === "lichess" ? await lichess(user) : await chesscom(user);
    games.sort((a, b) => b.endedAt - a.endedAt);
    keep(site, user, games);
    return games;
  }

  return { load, saved, pgnMoves, pgnHeaders };
})();

if (typeof module !== "undefined") module.exports = Games;
