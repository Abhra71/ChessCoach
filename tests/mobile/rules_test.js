// Tests for the phone app's move rules (docs/app/rules.js) and game reading (docs/app/games.js).
// Run:  node tests/mobile/rules_test.js      (Node only, no packages)
const assert = require("node:assert/strict");
global.Rules = require("../../docs/app/rules.js");
const Games = require("../../docs/app/games.js");
const Rules = global.Rules;

const placement = fen => fen.split(" ")[0];
let passed = 0;
function test(name, fn) { fn(); passed++; console.log("ok  " + name); }

test("the Opera Game (Morphy, 1858) ends in the right position, mate on d8", () => {
  const sans = "e4 e5 Nf3 d6 d4 Bg4 dxe5 Bxf3 Qxf3 dxe5 Bc4 Nf6 Qb3 Qe7 Nc3 c6 Bg5 b5 Nxb5 cxb5 Bxb5+ Nbd7 O-O-O Rd8 Rxd7 Rxd7 Rd1 Qe6 Bxd7+ Nxd7 Qb8+ Nxb8 Rd8#".split(" ");
  const { fens, moves } = Rules.replay(sans);
  assert.equal(placement(fens.at(-1)), "1n1Rkb1r/p4ppp/4q3/4p1B1/4P3/8/PPP2PPP/2K5");
  assert.equal(moves.at(-1).check, true);
  assert.equal(moves[22].from, "e1"); assert.equal(moves[22].to, "c1");   // O-O-O moves the king two squares
});

test("en passant takes the pawn that passed", () => {
  const { fens } = Rules.replay("e4 Nf6 e5 d5 exd6".split(" "));
  assert.equal(placement(fens.at(-1)), "rnbqkb1r/ppp1pppp/3P1n2/8/8/8/PPPP1PPP/RNBQKBNR");
});

test("promotion, with and without the = sign", () => {
  assert.equal(placement(Rules.replay(["a8=Q"], "8/P7/8/8/8/8/8/k6K w - - 0 1").fens[1]), "Q7/8/8/8/8/8/8/k6K");
  assert.equal(placement(Rules.replay(["a8N"], "8/P7/8/8/8/8/8/k6K w - - 0 1").fens[1]), "N7/8/8/8/8/8/8/k6K");
});

test("a pinned knight is skipped when the move doesn't say which knight", () => {
  // knights on d2 and h4 can both reach f3, but d2 is pinned by the bishop on a5
  const { moves } = Rules.replay(["Nf3"], "4k3/8/8/b7/7N/8/3N4/4K3 w - - 0 1");
  assert.equal(moves[0].from, "h4");
});

test("two pieces that fit the move: the file or rank picks one", () => {
  const start = "4k3/8/8/8/8/8/8/R4RK1 w - - 0 1";
  assert.equal(Rules.replay(["Rad1"], start).moves[0].from, "a1");
  assert.throws(() => Rules.replay(["Rd1"], start), /fits 2 pieces/);
});

test("castling rights go when the king or a rook moves", () => {
  const { fens } = Rules.replay("e4 e5 Nf3 Nc6 Bc4 Bc5 O-O Nf6 Rf1e1 Rb8".split(" "));
  assert.equal(fens.at(-1).split(" ")[2], "k");   // White castled, Black's a8 rook moved: only Black's short castle left
});

