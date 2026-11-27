"""Bad input from a page or a damaged file never crashes the coach (27 Nov bug hunt, after 1.2)."""
import http.client
import json
import threading

import pytest

from coach import fixes, service


def test_whole_numbers_from_anything():
    assert [service.whole(v) for v in ("3", 4, 4.7, "2.0")] == [3, 4, 4, 2]
    assert [service.whole(v) for v in ("abc", None, [], {}, "nan", "inf", float("inf"))] == [0] * 7
    assert service.whole("x", default=-1) == -1


@pytest.fixture
def server(tmp_path, monkeypatch):
    monkeypatch.setattr(service, "DATA", tmp_path)
    monkeypatch.setattr(service, "note_in_logbook", lambda *a, **k: None)
    monkeypatch.setattr(service.updater, "used", lambda path: None)
    srv = service.Server(("127.0.0.1", 0), service.Handler)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    monkeypatch.setattr(service, "PORT", port)  # the Host check uses the real port

    def post(path, body, ctype, length=None):
        c = http.client.HTTPConnection("127.0.0.1", port, timeout=10)
        c.putrequest("POST", path, skip_accept_encoding=True)
        c.putheader("Content-Type", ctype)
        c.putheader("Content-Length", str(len(body)) if length is None else length)
        c.endheaders()
        c.send(body)
        r = c.getresponse()
        out = r.status, r.read()
        c.close()
        return out
    yield post
    srv.shutdown()
    srv.server_close()


def test_feedback_with_a_word_for_helped_is_saved_not_crashed(server, tmp_path):
    body = json.dumps({"doing": "review", "wrong": "nothing", "page": "home", "helped": "a lot"}).encode()
    assert server("/api/feedback", body, "application/json")[0] == 200
    saved = json.loads((tmp_path / "feedback.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert saved["helped"] == 0 and saved["wrong"] == "nothing"


def test_listening_with_a_broken_size_says_so(server):
    status, _ = server("/api/listen", b"", "application/octet-stream", length="abc")
    assert status == 400  # was: the coach's request handler crashed and the page got no answer


def test_listening_on_this_pc_with_an_odd_byte(server, monkeypatch):
    from coach import ai, hearing

    def no_key(pcm, rate):
        raise ai.NoKey("no key")
    heard = {}
    monkeypatch.setattr(ai, "hear", no_key)
    monkeypatch.setattr(hearing, "available", lambda: True)
    monkeypatch.setattr(hearing, "transcribe", lambda samples: heard.setdefault("n", len(samples)) and "hello")
    loud = (b"\x00\x40" * hearing.RATE) + b"\x01"  # a second of sound, plus one stray byte
    status, body = server("/api/listen", loud, "application/octet-stream")
    assert status == 200 and json.loads(body)["text"] == "hello" and heard["n"] == hearing.RATE


def test_a_saved_fix_file_that_is_not_an_object(tmp_path, monkeypatch):
    monkeypatch.setattr(fixes, "FILE", tmp_path / "fixes.json")
    (tmp_path / "fixes.json").write_text("[1, 2, 3]")
    assert fixes.refresh(fetch=lambda: {"off": ["warmup"]})["off"] == ["warmup"]
    (tmp_path / "fixes.json").write_text(json.dumps({"at": "yesterday", "fixes": {}}))
    assert fixes.refresh(fetch=lambda: {"off": ["tags"]})["off"] == ["tags"]
