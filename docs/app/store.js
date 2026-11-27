// Saved on the phone: a tiny key -> value store in IndexedDB (the browser's own database, with far more room
// than localStorage, and it doesn't slow the page while saving). Falls back to localStorage if IndexedDB is
// missing or blocked (some private windows). Every call is safe: on any problem it just returns null.
const Store = (() => {
  let opening = null;
  function db() {
    if (!opening) opening = new Promise((ok, bad) => {
      if (!self.indexedDB) return bad(new Error("no IndexedDB"));
      const r = indexedDB.open("knightwise", 1);
      r.onupgradeneeded = () => r.result.createObjectStore("kv");
      r.onsuccess = () => ok(r.result);
      r.onerror = () => bad(r.error);
    });
    return opening;
  }
  function ask(mode, act) {
    return db().then(d => new Promise((ok, bad) => {
      const q = act(d.transaction("kv", mode).objectStore("kv"));
      q.onsuccess = () => ok(q.result === undefined ? null : q.result);
      q.onerror = () => bad(q.error);
    }));
  }
  async function get(key) {
    try { return await ask("readonly", s => s.get(key)); }
    catch { try { return JSON.parse(localStorage.getItem(key) || "null"); } catch { return null; } }
  }
  async function set(key, value) {
    try { await ask("readwrite", s => s.put(value, key)); }
    catch { try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* full: keep going without saving */ } }
  }
  // ask the browser not to clear our data when the phone runs low on space (it may say no; that's fine)
  if (navigator.storage && navigator.storage.persist) navigator.storage.persist().catch(() => {});
  return { get, set };
})();
