import pytest

from coach import settings


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    vault = {}
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    monkeypatch.setattr(settings.keyring, "set_password", lambda s, u, p: vault.__setitem__((s, u), p))
    monkeypatch.setattr(settings.keyring, "get_password", lambda s, u: vault.get((s, u)))
    monkeypatch.setattr(settings.keyring, "delete_password", lambda s, u: vault.pop((s, u)))
    return vault


def test_defaults_and_theme():
    assert settings.load()["theme"] == "system"
    assert settings.save({"theme": "dark", "voice": False, "evil": 1})["theme"] == "dark"
    assert "evil" not in settings.load()


def test_key_goes_to_vault_not_file(isolated):
    settings.set_key("slot1", "gemini", "AIzaSyTESTKEY1234567890abcd")
    assert "AIzaSy" not in settings.FILE.read_text()
    assert isolated[("ChessCoach", "slot1")] == "AIzaSyTESTKEY1234567890abcd"
    pub = settings.public()["slots"]["slot1"]
    assert pub == {"provider": "gemini", "set": True, "ends": "abcd"}


def test_bad_key_refused_and_remove():
    with pytest.raises(ValueError):
        settings.set_key("slot2", "groq", "short")
    with pytest.raises(ValueError):
        settings.set_key("slot3", "groq", "x" * 40)
    settings.set_key("slot2", "groq", "gsk_" + "x" * 40)
    settings.remove_key("slot2")
    assert settings.public()["slots"]["slot2"]["set"] is False
