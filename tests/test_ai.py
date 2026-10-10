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
    assert ai.complete("s", "p") == ("Your bishop was left alone.", "groq")
    assert calls == ["gemini", "groq"]


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
    assert first == again == {"text": "c3 took away the pawn that guarded your bishop.", "provider": "gemini"}
    assert len(seen) == 1                         # second time came from the cache
    assert "never invent" in seen[0][0]           # the rules forbid made-up moves
    assert "leaves loose: bishop on d3" in seen[0][1] and '"fen"' not in seen[0][1]
