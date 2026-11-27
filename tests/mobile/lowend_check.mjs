// Cheap-phone check for the phone app (docs/app): a headless Edge with its own throwaway profile, DevTools CPU
// throttling (6x slower), a slow network, a 375 px wide phone screen and an Android Chrome identity
// (Lichess answers "not found" to browsers that call themselves headless). Prints timings, size and memory.
//
// 1. Serve the site:   python -m http.server 8771 --bind 127.0.0.1 --directory docs
// 2. Run:              node tests/mobile/lowend_check.mjs "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe" <empty temp folder> chesscom <username> slow3g [2]
//    (site: chesscom or lichess; network: slow3g or slow4g; the last number pretends the phone has that many GB of memory)
// Uses the real chess.com / Lichess APIs, so it needs the internet. Not part of pytest.
// Cheap-phone test: headless Edge (own throwaway profile), DevTools CPU throttling + slow network, 375 px wide.
import { spawn } from "node:child_process";
const [,, edge, profile, site, user, net] = process.argv;
const NETS = { slow3g: { latency: 400, downloadThroughput: 400 * 1000 / 8, uploadThroughput: 400 * 1000 / 8 },
               slow4g: { latency: 150, downloadThroughput: 1600 * 1000 / 8, uploadThroughput: 750 * 1000 / 8 } };
const out0 = {}; const CPU = 6, URL0 = "http://localhost:8771/app/";
const proc = spawn(edge, ["--headless=new", "--remote-debugging-port=9333", `--user-data-dir=${profile}`, "--no-first-run", "about:blank"], { stdio: "ignore" });
const wait = ms => new Promise(r => setTimeout(r, ms));
let list; for (let i = 0; i < 40; i++) { try { list = await (await fetch("http://127.0.0.1:9333/json/list")).json(); break; } catch { await wait(250); } }
const ws = new WebSocket(list.find(t => t.type === "page").webSocketDebuggerUrl);
await new Promise(r => ws.onopen = r);
let id = 0; const waiting = {};
ws.onmessage = m => { const d = JSON.parse(m.data); if (d.id && waiting[d.id]) { waiting[d.id](d); delete waiting[d.id]; } };
const cdp = (method, params = {}) => new Promise(r => { const i = ++id; waiting[i] = r; ws.send(JSON.stringify({ id: i, method, params })); });
const js = async expr => { const r = await cdp("Runtime.evaluate", { expression: expr, awaitPromise: true, returnByValue: true }); if (r.result.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails)); return r.result.result.value; };
const until = async (expr, ms = 120000) => { const t = Date.now(); while (Date.now() - t < ms) { if (await js(expr)) return Date.now() - t; await wait(50); } return -1; };
const heap = async () => { const m = (await cdp("Performance.getMetrics")).result.metrics; return (m.find(x => x.name === "JSHeapUsedSize").value / 1e6).toFixed(1) + " MB"; };

await cdp("Network.enable"); await cdp("Performance.enable"); await cdp("Page.enable");
await cdp("Network.setCacheDisabled", { cacheDisabled: true });
await cdp("Network.emulateNetworkConditions", { offline: false, ...NETS[net] });
await cdp("Emulation.setCPUThrottlingRate", { rate: CPU });
await cdp("Emulation.setDeviceMetricsOverride", { width: 375, height: 812, deviceScaleFactor: 2, mobile: true });
await cdp("Emulation.setUserAgentOverride", { userAgent: "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36" });
if (process.argv[7]) { await cdp("Page.addScriptToEvaluateOnNewDocument", { source: `Object.defineProperty(navigator, "deviceMemory", { get: () => ${process.argv[7]} }); Object.defineProperty(navigator, "hardwareConcurrency", { get: () => 4 });` }); out0.memory = process.argv[7] + " GB, 4 cores"; }
const out = out0; Object.assign(out, { setup: `CPU ${CPU}x slower, ${net} (${NETS[net].latency} ms, ${NETS[net].downloadThroughput * 8 / 1000} kbit/s down), 375x812`, site, user });

let t = Date.now(); await cdp("Page.navigate", { url: URL0 });
await until(`document.querySelector('#user') !== null`);
out.firstScreen_ms = Date.now() - t;
out.firstLoad = await js(`(() => { const e = performance.getEntriesByType('resource'), n = performance.getEntriesByType('navigation')[0];
  const fcp = performance.getEntriesByName('first-contentful-paint')[0];
  return { files: e.length + 1, KB: Math.round((e.reduce((s, x) => s + x.transferSize, 0) + n.transferSize) / 1024), fcp_ms: fcp && Math.round(fcp.startTime) }; })()`);

await js(`document.querySelector('[data-site=${site === "lichess" ? "lichess" : "chesscom"}]').click(); document.querySelector('#user').value = ${JSON.stringify(user)}; document.querySelector('#who').requestSubmit(); true`);
t = Date.now();
out.firstGamesShown_ms = await until(`document.querySelectorAll('.game').length > 0`);
out.gamesAtFirstPaint = await js(`document.querySelectorAll('.game').length`);
out.allGames_ms = await until(`/Updated/.test(document.querySelector('.sub')?.textContent || '')`);
out.games = await js(`document.querySelectorAll('.game').length`);
out.screen = await js(`location.hash + ' | ' + document.querySelector('#view').innerText.slice(0, 300)`);

out.heapAfterList = await heap();

t = Date.now(); await js(`location.hash = document.querySelector('.game').getAttribute('href'); true`);
out.openGame_ms = await until(`!!document.querySelector('#board svg')`);
out.plies = await js(`document.querySelectorAll('#moves button').length`);
out.stepTap_ms = await js(`(async () => { const next = document.querySelector('[data-go=next]'), back = document.querySelector('[data-go=back]');
  document.querySelector('[data-go=start]').click(); await new Promise(r => requestAnimationFrame(() => setTimeout(r)));
  const times = []; for (let i = 0; i < 20; i++) { const t0 = performance.now(); next.click();
    await new Promise(r => requestAnimationFrame(() => setTimeout(r))); times.push(performance.now() - t0); }
  times.sort((a, b) => a - b); return { median: Math.round(times[10]), worst: Math.round(times[19]) }; })()`);
out.heapInGame = await heap();

await until(`navigator.serviceWorker.controller !== null || (navigator.serviceWorker.ready.then(() => true), false)`, 20000);
await js(`navigator.serviceWorker.ready.then(() => true)`);
await cdp("Network.setCacheDisabled", { cacheDisabled: false });
await cdp("Network.emulateNetworkConditions", { offline: true, latency: 0, downloadThroughput: -1, uploadThroughput: -1 });
await cdp("Page.navigate", { url: "about:blank" }); await wait(500);
t = Date.now(); await cdp("Page.navigate", { url: URL0 + "#/games" });
out.offlineReopen_ms = await until(`document.querySelectorAll('.game').length > 0`, 30000);
out.offlineNote = await js(`document.querySelector('.sub')?.textContent`);
console.log(JSON.stringify(out, null, 1));
ws.close(); proc.kill();
