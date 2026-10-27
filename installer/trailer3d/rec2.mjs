// Trailer 2's moving clips, take two: the real app in a hidden Edge, used by a visible mouse pointer that glides,
// hovers and clicks, captured with Chrome's live screencast (every repaint, about 25-30 frames a second) at 1920x1080.
// node rec2.mjs <scenes.json> <outdir> [only-scene]      (the test copy must be running on port 8766)
// Steps: ["wait", ms] | ["js", code] | ["move", selector-or-[x,y], ms] | ["click"] | ["clickat", selector, ms]
//        | ["scroll", y, ms] | ["play", times, gap-ms] (press ▶ again and again) | ["waitfor", selector, ms]
import { spawn } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const [, , list, outdir, only] = process.argv;
const scenes = JSON.parse(fs.readFileSync(list, "utf8")).filter(s => !only || s.name === only);
const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const BASE = "http://127.0.0.1:8766/";
const edge = spawn(EDGE, ["--headless=new", "--remote-debugging-port=9335", "--window-size=1536,864", "--force-device-scale-factor=1.25", "--hide-scrollbars",
  "--autoplay-policy=no-user-gesture-required", `--user-data-dir=${path.resolve(process.env.TEMP, "kw-rec2")}`, "about:blank"], { stdio: "ignore" });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let targets;
for (let k = 0; k < 160; k++) { try { targets = await (await fetch("http://127.0.0.1:9335/json")).json(); break; } catch { await sleep(250); } }
const ws = new WebSocket(targets.find(t => t.type === "page").webSocketDebuggerUrl);
await new Promise(r => ws.onopen = r);
let id = 0; const wait = {}, on = {};
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && wait[m.id]) { wait[m.id](m); delete wait[m.id]; } else if (m.method && on[m.method]) on[m.method](m.params); };
const send = (method, params = {}) => new Promise(r => { const n = ++id; wait[n] = r; ws.send(JSON.stringify({ id: n, method, params })); });
const run = async js => { const r = await send("Runtime.evaluate", { expression: js, awaitPromise: true, returnByValue: true }); return r.result && r.result.result && r.result.result.value; };
await send("Emulation.setDeviceMetricsOverride", { width: 1536, height: 864, deviceScaleFactor: 1.25, mobile: false });
await send("Page.enable");
await send("Page.navigate", { url: BASE + "#/home" }); await sleep(3000);
await run(`(() => { for (const k of ["home","games","practice","daily","plan","level","course","progress","train","guess","blindfold"]) localStorage.setItem("kw-intro-"+k,"seen"); localStorage.setItem("kw-voice","off"); return 1; })()`);
const TIDY = `(async () => {
  const names = (window.__kwNames ||= [...new Set((await (await fetch("/api/games")).json()).map(g => g.opponent).filter(Boolean))]);
  const re = new RegExp("(" + names.map(n => n.replace(/[.*+?^$()|[\\]\\\\-]/g, "\\\\$&")).join("|") + ")", "gi");
  const fix = root => { const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    for (let n; (n = w.nextNode());) { re.lastIndex = 0; if (re.test(n.nodeValue)) n.nodeValue = n.nodeValue.replace(re, "Opponent"); } };
  fix(document.body);
  if (!window.__kwTidy) { window.__kwTidy = new MutationObserver(() => fix(document.body)); window.__kwTidy.observe(document.body, { childList: true, subtree: true, characterData: true }); }
  return 1; })()`;
// the pointer: a white arrow with a soft shadow that glides (CSS), and a ring on each click
const POINTER = `(() => { if (document.getElementById("kwptr")) return 1;
  const p = document.createElement("div"); p.id = "kwptr";
  p.innerHTML = '<svg width="26" height="34" viewBox="0 0 26 34"><path d="M2 2 L2 26 L8.5 20 L13 31 L17.5 29 L13 18.5 L22 18.5 Z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>';
  p.style.cssText = "position:fixed;left:0;top:0;z-index:2147483647;pointer-events:none;filter:drop-shadow(0 3px 5px rgba(0,0,0,.55));transform:translate(1100px,700px);transition:transform 700ms cubic-bezier(.45,.05,.25,1)";
  document.documentElement.appendChild(p); window.__kwAt = [1100, 700];
  const st = document.createElement("style"); st.textContent = "@keyframes kwring{from{transform:translate(-50%,-50%) scale(.3);opacity:.9}to{transform:translate(-50%,-50%) scale(1.6);opacity:0}}";
  document.head.appendChild(st); return 1; })()`;
// where a target is on screen: a CSS selector, "js:<expression giving an element>", or [x, y]
const where = async t => Array.isArray(t) ? t : await run(`(() => { const e = ${t.startsWith("js:") ? t.slice(3) : `document.querySelector(${JSON.stringify(t)})`};
  if (!e) return null; const r = e.getBoundingClientRect(); return [r.left + r.width * 0.5, r.top + r.height * 0.52]; })()`);
