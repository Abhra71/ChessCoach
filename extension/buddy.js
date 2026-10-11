// The Knightwise coach on chess.com: a face in the corner, what it says in a box under it, and its voice.
//
// Fair play: it appears ONLY on sections where no game can be running (an allow-list below). On any play page,
// game page, Puzzle Battle or anything unknown it does not appear at all and reads nothing from the page.
// It never clicks or moves anything: it suggests, the player clicks.
(() => {
  if (window.top !== window) return;

  // path -> section. Anything not listed: no coach.
  function section(path) {
    if (path === "/" || path === "/home") return "home";
    if (/^\/puzzles\/(battle|rush\/battle)/.test(path)) return null;  // against other people
    if (/^\/puzzles(\/|$)/.test(path)) return "puzzles";
    if (/^\/(lessons|learn|courses)(\/|$)/.test(path)) return "lessons";
    if (/^\/(stats|games\/archive)(\/|$)/.test(path)) return "progress";
    return null;
  }

  const MINUTES_OPEN = 0.5;  // the box folds back to the face this long after it has finished talking
  let box = null, current = null, foldTimer = null, said = null;

  const send = msg => new Promise(resolve => {
    try { chrome.runtime.sendMessage(msg, r => resolve(chrome.runtime.lastError ? null : r)); } catch (e) { resolve(null); }
  });
  const today = () => new Date().toISOString().slice(0, 10);
  const esc = s => String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  function remove() {
    if (box) box.remove();
    box = null; current = null; clearTimeout(foldTimer);
    send({ type: "hush" });
  }

  function render(open) {
    const s = said;
    if (!s) return;
    if (!box) {
      box = document.createElement("div");
      box.className = "kw-coach";
      document.body.appendChild(box);
    }
    box.className = `kw-coach ${open ? "open" : "folded"}`;
    const face = `<button class="kw-avatar" title="${esc(s.name)}, your Knightwise coach">${KnightwiseFaces.svg(s.coach, s.mood)}</button>`;
    box.innerHTML = open ? `${face}
      <div class="kw-box" role="status">
        <div class="kw-head"><b>${esc(s.name)}</b><span>${esc(s.role || "Knightwise coach")}</span>
          <button class="kw-x" title="Fold away">–</button></div>
        ${s.lines.map(l => `<p>${esc(l)}</p>`).join("")}
        ${s.actions && s.actions.length ? `<div class="kw-actions">${s.actions.map(a =>
          `<a href="${esc(a.url)}">${esc(a.label)}</a>`).join("")}</div>` : ""}
        ${s.ai_hint ? `<p class="kw-hint">${esc(s.ai_hint)}</p>` : ""}
      </div>` : face;
    box.querySelector(".kw-avatar").onclick = () => { if (open) fold(); else { render(true); speak(); } };
    const x = box.querySelector(".kw-x");
    if (x) x.onclick = fold;
  }

  function fold() { clearTimeout(foldTimer); send({ type: "hush" }); render(false); }

  async function speak() {
    if (!said || !said.voice_on) return;
    send({ type: "say", text: said.lines.join(" "), voice: said.voice });
  }

  // the offscreen player tells us when the voice starts and stops, so the mouth moves only while it talks
  chrome.runtime.onMessage.addListener(msg => {
    if (msg.type !== "speaking" || !box) return;
    box.classList.toggle("talking", !!msg.on);
    if (!msg.on) { clearTimeout(foldTimer); foldTimer = setTimeout(() => render(false), MINUTES_OPEN * 60000); }
  });

  async function arrive() {
    const here = section(location.pathname);
    if (here === current) return;
    remove();
    if (!here) return;  // not a coach section: nothing at all
    current = here;
    const r = await send({ type: "coach", section: here, hour: new Date().getHours() });
    if (current !== here) return;
    said = r && r.ok ? r.data : {
      coach: "zara", name: "Zara", mood: "calm", voice_on: false, actions: [],
      lines: ["I'm asleep right now. Open Knightwise from the Start menu and I'll coach you here."],
    };
    const store = (await send({ type: "greeted", section: here })) || {};
    const first = store.day !== today();
    render(first);
    if (first && r && r.ok) { send({ type: "greeted", section: here, set: today() }); speak(); }  // asleep: try again later
  }

  // chess.com changes pages without reloading: notice the address changing
  let last = location.pathname;
  setInterval(() => { if (location.pathname !== last) { last = location.pathname; arrive(); } }, 700);
  arrive();
})();