test("a broken move says so instead of guessing", () => {
  assert.throws(() => Rules.replay(["e5"]), /fits 0 pieces/);
  assert.throws(() => Rules.replay(["hello"]), /Can't read/);
});

test("a chess.com PGN with clocks becomes a list of moves", () => {
  const pgn = `[Event "Live Chess"]\n[Site "Chess.com"]\n[Result "0-1"]\n\n1. e4 {[%clk 0:09:58.1]} 1... e5 {[%clk 0:09:57]} 2. Qh5 {[%clk 0:09:50]} 2... Nc6 3. Bc4 Nf6 4. Qxf7# 1-0`;
  assert.deepEqual(Games.pgnMoves(pgn), ["e4", "e5", "Qh5", "Nc6", "Bc4", "Nf6", "Qxf7#"]);
  assert.equal(Games.pgnHeaders(pgn).Result, "0-1");
  assert.equal(Rules.replay(Games.pgnMoves(pgn)).moves.at(-1).check, true);
});

test("a Lichess game: finished games kept, aborted ones dropped, moves kept as one line", () => {
  const base = { id: "abc", variant: "standard", status: "mate", winner: "white", moves: "e4 e5 Qh5 Nc6 Bc4 Nf6 Qxf7#",
    players: { white: { user: { name: "Someone" }, rating: 1500 }, black: { user: { name: "Me" }, rating: 1400 } }, lastMoveAt: 1 };
  const g = Games.fromLichess(base, "me");
  assert.equal(g.me, "b"); assert.equal(g.result, "loss"); assert.equal(g.plies, 7); assert.equal(typeof g.moves, "string");
  assert.equal(Games.fromLichess({ ...base, status: "aborted" }, "me"), null);
  assert.equal(Games.fromLichess({ ...base, status: "started" }, "me"), null);
  assert.equal(Games.fromLichess({ ...base, variant: "chess960" }, "me"), null);
});

// every game is taken (owner, 28 Nov); the second time only the newest saved month and newer ones are downloaded
async function everyGameThenOnlyNewMonths() {
  const game = (id, month, day) => ({ uuid: id, url: "https://www.chess.com/game/live/" + id, rules: "chess",
    pgn: `[Event "Live"]\n\n1. e4 e5 1-0`, end_time: Date.UTC(2026, month - 1, day) / 1000, time_class: "blitz", fen: "",
    white: { username: "Me", rating: 1000, result: "win" }, black: { username: "Them", rating: 1000, result: "resigned" } });
  const months = { "2026/09": [game("a", 9, 3)], "2026/10": [game("b", 10, 5), game("c", 10, 20)], "2026/11": [game("d", 11, 2)] };
  const asked = [];
  global.fetch = async url => {
    asked.push(url);
    const body = url.endsWith("/archives") ? { archives: Object.keys(months).map(m => "https://api.chess.com/pub/player/me/games/" + m) }
      : { games: months[url.slice(-7)] };
    return { ok: true, status: 200, json: async () => body };
  };
  const saved = {};
  global.Store = { get: async k => saved[k] || null, set: async (k, v) => { saved[k] = JSON.parse(JSON.stringify(v)); } };
  const seen = [];
  const all = await Games.load("chesscom", "Me", (some, month) => seen.push([month, some.length]));
  assert.deepEqual(all.map(g => g.id), ["cc-d", "cc-c", "cc-b", "cc-a"]);   // every game, newest first
  assert.deepEqual(seen, [["2026/11", 1], ["2026/10", 3], ["2026/09", 4]]);   // shown month by month
  months["2026/11"].push(game("e", 11, 25));                                   // a new game is played
  asked.length = 0;
  const again = await Games.load("chesscom", "Me");
  assert.equal(again.length, 5);
  assert.deepEqual(asked.map(u => u.slice(-8)), ["archives", "/2026/11"]);    // only the newest month again

  // a first download that stopped halfway (only November saved, never reached the first game): carry on backwards
  const k = "games.chesscom.me";
  saved[k] = { at: 1, games: saved[k].games.filter(g => g.id === "cc-d" || g.id === "cc-e") };   // no "complete"
  asked.length = 0;
  const resumed = await Games.load("chesscom", "Me");
  assert.equal(resumed.length, 5);
  assert.deepEqual(asked.map(u => u.slice(-8)), ["archives", "/2026/11", "/2026/10", "/2026/09"]);
  assert.equal(saved[k].complete, true);
  passed++; console.log("ok  every finished game, shown month by month; next time only the new month");
}

// perft: count every position a few moves deep; the right numbers are known (chessprogramming.org/Perft_Results),
// so any mistake in castling, en passant, promotion or pins shows up as a wrong count
function perft(pos, depth) {
  if (depth === 0) return 1;
  let n = 0;
  for (const m of Rules.moves(pos)) n += depth === 1 ? 1 : perft(Rules.play(pos, m), depth - 1);
  return n;
}

test("every legal move, counted (perft): the start, Kiwipete, en passant and promotion positions", () => {
  const cases = [
    [Rules.START, [20, 400, 8902]],
    ["r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", [48, 2039]],
    ["8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", [14, 191, 2812]],
    ["r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1", [6, 264, 9467]],
  ];
  for (const [fen, counts] of cases)
    counts.forEach((want, i) => assert.equal(perft(Rules.parse(fen), i + 1), want, `${fen} depth ${i + 1}`));
});

test("moves are written back the usual way: Nbd7, exd6, O-O-O, a8=Q, Qxf7#", () => {
  const check = (fen, san) => { const pos = Rules.parse(fen); assert.equal(Rules.toSan(pos, Rules.fromSan(pos, san)), san); };
  check("4k3/8/8/b7/7N/8/3N4/4K3 w - - 0 1", "Nf3");            // the pinned knight needs no letter
  check("4k3/8/8/8/8/8/8/R4RK1 w - - 0 1", "Rad1");
  check("8/P7/8/8/8/8/8/k6K w - - 0 1", "a8=Q+");
  check("r3k3/8/8/8/8/8/8/4K3 b q - 0 1", "O-O-O");
  check("r1bqkb1r/pppp1ppp/2n2n2/4p2Q/2B1P3/8/PPPP1PPP/RNB1K1NR w KQkq - 4 4", "Qxf7#");
});

everyGameThenOnlyNewMonths().then(() => console.log(`\n${passed} passed`), e => { console.error(e); process.exit(1); });