// the pointer glides there (drawn), and the browser gets real mouse moves along the way (so hovers light up)
async function moveTo(t, ms = 700) {
  const to = await where(t); if (!to) { console.log("  no target", t); return false; }
  await run(POINTER);
  const from = (await run("window.__kwAt")) || [1100, 700];
  await run(`(() => { const p = document.getElementById("kwptr"); p.style.transition = "transform ${ms}ms cubic-bezier(.45,.05,.25,1)";
    p.style.transform = "translate(${to[0]}px,${to[1]}px)"; window.__kwAt = [${to[0]}, ${to[1]}]; return 1; })()`);
  const steps = Math.max(4, Math.round(ms / 45));
  for (let k = 1; k <= steps; k++) {
    const u = k / steps, e = u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
    await send("Input.dispatchMouseEvent", { type: "mouseMoved", x: from[0] + (to[0] - from[0]) * e, y: from[1] + (to[1] - from[1]) * e });
    await sleep(ms / steps);
  }
  return true;
}
async function click() {
  const [x, y] = (await run("window.__kwAt")) || [0, 0];
  await run(`(() => { const r = document.createElement("div"); r.style.cssText = "position:fixed;left:${x}px;top:${y}px;width:46px;height:46px;border-radius:50%;border:3px solid rgba(255,255,255,.85);z-index:2147483646;pointer-events:none;animation:kwring 520ms ease-out forwards";
    document.documentElement.appendChild(r); setTimeout(() => r.remove(), 600); return 1; })()`);
  await send("Input.dispatchMouseEvent", { type: "mousePressed", x, y, button: "left", clickCount: 1 });
  await sleep(70);
  await send("Input.dispatchMouseEvent", { type: "mouseReleased", x, y, button: "left", clickCount: 1 });
}

for (const s of scenes) {
  const dir = path.join(outdir, s.name);
  fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
  await send("Page.navigate", { url: BASE + "#/home" }); await sleep(800);
  await send("Page.navigate", { url: BASE + s.hash }); await sleep(s.load || 3000);
  if (s.pre) { await run(s.pre); await sleep(s.preWait || 2500); }  // e.g. forget a set already answered, then load again
  await run(TIDY); await run(POINTER); await sleep(200);
  if (!s.coach) await run(`document.head.insertAdjacentHTML("beforeend", "<style>.kw-coach{display:none!important}</style>"); 1`);
  const frames = []; let t0 = null, n = 0;
  on["Page.screencastFrame"] = p => {
    const ts = p.metadata.timestamp; if (t0 === null) t0 = ts;
    fs.writeFileSync(path.join(dir, `${n}.jpg`), Buffer.from(p.data, "base64"));
    frames.push(ts - t0); n++;
    send("Page.screencastFrameAck", { sessionId: p.sessionId });
  };
  await send("Page.startScreencast", { format: "jpeg", quality: 82, maxWidth: 1920, maxHeight: 1080, everyNthFrame: 1 });
  const start = Date.now();
  for (const [what, a, b] of s.do || []) {
    if (what === "wait") await sleep(a);
    else if (what === "js") await run(a);
    else if (what === "log") console.log("  log:", await run(a));
    else if (what === "move") { await moveTo(a, b || 700); await sleep(80); }
    else if (what === "click") { await click(); await sleep(380); }
    else if (what === "clickat") {
      if (await moveTo(a, b || 700)) {
        await sleep(120);
        const now = await where(a), at = await run("window.__kwAt");  // the page may have moved under the pointer: aim again
        if (now && at && Math.hypot(now[0] - at[0], now[1] - at[1]) > 4) { await moveTo(a, 250); await sleep(60); }
        await click();
      }
      await sleep(380);
    }
    else if (what === "waitfor") { for (let t = 0; t < (b || 4000) && !(await where(a)); t += 100) await sleep(100); }
    else if (what === "scroll") {
      const steps = Math.round(b / 33), from = await run(`(document.scrollingElement || document.body).scrollTop`);
      for (let k = 1; k <= steps; k++) { const e = k / steps, y = from + (a - from) * (e < .5 ? 2 * e * e : 1 - Math.pow(-2 * e + 2, 2) / 2); await run(`window.scrollTo(0, ${y}); 1`); await sleep(33); }
    } else if (what === "play") { for (let k = 0; k < a; k++) { await run(`document.querySelector("[data-go='1']").click(); 1`); await sleep(b); } }
  }
  await send("Page.stopScreencast"); await sleep(300); on["Page.screencastFrame"] = null;
  fs.writeFileSync(path.join(dir, "frames.json"), JSON.stringify({ length: (Date.now() - start) / 1000, frames }));
  console.log(s.name, frames.length, "frames", ((Date.now() - start) / 1000).toFixed(1), "s", (frames.length / ((Date.now() - start) / 1000)).toFixed(1), "fps");
}
ws.close(); edge.kill();
