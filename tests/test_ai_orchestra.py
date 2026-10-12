import io
import urllib.error

import pytest

from coach import ai, settings


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    keys = {"slot1": "k1", "slot2": "k2"}  # Groq first, Gemini second (the defaults)
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    monkeypatch.setattr(settings, "get_key", lambda slot: keys.get(slot))
    monkeypatch.setattr(ai, "USAGE", tmp_path / "ai-usage.json")
    monkeypatch.setattr(ai, "_REST", {})
    return keys


def busy(code=429):
    return urllib.error.HTTPError("u", code, "busy", {}, io.BytesIO(b""))


def test_busy_main_model_falls_back_to_the_small_one(monkeypatch):
    seen = []

    def once(provider, key, system, prompt, max_tokens, model=None):
        seen.append((provider, model))
        if model is None:
            raise busy()
        return "Short answer."
    monkeypatch.setattr(ai, "_call_once", once)
    assert ai.complete("s", "p") == ("Short answer.", "groq")
    assert seen == [("groq", None), ("groq", "llama-3.1-8b-instant")]
    assert not ai.resting("groq")


def test_a_busy_provider_rests_and_the_next_key_answers_without_waiting(monkeypatch):
    seen = []

    def once(provider, key, system, prompt, max_tokens, model=None):
        seen.append(provider)
        if provider == "groq":
            raise busy(503)
        return "From Gemini."
    monkeypatch.setattr(ai, "_call_once", once)
    assert ai.complete("s", "p") == ("From Gemini.", "gemini")
    assert ai.resting("groq") and seen == ["groq", "groq", "gemini"]
    seen.clear()
    assert ai.complete("s", "p") == ("From Gemini.", "gemini")
    assert seen == ["gemini"]  # Groq is resting: not asked again for 10 minutes
    assert ai.usage()["groq"]["resting_minutes"] == 10


def test_a_wrong_key_is_not_a_rest(monkeypatch):
    def once(provider, key, system, prompt, max_tokens, model=None):
        raise busy(401)
    monkeypatch.setattr(ai, "_call_once", once)
    with pytest.raises(RuntimeError):
        ai.complete("s", "p")
    assert not ai.resting("groq") and not ai.resting("gemini")


def test_usage_is_counted_per_provider_per_day():
    from datetime import date
    ai._count("groq", 1200, today=date.today())
    ai._count("groq", 300, today=date.today())
    u = ai.usage()["groq"]
    assert (u["requests"], u["tokens"]) == (2, 1500)
