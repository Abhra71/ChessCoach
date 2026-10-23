"""Attacks on Knightwise's local server (127.0.0.1:8765): what another website, a bad program or garbage could do."""
import concurrent.futures
import http.client
import json
import socket
import time

import os, sys
H, P = "127.0.0.1", int(os.environ.get("KW_PORT", "8765"))
results = []


def req(method, path, body=None, headers=None, timeout=15):
    c = http.client.HTTPConnection(H, P, timeout=timeout)
    try:
        hs = {"Host": f"{H}:{P}", **(headers or {})}
        c.putrequest(method, path, skip_host=True, skip_accept_encoding=True)
        for k, v in hs.items():
            c.putheader(k, v)
        data = body if isinstance(body, (bytes, type(None))) else body.encode()
        if data is not None and "Content-Length" not in hs:
            c.putheader("Content-Length", str(len(data)))
        c.endheaders(data)
        r = c.getresponse()
        return r.status, r.read()[:300], dict(r.getheaders())
    except Exception as e:
        return None, repr(e)[:200].encode(), {}
    finally:
        c.close()


def alive():
    s, _, _ = req("GET", "/api/status")
    return s == 200


def check(name, ok, detail=""):
    results.append((("PASS" if ok else "FAIL"), name, detail))
    print(("PASS" if ok else "FAIL"), name, detail, "| alive:", alive(), flush=True)


J = {"Content-Type": "application/json"}
# 1. another website tries to command Knightwise
s, b, h = req("POST", "/api/show", json.dumps({"route": "settings"}), {**J, "Origin": "https://evil.example"})
check("foreign site can't send commands (POST /api/show)", s == 403, s)
s, b, h = req("GET", "/api/settings", None, {"Origin": "https://evil.example"})
check("foreign site can't read settings", s == 403 and "Access-Control-Allow-Origin" not in h, s)
s, b, h = req("POST", "/api/plan/mark", json.dumps({"id": "x", "done": True}), {**J, "Origin": "null"})
check("sandboxed page (Origin: null) refused", s == 403, s)
s, b, h = req("POST", "/api/show", json.dumps({"route": "home"}), {**J, "Origin": "https://www.chess.com"})
check("chess.com's own page can't command it directly", s == 403, s)
# 2. DNS rebinding: a site pointing its own name at this computer
s, b, h = req("GET", "/api/settings", None, {"Host": "evil.example:8765"})
check("foreign Host name refused (DNS rebinding)", s == 403, s)
# 3. a form post (no JSON) from anywhere
s, b, h = req("POST", "/api/show", "route=home", {"Content-Type": "application/x-www-form-urlencoded"})
check("plain form posts refused", s == 403, s)
# 4. files outside the app
for p in ["/ui/../coach/settings.py", "/ui/..%2f..%2fcoach%2fsettings.py", "/ui/%2e%2e/%2e%2e/data/settings.json",
          "/ui/....//....//coach/service.py", "/ui/..\\..\\coach\\settings.py", "/ui/C:/Windows/win.ini"]:
    s, b, h = req("GET", p)
    check(f"no file outside the app: {p}", s in (403, 404), s)
# 5. garbage
s, b, h = req("POST", "/api/plan/mark", b"{not json", J)
check("broken JSON answered, not crashed", s == 400 and alive(), s)
s, b, h = req("POST", "/api/plan/mark", json.dumps([1, 2, 3]), J)
check("JSON of the wrong shape: no crash", s is not None and alive(), s)
s, b, h = req("POST", "/api/plan/mark", json.dumps({"id": {"x": 1}, "done": "yes"}), J)
check("fields of the wrong type: no crash", s is not None and alive(), s)
big = b'{"id": "' + b"A" * (20 * 1024 * 1024) + b'"}'
t = time.time()
s, b, h = req("POST", "/api/plan/mark", big, J, timeout=60)
check("20 MB body: refused or cut, server alive", alive(), f"{s} in {time.time() - t:.1f}s")
s, b, h = req("POST", "/api/plan/progress", big, J, timeout=60)
check("20 MB body on the bigger endpoint: server alive", alive(), s)
s, b, h = req("POST", "/api/plan/mark", b"{}", {**J, "Content-Length": "abc"})
check("Content-Length not a number: no crash", alive(), s)
# a Content-Length that lies: says 100, sends 2 bytes, then waits
for _ in range(20):  # the server may still be busy throwing away the 20 MB: wait for it, and say how long
    if alive():
        break
    time.sleep(0.5)
check("back to normal after the 20 MB bodies", alive())
sock = socket.create_connection((H, P), timeout=5)
sock.sendall(b"POST /api/plan/mark HTTP/1.1\r\nHost: 127.0.0.1:8765\r\nContent-Type: application/json\r\nContent-Length: 100\r\n\r\n{}")
time.sleep(1)
check("a client that lies about its length doesn't block others", alive())
sock.close()
s, b, h = req("POST", "/api/show", json.dumps({"route": "home');alert(1);//"}), J)
check("route injection into the window refused or harmless", s in (200, 400, 403) and alive(), s)
s, b, h = req("GET", "/api/" + "x" * 60000)
check("very long address: no crash", alive(), s)
# 6. a flood
t = time.time()
with concurrent.futures.ThreadPoolExecutor(64) as ex:
    codes = list(ex.map(lambda _: req("GET", "/api/status", timeout=30)[0], range(600)))
check("600 requests at once: all answered, still alive", alive() and codes.count(200) >= 590,
      f"{codes.count(200)}/600 ok in {time.time() - t:.1f}s")
# 7. what any program on this PC can read without an Origin (local apps, scripts)
s, b, h = req("GET", "/api/settings")
txt = b.decode("utf-8", "ignore")
check("settings never contain a whole key", not any(len(w) > 30 and w.isalnum() for w in txt.replace('"', " ").split()), txt[:160])
# 8. any extension (not only Knightwise's) may talk to it
s, b, h = req("GET", "/api/settings", None, {"Origin": "chrome-extension://abcdefghijklmnopabcdefghijklmnop"})
check("another extension is treated like Knightwise's (info)", True, f"status {s}: any extension is allowed")

w = max(len(r[1]) for r in results)
for r in results:
    print(f"{r[0]}  {r[1]:<{w}}  {r[2]}")
print(f"\n{sum(r[0] == 'PASS' for r in results)} of {len(results)} pass")
