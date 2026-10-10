// Talks to the coach running on this computer (python -m coach.service). Requests come from here, not from
// the chess.com page, so chess.com never talks to your computer directly.
const COACH = "http://127.0.0.1:8765";

// Say hello to the coach, so its set-up page can show "Connected" as soon as the extension is loaded.
const hello = () => fetch(`${COACH}/api/hello`).catch(() => {});
chrome.runtime.onInstalled.addListener(hello);
chrome.runtime.onStartup.addListener(hello);
hello();

chrome.runtime.onMessage.addListener((msg, _sender, reply) => {
  if (msg.type !== "game" || !/^\d+$/.test(msg.id)) return false;
  fetch(`${COACH}/api/game/${msg.id}`)
    .then(r => r.json())
    .then(data => reply({ ok: true, data }))
    .catch(() => reply({ ok: false }));
  return true; // answer comes later
});
