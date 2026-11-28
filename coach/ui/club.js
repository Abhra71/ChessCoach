// The club (storyline steps 3.3, 3.4 and 3.6, 28 Nov): chess words you tap for their meaning, the Chess words page,
// each page's room name, Meet your coaches, and the coaches' memories that belong to opening a page.
// Plain script after app.js and coaches.js: it uses their api, go, shell, svg, esc and Coach.

// ---------- chess words, learned one at a time (owner, 28 Nov) ----------
// A word the player hasn't met has a small dotted line the first time it appears (at most two new ones a page, so
// it's never busy); hover or tap shows what it means. From then on it's ordinary text: the coaches just use it.
let KW_WORDS = null, KW_WORD_RE = null;
const KW_FORM = {}, KW_MET = new Set(), KW_NEW_HERE = {};  // word -> the page (hash) where it was new
const NO_MARK = "a,button,input,textarea,select,svg,h1,h2,code,pre,label,summary,.term,.board,.cg-wrap,.words-page,.explore,.kw-head,.kw-actions,.term-pop";
function loadWords() {
  if (KW_WORDS) return Promise.resolve(KW_WORDS);
  return api("/api/words").then(w => {
    KW_WORDS = w;
    (w.met || []).forEach(x => KW_MET.add(x));
    const forms = [];
    w.words.forEach(x => x.forms.forEach(f => { KW_FORM[f.toLowerCase()] = x; forms.push(f); }));
    forms.sort((a, b) => b.length - a.length);  // "passed pawns" before "passed pawn"
    if (forms.length) KW_WORD_RE = new RegExp(`\\b(${forms.map(f => f.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|")})\\b`, "i");
    return w;
  });
}
function markWords(root, where) {
  // Changes the page only where it underlines a word, never otherwise (28 Nov: splitting text at every match woke the
  // watcher below again and again and froze the app)
  if (!KW_WORD_RE || !root) return;
  const here = `${where}:${location.hash}`, limit = (KW_WORDS && KW_WORDS.per_page) || 2;
  const done = new Set([...root.querySelectorAll(".term")].map(e => e.dataset.word));
  const isNew = w => !KW_MET.has(w) || KW_NEW_HERE[w] === here;  // met on this very page: stays marked while you're here
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, { acceptNode: n =>
    n.nodeValue.trim().length > 2 && n.parentElement && !n.parentElement.closest(NO_MARK) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT });
  const nodes = [];
  while (walker.nextNode() && nodes.length < 4000) nodes.push(walker.currentNode);
  const every = new RegExp(KW_WORD_RE.source, "gi");
  for (let i = 0; i < nodes.length && i < 8000 && done.size < limit; i++) {
    const n = nodes[i];
    every.lastIndex = 0;
    let m, hit = null;
    while ((m = every.exec(n.nodeValue))) {
      const x = KW_FORM[m[1].toLowerCase()];
      if (x && !done.has(x.word) && isNew(x.word)) { hit = { m, x }; break; }
    }
    if (!hit) continue;
    const w = hit.x.word;
    done.add(w);
    if (!KW_MET.has(w)) { KW_MET.add(w); KW_NEW_HERE[w] = here; api("/api/words/met", { word: w }).catch(() => {}); }
    const word = n.splitText(hit.m.index), after = word.splitText(hit.m[1].length), b = document.createElement("button");
    b.type = "button"; b.className = "term"; b.dataset.word = w; b.textContent = word.nodeValue;
    b.setAttribute("aria-label", `${word.nodeValue}: what does it mean?`);
    word.replaceWith(b);
    if (after.nodeValue) nodes.push(after);  // the rest of this text may hold another new word
  }
}
let popHide = null, popShow = null;
function wordPop(b, keep) {
  const old = document.querySelector(".term-pop");
  if (old) { const same = old.dataset.word === b.dataset.word; if (same && keep) return; old.remove(); if (same) return; }
  const x = (KW_WORDS && KW_WORDS.words || []).find(w => w.word === b.dataset.word);
  if (!x) return;
  const pop = document.createElement("div");
  pop.className = "term-pop"; pop.dataset.word = x.word; pop.setAttribute("role", "tooltip");
  pop.innerHTML = `<b>${esc(x.word)}</b><p>${esc(x.meaning)}</p><a href="#/words">All chess words</a>`;
  document.body.appendChild(pop);
  const r = b.getBoundingClientRect(), w = Math.min(280, innerWidth - 32);
  pop.style.width = w + "px";
  pop.style.left = Math.max(16, Math.min(r.left, innerWidth - w - 16)) + "px";
  const below = r.bottom + 6, h = pop.offsetHeight;
  pop.style.top = (below + h > innerHeight - 8 ? Math.max(8, r.top - h - 6) : below) + "px";
  api("/api/words/looked", { word: x.word }).catch(() => {});
}
const closePop = () => { const p = document.querySelector(".term-pop"); if (p) p.remove(); };
document.addEventListener("click", e => {  // a tap: for touch screens, and for anyone who clicks
  const t = e.target.closest && e.target.closest(".term");
  if (t) { e.preventDefault(); e.stopPropagation(); clearTimeout(popShow); return wordPop(t, !!document.querySelector(".term-pop.hovered")); }
  if (!(e.target.closest && e.target.closest(".term-pop"))) closePop();
}, true);
document.addEventListener("mouseover", e => {  // a hover: the meaning comes after a short moment, goes when you move away
  const on = e.target.closest && (e.target.closest(".term") || e.target.closest(".term-pop"));
  if (!on) return;
  clearTimeout(popHide);
  if (on.classList.contains("term")) {
    clearTimeout(popShow);
    popShow = setTimeout(() => { wordPop(on, true); const p = document.querySelector(".term-pop"); if (p) p.classList.add("hovered"); }, 220);
  }
});
document.addEventListener("mouseout", e => {
  const from = e.target.closest && (e.target.closest(".term") || e.target.closest(".term-pop"));
  if (!from) return;
  clearTimeout(popShow);
  const p = document.querySelector(".term-pop.hovered");
  if (p) { clearTimeout(popHide); popHide = setTimeout(() => { if (!p.matches(":hover")) p.remove(); }, 300); }
});
document.addEventListener("keydown", e => { if (e.key === "Escape") closePop(); });
window.addEventListener("hashchange", closePop);
let markTimer = null, markWatch = null;
const WATCH = { childList: true, subtree: true };
function markAll() {
  if (markWatch) markWatch.disconnect();  // our own underlining must not wake the watcher
  try { markWords(document.getElementById("page"), "page"); document.querySelectorAll(".kw-coach .kw-box").forEach(b => markWords(b, "coach")); }
  finally { if (markWatch) { markWatch.takeRecords(); markWatch.observe(document.body, WATCH); } }
}
loadWords().then(() => {
  markWatch = new MutationObserver(() => { clearTimeout(markTimer); markTimer = setTimeout(markAll, 400); });
  markAll();
}).catch(() => {});

