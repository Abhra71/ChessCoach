import pytest

from coach import ai, settings


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    keys = {}
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    monkeypatch.setattr(settings, "get_key", lambda slot: keys.get(slot))
    monkeypatch.setattr(ai, "CACHE", tmp_path / "explanations.json")
    return keys


def test_no_key_says_so():
    with pytest.raises(ai.NoKey):
        ai.complete("system", "prompt")


def test_second_key_takes_over_when_first_fails(isolated, monkeypatch):
    isolated.update(slot1="k1", slot2="k2")
    calls = []

    def fake(provider, key, system, prompt, max_tokens):
        calls.append(provider)
        if key == "k1":
            raise RuntimeError("quota")
        return "Your bishop was left alone."
    monkeypatch.setattr(ai, "_call", fake)
    assert ai.complete("s", "p") == ("Your bishop was left alone.", "gemini")
    assert calls == ["groq", "gemini"]  # Groq first, Gemini takes over


def test_explanation_is_grounded_and_cached(isolated, monkeypatch):
    isolated.update(slot1="k1")
    seen = []

    def fake(provider, key, system, prompt, max_tokens):
        seen.append((system, prompt))
        return "c3 took away the pawn that guarded your bishop."
    monkeypatch.setattr(ai, "_call", fake)
    facts = {"fen": "x", "played": "c3", "best": "Nf3", "played_does": "pawn c2 to c3 (leaves loose: bishop on d3)"}
    first = ai.explain(facts, 300)
    again = ai.explain(facts, 300)
    assert first == again == {"text": "c3 took away the pawn that guarded your bishop.", "provider": "groq"}
    assert len(seen) == 1                         # second time came from the cache
    assert "never invent" in seen[0][0]           # the rules forbid made-up moves
    assert "leaves loose: bishop on d3" in seen[0][1] and '"fen"' not in seen[0][1]


def test_retired_model_is_picked_again(monkeypatch):
    import io
    import urllib.error
    from coach import ai
    ai._MODELS["gemini"] = "gemini-3.5-flash"
    seen = []

    def once(provider, key, system, prompt, max_tokens):
        seen.append(ai._MODELS.get(provider))
        if ai._MODELS.get(provider) == "gemini-3.5-flash":
            raise urllib.error.HTTPError("u", 404, "model retired", {}, io.BytesIO(b""))
        ai._MODELS[provider] = "gemini-flash-latest"
        return "ok"

    monkeypatch.setattr(ai, "_call_once", once)
    assert ai._call("gemini", "k", "s", "p", 10) == "ok"
    assert seen == ["gemini-3.5-flash", None] and ai._MODELS["gemini"] == "gemini-flash-latest"
    ai._MODELS.clear()


def test_hearing_goes_to_the_keys_that_can_hear_then_the_next(monkeypatch):
    from coach import ai, settings
    monkeypatch.setattr(settings, "load", lambda: {"slot1": {"provider": "groq"}, "slot2": {"provider": "gemini"}})
    monkeypatch.setattr(settings, "get_key", lambda slot: "k-" + slot)
    monkeypatch.setattr(ai, "_REST", {})
    calls = []

    def busy(key, audio):
        calls.append("groq")
        import urllib.error
        raise urllib.error.HTTPError("u", 429, "busy", {}, None)

    def gem(key, audio):
        calls.append("gemini")
        assert audio[:4] == b"RIFF"
        return "review my last game"
    text, by = ai.hear(b"\x00\x00" * 16000, hearers={"groq": busy, "gemini": gem})
    assert (text, by, calls) == ("review my last game", "gemini", ["groq", "gemini"])
    assert ai.resting("groq")  # the busy one rests


def test_hearing_without_a_key_that_can_hear(monkeypatch):
    import pytest
    from coach import ai, settings
    monkeypatch.setattr(settings, "load", lambda: {"slot1": {"provider": "anthropic"}, "slot2": {"provider": "openai"}})
    monkeypatch.setattr(settings, "get_key", lambda slot: "k")
    with pytest.raises(ai.NoKey):
        ai.hear(b"\x00\x00" * 16000)
