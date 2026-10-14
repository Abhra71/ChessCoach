// Plays the coach's voice for chess.com pages: asks the Knightwise app for each sentence as audio, then plays them
// in order. One sentence at a time, like the app, so she starts speaking after about a second instead of waiting
// for the whole message to be voiced (14 Oct: the voice on chess.com started late, debrief point 35).
const PAUSE = 450;  // a breath between sentences, the same as the app
let run = 0, audio = null;

const tell = on => chrome.runtime.sendMessage({ type: "speaking", on }).catch(() => {});
const sentences = text => (String(text).match(/[^.!?]+[.!?]*(\s+|$)/g) || []).map(s => s.trim()).filter(Boolean);

function stop() {
  run++;
  if (audio) { audio.pause(); audio = null; }
}

async function play(url, text, voice) {
  stop();
  const mine = run;
  const fetchOne = s => fetch(url, { method: "POST", headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ text: s, voice }) })
    .then(r => { if (!r.ok) throw new Error("no voice"); return r.blob(); });
  const parts = sentences(text);
  let next = parts.length ? fetchOne(parts[0]) : null;
  try {
    for (let i = 0; i < parts.length && mine === run; i++) {
      const blob = await next;
      next = i + 1 < parts.length ? fetchOne(parts[i + 1]) : null;  // the next one is voiced while this one plays
      if (mine !== run) return;
      await new Promise(done => {
        const a = new Audio(URL.createObjectURL(blob));
        audio = a;
        a.onplay = () => tell(true);
        a.onended = a.onerror = done;
        a.play().catch(done);
      });
      if (i + 1 < parts.length) await new Promise(r => setTimeout(r, PAUSE));
    }
  } catch (e) { /* the app isn't running or the voice isn't installed: stay quiet */ }
  if (mine === run) { audio = null; tell(false); }
}

chrome.runtime.onMessage.addListener(msg => {
  if (msg.type === "stop") { stop(); tell(false); }
  if (msg.type === "play") play(msg.url, msg.text, msg.voice);
});
