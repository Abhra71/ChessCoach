// Talks to the coach running on this computer (the Knightwise app). Requests come from here, not from the chess.com
// page, so chess.com never talks to your computer directly.
const COACH = "http://127.0.0.1:8765";

// Say hello to the coach, so its set-up page can show "Connected" as soon as the extension is loaded.
const hello = () => fetch(`${COACH}/api/hello`).catch(() => {});
chrome.runtime.onInstalled.addListener(hello);
chrome.runtime.onStartup.addListener(hello);
hello();

let speakingTab = null, lastCheck = 0;

// Updates without the player doing anything: when the Knightwise app brings new extension files (a Store update),
// or they change on disk, the extension reloads itself. The fingerprint is remembered when it (re)loads.
const stamp = () => fetch(`${COACH}/api/extension-stamp`).then(r => r.json()).then(d => d.stamp).catch(() => null);
chrome.runtime.onInstalled.addListener(async () => { const s = await stamp(); if (s) chrome.storage.local.set({ stamp: s }); });
chrome.alarms.create("update-check", { periodInMinutes: 1 });
chrome.alarms.onAlarm.addListener(async alarm => {
  if (alarm.name !== "update-check") return;
  const [now, { stamp: mine }] = await Promise.all([stamp(), chrome.storage.local.get("stamp")]);
  if (!now) return;  // the app isn't running
  if (!mine) chrome.storage.local.set({ stamp: now });
  else if (now !== mine) chrome.runtime.reload();
});

// The coach's voice plays in a hidden extension page (chess.com's page can't play sound from our app).
async function player() {
  if (await chrome.offscreen.hasDocument()) return;
  await chrome.offscreen.createDocument({ url: "offscreen.html", reasons: ["AUDIO_PLAYBACK"],
                                          justification: "The Knightwise coach speaks its advice." });
}

const json = (url, reply) => fetch(url).then(r => r.json()).then(data => reply({ ok: true, data }))
  .catch(() => reply({ ok: false }));

chrome.runtime.onMessage.addListener((msg, sender, reply) => {
  if (msg.type === "game" && /^\d+$/.test(msg.id)) {
    json(`${COACH}/api/game/${msg.id}`, reply);
    return true;
  }
  if (msg.type === "tags" && Array.isArray(msg.ids)) {  // the archive's tags: finished, checked games only
    const ids = msg.ids.filter(i => /^\d+$/.test(i)).slice(0, 100).join(",");
    json(`${COACH}/api/tags?ids=${ids}`, reply);
    return true;
  }
  if (msg.type === "coach") {
    const q = new URLSearchParams({ section: String(msg.section || "home"), hour: String(msg.hour ?? "") });
    if (/^\d+$/.test(msg.game || "")) q.set("game", msg.game);
    if (msg.again) q.set("again", "1");  // a second visit today: no full welcome again
    json(`${COACH}/api/coach?${q}`, reply);
    return true;
  }
  if (msg.type === "chat") {
    fetch(`${COACH}/api/chat`, { method: "POST", headers: { "Content-Type": "application/json" },
                                 body: JSON.stringify({ coach: msg.coach, message: msg.message, history: msg.history || [] }) })
      .then(r => r.json()).then(data => reply({ ok: true, data })).catch(() => reply({ ok: false }));
    return true;
  }
  if (msg.type === "greeted") {  // when this section's coach last greeted the player (once a day)
    const key = `greeted-${msg.section}`;
    if (msg.set) chrome.storage.local.set({ [key]: msg.set }).then(() => reply({ day: msg.set }));
    else chrome.storage.local.get(key).then(v => reply({ day: v[key] || null }));
    return true;
  }
  if (msg.type === "say" && sender.tab) {
    speakingTab = sender.tab.id;
    player().then(() => chrome.runtime.sendMessage({ type: "play", url: `${COACH}/api/say`, text: msg.text, voice: msg.voice }));
    return false;
  }
  if (msg.type === "open-app" && /^[a-z/]+$/.test(msg.route || "")) {  // bring the Knightwise window forward
    fetch(`${COACH}/api/show`, { method: "POST", headers: { "Content-Type": "application/json" },
                                 body: JSON.stringify({ route: msg.route }) }).catch(() => {});
    return false;
  }
  if (msg.type === "check-now") {  // at most once a minute, whatever the pages ask
    if (Date.now() - lastCheck > 55000) {
      lastCheck = Date.now();
      fetch(`${COACH}/api/check-now`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" }).catch(() => {});
    }
    return false;
  }
  if (msg.type === "health" && /^[a-z-]+$/.test(msg.check || "")) {  // the self-check: pass what a page found to the app
    fetch(`${COACH}/api/health`, { method: "POST", headers: { "Content-Type": "application/json" },
                                   body: JSON.stringify({ check: msg.check, ok: !!msg.ok, detail: String(msg.detail || "") }) })
      .catch(() => {});
    return false;
  }
  if (msg.type === "hush") {
    chrome.runtime.sendMessage({ type: "stop" }).catch(() => {});
    return false;
  }
  if (msg.type === "speaking" && speakingTab !== null) {  // from the hidden player: pass it on to the page
    chrome.tabs.sendMessage(speakingTab, msg).catch(() => {});
    return false;
  }
  return false;
});
