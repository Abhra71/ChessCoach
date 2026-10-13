// Toolbar popup: is the coach running on this computer? Links to the review and practice pages.
const COACH = "http://127.0.0.1:8765";
const state = document.getElementById("state"), more = document.getElementById("more");

fetch(`${COACH}/api/status`)
  .then(r => r.json())
  .then(s => {
    state.className = "on";
    state.innerHTML = `<span class="dot"></span>Running for <b></b>`;
    state.querySelector("b").textContent = s.player || "?";
    more.innerHTML = `<p class="muted">Last check for new games: ${s.last_update || "starting…"}</p>
      <p class="muted" id="health"></p>
      <a href="${COACH}/" target="_blank">Your review</a><a href="${COACH}/practice" target="_blank">Practice</a>`;
    document.getElementById("health").textContent = healthLine(s.health);
  })
  .catch(() => {
    state.className = "off";
    state.innerHTML = `<span class="dot"></span>The coach is not running`;
    more.innerHTML = `<p class="muted">Open <b>Knightwise</b> from the Start menu. It then keeps running by the clock.</p>`;
  });

// the chess.com self-check, in one line: all working, or what chess.com changed
function healthLine(h) {
  if (!h || (!h.verified && !h.broken.length)) return "chess.com check: not run yet. Open a finished game.";
  if (h.broken.length) return `chess.com check: ${h.broken[0].says}`;
  return `chess.com check: all working, last verified ${new Date(h.verified * 1000).toLocaleString()}.`;
}
