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

async function play(url, text, voice, slow) {
  stop();
  const mine = run;
  const fetchOne = s => fetch(url, { method: "POST", headers: { "Content-Type": "application/json" },
                                    body: JSON.stringify({ text: s, voice, ...(slow ? { slow: true } : {}) }) })
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
  if (msg.type === "play") play(msg.url, msg.text, msg.voice, msg.slow);
});

// ---- Talk on chess.com (0.6): record the player's voice here, then the Knightwise app writes it down ----
// Click to talk, click again to stop (20 Oct, the user: "click to talk, click again to stop is better"): it records
// until the player clicks Stop (sent) or leaves (nothing is sent), and stops by itself only after a minute.
let recording = null;
async function record(app) {
  let stream;
  try { stream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } }); }
  catch (e) { return { error: "mic" }; }  // not allowed yet: the page offers the one-time "Allow"
  const ctx = new AudioContext({ sampleRate: 16000 }), src = ctx.createMediaStreamSource(stream);
  const node = ctx.createScriptProcessor(4096, 1, 1), chunks = [];
  let level = 0, sound = false;  // sound: anything but zeros (a switched-off headset sends only zeros, 19 Oct)
  node.onaudioprocess = e => {
    const d = new Float32Array(e.inputBuffer.getChannelData(0)); chunks.push(d);
    let sum = 0; for (const v of d) { sum += v * v; if (v) sound = true; } level = Math.sqrt(sum / d.length);
  };
  src.connect(node); node.connect(ctx.destination);
  const me = recording = { send: false };
  const began = Date.now();
  let heard = false;
  while (recording === me) {
    await new Promise(r => setTimeout(r, 100));
    if (level > 0.02) heard = true;
    if (Date.now() - began > 60000) { me.send = true; break; }  // a minute: stop by itself, and send it
  }
  node.disconnect(); stream.getTracks().forEach(t => t.stop()); await ctx.close();
  if (recording === me) recording = null;
  if (!me.send) return { text: "", cancelled: true };
  if (!heard && !sound) return { error: "Your microphone sends no sound. Check which one Windows is using, then try again." };
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
  if (msg.type === "kw-record-stop" && recording) { recording.send = !!msg.send; recording = null; }
  return false;
});
