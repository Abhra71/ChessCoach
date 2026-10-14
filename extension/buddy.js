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
    const face = `<button class="kw-char" title="${esc(s.name)}, your Knightwise coach">${KnightwiseFaces.figure(s.coach, s.pose || s.mood)}</button>`;
    box.innerHTML = open ? `${face}
      <div class="kw-box" role="status">
        <div class="kw-head"><b>${esc(s.name)}</b><span>${esc(s.role || "Knightwise coach")}</span>
          <button class="kw-x" title="Fold away">–</button></div>
        ${s.lines.map(l => `<p>${esc(l)}</p>`).join("")}
        ${s.actions && s.actions.length ? `<div class="kw-actions">${s.actions.map((a, i) => {
          const best = a.best ? ` class="kw-best" title="${esc(a.why || "My pick")}"` : "";  // the coach's pick, said out loud
          return a.app ? `<button data-app="${esc(a.app)}"${best}>${esc(a.label)}</button>`
            : a.find && target(a.find) ? `<button data-guide="${i}"${best}>${esc(a.label)}</button>`
            : `<a href="${esc(a.url)}"${best}>${esc(a.label)}</a>`;
        }).join("")}</div>` : ""}
        ${s.ai_hint ? `<p class="kw-hint">${esc(s.ai_hint)}</p>` : ""}
        ${s.ai_ready ? `<form class="kw-ask"><input placeholder="Ask ${esc(s.name)} anything about your chess" maxlength="300">
          <button>Ask</button></form>` : ""}
        ${s.note ? `<p class="kw-hint">${esc(s.note)}</p>` : ""}
      </div>` : `${face}<button class="kw-tab">${esc(s.name)}</button>`;
    const wake = box.querySelector(".kw-tab");
    if (wake) wake.onclick = () => { render(true); speak(); };
    box.querySelector(".kw-char").onclick = () => { if (open) fold(); else { render(true); speak(); } };
    box.querySelectorAll("[data-app]").forEach(b => b.onclick = () => {  // opens the Knightwise app at that page
      send({ type: "open-app", route: b.dataset.app });
      said = { ...said, pose: "pleased", lines: ["Opening Knightwise for you. See you there."], actions: [] };
      render(true); speak();
    });
    box.querySelectorAll("[data-guide]").forEach(b => b.onclick = () => guide(s.actions[Number(b.dataset.guide)]));
    const form = box.querySelector(".kw-ask");
    if (form) form.onsubmit = e => { e.preventDefault(); const q = form.querySelector("input").value.trim(); if (q) ask(q); };
    const x = box.querySelector(".kw-x");
    if (x) x.onclick = fold;
  }

  // ---- the navigation guide: point at chess.com's own link, the player clicks it, the next coach notices ----
  let ring = null, ringFor = null, nudge = null;

  function target(find) {  // chess.com's visible link to that section, preferring the menu on the left
    const links = [...document.querySelectorAll("a[href]")].filter(a => {
      try { return new URL(a.href, location.href).pathname.startsWith(find.path) && a.getClientRects().length; } catch (e) { return false; }
    });
    return links.sort((a, b) => a.getBoundingClientRect().left - b.getBoundingClientRect().left)[0] || null;
  }

  function placeRing() {
    if (!ring || !ringFor || !ringFor.isConnected) return unring();
    const r = ringFor.getBoundingClientRect();
    const left = Math.max(2, r.left - 6), top = Math.max(2, r.top - 6);  // never cut off at the edge
    Object.assign(ring.style, { left: `${left}px`, top: `${top}px`, width: `${r.right + 6 - left}px`, height: `${r.bottom + 6 - top}px` });
  }

  function unring() {
    if (ring) ring.remove();
    ring = null; ringFor = null; clearTimeout(nudge);
    removeEventListener("scroll", placeRing, true); removeEventListener("resize", placeRing);
  }

  function guide(action) {
    const el = target(action.find);
    if (!el) { location.href = action.url; return; }  // their menu moved: plain link (the player asked to go there)
    unring();
    ringFor = el;
    ring = document.createElement("div");
    ring.className = "kw-ring";
    document.body.appendChild(ring);
    placeRing();
    addEventListener("scroll", placeRing, true); addEventListener("resize", placeRing);
    try { sessionStorage.setItem("kw-guided", action.find.path); } catch (e) {}
    said = { ...said, mood: "calm", pose: "point", actions: [], ai_hint: null,
             lines: [`Click "${action.find.name}" where the red ring is. I'll wait.`] };
    render(true); speak();
    nudge = setTimeout(() => {  // still here: point again, a little bigger
      if (!ring) return;
      ring.classList.add("again");
      said = { ...said, lines: [`It's right there, in the red ring: "${action.find.name}".`] };
      render(true); speak();
    }, 12000);
  }

  // ---- talking with the coach (with the player's free AI key; written replies when the AI is busy) ----
  const history = [];
  async function ask(question) {
    clearTimeout(foldTimer);
    history.push(["player", question]);
    said = { ...said, mood: "thinking", pose: "listen", lines: [`"${question}"`, "…"], actions: [], note: null };
    render(true);
    const r = await send({ type: "chat", coach: said.coach, message: question, history: history.slice(0, -1) });
    const reply = r && r.ok ? r.data : { text: "I can't reach the Knightwise app on this PC, and I answer from there. Open it from the Start menu.", mood: "calm" };
    history.push(["coach", reply.text]);
    said = { ...said, mood: reply.mood, pose: "explain", lines: [reply.text], note: reply.note || null };
    render(true); speak();
    const input = box && box.querySelector(".kw-ask input");
    if (input) input.focus();
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
    if (!msg.on) {
      if (said && said.pose && said.pose !== "point") { said = { ...said, pose: null }; render(true); }  // back to their mood
      clearTimeout(foldTimer); foldTimer = setTimeout(() => render(false), MINUTES_OPEN * 60000);
    }
  });

  async function arrive() {
    const here = section(location.pathname), path = location.pathname;
    if (!here) setTimeout(() => {  // the self-check: a game page at an address the review doesn't know yet?
      if (location.pathname === path && KnightwiseContract.unknownGameAddress(path, !!KnightwiseContract.board(document)))
        KnightwiseContract.report("game-address", false, `unknown: ${path.replace(/\d{6,}/g, "<id>")}`);
    }, 4000);
    if (here === current) return;
    unring();
    remove();
    if (!here) return;  // not a coach section: nothing at all
    current = here;
    const store = (await send({ type: "greeted", section: here })) || {};
    const first = store.day !== today();  // the first visit to this section today: the full welcome
    const r = await send({ type: "coach", section: here, hour: new Date().getHours(), again: !first });
    if (current !== here) return;
    said = r && r.ok ? r.data : {
      coach: "maya", name: "Maya", mood: "calm", voice_on: false, actions: [],
      lines: ["I'm asleep: the Knightwise app isn't running on this PC.",
              "Everything I do here, your reviews, my advice and my voice, comes from the app. Open Knightwise from the Start menu and I'll be right back."],
    };
    let guided = null;
    try { guided = sessionStorage.getItem("kw-guided"); sessionStorage.removeItem("kw-guided"); } catch (e) {}
    if (guided && location.pathname.startsWith(guided) && r && r.ok) {  // they followed the guide: say so, warmly
      said = { ...said, mood: "pleased", pose: "celebrate", lines: ["Nice, you found it.", ...said.lines.slice(1)] };
      render(true); speak();
      return;
    }
    if (current !== here) return;
    if (first && r && r.ok) said = { ...said, pose: "greet" };
    render(true);  // never silent: the full welcome first, later in the day just where things stand
    if (first && r && r.ok) { send({ type: "greeted", section: here, set: today() }); speak(); }  // asleep: try again later
    else { clearTimeout(foldTimer); foldTimer = setTimeout(() => render(false), MINUTES_OPEN * 60000); }
  }

  // ---- the archive: a Knightwise tag on each finished game ("clean game", "2 pieces left hanging") ----
  let tagTimer = null, archiveSince = null;
  async function tagArchive() {
    if (!/^\/games\/archive(\/|$)/.test(location.pathname)) { archiveSince = null; return; }
    archiveSince = archiveSince || Date.now();
    const rows = KnightwiseContract.archiveRows(document).filter(r => !r.slot.querySelector(".kw-tag"));
    if (!rows.length) {
      if (!document.querySelector(".kw-tag") && Date.now() - archiveSince > 15000) {  // still loading before that
        KnightwiseContract.report("archive-rows", false, "no game rows after 15 s");
      }
      if (!document.querySelector(".kw-tag")) { clearTimeout(tagTimer); tagTimer = setTimeout(tagArchive, 5000); }
      return;
    }
    KnightwiseContract.report("archive-rows", true);
    const r = await send({ type: "tags", ids: rows.map(x => x.id) });
    if (!r || !r.ok) return;  // the app isn't running: no tags, nothing else changes
    for (const { id, slot } of rows) {
      const t = r.data[id];
      if (!t || slot.querySelector(".kw-tag")) continue;
      const tag = document.createElement("span");
      tag.className = `kw-tag ${t.tone}`;
      tag.title = "Knightwise checked this game";
      tag.textContent = t.tone === "good" ? `✓ ${t.text}` : t.text;
      tag.onclick = e => { e.preventDefault(); e.stopPropagation(); send({ type: "open-app", route: `games/${id}` }); };
      slot.appendChild(tag);
    }
  }
  new MutationObserver(() => { clearTimeout(tagTimer); tagTimer = setTimeout(tagArchive, 600); })  // next pages load later
    .observe(document.body, { childList: true, subtree: true });

  // chess.com changes pages without reloading: notice the address changing
  let last = location.pathname;
  setInterval(() => { if (location.pathname !== last) { last = location.pathname; arrive(); } }, 700);
  arrive();
})();