// the Chess words page: part of the library (Your plan), so the plan stays lit in the menu
async function wordsView() {
  shell("plan", `<p class="muted">Loading…</p>`);
  const w = await loadWords();
  const met = new Set([...(w.met || []), ...KW_MET]);
  $("#page").innerHTML = `<div class="page-head"><div><h1>Chess words</h1>
      <p class="sub">The words strong players use, in plain language. A new word has a small dotted line the first time you meet it: hover or tap it for its meaning. ✓ marks the ones you've met.</p></div></div>
    <label class="explore-box words-find">${svg("search")}<input id="wq" type="search" autocomplete="off" spellcheck="false" placeholder="Find a word…"></label>
    <p class="small muted words-count">The basics: ${w.words.length} words. More come with the Book, as you climb.</p>
    <div class="words-page" id="wl">${w.words.map(x => `<div class="box word${met.has(x.word) ? " met" : ""}" data-find="${esc((x.word + " " + x.forms.join(" ") + " " + x.meaning).toLowerCase())}">
      <b>${esc(x.word)}</b><span>${esc(x.meaning)}</span></div>`).join("")}</div>
    <p class="muted small" id="wnone" hidden>No word by that name yet. Try Explore in Your plan.</p>`;
  const q = $("#wq");
  q.addEventListener("input", () => {
    const s = q.value.trim().toLowerCase();
    let shown = 0;
    document.querySelectorAll("#wl .word").forEach(el => { const on = !s || el.dataset.find.includes(s); el.hidden = !on; shown += on; });
    $("#wnone").hidden = shown > 0;
  });
}
// Explore is the library's dictionary: a chess word typed there shows its meaning above the results
function wordsFor(q) {
  const s = String(q || "").trim().toLowerCase();
  if (!KW_WORDS || s.length < 3) return [];
  return KW_WORDS.words.filter(x => x.word.toLowerCase().includes(s) || x.forms.some(f => f.toLowerCase() === s)).slice(0, 2);
}

