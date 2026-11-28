// The service worker: keeps the app's own files on the phone so it opens offline, like an installed app.
// Games are kept by the page itself (IndexedDB, store.js); requests to chess.com and Lichess are never touched here.
// Change VERSION whenever any file below changes, so phones fetch the new copy.
const VERSION = "kw-mobile-0.3.3";
const FILES = ["./", "index.html", "app.css", "app.js", "board.js", "pieces.js", "rules.js", "games.js", "store.js",
  "analysis/analysis-board.js", "analysis/analysis-board.css", "vendor/chessground/chessground.min.js",
  "vendor/chessground/chessground.base.css", "vendor/chessground/chessground.cburnett.css",
  "manifest.webmanifest", "icons/icon-64.png", "icons/icon-192.png"];   // the big install icons are fetched only when installing

self.addEventListener("install", e => {
  e.waitUntil(caches.open(VERSION).then(c => c.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {   // throw away older versions
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener("fetch", e => {
  const url = new URL(e.request.url);
  if (e.request.method !== "GET" || url.origin !== location.origin) return;   // chess.com / Lichess: straight to the network
  // the app's own files: the saved copy at once, and a fresh copy fetched for next time
  e.respondWith(caches.open(VERSION).then(async c => {
    const hit = await c.match(e.request, { ignoreSearch: true });
    const fresh = fetch(e.request).then(r => { if (r.ok) c.put(e.request, r.clone()); return r; }).catch(() => hit);
    return hit || fresh;
  }));
});
