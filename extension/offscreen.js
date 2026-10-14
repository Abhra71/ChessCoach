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

// ---- Talk on chess.com (0.6): record the player's voice here, then the Knightwise app writes it down ----
// Listens until they've spoken and then been quiet for a moment; nothing at all if they say nothing in 8 seconds.
let recording = null;
async function record(app) {
  let stream;
  try { stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } }); }
  catch (e) { return { error: "mic" }; }  // not allowed yet: the page offers the one-time "Allow"
  const ctx = new AudioContext({ sampleRate: 16000 }), src = ctx.createMediaStreamSource(stream);
  const node = ctx.createScriptProcessor(4096, 1, 1), chunks = [];
  let level = 0;
  node.onaudioprocess = e => {
    const d = new Float32Array(e.inputBuffer.getChannelData(0)); chunks.push(d);
    let sum = 0; for (const v of d) sum += v * v; level = Math.sqrt(sum / d.length);
  };
  src.connect(node); node.connect(ctx.destination);
  const me = recording = {};
  const began = Date.now();
  let heard = false, lastLoud = 0;
  while (true) {
    await new Promise(r => setTimeout(r, 100));
    const now = Date.now();
    if (level > 0.02) { heard = true; lastLoud = now; }
    if (recording !== me || (!heard && now - began > 8000)) { heard = heard && recording === me; break; }
    if ((heard && now - lastLoud > 1300) || now - began > 25000) break;
  }
  node.disconnect(); stream.getTracks().forEach(t => t.stop()); await ctx.close();
  if (recording === me) recording = null;
  if (!heard) return { text: "" };
  const n = chunks.reduce((a, c) => a + c.length, 0), pcm = new Int16Array(n);
  let i = 0;
  for (const c of chunks) for (const v of c) pcm[i++] = Math.max(-1, Math.min(1, v)) * 32767;
  try {
    const r = await fetch(`${app}/api/listen`, { method: "POST", headers: { "Content-Type": "application/octet-stream" }, body: pcm.buffer });
    const j = await r.json();
    return r.ok ? { text: j.text || "" } : { error: j.message || "Couldn't hear that." };
  } catch (e) { return { error: "app" }; }
}
chrome.runtime.onMessage.addListener((msg, sender, reply) => {
  if (msg.type === "kw-record") { record(msg.app).then(reply); return true; }
  if (msg.type === "kw-record-stop") recording = null;
  return false;
});
