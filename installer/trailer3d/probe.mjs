// List what can be clicked on a page of the test copy (port 8766), to script the trailer's moving clips.
// node probe.mjs "#/practice" ["js to run first"]
import { spawn } from "node:child_process";
import path from "node:path";

const [, , hash = "#/home", pre = ""] = process.argv;
const EDGE = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe";
const edge = spawn(EDGE, ["--headless=new", "--remote-debugging-port=9334", "--window-size=1536,864",
  `--user-data-dir=${path.resolve(process.env.TEMP, "kw-probe")}`, "about:blank"], { stdio: "ignore" });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let targets;
for (let k = 0; k < 160; k++) { try { targets = await (await fetch("http://127.0.0.1:9334/json")).json(); break; } catch { await sleep(250); } }
const ws = new WebSocket(targets.find(t => t.type === "page").webSocketDebuggerUrl);
await new Promise(r => ws.onopen = r);
let id = 0; const wait = {};
ws.onmessage = e => { const m = JSON.parse(e.data); if (m.id && wait[m.id]) { wait[m.id](m); delete wait[m.id]; } };
const send = (method, params = {}) => new Promise(r => { const n = ++id; wait[n] = r; ws.send(JSON.stringify({ id: n, method, params })); });
const run = async js => (await send("Runtime.evaluate", { expression: js, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send("Page.navigate", { url: "http://127.0.0.1:8766/" + hash }); await sleep(5000);
if (pre) { console.log("pre:", await run(pre)); await sleep(2500); }
console.log(await run(`[...document.querySelectorAll('button, a[href]')].filter(e => e.offsetParent || e.tagName==='rect')
  .slice(0, 80).map(e => (e.id ? '#' + e.id + ' ' : '') + e.tagName.toLowerCase() + (e.getAttribute('href') ? ' href=' + e.getAttribute('href') : '')
  + [...e.attributes].filter(a => a.name.startsWith('data-')).map(a => ' ' + a.name + '=' + a.value).join('') + ' :: ' + (e.textContent || '').trim().slice(0, 40)).join('\\n')`));
ws.close(); edge.kill();
