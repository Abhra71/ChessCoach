// Measure songs in a hidden Edge: loudness over time, the beat (tempo and where it falls), and the big hits.
// node beats.mjs song.mp3 [song2.mp3 ...]  -> beats-<song>.json
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
const songs = process.argv.slice(2);
const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const edge = spawn(EDGE, ["--headless=new", "--remote-debugging-port=9335", `--user-data-dir=${path.resolve("edgeprof3")}`, "about:blank"], { stdio: "ignore" });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let targets;
for (let k = 0; k < 200; k++) { try { targets = await (await fetch("http://127.0.0.1:9335/json")).json(); if (targets.find(t => t.type === "page")) break; } catch {} await sleep(250); }
const ws = new WebSocket(targets.find(t => t.type === "page").webSocketDebuggerUrl);
await new Promise(r => ws.onopen = r);
let id = 0; const wait = {};
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && wait[m.id]) { wait[m.id](m); delete wait[m.id]; } };
const send = (method, params = {}) => new Promise(r => { const n = ++id; wait[n] = r; ws.send(JSON.stringify({ id: n, method, params })); });
const run = async js => { const r = await send("Runtime.evaluate", { expression: js, awaitPromise: true, returnByValue: true }); if (r.result.exceptionDetails) console.log(JSON.stringify(r.result.exceptionDetails).slice(0, 500)); return r.result && r.result.result && r.result.result.value; };
await send("Page.navigate", { url: "http://127.0.0.1:8766/ui/trailer.html" }); await sleep(2500);
const JS = song => `(async () => {
  const raw = await (await fetch("/ui/vendor/film/${song}")).arrayBuffer();
  const ac = new OfflineAudioContext(1, 44100, 44100); const buf = await ac.decodeAudioData(raw);
  const SR = buf.sampleRate, N = buf.length;
  async function band(type, f) {  // the song through a filter, mono
    const o = new OfflineAudioContext(1, N, SR), s = o.createBufferSource(); s.buffer = buf;
    let last = s; if (type) { const b = o.createBiquadFilter(); b.type = type; b.frequency.value = f; s.connect(b); last = b; }
    last.connect(o.destination); s.start(); return (await o.startRendering()).getChannelData(0);
  }
  const all = await band(null), low = await band("lowpass", 150), high = await band("highpass", 2500);
  const HOP = 441;  // 10 ms
  const env = x => { const n = Math.floor(N / HOP), e = new Float32Array(n); for (let i = 0; i < n; i++) { let s = 0; for (let j = i * HOP; j < (i + 1) * HOP; j++) s += x[j] * x[j]; e[i] = Math.sqrt(s / HOP); } return e; };
  const E = env(all), L = env(low), Hh = env(high);
  const flux = e => { const f = new Float32Array(e.length); for (let i = 1; i < e.length; i++) f[i] = Math.max(0, Math.log(1e-4 + e[i]) - Math.log(1e-4 + e[i - 1])); return f; };
  const FL = flux(L), FH = flux(Hh), FA = flux(E);
  const O = FL.map((v, i) => v + 0.5 * FH[i] + 0.5 * FA[i]);
  // loudness, per half second, in dB
  const loud = []; for (let i = 0; i < E.length; i += 50) { let s = 0, c = 0; for (let j = i; j < Math.min(E.length, i + 50); j++) { s += E[j] * E[j]; c++; } loud.push(Math.round(10 * Math.log10(1e-9 + s / c))); }
  const lowloud = []; for (let i = 0; i < L.length; i += 50) { let s = 0, c = 0; for (let j = i; j < Math.min(L.length, i + 50); j++) { s += L[j] * L[j]; c++; } lowloud.push(Math.round(10 * Math.log10(1e-9 + s / c))); }
  // tempo over windows of 20 s: autocorrelation of the onset curve between 60 and 190 beats a minute
  function tempo(a, b) {
    let best = 0, bl = 0;
    for (let lag = 31; lag <= 100; lag++) { let s = 0; for (let i = a + lag; i < b; i++) s += O[i] * O[i - lag]; s /= (b - a - lag); if (s > best) { best = s; bl = lag; } }
    // refine to a fraction of a step
    const at = l => { let s = 0; for (let i = a + l; i < b; i++) s += O[i] * O[i - l]; return s / (b - a - l); };
    const y0 = at(bl - 1), y1 = at(bl), y2 = at(bl + 1), d = (y0 - y2) / (2 * (y0 - 2 * y1 + y2) || 1);
    return bl + (isFinite(d) ? d : 0);
  }
  const tempos = []; for (let a = 0; a + 2000 <= O.length; a += 1000) { const lag = tempo(a, a + 2000); tempos.push([a / 100, Math.round(6000 / lag * 10) / 10]); }
  // strong hits: onset peaks well above their surroundings
  const hits = [];
  for (let i = 5; i < O.length - 5; i++) {
    let m = true; for (let j = i - 8; j <= i + 8; j++) if (j !== i && O[j] > O[i]) { m = false; break; }
    if (!m) continue;
    let avg = 0; for (let j = i - 150; j < i + 150; j++) avg += O[Math.max(0, Math.min(O.length - 1, j))]; avg /= 300;
    if (O[i] > 3 * avg && O[i] > 0.4) hits.push([Math.round(i) / 100, Math.round(O[i] * 100) / 100, Math.round(FL[i] * 100) / 100]);
  }
  return { song: "${song}", duration: N / SR, loud, lowloud, tempos, hits, onset: Array.from(O, v => Math.round(v * 1000) / 1000), high: Array.from(Hh, v => Math.round(v * 1e5) / 1e5), low: Array.from(L, v => Math.round(v * 1e5) / 1e5) };
})()`;
for (const s of songs) {
  const r = await run(JS(s));
  fs.writeFileSync(`beats-${s.replace(".mp3", "")}.json`, JSON.stringify(r));
  console.log(s, r && r.duration, r && r.tempos.map(t => t.join("@")).join(" "));
}
ws.close(); edge.kill();
