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
      <a href="${COACH}/" target="_blank">Your review</a><a href="${COACH}/practice" target="_blank">Practice</a>`;
  })
  .catch(() => {
    state.className = "off";
    state.innerHTML = `<span class="dot"></span>The coach is not running`;
    more.innerHTML = `<p class="muted">Start it in the ChessCoach folder with <code>python -m coach.service</code>,
      or once and for all with <code>python -m coach.autorun install</code>.</p>`;
  });
