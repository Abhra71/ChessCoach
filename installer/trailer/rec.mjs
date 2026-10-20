// Record the trailer's clips: real pages of the test copy in a hidden Edge, scripted clicks, captured as frames.
// node rec.mjs <scenes.json> <outdir> [only-scene]
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const [, , list, outdir, only] = process.argv;
const scenes = JSON.parse(fs.readFileSync(list, "utf8")).filter(s => !only || s.name === only);
const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const BASE = "http://127.0.0.1:8766/";
const edge = spawn(EDGE, ["--headless=new", "--remote-debugging-port=9333", "--window-size=1536,864", "--hide-scrollbars",
  "--enable-unsafe-swiftshader", "--autoplay-policy=no-user-gesture-required", `--user-data-dir=${path.resolve("edgeprof")}`, "about:blank"], { stdio: "ignore" });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let targets;
for (let k = 0; k < 160; k++) { try { targets = await (await fetch("http://127.0.0.1:9333/json")).json(); break; } catch { await sleep(250); } }
const ws = new WebSocket(targets.find(t => t.type === "page").webSocketDebuggerUrl);
await new Promise(r => ws.onopen = r);
let id = 0; const wait = {}, on = {};
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && wait[m.id]) { wait[m.id](m); delete wait[m.id]; } else if (m.method && on[m.method]) on[m.method](m.params); };
const send = (method, params = {}) => new Promise(r => { const n = ++id; wait[n] = r; ws.send(JSON.stringify({ id: n, method, params })); });
const run = async js => { const r = await send("Runtime.evaluate", { expression: js, awaitPromise: true, returnByValue: true }); return r.result && r.result.result && r.result.result.value; };
// the app a little larger than at 1920 wide, so it reads in a video: 1536x864 shown at 1.25 = 1920x1080
await send("Emulation.setDeviceMetricsOverride", { width: 1536, height: 864, deviceScaleFactor: 1.25, mobile: false });
await send("Page.enable");
await send("Page.navigate", { url: BASE + "#/home" }); await sleep(3000);
await run(`(() => { for (const k of ["home","games","practice","daily","plan","level","course","progress"]) localStorage.setItem("kw-intro-"+k,"seen"); localStorage.setItem("kw-voice","off"); localStorage.setItem("kw-film-music","off"); return 1; })()`);
// the opponents' names, hidden: "their opponent" (they never said yes to being in a trailer)
const TIDY = `(async () => {
  const names = (window.__kwNames ||= [...new Set((await (await fetch("/api/games")).json()).map(g => g.opponent).filter(Boolean))]);
  const re = new RegExp("(" + names.map(n => n.replace(/[.*+?^$()|[\\]\\\\-]/g, "\\\\$&")).join("|") + ")", "gi");
  const fix = root => { const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n; (n = w.nextNode());) { re.lastIndex = 0; if (re.test(n.nodeValue)) n.nodeValue = n.nodeValue.replace(re, "Opponent"); } };
  fix(document.body);
  if (!window.__kwTidy) { window.__kwTidy = new MutationObserver(() => fix(document.body)); window.__kwTidy.observe(document.body, { childList: true, subtree: true, characterData: true }); }
  return 1; })()`;

for (const s of scenes) {
  const dir = path.join(outdir, s.name);
  fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
  await send("Page.navigate", { url: BASE + "#/home" }); await sleep(800);
  await send("Page.navigate", { url: BASE + s.hash }); await sleep(s.load || 3000);
  await run(TIDY); await sleep(300);
  if (s.nocoach) await run(`document.head.insertAdjacentHTML("beforeend", "<style>.kw-coach{display:none!important}</style>"); 1`);
  await run(`(() => { if (window.__kwTick) return 1; window.__kwTick = 1; const d = document.createElement("div"); d.style.cssText = "position:fixed;left:0;top:0;width:2px;height:2px;z-index:99999;pointer-events:none"; document.body.appendChild(d); let k = 0; (function f() { d.style.background = (k++ % 2) ? "rgba(0,0,0,.01)" : "rgba(0,0,0,.02)"; requestAnimationFrame(f); })(); return 1; })()`);  // keep frames coming while the page is still
  const frames = [], marks = {}; let t0 = Date.now();
  on["Page.screencastFrame"] = p => {
    const n = frames.length; fs.writeFileSync(path.join(dir, `${n}.jpg`), Buffer.from(p.data, "base64"));
    frames.push((Date.now() - t0) / 1000); send("Page.screencastFrameAck", { sessionId: p.sessionId });
  };
  await send("Page.startScreencast", { format: "jpeg", quality: 88, maxWidth: 1920, maxHeight: 1080 });
  t0 = Date.now();
  for (const [what, a, b] of s.do || []) {
    if (what === "wait") await sleep(a);
    else if (what === "click") await run(`(() => { const e = document.querySelector(${JSON.stringify(a)}); if (e) e.click(); return !!e; })()`);
    else if (what === "js") await run(a);
    else if (what === "type") {  // letter by letter, like a person
      for (let k = 1; k <= b.length; k++) { await run(`(() => { const e = document.querySelector(${JSON.stringify(a)}); e.value = ${JSON.stringify(b)}.slice(0, ${k}); e.dispatchEvent(new Event("input", {bubbles:true})); return 1; })()`); await sleep(55); }
    } else if (what === "scroll") {  // smooth, to y over b ms
      const steps = Math.round(b / 33);
      const from = await run(`(document.scrollingElement || document.body).scrollTop`);
      for (let k = 1; k <= steps; k++) { const e = k / steps, y = from + (a - from) * (e < .5 ? 2 * e * e : 1 - Math.pow(-2 * e + 2, 2) / 2); await run(`window.scrollTo(0, ${y}); 1`); await sleep(33); }
    } else if (what === "mark") {  // where something is on screen, now: for the trailer's zoom
      const r = await run(`(() => { const e = (${b}); if (!e) return null; const r = e.getBoundingClientRect(); return [r.left, r.top, r.width, r.height].map(v => Math.round(v * 1.25)); })()`);
      (marks[a] ||= []).push({ t: (Date.now() - t0) / 1000, r });
    } else if (what === "key") await run(`dispatchEvent(new KeyboardEvent("keydown", {key: ${JSON.stringify(a)}})); 1`);
  }
  await send("Page.stopScreencast");
  fs.writeFileSync(path.join(dir, "frames.json"), JSON.stringify({ length: (Date.now() - t0) / 1000, frames, marks }));
  console.log(s.name, frames.length, "frames", ((Date.now() - t0) / 1000).toFixed(1), "s");
}
ws.close(); edge.kill();
