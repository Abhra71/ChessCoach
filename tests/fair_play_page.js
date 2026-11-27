// A tiny stand-in for a chess.com tab, to run the extension's real page scripts (contract.js, coach.js, buddy.js)
// through the fair-play scenarios of docs/FAIR-PLAY-AUDIT.md. Used by tests/test_fair_play.py (needs Node.js).
//
//   node fair_play_page.js <extension folder> <scenario>
// prints one line of JSON: what the scenario found.
const vm = require("vm"), fs = require("fs"), path = require("path");
const [ext, scenario] = process.argv.slice(2);

function page(start) {
  const present = new Set();  // which chess.com elements exist, by selector
  const sent = [];            // every message the page scripts sent to the extension's background
  const observers = [];     // chess.com's page changing: every script's watcher hears it
  const answers = {};         // message type -> the background's reply (or a function of the message)
  const delays = {};          // message type -> ms before the reply comes back

  function el(tag) {
    const e = {
      tag, children: [], parent: null, style: {}, dataset: {}, innerHTML: "", className: "", isConnected: true, _q: {},
      classList: null, onclick: null, textContent: "", innerText: "", value: "",
      setAttribute() {}, getAttribute() { return null; }, focus() {}, click() {}, scrollIntoView() {},
      appendChild(c) { this.children.push(c); c.parent = this; return c; },
      remove() { if (this.parent) this.parent.children = this.parent.children.filter(x => x !== this); this.parent = null; },
      contains(n) { return n === this || this.children.some(c => c.contains && c.contains(n)); },
      querySelector(sel) { return (this._q[sel] = this._q[sel] || el("stub")); },
      querySelectorAll() { return []; },
      getBoundingClientRect() { return { left: 0, top: 0, right: 10, bottom: 10, width: 10, height: 10 }; },
      getClientRects() { return [1]; }, closest() { return null; },
    };
    const set = new Set();
    e.classList = { add: c => set.add(c), remove: c => set.delete(c), contains: c => set.has(c),
                    toggle: (c, on) => (on === undefined ? !set.has(c) : on) ? set.add(c) : set.delete(c),
                    [Symbol.iterator]: () => set[Symbol.iterator]() };
    return e;
  }
  const body = el("body");
  const board = el("wc-chess-board");
  const nodes = {};
  const document = {
    body, title: "Chess: alice vs bob - Chess.com",
    createElement: el, createElementNS: (ns, t) => el(t),
    querySelector(sel) {
      if (sel === "wc-chess-board" && present.has("board")) return board;
      const m = /^\[data-node="0-(\d+)"\]$/.exec(sel);
      if (m && present.has(`move ${m[1]}`)) return (nodes[m[1]] = nodes[m[1]] || el("move"));
      return null;
    },
    querySelectorAll() { return []; },
  };
  body.innerText = "alice bob";
  const store = new Map();
  const localStorage = {
    get length() { return store.size; }, key: i => [...store.keys()][i] ?? null,
    getItem: k => (store.has(k) ? store.get(k) : null), setItem: (k, v) => store.set(k, String(v)), removeItem: k => store.delete(k),
  };
  const session = new Map();
  const sessionStorage = { getItem: k => session.get(k) ?? null, setItem: (k, v) => session.set(k, String(v)), removeItem: k => session.delete(k) };
  const location = { pathname: start, href: "https://www.chess.com" + start, reload() {} };
  const chrome = {
    runtime: {
      id: "kw", lastError: undefined,
      sendMessage(msg, reply) {
        sent.push(msg);
        if (typeof reply === "function") setTimeout(() => {  // the answer as it is when the reply comes
          const a = answers[msg.type];
          reply(typeof a === "function" ? a(msg) : a);
        }, delays[msg.type] || 0);
        return Promise.resolve();
      },
      onMessage: { addListener() {} },
    },
    storage: { local: { get: () => Promise.resolve({}) } },
  };
  const ctx = {
    document, localStorage, sessionStorage, location, chrome, console,
    setTimeout, clearTimeout, setInterval, clearInterval, Promise, Date, Math, JSON, URL, RegExp, Number, String, Array,
    MutationObserver: class { constructor(f) { observers.push(f); } observe() {} },
    addEventListener() {}, removeEventListener() {},
    getComputedStyle: () => ({ visibility: "visible" }), innerHeight: 800, requestAnimationFrame: f => setTimeout(f, 0),
    matchMedia: () => ({ matches: true }), performance: { getEntriesByType: () => [] },
    KnightwiseFaces: { figure: () => "" }, PIECES: {},
  };
  ctx.window = ctx; ctx.top = ctx;
  vm.createContext(ctx);
  for (const f of ["contract.js", "coach.js", "buddy.js"]) vm.runInContext(fs.readFileSync(path.join(ext, f), "utf8"), ctx, { filename: f });
  return {
    present, sent, answers, delays, localStorage, location, body,
    mutate: () => observers.forEach(f => f([{ target: el("chess.com") }])),
    go(p) { location.pathname = p; location.href = "https://www.chess.com" + p; },
    review: () => body.children.some(c => /kw-review/.test(c.className)),
    coach: () => body.children.some(c => /^kw-coach/.test(c.className) && !/kw-review/.test(c.className)),
    said: () => sent.filter(m => m.type === "say").map(m => m.text),
    contract: vm.runInContext("KnightwiseContract", ctx),
  };
}

const wait = ms => new Promise(r => setTimeout(r, ms));
const MOMENT = { ply: 9, move_number: 5, placement: "x", after_placement: "y",
                 steps: [{ board: "before", kind: "mine", title: "You played", text: "You played Qe5.", arrows: [] }] };