// ---------- Meet your coaches ----------
const MEET = [
  { id: "maya", from: "Chennai, India", lines: [
      "Grew up in Chennai, India's chess city, playing school tournaments from the age of seven. State junior champion at 14, then open tournaments across Asia.",
      "Chose coaching over playing: \"I liked watching someone get it more than winning myself.\""],
    teaches: "Fast, warm and practical. Loves tactics and blitz. Never lets a mistake go by without: here's what to look for next time.",
    rooms: "Your games, Practice, Today's 5 minutes, and the coach beside you on chess.com." },
  { id: "viktor", from: "Berlin, Germany", lines: [
      "From Berlin, the city where Emanuel Lasker, world champion for 27 years, lived. Played the German championship for years, never became a grandmaster, and taught at a Berlin chess school for thirty years.",
      "Keeps a notebook of the games that changed chess. Each rank you reach opens a page of it."],
    teaches: "Calm, patient, a storyteller. Strict about one thing: see it before you move it.",
    rooms: "Progress, Your plan, Your level, Your course and the practice hall (Train)." },
];
function coachesView() {
  shell("home", "");
  $("#page").innerHTML = `<div class="page-head"><div><h1>Meet your coaches</h1></div></div>
    <div class="meet">${MEET.map(c => `<div class="box meet-card">
      <div class="meet-face">${KnightwiseFaces.figure(c.id, "greet")}</div>
      <div><h2>${esc(COACHES[c.id].name)}${KnightwiseFaces.flag ? KnightwiseFaces.flag(c.id) : ""}</h2>
        <div class="muted small">${esc(c.from)} · ${esc(COACHES[c.id].role)}</div>
        ${c.lines.map(l => `<p>${esc(l)}</p>`).join("")}
        <p><b>How ${c.id === "maya" ? "she" : "he"} teaches.</b> ${esc(c.teaches)}</p>
        <p class="muted small"><b>${c.id === "maya" ? "Her" : "His"} rooms:</b> ${esc(c.rooms)}</p></div></div>`).join("")}</div>
    <p class="muted small meet-note">Maya and Viktor are characters written for Knightwise, not real players. Your games, and everything they tell you about them, are real.</p>`;
}

// ---------- a memory that belongs to opening a page, told once (Viktor's regret in In your head) ----------
function pageMemory(name, wait) {
  if (!["calc", "repertoire"].includes(name)) return;
  const here = location.hash;
  api(`/api/memory?page=${name}`).then(m => {
    if (!m || !m.line) return;
    setTimeout(() => {
      if (location.hash !== here) return;  // they left: it waits for the next time
      Coach.react(m.coach, "explain", m.line);
      api(`/api/memory/told?id=${encodeURIComponent(m.id)}`).catch(() => {});
    }, wait);
  }).catch(() => {});
}