const GAME = { known: true, moments: [MOMENT], players: ["alice", "bob"], plies: 10, moves: [] };
const COACH = { voice_on: true, voice: "af_heart", lines: ["Hello."], mood: "calm", coach: "maya", name: "Maya", actions: [], ai_ready: true };
const finishedGame = p => { p.present.add("board"); for (let i = 0; i < 10; i++) p.present.add(`move ${i}`); };

const SCENARIOS = {
  // the finished game, its whole move list on the page: the review shows (so the guards don't break it)
  async finished() {
    const p = page("/game/123");
    p.answers.game = { ok: true, data: GAME }; p.answers.coach = { ok: true, data: COACH };
    finishedGame(p);
    p.mutate(); await wait(600);
    return { review: p.review(), live_here: p.contract.liveHere("/game/123") };
  },
  // a game being played at the same address the archived one had (a rematch on the same page): the move list is
  // shorter than the finished game's, so nothing shows, and what was showing goes at once, voice included
  async rematch_same_page() {
    const p = page("/game/123");
    p.answers.game = { ok: true, data: GAME }; p.answers.coach = { ok: true, data: COACH };
    finishedGame(p);
    p.mutate(); await wait(600);
    const before = p.review();
    for (let i = 3; i < 10; i++) p.present.delete(`move ${i}`);  // the new game: three half-moves so far
    const hushes = p.sent.filter(m => m.type === "hush").length;
    p.mutate(); await wait(400);
    return { before, after: p.review(), hushed: p.sent.filter(m => m.type === "hush").length > hushes,
             live_here: p.contract.liveHere("/game/123") };
  },
  // the app knows the game, but the page never shows its finished move list: nothing at all, not even the voice
  async never_the_finished_list() {
    const p = page("/game/123");
    p.answers.game = { ok: true, data: GAME }; p.answers.coach = { ok: true, data: COACH };
    p.present.add("board"); p.present.add("move 0"); p.present.add("move 1");
    p.mutate(); await wait(46500);
    return { review: p.review(), said: p.said() };
  },
  // a live game in another chess.com tab: a finished game's review in this tab stays away
  async review_with_live_game_elsewhere() {
    const p = page("/game/123");
    p.localStorage.setItem("kw-live:othertab", String(Date.now()));
    p.answers.game = { ok: true, data: GAME }; p.answers.coach = { ok: true, data: COACH };
    finishedGame(p);
    p.mutate(); await wait(600);
    return { review: p.review(), said: p.said() };
  },
  // the coach on chess.com's home page while another tab holds a live game: she doesn't appear
  async coach_with_live_game_elsewhere() {
    const p = page("/home");
    p.localStorage.setItem("kw-live:othertab", String(Date.now()));
    p.answers.coach = { ok: true, data: COACH }; p.answers.page = {};
    await wait(300);
    return { coach: p.coach(), said: p.said(), asked: p.sent.some(m => m.type === "coach") };
  },
  // she's up on home, then a game starts in another tab: she goes within about a second
  async live_game_starts_elsewhere() {
    const p = page("/home");
    p.answers.coach = { ok: true, data: COACH }; p.answers.page = {};
    await wait(300);
    const before = p.coach();
    p.localStorage.setItem("kw-live:othertab", String(Date.now()));
    await wait(1300);
    return { before, after: p.coach() };
  },
  // an answer to Ask that arrives after the player went into a game: it is never shown or spoken there
  async late_answer_on_a_game_page() {
    const p = page("/home");
    p.answers.coach = { ok: true, data: COACH }; p.answers.page = {};
    p.answers.talk = { ok: true, data: { text: "Play e4.", mood: "explain" } }; p.delays.talk = 1500;
    await wait(300);
    const box = p.body.children.find(c => /^kw-coach/.test(c.className));
    const form = box.querySelector(".kw-ask");
    form.querySelector("input").value = "what should I play";
    form.onsubmit({ preventDefault() {} });
    p.go("/game/live/555");  // into a live game before the answer comes
    await wait(2200);
    return { coach: p.coach(), said: p.said().filter(t => t.includes("e4")) };
  },
  // every address a game against a person can have counts as "may be live" (the old check knew only /game/live)
  async addresses() {
    const p = page("/home");
    const c = p.contract;
    return Object.fromEntries(["/game/185261729330", "/live/game/185261729330", "/game/live/185261729330",
      "/game/daily/162529818", "/play/online", "/play", "/puzzles/battle", "/newgame/185261729330",
      "/home", "/", "/puzzles/rated", "/member/demo_player", "/games/archive", "/stats/overview", "/lessons/x",
      "/puzzles/problem/1234567"].map(x => [x, c.mayBeLive(x)]));
  },
  // a mark from a tab that crashed long ago doesn't keep the coach away for ever; the storage unreadable: stay off
  async stale_marks() {
    const p = page("/home");
    const c = p.contract;
    p.localStorage.setItem("kw-live:old", String(Date.now() - 200000));
    const stale = c.liveElsewhere();
    p.localStorage.setItem("kw-live:new", String(Date.now()));
    const fresh = c.liveElsewhere();
    p.localStorage.getItem = () => { throw new Error("blocked"); };
    return { stale, fresh, unreadable: c.liveElsewhere() };
  },
};

SCENARIOS[scenario]().then(out => { console.log(JSON.stringify(out)); process.exit(0); },
                           e => { console.error(e && e.stack || e); process.exit(1); });
